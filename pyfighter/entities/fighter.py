"""
موجودیت مبارز: ماشین حالت، فیزیک، ورودی→حرکت، هیت‌باکس/هرت‌باکس، پرتابه، پسیوها.
"""
import math
import random
import pygame

from pyfighter import settings as S
from pyfighter.gfx import fxsprites as FX
from pyfighter.characters import get_def
from pyfighter.characters.base import Move, Hitbox
from pyfighter.gfx.sprites import get_character_sprites

STATES_ACTIONABLE = ("idle", "walk", "walk_back", "crouch")
STATES_AIR = ("jump_up", "jump_apex", "jump_fall")


class Projectile:
    def __init__(self, owner, move: Move, x, y, facing_right):
        p = move.projectile
        self.owner = owner
        self.move = move
        self.kind = p["kind"]
        self.x, self.y = x, y
        self.dir = 1 if facing_right else -1
        self.vx = p["speed"] * self.dir
        self.vy = 0.0
        self.life = p["life"]
        self.radius = p["radius"]
        self.color = p["color"]
        self.core = p.get("core", (255, 255, 255))
        self.hits_left = p.get("hits", 1)
        self.pierce = p.get("pierce", False)
        self.unblockable = p.get("unblockable", False)
        self.pull = p.get("pull", 0.0)
        self.expand_radius = p.get("expand_radius", 0)
        self.sprite = p.get("sprite")            # نام اسپرایت در assets/fx/<slug>/
        self.sprite_slug = owner.d.slug
        self.sprite_h = p.get("sprite_h", 0)     # ارتفاع رندر؛ 0 = 2*radius
        self.sprite_w = p.get("sprite_w", 0)
        self.sprite_fps = p.get("sprite_fps", 6)
        self.expanding = False
        self.hit_cd = 0
        self.age = 0
        self.dead = False
        self.trail = []

    def update(self, target):
        self.age += 1
        self.life -= 1
        if self.hit_cd > 0:
            self.hit_cd -= 1
        if self.expanding:
            self.radius = min(self.expand_radius, self.radius + 6)
            self.vx *= 0.85
        self.x += self.vx
        self.y += self.vy
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        if self.pull and target and not target.is_knocked():
            dx = self.x - target.x
            if abs(dx) < 420:
                target.x += math.copysign(min(self.pull, abs(dx) * 0.05), dx)
        if self.life <= 0 or self.x < -200 or self.x > S.STAGE_WIDTH + 200:
            self.dead = True

    def rect(self):
        r = self.radius
        return pygame.Rect(int(self.x - r), int(self.y - r), int(2 * r), int(2 * r))

    def on_hit(self):
        self.hits_left -= 1
        self.hit_cd = 8
        if self.expand_radius and not self.expanding:
            self.expanding = True
            self.life = max(self.life, 40)
        if self.hits_left <= 0 and not self.pierce:
            self.dead = True

    def draw(self, surf, cam):
        cx, cy = int(self.x - cam), int(self.y)
        t = self.age
        if self.sprite and FX.has(self.sprite_slug, self.sprite):
            img = FX.frame(self.sprite_slug, self.sprite, t // max(1, self.sprite_fps),
                           height=self.sprite_h or int(self.radius * 2.2),
                           width=self.sprite_w or None, flip=self.dir < 0)
            if self.sprite_w:
                img = FX.frame(self.sprite_slug, self.sprite, t // max(1, self.sprite_fps), width=self.sprite_w, flip=self.dir < 0)
            surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))
            return
        if self.kind == "blue_orb":
            g = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(g, (80, 150, 255, 60), (self.radius * 2, self.radius * 2), int(self.radius * 1.8))
            surf.blit(g, (cx - self.radius * 2, cy - self.radius * 2))
            for i in range(3):
                rr = self.radius + 6 * math.sin(t * 0.4 + i)
                pygame.draw.circle(surf, self.color, (cx, cy), int(rr), 2)
            pygame.draw.circle(surf, self.color, (cx, cy), int(self.radius * 0.7))
            pygame.draw.circle(surf, self.core, (cx, cy), int(self.radius * 0.35))
            for k in range(6):
                a = t * 0.3 + k * 1.05
                pygame.draw.line(surf, self.core, (cx, cy),
                                 (cx + math.cos(a) * self.radius * 1.4, cy + math.sin(a) * self.radius * 1.4), 2)
        elif self.kind == "purple_beam":
            for i, (tx, ty) in enumerate(self.trail):
                a = int(120 * i / len(self.trail))
                s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, a), (self.radius, self.radius), self.radius)
                surf.blit(s, (tx - cam - self.radius, ty - self.radius))
            pygame.draw.circle(surf, self.color, (cx, cy), self.radius)
            pygame.draw.circle(surf, (60, 200, 255), (cx, cy), int(self.radius * 0.75), 4)
            pygame.draw.circle(surf, (255, 80, 90), (cx, cy), int(self.radius * 0.55), 4)
            pygame.draw.circle(surf, self.core, (cx, cy), int(self.radius * 0.35))
        elif self.kind == "rasenshuriken":
            r = self.radius
            # هاله
            g = pygame.Surface((int(r * 3.6), int(r * 3.6)), pygame.SRCALPHA)
            pygame.draw.circle(g, (170, 230, 255, 60), (int(r * 1.8), int(r * 1.8)), int(r * 1.35))
            surf.blit(g, (cx - r * 1.8, cy - r * 1.8))
            # چهار تیغه‌ی خمیده‌ی چرخان
            for k in range(4):
                a0 = t * 0.45 + k * math.pi / 2
                pts = [(cx, cy)]
                for j in range(7):
                    a = a0 + j * 0.13
                    rr = r * (0.5 + 1.2 * math.sin(j / 6 * math.pi))
                    pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
                pygame.draw.polygon(surf, (200, 240, 255), pts)
                pygame.draw.polygon(surf, (120, 200, 255), pts, 2)
            # حلقه‌ی باد
            pygame.draw.circle(surf, (230, 250, 255), (cx, cy), int(r * 0.95), 2)
            # هسته‌ی سفید با مارپیچ
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), int(r * 0.5))
            for k in range(3):
                a = -t * 0.6 + k * 2.09
                pygame.draw.arc(surf, (140, 210, 255), (cx - r * 0.45, cy - r * 0.45, r * 0.9, r * 0.9), a, a + 1.4, 3)
        elif self.kind == "fireball":
            r = self.radius
            for i, (tx, ty) in enumerate(self.trail[-6:]):
                k = i / 6
                pygame.draw.circle(surf, (255, 90 + int(80 * k), 20), (int(tx - cam), int(ty)), int(r * (0.35 + 0.5 * k)))
            pygame.draw.circle(surf, (255, 110, 20), (cx, cy), r)
            pygame.draw.circle(surf, (255, 190, 60), (cx, cy), int(r * 0.7))
            pygame.draw.circle(surf, (255, 245, 190), (cx, cy), int(r * 0.38))
            for k in range(6):
                a = t * 0.5 + k * 1.05
                pygame.draw.circle(surf, (255, 140, 30), (int(cx + math.cos(a) * r * 1.05), int(cy + math.sin(a) * r * 0.8)), 6)
        elif self.kind == "indra_arrow":
            r = self.radius
            d = 1 if self.vx > 0 else -1
            g = pygame.Surface((r * 6, r * 3), pygame.SRCALPHA)
            pygame.draw.ellipse(g, (140, 70, 255, 80), (0, 0, r * 6, r * 3))
            surf.blit(g, (cx - r * 3, cy - r * 1.5))
            pts = [(cx + d * r * 2.2, cy), (cx - d * r * 2.0, cy - r * 0.45), (cx - d * r * 1.3, cy), (cx - d * r * 2.0, cy + r * 0.45)]
            pygame.draw.polygon(surf, (200, 170, 255), pts)
            pygame.draw.polygon(surf, (110, 40, 220), pts, 3)
            for k in range(7):
                a = t * 1.3 + k
                pygame.draw.line(surf, (230, 220, 255), (cx + math.cos(a) * r, cy + math.sin(a) * r * 0.6),
                                 (cx + math.cos(a + 1.5) * r * 1.6, cy + math.sin(a + 1.5) * r), 2)
        elif self.kind == "bijuu_dama":
            pygame.draw.circle(surf, (40, 20, 60), (cx, cy), self.radius)
            pygame.draw.circle(surf, (120, 40, 140), (cx, cy), int(self.radius * 0.8), 5)
            pygame.draw.circle(surf, (255, 200, 80), (cx, cy), int(self.radius * 0.3))
        else:
            pygame.draw.circle(surf, self.color, (cx, cy), self.radius)


class Clone:
    """کلون سایه‌ی ناروتو: به سمت حریف می‌دود، یک ضربه می‌زند، puff می‌شود."""

    def __init__(self, owner, x, facing_right):
        self.owner = owner
        self.x = x
        self.dir = 1 if facing_right else -1
        self.life = 150
        self.anim_t = 0
        self.state = "run"
        self.attack_t = 0
        self.dead = False
        self.hit_done = False
        self.poof = 0

    def update(self, target):
        self.anim_t += 1
        self.life -= 1
        if self.poof:
            self.poof -= 1
            if self.poof == 0:
                self.dead = True
            return
        if self.state == "run":
            self.x += 7 * self.dir
            if abs(self.x - target.x) < 90 or self.life < 60:
                self.state = "attack"
                self.attack_t = 0
        elif self.state == "attack":
            self.attack_t += 1
            if self.attack_t > 20:
                self.poof = 12
        if self.life <= 0:
            self.poof = 10

    def hitbox(self):
        if self.state == "attack" and 6 <= self.attack_t <= 12 and not self.hit_done:
            return pygame.Rect(int(self.x + (20 if self.dir > 0 else -120)), S.FLOOR_Y - 250, 100, 90)
        return None

    def draw(self, surf, cam):
        spr = self.owner.sprites
        if self.poof:
            r = 40 + (12 - self.poof) * 6
            pygame.draw.circle(surf, (240, 240, 240), (int(self.x - cam), S.FLOOR_Y - 120), r)
            return
        name = "walk" if self.state == "run" else "medium_punch"
        anim = spr.get(name, self.dir > 0)
        f, _ = anim.frame_at(self.anim_t if self.state == "run" else self.attack_t)
        if f:
            surf.blit(f, (self.x - cam - f.get_width() // 2, S.FLOOR_Y - f.get_height()))


class Fighter:
    def __init__(self, slug: str, x: float, facing_right: bool, player_index: int, costume: int = 0):
        self.slug = slug
        self.d = get_def(slug)
        self.sprites = get_character_sprites(slug)
        self.player_index = player_index
        self.costume = costume
        self.x = x
        self.y = float(S.FLOOR_Y)   # موقعیت پا
        self.vx = 0.0
        self.vy = 0.0
        self.facing_right = facing_right
        self.health = self.d.health
        self.max_health = self.d.health
        self.meter = 0
        self.state = "idle"
        self.state_t = 0
        self.move: Move | None = None
        self.move_hit_done = set()
        self.multi_hits = 0
        self.hitstun = 0
        self.blockstun = 0
        self.hitstop = 0
        self.blocking = False
        self.crouching = False
        self.airborne = False
        self.knocked = False
        self.lying_t = 0
        self.dead = False
        self.combo_count = 0
        self.combo_damage = 0
        self.invuln = 0
        self.armor = 0
        self.projectiles = []
        self.clones = []
        self.input = None
        self.ai = None
        self.opponent = None
        self.dash_t = 0
        self.dash_dir = 0
        self.transform = None
        self.transform_t = 0
        self.stunned = 0
        self.burn_t = 0        # Amaterasu: فریم‌های باقی‌مانده‌ی سوختن
        self.burn_dmg = 0
        self.burn_by = None
        self.wins = 0
        self.flash = 0
        self.aura = 0.0
        self.last_hit_by = None
        self.stats = {"hits": 0, "blocks": 0, "specials": 0, "jumps": 0, "throws": 0}

    # ---------- کمکی ----------
    def is_knocked(self):
        return self.state in ("knockdown", "lying", "getup", "ko")

    def actionable(self):
        return (self.state in STATES_ACTIONABLE or self.state == "block" or self.state == "crouch_block") \
            and self.hitstun == 0 and self.blockstun == 0 and self.stunned == 0 and not self.dead

    def body_rect(self) -> pygame.Rect:
        h = self.d.crouch_height if (self.crouching or self.state.startswith("crouch")) else self.d.height
        if self.is_knocked():
            h = 90
        return pygame.Rect(int(self.x - self.d.width // 2), int(self.y - h), self.d.width, h)

    def hurt_rect(self) -> pygame.Rect:
        r = self.body_rect()
        if self.airborne:
            r.y = int(self.y - self.d.height * 0.85)
            r.h = int(self.d.height * 0.75)
        return r.inflate(20, 0)

    def set_state(self, st, move: Move | None = None):
        self.state = st
        self.state_t = 0
        self.move = move
        self.move_hit_done = set()
        self.multi_hits = 0

    def face_opponent(self):
        if self.opponent and not self.airborne and self.actionable():
            self.facing_right = self.opponent.x >= self.x

    def dir(self):
        return 1 if self.facing_right else -1

    def add_meter(self, n):
        self.meter = max(0, min(S.MAX_METER, self.meter + n))

    # ---------- اجرای حرکات ----------
    def start_move(self, name):
        mv = self.d.moves[name]
        if mv.meter_cost > self.meter:
            return False
        if self.airborne and not mv.airborne_ok:
            return False
        self.add_meter(-mv.meter_cost)
        self.set_state("attack", mv)
        self.invuln = max(self.invuln, mv.invuln_frames)
        self.armor = max(self.armor, mv.armor_frames)
        self.crouching = self.crouching and name == "crouch_punch"
        if mv.strength in ("special", "ultimate"):
            self.stats["specials"] += 1
        # hooks
        for tag in mv.tags:
            if tag == "summon_clone":
                self.clones.append(Clone(self, self.x + 40 * self.dir(), self.facing_right))
            elif tag.startswith("transform_"):
                _, kind, dur = tag.split("_")
                self.transform = kind
                self.transform_t = int(dur)
                self.aura = 1.0
        if mv.self_heal:
            self.health = min(self.max_health, self.health + mv.self_heal)
        return True

    def try_specials(self, inp):
        for sp in self.d.specials:
            if inp.match_motion(sp.motion, sp.button):
                if self.start_move(sp.move):
                    inp.clear_history()
                    return True
        return False

    def try_normals(self, st):
        if self.airborne:
            if st.pressed["punch"]:
                return self.start_move("jump_punch")
            if st.pressed["kick"]:
                return self.start_move("jump_kick")
            return False
        strength_mod = "heavy" if st.held["block"] else None  # نگه‌داشتن B + ضربه = سنگین
        if st.pressed["punch"]:
            if self.crouching:
                return self.start_move("crouch_punch")
            if strength_mod:
                return self.start_move("heavy_punch")
            return self.start_move("medium_punch" if st.fwd(self.facing_right) else "light_punch")
        if st.pressed["kick"]:
            if self.crouching:
                return self.start_move("light_kick")
            if strength_mod:
                return self.start_move("heavy_kick")
            return self.start_move("medium_kick" if st.fwd(self.facing_right) else "light_kick")
        if st.pressed["special"] and self.transform == "kurama" and self.meter >= 100:
            return self.start_move("bijuu_dama") if "bijuu_dama" in self.d.moves else False
        if st.pressed["special"] and self.transform == "susanoo" and self.meter >= 100:
            return self.start_move("indra_arrow") if "indra_arrow" in self.d.moves else False
        return False

    # ---------- به‌روزرسانی ----------
    def update(self, inp_source):
        if self.hitstop > 0:
            self.hitstop -= 1
            return
        self.state_t += 1
        if self.invuln > 0:
            self.invuln -= 1
        if self.armor > 0:
            self.armor -= 1
        if self.flash > 0:
            self.flash -= 1
        if self.transform_t > 0:
            self.transform_t -= 1
            if self.transform_t == 0:
                self.transform = None
            elif self.transform == "kurama" and self.state_t % 20 == 0:
                self.health = min(self.max_health, self.health + 3)
        self.aura = max(0.0, self.aura - 0.01)
        if self.stunned > 0:
            self.stunned -= 1
        if self.burn_t > 0:
            self.burn_t -= 1
            if self.burn_t % 12 == 0 and not self.dead:
                self.health = max(1, self.health - self.burn_dmg)
                self.flash = 2
        if self.transform == "susanoo" and self.armor < 2:
            self.armor = 2

        st = inp_source.state if inp_source else None
        speed_mult = 1.35 if self.transform == "kurama" else 1.0

        # --- stun timers ---
        if self.hitstun > 0:
            self.hitstun -= 1
            if self.hitstun == 0 and not self.airborne and not self.is_knocked():
                self.set_state("idle")
        if self.blockstun > 0:
            self.blockstun -= 1
            if self.blockstun == 0:
                self.set_state("crouch" if self.crouching else "idle")

        # --- ماشین حالت ---
        if self.state == "attack":
            mv = self.move
            if mv.move_forward and self.state_t <= mv.startup + mv.active:
                self.vx = mv.move_forward * self.dir()
            if self.state_t >= mv.total:
                self.set_state("crouch" if self.crouching else ("jump_fall" if self.airborne else "idle"))
            elif st and mv.cancel_into_special and self.state_t > mv.startup and self.multi_hits > 0:
                self.try_specials(inp_source)
        elif self.state == "knockdown":
            if not self.airborne and self.state_t > 6:
                self.set_state("lying")
                self.vx = 0
        elif self.state == "lying":
            if self.dead:
                pass
            elif self.state_t > 34:
                self.set_state("getup")
                self.invuln = 20
        elif self.state == "getup":
            if self.state_t > 16:
                self.set_state("idle")
        elif self.state == "dash":
            self.vx = self.d.dash_speed * self.dash_dir
            if self.state_t > 12:
                self.set_state("idle")
        elif self.state in ("hit_high", "hit_low"):
            pass
        elif self.state == "jump_pre":
            if self.state_t >= 3:
                self.vy = self.d.jump_velocity
                self.airborne = True
                self.set_state("jump_up")
                self.stats["jumps"] += 1
        elif self.state == "jump_land":
            if self.state_t >= 4:
                self.set_state("idle")
        elif st is not None and self.actionable() and self.stunned == 0:
            self._handle_input(inp_source, st, speed_mult)

        # --- فیزیک ---
        if self.airborne:
            self.vy += S.GRAVITY
            self.vy = min(self.vy, S.MAX_FALL_SPEED)
            self.y += self.vy
            if self.state == "jump_up" and self.vy > -4:
                self.set_state("jump_apex")
            elif self.state == "jump_apex" and self.vy > 4:
                self.set_state("jump_fall")
            if self.y >= S.FLOOR_Y:
                self.y = S.FLOOR_Y
                self.airborne = False
                self.vy = 0
                if self.state == "knockdown" or self.knocked:
                    self.knocked = False
                    self.set_state("lying")
                    self.vx = 0
                elif self.state == "attack":
                    self.set_state("idle")
                else:
                    self.set_state("jump_land")
                    self.vx = 0
        self.x += self.vx
        if not self.airborne and self.state not in ("dash",) and not (self.state == "attack" and self.move.move_forward):
            self.vx *= 0.6 if abs(self.vx) > 0.5 else 0
        self.x = max(S.WALL_MARGIN, min(S.STAGE_WIDTH - S.WALL_MARGIN, self.x))

        # --- پرتابه/کلون ---
        for p in self.projectiles:
            p.update(self.opponent)
        self.projectiles = [p for p in self.projectiles if not p.dead]
        for c in self.clones:
            c.update(self.opponent)
        self.clones = [c for c in self.clones if not c.dead]

        # --- شلیک پرتابه در فریم فعال ---
        if self.state == "attack" and self.move.projectile and self.state_t == self.move.startup and "proj" not in self.move_hit_done:
            self.move_hit_done.add("proj")
            p = self.move.projectile
            self.projectiles.append(Projectile(self, self.move, self.x + 60 * self.dir(), self.y + p.get("y", -220), self.facing_right))

    def _handle_input(self, inp_source, st, speed_mult):
        self.face_opponent()
        d = st.direction(self.facing_right)
        self.crouching = d in ("down", "downfwd", "downback")
        holding_back = d in ("back", "downback")
        # گارد: نگه داشتن عقب یا دکمه‌ی block
        want_block = st.held["block"] or (holding_back and self.opponent and self.opponent.is_threatening())
        # ویژه‌ها اولویت دارند
        if self.try_specials(inp_source):
            return
        # پرش
        if d in ("up", "upfwd", "upback"):
            self.vx = (self.d.jump_forward if d == "upfwd" else -self.d.jump_forward if d == "upback" else 0) * self.dir() * speed_mult
            self.set_state("jump_pre")
            return
        # دَش
        if st.pressed["dash"] or inp_source.double_tap("fwd", self.facing_right):
            self.dash_dir = self.dir() * (-1 if holding_back else 1)
            self.set_state("dash")
            inp_source.clear_history()
            return
        if inp_source.double_tap("back", self.facing_right):
            self.dash_dir = -self.dir()
            self.set_state("dash")
            inp_source.clear_history()
            return
        # ضربات
        if self.try_normals(st):
            return
        # گارد / حرکت
        if want_block:
            self.blocking = True
            self.set_state("crouch_block" if self.crouching else "block") if self.state not in ("block", "crouch_block") else None
            self.vx = 0
            return
        self.blocking = False
        if self.crouching:
            if self.state != "crouch":
                self.set_state("crouch")
            self.vx = 0
        elif d in ("fwd",):
            self.vx = self.d.walk_speed * self.dir() * speed_mult
            if self.state != "walk":
                self.set_state("walk")
        elif d in ("back",):
            self.vx = -self.d.back_speed * self.dir() * speed_mult
            if self.state != "walk_back":
                self.set_state("walk_back")
        else:
            self.vx = 0
            if self.state != "idle":
                self.set_state("idle")

    def is_threatening(self):
        """آیا حریف در حال حمله است (برای گارد خودکار با عقب نگه‌داشتن)."""
        if self.state == "attack":
            return True
        if self.projectiles:
            return True
        return any(c.state == "attack" for c in self.clones)

    # ---------- هیت‌باکس فعال ----------
    def active_hitbox(self):
        if self.state != "attack" or not self.move:
            return None
        mv = self.move
        if mv.projectile or mv.damage == 0:
            return None
        t = self.state_t
        # چندضربه‌ای: هر N فریم دوباره فعال می‌شود
        multi = next((int(tg.split("_")[-1]) for tg in mv.tags if tg.startswith("multi_hit_")), 1)
        if mv.startup <= t < mv.startup + mv.active:
            if multi > 1:
                seg = max(1, mv.active // multi)
                idx = (t - mv.startup) // seg
                key = f"h{idx}"
                if key in self.move_hit_done:
                    return None
                self._pending_key = key
            else:
                if "h0" in self.move_hit_done:
                    return None
                self._pending_key = "h0"
            hb = mv.hitbox
            reach = 1.25 if self.transform in ("kurama", "susanoo") else 1.0
            if self.facing_right:
                return pygame.Rect(int(self.x + hb.x), int(self.y + hb.y), int(hb.w * reach), int(hb.h))
            return pygame.Rect(int(self.x - hb.x - hb.w * reach), int(self.y + hb.y), int(hb.w * reach), int(hb.h))
        return None

    def mark_hit(self):
        self.move_hit_done.add(getattr(self, "_pending_key", "h0"))
        self.multi_hits += 1

    # ---------- دریافت ضربه ----------
    def can_block(self, mv: Move, unblockable=False) -> bool:
        if unblockable:
            return False
        if self.airborne or self.is_knocked() or self.state == "attack" or self.stunned:
            return False
        if not (self.blocking or self.state in ("block", "crouch_block")):
            # گارد با عقب نگه‌داشتن
            if not (self.input and self.input.state.back(self.facing_right)):
                return False
        if mv.hits_low and not self.crouching:
            return False
        if mv.hits_high and self.crouching:
            return False
        return True

    def take_hit(self, mv: Move, attacker, damage_scale=1.0, unblockable=False, from_projectile=False):
        """برمی‌گرداند 'block' | 'hit' | 'armor'"""
        if self.invuln > 0 and not from_projectile:
            return "miss"
        if self.can_block(mv, unblockable):
            chip = int(mv.damage * S.CHIP_DAMAGE_RATIO) if mv.strength in ("special", "ultimate") else 0
            self.health = max(1 if chip else 0, self.health - chip)
            self.blockstun = mv.blockstun
            self.set_state("crouch_block" if self.crouching else "block")
            self.vx = -S.PUSHBACK_ON_BLOCK * self.dir() * 0.6
            self.add_meter(S.METER_PER_BLOCK)
            self.stats["blocks"] += 1
            self.hitstop = S.HITSTOP.get(mv.strength, 5) // 2
            return "block"
        if self.armor > 0 and mv.strength in ("light", "medium"):
            dmg = int(mv.damage * damage_scale * 0.5)
            self.health -= dmg
            self.flash = 4
            return "armor"
        dmg = int(mv.damage * damage_scale)
        if self.transform == "kurama":
            dmg = int(dmg * 0.8)
        elif self.transform == "susanoo":
            dmg = int(dmg * 0.6)
        self.health -= dmg
        self.add_meter(S.METER_PER_HIT_TAKEN)
        self.hitstun = mv.hitstun
        self.blockstun = 0
        self.blocking = False
        self.crouching = False
        self.flash = 6
        self.hitstop = S.HITSTOP.get(mv.strength, 5)
        self.last_hit_by = attacker
        kb = mv.knockback * self.d.weight
        self.vx = -kb * self.dir() if attacker.x * self.dir() > self.x * self.dir() or True else kb
        # جهت پرتاب بر اساس موقعیت حمله‌کننده
        push_dir = -1 if attacker.x < self.x else 1
        self.vx = kb * push_dir
        for tg in mv.tags:
            if tg.startswith("burn_"):
                _, dur, per = tg.split("_")
                self.burn_t = int(dur)
                self.burn_dmg = int(per)
                self.burn_by = attacker
        if "stun_180" in mv.tags:
            self.stunned = 180
            self.set_state("hit_high")
            self.hitstun = 180
            return "hit"
        if mv.launch or mv.knockdown or self.airborne or self.health <= 0:
            self.vy = mv.launch if mv.launch else -6.0
            self.airborne = True
            self.knocked = True
            self.set_state("knockdown")
            self.hitstun = 999
        else:
            self.set_state("hit_low" if mv.hits_low else "hit_high")
        if self.health <= 0:
            self.health = 0
            self.dead = True
            self.hitstun = 999
            self.vy = -14
            self.vx = 9 * push_dir
        return "hit"

    # ---------- رسم ----------
    def _special_frame(self, anim):
        """حرکات ویژه‌ی چندفریمی: فریم‌ها روی طول کل حرکت (startup+active+recovery) پخش می‌شوند.
        فریم‌های ابتدایی در startup، فریم میانی/اوج در active، بقیه در recovery؛ فریم آخر نگه داشته می‌شود."""
        mv = self.move
        n = len(anim.frames)
        if n <= 1 or mv is None:
            return anim.frame_at(self.state_t)
        total = max(1, mv.startup + mv.active + mv.recovery)
        t = min(self.state_t, total - 1)
        # نگاشت غیرخطی: تا پایان active نیمه‌ی اول+یک فریم را می‌بینیم، بقیه در recovery
        peak = max(1, n // 2)
        if t < mv.startup:
            i = int(t / max(1, mv.startup) * peak)
        elif t < mv.startup + mv.active:
            i = peak + int((t - mv.startup) / max(1, mv.active) * max(1, (n - peak) // 2))
        else:
            rest = n - 1 - (peak + max(1, (n - peak) // 2) - 1)
            i = (peak + max(1, (n - peak) // 2) - 1) + int((t - mv.startup - mv.active) / max(1, mv.recovery) * (rest + 1))
        i = max(0, min(n - 1, i))
        return anim.frames[i], i

    def draw(self, surf, cam, debug=False):
        name = self._anim_name()
        anim = self.sprites.get(name, self.facing_right)
        if self.state == "attack" and self.move and name == self.move.anim and name not in (
                "light_punch", "medium_punch", "heavy_punch", "light_kick", "medium_kick", "heavy_kick", "crouch_punch"):
            frame, _ = self._special_frame(anim)
        else:
            frame, _ = anim.frame_at(self.state_t)
        if frame is None:
            return
        fx = int(self.x - cam - frame.get_width() // 2)
        fy = int(self.y - frame.get_height())
        if self.state in ("lying", "ko") or (self.state == "knockdown" and not self.airborne):
            fy = int(self.y - frame.get_height())
        # هاله‌ی تبدیل/چاکرا
        if self.transform or self.aura > 0:
            glow = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            col = {"kurama": (255, 190, 40), "susanoo": (140, 60, 255)}.get(self.transform, self.d.aura_color)
            a = 120 if self.transform else int(160 * self.aura)
            mask = pygame.mask.from_surface(frame)
            outline = mask.outline(4)
            if len(outline) > 2:
                pygame.draw.polygon(glow, (*col, a), outline, 8)
            surf.blit(glow, (fx, fy), special_flags=pygame.BLEND_ADD)
        img = frame
        if self.flash > 0 and self.flash % 2 == 0:
            img = frame.copy()
            img.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)
        elif self.transform == "kurama" and not self.sprites.has("kurama"):
            img = frame.copy()
            img.fill((90, 60, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.transform == "susanoo":
            self._draw_susanoo(surf, cam)
        surf.blit(img, (fx, fy))
        if self.state == "attack" and self.move and self.move.name in ("Chidori", "Chidori Sharp Spear") and FX.has(self.d.slug, "chidori"):
            self._draw_chidori(surf, cam, frame, fx, fy)
        if self.burn_t > 0:
            self._draw_amaterasu(surf, fx, fy, frame)
        for p in self.projectiles:
            p.draw(surf, cam)
        for c in self.clones:
            c.draw(surf, cam)
        if debug:
            hr = self.hurt_rect()
            pygame.draw.rect(surf, (60, 200, 255), hr.move(-cam, 0), 2)
            hb = self.active_hitbox()
            if hb:
                pygame.draw.rect(surf, (255, 60, 60), hb.move(-cam, 0), 2)

    def _draw_susanoo(self, surf, cam):
        """Susanoo ساسکه: اسپرایت اختصاصی پشت کاراکتر (نیمه‌شفاف، نفس‌کشنده)؛ در نبود اسپرایت، نسخه‌ی پروسیجرال."""
        t = self.state_t
        if self.sprites.has("susanoo"):
            fr = self.sprites.anims["susanoo"].frames[0]
            H = int(self.d.height * 1.72 * (1 + 0.012 * math.sin(t * 0.08)))
            sc = H / fr.get_height()
            key = ("susanoo_big", H, self.facing_right)
            cache = self.__dict__.setdefault("_big_cache", {})
            if key not in cache:
                img = pygame.transform.smoothscale(fr, (int(fr.get_width() * sc), H))
                if not self.facing_right:
                    img = pygame.transform.flip(img, True, False)
                img.set_alpha(190)
                cache.clear()
                cache[key] = img
            img = cache[key]
            # اگر تازه فعال شده: از پایین بالا می‌آید
            grow = min(1.0, self.aura * 1.5) if self.transform_t > 560 else 1.0
            fy = int(self.y - H * (0.98 if grow >= 1 else 0.98 * (0.6 + 0.4 * grow)))
            surf.blit(img, (int(self.x - cam - img.get_width() * (0.5 if self.facing_right else 0.5)), fy))
            return
        w, h = int(self.d.width * 5.2), int(self.d.height * 1.55)
        g = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (120, 50, 230, 70)
        edge = (190, 140, 255, 150)
        cx = w // 2
        pygame.draw.ellipse(g, col, (cx - w * 0.36, h * 0.2, w * 0.72, h * 0.75))
        pygame.draw.ellipse(g, edge, (cx - w * 0.36, h * 0.2, w * 0.72, h * 0.75), 4)
        for i in range(5):  # دنده‌ها
            y = h * 0.3 + i * h * 0.1
            pygame.draw.arc(g, edge, (cx - w * 0.34, y, w * 0.68, h * 0.28), 0.2, 2.9, 4)
        # جمجمه
        pygame.draw.ellipse(g, (150, 90, 255, 110), (cx - w * 0.14, h * 0.02, w * 0.28, h * 0.22))
        pygame.draw.ellipse(g, edge, (cx - w * 0.14, h * 0.02, w * 0.28, h * 0.22), 3)
        for sx in (-1, 1):
            pygame.draw.circle(g, (255, 230, 120, 200), (int(cx + sx * w * 0.06), int(h * 0.11)), 6 + (t // 6) % 3)
        surf.blit(g, (int(self.x - cam - cx), int(self.y - h * 0.98)))

    def _draw_chidori(self, surf, cam, frame, fx, fy):
        """گوی رعد روی دست جلو؛ برای Sharp Spear کشیده می‌شود."""
        t = self.state_t
        w, h = frame.get_size()
        hx = fx + int(w * (0.86 if self.facing_right else 0.14))
        hy = fy + int(h * 0.27)
        if self.move.name == "Chidori Sharp Spear":
            mv = self.move
            if mv.startup <= t < mv.startup + mv.active + 6:
                L = int(mv.hitbox.w * 1.0)
                img = FX.frame(self.d.slug, "chidori", t // 3, height=int(h * 0.5))
                img = pygame.transform.scale(img, (L, int(h * 0.3)))
                if not self.facing_right:
                    img = pygame.transform.flip(img, True, False)
                sx = hx if self.facing_right else hx - L
                surf.blit(img, (sx, hy - img.get_height() // 2))
            else:
                img = FX.frame(self.d.slug, "chidori", t // 3, height=int(h * 0.45))
                surf.blit(img, (hx - img.get_width() // 2, hy - img.get_height() // 2))
            return
        img = FX.frame(self.d.slug, "chidori", t // 3, height=int(h * (0.55 + 0.1 * math.sin(t * 0.9))))
        surf.blit(img, (hx - img.get_width() // 2, hy - img.get_height() // 2))

    def _draw_amaterasu(self, surf, fx, fy, frame):
        if FX.has("sasuke", "amaterasu"):
            w, h = frame.get_size()
            t = self.state_t + self.burn_t
            for j, (ox, oy, hh) in enumerate(((0.5, 0.15, 0.55), (0.25, 0.5, 0.42), (0.7, 0.55, 0.4))):
                img = FX.frame("sasuke", "amaterasu", t // 5 + j, height=int(h * hh))
                surf.blit(img, (fx + int(w * ox) - img.get_width() // 2, fy + int(h * oy) - img.get_height() // 2))
            return
        import random as _r
        rnd = _r.Random(self.state_t // 3)
        w, h = frame.get_size()
        for _ in range(9):
            px = fx + rnd.randint(int(w * 0.25), int(w * 0.75))
            py = fy + rnd.randint(int(h * 0.05), int(h * 0.9))
            rr = rnd.randint(8, 18)
            pygame.draw.circle(surf, (10, 5, 15), (px, py), rr)
            pygame.draw.circle(surf, (40, 20, 60), (px, py - rr // 2), rr // 2)

    def _anim_name(self):
        if self.transform == "kurama" and self.sprites.has("kurama") and self.state in ("idle", "walk", "walk_back", "dash", "crouch", "block"):
            return "kurama"
        if self.state == "attack" and self.move:
            return self.move.anim if self.sprites.has(self.move.anim) else "medium_punch"
        if self.state == "dash":
            return "walk"
        if self.state == "ko":
            return "ko"
        if self.dead and self.state in ("lying", "knockdown"):
            return "lying" if not self.airborne else "knockdown"
        return self.state
