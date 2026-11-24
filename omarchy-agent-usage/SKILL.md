---
name: omarchy-agent-usage
description: "Token usage, quota/limit %, per-day x per-model breakdowns, pay-as-you-go cost simulation (Artificial Analysis prices), cache-hit / token-per-prompt / cost-per-task metrics and weekly reports for local AI agents on Omarchy (Hermes, Claude Code, Codex, OpenCode, grok, agy). Triggers: cek penggunaan token, berapa token terpakai, kuota atau limit habis, agent mana paling boros, simulasi biaya, biaya pay-as-you-go, cache hit ratio, token per prompt, cost per task, laporan mingguan, track usage per hari."
version: 0.3.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, token-usage, metrics, agents, quota, cost]
    related_skills: [omarchy-plugin-authoring]
---

# Omarchy Agent Usage Skill

Baca ini sebelum menjawab pertanyaan tentang pemakaian token, kuota, atau
biaya agent AI di mesin ini, atau sebelum membangun riwayat usage.

## When to Use

- "cek penggunaan token", "berapa token yang sudah dipakai", "kuota habis?"
- "simpan data penggunaan token selama N hari", "track usage per hari"
- "agent mana yang paling boros", "kenapa limit cepat habis"
- "simulasi biaya token", "kalau dibayar per token berapa", "biaya pay-as-you-go"
- "metrik dashboard", "cache hit ratio", "token per prompt", "cost per task"
- "laporan minggu ini", pecahan per hari × per model.

**Don't use for:** membuat plugin Omarchy yang menampilkan usage (lihat
`omarchy-plugin-authoring`), atau dashboard billing cloud provider. Skill ini
membaca store LOKAL agent dan record Omarchy.

## Prerequisites / Config

Requires: commands `python3`; Omarchy wrappers `<OMARCHY_PATH>/bin/omarchy-agent-usage-*` (Linux + Omarchy only).
Local files: `references/task-signal.local.md` (template `references/task-signal.example.md`).

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `OMARCHY_USAGE_DATA` | Data dir (snapshots, CSV, reports) | `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/usage-history` | setting |
| `OMARCHY_USAGE_PRICING_CACHE` | Runtime price cache | `${XDG_CACHE_HOME:-$HOME/.cache}/omarchy-agent-usage/pricing.json` | advanced |
| `OMARCHY_USAGE_PRICING_SEED` | Optional read-only local price seed | `<skill-dir>/references/pricing.json` | advanced |
| `OMARCHY_TASKS_FILE` | Task signal file | `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/agents/tasks.jsonl` | advanced |
| `OMARCHY_PATH` | Omarchy install | `/usr/share/omarchy` | advanced |
| `ARTIFICIAL_ANALYSIS_API_KEY` | Free Artificial Analysis Data API key (prices) | none: no network calls | secret |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { v=$(printenv "$1"); [ -n "$v" ] || v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1); printf '%s\n' "${v:-$2}"; }
rs_get OMARCHY_PATH /usr/share/omarchy
```

The scripts resolve these themselves in the same order (`scripts/common.py`); the API key is read from the env var only (`scripts/cost.py`).

## Quick snapshot (satu agent)

```bash
omarchy-agent-usage-claude      # atau hermes, codex, opencode, grok, ... -> satu JSON record di stdout
ls "$(rs_get OMARCHY_PATH /usr/share/omarchy)"/bin/omarchy-agent-usage-* | grep -v -- '-update$'   # daftar agent
```

- Wrapper per agent tidak mengubah state, tapi sebagian memanggil API limit
  provider (network).
- **JANGAN jalankan `omarchy-agent-usage-update`** kecuali user memintanya
  eksplisit. Itu bukan "refresh read-only":
  - ia menulis ulang semua `~/.local/state/omarchy/agents/usage/<agent>.json`;
  - me-refresh registry akun;
  - menjalankan `omarchy-agent-account-state autoswitch` untuk claude/codex/grok,
    yang **bisa mengganti akun yang sedang login**;
  - stdout-nya kosong (bukan JSON).

  Kalau user memintanya, peringatkan dulu soal auto-switch.

### Field record

| Field | Arti |
|---|---|
| `todayTotalTokens` | Total token hari ini. |
| `todayTokensByModel` | `{model: tokens}` hari ini. |
| `todayPrompts` / `todaySessions` | Jumlah prompt dan sesi hari ini. |
| `recentDays` | 7 hari terakhir: `{date, messageCount}`. **`messageCount` ISINYA TOKEN**, bukan jumlah pesan. |
| `modelUsage` | Total seumur hidup per model (`inputTokens`, `outputTokens`, `cacheReadInputTokens`, `cacheCreationInputTokens`). |
| `limits[]` | `{label, percent, resetsAt}`. **`percent` = pecahan 0–1** (0.95 = 95% terpakai, BUKAN 0.95%). `resetsAt` = waktu ISO UTC dan bisa sudah lewat; bandingkan dengan sekarang sebelum bilang "reset nanti". |
| `totalPrompts` / `totalSessions` / `activeDays` | Total seumur hidup. |

### Aturan membaca angka

- **`cacheReadInputTokens` bukan token baru.** Total token bisa 10–100x input
  segar. Saat melapor, pisahkan dan pakai **token non-cache** (input + output)
  sebagai pemakaian aktual. Jangan bilang "boros 600 juta token" kalau 600 juta
  itu cache read.
- **`recentDays` hanya 7 hari, total saja.** Untuk pecahan per hari × per model,
  pakai pipeline di bawah.
- **Agent tanpa baris lokal** (agy, grok, copilot, openrouter, ...) hanya punya
  total per hari dari `recentDays`. Jangan mengarang pecahan model.
- **Baris `(unknown)`** = baris tanpa token dan tanpa nama model; isinya hanya
  prompt/sesi:
  - **Hermes:** SEMUA prompt Hermes ada di sini. Wrapper mencatat prompt
    terpisah dari token, jadi baris model Hermes selalu `prompts=0`.
  - **Claude:** prompt yang belum dibalas + baris penanda sesi aktif.
  - **Codex / OpenCode:** jarang; prompt tanpa token.

  Karena itu token per prompt dihitung per **agent** (Σ token ÷ Σ prompt SEMUA
  baris, termasuk `(unknown)`). Token per prompt per model Hermes tidak bermakna.
- **`sessions` di `daily_by_model.csv` = sesi unik per model — jangan
  dijumlahkan** (satu sesi memakai beberapa model). Sesi unik per hari ada di
  `daily.csv`.

## Data dir & pipeline

Semua output ada di **data dir**, bukan di folder skill (folder skill boleh
di-sync/ditimpa; data jangan ikut):

```
<OMARCHY_USAGE_DATA>/            (resolved; see Prerequisites / Config)
  snapshots/<tanggal>.json     snapshots/archive/ (tidak dibaca)   archive/ (data lama)
  daily.csv  daily_by_model.csv  report.md
  cost_daily.csv  cost_by_model.csv  cost_report.md
  metrics_daily.csv  metrics_by_agent.csv  metrics_report.md
  weekly.csv  report_week.md  cron.log
```

Env (nilai dan default: tabel di Prerequisites / Config):
- `OMARCHY_USAGE_DATA` — data dir.
- `OMARCHY_USAGE_PRICING_CACHE` — cache harga runtime.
- `OMARCHY_USAGE_PRICING_SEED` — seed harga lokal opsional, read-only (default `references/pricing.json`, gitignored; boleh tidak ada).
- `ARTIFICIAL_ANALYSIS_API_KEY` — kunci Data API gratis Artificial Analysis. **Hanya dari env var**; jangan tulis ke file, jangan minta user menempelkannya di chat. Tanpa kunci: tidak ada panggilan jaringan (pakai cache/seed) dan satu baris petunjuk dicetak. Kunci gratis: https://artificialanalysis.ai/api-key-management-redirect
- `OMARCHY_TASKS_FILE` — task signal file.
- `OMARCHY_PATH` — install Omarchy.

**Tes: arahkan semuanya ke dir temp.**

Urutan pipeline (tiap tahap membaca output tahap sebelumnya):

```bash
S=<folder-skill>/scripts     # mis. $HOME/.hermes/skills/omarchy-agent-usage/scripts
python3 $S/collect.py                       # 1. scan + snapshot hari ini + daily*.csv + report.md
python3 $S/cost.py --report                 # 2. biaya (fetch harga live; --offline = cache/seed)
python3 $S/metrics.py --report --offline    # 3. metrik (pakai harga dari tahap 2)
python3 $S/weekly.py                        # 4. ringkasan minggu
python3 $S/collect.py --all                 # 1->4 sekaligus (tambah --offline: tanpa fetch harga)
python3 $S/collect.py --report --all --offline   # bangun ulang semuanya dari snapshot: tanpa scan, tanpa network
```

**Sebelum mengutip angka**, cek stempel di kepala laporan: `Snapshot terbaru`,
mtime `daily_by_model.csv`, dan `fetched_at` harga.
- Kalau snapshot terbaru lebih tua dari kemarin, atau laporan lebih tua dari
  `daily_by_model.csv`, jalankan ulang pipeline atau sebut tanggalnya.
- Kalau laporan bertanda `INCOMPLETE`, jangan sajikan totalnya sebagai biaya
  lengkap.

## Membangun riwayat (`collect.py`)

1. **Snapshot harian.** Menjalankan semua wrapper
   `$OMARCHY_PATH/bin/omarchy-agent-usage-*` secara paralel (daftar agent dari
   folder itu, tanpa `update`), lalu scanner internal untuk
   Hermes/Claude/Codex/OpenCode, dan menulis `snapshots/<hari ini>.json`.
   - **Efek samping network:** beberapa wrapper memanggil API limit provider.
   - Tidak ada fetch harga di tahap ini.
2. **Kedalaman backfill tergantung sumber.**
   - Hermes/Claude/OpenCode: seluruh riwayat lokal yang masih ada.
   - **Codex: hanya 30 hari terakhir** (jendela rollout upstream).
   - Snapshot lama tetap menyimpan hari yang sudah tak terlihat. **Jangan hapus
     snapshot lama.**
3. **Penggabungan.** Snapshot terbaru menang per (hari, agent), kecuali scan
   tidak lengkap (`complete: false`) tidak pernah menimpa scan lengkap.
4. **Cek paritas.**
   - Total baris tiap agent lokal dibandingkan dengan `recentDays` record-nya
     (7 hari). Selisih dicatat (`! parity …`) dan ditulis di `report.md`.
   - Selisih di luar hari berjalan = komposisi scan skill drift dari wrapper
     upstream. Laporkan, dan jangan percaya pecahan per model untuk hari itu.
5. **Idempoten.** Dua kali di hari yang sama menimpa snapshot yang sama.
6. **Opsi.** `--report` membangun ulang CSV + report dari snapshot tanpa scan.
   `--days N` mengubah rentang `report.md` (default 7).

## Jadwal harian (opsional)

Riwayat hanya terisi di hari skill dijalankan, jadi untuk tracking harian
pasang job terjadwal **tanpa LLM** yang menjalankan `collect.py --all`
(mis. tiap hari 23:45). Skill tidak membuat job sendiri; tanyakan user dulu.

- Perintah job: `python3 <folder-skill>/scripts/collect.py --all`. Boleh dibungkus
  script shell kecil yang mengarahkan stdout/stderr ke `<data dir>/cron.log`.
- Pemicu: cron, systemd timer, atau scheduler agent (mis. `hermes cron`)
  dengan mode tanpa agent/LLM. Stdout kosong saat sukses.
- **Jangan batasi jumlah pengulangan** (mis. `--repeat N`): sebagian scheduler
  berhenti diam-diam setelah N kali, sehingga riwayat harian bolong.
- Setelah dipasang, cek `<data dir>/cron.log` dan stempel `Snapshot terbaru`
  di `report.md` esok harinya.

### Simulasi biaya (`cost.py`)

Mengubah `daily_by_model.csv` menjadi estimasi biaya pakai harga **Artificial
Analysis** (Data API gratis). Laporan wajib memuat atribusi
"Source: Artificial Analysis (artificialanalysis.ai)" dengan tautan
<https://artificialanalysis.ai/>, plus "Based on data from Artificial Analysis"
dan "Created by omarchy-agent-usage, not by Artificial Analysis. Artificial Analysis does not endorse this report/tool" untuk angka turunan
(sudah otomatis di `cost`/`metrics`; sertakan juga bila Anda menyajikan angka
harga di tempat lain). **Kartu/grafik yang dibagikan ke publik juga wajib
menampilkan logo Artificial Analysis** (syarat Data Platform Terms); logo tidak
disertakan di repo ini, ambil dari situs mereka. Hanya simulasi: Claude Code / Codex / OpenCode sebenarnya
langganan, bukan meteran.

**Format biaya = tepat 2 angka desimal** (`$168.23`, `$0.00`, `$1.70`), bukan
4 atau 6 desimal, dan jangan buang trailing zero. Berlaku di `cost_report.md`,
`cost_daily.csv`, `cost_by_model.csv`, stdout CLI, dan kolom biaya di `metrics.py`
(`costUSD`, `costPerTask`, total, proxy). Pakai `cost.fmt()` untuk angka USD.
Rasio (cache-hit, output share) dan token **tidak** ikut aturan ini.

```bash
python3 scripts/cost.py 2026-01-01          # pecahan per model untuk 1 tanggal
python3 scripts/cost.py                     # rekap per hari (partial ditandai)
python3 scripts/cost.py --report            # tulis cost_daily.csv + cost_by_model.csv + cost_report.md
python3 scripts/cost.py --offline           # tanpa API (cache, lalu seed)
python3 scripts/cost.py --report --strict   # exit 3 bila INCOMPLETE
```

- **Urutan harga:** seed lokal opsional (`OMARCHY_USAGE_PRICING_SEED`) ← cache
  `~/.cache/omarchy-agent-usage/pricing.json` ← Data API AA.
  - API hanya dipanggil bila `ARTIFICIAL_ANALYSIS_API_KEY` di-set, bukan
    `--offline`, dan cache API lebih tua dari 24 jam (tier gratis: 100 request
    per 24 jam; 1 fetch = 1-2 request).
  - Fetch hanya menimpa slug yang ada di hasil fetch.
  - Slug yang hilang tetap memakai harga terakhirnya, ditandai `stale` +
    `last_seen`.
  - File seed tidak pernah ditulis.
- `cacheReadInputTokens` → **cacheHitPrice**; cache write → cacheWritePrice.
  Kalau AA tidak punya harga cache: cacheHit = input, cacheWrite = 1.25 × input
  (dicatat di laporan).
- Model `:free`/`-free` → `$0`, diperiksa SEBELUM `MODEL_MAP`. Padanan
  berbayarnya tampil di seksi **"Model free — estimasi proxy"**, bukan bagian
  total.
- **Model berbayar tanpa harga** → di luar total, tapi **dicantumkan** di seksi
  **"Tidak terhitung"** (token + alasan), dan hari yang memuatnya ditandai
  `partial`.
  - Kalau > 1% token berbayar tak terharga → banner **`INCOMPLETE`** (stdout +
    laporan).
  - Baris tanpa token (prompt saja) bukan "tak terharga".
- Model yang dipatok ke slug **successor** (slug aslinya hilang dari AA)
  dicantumkan di laporan. Saat ini: `gpt-6.1-sol → gpt-6-2-sol` (harga sama)
  dan `gpt-6-astra → gpt-6-2-astra` (successor lebih murah dari harga lama; lihat
  `references/pricing-sources.md`).
- Jangan campur cache read ke "token aktual"; laporkan terpisah.
- **AA hanya punya harga saat ini, bukan historis.** Laporan biaya = revaluasi
  pemakaian historis ke harga tanggal fetch. Selalu sebut `fetched_at`.
  - Pertanyaan "model X minggu ini lebih murah dari minggu lalu?" tidak bisa
    dijawab dari AA; butuh snapshot Wayback dari halaman harga provider sendiri (bukan Artificial Analysis) / newsroom provider.

## Metrik dashboard (`metrics.py`, Lapisan A)

Analitik offline dari `daily_by_model.csv` + harga + `tasks.jsonl`. Plugin QML
`omarchy-ai-usage` terpisah: kontraknya cuma kuota.

```bash
python3 scripts/metrics.py [YYYY-MM-DD] [--report] [--offline] [--strict]
```

| Metrik | Rumus | Catatan |
|---|---|---|
| Cost per agent | Σ biaya per agent per hari | free = $0 *diketahui*; `partial` (+?) kalau ada token tak terharga |
| Cache hit ratio | `cacheRead / (input + cacheRead + cacheWrite)` | porsi input sisi-prompt dari cache; output tidak ikut |
| Token per prompt | non-cache: `(input + output) / prompts`; total: semua token / prompts | prompts = SEMUA baris agent-hari, termasuk `(unknown)` |
| Cost per task | biaya agent ÷ bobot task agent (`ok`=1, `partial`=0.5, `fail`=0) | task = sesi unik di `tasks.jsonl`; agregat tanggal/periode = Σ biaya ÷ Σ bobot **hanya** atas agent-hari yang punya baris task |
| Output token | `outputTokens` + % dari total | |
| Daily trend | delta vs hari **kalender** sebelumnya; avg7d kalender (hari nol ikut) | avg7d muncul setelah 7 hari sejak pemakaian pertama agent |

Output: `metrics_daily.csv`, `metrics_by_agent.csv`, `metrics_report.md`.

- Catatan `costPerTask`:
  - `n/a (no tasks)`
  - `n/a (all tasks failed, weight 0)`
  - `n/a (no usage data)`: task ada tapi snapshot belum memuat hari itu
  - `n/a (unpriced tokens)`
  - `x.xxxx (free)`: semua pemakaian gratis
- **Hanya agent yang punya hook penulis yang punya task rows** (mis. OpenCode setelah plugin
  diperbaiki). Cost per task Claude/Codex = `n/a (no tasks)`. Jangan pernah
  menyebut satu angka "cost per task semua agent".
- **Token/cost ≠ produktivitas.** Laporan wajib menyebut ini: agent dinilai
  dari pekerjaan yang berhasil diselesaikan, bukan token atau biaya.
- **Cost per task jangan diganti "cost per prompt"** tanpa label jelas.

## Task signal

`OMARCHY_TASKS_FILE` (default `~/.local/state/omarchy/agents/tasks.jsonl`; append-only). Tulis dengan
`omarchy-tasklog record --agent <a> --status ok|partial|fail [--session ID]`
(shim di `~/.local/bin`, memanggil `scripts/tasklog.py`).
`tasklog.py summary` menampilkan jumlah task per hari setelah dedupe sesi; tidak
menghitung biaya.

Status hook: tiap mesin berbeda. Contoh generik ada di
`references/task-signal.md`. **Kalau `references/task-signal.local.md` ada,
baca juga**: itu catatan hook mesin ini (gitignored). Yang berlaku umum:
- Hook akhir-giliran (mis. `on_session_end`, `Stop`, `session.idle`) fire
  **per giliran**, jadi satu sesi bisa menulis puluhan baris; pembaca
  men-dedupe per (agent, sesi).
- Pastikan ada baris `"agent": "<nama>"` di `tasks.jsonl` sebelum mengandalkan
  task rows agent itu. Tanpa hook, agent tersebut tidak punya task rows.

Detail skema & semantik: `references/task-signal.md`. Saat tes, set
`OMARCHY_TASKS_FILE` ke file temp.

## Laporan minggu (`weekly.py`)

`python3 scripts/weekly.py [--week-start YYYY-MM-DD]`. Hanya membaca snapshot
(tanpa scan ulang).
- Jendela = 7 hari kalender mulai `--week-start` (default: Senin minggu
  snapshot terbaru), dipotong di tanggal snapshot terbaru. Minggu berjalan
  → < 7 hari, dan judul menandai "belum lengkap".
- Start setelah snapshot terbaru → exit 2.

## Grafik / video

Gaya bawaan kartu/grafik ada di `references/visual-preferences.md`. Biaya per
agent untuk grafik **selalu diambil dari `cost_by_model.csv` / `cost_daily.csv`**
(hasil `cost.py`, harga input/output/cache terpisah). Jangan hitung ulang
"token × harga" di kode grafik, karena angkanya akan berbeda dari laporan.

## Pitfalls

- **`spec_from_file_location` gagal untuk wrapper `omarchy-agent-usage-*`.**
  File-nya tanpa ekstensi `.py`, jadi `spec.loader` bernilai `None`. Pakai
  `importlib.machinery.SourceFileLoader` + `spec_from_loader`
  (`common.load_collector`).
- **`scan_codex_routed("codex")` mengembalikan 0 baris** saat
  `codex_provider_urls()` kosong. Rollout native dibaca lewat
  `codex_rollouts(..., native=True)` lalu disaring provider/owner seperti wrapper.
- **Baris di-bucket per tanggal lokal** (`local_day`), jadi sesi yang melewati
  tengah malam terpecah di dua hari.
- **Cache scan.** `collect.py` memanggil scanner langsung; `cached_scan` (cache
  per hari) hanya dipakai wrapper. Tetapi `claude_code_usage` dan
  `codex_rollouts` menulis index/cache bersama di `~/.cache/omarchy/agent-usage/`,
  jadi jalan kedua tetap lebih cepat.
- **Angka satu hari berubah setelah kolektor dijalankan ulang.** Jangan anggap
  biaya/token satu hari final sebelum hari itu lewat; sebutkan tanggal snapshot
  saat melapor.
- **Slug AA drift.** Kalau sebuah model muncul di "Tidak terhitung" dengan
  alasan "slug … tidak ada di harga", atau ada peringatan `! slug AA … stale`,
  slug AA-nya berubah.
  - Cari slug penggantinya di cache harga, lalu perbarui `MODEL_MAP` (+
    `SUCCESSOR_OF` bila penerus) dan tabel di `references/pricing-sources.md`.
  - **Jangan laporkan total sebagai lengkap sebelum itu.**
- **Fetch API gagal / kunci tidak ada.** `cost.py` memakai cache (lalu seed) dan
  mencetak peringatan. Jangan menebak harga, jangan scrape halaman AA.
- **Model `:free`/`-free` harus diperiksa SEBELUM `MODEL_MAP`.** Jangan pernah
  memasukkan model free ke `MODEL_MAP`; letakkan padanannya di `PROXY`.
- **Menambah metrik:** tambahkan ke `aggregate_by_day_agent` → `metric_values`
  → `COLUMNS`/`CSV_FIELDS` di `metrics.py`. Semua presenter (CLI, CSV, report)
  memakai builder yang sama.
- **`cost per task` = biaya per sesi, bukan per tugas semantik.**
- **Jangan menulis data ke folder skill.** Semua script menulis ke data dir;
  seed harga (`references/pricing.json`, lokal) tidak pernah ditulis.

## Support files

- `references/collector-internals.md`: signature scanner, cara memuat
  kolektor, komposisi scan per agent, resolusi owner.
- `references/pricing-sources.md`: Data API AA, pemetaan harga, successor,
  footnote proxy, cache harga.
- `references/task-signal.md`: skema `tasks.jsonl`, dedupe, semantik, contoh hook
  generik. `references/task-signal.local.md` (gitignored, bila ada): hook mesin ini.
- `references/visual-preferences.md`: gaya bawaan grafik/video usage (kartu 9:16, aturan angka biaya).
- `scripts/common.py`: path, IO atomik, merge snapshot, pembaca task.
- `scripts/collect.py`: kolektor (snapshot + CSV + report + cek paritas; `--all`).
- `scripts/cost.py`: simulasi biaya pay-as-you-go.
- `scripts/metrics.py`: metrik dashboard (Lapisan A).
- `scripts/weekly.py`: ringkasan mingguan dari snapshot.
- `scripts/tasklog.py`: tulis/baca `tasks.jsonl` (`record`, `summary`, `validate`).
- `tests/`: tes fixture (`python3 -m unittest discover -s tests -v`).
