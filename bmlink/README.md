# bmlink

## Apa ini

Skill untuk menyimpan satu URL sebagai satu baris di satu tabel Markdown bookmark. Setiap baris memuat judul, link, domain, tag, catatan, dan tanggal simpan. Skill tidak mengambil isi artikel dan tidak membuat catatan per link.

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Pengguna menjalankan `/bmlink` atau meminta menyimpan link ke daftar bookmark.
- Tidak ada URL di pesan: agent meminta pengguna mengirim link.

Tidak dipakai untuk:

- Catatan bookmark per link (`bookmark-link`).
- Menyimpan link beserta isinya atau dengan rute berkategori (`discord-link-save`).
- Mengarsipkan artikel penuh (`web-article-to-vault`).

## Kebutuhan

- Alat runtime: tidak ada skrip. Agent memakai `date` dan akses tulis ke berkas.
- Skill di luar repo ini: tidak ada yang wajib. `bookmark-link`, `discord-link-save`, dan `web-article-to-vault` hanya disebut sebagai tujuan alih (hanya rute) dan terdaftar di `related_skills`.

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `BMLINK_FILE` | Path tabel bookmark | `$HOME/bookmarks/linksaved.md` |
| `BMLINK_TZ` | Zona waktu untuk tanggal simpan | zona waktu sistem |

Berkas dan folder induknya dibuat saat simpan pertama. File yang disebut pengguna di permintaan lebih diutamakan. Bila lokasi default bukan tempat tabel Anda, set `BMLINK_FILE`; kalau tidak, tabel baru dibuat di lokasi default.

## Contoh pemakaian

```text
/bmlink https://example.com/artikel #ai #tools -- baca nanti
```

Satu baris ditambahkan ke tabel:

```markdown
| Title | Link | Domain | Tags | Note | Saved on |
|---|---|---|---|---|---|
| Artikel | https://example.com/artikel | example.com | #ai #tools | baca nanti | 2026-10-29 |
```

Tag dan catatan hanya diisi dari yang Anda tulis; tidak pernah ditebak. Agent membaca ulang baris itu untuk memastikan tiap sel benar.

```text
/bmlink https://www.example.com/artikel/?utm_source=x
```

Bila URL itu sudah ada (dibandingkan setelah normalisasi: huruf kecil, tanpa `www.`, fragmen, garis miring akhir, dan parameter pelacak), tidak ada baris baru dan agent memberi tahu bahwa link sudah tersimpan.

## Isi folder

```
bmlink/
└── SKILL.md    # instruksi untuk agent
```

---

Versi 1.0.0 · Lisensi MIT · [README repo](../README.md)
