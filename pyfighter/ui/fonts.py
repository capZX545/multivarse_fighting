"""فونت‌ها با کش (فونت پیش‌فرض pygame؛ روی همه پلتفرم‌ها بدون فایل خارجی کار می‌کند)."""
import os
import pygame
from pyfighter import paths

_cache = {}
_FONT_FILE = None
for cand in ("PressStart2P.ttf", "pixel.ttf"):
    p = os.path.join(paths.FONT_DIR, cand)
    if os.path.isfile(p):
        _FONT_FILE = p
        break


def font(size: int) -> pygame.font.Font:
    key = (size, _FONT_FILE)
    if key not in _cache:
        _cache[key] = pygame.font.Font(_FONT_FILE, size)
    return _cache[key]


def draw_text(surf, text, size, color, center=None, topleft=None, shadow=True):
    f = font(size)
    t = f.render(text, True, color)
    r = t.get_rect(center=center) if center else t.get_rect(topleft=topleft)
    if shadow:
        s = f.render(text, True, (0, 0, 0))
        surf.blit(s, r.move(3, 3))
    surf.blit(t, r)
    return r
