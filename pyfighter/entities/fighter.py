"""
موجودیت مبارز: ماشین حالت، فیزیک، ورودی→حرکت، هیت‌باکس/هرت‌باکس، پرتابه، پسیوها.
"""
import math
import random
import pygame

from pyfighter import settings as S
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
        if self.kind == "blue_orb":
            for i in range(3):
                rr = self.radius + 6 * math.sin(t * 0.4 + i)
                pygame.draw.circle(surf, (*self.color, ), (cx, cy), int(rr), 3)
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
            pts = []
            for k in range(4):
                a = t * 0.5 + k * math.pi / 2
                pts.append((cx + math.cos(a) * r * 1.6, cy + math.sin(a) * r * 1.6))
                pts.append((cx + math.cos(a + 0.5) * r * 0.7, cy + math.sin(a + 0.5) * r * 0.7))
            pygame.draw.polygon(surf, self.color, pts)
            pygame.draw.polygon(surf, self.core, pts, 2)
            pygame.draw.circle(surf, self.color, (cx, cy), int(r * 0.6))
            pygame.draw.circle(surf, self.core, (cx, cy), int(r * 0.3))
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
            reach = 1.25 if self.transform == "kurama" else 1.0
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
    def draw(self, surf, cam, debug=False):
        anim = self.sprites.get(self._anim_name(), self.facing_right)
        frame, _ = anim.frame_at(self.state_t)
        if frame is None:
            return
        fx = int(self.x - cam - frame.get_width() // 2)
        fy = int(self.y - frame.get_height())
        if self.state in ("lying", "ko") or (self.state == "knockdown" and not self.airborne):
            fy = int(self.y - frame.get_height())
        # هاله‌ی تبدیل/چاکرا
        if self.transform == "kurama" or self.aura > 0:
            glow = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
            col = (255, 190, 40) if self.transform == "kurama" else self.d.aura_color
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
        elif self.transform == "kurama":
            img = frame.copy()
            img.fill((90, 60, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(img, (fx, fy))
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

    def _anim_name(self):
        if self.state == "attack" and self.move:
            return self.move.anim if self.sprites.has(self.move.anim) else "medium_punch"
        if self.state == "dash":
            return "walk"
        if self.state == "ko":
            return "ko"
        if self.dead and self.state in ("lying", "knockdown"):
            return "lying" if not self.airborne else "knockdown"
        return self.state
