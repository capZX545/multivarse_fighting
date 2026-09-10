"""
پایپ‌لاین اسپرایت: تصویر خام (پس‌زمینه مجنتا) -> فریم‌های شفاف جداگانه + اطلس

استفاده:
  python tools/sprites.py slice  <raw.png> <out_dir> <prefix> [--rows N --cols N] [--min-area N]
  python tools/sprites.py single <raw.png> <out.png>
  python tools/sprites.py sheet  <frames_dir> <out.png>          (کانتکت‌شیت برای بازبینی)
  python tools/sprites.py gif    <frames_dir> <prefix> <out.gif> [dur_ms]
"""
import sys, os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage


def chroma_key(im: Image.Image) -> Image.Image:
    a = np.array(im.convert("RGBA")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # مجنتا و مشتقات کم‌رنگ آن (لبه‌های anti-alias)
    mag = (r > 140) & (b > 110) & (g < 150) & (np.abs(r - b) < 110) & ((r + b) / 2 - g > 60)
    a[mag, 3] = 0
    # خطوط جداکننده‌ی افقی/عمودی تیره که تمام عرض/ارتفاع را می‌گیرند
    alpha = a[..., 3] > 0
    dark = (r + g + b < 90) & alpha
    H, W = alpha.shape
    row_full = dark.sum(axis=1) > W * 0.97
    col_full = dark.sum(axis=0) > H * 0.97
    a[row_full, :, 3] = 0
    a[:, col_full, 3] = 0
    return Image.fromarray(a.astype("uint8"))


def drop_ghosts(a: np.ndarray) -> np.ndarray:
    """حذف افترایمیج‌های نیمه‌شفاف (خاکستری-بنفش کم‌کنتراست)."""
    r, g, b, al = [a[..., i].astype(int) for i in range(4)]
    sat = np.max(a[..., :3], axis=2).astype(int) - np.min(a[..., :3], axis=2).astype(int)
    ghost = (al > 0) & (sat < 40) & (r > 90) & (r < 200) & (np.abs(r - b) < 30)
    a = a.copy()
    a[ghost, 3] = 0
    return a


def split_components(im: Image.Image, min_area=6000, dilate=10):
    a = np.array(im)
    alpha = a[..., 3] > 0
    d = ndimage.binary_dilation(alpha, iterations=dilate)
    lab, n = ndimage.label(d)
    sizes = ndimage.sum(alpha, lab, range(1, n + 1))
    comps = []
    for i, s in enumerate(sizes, 1):
        if s < min_area:
            continue
        m = (lab == i) & alpha
        ys, xs = np.where(m)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        crop = a[y0:y1, x0:x1].copy()
        crop[~m[y0:y1, x0:x1]] = 0
        comps.append({"x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0),
                      "cy": float(ys.mean()), "img": Image.fromarray(crop)})
    return comps


def order_reading(comps, row_tol=0.5):
    """مرتب‌سازی چپ→راست، بالا→پایین با خوشه‌بندی ردیف‌ها."""
    comps = sorted(comps, key=lambda c: c["cy"])
    rows = []
    for c in comps:
        if rows and abs(c["cy"] - rows[-1][-1]["cy"]) < c["h"] * row_tol:
            rows[-1].append(c)
        else:
            rows.append([c])
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda c: c["x"]))
    return out


def clean_frame(img: Image.Image, keep_ratio=0.06):
    a = np.array(img)
    alpha = a[..., 3] > 0
    if not alpha.any():
        return None
    lab, n = ndimage.label(ndimage.binary_dilation(alpha, iterations=3))
    sizes = ndimage.sum(alpha, lab, range(1, n + 1))
    keep = np.zeros_like(alpha)
    for i, s in enumerate(sizes, 1):
        if s >= sizes.max() * keep_ratio:
            keep |= lab == i
    a[~(keep & alpha)] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def slice_raw(raw, out_dir, prefix, rows=None, cols=None, min_area=6000, ghosts=True):
    im = chroma_key(Image.open(raw))
    if ghosts:
        im = Image.fromarray(drop_ghosts(np.array(im)))
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    if rows and cols:
        W, H = im.size
        fw, fh = W / cols, H / rows
        for r in range(rows):
            for c in range(cols):
                cell = im.crop((int(c * fw), int(r * fh), int((c + 1) * fw), int((r + 1) * fh)))
                # بزرگ‌ترین جزء داخل خانه
                comps = split_components(cell, min_area=min_area // 2, dilate=8)
                if not comps:
                    continue
                best = max(comps, key=lambda k: k["w"] * k["h"])
                frames.append(clean_frame(best["img"]))
    else:
        comps = order_reading(split_components(im, min_area=min_area))
        frames = [clean_frame(c["img"]) for c in comps]
    frames = [f for f in frames if f is not None]
    for p in glob.glob(os.path.join(out_dir, f"{prefix}_*.png")):
        os.remove(p)
    for i, f in enumerate(frames):
        f.save(os.path.join(out_dir, f"{prefix}_{i}.png"))
    print(f"{prefix}: {len(frames)} frames", [f.size for f in frames])
    return frames


def single(raw, out):
    im = chroma_key(Image.open(raw))
    im = Image.fromarray(drop_ghosts(np.array(im)))
    comps = split_components(im, min_area=6000)
    best = max(comps, key=lambda k: k["w"] * k["h"])
    f = clean_frame(best["img"])
    # حذف سایه‌ی زیر پا: ردیف‌های پایینی که فقط بنفش تیره/کم‌اشباع هستند
    f.save(out)
    print("single:", f.size)


def contact_sheet(frames_dir, out, prefix=None, H=260):
    pat = f"{prefix}_*.png" if prefix else "*.png"
    files = sorted(glob.glob(os.path.join(frames_dir, pat)),
                   key=lambda p: (p.rsplit("_", 1)[0], int(p.rsplit("_", 1)[1].split(".")[0])))
    groups = {}
    for p in files:
        groups.setdefault(os.path.basename(p).rsplit("_", 1)[0], []).append(Image.open(p))
    rows = []
    for name, fs in groups.items():
        cells = [f.resize((max(1, int(f.width * H / f.height)), H), Image.NEAREST) for f in fs]
        W = sum(c.width for c in cells) + 16 * (len(cells) + 1)
        row = Image.new("RGBA", (W, H + 16), (30, 30, 40, 255))
        x = 16
        for c in cells:
            row.paste(c, (x, 8), c)
            x += c.width + 16
        rows.append(row)
    W = max(r.width for r in rows)
    sheet = Image.new("RGBA", (W, sum(r.height for r in rows)), (30, 30, 40, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(out)
    print("sheet:", out, sheet.size)


def gif(frames_dir, prefix, out, dur=100, H=380, pingpong=False):
    files = sorted(glob.glob(os.path.join(frames_dir, f"{prefix}_*.png")),
                   key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]))
    fs = [Image.open(p) for p in files]
    if pingpong:
        fs = fs + [fs[0]]
    mh = max(f.height for f in fs); mw = max(f.width for f in fs) + 20
    canvas = []
    for f in fs:
        c = Image.new("RGBA", (mw, mh), (30, 30, 40, 255))
        c.paste(f, ((mw - f.width) // 2, mh - f.height), f)
        s = H / mh
        canvas.append(c.resize((int(mw * s), H), Image.NEAREST))
    canvas[0].save(out, save_all=True, append_images=canvas[1:], duration=dur, loop=0, disposal=2)
    print("gif:", out, len(fs))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "slice":
        kw = {}
        args = sys.argv[2:]
        if "--rows" in args:
            kw["rows"] = int(args[args.index("--rows") + 1])
        if "--cols" in args:
            kw["cols"] = int(args[args.index("--cols") + 1])
        if "--min-area" in args:
            kw["min_area"] = int(args[args.index("--min-area") + 1])
        slice_raw(args[0], args[1], args[2], **kw)
    elif cmd == "single":
        single(sys.argv[2], sys.argv[3])
    elif cmd == "sheet":
        contact_sheet(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "gif":
        gif(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 100)
