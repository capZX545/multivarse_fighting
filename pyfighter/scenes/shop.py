"""فروشگاه اصلی، ارتقای دائمی کاراکتر، تنظیمات."""
import pygame
from pyfighter import settings as S
from pyfighter.scenes.base import Scene
from pyfighter.ui.fonts import draw_text
from pyfighter.ui.widgets import MenuList
from pyfighter.data import characters_db as db
from pyfighter.systems.save import save_state


class ShopScene(Scene):
    """خرید کاراکتر (فقط قابل‌بازی‌ها قابل خریدند)، لباس، Buff."""

    def __init__(self, game):
        super().__init__(game)
        st = game.save
        self.items = []
        for c in db.playable():
            if c["slug"] not in st["unlocked"]:
                self.items.append(("char", c["slug"], f"UNLOCK {c['name']}", c["brick_cost"], 0))
        for c in db.playable():
            owned = st["costumes"].get(c["slug"], [0])
            for i, label in enumerate(("Costume 2", "Costume 3")):
                idx = i + 1
                if idx not in owned:
                    self.items.append(("costume", (c["slug"], idx), f"{c['name']} — {label}", 250 if idx == 1 else 0, 0 if idx == 1 else 4))
        self.items.append(("gold_for_gems", None, "EXCHANGE 1 GEM -> 150 GOLD", 0, 1))
        self.items.append(("back", None, "BACK", 0, 0))
        self.menu = MenuList([self._label(it) for it in self.items], (S.SCREEN_WIDTH // 2, 200), 46, game, size=30)

    def _label(self, it):
        kind, _, text, gold, gems = it
        if kind == "back":
            return text
        cost = f"{gold} G" if gold else f"{gems} GEM"
        return f"{text}   [{cost}]"

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._back()
            return
        r = self.menu.handle_event(e)
        if r is not None:
            self._buy(r)

    def _back(self):
        from pyfighter.scenes.menu import MainMenu
        self.goto(MainMenu(self.game))

    def _buy(self, i):
        kind, key, text, gold, gems = self.items[i]
        st = self.game.save
        if kind == "back":
            self._back()
            return
        if st["gold"] < gold or st["gems"] < gems:
            self.game.audio.play("error")
            return
        st["gold"] -= gold
        st["gems"] -= gems
        if kind == "char":
            st["unlocked"].append(key)
        elif kind == "costume":
            slug, idx = key
            st["costumes"].setdefault(slug, [0]).append(idx)
        elif kind == "gold_for_gems":
            st["gold"] += 150
        save_state(st)
        self.game.audio.play("buy")
        self.__init__(self.game)

    def draw(self, surf):
        surf.fill((16, 14, 30))
        draw_text(surf, "SHOP", 60, S.YELLOW, center=(S.SCREEN_WIDTH // 2, 70))
        st = self.game.save
        draw_text(surf, f"GOLD {st['gold']}   GEMS {st['gems']}", 26, S.WHITE, center=(S.SCREEN_WIDTH // 2, 130))
        self.menu.draw(surf)
        self.game.touch.draw(surf)


STAT_KEYS = ("hp", "atk", "def", "spd", "tech")
UPGRADE_COST = [100, 180, 300, 480, 700]


class UpgradeScene(Scene):
    """ارتقای دائمی آمار کاراکتر (برای حالت دانجن و کمی در فایتینگ)."""

    def __init__(self, game):
        super().__init__(game)
        self.chars = [c for c in db.playable() if c["slug"] in game.save["unlocked"]]
        self.ci = 0
        self.si = 0

    def handle_event(self, e):
        st = self.game.save
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                from pyfighter.scenes.menu import MainMenu
                self.goto(MainMenu(self.game))
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.ci = (self.ci - 1) % len(self.chars)
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.ci = (self.ci + 1) % len(self.chars)
            elif e.key in (pygame.K_UP, pygame.K_w):
                self.si = (self.si - 1) % len(STAT_KEYS)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.si = (self.si + 1) % len(STAT_KEYS)
            elif e.key in (pygame.K_RETURN, pygame.K_j, pygame.K_SPACE):
                self._buy()
        elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            pos = self.game.event_pos(e)
            if pos[1] < 120:
                if pos[0] < S.SCREEN_WIDTH // 2:
                    self.ci = (self.ci - 1) % len(self.chars)
                else:
                    self.ci = (self.ci + 1) % len(self.chars)
            elif 200 <= pos[1] < 200 + 60 * len(STAT_KEYS):
                i = (pos[1] - 200) // 60
                if i == self.si:
                    self._buy()
                else:
                    self.si = i
            else:
                from pyfighter.scenes.menu import MainMenu
                self.goto(MainMenu(self.game))

    def _buy(self):
        st = self.game.save
        slug = self.chars[self.ci]["slug"]
        up = st["upgrades"].setdefault(slug, {k: 0 for k in STAT_KEYS})
        k = STAT_KEYS[self.si]
        lvl = up.get(k, 0)
        if lvl >= len(UPGRADE_COST):
            self.game.audio.play("error")
            return
        cost = UPGRADE_COST[lvl]
        if st["gold"] < cost:
            self.game.audio.play("error")
            return
        st["gold"] -= cost
        up[k] = lvl + 1
        save_state(st)
        self.game.audio.play("buy")

    def draw(self, surf):
        surf.fill((14, 18, 30))
        st = self.game.save
        c = self.chars[self.ci]
        draw_text(surf, f"<  {c['name'].upper()}  >", 44, S.YELLOW, center=(S.SCREEN_WIDTH // 2, 60))
        draw_text(surf, f"GOLD {st['gold']}", 24, S.WHITE, center=(S.SCREEN_WIDTH // 2, 110))
        up = st["upgrades"].get(c["slug"], {})
        for i, k in enumerate(STAT_KEYS):
            y = 200 + i * 60
            lvl = up.get(k, 0)
            sel = i == self.si
            col = S.YELLOW if sel else S.WHITE
            draw_text(surf, k.upper(), 32, col, topleft=(300, y))
            for j in range(len(UPGRADE_COST)):
                pygame.draw.rect(surf, (90, 200, 120) if j < lvl else (40, 40, 60), (450 + j * 60, y + 6, 50, 24))
                pygame.draw.rect(surf, S.WHITE, (450 + j * 60, y + 6, 50, 24), 2)
            cost = UPGRADE_COST[lvl] if lvl < len(UPGRADE_COST) else None
            draw_text(surf, f"{cost} G" if cost else "MAX", 26, col, topleft=(800, y))
            base = c["stats"][k]
            draw_text(surf, f"{base} -> {base + lvl * 4}", 22, S.GRAY, topleft=(930, y + 4))
        draw_text(surf, "ENTER: upgrade   ESC: back", 20, S.GRAY, center=(S.SCREEN_WIDTH // 2, 600))
        self.game.touch.draw(surf)


class OptionsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu = MenuList(self._items(), (S.SCREEN_WIDTH // 2, 220), 56, game, size=34)

    def _items(self):
        st = self.game.save["settings"]
        return [f"DIFFICULTY: {st.get('difficulty', 'normal').upper()}",
                f"SOUND: {'ON' if self.game.audio.volume > 0 else 'OFF'}",
                f"TOUCH CONTROLS: {'ON' if self.game.touch.visible else 'OFF'}",
                f"FULLSCREEN: {'ON' if self.game.fullscreen else 'OFF'}",
                "RESET SAVE DATA",
                "BACK"]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self._back()
            return
        r = self.menu.handle_event(e)
        if r is None:
            return
        st = self.game.save["settings"]
        if r == 0:
            order = ["easy", "normal", "hard", "insane"]
            st["difficulty"] = order[(order.index(st.get("difficulty", "normal")) + 1) % 4]
        elif r == 1:
            self.game.audio.volume = 0.0 if self.game.audio.volume > 0 else 0.6
        elif r == 2:
            self.game.touch.visible = not self.game.touch.visible
        elif r == 3:
            self.game.toggle_fullscreen()
        elif r == 4:
            from pyfighter.systems.save import DEFAULT
            import json
            self.game.save = json.loads(json.dumps(DEFAULT))
        elif r == 5:
            self._back()
            return
        save_state(self.game.save)
        self.menu.items = self._items()

    def _back(self):
        from pyfighter.scenes.menu import MainMenu
        self.goto(MainMenu(self.game))

    def draw(self, surf):
        surf.fill((14, 14, 26))
        draw_text(surf, "OPTIONS", 60, S.YELLOW, center=(S.SCREEN_WIDTH // 2, 90))
        self.menu.draw(surf)
        draw_text(surf, "P1: WASD move  J punch  K kick  L special  U block  I dash  (hold U + J/K = heavy)", 18, S.GRAY, center=(S.SCREEN_WIDTH // 2, 600))
        draw_text(surf, "P2: Arrows  Num1 punch  Num2 kick  Num3 special  Num4 block  Num5 dash  (or , . / M N)", 18, S.GRAY, center=(S.SCREEN_WIDTH // 2, 630))
        self.game.touch.draw(surf)
