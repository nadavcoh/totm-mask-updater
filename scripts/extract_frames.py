#!/usr/bin/env python3
"""Turn a Tomb of the Mask 'Masks' screen recording into a handful of readable contact sheets.

The recording is a horizontally scrolling grid (2 rows x N columns of mask cards). Reading it
frame by frame is slow, so this script:
  1. extracts the card-grid region at 30 fps,
  2. drops frames that are not the grid (iOS control center at the end, etc.),
  3. estimates how far the grid has scrolled in each frame,
  4. picks the SHARPEST frame (slowest scroll = least ghosting) every ~60% of a screen width,
     so consecutive frames overlap by ~40% and no column is missed,
  5. stacks the picks two at a time into tall sheets (frame A on top of frame B, separated by a magenta bar).

Usage:  extract_frames.py VIDEO [--outdir /tmp/totm] [--fps 30] [--spacing 0.6] [--crop Y0,H]
Prints a manifest (also saved as OUTDIR/manifest.json). View OUTDIR/sheets/pair_*.png in order.
To zoom on a doubtful card:  extract_frames.py VIDEO --zoom 6.55 --outdir /tmp/totm
"""
import argparse, json, os, subprocess, sys, shutil, glob
import numpy as np
from PIL import Image, ImageDraw

W = 563  # working width of each frame (original is ~1126 px)

def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def probe(video):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height:format=duration', '-of', 'json', video])
    j = json.loads(out)
    return j['streams'][0]['width'], j['streams'][0]['height'], float(j['format']['duration'])

def grid_crop(w, h, override):
    # On the 1126x2436 iPhone recording the card grid spans y=940..2130 (38.6% .. 87.4% of the height).
    if override:
        y0, ch = [int(x) for x in override.split(',')]
    else:
        y0, ch = round(0.386 * h), round(0.4885 * h)
    return y0, ch

def yellow_fraction(img):
    a = np.asarray(img.convert('RGB')).astype(int)
    return float(((a[..., 0] > 225) & (a[..., 1] > 215) & (a[..., 2] < 70)).mean())

def shift_between(a, b, rng=150):
    """Horizontal scroll (px, at W scale) between two column-brightness profiles."""
    best, bs = 0, 1e18
    for s in range(-rng, rng + 1):
        d = np.abs(a[s:] - b[:len(b) - s]).mean() if s >= 0 else np.abs(a[:s] - b[-s:]).mean()
        if d < bs:
            bs, best = d, s
    return best

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--outdir', default='/tmp/totm')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--spacing', type=float, default=0.6, help='gap between picked frames as a fraction of screen width')
    ap.add_argument('--crop', help='Y0,H of the card grid in the ORIGINAL video if auto-crop is wrong')
    ap.add_argument('--zoom', type=float, help='extract one full-resolution crop at this time (s) and exit')
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    vw, vh, dur = probe(a.video)
    y0, ch = grid_crop(vw, vh, a.crop)

    if a.zoom is not None:
        p = os.path.join(a.outdir, f'zoom_{a.zoom}.png')
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.zoom), '-i', a.video, '-frames:v', '1',
             '-vf', f'crop={vw}:{ch}:0:{y0}', p])
        print(p); return

    # coin balance lives in the header of the first frame; save it so it can be read without another ffmpeg call
    hp = os.path.join(a.outdir, 'header.png')
    run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-frames:v', '1', '-vf',
         f'crop={vw}:{round(0.07 * vh)}:0:{round(0.05 * vh)},scale={W}:-1', hp])

    fdir = os.path.join(a.outdir, 'frames')
    shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    run(['ffmpeg', '-v', 'error', '-i', a.video, '-vf', f'fps={a.fps},crop={vw}:{ch}:0:{y0},scale={W}:-1',
         os.path.join(fdir, 'f_%04d.png')])
    files = sorted(glob.glob(os.path.join(fdir, 'f_*.png')))

    # keep only frames that actually show the card grid (cards are bright yellow; control center is ~0%)
    kept = []
    for i, f in enumerate(files):
        im = Image.open(f)
        if yellow_fraction(im) >= 0.1:
            kept.append((i, f, np.asarray(im.convert('L'), dtype=float).mean(0)))
    if not kept:
        sys.exit('No frames look like the mask grid. Check --crop (Y0,H in original pixels).')

    offs = [0]
    for k in range(1, len(kept)):
        offs.append(offs[-1] + shift_between(kept[k - 1][2], kept[k][2]))
    speed = [0] + [abs(offs[k] - offs[k - 1]) for k in range(1, len(offs))]
    lo, hi = min(offs), max(offs)
    S = a.spacing * W

    picks = []
    t = lo
    while True:
        cand = [k for k in range(len(kept)) if abs(offs[k] - t) <= 0.2 * S]
        if cand:
            k = min(cand, key=lambda k: (speed[k], abs(offs[k] - t)))
            if not picks or picks[-1] != k:
                picks.append(k)
        if t >= hi:
            break
        t = min(t + S, hi)
    plateau = [k for k in range(len(kept)) if offs[k] >= hi - 5]
    last = min(plateau, key=lambda k: speed[k])
    if picks[-1] != last:
        picks.append(last)

    sdir = os.path.join(a.outdir, 'sheets')
    shutil.rmtree(sdir, ignore_errors=True); os.makedirs(sdir)
    manifest = {'video': a.video, 'fps': a.fps, 'grid_crop': [y0, ch], 'frames': [], 'sheets': []}
    for n, k in enumerate(picks):
        manifest['frames'].append({'n': n, 'time_s': round(kept[k][0] / a.fps, 2), 'scroll_px': int(offs[k] - lo)})
    for s in range(0, len(picks), 2):
        ims = [Image.open(kept[k][1]).convert('RGB') for k in picks[s:s + 2]]
        h = ims[0].size[1]
        gap = 10
        sheet = Image.new('RGB', (W, h * len(ims) + gap * (len(ims) - 1)), (255, 0, 255))
        for j, im in enumerate(ims):
            sheet.paste(im, (0, j * (h + gap)))
            ImageDraw.Draw(sheet).text((4, j * (h + gap) + 2), f'#{s + j}', fill=(255, 0, 0))
        p = os.path.join(sdir, f'pair_{s // 2:02d}.png')
        sheet.save(p)
        manifest['sheets'].append({'path': p, 'frames': [s + j for j in range(len(ims))]})
    json.dump(manifest, open(os.path.join(a.outdir, 'manifest.json'), 'w'), indent=1)
    print('Coin balance (read it for spec.coins):', hp)
    print(f"{len(files)} frames -> {len(kept)} grid frames -> {len(picks)} picks -> {len(manifest['sheets'])} sheets")
    cols = (hi - lo) / 225 + 2.5
    print(f"total scroll ~{hi - lo}px  (~{cols:.0f} columns, roughly {round(cols * 2)} masks; the last column may hold only one)")
    for sh in manifest['sheets']:
        print(sh['path'], 'frames', sh['frames'], [manifest['frames'][i]['time_s'] for i in sh['frames']], 's')

if __name__ == '__main__':
    main()
