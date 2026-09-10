"""
کنترل لمسی (اندروید / موس روی دسکتاپ برای تست).
جوی‌استیک مجازی سمت چپ + دکمه‌های اکشن سمت راست. مختصات در فضای منطقی ۱۲۸۰×۷۲۰.
"""
import math
import pygame
from pyfighter import settings

W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT


class TouchControls:
    def __init__(self, layout="fighter"):
        self.layout = layout
        self.fingers = {}          # finger_id -> (x, y) منطقی
        self.stick_center = (170, H - 170)
        self.stick_radius = 110
        self.stick_finger = None
        self.stick_vec = (0.0, 0.0)
        r = 58
        if layout == "fighter":
            self.buttons = {
                "punch": (W - 280, H - 250, r, (230, 80, 80), "P"),
                "kick": (W - 150, H - 190, r, (80, 160, 240), "K"),
                "special": (W - 210, H - 380, r, (200, 90, 240), "S"),
                "block": (W - 410, H - 150, r, (90, 200, 120), "B"),
                "dash": (W - 340, H - 400, 46, (240, 200, 70), "D"),
                "start": (W - 70, 50, 34, (120, 120, 130), "="),
            }
        else:  # dungeon
            self.buttons = {
                "punch": (W - 150, H - 190, 64, (230, 80, 80), "A"),
                "special": (W - 280, H - 300, r, (200, 90, 240), "S"),
                "dash": (W - 300, H - 130, r, (240, 200, 70), "D"),
                "kick": (W - 420, H - 260, 46, (80, 160, 240), "W"),
                "block": (W - 130, H - 340, 46, (90, 200, 120), "E"),
                "start": (W - 70, 50, 34, (120, 120, 130), "="),
            }
        self.active = {b: False for b in self.buttons}
        self.visible = settings.IS_ANDROID
        self.opacity = 120

    def to_logical(self, x, y, screen_rect):
        """پیکسل پنجره -> فضای منطقی (با توجه به letterbox)."""
        sx = (x - screen_rect.x) / screen_rect.w * W
        sy = (y - screen_rect.y) / screen_rect.h * H
        return sx, sy

    def handle_event(self, e, screen_rect, window_size):
        if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            fid = e.finger_id
            px, py = e.x * window_size[0], e.y * window_size[1]
            pos = self.to_logical(px, py, screen_rect)
            if e.type == pygame.FINGERUP:
                self._up(fid)
            else:
                self.fingers[fid] = pos
                self._recalc()
            self.visible = True
        elif not settings.IS_ANDROID and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            # شبیه‌سازی با موس (فقط دکمه چپ)
            if e.type == pygame.MOUSEBUTTONUP:
                self._up("mouse")
            elif e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.MOUSEMOTION and e.buttons[0]):
                if e.type == pygame.MOUSEMOTION and "mouse" not in self.fingers:
                    return
                self.fingers["mouse"] = self.to_logical(*e.pos, screen_rect)
                self._recalc()

    def _up(self, fid):
        self.fingers.pop(fid, None)
        if self.stick_finger == fid:
            self.stick_finger = None
            self.stick_vec = (0.0, 0.0)
        self._recalc()

    def _recalc(self):
        for b in self.active:
            self.active[b] = False
        stick_found = False
        for fid, (x, y) in self.fingers.items():
            cx, cy = self.stick_center
            if fid == self.stick_finger or (not stick_found and x < W * 0.42 and not self.stick_finger):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if fid == self.stick_finger or d < self.stick_radius * 2.2:
                    self.stick_finger = fid
                    stick_found = True
                    if d > self.stick_radius:
                        dx, dy = dx / d * self.stick_radius, dy / d * self.stick_radius
                    self.stick_vec = (dx / self.stick_radius, dy / self.stick_radius)
                    continue
            for name, (bx, by, r, _, _) in self.buttons.items():
                if math.hypot(x - bx, y - by) <= r * 1.25:
                    self.active[name] = True
        if not stick_found and self.stick_finger not in self.fingers:
            self.stick_finger = None
            self.stick_vec = (0.0, 0.0)

    def read(self) -> dict:
        vx, vy = self.stick_vec
        dz = 0.35
        out = {"left": vx < -dz, "right": vx > dz, "up": vy < -0.5, "down": vy > 0.5, "vx": vx, "vy": vy}
        out.update(self.active)
        return out

    def draw(self, surf):
        if not self.visible:
            return
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = self.stick_center
        pygame.draw.circle(ov, (255, 255, 255, 40), (cx, cy), self.stick_radius)
        pygame.draw.circle(ov, (255, 255, 255, 90), (cx, cy), self.stick_radius, 3)
        kx, ky = cx + self.stick_vec[0] * self.stick_radius * 0.7, cy + self.stick_vec[1] * self.stick_radius * 0.7
        pygame.draw.circle(ov, (255, 255, 255, 140), (int(kx), int(ky)), 44)
        font = pygame.font.Font(None, 44)
        for name, (bx, by, r, col, label) in self.buttons.items():
            a = 190 if self.active[name] else self.opacity
            pygame.draw.circle(ov, (*col, a), (bx, by), r)
            pygame.draw.circle(ov, (255, 255, 255, a), (bx, by), r, 3)
            t = font.render(label, True, (255, 255, 255))
            ov.blit(t, t.get_rect(center=(bx, by)))
        surf.blit(ov, (0, 0))
