"""صحنه‌ی مبارزه‌ی رو در رو."""
import math
import random
import pygame

from pyfighter import settings as S
from pyfighter.scenes.base import Scene
from pyfighter.entities.fighter import Fighter
from pyfighter.systems.input import InputSource
from pyfighter.systems.adaptive_ai import FighterAI
from pyfighter.gfx.stage import Stage
from pyfighter.gfx.effects import Effects
from pyfighter.ui.hud import FightHUD
from pyfighter.ui.fonts import draw_text, font


class FightScene(Scene):
    def __init__(self, game, p1_slug, p2_slug, p2_is_ai=True, difficulty="normal", stage_key=None,
                 p1_costume=0, p2_costume=0):
        super().__init__(game)
        self.p1_slug, self.p2_slug = p1_slug, p2_slug
        self.p2_is_ai = p2_is_ai
        self.difficulty = difficulty
        self.stage = Stage(stage_key or random.choice([p1_slug, p2_slug]))
        self.fx = Effects()
        self.wins = [0, 0]
        self.round_no = 1
        self.cam = 0.0
        self.shake = 0
        self.slowmo = 0
        self.frame_accum = 0.0
        self.in1 = InputSource(0, joystick=game.joysticks[0] if game.joysticks else None, touch=game.touch)
        self.in2 = None if p2_is_ai else InputSource(1, joystick=game.joysticks[1] if len(game.joysticks) > 1 else None)
        self.p1_costume, self.p2_costume = p1_costume, p2_costume
        self.paused = False
        self.pause_idx = 0
        self.match_over = False
        self.match_over_t = 0
        self._new_round()

    def _new_round(self):
        self.f1 = Fighter(self.p1_slug, 420, True, 0, self.p1_costume)
        self.f2 = Fighter(self.p2_slug, S.STAGE_WIDTH - 420, False, 1, self.p2_costume)
        self.f1.opponent, self.f2.opponent = self.f2, self.f1
        self.f1.input = self.in1
        self.f2.input = self.in2
        self.f1.wins, self.f2.wins = self.wins
        self.ai = FighterAI(self.f2, self.f1, self.difficulty, profile_key=f"{self.p1_slug}") if self.p2_is_ai else None
        self.hud = FightHUD(self.f1, self.f2)
        self.timer = S.ROUND_TIME * 60
        self.pre = S.PRE_ROUND_FRAMES
        self.ko_t = 0
        self.round_over = False
        self.hud.message(f"ROUND {self.round_no}", 80)
        self.cam = (self.f1.x + self.f2.x) / 2 - S.SCREEN_WIDTH / 2

    # ---------- رویداد ----------
    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif e.key == pygame.K_F1:
                S.DEBUG_HITBOXES = not S.DEBUG_HITBOXES
            elif self.paused:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.pause_idx = (self.pause_idx - 1) % 3
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_idx = (self.pause_idx + 1) % 3
                elif e.key in (pygame.K_RETURN, pygame.K_j, pygame.K_SPACE):
                    self._pause_select()
        if self.match_over and e.type in (pygame.KEYDOWN, pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN) and self.match_over_t > 60:
            from pyfighter.scenes.menu import MainMenu
            self.goto(MainMenu(self.game))

    def _pause_select(self):
        if self.pause_idx == 0:
            self.paused = False
        elif self.pause_idx == 1:
            self.wins = [0, 0]
            self.round_no = 1
            self._new_round()
            self.paused = False
        else:
            from pyfighter.scenes.menu import MainMenu
            self.goto(MainMenu(self.game))

    # ---------- به‌روزرسانی ----------
    def update(self):
        if self.paused:
            if self.in1.state.pressed.get("start"):
                self.paused = False
            return
        keys = pygame.key.get_pressed()
        self.in1.poll(keys, self.f1.facing_right)
        if self.in2:
            self.in2.poll(keys, self.f2.facing_right)
        if self.in1.state.pressed["start"] and not self.match_over:
            self.paused = True
            return
        if self.match_over:
            self.match_over_t += 1
            self._physics_only()
            return
        if self.pre > 0:
            self.pre -= 1
            if self.pre == 60:
                self.hud.message("FIGHT!", 50)
            self._update_camera()
            self.fx.update()
            return
        # slow-mo
        step = 1.0
        if self.slowmo > 0:
            self.slowmo -= 1
            step = 0.33
        self.frame_accum += step
        while self.frame_accum >= 1.0:
            self.frame_accum -= 1.0
            self._tick()

    def _physics_only(self):
        for f in (self.f1, self.f2):
            f.update(None)
        self.fx.update()
        self._update_camera()

    def _tick(self):
        f1, f2 = self.f1, self.f2
        if not self.round_over:
            self.timer -= 1
        f1.update(self.in1 if not self.round_over else None)
        if self.ai and not self.round_over:
            self.ai.update()
        f2.update(self.in2 if (self.in2 and not self.round_over) else None)
        if self.ai is None or self.round_over:
            pass
        self._push_apart()
        self._resolve_hits(f1, f2)
        self._resolve_hits(f2, f1)
        self._resolve_projectiles(f1, f2)
        self._resolve_projectiles(f2, f1)
        self._resolve_clones(f1, f2)
        self._resolve_clones(f2, f1)
        self.fx.update()
        self._update_camera()
        if self.shake > 0:
            self.shake -= 1
        # پایان راند
        if not self.round_over:
            if f1.dead or f2.dead or self.timer <= 0:
                self._end_round()
        else:
            self.ko_t += 1
            if self.ko_t > 150:
                if max(self.wins) >= S.ROUNDS_TO_WIN:
                    self.match_over = True
                    self._on_match_end()
                else:
                    self.round_no += 1
                    self._new_round()

    def _end_round(self):
        f1, f2 = self.f1, self.f2
        self.round_over = True
        if f1.dead and f2.dead:
            winner = None
        elif f1.dead:
            winner = 1
        elif f2.dead:
            winner = 0
        else:
            winner = 0 if f1.health > f2.health else 1 if f2.health > f1.health else None
        if winner is None:
            self.hud.message("DRAW", 120)
        else:
            self.wins[winner] += 1
            self.hud.message("K.O." if (f1.dead or f2.dead) else "TIME OVER", 120)
            self.slowmo = S.KO_SLOWMO_FRAMES
            self.shake = 20
        if self.ai:
            self.ai.on_round_end()

    def _on_match_end(self):
        from pyfighter.systems.save import save_state
        st = self.game.save
        winner = 0 if self.wins[0] > self.wins[1] else 1
        if winner == 0:
            reward = {"easy": 60, "normal": 120, "hard": 220, "insane": 400}.get(self.difficulty, 100) if self.p2_is_ai else 50
            st["gold"] += reward
            st["stats"]["wins"] = st["stats"].get("wins", 0) + 1
            if self.p2_is_ai and self.difficulty in ("hard", "insane"):
                st["gems"] += 3 if self.difficulty == "hard" else 8
            self.reward_text = f"+{reward} GOLD"
        else:
            st["stats"]["losses"] = st["stats"].get("losses", 0) + 1
            self.reward_text = "+20 GOLD"
            st["gold"] += 20
        st["xp"] = st.get("xp", 0) + (40 if winner == 0 else 15)
        save_state(st)

    def _push_apart(self):
        f1, f2 = self.f1, self.f2
        r1, r2 = f1.body_rect(), f2.body_rect()
        if r1.colliderect(r2) and not (f1.is_knocked() or f2.is_knocked()):
            overlap = (r1.w + r2.w) / 2 - abs(f1.x - f2.x)
            if overlap > 0:
                s = overlap / 2 + 0.5
                if f1.x < f2.x:
                    f1.x -= s
                    f2.x += s
                else:
                    f1.x += s
                    f2.x -= s
        # قفل فاصله
        if abs(f1.x - f2.x) > S.MAX_PLAYER_DISTANCE:
            mid = (f1.x + f2.x) / 2
            half = S.MAX_PLAYER_DISTANCE / 2
            if f1.x < f2.x:
                f1.x, f2.x = mid - half, mid + half
            else:
                f1.x, f2.x = mid + half, mid - half
        for f in (f1, f2):
            f.x = max(S.WALL_MARGIN, min(S.STAGE_WIDTH - S.WALL_MARGIN, f.x))

    def _apply_hit(self, attacker, defender, mv, unblockable=False, from_projectile=False, hit_pos=None):
        combo = attacker.combo_count
        scale = S.COMBO_SCALING[min(combo, len(S.COMBO_SCALING) - 1)] if combo < len(S.COMBO_SCALING) else S.COMBO_MIN_SCALING
        res = defender.take_hit(mv, attacker, scale, unblockable, from_projectile)
        pos = hit_pos or (defender.x, defender.y - 180)
        if res == "hit":
            attacker.add_meter(S.METER_PER_HIT_DEALT + mv.meter_gain)
            attacker.stats["hits"] += 1
            attacker.hitstop = S.HITSTOP.get(mv.strength, 5)
            attacker.combo_count += 1
            self.hud.combo(attacker.player_index, attacker.combo_count)
            self.fx.hit_spark(pos, mv.strength, attacker.d.aura_color)
            if mv.strength in ("heavy", "special", "ultimate"):
                self.shake = max(self.shake, 8 if mv.strength == "heavy" else 14)
            self.game.audio.play("hit_" + ("heavy" if mv.strength in ("heavy", "special", "ultimate") else "light"))
        elif res == "block":
            attacker.add_meter(3)
            attacker.hitstop = S.HITSTOP.get(mv.strength, 5) // 2
            self.fx.block_spark(pos)
            self.game.audio.play("block")
        elif res == "armor":
            self.fx.block_spark(pos)
        # ریست کمبو وقتی حریف آزاد شد
        if defender.hitstun == 0 and not defender.is_knocked():
            attacker.combo_count = 0
        return res

    def _resolve_hits(self, a, b):
        if b.dead and b.state == "lying":
            return
        hb = a.active_hitbox()
        if hb is None:
            if a.combo_count and b.hitstun == 0 and not b.is_knocked() and b.state != "attack":
                a.combo_count = 0
            return
        if hb.colliderect(b.hurt_rect()) or (a.move and "domain" in a.move.tags):
            a.mark_hit()
            c = hb.clip(b.hurt_rect()).center if hb.colliderect(b.hurt_rect()) else (b.x, b.y - 180)
            self._apply_hit(a, b, a.move, unblockable="domain" in a.move.tags, hit_pos=c)
            if "domain" in a.move.tags:
                self.fx.domain(a.d.aura_color)
                self.shake = 30

    def _resolve_projectiles(self, a, b):
        for p in a.projectiles:
            if p.hit_cd > 0 or p.dead:
                continue
            # Infinity گوجو: پرتابه‌ها با گارد + Meter متوقف می‌شوند
            if b.d.passive == "infinity" and b.state in ("block", "crouch_block") and b.meter >= 20 and abs(p.x - b.x) < 120:
                b.add_meter(-20)
                p.vx *= 0.2
                p.life = min(p.life, 25)
                p.hit_cd = 99
                self.fx.infinity_stop((p.x, p.y))
                continue
            if p.rect().colliderect(b.hurt_rect()):
                res = self._apply_hit(a, b, p.move, unblockable=p.unblockable, from_projectile=True, hit_pos=(p.x, p.y))
                if res in ("hit", "block", "armor"):
                    p.on_hit()
                if p.kind == "blue_orb" and res == "hit":
                    self.fx.explosion((p.x, p.y), (80, 160, 255), 90)
                if p.kind == "rasenshuriken" and res == "hit" and not p.expanding:
                    self.fx.explosion((p.x, p.y), (160, 230, 255), 160)
        # برخورد پرتابه با پرتابه
        for p in a.projectiles:
            for q in b.projectiles:
                if not p.dead and not q.dead and p.rect().colliderect(q.rect()):
                    if p.move.strength == "ultimate" and q.move.strength != "ultimate":
                        q.dead = True
                    elif q.move.strength == "ultimate" and p.move.strength != "ultimate":
                        p.dead = True
                    else:
                        p.dead = q.dead = True
                    self.fx.explosion(((p.x + q.x) / 2, (p.y + q.y) / 2), (255, 255, 255), 70)

    def _resolve_clones(self, a, b):
        for c in a.clones:
            hb = c.hitbox()
            if hb and hb.colliderect(b.hurt_rect()):
                c.hit_done = True
                mv = a.d.moves["medium_punch"]
                self._apply_hit(a, b, mv, hit_pos=hb.center)
                c.poof = 10
            # کلون با ضربه‌ی حریف از بین می‌رود
            ob = b.active_hitbox()
            if ob and not c.poof and ob.colliderect(pygame.Rect(int(c.x - 35), S.FLOOR_Y - 290, 70, 290)):
                c.poof = 10
                self.fx.hit_spark((c.x, S.FLOOR_Y - 180), "light", (255, 255, 255))

    def _update_camera(self):
        mid = (self.f1.x + self.f2.x) / 2
        target = mid - S.SCREEN_WIDTH / 2
        target = max(0, min(S.STAGE_WIDTH - S.SCREEN_WIDTH, target))
        self.cam += (target - self.cam) * 0.12

    # ---------- رسم ----------
    def draw(self, surf):
        cam = self.cam
        if self.shake:
            cam += random.randint(-6, 6)
            oy = random.randint(-4, 4)
        else:
            oy = 0
        self.stage.draw(surf, cam)
        # سایه‌ها
        for f in (self.f1, self.f2):
            sw = 90
            sh = pygame.Surface((sw, 22), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 110), (0, 0, sw, 22))
            surf.blit(sh, (f.x - cam - sw // 2, S.FLOOR_Y - 11 + oy))
        # ترتیب رسم: کسی که حمله می‌کند جلو
        order = (self.f2, self.f1) if self.f1.state == "attack" else (self.f1, self.f2)
        for f in order:
            f.draw(surf, cam, S.DEBUG_HITBOXES)
        self.fx.draw(surf, cam)
        # نور دامین
        self.hud.draw(surf, self.timer / 60, self.round_no, self.wins)
        if self.ai and S.DEBUG_HITBOXES:
            draw_text(surf, self.ai.debug_text, 16, S.CYAN, topleft=(20, 130))
        if self.paused:
            self._draw_pause(surf)
        if self.match_over:
            self._draw_match_over(surf)
        self.game.touch.draw(surf)

    def _draw_pause(self, surf):
        ov = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        surf.blit(ov, (0, 0))
        draw_text(surf, "PAUSED", 72, S.WHITE, center=(S.SCREEN_WIDTH // 2, 200))
        for i, t in enumerate(("RESUME", "RESTART", "MAIN MENU")):
            c = S.YELLOW if i == self.pause_idx else S.GRAY
            draw_text(surf, t, 40, c, center=(S.SCREEN_WIDTH // 2, 320 + i * 60))

    def _draw_match_over(self, surf):
        ov = pygame.Surface((S.SCREEN_WIDTH, S.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, min(180, self.match_over_t * 4)))
        surf.blit(ov, (0, 0))
        w = self.f1 if self.wins[0] > self.wins[1] else self.f2
        draw_text(surf, f"{w.d.display_name.upper()} WINS", 64, S.YELLOW, center=(S.SCREEN_WIDTH // 2, 240))
        line = w.d.voice_lines.get("win", "")
        if line:
            draw_text(surf, f'"{line}"', 26, S.WHITE, center=(S.SCREEN_WIDTH // 2, 320))
        draw_text(surf, getattr(self, "reward_text", ""), 36, S.GREEN, center=(S.SCREEN_WIDTH // 2, 400))
        if self.match_over_t > 60 and (self.match_over_t // 30) % 2 == 0:
            draw_text(surf, "PRESS ANY KEY", 28, S.GRAY, center=(S.SCREEN_WIDTH // 2, 520))
