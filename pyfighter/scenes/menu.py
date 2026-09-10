"""منوی اصلی."""
import math
import pygame
from pyfighter import settings as S
from pyfighter.scenes.base import Scene
from pyfighter.ui.fonts import draw_text, font
from pyfighter.ui.widgets import MenuList


class MainMenu(Scene):
    ITEMS = ["VERSUS  (P1 vs CPU)", "VERSUS  (P1 vs P2)", "DUNGEON", "SHOP", "UPGRADES", "OPTIONS", "QUIT"]

    def __init__(self, game):
        super().__init__(game)
        self.menu = MenuList(self.ITEMS, (S.SCREEN_WIDTH // 2, 300), 52, game)
        self.t = 0
        self._bg = self._make_bg()

    def _make_bg(self):
        s = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT))
        for y in range(S.SCREEN_HEIGHT):
            k = y / S.SCREEN_HEIGHT
            s.fill((int(10 + 30 * k), int(8 + 10 * k), int(30 + 60 * k)), (0, y, S.SCREEN_WIDTH, 1))
        return s

    def handle_event(self, e):
        r = self.menu.handle_event(e)
        if r is not None:
            self._select(r)

    def _select(self, i):
        from pyfighter.scenes.select import CharacterSelect
        from pyfighter.scenes.shop import ShopScene, UpgradeScene, OptionsScene
        if i == 0:
            self.goto(CharacterSelect(self.game, vs_ai=True))
        elif i == 1:
            self.goto(CharacterSelect(self.game, vs_ai=False))
        elif i == 2:
            from pyfighter.scenes.dungeon_select import DungeonSelect
            self.goto(DungeonSelect(self.game))
        elif i == 3:
            self.goto(ShopScene(self.game))
        elif i == 4:
            self.goto(UpgradeScene(self.game))
        elif i == 5:
            self.goto(OptionsScene(self.game))
        elif i == 6:
            self.game.running = False

    def update(self):
        self.t += 1
        r = self.menu.update()
        if r is not None:
            self._select(r)

    def draw(self, surf):
        surf.blit(self._bg, (0, 0))
        # لوگو
        y = 120 + math.sin(self.t * 0.05) * 6
        draw_text(surf, "MULTIVARSE", 90, (255, 230, 90), center=(S.SCREEN_WIDTH // 2, y))
        draw_text(surf, "FIGHTING", 64, (255, 120, 60), center=(S.SCREEN_WIDTH // 2, y + 75))
        self.menu.draw(surf)
        st = self.game.save
        draw_text(surf, f"GOLD {st['gold']}   GEMS {st['gems']}   LV {st['level']}", 22, S.WHITE, topleft=(20, S.SCREEN_HEIGHT - 40))
        draw_text(surf, f"v{S.VERSION}", 18, S.GRAY, topleft=(S.SCREEN_WIDTH - 90, S.SCREEN_HEIGHT - 30))
        self.game.touch.draw(surf)
