---
name: note-to-quote
description: Pilih gagasan dari note atau rangkuman untuk menjadi quote singkat yang dapat berdiri sendiri. Gunakan untuk quote card, teks Instagram Stories, atau memilih kutipan pembicara; bedakan rumusan editorial, calon kutipan, dan kutipan yang telah diperiksa pada sumber asli. Hasil berupa teks beserta konteks dan atribusi.
version: 1.0.0
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [quote, note, editorial, indonesian]
    related_skills: []
---

# Note → Quote

Pilih satu gagasan kuat dari satu note, kemudian hasilkan satu quote utama dengan makna dan sumber yang jelas. Topik tiap note boleh berbeda. Kualitas quote ditentukan oleh kekhususan insight dan ketepatan makna, bukan sekadar terdengar bijak.

## Pemakaian dan default

```text
Baca skills/note-to-quote/SKILL.md dan gunakan untuk note pilihan saya.
Pilih satu quote terkuat, jelaskan alasan pemilihannya,
dan sertakan konteks serta sumbernya.
```

- Bahasa default: Indonesia yang natural. Audiens default: pembaca awam yang ingin memperoleh gagasan dari bacaan/tontonan. Nyatakan asumsi atau sesuaikan dengan pilihan user.
- **Quote editorial** adalah default untuk bahan berupa ringkasan. Kalimat dirumuskan ulang dari isi note; tulis label publik “Diolah dari catatan …”. Nama narasumber menjadi kredit sumber inspirasi, bukan tanda tangan pengucap kalimat hasil olahan.
- Jika user meminta **kutipan asli**, gunakan alur verifikasi di bawah. Bila verifikasi belum tersedia, tampilkan calon kutipan dengan status jelas; jangan diam-diam menggantinya dengan rumusan editorial.
- Satu note menghasilkan satu quote utama. Dua atau tiga calon berbeda dapat dibandingkan secara internal, tetapi tidak harus semuanya diterbitkan.
- Umumnya 12–30 kata dan maksimal dua kalimat cukup untuk rumusan editorial. Ini patokan penulisan, bukan kewajiban: tambah konteks atau batalkan pilihan jika pemendekan mengubah makna.
- Quote adalah teks untuk satu frame/card. Desain gambar dan publikasi berada di luar keluaran skill ini; untuk visual Story, pakai skill desain gambar yang tersedia di agent Anda.
- Paket ini disimpan lokal dan dapat dipakai dengan meminta agent membaca file ini. Pemasangan ke katalog skill agent adalah langkah terpisah.

## 1. Baca note dan petakan konteks

Baca isi lengkap, frontmatter, sumber, pembicara, serta bagian sebelum dan sesudah calon gagasan. Catat pembedaan penting, alasan, pengalaman atau contoh yang menjelaskan gagasan itu.

Note ringkas dapat cukup untuk quote definisi jika konsepnya jelas; tidak harus cukup untuk carousel. Namun heading kosong, judul paper, atau definisi tanpa hasil tidak menjadi dasar mengarang kesimpulan penelitian. Jika tidak ada gagasan yang cukup utuh, keluarkan `perlu-lengkapi` dan sebutkan bahan yang kurang.

Gunakan `note/` sebagai bahan utama. Tautan ke konsep atau MOC merupakan petunjuk tema, bukan bukti isi tambahan. Proses banyak note hanya bila diminta; pertahankan satu keluaran terpisah per note dan jangan memaksakan benang merah lintas sumber.

## 2. Tentukan jenis teks dan atribusi

| Jenis | Dasar | Cara menyajikan |
|---|---|---|
| `editorial` | Gagasan didukung note, kalimat disusun ulang | Teks tanpa tanda kutip atau tanda tangan narasumber; label “Diolah dari catatan …” pada card/frame |
| `calon-kutipan` | Kalimat tercatat sebagai ucapan dalam note, sumber asli belum diperiksa | Tampilkan untuk review internal, label “Belum diverifikasi”; belum menjadi kutipan siap dipakai atas nama pembicara |
| `kutipan-terverifikasi` | Kata, pengucap, dan konteks diperiksa pada sumber asli | Tanda kutip, nama pengucap, sumber asli, dan penunjuk lokasi yang tersedia |

Kutipan orang ketiga yang diulang pembicara tetap milik pengucap asal. Bila note menulis bahwa kreator mengutip James Clear, jangan mengatribusikan kalimat itu kepada kreator. Catat rantai sumber dan verifikasi sumber asal sebelum menjadikannya kutipan terverifikasi.

Untuk kutipan asli, gunakan materi sumber yang benar-benar tersedia: rekaman beserta lokasinya, transkrip yang dapat diandalkan, atau teks asli dengan halaman/paragraf. Transkrip otomatis merupakan petunjuk; periksa bagian rekaman yang relevan bila wording atau identitas pengucap meragukan. Catat apa yang diperiksa, jangan membuat timestamp. Jika akses atau bukti tidak cukup, pertahankan status calon dan sebutkan kekurangannya.

Kutipan asli mempertahankan bahasa dan kata pengucap; pindah baris boleh. Tandai pemotongan dengan elipsis dan pastikan konteks tetap utuh. Kalimat yang dipoles atau dirangkai dari bagian terpisah menjadi editorial. Untuk terjemahan kutipan, tampilkan label “Terjemahan”, simpan teks asli dan sumbernya di catatan internal, dan jangan menyebut susunan kata terjemahan sebagai ucapan verbatim.

## 3. Cari dan pilih highlight

Cari 2–4 kandidat jika isinya mendukung; satu kandidat cukup untuk note sempit. Kandidat berasal dari pembedaan yang berguna, mekanisme yang menjelaskan sesuatu, dilema, prinsip praktis, atau perubahan pemahaman yang konkret.

Sebelum memberi skor, kandidat harus lolos dua syarat:

1. **Ada dasar spesifik:** tunjukkan heading/paragraf dan inti gagasan yang mendukung kalimat.
2. **Makna tetap utuh:** pemendekan mempertahankan siapa, konteks, ketidakpastian, dan batas klaim yang diperlukan. Jika tidak bisa muat tanpa menyesatkan, pilih gagasan lain atau tandai kurang cocok untuk format quote.

Bandingkan kandidat dengan skor editorial 0–2 per kriteria: 0 lemah, 1 sebagian, 2 kuat.

| Kriteria | Pertanyaan |
|---|---|
| Kekhususan | Apakah ada pembedaan atau ide nyata, bukan slogan yang cocok untuk semua topik? |
| Relevansi | Mengapa audiens sasaran perlu memahami ini? |
| Kemandirian | Apakah pembaca mengerti tanpa video, slide lain, atau kata “ini/itu” yang rujukannya hilang? |
| Kejelasan | Apakah kalimat mudah dibaca dan bebas jargon yang tidak dijelaskan? |
| Daya ingat | Apakah susunannya ringkas dan berkesan tanpa melebihkan makna? |

Pilih total tertinggi dari 10; bila seri, utamakan dukungan sumber dan kebutuhan konteks yang paling sedikit. Skor bukan prediksi viral. Tunjukkan perbandingan singkat serta alasan memilih satu kandidat. Cadangan harus membawa gagasan berbeda, bukan banyak versi sinonim dari satu kalimat.

## 4. Susun teks card dan pendamping

Gunakan [template hasil](references/output-template.md). Untuk editorial, padatkan satu insight, pertahankan detail pembeda, lalu tambahkan label sumber publik yang tepat. Hindari menaikkan kata “bisa” menjadi “pasti”, pengalaman pribadi menjadi hukum umum, atau hubungan menjadi sebab-akibat.

Jika makna memerlukan konteks atau atribusi, masukkan pada teks utama atau baris konteks di frame yang sama. Caption boleh menambah penjelasan, tetapi tidak membetulkan quote yang sudah menyesatkan ketika berdiri sendiri. Pendapat dan pengalaman tetap beratribusi. Kalimat medis, hukum, finansial, ilmiah, atau mutakhir yang bergantung pada kebenaran faktual perlu diperiksa sebelum diklaim sebagai fakta; bila belum, gunakan bentuk beratribusi yang akurat atau pilih insight lain.

Untuk sumber berbahasa lain, rumusan editorial boleh berbahasa Indonesia dengan kredit adaptasi. Jika user memilih kutipan asli, ikuti aturan bahasa dan terjemahan pada bagian jenis teks.

Tulis caption singkat yang menjelaskan konteks dan sumber asli. Jika sumber asli belum diperiksa, katakan bahwa adaptasi berdasarkan note. Untuk Stories tanpa caption, sediakan teks pendamping yang dapat ditempatkan pada frame sumber/link. Jika URL/DOI atau pengucap tidak diketahui, nyatakan kekurangannya; jangan melengkapinya dari tebakan.

## 5. Pemeriksaan akhir dan penyimpanan

Periksa dengan membayangkan hanya card-nya yang dibagikan ulang:

- Pembaca tetap memahami maksud, atribusi, dan batas pentingnya.
- Semua gagasan dapat dipetakan ke note atau sumber asli yang benar-benar dibaca.
- Label publik membedakan kalimat olahan dari kutipan asli.
- Kalimat tetap spesifik terhadap gagasan note, tanpa tambahan klaim, motivasi, atau janji hasil.
- Kutipan tidak kehilangan negasi, syarat, ironi, atau konteks pertanyaan host.
- Bila nama orang disebut, ejaan dan siapa yang berbicara sesuai sumber serta aturan vault.

Kirim satu quote utama, alasan pemilihan, konteks singkat, kredit publik, caption/teks pendamping, serta peta sumber internal. Jika hanya ada calon kutipan atau note belum layak, nyatakan hasil tersebut tanpa mengklaim siap publikasi.

Jika diminta menyimpan, ikuti lokasi user dan konvensi vault/folder user bila ada. Kalau `references/vault-rules.local.md` ada (gitignored), baca dan ikuti: lokasi bawaan, registrasi indeks, dan format frontmatter vault. Kalau note sumber berada di vault atau folder lain, tanyakan dulu tujuan penyimpanannya — jangan mengasumsikan vault note sama dengan vault tempat skill ini tinggal. Pertahankan note sumber, brand, index, konsep, MOC, dan skill carousel. Buat versi baru bila draft tujuan sudah diedit user. Gunakan brand hanya jika sudah ditentukan; jangan mengisi identitas brand dari asumsi.

Format default untuk berkas quote: judul `# Quote — <judul pendek>`; bagian A–D mengikuti [template hasil](references/output-template.md); tambahkan bagian **E. Aset produksi** bila ada gambar. Frontmatter dan pendaftaran di indeks mengikuti konvensi vault user (atau `references/vault-rules.local.md`). Note sumber yang berada di vault lain tidak boleh dirujuk dengan wikilink `[[note]]` — tulis pathnya.

Baca [contoh penerapan](references/examples.md) saat perlu contoh quote editorial, penanganan calon kutipan, kutipan berantai, atau penolakan bahan yang belum lengkap.
