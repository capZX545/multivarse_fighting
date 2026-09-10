"""ویجت‌های منو: لیست قابل ناوبری با کیبورد/گیم‌پد/لمس."""
import pygame
from pyfighter import settings as S
from pyfighter.ui.fonts import draw_text, font


class MenuList:
    def __init__(self, items, center, spacing, game, size=40):
        self.items = items
        self.cx, self.cy = center
        self.spacing = spacing
        self.idx = 0
        self.game = game
        self.size = size
        self.rects = []
        self._cd = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self._move(-1)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self._move(1)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_j, pygame.K_KP_ENTER):
                self.game.audio.play("menu_select")
                return self.idx
        elif e.type == pygame.JOYBUTTONDOWN and e.button in (0, 7):
            self.game.audio.play("menu_select")
            return self.idx
        elif e.type == pygame.JOYHATMOTION:
            if e.value[1] > 0:
                self._move(-1)
            elif e.value[1] < 0:
                self._move(1)
        elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            pos = self.game.event_pos(e)
            for i, r in enumerate(self.rects):
                if r.collidepoint(pos):
                    if self.idx == i:
                        self.game.audio.play("menu_select")
                        return i
                    self.idx = i
                    self.game.audio.play("menu_move")
        return None

    def update(self):
        # ناوبری با آنالوگ گیم‌پد
        if self._cd > 0:
            self._cd -= 1
            return None
        for j in self.game.joysticks:
            try:
                ay = j.get_axis(1)
            except pygame.error:
                continue
            if ay < -0.6:
                self._move(-1)
                self._cd = 12
            elif ay > 0.6:
                self._move(1)
                self._cd = 12
        return None

    def _move(self, d):
        self.idx = (self.idx + d) % len(self.items)
        self.game.audio.play("menu_move")

    def draw(self, surf):
        self.rects = []
        for i, t in enumerate(self.items):
            sel = i == self.idx
            col = S.YELLOW if sel else (200, 200, 210)
            r = draw_text(surf, ("> " if sel else "") + t, self.size, col, center=(self.cx, self.cy + i * self.spacing))
            self.rects.append(r.inflate(60, 10))
