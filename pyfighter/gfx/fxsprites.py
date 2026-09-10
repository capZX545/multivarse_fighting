"""بارگذاری اسپرایت‌های افکت (پرتابه/جادو) از assets/fx/<slug>/<name>_<i>.png با کش مقیاس."""
import os
import glob
import pygame
from pyfighter import paths

_CACHE = {}
_SCALED = {}


def frames(slug, name):
    key = (slug, name)
    if key not in _CACHE:
        d = os.path.join(paths.ASSETS, "fx", slug)
        files = sorted(glob.glob(os.path.join(d, f"{name}_*.png")),
                       key=lambda p: int(os.path.splitext(p)[0].rsplit("_", 1)[1]))
        _CACHE[key] = [pygame.image.load(f).convert_alpha() for f in files]
    return _CACHE[key]


def has(slug, name):
    return bool(frames(slug, name))


def frame(slug, name, i, height=None, width=None, flip=False):
    """فریم i (چرخشی) با ارتفاع یا عرض هدف؛ نتیجه کش می‌شود."""
    fr = frames(slug, name)
    if not fr:
        return None
    img = fr[i % len(fr)]
    w, h = img.get_size()
    if height:
        sc = height / h
    elif width:
        sc = width / w
    else:
        sc = 1.0
    size = (max(1, int(w * sc)), max(1, int(h * sc)))
    k = (slug, name, i % len(fr), size, flip)
    if k not in _SCALED:
        s = pygame.transform.smoothscale(img, size)
        if flip:
            s = pygame.transform.flip(s, True, False)
        _SCALED[k] = s
    return _SCALED[k]
