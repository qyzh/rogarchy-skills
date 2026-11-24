# blog-post

## Apa ini

Skill untuk menulis satu blog post Markdown yang bersitasi. Urutannya: riset dulu (paket riset dengan peta sikap pro/kontra dan blok *Balance*), lalu draf, lalu penilaian dengan rubrik. Skill ini berhenti di satu post; tidak menerbitkan, commit, atau memposting.

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Pengguna meminta blog post, artikel, atau penjelasan bersumber untuk dipublikasikan.
- Pengguna ingin statistik terkini dan celah dari kompetitor, lalu draf yang bisa disunting.

Tidak dipakai untuk:

- Makalah akademik (`academic-research-writer`).
- Catatan YouTube (`ytsum` / `youtube-content`).
- Menyimpan URL yang sudah ada ke vault (`web-article-to-vault`).
- Brief aset sosial (`content-brief-curation`).
- Tugas koding yang kebetulan memuat kata "blog".

## Kebutuhan

Skill di luar repo ini (pasang terpisah):

| Skill | Status | Fungsi |
|---|---|---|
| `grounded-citations` | **Wajib** | Pencatatan sumber (`sources.py`), render sitasi `[n]`, dan `verify`. |
| `humanizer` | **Wajib** | Perapian prosa sebelum verifikasi. |
| `content-brief-curation` | Hanya rute | Disebut sebagai tujuan alih untuk brief aset sosial. |
| `academic-research-writer` | Hanya rute | Disebut sebagai tujuan alih untuk makalah akademik. |
| `web-article-to-vault` | Hanya rute | Disebut sebagai tujuan alih untuk menyimpan artikel. |
| `youtube-content` | Hanya rute | Disebut (bersama `ytsum`, yang ada di repo ini) sebagai tujuan alih untuk catatan YouTube. |

Alat runtime: Python (untuk `sources.py` milik `grounded-citations`), `curl`, dan akses pencarian web dari agent. Skill ini sendiri tidak punya skrip.

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `OUT` | Folder keluaran draf, paket riset, dan ledger sumber | `$HOME/blog-posts` |

Path absolut yang disebut pengguna di permintaan lebih diutamakan daripada `OUT`. Skill tidak menulis ke vault catatan kecuali pengguna menyebut vault itu.

Nilai di atas juga bisa disimpan di berkas pengaturan `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (lewat [`rogarchy-setup`](../rogarchy-setup/README.md)); env var tetap menang, lalu berkas itu, lalu default.

## Contoh pemakaian

```text
Tulis blog post tentang dampak caching HTTP pada Core Web Vitals, dalam bahasa Indonesia.
```

Agent melakukan pra-pemeriksaan, merencanakan kueri pendukung dan kontra, lalu menulis paket riset dan **berhenti** untuk persetujuan. Setelah dilanjutkan, hasilnya `<slug>_<tanggal>.md` berisi jawaban singkat, isi, bagian "When it doesn't hold" / "Kapan ini tidak berlaku", dan daftar sumber, ditambah `_research-<slug>-<tanggal>.md` dan `.sources-<slug>-<tanggal>.json`. Skor riset (≥70) dan skor draf (≥80) dilaporkan di chat.

```text
Tulis post tentang Rust untuk backend dev pemula, sampai selesai.
```

Kata "sampai selesai" membuat agent tidak berhenti di antara fase.

## Isi folder

```
blog-post/
├── SKILL.md                      # instruksi untuk agent
├── references/
│   ├── research-quality.md       # tingkat sumber, pra-pemeriksaan, format peta sikap dan blok Balance, rubrik riset
│   ├── voice-personal.example.md # templat gaya personal (salin ke voice-personal.local.md)
│   └── voice-personal.local.md   # gaya personal Anda (opsional, gitignored)
└── templates/
    └── post.md                   # kerangka draf (jawaban singkat, isi, Kapan ini tidak berlaku, Sources)
```

## Kredit

Diadaptasi dari [AgriciDaniel/claude-blog](https://github.com/AgriciDaniel/claude-blog) (MIT): disiplin riset dan kutipan, serta `references/research-quality.md` (yang juga merujuk [last30days-skill](https://github.com/mvanhorn/last30days-skill), MIT). Teks lisensi dan hak cipta asli ada di [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

---

Versi 0.2.0 · Lisensi MIT · [README repo](../README.md)
