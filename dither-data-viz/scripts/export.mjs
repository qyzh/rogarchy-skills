#!/usr/bin/env node
/**
 * Export every chart canvas in an HTML file to an opaque PNG.
 *
 * Usage:
 *   node scripts/export.mjs <index.html>
 *
 * Env:
 *   CHROME_BIN  Path to Chrome/Chromium when it is not on PATH. Env var first,
 *               then the CHROME_BIN= line of the rogarchy-skills config file
 *               (${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env).
 *
 * The script launches headless Chromium, emulates a 540x960 mobile viewport at
 * DPR 2 with prefers-reduced-motion: reduce, waits for the page to report
 * window.__DITHER_READY__, then composites each chart canvas onto #0c0c0e
 * before writing <name>.png beside the HTML file.
 */
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { constants as fsConstants } from 'node:fs';
import { access, mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const BG = '#0c0c0e';
const MIN_BYTES = 1024;
const READY_TIMEOUT = 30_000;
const VIEWPORT = { width: 540, height: 960, deviceScaleFactor: 2, mobile: true };

const input = process.argv[2];
if (!input || input === '-h' || input === '--help') {
  console.error('Usage: node scripts/export.mjs <index.html>');
  process.exit(input ? 0 : 1);
}

const htmlPath = resolve(input);

function fail(message) {
  console.error('export: ' + message);
  process.exit(1);
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function slug(value, fallback = 'chart') {
  const s = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return s || fallback;
}

// Env var if non-empty, else the last `name=value` line of config.env, else ''.
// The file is read as data, never sourced: values are literal.
async function setting(name) {
  if (process.env[name]) return process.env[name];
  const base = process.env.XDG_CONFIG_HOME || join(homedir(), '.config');
  let text;
  try {
    text = await readFile(join(base, 'rogarchy-skills', 'config.env'), 'utf8');
  } catch {
    return '';
  }
  let found = '';
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trimEnd();
    if (!line || line.trimStart().startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq > 0 && line.slice(0, eq) === name) found = line.slice(eq + 1);
  }
  return found;
}

async function findBrowser() {
  const chromeBin = await setting('CHROME_BIN');
  if (chromeBin) {
    await access(chromeBin, fsConstants.X_OK).catch(() => {
      throw new Error(`CHROME_BIN is not executable: ${chromeBin}`);
    });
    return chromeBin;
  }

  const candidates = process.platform === 'darwin'
    ? [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        'google-chrome',
        'chromium',
      ]
    : process.platform === 'win32'
      ? [
          'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
          'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
          'chrome.exe',
          'chromium.exe',
        ]
      : [
          'chromium',
          'chromium-browser',
          'google-chrome-stable',
          'google-chrome',
          'chrome',
        ];

  for (const bin of candidates) {
    if (bin.includes('/') || bin.includes('\\')) {
      try {
        await access(bin, fsConstants.X_OK);
        return bin;
      } catch {
        continue;
      }
    }
    const found = await new Promise((res) => {
      const probe = spawn(bin, ['--version'], { stdio: 'ignore' });
      probe.on('error', () => res(false));
      probe.on('exit', (code) => res(code === 0));
    });
    if (found) return bin;
  }

  throw new Error('No Chrome/Chromium found. Set CHROME_BIN to the browser executable.');
}

async function launch(bin) {
  const profile = await mkdtemp(join(tmpdir(), 'dither-export-'));
  const args = [
    '--headless=new',
    '--remote-debugging-port=0',
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-sync',
    '--hide-scrollbars',
    '--allow-file-access-from-files',
    'about:blank',
  ];
  if (typeof process.getuid === 'function' && process.getuid() === 0) {
    args.unshift('--no-sandbox');
  }

  const proc = spawn(bin, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  let stderr = '';

  try {
    const wsUrl = await new Promise((res, rej) => {
      const timer = setTimeout(() => {
        rej(new Error('Chromium did not expose DevTools within 20s.\n' + stderr));
      }, 20_000);

      proc.stderr?.setEncoding('utf8');
      proc.stderr?.on('data', (chunk) => {
        stderr += chunk;
        const match = stderr.match(/DevTools listening on (ws:\/\/\S+)/);
        if (match) {
          clearTimeout(timer);
          res(match[1]);
        }
      });
      proc.on('error', (err) => {
        clearTimeout(timer);
        rej(err);
      });
      proc.on('exit', (code) => {
        clearTimeout(timer);
        rej(new Error(`Chromium exited early (code ${code}).\n${stderr}`));
      });
    });

    return { proc, profile, wsUrl };
  } catch (err) {
    proc.kill('SIGKILL');
    await rm(profile, { recursive: true, force: true }).catch(() => {});
    throw err;
  }
}

async function connect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url);
    const pending = new Map();
    const listeners = new Map();
    let nextId = 0;
    let opened = false;

    const api = {
      send(method, params = {}) {
        return new Promise((resolveSend, rejectSend) => {
          const id = ++nextId;
          pending.set(id, { resolve: resolveSend, reject: rejectSend });
          ws.send(JSON.stringify({ id, method, params }));
        });
      },
      once(method) {
        return new Promise((resolveEvent) => {
          const list = listeners.get(method) || [];
          list.push(resolveEvent);
          listeners.set(method, list);
        });
      },
      close() {
        ws.close();
      },
    };

    ws.addEventListener('open', () => {
      opened = true;
      res(api);
    });
    ws.addEventListener('error', () => rej(new Error('DevTools WebSocket connection failed')));
    ws.addEventListener('close', () => {
      const err = new Error('DevTools connection closed');
      if (!opened) rej(err);
      for (const { reject } of pending.values()) reject(err);
      pending.clear();
    });
    ws.addEventListener('message', (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve: resolveSend, reject: rejectSend } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) rejectSend(new Error(msg.error.message));
        else resolveSend(msg.result);
        return;
      }
      if (msg.method && listeners.has(msg.method)) {
        const list = listeners.get(msg.method);
        listeners.delete(msg.method);
        list.forEach(fn => fn(msg.params));
      }
    });
  });
}

async function pageSocket(wsUrl) {
  const port = new URL(wsUrl).port;
  const endpoint = `http://127.0.0.1:${port}/json/list`;

  for (let attempt = 0; attempt < 50; attempt++) {
    try {
      const response = await fetch(endpoint);
      const targets = await response.json();
      const page = targets.find(t => t.type === 'page');
      if (page && page.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
    } catch {
      // Browser is still starting; retry.
    }
    await delay(100);
  }

  throw new Error('Could not find a page target in Chromium');
}

async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
    userGesture: true,
  });
  if (result.exceptionDetails) {
    const detail = result.exceptionDetails.exception?.description
      || result.exceptionDetails.text
      || 'unknown evaluation error';
    throw new Error(detail);
  }
  return result.result.value;
}

async function waitForReady(cdp) {
  const deadline = Date.now() + READY_TIMEOUT;
  while (Date.now() < deadline) {
    let ready = false;
    let pageError = null;
    try {
      ready = await evaluate(cdp, 'window.__DITHER_READY__ === true');
      if (!ready) pageError = await evaluate(cdp, 'window.__DITHER_ERROR__ || null');
    } catch {
      // Navigation can briefly destroy the execution context; retry.
      await delay(100);
      continue;
    }
    if (ready) return;
    if (pageError) throw new Error(pageError);
    await delay(100);
  }
  const state = await evaluate(cdp, `JSON.stringify({
    ready: window.__DITHER_READY__ === true,
    error: window.__DITHER_ERROR__ || null,
    count: window.__DITHER_COUNT__ ?? null,
    charts: Array.isArray(window.CHARTS) ? window.CHARTS.length : (window.CHART ? 1 : 0),
    canvases: document.querySelectorAll('canvas').length,
  })`).catch(() => '{}');
  throw new Error(`Charts did not finish painting within ${READY_TIMEOUT / 1000}s: ${state}`);
}

async function composite(cdp) {
  return evaluate(cdp, `(() => {
    const canvases = [...new Set(document.querySelectorAll('.chart-card canvas, canvas.chart, #chart'))];

    return canvases.map((canvas, i) => {
      if (!canvas.width || !canvas.height) {
        throw new Error('Canvas ' + i + ' has no bitmap; call Dither.fit before paint.');
      }
      const out = document.createElement('canvas');
      out.width = canvas.width;
      out.height = canvas.height;
      const ctx = out.getContext('2d', { willReadFrequently: true });
      ctx.fillStyle = ${JSON.stringify(BG)};
      ctx.fillRect(0, 0, out.width, out.height);
      ctx.drawImage(canvas, 0, 0);

      const pixels = ctx.getImageData(0, 0, out.width, out.height).data;
      let ink = 0;
      let clear = 0;
      for (let p = 0; p < pixels.length; p += 16) {
        if (pixels[p + 3] !== 255) clear++;
        else if (pixels[p] !== 12 || pixels[p + 1] !== 12 || pixels[p + 2] !== 14) ink++;
      }

      return {
        name: canvas.dataset.export || (canvases.length > 1 ? 'chart-' + (i + 1) : 'chart'),
        data: out.toDataURL('image/png'),
        width: out.width,
        height: out.height,
        ink,
        clear,
      };
    });
  })()`);
}

async function main() {
  if (typeof WebSocket === 'undefined') {
    fail('Node 22+ is required (global WebSocket is missing)');
  }
  await access(htmlPath, fsConstants.R_OK).catch(() => {
    fail(`cannot read ${htmlPath}`);
  });
  const info = await stat(htmlPath).catch(() => null);
  if (!info || !info.isFile()) fail(`not a file: ${htmlPath}`);

  let browser;
  let cdp;

  try {
    const bin = await findBrowser();
    browser = await launch(bin);

    const socket = await pageSocket(browser.wsUrl);
    cdp = await connect(socket);

    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', VIEWPORT);
    await cdp.send('Emulation.setEmulatedMedia', {
      features: [{ name: 'prefers-reduced-motion', value: 'reduce' }],
    });

    const loaded = cdp.once('Page.loadEventFired');
    await cdp.send('Page.navigate', { url: pathToFileURL(htmlPath).href });
    await Promise.race([
      loaded,
      delay(READY_TIMEOUT).then(() => {
        throw new Error('Page load timed out');
      }),
    ]);

    await waitForReady(cdp);

    const charts = await composite(cdp);
    if (!charts.length) {
      throw new Error('No chart canvases found. Expected .chart-card canvas, canvas.chart, or #chart.');
    }

    const expected = await evaluate(cdp, 'window.__DITHER_COUNT__ ?? null');
    if (expected != null && expected !== charts.length) {
      throw new Error(`Rendered ${expected} chart cards but found ${charts.length} canvases`);
    }

    const names = new Set();
    const planned = [];

    for (const chart of charts) {
      const name = slug(chart.name);
      if (names.has(name)) {
        throw new Error(`Duplicate export name "${name}". Give each spec a unique name.`);
      }
      names.add(name);

      if (!chart.data || !chart.data.startsWith('data:image/png;base64,')) {
        throw new Error(`Canvas "${name}" did not return a PNG data URL`);
      }
      if (chart.ink === 0) {
        throw new Error(`Canvas "${name}" is blank (no pixels differ from ${BG})`);
      }
      if (chart.clear !== 0) {
        throw new Error(`Canvas "${name}" is not opaque`);
      }

      const buffer = Buffer.from(chart.data.slice('data:image/png;base64,'.length), 'base64');
      if (buffer.length < MIN_BYTES) {
        throw new Error(`Canvas "${name}" produced ${buffer.length} bytes; expected > ${MIN_BYTES}`);
      }

      planned.push({ name, buffer, width: chart.width, height: chart.height });
    }

    const seen = new Map();
    for (const item of planned) {
      const digest = createHash('sha256').update(item.buffer).digest('hex');
      if (seen.has(digest)) {
        throw new Error(`"${item.name}" is identical to "${seen.get(digest)}"; charts must be distinct`);
      }
      seen.set(digest, item.name);
    }

    const written = [];
    for (const item of planned) {
      const file = join(dirname(htmlPath), item.name + '.png');
      await writeFile(file, item.buffer);
      written.push({ file, bytes: item.buffer.length, width: item.width, height: item.height });
    }

    for (const item of written) {
      console.log(`export: ${item.file} (${item.width}x${item.height}, ${item.bytes} bytes)`);
    }
    console.log(`export: ${written.length} PNG${written.length === 1 ? '' : 's'}`);
  } finally {
    if (cdp) cdp.close();
    if (browser) {
      browser.proc.kill('SIGTERM');
      await Promise.race([
        new Promise(resolve => browser.proc.once('exit', resolve)),
        delay(2000),
      ]);
      browser.proc.kill('SIGKILL');
      await rm(browser.profile, { recursive: true, force: true }).catch(() => {});
    }
  }
}

main().catch((err) => {
  fail(err.message || String(err));
});
