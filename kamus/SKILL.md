---
name: kamus
description: "Use when saving a term as one definition note in the user's kamus folder."
version: 1.0.1
author: qyzh, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kamus, obsidian, definisi]
    related_skills: [ytsum]
---

# Kamus

## Overview

Satu istilah = satu note definisi di folder kamus milik user (`KAMUS_DIR`). Skill ini menjaga format konsisten dan arti terverifikasi. Skill tidak menjalankan validator, graph, Index, atau MOC kecuali user memintanya.

## Prerequisites / Config

Requires: none.
Local files: `references/vault-rules.local.md` (template `references/vault-rules.example.md`).

| Variable | Meaning | Default | Kind |
|---|---|---|---|
| `KAMUS_DIR` | Folder tempat note kamus disimpan | `$HOME/kamus` | setting |

Resolve each variable once, before the first step that needs it: the env var if set and non-empty; else its `KEY=value` line in `${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env` (written by `rogarchy-setup`; read it as data, never `source` it; the last matching line wins); else the default. A missing file or line means the default. Kind: `setting` = setup asks for it; `advanced` = setup keeps the default unless the user asks; `secret` = env var only, never in `config.env` or chat. In a shell, `rs_get` does the same lookup:

```bash
rs_get() { _rs_v=$(printenv "$1" || :); [ -n "$_rs_v" ] || _rs_v=$(sed -n "s/[[:space:]]*\$//; s/^$1=//p" "${XDG_CONFIG_HOME:-$HOME/.config}/rogarchy-skills/config.env" 2>/dev/null | tail -n 1 || :); printf '%s\n' "${_rs_v:-$2}"; }
rs_get KAMUS_DIR "$HOME/kamus"
```

Bila user menyebut folder lain di permintaan, pakai itu. Buat folder pada penyimpanan pertama bila belum ada.

Bila `references/vault-rules.local.md` ada di folder skill ini, baca dan ikuti: berisi aturan khusus vault user (file lokal, tidak ada di repo) yang menimpa teks generik di sini.

## When to Use

- User meminta "simpan kata X", "tambah istilah", "definisi ...", atau menyebut kamus.
- User memberi kata asing/istilah yang ingin dicatat sebagai entri kamus.

When NOT to use: ringkasan video → `ytsum`; konsep lintas sumber → concept note; kamus di folder lain → path eksplisit user menang.

## Workflow

1. **Resolve path.** Target: `<KAMUS_DIR yang sudah di-resolve>/<Istilah>.md` (lihat Prerequisites / Config). Nama file = istilah, huruf pertama kapital, spasi diperbolehkan. Jangan buat subfolder baru.
2. **Cek duplikat.** List folder kamus. Bila file sudah ada, laporkan isinya dan tanya apakah mau diperbarui — jangan diam-diam menimpa.
3. **Verifikasi arti.** Cari makna di KBBI (`kbbi.kemdikdasmen.go.id` atau `kbbi.web.id`) untuk kata Indonesia; untuk kata asing pakai Wiktionary atau kamus resmi. Jangan mengarang arti dari bentuk kata. Bila sumber tidak ditemukan, tanyakan ke user atau tulis status jelas di `## Catatan` bahwa definisi belum terverifikasi.
4. **Tulis file** memakai template di bawah, isi semua bagian.
5. **Verifikasi hasil.** Baca kembali file: kunci frontmatter harus `type/status/topics`, ketiga `##` bagian harus ada, dan setiap wikilink `[[Istilah]]` harus menunjuk ke file yang benar-benar ada di folder kamus.
6. **Laporkan** path absolut file. Jangan menyentuh graph atau Index kecuali user memintanya.

## Template wajib

```markdown
---
type: kamus
status: active
topics: [filsafat, waktu]
---

# <Istilah>

**<Istilah>** adalah ... (definisi satu paragraf; sebutkan bahasa asal bila bukan bahasa Indonesia)

## Bedakan dengan kata mirip

- ...

## Contoh

> ...

## Catatan

Sumber: <URL KBBI/Wiktionary/kamus resmi>. Ejaan alternatif: ...
```

Aturan template: `status` = `active` atau `verified`; `topics` minimal satu nilai lowercase kebab-case; bagian `## Bedakan dengan kata mirip` adalah inti nilai kamus ini — isi dengan kata yang mudah tertukar, bukan dipaksakan bila tidak ada.

## Common mistakes

- Mengarang kunci frontmatter seperti `istilah:`, `bahasa:`, `jenis:`, `kamus: true`, atau `tags:` — pakai hanya `type/status/topics`.
- Mengganti nama bagian dengan `## Arti` atau `## Etimologi` — pakai tiga judul yang ditentukan.
- Menulis definisi tanpa mengecek sumber, lalu mengaku terverifikasi.
- Menambahkan entri ke Index/MOC atau menjalankan validator/graph kecuali user atau aturan lokal memintanya.
