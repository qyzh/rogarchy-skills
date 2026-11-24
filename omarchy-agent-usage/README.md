# omarchy-agent-usage

## Apa ini

Skill yang membaca pemakaian token agent AI lokal di Omarchy (Hermes, Claude Code, Codex, OpenCode, grok, agy) lalu menyusunnya menjadi riwayat dan laporan: token per hari × per model, persentase kuota/limit, simulasi biaya pay-as-you-go, metrik (cache hit, token per prompt, cost per task), dan ringkasan mingguan. Semua data ditulis ke folder data di luar folder skill. Harga berasal dari Artificial Analysis (lihat Kredit).

**Hanya Linux dengan Omarchy.** Skill membaca wrapper `omarchy-agent-usage-*` dan store lokal agent; tanpa Omarchy skill ini tidak berguna.

## Kapan dipakai / tidak dipakai

Dipakai bila Anda meminta:

- Cek token yang terpakai, kuota atau limit habis, agent mana yang paling boros.
- Menyimpan riwayat pemakaian per hari, laporan minggu ini.
- Simulasi biaya bila pemakaian dibayar per token, cache hit ratio, token per prompt, cost per task.

Tidak dipakai bila:

- Anda ingin membuat plugin Omarchy yang menampilkan usage (pakai `omarchy-plugin-authoring`).
- Anda butuh dashboard billing cloud provider. Skill ini hanya membaca store lokal.

Skill tidak menjalankan `omarchy-agent-usage-update` kecuali diminta, karena perintah itu bisa mengganti akun yang sedang login.

## Kebutuhan

| Kebutuhan | Status | Fungsi |
|---|---|---|
| Linux + Omarchy | **Wajib** | Menyediakan wrapper `omarchy-agent-usage-*` di `$OMARCHY_PATH/bin`. |
| Python 3 | **Wajib** | Menjalankan skrip di `scripts/`. Hanya pustaka standar. |
| Akses internet + `ARTIFICIAL_ANALYSIS_API_KEY` | Opsional | Mengambil harga dari Data API gratis Artificial Analysis. Tanpa kunci tidak ada panggilan jaringan; skill memakai cache/seed. |
| `omarchy-plugin-authoring` (di luar repo) | Hanya rute | Tujuan alih untuk membuat plugin tampilan usage. |
| [`dither-data-viz`](../dither-data-viz/README.md) (repo ini) | Opsional | Membuat kartu/grafik dari CSV keluaran skill ini. |

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `OMARCHY_USAGE_DATA` | Folder data (snapshot, CSV, laporan) | `~/.local/state/omarchy/agents/usage-history` |
| `ARTIFICIAL_ANALYSIS_API_KEY` | Kunci Data API gratis Artificial Analysis ([ambil di sini](https://artificialanalysis.ai/api-key-management-redirect)). Hanya dari env var, jangan ditulis ke file | (kosong: tanpa panggilan jaringan) |
| `OMARCHY_USAGE_PRICING_CACHE` | Cache harga hasil fetch API (dipakai ulang 24 jam) | `~/.cache/omarchy-agent-usage/pricing.json` |
| `OMARCHY_USAGE_PRICING_SEED` | Seed harga lokal opsional, read-only (tidak ikut repo) | `references/pricing.json` (gitignored) |
| `OMARCHY_TASKS_FILE` | File sinyal task (`tasks.jsonl`) | `~/.local/state/omarchy/agents/tasks.jsonl` |
| `OMARCHY_PATH` | Lokasi instalasi Omarchy | `/usr/share/omarchy` |

Untuk tes, arahkan semuanya ke folder sementara.

## Contoh pemakaian

```text
Berapa token yang kupakai minggu ini, dan kalau dibayar per token jadinya berapa?
```

Menjalankan pipeline secara manual (dari folder repo):

```bash
S=omarchy-agent-usage/scripts
python3 $S/collect.py --all             # scan + snapshot + CSV + biaya + metrik + mingguan
python3 $S/collect.py --report --all --offline   # bangun ulang dari snapshot, tanpa scan dan network
python3 $S/cost.py 2026-01-01           # pecahan biaya per model untuk satu tanggal
python3 $S/weekly.py                    # ringkasan minggu berjalan
```

Menjalankan tes (tidak menyentuh state asli, network dimatikan):

```bash
cd omarchy-agent-usage && python3 -m unittest discover -s tests -v
```

Untuk tracking harian, pasang job terjadwal tanpa LLM yang menjalankan `collect.py --all`; langkahnya ada di SKILL.md bagian "Jadwal harian".

## Isi folder

```
omarchy-agent-usage/
├── SKILL.md                       # instruksi untuk agent
├── references/
│   ├── collector-internals.md     # signature scanner, komposisi scan per agent
│   ├── pricing-sources.md         # sumber harga AA, pemetaan model, successor, proxy
│   ├── pricing.json               # seed harga lokal opsional (gitignored, tidak ada di repo)
│   ├── task-signal.md             # skema tasks.jsonl, dedupe, contoh hook generik
│   ├── task-signal.local.md       # catatan hook mesin Anda (opsional, gitignored)
│   └── visual-preferences.md      # gaya bawaan kartu/grafik usage
├── scripts/
│   ├── common.py                  # path, IO atomik, merge snapshot, pembaca task
│   ├── collect.py                 # kolektor: snapshot + CSV + report + cek paritas
│   ├── cost.py                    # simulasi biaya pay-as-you-go
│   ├── metrics.py                 # metrik dashboard
│   ├── weekly.py                  # ringkasan mingguan
│   └── tasklog.py                 # tulis/baca tasks.jsonl
└── tests/                         # tes unittest + fixture
```

## Kredit

Sebagian kecil kode di `scripts/collect.py` (regex dan predikat pendeteksi billing) disalin dari wrapper `omarchy-agent-usage-*` milik [Omarchy](https://github.com/omacom/omarchy) (MIT, © David Heinemeier Hansson); lihat [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Tidak berafiliasi dengan atau didukung oleh Omarchy/Basecamp.

Source: [Artificial Analysis (artificialanalysis.ai)](https://artificialanalysis.ai/). Harga token diambil lewat Data API gratis mereka memakai kunci Anda sendiri (`ARTIFICIAL_ANALYSIS_API_KEY`), disimpan di cache lokal, dan tidak ikut di repo ini. Setiap laporan biaya mencantumkan "Source: Artificial Analysis (artificialanalysis.ai)" dengan tautan, "Based on data from Artificial Analysis", dan "Created by omarchy-agent-usage, not by Artificial Analysis. Artificial Analysis does not endorse this report/tool". Kartu atau grafik yang dibagikan ke publik juga wajib menampilkan logo Artificial Analysis (syarat Data Platform Terms; logo tidak disertakan di repo). Rincian sumber ada di [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md); pemakaian API tunduk pada syarat Artificial Analysis. Ini bukan nasihat hukum.

---

Versi 0.3.0 · Lisensi MIT · [README repo](../README.md)
