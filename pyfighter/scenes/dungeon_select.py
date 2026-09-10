"""انتخاب کاراکتر برای دانجن — حالت دانجن در مرحله‌ی بعدی ساخته می‌شود."""
import pygame
from pyfighter import settings as S
from pyfighter.scenes.base import Scene
from pyfighter.ui.fonts import draw_text


class DungeonSelect(Scene):
    def __init__(self, game):
        super().__init__(game)

    def handle_event(self, e):
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN, pygame.JOYBUTTONDOWN):
            from pyfighter.scenes.menu import MainMenu
            self.goto(MainMenu(self.game))

    def draw(self, surf):
        surf.fill((10, 16, 20))
        draw_text(surf, "DUNGEON MODE", 60, S.YELLOW, center=(S.SCREEN_WIDTH // 2, 200))
        draw_text(surf, "Regions - 5 stages each - 8-20 rooms - Region bosses", 26, S.WHITE, center=(S.SCREEN_WIDTH // 2, 280))
        draw_text(surf, "COMING IN THE NEXT BUILD", 34, S.ORANGE, center=(S.SCREEN_WIDTH // 2, 380))
        draw_text(surf, "press any key", 20, S.GRAY, center=(S.SCREEN_WIDTH // 2, 500))
        self.game.touch.draw(surf)
