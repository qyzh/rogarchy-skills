# Sumber harga token

Dipakai oleh `scripts/cost.py`.

## File harga

| File | Peran |
|---|---|
| `references/pricing.json` | **Seed lokal opsional**, gitignored (tidak ada di repo), tidak pernah ditulis kode. Bisa dibuat dari cache runtime. Bila tidak ada, dilewati. |
| `~/.cache/omarchy-agent-usage/pricing.json` (`OMARCHY_USAGE_PRICING_CACHE`) | Cache runtime. Hasil merge seed ← cache lama ← fetch API. |

Urutan muat:
1. seed (bila ada);
2. ditimpa cache;
3. ditimpa fetch API (hanya bila ada kunci, bukan `--offline`, cache API > 24 jam).

Fetch **menimpa per slug**: slug yang tidak ada di fetch terbaru tetap memakai
harga terakhir dengan `stale: true` dan `last_seen`.

## Sumber: Artificial Analysis Data API (tier gratis)

- Dokumentasi: https://artificialanalysis.ai/data-api/docs ·
  https://artificialanalysis.ai/api-reference
- Endpoint: `GET https://artificialanalysis.ai/api/v2/language/models/free`
  (query `page`, mulai 1; respons `pagination.has_more`).
  Jalur `/api/v2/language/models` khusus Pro+.
- Auth: header `x-api-key`, nilainya dari env `ARTIFICIAL_ANALYSIS_API_KEY`.
- Rate limit tier gratis: 100 request per jendela 24 jam (dimulai dari request
  pertama); 429 membawa `Retry-After`. Cache 24 jam menjaga pemakaian jauh di
  bawah itu.
- Atribusi wajib: "Source: Artificial Analysis (artificialanalysis.ai)" dengan
  tautan ke https://artificialanalysis.ai/. Angka turunan (biaya hasil hitung):
  "Based on data from Artificial Analysis" + "Artificial Analysis does not
  endorse this report/tool". Kartu/grafik yang dibagikan publik wajib memuat
  logo AA.
- Satuan: USD per **1 juta token**. Field model: `slug`, `name`,
  `pricing.price_1m_input_tokens`, `pricing.price_1m_output_tokens`,
  `pricing.price_1m_cache_hit_tokens`, `pricing.price_1m_cache_write_tokens`
  (cache bisa `null`/tidak ada, tidak dijamin di tier gratis).
- `cost.parse_api_models()` memetakan ke format internal
  `{input, output, cacheHit, cacheWrite}`; `slug` dipakai sebagai kunci
  (`MODEL_MAP` memetakan model lokal ke slug itu).
- Tanpa kunci: tidak ada panggilan jaringan. Tidak ada fallback scraping.

Harga cache yang tidak tersedia: cacheHit = harga input, cacheWrite = 1.25 ×
harga input. Asumsi ini dicantumkan di laporan.

## Pemetaan model lokal → slug AA (`MODEL_MAP`)

| Model lokal | Slug AA | Catatan |
|---|---|---|
| `claude-opus-5-5` | `claude-opus-5-5` | |
| `claude-sonnet-5-5` | `claude-sonnet-5-5` | |
| `claude-fable-5-2` | `claude-fable-5-2` | |
| `claude-haiku-5-5` | `claude-haiku-5-5` | |
| `gpt-6-luna` | `gpt-6-luna` | |
| `gpt-6.1-sol` | `gpt-6-2-sol` | **successor**; slug asli `gpt-6-1-sol` hilang dari AA (fetch 2026-11-19) |
| `gpt-6.1-terra` | `gpt-6-1-terra` | |
| `gpt-6-astra` | `gpt-6-2-astra` | **successor**; slug asli `gpt-6-astra` hilang dari AA (fetch 2026-11-19) |

Model successor tercantum di `SUCCESSOR_OF` di `cost.py` dan di setiap laporan
("Dipatok ke harga slug successor").

**Model `:free`/`-free` TIDAK boleh ada di tabel ini.** Aturannya $0; padanannya
dipakai sebagai proxy (tabel bawah). `cost.py` memeriksa `is_free` sebelum
`MODEL_MAP`. Kalau urutannya dibalik, model free yang punya padanan akan keliru
ditagih.

## Model tanpa harga

Model berbayar yang tidak ada di `MODEL_MAP`, atau yang slug-nya tidak ada di
harga:
- dikeluarkan dari total, tapi **dicantumkan** di seksi "Tidak terhitung"
  (`cost_report.md`, `metrics_report.md`) beserta jumlah token dan alasannya;
- hari yang memuatnya ditandai `partial`;
- lebih dari 1% token berbayar tak terharga → banner `INCOMPLETE`
  (`--strict` → exit 3).

Baris tanpa token (`(unknown)`, prompt saja) tidak dihitung "tak terharga".

**Kalau slug drift:** cari slug penggantinya di cache harga, lalu perbarui
`MODEL_MAP` (+ `SUCCESSOR_OF`) dan tabel ini.

## Footnote proxy untuk model free

Model free = $0. Supaya tetap informatif, laporan memuat seksi "Model free —
estimasi proxy" (seandainya dipatok harga padanannya), hanya kalau AA punya
model sejenis:

| Model free | Proxy |
|---|---|
| `meituan/longcat-2.5:free`, `meituan/longcat-2.5-preview:free`, `meituan/longcat-2.0:free` | `longcat-2-0` |
| `tencent/hy4-flash:free` | `tencent-hy4` |
| `GLM-5.3-flash-free` | `glm-5-3-flash` |
| `deepseek-v4.1-flash-free` | `deepseek-v4-1-flash-1017` |
| `minimax-m3.1-flash-free` | `minimax-m3-1-flash` |
| `upstage/solar-pro4:free` | `solar-pro4` |
| `upstage/solar-mini4:free` | `solar-mini4` |
| `reflection/beam-1.0-501b-a23b:free` | `reflection-beam` |

Tanpa proxy (tidak ada padanan): `stepfun/*`, `poolside/*`, `stealth/*`,
`muse-spark-*`, `beam-free`, `big-pickle`, `nemotron-*`.

## Penting: harga bisa naik/turun

- AA menampilkan harga **saat ini**, bukan historis. Simulasi ini berarti
  "seandainya pemakaian historis dipatok harga hari ini".
- Setiap laporan mencantumkan `fetched_at` + `mode` (live/cache/seed).
- **AA tidak menyediakan historis.** Untuk membandingkan harga antar-minggu,
  pakai snapshot Wayback Machine dari halaman harga milik provider sendiri (bukan Artificial Analysis) atau newsroom provider.
