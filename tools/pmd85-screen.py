#!/usr/bin/env python3
"""Turn a PMD 85 screen bitmap into something that looks like a photo of the monitor.

The bitmaps under tools/raster/ are the real thing: a PMD 85-2 with the BASIC-G
V2.0 ROM module, running in GPMD85Emulator (https://github.com/mborik/GPMD85Emulator)
inside a container and driven by synthetic keystrokes. The emulator's viewport is
the 288x256 PMD raster scaled 3x, so `extract` reduces a window capture back to
the exact bitmap the machine produced.

`render` adds only what a camera would add: the 4:3 stretch of the tube (the
PMD's pixels were wider than tall), green phosphor, scanlines, bloom, tube
curvature, vignette and grain.

    python3 tools/pmd85-screen.py extract capture.png tools/raster/listing.png
    python3 tools/pmd85-screen.py render tools/raster/listing.png images/pmd85-screen.jpg
"""

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SCR_W, SCR_H = 288, 256   # the PMD 85 raster
ZOOM = 3                  # emulator scaler used for the captures

SCALE = 5                 # logical pixel -> raster pixels when rendering
PIXEL_ASPECT = 4 / 3      # 288x256 shown on a 4:3 tube
OUT_W = 1024              # width of the glass area in the final image
BEZEL = 46                # frame thickness in final pixels

# Sampled off a photograph of a real PMD 85 on a Tesla PMD-60.1: the unlit
# phosphor is a warm near-black, a lit stroke is a desaturated mint, and the
# beam core photographs as almost white with a green cast.
BG = np.array([18, 20, 13], dtype=np.float32)       # unlit phosphor
INK = np.array([96, 196, 134], dtype=np.float32)    # a lit stroke
HOT = np.array([216, 253, 238], dtype=np.float32)   # beam core
OVERSCAN = (0.075, 0.055)                           # black margin around the raster


def extract(capture_path, raster_path):
    """Find the emulator viewport in a window capture and reduce it to 288x256."""
    img = np.asarray(Image.open(capture_path).convert('L'), dtype=np.float32)
    h, w = img.shape
    vw, vh = SCR_W * ZOOM, SCR_H * ZOOM
    if w < vw or h < vh:
        raise SystemExit('capture %dx%d is smaller than the %dx%d viewport'
                         % (w, h, vw, vh))

    # The viewport is the only region where every 3x3 block is flat, so score
    # candidate offsets by how flat the blocks come out.
    best, best_at = None, (0, 0)
    for y in range(0, h - vh + 1):
        for x in range(0, w - vw + 1):
            win = img[y:y + vh, x:x + vw]
            blocks = win.reshape(SCR_H, ZOOM, SCR_W, ZOOM)
            err = float(np.abs(blocks - blocks.mean(axis=(1, 3), keepdims=True)).sum())
            if best is None or err < best:
                best, best_at = err, (x, y)
    x, y = best_at
    win = img[y:y + vh, x:x + vw].reshape(SCR_H, ZOOM, SCR_W, ZOOM).mean(axis=(1, 3))
    Image.fromarray((win > 127).astype(np.uint8) * 255, 'L').convert('1').save(raster_path)
    print('%s  viewport at %d,%d  block error %.0f' % (raster_path, x, y, best))


def curve(img, k=0.055):
    """Bend the flat raster over a slightly convex tube."""
    h, w = img.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xs / (w - 1) * 2 - 1
    v = ys / (h - 1) * 2 - 1
    r2 = u * u + v * v
    su = u * (1 + k * r2 * (1 + 0.35 * v * v))
    sv = v * (1 + k * r2 * (1 + 0.35 * u * u))
    sx = (su + 1) / 2 * (w - 1)
    sy = (sv + 1) / 2 * (h - 1)
    inside = (sx >= 0) & (sx <= w - 1) & (sy >= 0) & (sy <= h - 1)
    x0 = np.clip(np.floor(sx), 0, w - 2).astype(np.int32)
    y0 = np.clip(np.floor(sy), 0, h - 2).astype(np.int32)
    fx = (sx - x0)[..., None]
    fy = (sy - y0)[..., None]
    out = (img[y0, x0] * (1 - fx) * (1 - fy)
           + img[y0, x0 + 1] * fx * (1 - fy)
           + img[y0 + 1, x0] * (1 - fx) * fy
           + img[y0 + 1, x0 + 1] * fx * fy)
    return out * inside[..., None]


def render(raster_path, out_path):
    px = np.asarray(Image.open(raster_path).convert('L'), dtype=np.float32) / 255.0
    if px.shape != (SCR_H, SCR_W):
        raise SystemExit('expected a %dx%d raster, got %dx%d'
                         % (SCR_W, SCR_H, px.shape[1], px.shape[0]))

    # blow the logical pixels up, leaving a hair of gap so the phosphor grid shows
    big = np.repeat(np.repeat(px, SCALE, axis=0), SCALE, axis=1)
    big[SCALE - 1::SCALE, :] *= 0.55
    big[:, SCALE - 1::SCALE] *= 0.80

    # the raster was not square on a 4:3 tube
    flat_h = SCR_H * SCALE
    flat_w = int(round(flat_h * PIXEL_ASPECT))
    img = Image.fromarray((np.clip(big, 0, 1) * 255).astype(np.uint8), 'L')
    img = img.resize((flat_w, flat_h), Image.LANCZOS)

    # scanlines follow the 256 lines of the raster - on the real tube they are
    # barely there, the strokes bleed into each other vertically
    a = np.asarray(img, dtype=np.float32) / 255.0
    y = np.arange(flat_h, dtype=np.float32)
    a *= (0.90 + 0.10 * np.cos(2 * np.pi * y / SCALE))[:, None]

    # the raster never reached the edge of the tube; pad before the bloom so the
    # glow spills over the edge instead of stopping at a hard rectangle
    mx = int(round(a.shape[1] * OVERSCAN[0]))
    my = int(round(a.shape[0] * OVERSCAN[1]))
    a = np.pad(a, ((my, my), (mx, mx)))

    # phosphor bloom: a tight halo plus a wide glow
    lum = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), 'L')
    near = np.asarray(lum.filter(ImageFilter.GaussianBlur(2.4)), np.float32) / 255.0
    far = np.asarray(lum.filter(ImageFilter.GaussianBlur(16.0)), np.float32) / 255.0
    inten = a * 1.45 + near * 0.55 + far * 0.28

    # intensity -> phosphor colour, blooming towards white where the beam piles up
    i = np.clip(inten, 0, 1)[..., None]
    over = np.clip(inten - 1.05, 0, 1.2)[..., None]
    rgb = BG + i * (INK - BG) + over * (HOT - INK)

    rgb = curve(rgb)

    # vignette and a soft sheen on the glass
    h, w = rgb.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    u = xs / (w - 1) * 2 - 1
    v = ys / (h - 1) * 2 - 1
    rgb *= np.clip(1.0 - 0.28 * (u * u + v * v) ** 2.2, 0, 1)[..., None]
    sheen = np.clip(1.0 - ((u + 0.5) ** 2 + (v + 0.85) ** 2) / 2.2, 0, 1) ** 2
    rgb += sheen[..., None] * np.array([9, 12, 10], dtype=np.float32)

    # a little film grain so it does not read as vector art
    rng = np.random.default_rng(41)
    rgb += rng.normal(0, 3.0, rgb.shape).astype(np.float32)

    screen = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    out_h = int(round(OUT_W * h / w))
    screen = screen.resize((OUT_W, out_h), Image.LANCZOS)

    # rounded glass inside a dark bezel
    canvas = Image.new('RGB', (OUT_W + 2 * BEZEL, out_h + 2 * BEZEL), (26, 27, 24))
    frame = ImageDraw.Draw(canvas)
    frame.rounded_rectangle([6, 6, canvas.width - 7, canvas.height - 7],
                            radius=26, outline=(58, 58, 52), width=2)
    frame.rounded_rectangle([BEZEL - 8, BEZEL - 8, OUT_W + BEZEL + 7, out_h + BEZEL + 7],
                            radius=22, fill=(12, 12, 11))

    mask = Image.new('L', screen.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, OUT_W - 1, out_h - 1], radius=18, fill=255)
    canvas.paste(screen, (BEZEL, BEZEL), mask)

    if out_path.lower().endswith(('.jpg', '.jpeg')):
        canvas.save(out_path, quality=90, subsampling=0, optimize=True, progressive=True)
    else:
        canvas.save(out_path, optimize=True)
    print('%s  %dx%d' % (out_path, canvas.width, canvas.height))


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in ('extract', 'render'):
        raise SystemExit(__doc__)
    (extract if sys.argv[1] == 'extract' else render)(sys.argv[2], sys.argv[3])
