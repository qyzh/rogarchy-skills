# Task Signal — `tasks.jsonl`

Sinyal tugas selesai untuk metrik **cost per task**.

## Lokasi file

```
~/.local/state/omarchy/agents/tasks.jsonl
```

Append-only, satu JSON per baris. Override via env `OMARCHY_TASKS_FILE`
(wajib saat tes).

## Skema

```json
{"ts":"2026-11-17T16:20:00+07:00","agent":"hermes","session":"local-9b07…","label":"hermes session","status":"ok"}
```

| Field     | Wajib | Tipe    | Aturan |
|-----------|-------|---------|--------|
| `ts`      | ya    | string  | ISO 8601 (zona waktu disarankan; tanpa zona = waktu lokal). `Z` diterima |
| `agent`   | ya    | string  | `hermes` \| `claude` \| `codex` \| `opencode` \| `agy` \| `grok` |
| `session` | —     | string  | id sesi; **dipakai untuk dedupe** |
| `label`   | —     | string  | bebas |
| `status`  | ya    | string  | `ok` \| `partial` \| `fail` |
| `turns`   | —     | integer | ≥ 1 |

### Aturan

- Append-only. Baris yang sudah ditulis tidak boleh dihapus atau diedit.
- Baris cacat di-skip **dan dihitung** (tidak diam-diam diabaikan).
- **Dedupe saat membaca** (`common.read_tasks`):
  - satu task = satu (agent, session);
  - pemenangnya baris dengan `ts` terbaru (status & tanggalnya yang dipakai);
  - baris tanpa `session` = task sendiri-sendiri.

  Dedupe diperlukan karena hook yang terpasang fire **per giliran**, bukan per
  sesi.
- Tanggal = hari LOKAL dari `ts` (`ts` dikonversi ke zona lokal dulu),
  konsisten dengan bucket `local_day` di `collect.py`.

## Semantik

| Status    | Bobot |
|-----------|------:|
| `ok`      |   1.0 |
| `partial` |   0.5 |
| `fail`    |   0.0 |

- **Cost per task (per agent-hari)** = biaya agent pada hari itu ÷ bobot task
  agent itu. Biaya task gagal tetap dihitung (bobotnya 0 di penyebut).
- **Agregat tanggal / periode** = Σ biaya ÷ Σ bobot **hanya atas agent-hari
  yang punya baris task**. Agent tanpa task signal (saat ini Claude, Codex)
  tidak ikut. Agent-hari tanpa data usage atau dengan token tak terharga
  dikecualikan, dan dicantumkan di laporan.
- Pemakaian yang seluruhnya model free = biaya $0 *diketahui* →
  `0.0000 (free)`.
- `n/a` selalu disertai alasan:
  - `n/a (no tasks)`
  - `n/a (all tasks failed, weight 0)`
  - `n/a (no usage data)`
  - `n/a (unpriced tokens)`
- Granularitas: karena task = sesi, "cost per task" = **biaya per sesi**,
  bukan per tugas semantik.

## CLI

```bash
omarchy-tasklog record --agent hermes --label "fix tests" --status ok --session S1   # shim di ~/.local/bin
python3 scripts/tasklog.py record --agent hermes --status ok                         # sama, langsung
python3 scripts/tasklog.py summary [--days 7] [--agent hermes]
python3 scripts/tasklog.py validate
```

- `record`: append satu baris (default `status=ok`, `ts=now`); `--ts` divalidasi ISO 8601.
- `summary`: jumlah task per agent/hari + bobot, **setelah dedupe sesi**
  (mencetak berapa baris duplikat). **Tidak** menghitung biaya; cost per task
  ada di `metrics.py`.
- `validate`: cek semua baris mentah (tanpa dedupe), laporkan baris cacat
  (nomor baris + alasan).
- Stdlib only.

## Penulis hook (contoh generik)

Setiap agent punya mekanisme hook sendiri; cek dokumentasi agent Anda. Pola
umumnya sama:

1. Hook "akhir giliran/sesi" memanggil `omarchy-tasklog record --agent <a>
   --status ok --session <ID sesi dari payload hook>`.
2. Hook itu tidak boleh memblokir agent (`|| true`) dan tidak membaca kredensial.
3. Banyak agent mengirim event ini **per giliran**, bukan per sesi. Satu sesi
   bisa menulis puluhan baris; pembaca men-dedupe per (agent, sesi).
4. Cek hasil: `grep -c '"agent": "<a>"' "$OMARCHY_TASKS_FILE"` > 0 setelah satu
   sesi. Kegagalan hook sebaiknya dicatat ke `tasklog-errors.log` di folder yang
   sama dengan `tasks.jsonl`.

Catatan hook yang spesifik untuk mesin Anda (path, allowlist, cara mencabut)
simpan di `references/task-signal.local.md`. File itu ada di `.gitignore`;
agent diminta membacanya bila ada.

## Template belum diuji

Hanya contoh. Cocokkan dulu dengan hook system agent yang asli. Semua template
memanggil shim, tidak membaca kredensial, dan tidak memblokir agent kalau
gagal.

### Claude Code (`~/.claude/settings.json`, hook `Stop`)

Claude Code mengirim payload JSON lewat stdin yang memuat `session_id`.
`Stop` fire per giliran; dedupe di pembaca menanganinya.

```jsonc
{
  "hooks": {
    "Stop": [
      { "matcher": "", "hooks": [ { "type": "command",
        "command": "sid=$(jq -r '.session_id // empty' 2>/dev/null); omarchy-tasklog record --agent claude --status ok --label 'claude stop' --session \"$sid\" >/dev/null 2>&1 || true" } ] }
    ]
  }
}
```

Codex dan agy: belum ada mekanisme hook yang terverifikasi. Catat manual
dengan `omarchy-tasklog record --agent codex …` bila perlu.
