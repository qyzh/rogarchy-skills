# Pemberitahuan Pihak Ketiga (Third-Party Notices)

Karya milik repo ini sendiri berlisensi MIT, hak cipta qyzh (lihat [LICENSE](LICENSE)).
Beberapa bagian diadaptasi dari proyek lain. Bagian itu tetap di bawah lisensi aslinya;
teks lisensi dan baris hak cipta asli disalin apa adanya (bahasa Inggris) di bawah ini.

Dokumen ini praktik atribusi open source yang umum, bukan nasihat hukum.

Catatan: sebagian isi repo ini diadaptasi dari karya pihak ketiga dan tetap berada di bawah
lisensinya masing-masing (LICENSE berisi teks MIT polos untuk karya repo ini).

---

## 1. claude-blog

- Proyek: claude-blog, <https://github.com/AgriciDaniel/claude-blog>
- Skill: `blog-post`
- Bagian yang diadaptasi (bukan salinan utuh, disingkat dan ditulis ulang untuk agent lain):
  disiplin riset dan kutipan di `blog-post/SKILL.md`, dan `blog-post/references/research-quality.md`
  (berdasarkan `research-quality.md` upstream).
- Hak cipta asli: `Copyright (c) 2025-2026 AgriciDaniel`
- Lisensi: MIT

```text
MIT License

Copyright (c) 2025-2026 AgriciDaniel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 2. last30days-skill

claude-blog sendiri mengadaptasi rubrik kualitas riset dari proyek ini, dan
`blog-post/references/research-quality.md` menyebutnya sebagai sumber.

- Proyek: last30days-skill, <https://github.com/mvanhorn/last30days-skill>
- Skill: `blog-post`
- Bagian yang diadaptasi: gagasan rubrik kualitas riset di `blog-post/references/research-quality.md`
  (diadaptasi, ditulis ulang).
- Hak cipta asli: `Copyright (c) 2026 Matt Van Horn`
- Lisensi: MIT

```text
MIT License

Copyright (c) 2026 Matt Van Horn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 3. dither-kit-rs

- Proyek: dither-kit-rs, <https://github.com/DeepanshuMishraa/dither-kit-rs>
- Skill: `dither-data-viz`
- Bagian yang diadaptasi: mesin dither di `dither-data-viz/scripts/dither.js` dan salinannya
  `dither-data-viz/design-options/dither.js`. Ini port ke JavaScript (diadaptasi, bukan salinan):
  matriks Bayer 2/4/8, matriks halftone 4x4, noise berbasis hash, dan gagasan komponen
  (grafik area, pie, radar, tombol, avatar, gradien, latar, meter, sparkline) mengikuti
  `crates/dither-core` upstream. Kode kartu, template, dan skrip ekspor ditulis sendiri.
- Hak cipta asli: `Copyright (c) 2026 Deepanshu Mishra`
- Catatan: dither-kit-rs sendiri berbasis [Boring-Software-Inc/dither-kit](https://github.com/Boring-Software-Inc/dither-kit)
  (versi React; `package.json`-nya menyatakan MIT). Kode di repo ini diadaptasi dari versi Rust.
- Lisensi: upstream menawarkan "MIT OR Apache-2.0" (lihat `Cargo.toml`). Repo ini memakai opsi MIT
  (`LICENSE-MIT` upstream), teksnya di bawah.

```text
MIT License

Copyright (c) 2026 Deepanshu Mishra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. Artificial Analysis (sumber data harga)

Ini **sumber data**, bukan kode yang diadaptasi, dan berbeda dari entri 1-3: tidak ada teks lisensi
open source yang bisa disalin.

- Sumber: Artificial Analysis, <https://artificialanalysis.ai/>
- Skill: `omarchy-agent-usage`
- Pemakaian: `omarchy-agent-usage/scripts/cost.py` memanggil Data API gratis Artificial Analysis
  (`https://artificialanalysis.ai/api/v2/language/models/free`) memakai kunci API milik pengguna, yang
  hanya dibaca dari env var `ARTIFICIAL_ANALYSIS_API_KEY`, untuk mendapat harga token per 1 juta token
  (input, output, cache). Hasilnya disimpan di cache lokal pengguna dan dipanggil jarang (cache 24 jam).
  Tanpa kunci tidak ada panggilan jaringan. Repo ini tidak menyertakan salinan data harga mereka.
  Lihat `omarchy-agent-usage/references/pricing-sources.md`.
- Hak cipta dan hak atas data: milik Artificial Analysis. Repo ini tidak mengklaim memilikinya.
- Atribusi: dokumentasi API (<https://artificialanalysis.ai/data-api/docs>, <https://artificialanalysis.ai/api-reference>)
  menyatakan atribusi ke Artificial Analysis wajib untuk pemakaian API. Sesuai Data Platform Terms v1.1
  (<https://artificialanalysiscdn.com/legal/ProDataPlatformTerms.pdf>, §5), laporan biaya skill ini
  mencantumkan persis "Source: Artificial Analysis (artificialanalysis.ai)" dengan tautan ke
  <https://artificialanalysis.ai/>; untuk angka turunan (biaya hasil hitung dari harga AA) ditambah
  "Based on data from Artificial Analysis" dan pernyataan "Created by <nama skill>, not by Artificial
  Analysis. Artificial Analysis does not endorse
  this report/tool". Kartu atau grafik yang dibagikan ke publik juga harus menampilkan logo Artificial
  Analysis (logo tidak disertakan di repo). README skill memuat kreditnya.
- Syarat: pemakaian API tunduk pada Terms of Use dan Data Platform Terms v1.1 Artificial Analysis. Syarat itu bisa
  berubah dan penafsirannya bukan wewenang repo ini; periksa versi terbaru sebelum membagikan atau memakai
  data harga secara komersial. Ini bukan nasihat hukum.

---

## 5. Omarchy

- Proyek: Omarchy, <https://github.com/omacom/omarchy>
- Skill: `omarchy-agent-usage`
- Bagian yang diadaptasi: potongan kecil di `omarchy-agent-usage/scripts/collect.py` (tiga regex
  `*_PI_PATTERN` dan beberapa predikat satu baris seperti `claude_billed`, `codex_pi_billed`) yang
  disalin dari wrapper `omarchy-agent-usage-claude` / `-codex` upstream; selebihnya ditulis sendiri.
  `omarchy-agent-usage/references/collector-internals.md` menjelaskan antarmuka wrapper tersebut.
- Hak cipta asli: `Copyright (c) David Heinemeier Hansson`
- Lisensi: MIT, teksnya di bawah.
- Skill ini tidak berafiliasi dengan atau didukung oleh Omarchy/Basecamp.

```text
Copyright (c) David Heinemeier Hansson

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
