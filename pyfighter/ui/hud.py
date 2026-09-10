"""HUD مبارزه: نوار سلامتی با آسیب تأخیری، Meter سه‌خانه، تایمر، نام، پرتره، کمبو، پیام‌های وسط."""
import pygame
from pyfighter import settings as S
from pyfighter.ui.fonts import font


class FightHUD:
    def __init__(self, f1, f2):
        self.f1, self.f2 = f1, f2
        self.delayed = [f1.health, f2.health]
        self.p1 = pygame.transform.smoothscale(f1.sprites.portrait, (84, 84))
        self.p2 = pygame.transform.smoothscale(f2.sprites.portrait, (84, 84))
        self.p2 = pygame.transform.flip(self.p2, True, False)
        self.msg = ""
        self.msg_t = 0
        self.msg_scale = 1.0
        self.combo_t = [0, 0]
        self.combo_n = [0, 0]

    def message(self, text, frames=90):
        self.msg, self.msg_t = text, frames

    def combo(self, idx, n):
        self.combo_n[idx] = n
        self.combo_t[idx] = 70

    def draw(self, surf, timer, round_no, wins):
        W = S.SCREEN_WIDTH
        bar_w, bar_h, top = 500, 26, 30
        for i, (f, x0, right) in enumerate(((self.f1, 110, False), (self.f2, W - 110 - bar_w, True))):
            # آسیب تأخیری
            if self.delayed[i] > f.health:
                self.delayed[i] = max(f.health, self.delayed[i] - 4)
            else:
                self.delayed[i] = f.health
            pygame.draw.rect(surf, (20, 20, 25), (x0 - 3, top - 3, bar_w + 6, bar_h + 6))
            pygame.draw.rect(surf, (70, 20, 20), (x0, top, bar_w, bar_h))
            dw = int(bar_w * self.delayed[i] / f.max_health)
            hw = int(bar_w * f.health / f.max_health)
            col = S.HEALTH_GREEN if f.health > f.max_health * 0.3 else (240, 160, 50)
            if right:
                pygame.draw.rect(surf, S.HEALTH_DAMAGE, (x0 + bar_w - dw, top, dw, bar_h))
                pygame.draw.rect(surf, col, (x0 + bar_w - hw, top, hw, bar_h))
            else:
                pygame.draw.rect(surf, S.HEALTH_DAMAGE, (x0, top, dw, bar_h))
                pygame.draw.rect(surf, col, (x0, top, hw, bar_h))
            # براقی
            pygame.draw.rect(surf, (255, 255, 255), (x0, top, bar_w, 5))
            # نام
            name = font(26).render(f.d.display_name.upper(), True, S.WHITE)
            surf.blit(name, (x0 + (bar_w - name.get_width() if right else 0), top + bar_h + 4))
            # پرتره
            pr = self.p2 if right else self.p1
            px = W - 100 if right else 16
            pygame.draw.rect(surf, S.DARK, (px - 3, top - 8, 90, 90))
            surf.blit(pr, (px, top - 5))
            # برد راند
            for k in range(S.ROUNDS_TO_WIN):
                cx = (x0 + bar_w - 16 - k * 26) if right else (x0 + 16 + k * 26)
                pygame.draw.circle(surf, S.YELLOW if wins[i] > k else (50, 50, 60), (cx, top + bar_h + 48), 9)
                pygame.draw.circle(surf, S.WHITE, (cx, top + bar_h + 48), 9, 2)
            # Meter
            my = S.SCREEN_HEIGHT - 46
            seg_w = 120
            for k in range(3):
                sx = (W - 40 - (k + 1) * (seg_w + 6)) if right else (40 + k * (seg_w + 6))
                pygame.draw.rect(surf, (25, 25, 35), (sx, my, seg_w, 16))
                fill = max(0, min(100, f.meter - k * 100)) / 100
                if fill > 0:
                    fw = int(seg_w * fill)
                    c = S.METER_FULL if f.meter >= 300 else S.METER_BLUE
                    pygame.draw.rect(surf, c, ((sx + seg_w - fw) if right else sx, my, fw, 16))
                pygame.draw.rect(surf, S.WHITE, (sx, my, seg_w, 16), 2)
            if f.transform:
                t = font(20).render(f.transform.upper() + f" {f.transform_t // 60 + 1}s", True, S.YELLOW)
                surf.blit(t, (x0 + (bar_w - t.get_width() if right else 0), my - 24))
            # کمبو
            if self.combo_t[i] > 0:
                self.combo_t[i] -= 1
                n = self.combo_n[i]
                if n >= 2:
                    cx = W - 300 if not right else 300   # نمایش سمت حریف
                    txt = font(56).render(f"{n} HITS", True, S.YELLOW)
                    sh = font(56).render(f"{n} HITS", True, S.BLACK)
                    surf.blit(sh, (cx - txt.get_width() // 2 + 3, 203))
                    surf.blit(txt, (cx - txt.get_width() // 2, 200))
        # تایمر
        pygame.draw.rect(surf, S.DARK, (W // 2 - 50, top - 8, 100, 62))
        t = font(54).render(f"{max(0, int(timer)):02d}", True, S.WHITE if timer > 10 else S.RED)
        surf.blit(t, t.get_rect(center=(W // 2, top + 24)))
        r = font(18).render(f"ROUND {round_no}", True, S.GRAY)
        surf.blit(r, r.get_rect(center=(W // 2, top + 66)))
        # پیام
        if self.msg_t > 0:
            self.msg_t -= 1
            sc = 1.0 + 0.15 * max(0, (self.msg_t - 70) / 20) if self.msg_t > 70 else 1.0
            txt = font(int(96 * sc)).render(self.msg, True, S.YELLOW)
            sh = font(int(96 * sc)).render(self.msg, True, S.BLACK)
            c = (W // 2, S.SCREEN_HEIGHT // 2 - 60)
            surf.blit(sh, sh.get_rect(center=(c[0] + 4, c[1] + 4)))
            surf.blit(txt, txt.get_rect(center=c))
