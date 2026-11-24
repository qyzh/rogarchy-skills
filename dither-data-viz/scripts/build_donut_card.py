#!/usr/bin/env python3
"""Bangun kartu "Ledger First" default dari data_usage Omarchy (HTML mandiri).

Pakai:
  python3 build_donut_card.py --start 2026-01-01 --end 2026-01-06 --out <folder>

Membaca daily_by_model.csv + cost_by_model.csv dari data dir, lalu menulis
index.html mandiri (tanpa template) di --out. Salin dither.js dan export.mjs
ke --out bila belum ada. Layout: tabel ledger sebagai hero (bar dither per
baris) + donut kecil; donut diekspor sebagai PNG (name: model-donut).
Biaya ditulis tepat 2 desimal ($168.23, $0.00).
"""
from __future__ import annotations

import argparse, csv, html, json, os, shutil, sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TONES = ["green", "blue", "purple", "orange", "pink", "red", "grey"]


def setting(var):
    """Env var if non-empty, else the last `var=value` line of the rogarchy-skills
    config file (${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env), else None.
    The file is read as data, never sourced: values are literal."""
    value = os.environ.get(var)
    if value:
        return value
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    try:
        text = (Path(base) / "rogarchy-skills" / "config.env").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    found = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        key, sep, val = line.partition("=")
        if sep and key == var:
            found = val
    return found or None


def default_data_dir():
    """--data-dir is handled by the caller; then OMARCHY_USAGE_DATA (env, then
    config.env); then ${XDG_STATE_HOME:-~/.local/state}/omarchy/agents/usage-history."""
    value = setting("OMARCHY_USAGE_DATA")
    if value:
        return Path(value).expanduser()
    state = os.environ.get("XDG_STATE_HOME")
    base = Path(state).expanduser() if state else Path.home() / ".local" / "state"
    return base / "omarchy" / "agents" / "usage-history"


def days_between(start, end):
    d, out = start, []
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def partial_days(data, days):
    """Sorted partial-cost days in range; None when the status is unknown."""
    p = data / "cost_daily.csv"
    if not p.exists():
        return None
    with p.open(newline="") as f:
        rd = csv.DictReader(f)
        if "partial" not in (rd.fieldnames or []):
            return None
        return sorted({r["date"] for r in rd
                       if r["date"] in days and (r.get("partial") or "0").strip() not in ("", "0")})


def main():
    ap = argparse.ArgumentParser(description="Kartu donut model — default dither-data-viz")
    ap.add_argument("--data-dir", default=None,
                    help="default: $OMARCHY_USAGE_DATA atau ~/.local/state/omarchy/agents/usage-history")
    ap.add_argument("--start", type=date.fromisoformat, required=True)
    ap.add_argument("--end", type=date.fromisoformat, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    data = Path(args.data_dir).expanduser() if args.data_dir else default_data_dir()
    if args.start > args.end:
        sys.exit(f"build_donut_card: --start {args.start} is after --end {args.end}")
    for name in ("daily_by_model.csv", "cost_by_model.csv"):
        if not (data / name).exists():
            sys.exit(f"build_donut_card: missing {data / name}")
    days = set(days_between(args.start, args.end))

    agg = defaultdict(lambda: dict(nc=0, tok=0, prompt=0, agents=set(), cost=0.0))
    with (data / "daily_by_model.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            if r["date"] not in days:
                continue
            m = r.get("model") or "(unknown)"
            v = agg[m]
            v["nc"] += int(r.get("inputTokens") or 0) + int(r.get("outputTokens") or 0)
            v["tok"] += int(r.get("tokens") or 0)
            v["prompt"] += int(r.get("prompts") or 0)
            v["agents"].add(r["agent"])
    cost_all = 0.0
    with (data / "cost_by_model.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            if r["date"] in days:
                cost_all += float(r.get("costUSD") or 0)
                if r["model"] in agg:
                    agg[r["model"]]["cost"] += float(r.get("costUSD") or 0)

    agg = {m: v for m, v in agg.items() if v["nc"] > 0}
    if not agg:
        sys.exit(f"build_donut_card: no non-cache token usage between {args.start} and {args.end} in {data}")

    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name, src in [("dither.js", SKILL / "scripts/dither.js"),
                      ("export.mjs", SKILL / "scripts/export.mjs")]:
        if not (out / name).exists():
            shutil.copy2(src, out / name)
    (out / "scripts").mkdir(exist_ok=True)
    if not (out / "scripts/export.mjs").exists():
        shutil.copy2(SKILL / "scripts/export.mjs", out / "scripts/export.mjs")

    ranked = sorted(agg.items(), key=lambda kv: -kv[1]["nc"])
    top, rest = ranked[:args.top], ranked[args.top:]
    others = dict(nc=sum(v["nc"] for _, v in rest), tok=sum(v["tok"] for _, v in rest),
                  prompt=sum(v["prompt"] for _, v in rest),
                  cost=sum(v["cost"] for _, v in rest),
                  agents=set().union(*(v["agents"] for _, v in rest)) if rest else set())
    items = [(m, v) for m, v in top]
    if rest:
        items.append(("Lainnya (%d model)" % len(rest), others))
    total_nc = sum(v["nc"] for _, v in items)
    total_cost = sum(v["cost"] for _, v in items)
    usd = lambda x: f"${x:,.2f}"
    unshown = cost_all - total_cost
    unshown_note = ""
    if unshown >= 0.005:
        unshown_note = f"Biaya {usd(unshown)} dari model tanpa token non-cache tidak ditampilkan di tabel. "
        print(f"WARN: {usd(unshown)} cost from models without non-cache tokens is not in the table", file=sys.stderr)

    slices = []
    for i, (model, v) in enumerate(items):
        label = f"{model} · {', '.join(sorted(v['agents']))}" if v["agents"] else model
        slices.append({"name": label, "tone": TONES[i % len(TONES)],
                       "fill": "gradient", "value": v["nc"]})
    # Largest-remainder rounding to 0.1 so displayed shares sum to exactly 100.0.
    raw = [1000 * v["nc"] / total_nc for _, v in items]
    tenths = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - tenths[i], reverse=True)[:1000 - sum(tenths)]:
        tenths[i] += 1
    pcts = [t / 10 for t in tenths]

    report = (data / "cost_report.md").read_text() if (data / "cost_report.md").exists() else ""
    fetched = next((ln.split("fetched_at ", 1)[1].strip()
                    for ln in report.splitlines() if "fetched_at " in ln), "n/a")
    pdays = partial_days(data, days)
    inc, inc_note = "", ""
    if pdays:
        inc = " · INCOMPLETE"
        inc_note = f"Biaya INCOMPLETE: hari parsial (ada token berbayar tak terharga) {', '.join(pdays)} — total di bawah nilai sebenarnya. "
    elif pdays is None:
        inc_note = "Status kelengkapan biaya tidak diketahui (cost_daily.csv tidak ada atau tanpa kolom partial). "
    rng = f"{args.start} s/d {args.end}"
    title = args.title or f"Token per Model — {args.start.strftime('%d %b')}–{args.end.strftime('%d %b %Y')}"
    folded_note = "Model dengan pemakaian kecil digabung dalam “Lainnya”. " if rest else ""
    esc = html.escape
    zw = lambda t: t.replace("non-cache", "non-​cache")  # font mono tertentu menutup "NON-CACHE"

    mx = max(v["nc"] for _, v in items)
    rows = []
    for k, ((model, v), pct, sl) in enumerate(zip(items, pcts, slices)):
        rows.append(
            f'<div class="r"><span class="n">{k+1:02d}</span>'
            f'<div class="m"><span class="sw" data-tone="{sl["tone"]}"></span>{esc(model)}'
            f'<small>{esc(", ".join(sorted(v["agents"])))} · {pct:.1f}% · {usd(v["cost"])}</small></div>'
            f'<div class="bar"><div class="plot"><canvas id="b{k}"></canvas></div></div>'
            f'<span class="v">{v["nc"]:,}</span><span class="p">{pct:.1f}%</span></div>')
    bars = [round(v["nc"] / mx, 6) for _, v in items]

    css = """
*{box-sizing:border-box}
:root{--bg:#0b0b0c;--fg:#ededee;--muted:#a3a3ab;--line:#1d1d20;--plot:#0c0c0e;
--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
--mono:"DejaVu Sans Mono","Liberation Mono","SF Mono",Menlo,Consolas,"Courier New",monospace;color-scheme:dark}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:var(--bg);color:var(--fg);font-family:var(--sans);-webkit-font-smoothing:antialiased;font-size:14px;line-height:1.4}
body{display:flex;flex-direction:column;padding:60px 60px 40px}
.plot{position:relative;background:var(--plot);overflow:hidden}
canvas{position:absolute;inset:0;width:100%;height:100%;display:block;image-rendering:pixelated}
.sw{display:inline-block;width:11px;height:11px;margin-right:8px;border-radius:2px;box-shadow:inset 0 0 0 1px rgb(255 255 255/.16)}
.chip{font:500 12px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.top{display:grid;grid-template-columns:1fr 300px;gap:30px;align-items:end;border-bottom:2px solid var(--fg);padding-bottom:26px}
h1{margin:12px 0 0;font:700 54px/.98 var(--mono);letter-spacing:-.06em;text-transform:uppercase}
.sub{margin:16px 0 0;font-size:17px;color:var(--muted);max-width:44ch}
.ring{position:relative;width:300px;height:300px}.ring .plot{position:absolute;inset:0;background:transparent}
.kpi{display:flex;gap:44px;margin-top:22px}.kpi b{display:block;font:600 34px/1 var(--mono)}.kpi span{font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.rows{margin-top:6px;flex:1;display:flex;flex-direction:column}
.hd,.r,.tot{display:grid;grid-template-columns:44px 1fr 250px 118px 104px;gap:14px;align-items:center}
.hd{font:500 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:14px 0 10px;border-bottom:1px solid var(--line)}
.hd span:nth-child(n+4){text-align:right}
#rows{display:flex;flex-direction:column;flex:1}
.r{flex:1;border-bottom:1px solid var(--line)}
.r .n{font:500 15px var(--mono);color:var(--muted)}
.r .m{font:500 21px/1.15 var(--sans);letter-spacing:-.02em;overflow-wrap:anywhere}.r .m small{display:block;font:400 13px var(--mono);color:var(--muted);margin-top:3px;letter-spacing:0}
.r .bar{position:relative;height:30px}.r .bar .plot{position:absolute;inset:0;border-radius:3px}
.r .v{font:500 17px var(--mono);text-align:right;font-variant-numeric:tabular-nums}.r .p{font:600 20px var(--mono);text-align:right}
.tot{padding:18px 0 0;border-top:2px solid var(--fg);font:600 22px var(--mono);align-items:baseline}
.tot .c{grid-column:2/4}.tot .v,.tot .p{text-align:right}.tot .v{font-size:17px}
.foot{margin:18px 0 0;font-size:12px;color:var(--muted)}
"""
    spec = {"name": "model-donut", "title": "Porsi token non-cache per model",
            "type": "pie", "inner": 0.62, "slices": slices}
    js = """
const SPEC = %s, BARS = %s, PX = 3;
const paintAll = () => { try {
  for (const [id, build] of [['chart', (w, h) => Dither.pie(w, h, SPEC.slices, {inner: SPEC.inner})],
      ...BARS.map((v, k) => ['b' + k, (w, h) => Dither.meter(w, h, v, SPEC.slices[k].tone, 'gradient')])]) {
    const c = document.getElementById(id), [w, h] = Dither.fit(c, PX);
    if (w < 2 || h < 2) throw new Error('canvas ' + id + ' has no layout box');
    Dither.paint(c, build(w, h), PX);
  }
  window.__DITHER_READY__ = true; document.documentElement.dataset.chartsReady = 'true';
} catch (e) { window.__DITHER_ERROR__ = String(e && e.message || e); } };
window.addEventListener('load', () => {
  if (typeof Dither === 'undefined') { window.__DITHER_ERROR__ = 'Dither is undefined (dither.js failed to load)'; return; }
  document.querySelectorAll('.sw').forEach(s => { s.style.background = Dither.color(s.dataset.tone, 0.7, 1); });
  window.__DITHER_COUNT__ = 1; paintAll();
});
""" % (json.dumps(spec, ensure_ascii=False), json.dumps(bars))

    doc = f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=1080">
<title>{esc(title)}</title>
<style>{css}</style></head>
<body>
<div class="top"><div><span class="chip">Ledger · token non-cache per model</span><h1>{esc(args.title or 'Token per Model')}</h1>
<p class="sub">{esc(rng)} · diurut dari token non-cache terbesar</p></div>
<div class="ring"><div class="plot"><canvas id="chart" class="chart" data-export="model-donut" role="img" aria-label="Donut porsi token non-cache per model"></canvas></div></div></div>
<div class="kpi"><div><b>{total_nc/1e6:.2f} jt</b><span>token non-cache</span></div><div><b>{usd(total_cost)}</b><span>total biaya{inc}</span></div><div><b>{len(ranked)}</b><span>model</span></div></div>
<div class="rows"><div class="hd"><span>#</span><span>Model · agent</span><span>Porsi (bar dither)</span><span>Token</span><span>Porsi</span></div>
<div id="rows">{''.join(rows)}</div></div>
<div class="tot"><span></span><span class="c">TOTAL · biaya {usd(total_cost)}{inc}</span><span class="v">{total_nc:,}</span><span class="p">{sum(pcts):.1f}%</span></div>
<p class="foot">Token non-cache = input non-cache + output; cache read tidak dihitung. {folded_note}{inc_note}{unshown_note}Biaya = revaluasi historis ke harga saat fetch ({esc(fetched)}; simulasi pay-as-you-go), bukan tagihan langganan. Sumber: omarchy-agent-usage. <a href="https://artificialanalysis.ai/">Source: Artificial Analysis (artificialanalysis.ai)</a>. Based on data from Artificial Analysis. Created by dither-data-viz, not by Artificial Analysis. Artificial Analysis does not endorse this report/tool.</p>
<script src="./dither.js"></script>
<script>{js}</script></body></html>"""
    (out / "index.html").write_text(zw(doc))

    print(f"OUT={out / 'index.html'}")
    print(f"slices={len(slices)} models={len(ranked)} total_nc={total_nc:,} cost={usd(total_cost)}"
          + (f" INCOMPLETE partial={', '.join(pdays)}" if pdays else ""))
    for (model, v), pct in zip(items, pcts):
        print(f"  {model:34s} {v['nc']:>11,}  {pct:5.1f}%  {','.join(sorted(v['agents']))}")


if __name__ == "__main__":
    main()
