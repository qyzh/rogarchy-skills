# kamus

## Apa ini

Skill untuk menyimpan satu istilah sebagai satu note definisi di folder kamus Anda. Format note tetap (frontmatter `type/status/topics`, bagian "Bedakan dengan kata mirip", "Contoh", "Catatan"), dan arti diverifikasi ke sumber seperti KBBI atau Wiktionary, tidak dikarang dari bentuk kata.

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Pengguna meminta "simpan kata X", "tambah istilah", atau "definisi ...", atau menyebut kamus.
- Pengguna memberi kata asing atau istilah yang ingin dicatat sebagai entri kamus.

Tidak dipakai untuk:

- Ringkasan video (`ytsum`).
- Konsep lintas sumber (gunakan concept note).
- Kamus di folder lain: path yang disebut pengguna diutamakan.

## Kebutuhan

- Alat runtime: tidak ada skrip. Agent memakai akses baca/tulis berkas dan akses web untuk memeriksa arti.
- Skill di luar repo ini: tidak ada yang wajib. `ytsum` (di repo ini) hanya disebut sebagai tujuan alih dan terdaftar di `related_skills`. Format note cocok untuk vault Obsidian (wikilink `[[Istilah]]`), tetapi Obsidian tidak wajib.

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `KAMUS_DIR` | Folder tempat note kamus disimpan | `$HOME/kamus` |

Folder dibuat saat penyimpanan pertama. Folder yang disebut pengguna di permintaan lebih diutamakan. Bila folder default bukan tempat kamus Anda, set `KAMUS_DIR`.

Aturan khusus vault Anda (misalnya "jangan sentuh Index/MOC") bisa ditaruh di `kamus/references/vault-rules.local.md` (templat: `vault-rules.example.md`). Agent membacanya bila ada; file `*.local.md` diabaikan git, jadi tidak ikut terpublikasi.

Nilai di atas juga bisa disimpan di berkas pengaturan `${XDG_CONFIG_HOME:-~/.config}/rogarchy-skills/config.env` (lewat [`rogarchy-setup`](../rogarchy-setup/README.md)); env var tetap menang, lalu berkas itu, lalu default.

## Contoh pemakaian

```text
simpan kata "hakikat" ke kamus
```

Agent memeriksa duplikat, memverifikasi arti, lalu menulis `$KAMUS_DIR/Hakikat.md`:

```markdown
---
type: kamus
status: active
topics: [filsafat]
---

# Hakikat

**Hakikat** adalah ... (definisi satu paragraf)

## Bedakan dengan kata mirip

- ...

## Contoh

> ...

## Catatan

Sumber: <URL KBBI>. Ejaan alternatif: ...
```

Bila file sudah ada, agent melaporkan isinya dan bertanya dulu sebelum menimpa. Setelah menulis, agent membaca ulang file dan memastikan setiap wikilink menunjuk ke file yang ada.

## Isi folder

```
kamus/
├── SKILL.md                         # instruksi untuk agent
├── README.md                        # dokumen ini
└── references/
    ├── vault-rules.example.md       # templat aturan vault (salin ke vault-rules.local.md)
    └── vault-rules.local.md         # opsional, lokal, tidak masuk git
```

---

Versi 1.0.0 · Lisensi MIT · [README repo](../README.md)
