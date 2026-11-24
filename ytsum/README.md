# ytsum

## Apa ini

Skill yang mengubah satu URL YouTube menjadi satu file rangkuman Markdown yang setia pada isi video. Metadata diambil dengan `yt-dlp`, transkrip dengan skill `youtube-content`, lalu rangkuman ditulis dalam bahasa video dengan frontmatter YAML. Video panjang dipecah per 5 menit lewat skrip pembantu.

## Kapan dipakai / tidak dipakai

Dipakai bila:

- Anda memberi URL YouTube dan ingin rangkumannya **disimpan sebagai file**.

Tidak dipakai (alihkan ke `youtube-content`) bila:

- Anda hanya ingin rangkuman di chat.
- Anda meminta transkrip mentah.

Agent juga berhenti bila video sudah pernah diringkas (`video_id` atau nama file sudah ada), `yt-dlp` gagal, atau caption dinonaktifkan.

## Kebutuhan

| Kebutuhan | Status | Fungsi |
|---|---|---|
| `yt-dlp` | **Wajib** | Metadata video (id, kreator, tanggal unggah, durasi, judul). |
| Python 3 | **Wajib** | Menjalankan `fetch_transcript.py` dan `scripts/transcript_chapters.py`. |
| Skill `youtube-content` (di luar repo) | **Wajib** | Menyediakan `scripts/fetch_transcript.py` untuk mengambil transkrip. Juga tujuan alih untuk permintaan chat-saja atau transkrip mentah. |

Platform: Linux dan macOS (sesuai frontmatter).

## Konfigurasi

| Variabel | Arti | Default |
|---|---|---|
| `YTSUM_OUTPUT_DIR` | Folder tempat rangkuman ditulis | `$HOME/ytsum` |
| `YTSUM_SCRATCH_DIR` | Folder sementara untuk transkrip dan potongan | `${TMPDIR:-/tmp}/ytsum-scratch` |

Folder keluaran yang disebut di permintaan lebih diutamakan. File sementara dihapus di akhir proses.

## Contoh pemakaian

```text
/ytsum https://www.youtube.com/watch?v=<video_id>
```

Hasil: satu file `<kreator> - <judul>_<tanggal unggah>.md` di folder keluaran, berisi frontmatter (`title`, `creator`, `video_id`, `upload_date`, `summary_date`, `source`, `language`), paragraf pembuka, definisi istilah, bagian tematik `##`, dan poin penting. Agent melaporkan path file.

Memeriksa transkrip video panjang secara manual (opsional):

```bash
python3 ytsum/scripts/transcript_chapters.py transkrip.txt --minutes 5 > potongan.txt
```

Skrip membaca transkrip berstempel waktu (`M:SS` atau `H:MM:SS` per baris) dan mencetak blok `## mulai–selesai`. Opsi `--index` dan `--json` tersedia. Selalu alihkan keluarannya ke file.

## Isi folder

```
ytsum/
├── SKILL.md                       # instruksi untuk agent
└── scripts/
    └── transcript_chapters.py     # membagi transkrip berstempel waktu menjadi blok per N menit
```

---

Versi 3.0.0 · Lisensi MIT · [README repo](../README.md)
