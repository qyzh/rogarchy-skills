// Ordered-dither rasterizer.
// Adapted from dither-kit-rs (https://github.com/DeepanshuMishraa/dither-kit-rs), Copyright (c) 2026 Deepanshu Mishra, MIT. See THIRD_PARTY_NOTICES.md.
(() => {
  'use strict';

  // ---------- Engine ----------
  const TAU = Math.PI * 2;
  const mod = (v, n) => ((v % n) + n) % n;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const B2 = [0, 2, 3, 1], B4 = [], B8 = [];
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++)
    B4[y * 4 + x] = 4 * B2[(y % 2) * 2 + (x % 2)] + B2[(y >> 1) * 2 + (x >> 1)];
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++)
    B8[y * 8 + x] = 4 * B4[(y % 4) * 4 + (x % 4)] + B2[((y >> 2) % 2) * 2 + ((x >> 2) % 2)];
  const HT = [12, 5, 6, 13, 4, 0, 1, 7, 11, 3, 2, 8, 15, 10, 9, 14];
  const t8 = (x, y) => (B8[mod(y, 8) * 8 + mod(x, 8)] + 0.5) / 64;
  const t4 = (x, y) => (B4[mod(y, 4) * 4 + mod(x, 4)] + 0.5) / 16;
  const tHalf = (x, y) => (HT[mod(y, 4) * 4 + mod(x, 4)] + 0.5) / 16;

  function hash01(x, y) {
    let h = Math.imul(x | 0, 0x9e3779b1) ^ Math.imul(y | 0, 0x85ebca77);
    h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d);
    h ^= h >>> 12; h = Math.imul(h, 0x297a2d39);
    h ^= h >>> 15;
    return (h >>> 0) / 4294967295;
  }

  const HUE = { green: 150, blue: 250, purple: 300, pink: 350, orange: 55, red: 25, grey: 260 };
  const TONES = ['green', 'blue', 'purple', 'pink', 'orange', 'red', 'grey'];
  const css = new Map();
  function color(tone, level, alpha) {
    const l = Math.round(clamp(level, 0, 1) * 50) / 50;
    const a = Math.round(clamp(alpha, 0, 1) * 20) / 20;
    const key = tone + '|' + l + '|' + a;
    let c = css.get(key);
    if (!c) {
      const hue = typeof tone === 'number' ? tone : HUE[tone];
      const base = tone === 'grey' ? 0.012 : 0.19;
      const chroma = base * clamp(1 - Math.abs(l - 0.55) * 1.3, 0.25, 1);
      c = `oklch(${(0.22 + l * 0.72).toFixed(3)} ${chroma.toFixed(3)} ${hue} / ${a})`;
      css.set(key, c);
    }
    return c;
  }

  function covers(fill, x, y, i) {
    switch (fill) {
      case 'dotted':
        return mod(x, 2) === 0 && mod(y + mod(Math.trunc(x / 2), 2), 2) === 0 &&
          i * 1.4 > t4(Math.trunc(x / 2), Math.trunc(y / 2));
      case 'hatched': return mod(x + y, 3) === 0 && 0.25 + i > t4(x, y);
      case 'solid': return i > 0.02;
      default: return i > t8(x, y);
    }
  }

  class Grid {
    constructor(w, h) { this.w = w; this.h = h; this.c = new Array(w * h).fill(null); }
    set(x, y, tone, level, alpha = 1) {
      if (x >= 0 && y >= 0 && x < this.w && y < this.h) this.c[y * this.w + x] = [tone, level, alpha];
    }
    get(x, y) { return x >= 0 && y >= 0 && x < this.w && y < this.h ? this.c[y * this.w + x] : null; }
    clear(x, y) { if (x >= 0 && y >= 0 && x < this.w && y < this.h) this.c[y * this.w + x] = null; }
    bloom(radius, strength) {
      const src = this.c.slice();
      const at = (x, y) => (x >= 0 && y >= 0 && x < this.w && y < this.h ? src[y * this.w + x] : null);
      for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) {
        if (at(x, y)) continue;
        let best = null, bd = 0;
        search: for (let d = 1; d <= radius; d++)
          for (let oy = -d; oy <= d; oy++) for (let ox = -d; ox <= d; ox++) {
            if (Math.abs(ox) !== d && Math.abs(oy) !== d) continue;
            const c = at(x + ox, y + oy);
            if (c && c[2] > 0.63) { best = c; bd = d; break search; }
          }
        if (best) {
          const glow = strength * (1 - (bd - 1) / radius);
          if (glow > t4(x, y)) this.set(x, y, best[0], best[1], best[2] * (0.35 + 0.25 * glow));
        }
      }
    }
    sparkle(time, density, tone, anywhere) {
      for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) {
        if (hash01(x, y ^ 0x5bd1) >= density) continue;
        if (!anywhere && !this.get(x, y)) continue;
        const phase = hash01(y, x ^ 0x1b56) * TAU;
        const speed = 1.5 + 2.5 * hash01(x ^ 0x77, y);
        const wink = Math.pow(Math.max(0, Math.sin(time * speed + phase)), 12);
        if (wink > 0.35) this.set(x, y, tone, 0.97, wink);
      }
    }
  }

  function bloom(g, radius, strength) {
    g.bloom(radius, strength);
    return g;
  }

  function line(g, x0, y0, x1, y1, tone, level, alpha, dash = 1) {
    const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx + dy, step = 0;
    for (;;) {
      if (dash <= 1 || step % dash === 0) g.set(x0, y0, tone, level, alpha);
      step++;
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  }
  const guide = (g, x0, y0, x1, y1, dash) => line(g, x0, y0, x1, y1, 'grey', 0.55, 0.45, dash);
  function dot(g, x, y, tone, ring, center, alpha = 1) {
    for (let oy = -1; oy <= 1; oy++) for (let ox = -1; ox <= 1; ox++)
      g.set(x + ox, y + oy, tone, ox || oy ? ring : center, alpha);
  }

  function niceScale(max, count = 4) {
    if (!(max > 0)) max = 1;
    const raw = max / count, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw);
    const top = Math.ceil(max / step) * step;
    const ticks = [];
    for (let i = 0; i <= Math.round(top / step); i++) ticks.push(i * step);
    return { max: top, ticks, y: (v, h) => (h - 1) - clamp(v / top, 0, 1) * (h - 1) };
  }

  function interpolate(v, f) {
    const n = v.length;
    if (n === 0) return null;
    if (n === 1) return Number.isFinite(v[0]) ? v[0] : null;
    f = clamp(f, 0, n - 1);
    const i = Math.min(Math.floor(f), n - 2), t = f - i;
    const at = k => v[clamp(k, 0, n - 1)];
    const p0 = at(i - 1), p1 = at(i), p2 = at(i + 1), p3 = at(i + 2);
    if (Number.isFinite(p1) && t === 0) return p1;
    if (Number.isFinite(p2) && t === 1) return p2;
    if (!Number.isFinite(p1) || !Number.isFinite(p2)) return null;
    const q0 = Number.isFinite(p0) ? p0 : p1;
    const q3 = Number.isFinite(p3) ? p3 : p2;
    const r = 0.5 * (2 * p1 + (-q0 + p2) * t + (2 * q0 - 5 * p1 + 4 * p2 - q3) * t * t +
      (-q0 + 3 * p1 - 3 * p2 + q3) * t * t * t);
    return clamp(r, Math.min(p1, p2), Math.max(p1, p2));
  }

  function areaChart(w, h, series, opts) {
    opts = opts || {};
    const g = new Grid(w, h);
    const n = Math.max(...series.map(s => s.values.length));
    const nums = series.flatMap(s => s.values).filter(Number.isFinite);
    const max = opts.yMax ?? Math.max(0, ...nums);
    const sc = niceScale(max);
    if (opts.grid !== false) {
      for (const t of sc.ticks.slice(1)) { const y = Math.round(sc.y(t, h)); guide(g, 0, y, w - 1, y, 3); }
      guide(g, 0, h - 1, w - 1, h - 1, 2);
    }
    const progress = opts.progress ?? 1;
    const reveal = progress * w, grow = 0.6 + 0.4 * progress;
    const alphaFor = i => (opts.selected != null && opts.selected !== i ? 0.3 : 1);
    const cols = series.map(() => new Array(w).fill(null));
    for (let x = 0; x < w && x <= reveal; x++) {
      const f = n > 1 ? (x / (w - 1)) * (n - 1) : 0;
      series.forEach((s, si) => {
        const yv = interpolate(s.values, f);
        cols[si][x] = Number.isFinite(yv) ? sc.y(yv * grow, h) : null;
      });
    }
    series.forEach((s, si) => {
      const a = alphaFor(si);
      cols[si].forEach((top, x) => {
        if (top == null) return;
        const span = Math.max(1, h - 1 - top);
        for (let y = Math.ceil(top) + 1; y <= h - 1; y++) {
          const t = 1 - (y - top) / span;
          if (covers(s.fill, x, y, 0.1 + 0.9 * t)) g.set(x, y, s.tone, 0.32 + 0.4 * t, a);
        }
      });
    });
    series.forEach((s, si) => {
      let prev = null;
      cols[si].forEach((top, x) => {
        if (top == null) { prev = null; return; }
        const ty = Math.round(top), from = prev ?? ty;
        for (let y = Math.min(from, ty); y <= Math.max(from, ty); y++) g.set(x, y, s.tone, 0.78, alphaFor(si));
        prev = ty;
      });
    });
    if (opts.bloom) g.bloom(opts.bloom[0], opts.bloom[1]);
    if (opts.hover != null) {
      const x = Math.round((opts.hover * (w - 1)) / (n - 1));
      line(g, x, 0, x, h - 1, 'grey', 0.75, 0.7, 2);
      series.forEach(s => dot(g, x, Math.round(sc.y(s.values[opts.hover], h)), s.tone, 0.7, 0.98));
    }
    return g;
  }

  function pie(w, h, slices, opts) {
    opts = opts || {};
    const g = new Grid(w, h);
    const total = slices.reduce((a, s) => a + s.value, 0);
    const sweep = TAU * (opts.progress ?? 1);
    let acc = 0;
    const angles = slices.map(s => { const a = (s.value / total) * sweep; const r = [acc, acc + a]; acc += a; return r; });
    const radius = Math.min(w, h) / 2 - 2.5, inner = radius * opts.inner;
    const cx = w / 2, cy = h / 2;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const dx = x + 0.5 - cx, dy = y + 0.5 - cy, r = Math.hypot(dx, dy);
      const a = mod(Math.atan2(dx, -dy), TAU);
      const i = angles.findIndex(([a0, a1]) => a >= a0 && a < a1);
      if (i < 0) continue;
      const outer = radius - 2 + (opts.hover === i ? 2 : 0);
      if (r < inner || r > outer) continue;
      const [a0, a1] = angles[i];
      if (Math.min(a - a0, a1 - a) * r < 0.9) continue;
      const s = slices[i], dim = opts.hover != null && opts.hover !== i ? 0.5 : 1;
      const t = clamp((r - inner) / Math.max(1, outer - inner), 0, 1), rim = outer - r < 1.2;
      if (rim || covers(s.fill || 'gradient', x, y, 0.3 + 0.7 * t)) g.set(x, y, s.tone, rim ? 0.8 : 0.3 + 0.4 * t, dim);
    }
    g.geometry = { cx, cy, radius, inner, angles };
    return g;
  }

  function inside(poly, x, y) {
    let c = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xi, yi] = poly[i], [xj, yj] = poly[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
    }
    return c;
  }

  function radar(w, h, series, opts) {
    opts = opts || {};
    const g = new Grid(w, h);
    const n = series[0].values.length, cx = w / 2, cy = h / 2, R = Math.min(w, h) / 2 - 2;
    const tip = i => { const a = -Math.PI / 2 + (TAU * i) / n; return [cx + Math.cos(a) * R, cy + Math.sin(a) * R]; };
    const at = (i, f) => { const [tx, ty] = tip(i % n); return [Math.round(cx + (tx - cx) * f), Math.round(cy + (ty - cy) * f)]; };
    for (let ring = 1; ring <= 4; ring++) for (let i = 0; i < n; i++) guide(g, ...at(i, ring / 4), ...at(i + 1, ring / 4), 2);
    for (let i = 0; i < n; i++) guide(g, Math.round(cx), Math.round(cy), ...at(i, 1), 3);
    const nums = series.flatMap(s => s.values).filter(Number.isFinite);
    const max = niceScale(Math.max(0, ...nums)).max;
    const progress = opts.progress ?? 1;
    series.forEach((s, si) => {
      const alpha = opts.selected != null && opts.selected !== si ? 0.3 : 1;
      const pts = s.values.map((v, i) => { const f = (v / max) * progress; const [tx, ty] = tip(i); return [cx + (tx - cx) * f, cy + (ty - cy) * f]; });
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        if (!inside(pts, x + 0.5, y + 0.5)) continue;
        const d = Math.hypot(x + 0.5 - cx, y + 0.5 - cy) / R;
        if (covers('gradient', x, y, 0.2 + 0.55 * d)) g.set(x, y, s.tone, 0.32 + 0.35 * d, alpha);
      }
      pts.forEach((p, i) => { const q = pts[(i + 1) % n]; line(g, Math.round(p[0]), Math.round(p[1]), Math.round(q[0]), Math.round(q[1]), s.tone, 0.8, alpha); });
      pts.forEach(p => dot(g, Math.round(p[0]), Math.round(p[1]), s.tone, 0.8, 0.97, alpha));
    });
    return g;
  }
  function buttonTexture(w, h, tone, style, density, time) {
    const g = new Grid(w, h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const edge = x === 0 || y === 0 || x === w - 1 || y === h - 1;
      if (edge && style !== 'ghost') {
        if ((x + y) % 2 === 0 || style === 'solid') g.set(x, y, tone, 0.6);
        continue;
      }
      const fy = h > 1 ? y / (h - 1) : 0.5, i = density * (1.05 - 0.45 * fy);
      if (covers('gradient', x, y, i)) g.set(x, y, tone, 0.45 + 0.25 * (1 - fy));
    }
    if (density > 0.4) g.sparkle(time, 0.04 * density, tone, false);
    return g;
  }
  const DENSITY = { solid: [0.32, 0.55, 0.85], outline: [0, 0.3, 0.6], ghost: [0, 0.25, 0.5] };

  function fnv1a(str) {
    let h = 0xcbf29ce484222325n;
    for (const b of new TextEncoder().encode(str)) { h ^= BigInt(b); h = (h * 0x100000001b3n) & 0xffffffffffffffffn; }
    return h;
  }
  function avatar(name) {
    const h = fnv1a(name);
    const bits = Number(h & 0xffffffffn), mirrorX = ((h >> 32n) & 1n) === 0n;
    const hue = Number((h >> 33n) % 180n) * 2, acc = Number((h >> 41n) & 0xffffffffn);
    const g = new Grid(8, 8);
    for (let i = 0; i < 32; i++) {
      const [x, y] = mirrorX ? [i % 4, i >> 2] : [i % 8, i >> 3];
      const [mx, my] = mirrorX ? [7 - x, y] : [x, 7 - y];
      const on = (bits >>> i) & 1;
      const accent = on && (acc >>> (i % 23)) & 1 && (acc >>> ((i + 7) % 23)) & 1;
      const level = accent ? 0.92 : on ? 0.62 : 0.16;
      g.set(x, y, hue, level); g.set(mx, my, hue, level);
    }
    return g;
  }

  function gradient(w, h, from, to, dir) {
    const g = new Grid(w, h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const fx = w > 1 ? x / (w - 1) : 0.5, fy = h > 1 ? y / (h - 1) : 0.5;
      const p = dir === 'right' ? fx : dir === 'down' ? fy : dir === 'radial' ? Math.min(1, Math.hypot(fx - 0.5, fy - 0.5) / Math.SQRT1_2) : 1 - fy;
      if (to) {
        const tone = p > t8(x, y) ? to : from;
        if (0.55 + 0.45 * p > t8(x + 3, y + 5)) g.set(x, y, tone, 0.35 + 0.35 * p);
      } else if (1 - p > t8(x, y)) g.set(x, y, from, 0.3 + 0.4 * (1 - p));
    }
    return g;
  }

  const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  function vnoise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), fx = x - xi, fy = y - yi;
    const s = t => t * t * (3 - 2 * t), sx = s(fx), sy = s(fy), n = hash01;
    const top = n(xi, yi) + (n(xi + 1, yi) - n(xi, yi)) * sx;
    const bot = n(xi, yi + 1) + (n(xi + 1, yi + 1) - n(xi, yi + 1)) * sx;
    return top + (bot - top) * sy;
  }
  const FIELDS = {
    plasma: (u, v, t) => ((Math.sin(u * 7 + t * 0.9) + Math.sin(v * 6 - t * 0.7) + Math.sin((u + v) * 5 + t * 0.5) +
      Math.sin(Math.hypot(u - 0.5, v - 0.5) * 12 - t * 1.2)) / 8 + 0.5),
    waves: (u, v, t) => { const c = 0.5 + 0.18 * Math.sin(u * 6 + t * 1.1) + 0.08 * Math.sin(u * 15 - t * 1.7); return clamp(1 - Math.abs(v - c) * 2.6, 0, 1) * 0.9 + v * 0.15; },
    ripple: (u, v, t) => { const d = Math.hypot(u - 0.5, v - 0.5); return 0.5 + 0.5 * Math.sin(d * 30 - t * 3) * Math.max(0, 1 - d * 1.2); },
    noise: (u, v, t) => vnoise(u * 6 + t * 0.35, v * 4 - t * 0.2) * 0.7 + vnoise(u * 13 - t * 0.5, v * 9) * 0.3,
    aurora: (u, v, t) => { const c = vnoise(u * 5 + t * 0.25, t * 0.15) * 0.6 + 0.4 * Math.abs(Math.sin(u * 9 + t * 0.6)); return c * clamp(1 - Math.max(0, v - 0.35 * c) * 1.6, 0, 1); },
  };
  function background(w, h, field, tone, accent, density, time) {
    const g = new Grid(w, h), f = FIELDS[field];
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const i = smooth(0.18, 0.82, clamp(f(x / w, y / h, time), 0, 1));
      if (i * density > t8(x, y)) {
        const tn = accent && (i - 0.62) * 2.2 > t4(x + 1, y + 2) ? accent : tone;
        g.set(x, y, tn, 0.3 + 0.5 * i);
      }
    }
    return g;
  }

  function meter(w, h, value, tone, fill) {
    const g = new Grid(w, h), filled = Math.round(clamp(value, 0, 1) * w);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      if (x < filled) {
        const i = 0.35 + 0.65 * (x + 1) / Math.max(1, filled);
        if (covers(fill, x, y, i) || x + 1 === filled) g.set(x, y, tone, 0.4 + 0.35 * i);
      } else if ((x + y) % 4 === 0) g.set(x, y, 'grey', 0.35, 0.6);
    }
    return g;
  }

  function sparkline(w, h, values, opts = {}) {
    const yMax = opts.yMax ?? Math.max(...values) * 1.1;
    return areaChart(w, h, [{ tone: opts.tone || 'green', fill: 'gradient', values }],
      { progress: opts.progress ?? 1, grid: false, yMax, bloom: opts.bloom });
  }

  // ---------- Painting ----------
  const dpr = () => (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
  function fit(canvas, px) {
    const r = canvas.getBoundingClientRect(), d = dpr();
    const W = Math.max(1, Math.round(r.width * d)), H = Math.max(1, Math.round(r.height * d));
    if (canvas.width !== W || canvas.height !== H) { canvas.width = W; canvas.height = H; }
    return [Math.floor(r.width / px), Math.floor(r.height / px)];
  }
  function paint(canvas, g, px) {
    const ctx = canvas.getContext('2d'), s = px * dpr();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const buckets = new Map();
    for (let y = 0; y < g.h; y++) {
      let x = 0;
      while (x < g.w) {
        const c = g.c[y * g.w + x];
        if (!c) { x++; continue; }
        const key = color(c[0], c[1], c[2]);
        let end = x + 1;
        while (end < g.w) { const n = g.c[y * g.w + end]; if (!n || color(n[0], n[1], n[2]) !== key) break; end++; }
        let list = buckets.get(key);
        if (!list) buckets.set(key, (list = []));
        list.push(x, y, end - x);
        x = end;
      }
    }
    for (const [fill, list] of buckets) {
      ctx.fillStyle = fill;
      for (let i = 0; i < list.length; i += 3) {
        const x0 = Math.round(list[i] * s), x1 = Math.round((list[i] + list[i + 2]) * s);
        const y0 = Math.round(list[i + 1] * s), y1 = Math.round((list[i + 1] + 1) * s);
        ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
      }
    }
  }

  const api = {
    Grid, covers, bloom,
    areaChart, pie, radar, sparkline, meter,
    paint, fit, color, TONES,
    buttonTexture, avatar, gradient, background, DENSITY,
  };
  const root = typeof globalThis !== 'undefined' ? globalThis : this;
  root.Dither = api;
  Object.assign(root, {
    Grid, covers, bloom, areaChart, pie, radar, sparkline, meter, paint, fit,
  });
})();
