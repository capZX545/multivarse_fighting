"""استیج پیکسلی پروسیجرال با پارالاکس — تم بر اساس کاراکتر/دنیا."""
import math
import random
import pygame
from pyfighter import settings as S

THEMES = {
    "gojo": {"sky": [(8, 10, 24), (20, 30, 70)], "far": (28, 34, 70), "mid": (40, 48, 92), "near": (60, 70, 120),
             "floor": (200, 205, 220), "floor2": (160, 165, 185), "accent": (90, 160, 255), "kind": "prism"},
    "naruto": {"sky": [(255, 170, 90), (120, 60, 90)], "far": (90, 60, 80), "mid": (70, 90, 60), "near": (50, 80, 50),
               "floor": (150, 120, 80), "floor2": (120, 95, 60), "accent": (230, 110, 40), "kind": "konoha"},
    "sasuke": {"sky": [(30, 12, 28), (90, 20, 40)], "far": (40, 18, 30), "mid": (60, 24, 34), "near": (30, 14, 20),
               "floor": (70, 50, 55), "floor2": (55, 40, 45), "accent": (220, 40, 60), "kind": "konoha"},
    "default": {"sky": [(30, 30, 60), (90, 60, 120)], "far": (50, 45, 90), "mid": (70, 60, 110), "near": (90, 80, 130),
                "floor": (110, 100, 130), "floor2": (85, 78, 105), "accent": (200, 150, 255), "kind": "city"},
}


def _vgrad(w, h, c1, c2):
    s = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        s.fill(tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)), (0, y, w, 1))
    return s


class Stage:
    def __init__(self, theme_key="default", seed=7):
        self.t = THEMES.get(theme_key, THEMES["default"])
        self.rng = random.Random(seed)
        self.W, self.H = S.SCREEN_WIDTH, S.SCREEN_HEIGHT
        self.sky = _vgrad(self.W, S.FLOOR_Y, *self.t["sky"])
        self.far = self._layer(0.25, 260, 420, self.t["far"])
        if self.t["kind"] == "konoha":
            rock = pygame.Surface(self.far[0].get_size(), pygame.SRCALPHA)
            self._hokage_rock(rock)
            rock.blit(self.far[0], (0, 0))
            self.far = (rock, 0.25)
        self.mid = self._layer(0.5, 160, 300, self.t["mid"])
        self.near = self._layer(0.8, 90, 200, self.t["near"])
        self.floor = self._floor()
        self.time = 0
        self.particles = [(self.rng.uniform(0, S.STAGE_WIDTH), self.rng.uniform(50, S.FLOOR_Y - 50), self.rng.uniform(0.3, 1.2)) for _ in range(40)]

    def _layer(self, par, hmin, hmax, col):
        w = int(S.STAGE_WIDTH * par) + self.W
        s = pygame.Surface((w, S.FLOOR_Y), pygame.SRCALPHA)
        x = 0
        kind = self.t["kind"]
        while x < w:
            bw = self.rng.randint(60, 180)
            bh = self.rng.randint(hmin, hmax)
            r = pygame.Rect(x, S.FLOOR_Y - bh, bw, bh)
            pygame.draw.rect(s, col, r)
            dark = tuple(max(0, c - 18) for c in col)
            if kind == "konoha":
                # سقف کاشی و بالکن
                roof = [(x - 8, S.FLOOR_Y - bh), (x + bw // 2, S.FLOOR_Y - bh - 30), (x + bw + 8, S.FLOOR_Y - bh)]
                pygame.draw.polygon(s, (170, 80, 50), roof)
                for wy in range(S.FLOOR_Y - bh + 40, S.FLOOR_Y - 20, 44):
                    for wx in range(x + 12, x + bw - 16, 30):
                        pygame.draw.rect(s, (250, 210, 120) if self.rng.random() < 0.5 else dark, (wx, wy, 14, 20))
            elif kind == "prism":
                pygame.draw.rect(s, dark, r, 3)
                for i in range(3):
                    px = x + self.rng.randint(0, bw)
                    pygame.draw.line(s, self.t["accent"], (px, S.FLOOR_Y - bh), (px + self.rng.randint(-30, 30), S.FLOOR_Y), 1)
            else:
                for wy in range(S.FLOOR_Y - bh + 20, S.FLOOR_Y - 10, 30):
                    for wx in range(x + 10, x + bw - 10, 22):
                        if self.rng.random() < 0.6:
                            pygame.draw.rect(s, (240, 220, 140), (wx, wy, 10, 14))
            x += bw + self.rng.randint(4, 30)
        return s, par

    def _hokage_rock(self, surf):
        """صخره‌ی هوکاگه: کوه با چهار (پنج) چهره‌ی حکاکی‌شده در پس‌زمینه‌ی دور."""
        W = surf.get_width()
        base = S.FLOOR_Y - 150
        pts = [(0, S.FLOOR_Y), (0, base - 120), (W * 0.15, base - 200), (W * 0.5, base - 240), (W * 0.85, base - 190), (W, base - 130), (W, S.FLOOR_Y)]
        pygame.draw.polygon(surf, (120, 100, 90), pts)
        pygame.draw.polygon(surf, (90, 75, 68), pts, 4)
        n = 5
        for i in range(n):
            cx = W * (0.14 + i * 0.18)
            cy = base - 120
            # سر
            pygame.draw.ellipse(surf, (150, 128, 112), (cx - 55, cy - 80, 110, 150))
            pygame.draw.ellipse(surf, (110, 92, 80), (cx - 55, cy - 80, 110, 150), 3)
            # مو / پیشانی
            pygame.draw.polygon(surf, (135, 112, 98), [(cx - 60, cy - 60), (cx - 30, cy - 105), (cx, cy - 85), (cx + 30, cy - 110), (cx + 60, cy - 60)])
            # چشم‌ها، بینی، دهان
            for ex in (cx - 22, cx + 22):
                pygame.draw.ellipse(surf, (90, 75, 68), (ex - 10, cy - 20, 20, 9))
            pygame.draw.line(surf, (100, 84, 74), (cx, cy - 10), (cx - 6, cy + 20), 3)
            pygame.draw.arc(surf, (100, 84, 74), (cx - 18, cy + 25, 36, 18), 3.3, 6.1, 3)
        return surf

    def _floor(self):
        s = pygame.Surface((S.STAGE_WIDTH + self.W, self.H - S.FLOOR_Y))
        s.fill(self.t["floor"])
        for x in range(0, s.get_width(), 64):
            pygame.draw.line(s, self.t["floor2"], (x, 0), (x - 40, s.get_height()), 3)
        pygame.draw.rect(s, self.t["floor2"], (0, 0, s.get_width(), 6))
        return s

    def draw(self, surf, cam):
        self.time += 1
        surf.blit(self.sky, (0, 0))
        for layer, par in (self.far, self.mid, self.near):
            surf.blit(layer, (-int(cam * par), 0))
        # ذرات (چاکرا/گرد و غبار)
        for i, (px, py, sp) in enumerate(self.particles):
            py -= sp
            if py < 0:
                py = S.FLOOR_Y
            self.particles[i] = (px, py, sp)
            sx = (px - cam * 0.9) % (self.W + 40) - 20
            pygame.draw.circle(surf, self.t["accent"], (int(sx), int(py)), 2)
        surf.blit(self.floor, (-int(cam), S.FLOOR_Y))
