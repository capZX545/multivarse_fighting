"""افکت‌های ضربه/انفجار/دامین به سبک MUGEN (پروسیجرال)."""
import math
import random
import pygame
from pyfighter import settings as S


class Effects:
    def __init__(self):
        self.items = []
        self.flash = 0
        self.flash_col = (255, 255, 255)
        self.domain_t = 0
        self.domain_col = (90, 160, 255)

    def hit_spark(self, pos, strength, col):
        n = {"light": 8, "medium": 12, "heavy": 18, "special": 22, "ultimate": 30}.get(strength, 10)
        size = {"light": 26, "medium": 36, "heavy": 50, "special": 56, "ultimate": 70}.get(strength, 30)
        self.items.append({"kind": "spark", "x": pos[0], "y": pos[1], "t": 0, "life": 10, "size": size, "col": col})
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(4, 12)
            self.items.append({"kind": "p", "x": pos[0], "y": pos[1], "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                               "t": 0, "life": random.randint(10, 20), "col": (255, 240, 180)})
        if strength in ("heavy", "special", "ultimate"):
            self.flash = 3

    def block_spark(self, pos):
        self.items.append({"kind": "block", "x": pos[0], "y": pos[1], "t": 0, "life": 10})

    def explosion(self, pos, col, radius):
        self.items.append({"kind": "boom", "x": pos[0], "y": pos[1], "t": 0, "life": 22, "r": radius, "col": col})
        for _ in range(24):
            a = random.uniform(0, math.tau)
            sp = random.uniform(3, 10)
            self.items.append({"kind": "p", "x": pos[0], "y": pos[1], "vx": math.cos(a) * sp, "vy": math.sin(a) * sp - 2,
                               "t": 0, "life": random.randint(14, 28), "col": col})

    def infinity_stop(self, pos):
        self.items.append({"kind": "inf", "x": pos[0], "y": pos[1], "t": 0, "life": 26})

    def domain(self, col):
        self.domain_t = 150
        self.domain_col = col
        self.flash = 8
        self.flash_col = (255, 255, 255)

    def update(self):
        for it in self.items:
            it["t"] += 1
            if it["kind"] == "p":
                it["x"] += it["vx"]
                it["y"] += it["vy"]
                it["vy"] += 0.5
                it["vx"] *= 0.94
        self.items = [i for i in self.items if i["t"] < i["life"]]
        if self.flash > 0:
            self.flash -= 1
        if self.domain_t > 0:
            self.domain_t -= 1

    def draw(self, surf, cam):
        if self.domain_t > 0:
            # Unlimited Void: تاریکی + حلقه‌های سفید/آبی
            ov = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT), pygame.SRCALPHA)
            a = min(170, (150 - self.domain_t) * 12) if self.domain_t > 30 else self.domain_t * 5
            ov.fill((5, 5, 20, a))
            cx, cy = S.SCREEN_WIDTH // 2, S.SCREEN_HEIGHT // 2
            for i in range(8):
                r = (i * 90 + (150 - self.domain_t) * 6) % 900
                pygame.draw.circle(ov, (*self.domain_col, max(0, 120 - r // 8)), (cx, cy), int(r), 3)
            for k in range(30):
                rr = random.randint(100, 800)
                ang = random.uniform(0, math.tau)
                pygame.draw.circle(ov, (255, 255, 255, 90), (int(cx + math.cos(ang) * rr), int(cy + math.sin(ang) * rr)), 2)
            surf.blit(ov, (0, 0))
        for it in self.items:
            x, y, t = int(it["x"] - cam), int(it["y"]), it["t"]
            k = it["kind"]
            if k == "spark":
                s = it["size"] * (1 + t * 0.15)
                pts = []
                for i in range(8):
                    a = i * math.pi / 4 + t * 0.2
                    r = s if i % 2 == 0 else s * 0.4
                    pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
                pygame.draw.polygon(surf, (255, 255, 255) if t < 3 else it["col"], pts)
                pygame.draw.polygon(surf, (255, 240, 120), pts, 3)
            elif k == "p":
                r = max(1, int(4 * (1 - t / it["life"])))
                pygame.draw.circle(surf, it["col"], (x, y), r)
            elif k == "block":
                r = 20 + t * 4
                pygame.draw.circle(surf, (120, 200, 255), (x, y), r, 4)
                pygame.draw.line(surf, (255, 255, 255), (x - r, y), (x + r, y), 2)
            elif k == "boom":
                r = int(it["r"] * math.sin(min(1, t / it["life"]) * math.pi / 2))
                s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*it["col"], max(0, 180 - t * 8)), (r + 2, r + 2), r)
                pygame.draw.circle(s, (255, 255, 255, max(0, 220 - t * 12)), (r + 2, r + 2), r, 5)
                surf.blit(s, (x - r - 2, y - r - 2))
            elif k == "inf":
                # شش‌ضلعی‌های Infinity
                for i in range(3):
                    r = 30 + i * 18 + t * 2
                    pts = [(x + math.cos(a) * r, y + math.sin(a) * r) for a in [j * math.pi / 3 for j in range(6)]]
                    pygame.draw.polygon(surf, (120, 200, 255), pts, 2)
        if self.flash > 0:
            ov = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT))
            ov.fill(self.flash_col)
            ov.set_alpha(60 * self.flash // 3)
            surf.blit(ov, (0, 0))
