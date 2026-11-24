# rogarchy-skills

Koleksi pribadi skill agent dalam format `SKILL.md`. Satu repo, satu folder per skill.

> Skill di repo ini **hanya diuji di Hermes Agent**. Agent lain yang membaca
> folder skill berformat `SKILL.md` seharusnya bisa memakainya, tetapi belum diuji.

## Daftar skill

| Skill | Deskripsi | Versi | Folder tambahan |
|---|---|---|---|
| [`blog-post`](blog-post/README.md) | Menulis satu blog post bersitasi: riset dulu, draf kedua, penilaian ketiga. | 0.2.0 | `references/`, `templates/` |
| [`bmlink`](bmlink/README.md) | Menyimpan URL sebagai satu baris di tabel Markdown bookmark. Tanpa catatan per link. | 1.0.0 | - |
| [`dither-data-viz`](dither-data-viz/README.md) | Membuat grafik ber-dither (Bayer) di canvas dengan label HTML asli. Keluarannya `index.html` dan satu PNG per canvas. Ada 5 desain kartu (A–E), default B. | 0.4.0 | `scripts/`, `templates/`, `design-options/` |
| [`kamus`](kamus/README.md) | Menyimpan satu istilah sebagai satu note definisi di folder kamus, dengan arti yang diverifikasi ke KBBI/Wiktionary. | 1.0.0 | `references/` (opsional, lokal) |
| [`note-to-quote`](note-to-quote/README.md) | Memilih satu gagasan dari note atau rangkuman menjadi quote singkat, lengkap dengan konteks dan atribusi. | 1.0.0 | `references/` |
| [`omarchy-agent-usage`](omarchy-agent-usage/README.md) | Riwayat dan laporan pemakaian token agent AI lokal di Omarchy: per hari × per model, kuota, simulasi biaya, metrik. Hanya Linux/Omarchy. | 0.3.0 | `references/`, `scripts/`, `tests/` |
| [`ytsum`](ytsum/README.md) | Mengubah satu URL YouTube menjadi satu file rangkuman Markdown yang setia pada isi video. | 3.0.0 | `scripts/` |

Kebutuhan runtime:

- `dither-data-viz`: Node.js, Python 3, dan Chrome/Chromium (diatur lewat `CHROME_BIN` bila tidak ada di `PATH`) untuk ekspor PNG.
- `omarchy-agent-usage`: Linux dengan Omarchy (wrapper `omarchy-agent-usage-*`) dan Python 3 (pustaka standar). Internet opsional (harga dari Data API gratis Artificial Analysis, perlu `ARTIFICIAL_ANALYSIS_API_KEY`; tanpa kunci tidak ada panggilan jaringan; `--offline` memakai cache/seed).
- `ytsum`: `yt-dlp`, Python 3, dan skill `youtube-content` (untuk mengambil transkrip).
- `bmlink`, `blog-post`, `note-to-quote`, `kamus`: tidak ada skrip. Sebagian skill menyebut skill lain di `related_skills`; skill itu opsional dan tidak disertakan di repo ini.
- Lokasi keluaran bisa diatur lewat environment variable (default dipakai bila tidak diset):
  - `bmlink`: `BMLINK_FILE` (default `$HOME/bookmarks/linksaved.md`), `BMLINK_TZ` (default zona waktu sistem).
  - `ytsum`: `YTSUM_OUTPUT_DIR` (default `$HOME/ytsum`), `YTSUM_SCRATCH_DIR` (default `${TMPDIR:-/tmp}/ytsum-scratch`).
  - `kamus`: `KAMUS_DIR` (default `$HOME/kamus`).
  - `blog-post`: `OUT` (default `$HOME/blog-posts`).
  - `omarchy-agent-usage`: `OMARCHY_USAGE_DATA` (default `~/.local/state/omarchy/agents/usage-history`), `ARTIFICIAL_ANALYSIS_API_KEY`, `OMARCHY_USAGE_PRICING_CACHE`, `OMARCHY_USAGE_PRICING_SEED`, `OMARCHY_TASKS_FILE`, `OMARCHY_PATH`.
- Semua skill memakai author `qyzh, Hermes Agent`.

## Skill pendukung

Beberapa skill merujuk skill lain yang **tidak ada di repo ini**. Pasang terpisah di agent Anda bila perlu.

| Skill pendukung | Status | Dipakai oleh |
|---|---|---|
| `grounded-citations` | Wajib | `blog-post` (ledger sumber, render dan verifikasi sitasi) |
| `humanizer` | Wajib | `blog-post` (perapian prosa) |
| `youtube-content` | Wajib | `ytsum` (mengambil transkrip) |
| `omarchy-plugin-authoring` | Hanya rute | `omarchy-agent-usage` (tujuan alih untuk membuat plugin tampilan usage) |
| `content-brief-curation` | Hanya rute | `blog-post` (tujuan alih untuk brief aset sosial) |
| `academic-research-writer` | Hanya rute | `blog-post` (tujuan alih untuk makalah akademik) |
| `web-article-to-vault` | Hanya rute | `blog-post`, `bmlink` (tujuan alih untuk menyimpan artikel) |

"Hanya rute" berarti skill hanya disebut sebagai tujuan alih untuk permintaan di luar cakupan; skill tetap berjalan tanpanya.

## Struktur

```
<nama-skill>/
├── SKILL.md        # wajib, untuk agent
├── README.md       # wajib, untuk manusia
├── references/     # opsional
├── templates/      # opsional
└── scripts/        # opsional
```

Nama folder **harus** sama dengan field `name:` di frontmatter `SKILL.md`.

## Install (symlink)

Repo ini sumber kebenaran. Jangan menyalin isi skill; buat symlink supaya update cukup `git pull`.

```bash
git clone <repo-url> <path-ke-repo>
```

### Hermes Agent

```bash
mkdir -p ~/.hermes/profiles/<profil>/skills

# semua skill sekaligus
for d in <path-ke-repo>/*/; do
  [ -f "$d/SKILL.md" ] || continue
  ln -sfn "${d%/}" ~/.hermes/profiles/<profil>/skills/"$(basename "$d")"
done

# satu skill
ln -sfn <path-ke-repo>/<nama-skill> ~/.hermes/profiles/<profil>/skills/<nama-skill>
```

### Agent lain

Ganti tujuan dengan direktori skills milik agent tersebut.

```bash
mkdir -p <direktori-skills-agent>

# semua skill sekaligus
for d in <path-ke-repo>/*/; do
  [ -f "$d/SKILL.md" ] || continue
  ln -sfn "${d%/}" <direktori-skills-agent>/"$(basename "$d")"
done

# satu skill
ln -sfn <path-ke-repo>/<nama-skill> <direktori-skills-agent>/<nama-skill>
```

## Update

```bash
cd <path-ke-repo> && git pull
```

Semua symlink otomatis menunjuk versi baru.

## Menambah skill baru

1. Buat folder `<nama-skill>/` di root repo.
2. Isi `SKILL.md` dengan frontmatter `name` yang sama persis dengan nama folder.
3. Tambah `references/`, `templates/`, atau `scripts/` bila perlu.
4. Tulis `<nama-skill>/README.md` untuk manusia dengan bagian yang sama seperti skill lain: Apa ini, Kapan dipakai / tidak dipakai, Kebutuhan, Konfigurasi, Contoh pemakaian, Isi folder, dan baris versi, lisensi, tautan ke `../README.md`. Jangan mengubah isi `SKILL.md` untuk keperluan ini.
5. Bila mengadaptasi karya orang lain, tambahkan entri di `THIRD_PARTY_NOTICES.md` (sumber, berkas, hak cipta, teks lisensi) dan bagian "Kredit" di README skill.
6. Tambah skill ke tabel di README root (nama berupa tautan ke README skill) dan ke "Skill pendukung" bila memakai skill di luar repo.
7. Commit, lalu symlink ke direktori skills agent.

## Lisensi

Karya sendiri: MIT © qyzh, lihat [LICENSE](LICENSE). Bagian yang diadaptasi dari pihak ketiga tetap berlisensi aslinya, lihat [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Ini atribusi open source yang umum, bukan nasihat hukum.

## Rilis

Versi per skill ditandai dengan tag `<nama-skill>/vX.Y.Z` (mis. `blog-post/v0.2.0`).
