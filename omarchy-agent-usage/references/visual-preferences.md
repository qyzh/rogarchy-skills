# Gaya tampilan visual bawaan

Gaya bawaan skill untuk grafik/video data usage. Dipisah dari SKILL.md karena
ini soal tampilan, bukan perilaku tool. Pengguna boleh meminta gaya lain; permintaan
eksplisit mengalahkan bawaan ini.

Kalau diminta grafik/video dari data usage:

- Rasio mobile **9:16** (1080×1920), tema gelap.
- Tampilkan **hanya** nama agent, token, dan prompt, dipecah per hari, tanpa
  input/output/cache.
- Gaya: bar kontras di latar gelap, tipografi terbaca di layar HP. Konsep yang
  sama dipakai ulang untuk varian video.

**PNG = kartu informatif, bukan canvas-only.**
- Bawaan: jangan keluarkan grafik saja. PNG harus capture seluruh kartu (judul
  + chart + legenda + tabel angka + catatan kaki) via `Page.captureScreenshot`
  clip 1080×1920 @ deviceScaleFactor 2, lalu di-downscale LANCZOS ke 1080×1920.
- Jangan tulis label ke dalam bitmap.

**Istilah:** pakai **token non-cache** (bukan "token segar") (= input non-cache + output).

**Biaya di grafik (kalau diminta):** ambil biaya per agent dari
`cost_by_model.csv` (jumlahkan per agent untuk rentang tanggal grafik) di data
dir. **Jangan** menghitung ulang "token non-cache × harga per 1M": `cost.py`
memakai harga input, output, cache-hit dan cache-write terpisah, jadi angka
inline akan berbeda dari `cost_report.md`.
- Tampilkan kolom Biaya per agent + banner total di bawah chart.
- Sertakan `fetched_at`, dan tandai `INCOMPLETE` bila laporan biaya begitu.
- **Semua angka USD di kartu ditulis tepat 2 desimal** (`$168.23`, `$0.00`).
  Jangan tampilkan 4–6 desimal dari CSV lama; format ulang saat membaca.
- `cost_by_model.csv` menyimpan biaya **per model yang sudah dibulatkan 2 desimal**.
  Menjumlahkannya bisa beda beberapa sen dari `cost_daily.csv` / `cost_report.md`
  (cost.py menjumlahkan nilai mentah lalu membulatkan total). Untuk total kartu,
  pakai angka resmi `cost_daily.csv`; selisihnya dibebankan ke agent berbiaya
  terbesar agar baris tabel tetap berjumlah total.
