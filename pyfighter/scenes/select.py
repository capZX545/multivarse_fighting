"""صفحه انتخاب کاراکتر: گرید پرتره‌ها، پیش‌نمایش انیمیشن، انتخاب لباس، P1/P2 یا CPU."""
import math
import pygame
from pyfighter import settings as S
from pyfighter.scenes.base import Scene
from pyfighter.ui.fonts import draw_text, font
from pyfighter.data import characters_db as db
from pyfighter.gfx.sprites import get_character_sprites
from pyfighter.characters import get_def

COLS = 8
CELL = 92
GRID_X = (S.SCREEN_WIDTH - COLS * CELL) // 2
GRID_Y = 470

RARITY_COL = {"Rare": (120, 200, 120), "Epic": (170, 90, 240), "Legendary": (250, 170, 40), "Mythic": (255, 80, 120)}


class Cursor:
    def __init__(self, idx, color, label):
        self.idx = idx
        self.color = color
        self.label = label
        self.locked = False
        self.costume = 0
        self.anim_t = 0


class CharacterSelect(Scene):
    def __init__(self, game, vs_ai=True):
        super().__init__(game)
        self.vs_ai = vs_ai
        self.chars = db.all_sorted()
        self.playable = [c for c in self.chars if c["playable"]]
        # فقط قابل‌بازی‌ها در گرید نمایش داده می‌شوند؛ بقیه به‌صورت "COMING SOON" خاکستری
        self.grid = self.playable + [c for c in self.chars if not c["playable"]][:COLS * 3 - len(self.playable)]
        self.rows = max(1, math.ceil(len(self.grid) / COLS))
        self.c1 = Cursor(0, (80, 160, 255), "P1")
        self.c2 = Cursor(min(1, len(self.playable) - 1), (255, 90, 90), "P2" if not vs_ai else "CPU")
        self.stage_pick = False
        self.t = 0
        self.diff_idx = ["easy", "normal", "hard", "insane"].index(game.save["settings"].get("difficulty", "normal"))
        self.previews = {}
        self.scroll = 0
        self.ready_t = 0

    # ---------- کمکی ----------
    def _char(self, cur):
        return self.grid[cur.idx]

    def _sprites(self, slug):
        if slug not in self.previews:
            self.previews[slug] = get_character_sprites(slug)
        return self.previews[slug]

    def _move(self, cur, dx, dy):
        n = len(self.grid)
        r, c = divmod(cur.idx, COLS)
        c = (c + dx) % COLS
        r = (r + dy) % self.rows
        i = r * COLS + c
        if i >= n:
            i = n - 1 if dy else (r * COLS)
        cur.idx = i
        cur.anim_t = 0
        self.game.audio.play("menu_move")

    def _confirm(self, cur):
        ch = self._char(cur)
        if not ch["playable"]:
            self.game.audio.play("error")
            return
        cur.locked = True
        self.game.audio.play("menu_select")
        # اگر هر دو یک کاراکتر با یک لباس، لباس متفاوت
        if self.c1.locked and self.c2.locked and self._char(self.c1)["slug"] == self._char(self.c2)["slug"] and self.c1.costume == self.c2.costume:
            self.c2.costume = (self.c2.costume + 1) % 3

    def _cycle_costume(self, cur, d):
        cur.costume = (cur.costume + d) % 3
        self.game.audio.play("menu_move")

    # ---------- رویداد ----------
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.c2.locked and not self.vs_ai:
                    self.c2.locked = False
                elif self.c1.locked:
                    self.c1.locked = False
                    if self.vs_ai:
                        self.c2.locked = False
                else:
                    from pyfighter.scenes.menu import MainMenu
                    self.goto(MainMenu(self.game))
                return
            self._key_for(self.c1, e.key, {"l": pygame.K_a, "r": pygame.K_d, "u": pygame.K_w, "d": pygame.K_s,
                                             "ok": (pygame.K_j, pygame.K_RETURN, pygame.K_SPACE), "cos": (pygame.K_k, pygame.K_q, pygame.K_e)})
            if not self.vs_ai:
                self._key_for(self.c2, e.key, {"l": pygame.K_LEFT, "r": pygame.K_RIGHT, "u": pygame.K_UP, "d": pygame.K_DOWN,
                                                 "ok": (pygame.K_KP1, pygame.K_COMMA, pygame.K_KP_ENTER), "cos": (pygame.K_KP2, pygame.K_PERIOD)})
            else:
                if self.c1.locked and not self.c2.locked:
                    # انتخاب حریف CPU با همان کلیدهای P1
                    self._key_for(self.c2, e.key, {"l": pygame.K_a, "r": pygame.K_d, "u": pygame.K_w, "d": pygame.K_s,
                                                     "ok": (pygame.K_j, pygame.K_RETURN, pygame.K_SPACE), "cos": (pygame.K_k, pygame.K_q, pygame.K_e)})
                if e.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET, pygame.K_TAB):
                    self.diff_idx = (self.diff_idx + (1 if e.key != pygame.K_LEFTBRACKET else -1)) % 4
        elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            pos = self.game.event_pos(e)
            cur = self.c1 if not self.c1.locked else self.c2
            if cur.locked:
                self._start()
                return
            # گرید
            gx, gy = pos[0] - GRID_X, pos[1] - GRID_Y
            if 0 <= gx < COLS * CELL and 0 <= gy < self.rows * CELL:
                i = int(gy // CELL) * COLS + int(gx // CELL)
                if i < len(self.grid):
                    if cur.idx == i:
                        self._confirm(cur)
                    else:
                        cur.idx = i
                        cur.anim_t = 0
                        self.game.audio.play("menu_move")
            # دکمه‌های لباس / سختی
            for r, (c, d) in self._touch_buttons().items():
                if r.collidepoint(pos):
                    if c == "diff":
                        self.diff_idx = (self.diff_idx + 1) % 4
                    elif c == "back":
                        from pyfighter.scenes.menu import MainMenu
                        self.goto(MainMenu(self.game))
                    else:
                        self._cycle_costume(c, d)
        elif e.type == pygame.JOYBUTTONDOWN:
            cur = self.c1 if e.joy == 0 else self.c2
            if e.button in (0, 7):
                self._confirm(cur)
            elif e.button == 2:
                self._cycle_costume(cur, 1)
            elif e.button == 1:
                cur.locked = False
        elif e.type == pygame.JOYHATMOTION:
            cur = self.c1 if e.joy == 0 else self.c2
            if not cur.locked:
                if e.value[0]:
                    self._move(cur, e.value[0], 0)
                if e.value[1]:
                    self._move(cur, 0, -e.value[1])

    def _key_for(self, cur, key, m):
        if cur.locked:
            return
        if key == m["l"]:
            self._move(cur, -1, 0)
        elif key == m["r"]:
            self._move(cur, 1, 0)
        elif key == m["u"]:
            self._move(cur, 0, -1)
        elif key == m["d"]:
            self._move(cur, 0, 1)
        elif key in m["ok"]:
            self._confirm(cur)
        elif key in m["cos"]:
            self._cycle_costume(cur, 1)

    def _touch_buttons(self):
        W = S.SCREEN_WIDTH
        return {
            pygame.Rect(40, 400, 44, 44): (self.c1, -1),
            pygame.Rect(300, 400, 44, 44): (self.c1, 1),
            pygame.Rect(W - 344, 400, 44, 44): (self.c2, -1),
            pygame.Rect(W - 84, 400, 44, 44): (self.c2, 1),
            pygame.Rect(W // 2 - 110, 400, 220, 40): ("diff", 0),
            pygame.Rect(20, 20, 120, 40): ("back", 0),
        }

    # ---------- به‌روزرسانی ----------
    def update(self):
        self.t += 1
        self.c1.anim_t += 1
        self.c2.anim_t += 1
        if self.vs_ai and self.c1.locked and not self.c2.locked and self.game.touch.visible is False and False:
            pass
        if self.c1.locked and self.c2.locked:
            self.ready_t += 1
            if self.ready_t > 45:
                self._start()
        else:
            self.ready_t = 0

    def _start(self):
        from pyfighter.scenes.fight import FightScene
        diff = ["easy", "normal", "hard", "insane"][self.diff_idx]
        self.game.save["settings"]["difficulty"] = diff
        self.goto(FightScene(self.game, self._char(self.c1)["slug"], self._char(self.c2)["slug"],
                             p2_is_ai=self.vs_ai, difficulty=diff,
                             p1_costume=self.c1.costume, p2_costume=self.c2.costume))

    # ---------- رسم ----------
    def draw(self, surf):
        W, H = S.SCREEN_WIDTH, S.SCREEN_HEIGHT
        surf.fill((14, 12, 28))
        for i in range(0, W, 40):
            pygame.draw.line(surf, (22, 20, 40), (i, 0), (i - 200, H), 2)
        draw_text(surf, "SELECT YOUR FIGHTER", 44, S.YELLOW, center=(W // 2, 40))
        # پیش‌نمایش‌ها
        self._draw_preview(surf, self.c1, 60, False)
        self._draw_preview(surf, self.c2, W - 60, True)
        # VS
        draw_text(surf, "VS", 80, (255, 90, 60), center=(W // 2, 230))
        if self.vs_ai:
            d = ["EASY", "NORMAL", "HARD", "INSANE"][self.diff_idx]
            draw_text(surf, f"CPU: {d}  [TAB]", 24, S.WHITE, center=(W // 2, 420))
        # گرید
        for i, ch in enumerate(self.grid):
            r, c = divmod(i, COLS)
            x, y = GRID_X + c * CELL, GRID_Y + r * CELL
            rect = pygame.Rect(x + 3, y + 3, CELL - 6, CELL - 6)
            pygame.draw.rect(surf, (30, 30, 50), rect)
            if ch["playable"]:
                pr = pygame.transform.smoothscale(self._sprites(ch["slug"]).portrait, (CELL - 10, CELL - 10))
                surf.blit(pr, (x + 5, y + 5))
            else:
                draw_text(surf, "?", 40, (60, 60, 80), center=rect.center, shadow=False)
            pygame.draw.rect(surf, RARITY_COL.get(ch["rarity"], S.GRAY), rect, 2)
            for cur in (self.c1, self.c2):
                if cur.idx == i:
                    w = 4 if not cur.locked else 6
                    pygame.draw.rect(surf, cur.color, rect.inflate(6, 6), w)
                    draw_text(surf, cur.label, 16, cur.color, topleft=(x + 6, y + 6))
        draw_text(surf, "BACK", 22, S.GRAY, topleft=(30, 26))
        if self.c1.locked and self.c2.locked:
            draw_text(surf, "READY!", 60, S.GREEN, center=(W // 2, 320))
        self.game.touch.draw(surf)

    def _draw_preview(self, surf, cur, x, right):
        ch = self._char(cur)
        W = S.SCREEN_WIDTH
        panel = pygame.Rect(x if not right else x - 340, 80, 340, 380)
        pygame.draw.rect(surf, (24, 22, 44), panel)
        pygame.draw.rect(surf, cur.color, panel, 3)
        if ch["playable"]:
            spr = self._sprites(ch["slug"])
            anim = spr.get("idle" if not cur.locked else "medium_punch", not right)
            fr, _ = anim.frame_at(cur.anim_t if not cur.locked else min(cur.anim_t, anim.total - 1))
            if fr:
                fr = pygame.transform.smoothscale(fr, (int(fr.get_width() * 0.95), int(fr.get_height() * 0.95)))
                surf.blit(fr, (panel.centerx - fr.get_width() // 2, panel.bottom - fr.get_height() - 8))
            d = get_def(ch["slug"])
            cos = d.costumes[cur.costume % len(d.costumes)]
        else:
            draw_text(surf, "COMING SOON", 24, S.GRAY, center=panel.center)
            cos = "-"
        name = ch["name"].upper()
        draw_text(surf, name, 28 if len(name) < 16 else 20, S.WHITE, center=(panel.centerx, panel.top - 18))
        draw_text(surf, f"{ch['role']}  |  {ch['element']}", 18, RARITY_COL.get(ch["rarity"], S.GRAY), center=(panel.centerx, panel.bottom + 14))
        draw_text(surf, f"<  {cos}  >", 18, S.YELLOW, center=(panel.centerx, panel.bottom + 40))
        # آمار
        st = ch["stats"]
        for i, k in enumerate(("hp", "atk", "def", "spd", "tech")):
            bx = panel.left + 10 + i * 64
            pygame.draw.rect(surf, (40, 40, 60), (bx, panel.top + 8, 54, 8))
            pygame.draw.rect(surf, cur.color, (bx, panel.top + 8, int(54 * st[k] / 100), 8))
            draw_text(surf, k.upper(), 12, S.GRAY, topleft=(bx, panel.top + 18), shadow=False)
