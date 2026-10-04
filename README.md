# Approximately Up whiteboard tool

Export the drawings on your [Approximately Up](https://store.steampowered.com/search/?term=approximately+up) whiteboards to PNG, edit them in any image editor, and import them back.

This is an unofficial, community tool. It was made by reverse-engineering the save format and is not affiliated with the game's developers. Tested with game version 1.0.212; later versions may change the format.

## How it works

Whiteboard pixels are not stored in the `.bp` blueprint file. They live in a sibling `.bpex` file with the same name. A `.bpex` is a sequence of boards, one after another, each one:

- 384 × 256 pixels, 1 byte per pixel, no header or compression
- rows stored bottom-to-top (the tool flips them for you)
- value `0` = blank/white; the seven pens are `255`…`249`

| Byte | Colour |
|------|--------|
| 0 | white |
| 255 | black |
| 254 | red |
| 253 | green |
| 252 | blue |
| 251 | yellow |
| 250 | purple |
| 249 | cyan |

A blueprint with no whiteboards has no `.bpex`. Blueprints live in
`%USERPROFILE%\AppData\LocalLow\ApproximatelyGames\ApproximatelyUp\Blueprints`
(`<guid>.bp`, `<guid>.bpmeta`, and `<guid>.bpex` if it has whiteboards; `.bpmeta` is JSON with the blueprint's name).

## Install

Needs Python 3.8+ and [Pillow](https://pypi.org/project/pillow/):

```bash
pip install -r requirements.txt
```

## Usage

```bash
python bpex.py export <file.bpex> [out_dir]    # -> <name>_0.png, <name>_1.png, ...
python bpex.py import <dest.bpex> <png> [png ...]
python bpex.py info   <file.bpex>              # pixel counts per colour, per board
```

### Typical workflow

1. In the game, put a number or label on each whiteboard so you can tell them apart, and save the blueprint.
2. Export: `python bpex.py export "<guid>.bpex" my_boards`
3. Edit the PNGs (keep them 384 × 256; the tool snaps every pixel to the nearest pen colour).
4. Import: `python bpex.py import "<guid>.bpex" my_boards/<guid>_1.png`
5. Load the blueprint in the game.

Notes:

- **Slots are 1:1 with the file, not with creation order.** Boards are stored in an order set by the game; use your labels to find which is which. This tool never adds, removes or reorders boards.
- **Import replaces only the boards you pass.** A PNG named `*_N.png` goes into slot N; unnumbered PNGs fill slots 0, 1, … in order. Everything else is left untouched.
- The first import onto a file writes `<file>.bpex.bak` next to it. Keep your own backups of the blueprint too. You don't need to close the game before importing.
- Export → import with no edits reproduces the original file byte for byte.
- `palette/approximately-up.act` is the 8-colour palette as an Adobe Colour Table. Load it in Photoshop (Indexed Color → Custom) or similar to stay on-palette.

## Demo

`examples/demo/` is a small blueprint (one whiteboard and a light) to try the tool on. Copy the three files (`.bp`, `.bpmeta`, `.bpex`) into your Blueprints folder, load "Whiteboard" in the game, and run:

```bash
python bpex.py export examples/demo/9ddec29d-8178-443e-a222-531d9a15d347.bpex out
```

![Demo whiteboard exported to PNG](examples/demo/preview.png)

The demo image was made for this project (AI-assisted) and dithered to the game's 8 colours.

## Limitations

- It can't change the number of whiteboards in a blueprint; do that in the game.
- Exact in-game RGB values were matched by eye, so colours may be slightly off. The saved data only stores the pen index.

## License

MIT
