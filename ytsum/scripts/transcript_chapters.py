#!/usr/bin/env python3
"""Split a timestamped YouTube transcript into fixed-duration blocks for sectioned summaries.

Input is the output of `fetch_transcript.py "<URL>" --text-only --timestamps`:
one segment per line, `M:SS` or `H:MM:SS`, e.g. `0:05 dan selamat datang`.
Lines without a timestamp join the previous segment's text.

`--index` prints one short line per block with its time range and the line range
of the input file it covers (`L<first>–<last>`, 1-based, contiguous, no gaps), so
the raw transcript can be read block by block without loading the long block text.
"""
import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True

LINE = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?\s+(.*)$')


def parse_timestamp(match):
    """Turn an `M:SS` or `H:MM:SS` line match into total seconds."""
    first, second, third = match.group(1), match.group(2), match.group(3)
    if third is None:
        return int(first) * 60 + int(second)
    return (int(first) * 60 + int(second)) * 60 + int(third)


def format_time(total):
    """Render seconds back as `M:SS` below one hour, `H:MM:SS` at or above it."""
    if total < 3600:
        return f'{total // 60}:{total % 60:02d}'
    return f'{total // 3600}:{total % 3600 // 60:02d}:{total % 60:02d}'


def split_lines(text):
    """File lines as a line-reading tool numbers them: split on newline only, keep `\\r` for strip()."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def parse_segments(text):
    """Reduce transcript text to [{'start': seconds, 'text': str, 'line': n}]; malformed lines join the previous one.

    `line` is the 1-based input line of the segment's timestamp."""
    segments = []
    for number, raw in enumerate(split_lines(text), start=1):
        line = raw.strip()
        if not line:
            continue
        match = LINE.match(line)
        if not match:
            if segments:
                segments[-1]['text'] += ' ' + line
            continue  # text before the first timestamp carries no anchor
        segments.append({'start': parse_timestamp(match),
                         'text': match.group(4).strip(), 'line': number})
    return segments


def build_blocks(segments, minutes):
    """Group consecutive segments; close a block when the next start reaches start + N minutes."""
    limit = minutes * 60
    blocks = []
    for segment in segments:
        if blocks and segment['start'] < blocks[-1]['start'] + limit:
            blocks[-1]['end'] = segment['start']
            blocks[-1]['text'] += ' ' + segment['text']
        else:
            blocks.append({'start': segment['start'], 'end': segment['start'],
                           'text': segment['text'], 'line': segment['line']})
    return blocks


def line_ranges(blocks, total_lines):
    """[(first, last)] input lines per block: block i runs up to the line before block i+1.

    The first block starts at line 1 (text before the first timestamp stays covered) and
    the last ends at `total_lines`, so the ranges cover the whole file in order."""
    firsts = [1] + [b['line'] for b in blocks[1:]]
    lasts = [b['line'] - 1 for b in blocks[1:]] + [total_lines]
    return list(zip(firsts, lasts))


def render_index(blocks, total_lines):
    """One line per block: `- start–end  Lfirst–last  first words…`."""
    return ''.join(f"- {format_time(b['start'])}–{format_time(b['end'])}  L{first}–{last}  {preview(b['text'])}\n"
                   for b, (first, last) in zip(blocks, line_ranges(blocks, total_lines)))


def preview(text, width=12):
    """First `width` words of a block, with an ellipsis when there is more."""
    words = text.split()
    return ' '.join(words[:width]) + ('…' if len(words) > width else '')


def render_text(blocks):
    """One `## start–end` header per block, its text, and a blank line after each block."""
    return '\n\n'.join(f"## {format_time(b['start'])}–{format_time(b['end'])}\n{b['text']}"
                       for b in blocks) + '\n'


def render_json(blocks):
    return json.dumps([{'start': format_time(b['start']), 'end': format_time(b['end']),
                        'text': b['text']} for b in blocks], ensure_ascii=False, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript', type=Path)
    parser.add_argument('--minutes', type=int, default=5, metavar='N',
                        help='target block length in minutes (default: 5)')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--index', action='store_true',
                      help='print one short line per block: time range, input line range (Lfirst–last) and first words')
    mode.add_argument('--json', action='store_true', help='print a JSON array of blocks')
    args = parser.parse_args(argv)
    if args.minutes < 1:
        print(f'ERROR: --minutes must be at least 1, got {args.minutes}', file=sys.stderr)
        return 1
    try:
        text = args.transcript.read_text(encoding='utf-8')
    except OSError as exc:
        print(f'ERROR: cannot read {args.transcript}: {exc.strerror or exc}', file=sys.stderr)
        return 1
    segments = parse_segments(text)
    if not segments:
        print(f'ERROR: no timestamped lines found in {args.transcript}', file=sys.stderr)
        return 1
    blocks = build_blocks(segments, args.minutes)
    if args.index:
        print(render_index(blocks, len(split_lines(text))), end='')
    elif args.json:
        print(render_json(blocks))
    else:
        print(render_text(blocks), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
