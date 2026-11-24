# dither-data-viz

## Apa ini

Skill untuk membuat grafik ber-dither (pola Bayer) di canvas, dengan label, legenda, dan keterangan berupa HTML asli. Keluarannya `index.html` yang bisa dibuka lewat `file://` plus satu PNG opak per canvas grafik. Untuk kartu pemakaian/pangsa model ada 5 desain (A–E); bila tidak disebut, agent bertanya dulu, dan default-nya B "Ledger First".

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Anda ingin grafik dither/Bayer/grainy di canvas sebagai HTML dan PNG.
- Datanya bagian dari keseluruhan (default, donat), deret waktu, skor (radar), tren mini, atau progres 0–1.
- Anda meminta kartu pemakaian token/kuota/biaya agent (desain A–E).

Tidak dipakai (alihkan) untuk:

| Permintaan | Skill |
|---|---|
| Graf node–edge / jaringan / wikilink | `graph-visualization` |
| Grafik 3D / three.js | `threejs-data-viz` |
| Gambar infografik | `baoyu-infographic` |
| Laporan HTML Chart.js biasa | `html-data-report` |

Aturan tegasnya: hanya tanda Bayer di canvas (tanpa Chart.js, CDN, SVG `<pattern>`), teks tidak dipanggang ke bitmap, dan nilai tidak pernah dikarang (sel kosong tetap `null`).

## Kebutuhan

| Kebutuhan | Status | Fungsi |
|---|---|---|
| Node.js 22+ | **Wajib** | Menjalankan `scripts/export.mjs`. |
| Chrome/Chromium | **Wajib** | Ekspor PNG headless. Set `CHROME_BIN` bila tidak ada di `PATH`. |
| Python 3 | Wajib untuk kartu B | Menjalankan `scripts/build_donut_card.py`. |
| `web-design-guidelines` (di luar repo) | Dipanggil saat audit | Audit fokus, kontras, reduced-motion, dan nama aksesibel. |
| [`omarchy-agent-usage`](../omarchy-agent-usage/README.md) (repo ini) | Hanya untuk kartu pemakaian | Menyediakan `visual-preferences.md` (gaya bawaan kartu) dan CSV biaya. Hanya Linux/Omarchy. |
| `graph-visualization`, `threejs-data-viz`, `baoyu-infographic`, `html-data-report` | Hanya rute | Tujuan alih untuk permintaan di luar cakupan. |

Kartu pemakaian membutuhkan `daily_by_model.csv` dan `cost_by_model.csv` (serta `cost_daily.csv` untuk menandai hari berbiaya parsial).

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `CHROME_BIN` | Path Chrome/Chromium untuk `export.mjs` | dicari di `PATH` |
| `OMARCHY_USAGE_DATA` | Folder data CSV pemakaian untuk `build_donut_card.py`; opsi `--data-dir` lebih diutamakan | direktori riwayat usage Omarchy, `~/.local/state/omarchy/agents/usage-history` |

## Contoh pemakaian

```text
Buat grafik dither area dari data traffic mingguan ini: Sen 120, Sel 98, Rab 143.
```

Hasil: folder berisi `index.html`, `dither.js`, `scripts/export.mjs`, dan satu PNG bernama dari `spec.name`. Jalankan `node ./scripts/export.mjs index.html` dari folder keluaran untuk mengekspor PNG.

```text
Buat kartu pangsa token per model untuk 2026-01-01 sampai 2026-01-06.
```

Karena desain belum disebut, agent menawarkan opsi A–E (B direkomendasikan; galeri ada di `design-options/index.html`). Untuk B:

```bash
python3 scripts/build_donut_card.py --data-dir <folder-csv> --start 2026-01-01 --end 2026-01-06 --out <folder-keluaran>
```

Hasilnya kartu 1080×1920 gelap: tabel ledger 10 teratas + "Lainnya", satu donat kecil (satu-satunya PNG yang diekspor), strip KPI, total biaya, dan catatan kaki. Agent juga menangkap kartu penuh sebagai PNG.

## Isi folder

```
dither-data-viz/
├── SKILL.md                          # instruksi untuk agent
├── scripts/
│   ├── dither.js                     # mesin dither (globalThis.Dither): area, pie, radar, spark, meter
│   ├── export.mjs                    # ekspor PNG tiap canvas via Chromium headless
│   └── build_donut_card.py           # pembangun kartu "Ledger First" (B) dari CSV pemakaian
├── templates/
│   └── page.html                     # kerangka halaman untuk grafik umum (window.CHARTS / window.CHART)
└── design-options/
    ├── index.html                    # galeri 5 desain
    ├── dither.js                     # salinan mesin untuk pratinjau mandiri
    ├── option-a-donut-refined.html   # A: donat besar, legenda 2 kolom, banner biaya
    ├── option-b-ledger-first.html    # B: tabel ledger sebagai hero (default)
    ├── option-c-cost-banner.html     # C: total biaya raksasa, cincin pangsa biaya
    ├── option-d-split-agent.html     # D: donat + legenda, panel per agent
    └── option-e-dense-dashboard.html # E: grid padat 12 tanda dither
```

Angka di file pratinjau adalah data contoh (fiktif, rentang 2026-01-01..06); jangan dipakai ulang untuk data Anda.

## Kredit

Kartu penggunaan memuat harga turunan dari [Artificial Analysis](https://artificialanalysis.ai/) ("Source: Artificial Analysis (artificialanalysis.ai)" ada di footer kartu). Kartu atau grafik yang dibagikan ke publik juga wajib menampilkan logo Artificial Analysis (syarat Data Platform Terms; logo tidak disertakan di repo).

Mesin dither (`scripts/dither.js`, `design-options/dither.js`) diadaptasi dari [DeepanshuMishraa/dither-kit-rs](https://github.com/DeepanshuMishraa/dither-kit-rs) (MIT OR Apache-2.0; di sini memakai MIT), ditulis ulang ke JavaScript. Teks lisensi dan hak cipta asli ada di [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

---

Versi 0.4.0 · Lisensi MIT · [README repo](../README.md)
