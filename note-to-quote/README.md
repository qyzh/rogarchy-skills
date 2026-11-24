# note-to-quote

## Apa ini

Skill untuk memilih satu gagasan dari satu note atau rangkuman, lalu menjadikannya satu quote singkat yang bisa berdiri sendiri, lengkap dengan konteks dan atribusi. Skill membedakan tiga jenis teks: rumusan editorial, calon kutipan, dan kutipan yang sudah diperiksa pada sumber asli. Keluarannya teks; desain gambar dan publikasi di luar cakupan.

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Anda ingin quote card, teks Instagram Stories, atau pilihan kutipan pembicara dari sebuah note atau rangkuman.
- Anda perlu tahu apakah kalimatnya olahan editorial, calon kutipan, atau kutipan terverifikasi.

Tidak dipakai untuk:

- Membuat gambar atau mendesain frame (pakai skill desain gambar di agent Anda).
- Menerbitkan atau memposting.
- Mencari benang merah lintas banyak note; satu note menghasilkan satu keluaran terpisah, dan banyak note hanya diproses bila diminta.

## Kebutuhan

- Alat runtime: tidak ada. Skill ini tidak punya skrip.
- Skill di luar repo ini: tidak ada. `related_skills` kosong. Untuk visual Story, SKILL.md hanya menyarankan skill desain gambar milik agent Anda (tidak wajib).
- Untuk kutipan asli, agent butuh materi sumber yang benar-benar tersedia (rekaman dengan lokasinya, transkrip yang andal, atau teks asli dengan halaman/paragraf). Tanpa itu, hasilnya tetap berstatus calon kutipan.

## Konfigurasi

Tidak ada. Bahasa default Indonesia dan audiens default pembaca awam; keduanya bisa diubah di permintaan. Bila Anda meminta hasil disimpan, ikuti lokasi yang Anda sebut. Aturan vault pribadi bisa ditaruh di `references/vault-rules.local.md` (templat: `vault-rules.example.md`; [`rogarchy-setup`](../rogarchy-setup/README.md) bisa membuatnya).

## Contoh pemakaian

```text
Baca note-to-quote/SKILL.md dan gunakan untuk note ini.
Pilih satu quote terkuat, jelaskan alasan pemilihannya,
dan sertakan konteks serta sumbernya.
```

Hasil: satu quote utama (default editorial, berlabel "Diolah dari catatan …"), perbandingan singkat kandidat dengan skor 0–2 per kriteria, alasan pemilihan, konteks, kredit publik, caption atau teks pendamping, dan peta sumber internal. Bila note belum cukup utuh, hasilnya `perlu-lengkapi` beserta bahan yang kurang.

```text
Saya mau kutipan asli pembicaranya, bukan rumusan ulang.
```

Agent memakai alur verifikasi pada sumber asli. Bila belum bisa diverifikasi, kalimat ditampilkan sebagai calon kutipan berlabel "Belum diverifikasi", bukan diganti diam-diam dengan rumusan editorial.

## Isi folder

```
note-to-quote/
├── SKILL.md                       # instruksi untuk agent
└── references/
    ├── output-template.md         # template hasil (bagian A–D: pemilihan, teks card, caption, peta sumber)
    ├── vault-rules.example.md     # templat aturan vault (salin ke vault-rules.local.md)
    ├── vault-rules.local.md       # aturan vault pribadi Anda (opsional, gitignored)
    └── examples.md                # contoh: quote editorial, calon kutipan, kutipan berantai, penolakan bahan belum lengkap
```

---

Versi 1.0.0 · Lisensi MIT · [README repo](../README.md)
