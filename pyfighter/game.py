"""حلقه‌ی اصلی بازی: پنجره با مقیاس‌بندی letterbox، مدیریت صحنه، ورودی‌ها، ذخیره."""
import os
import sys
import pygame

from pyfighter import settings as S
from pyfighter.systems.audio import Audio
from pyfighter.systems.touch import TouchControls
from pyfighter.systems.save import load_state, save_state


class Game:
    def __init__(self):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        pygame.display.set_caption(S.TITLE)
        self.fullscreen = S.IS_ANDROID
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        if S.IS_ANDROID:
            self.window = pygame.display.set_mode((0, 0), flags)
        else:
            self.window = pygame.display.set_mode((S.SCREEN_WIDTH, S.SCREEN_HEIGHT), flags)
        self.canvas = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT)).convert()
        self.clock = pygame.time.Clock()
        self.running = True
        self.audio = Audio()
        self.touch = TouchControls()
        self.save = load_state()
        pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joysticks.append(j)
        from pyfighter.scenes.menu import MainMenu
        self.scene = MainMenu(self)
        self.screen_rect = self._compute_rect()
        self.show_fps = False

    # ---------- مقیاس‌بندی ----------
    def _compute_rect(self):
        ww, wh = self.window.get_size()
        scale = min(ww / S.SCREEN_WIDTH, wh / S.SCREEN_HEIGHT)
        w, h = int(S.SCREEN_WIDTH * scale), int(S.SCREEN_HEIGHT * scale)
        return pygame.Rect((ww - w) // 2, (wh - h) // 2, w, h)

    def event_pos(self, e):
        """موقعیت رویداد موس/لمس در مختصات منطقی."""
        if e.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
            ww, wh = self.window.get_size()
            px, py = e.x * ww, e.y * wh
        else:
            px, py = e.pos
        r = self.screen_rect
        return ((px - r.x) / r.w * S.SCREEN_WIDTH, (py - r.y) / r.h * S.SCREEN_HEIGHT)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((S.SCREEN_WIDTH, S.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.screen_rect = self._compute_rect()

    # ---------- حلقه ----------
    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.window = pygame.display.set_mode(e.size, pygame.RESIZABLE)
                    self.screen_rect = self._compute_rect()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F3:
                    self.show_fps = not self.show_fps
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_AC_BACK:   # دکمه back اندروید
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", scancode=0)
                    self.scene.handle_event(e)
                    continue
                elif e.type == pygame.JOYDEVICEADDED:
                    j = pygame.joystick.Joystick(e.device_index)
                    j.init()
                    self.joysticks.append(j)
                self.touch.handle_event(e, self.screen_rect, self.window.get_size())
                self.scene.handle_event(e)
            self.scene.update()
            if self.scene.next_scene is not None:
                self.scene = self.scene.next_scene
            self.scene.draw(self.canvas)
            if self.show_fps:
                from pyfighter.ui.fonts import draw_text
                draw_text(self.canvas, f"{self.clock.get_fps():.0f} FPS", 18, S.GREEN, topleft=(S.SCREEN_WIDTH - 90, 4))
            self.window.fill((0, 0, 0))
            if self.screen_rect.size == self.canvas.get_size():
                self.window.blit(self.canvas, self.screen_rect.topleft)
            else:
                pygame.transform.smoothscale(self.canvas, self.screen_rect.size, self.window.subsurface(self.screen_rect))
            pygame.display.flip()
            self.clock.tick(S.FPS)
        save_state(self.save)
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
