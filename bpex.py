#!/usr/bin/env python3
"""Convert Approximately Up whiteboard files (.bpex) to PNGs and back.

A .bpex is N concatenated whiteboards, each 384x256, one byte per pixel,
rows stored bottom-to-top. 0 = blank, ink colours count down from 255.

  python bpex.py export  <file.bpex> [out_dir]    -> <name>_0.png, <name>_1.png, ...
  python bpex.py import  <dest.bpex> <png> [png ...]
  python bpex.py info    <file.bpex>

Import replaces only the boards you pass: a PNG named *_N.png goes into slot N
(unnumbered PNGs fill slots 0, 1, ... in order); other boards are kept. The
first import also saves <dest>.bak. Round trip is lossless for unedited
boards; on import every pixel snaps to the nearest palette colour.
"""
import re
import sys
from pathlib import Path

from PIL import Image

W, H = 384, 256
BOARD = W * H

# Pen colours, from approximately-up.act (matched against the game).
KNOWN = {
    0: (255, 255, 255),
    255: (0, 0, 0),
    254: (255, 0, 0),
    253: (0, 255, 0),
    252: (0, 0, 255),
    251: (255, 242, 0),
    250: (100, 0, 100),
    249: (0, 174, 239),
}


def build_palette():
    pal = []
    for v in range(256):
        # Unknown values get a unique colour so they survive a round trip.
        pal.append(KNOWN.get(v, (v, 128, 255 - v)))
    return pal


PALETTE = build_palette()
COLOR_TO_VALUE = {c: v for v, c in enumerate(PALETTE)}


def nearest(rgb, cache={}):
    if rgb in COLOR_TO_VALUE:
        return COLOR_TO_VALUE[rgb]
    if rgb not in cache:
        # Snap only to real pen colours; filler colours for unknown values
        # are matched exactly (above) so they round-trip but never attract.
        cache[rgb] = min(
            KNOWN,
            key=lambda v: sum((a - b) ** 2 for a, b in zip(rgb, PALETTE[v])),
        )
    return cache[rgb]


def board_count(data):
    if len(data) % BOARD:
        sys.exit(f"size {len(data)} is not a multiple of {BOARD}")
    return len(data) // BOARD


def board_to_image(block):
    img = Image.new("RGB", (W, H))
    img.putdata([PALETTE[v] for v in block])
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def image_to_board(path):
    img = Image.open(path)
    if img.size != (W, H):
        sys.exit(f"{path}: expected {W}x{H}, got {img.size[0]}x{img.size[1]}")
    img = img.convert("RGB").transpose(Image.FLIP_TOP_BOTTOM)
    pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    return bytes(nearest(px) for px in pixels)


def cmd_export(src, out_dir=None):
    src = Path(src)
    data = src.read_bytes()
    out = Path(out_dir) if out_dir else src.parent
    out.mkdir(parents=True, exist_ok=True)
    for k in range(board_count(data)):
        dest = out / f"{src.stem}_{k}.png"
        board_to_image(data[k * BOARD:(k + 1) * BOARD]).save(dest)
        print(dest)


def slot_of(path):
    m = re.search(r"_(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else None


def cmd_import(dest, *pngs):
    """Replace boards in dest. PNGs named *_N.png go to slot N; otherwise
    they fill slots 0, 1, ... in order. Boards not given are left untouched."""
    if not pngs:
        sys.exit("give at least one PNG")
    dest = Path(dest)
    boards = []
    if dest.exists():
        data = dest.read_bytes()
        boards = [data[k * BOARD:(k + 1) * BOARD] for k in range(board_count(data))]
        backup = dest.with_name(dest.name + ".bak")
        if not backup.exists():
            backup.write_bytes(data)
    slots = [slot_of(p) for p in pngs]
    if None in slots:
        slots = list(range(len(pngs)))
    for slot, png in zip(slots, pngs):
        while len(boards) <= slot:
            boards.append(bytes(BOARD))
        boards[slot] = image_to_board(png)
        print(f"board {slot} <- {png}")
    dest.write_bytes(b"".join(boards))
    print(f"wrote {dest} ({len(boards)} board(s))")


def cmd_info(src):
    data = Path(src).read_bytes()
    for k in range(board_count(data)):
        block = data[k * BOARD:(k + 1) * BOARD]
        counts = {v: block.count(v) for v in set(block)}
        print(f"board {k}: " + ", ".join(f"{v}:{n}" for v, n in sorted(counts.items())))


COMMANDS = {"export": cmd_export, "import": cmd_import, "info": cmd_info}

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    COMMANDS[sys.argv[1]](*sys.argv[2:])
