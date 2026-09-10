"""
هوش مصنوعی تطبیق‌پذیر برای حالت فایتینگ.

سه لایه:
  1) PlayerProfile — آمار رفتاری حریف انسانی (پرش، گارد، پرتابه، ضربات پرتکرار، پاسخ بعد از knockdown...)
     بین مسابقات ذخیره می‌شود (به ازای هر کاراکتر انسان).
  2) Utility scoring — هر فریم تصمیم، لیست گزینه‌ها (نزدیک شدن، عقب رفتن، پرش، ضربه X، ویژه Y، گارد، دَش)
     امتیاز می‌گیرند بر اساس وضعیت فعلی + پروفایل حریف + شخصیت AI. بهترین (با کمی نویز) انتخاب می‌شود.
  3) Reaction model — زمان واکنش انسانی + احتمال خطا؛ سطح سختی فقط این‌ها را عوض می‌کند.
"""
import json
import os
import random
from collections import Counter, deque

from pyfighter import settings as S, paths

DIFFICULTY = {
    # reaction (فریم), error (احتمال اشتباه گارد/whiff), aggression پایه, adapt (سرعت یادگیری)
    "easy":   {"reaction": 22, "error": 0.45, "aggression": 0.35, "adapt": 0.4, "special_rate": 0.25},
    "normal": {"reaction": 14, "error": 0.25, "aggression": 0.5, "adapt": 0.7, "special_rate": 0.45},
    "hard":   {"reaction": 9,  "error": 0.12, "aggression": 0.65, "adapt": 1.0, "special_rate": 0.65},
    "insane": {"reaction": 5,  "error": 0.04, "aggression": 0.75, "adapt": 1.3, "special_rate": 0.85},
}


class PlayerProfile:
    """آمار رفتاری بازیکن انسانی (ذخیره‌شونده)."""

    def __init__(self, key: str):
        self.key = key
        self.path = os.path.join(paths.save_dir(), f"profile_{key}.json")
        self.data = {
            "frames": 1, "jumps": 0, "blocks": 0, "crouch_frames": 0, "block_frames": 0,
            "projectiles": 0, "specials": 0, "dashes": 0,
            "moves": {}, "wakeup": {"attack": 0, "block": 0, "jump": 0, "backdash": 0, "idle": 0},
            "pref_distance": [], "hits_taken_by": {}, "combo_starters": {},
            "matches": 0,
        }
        self.load()

    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                saved = json.load(f)
            for k, v in saved.items():
                self.data[k] = v
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            d = dict(self.data)
            d["pref_distance"] = d["pref_distance"][-400:]
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(d, f)
        except OSError:
            pass

    # نرخ‌ها (به ازای ۱۰۰۰ فریم)
    def rate(self, key):
        return self.data.get(key, 0) * 1000.0 / max(1, self.data["frames"])

    @property
    def jump_rate(self):
        return self.rate("jumps")

    @property
    def block_ratio(self):
        return self.data["block_frames"] / max(1, self.data["frames"])

    @property
    def crouch_ratio(self):
        return self.data["crouch_frames"] / max(1, self.data["frames"])

    @property
    def projectile_rate(self):
        return self.rate("projectiles")

    def favorite_move(self):
        m = self.data["moves"]
        if not m:
            return None, 0.0
        name, cnt = Counter(m).most_common(1)[0]
        return name, cnt / max(1, sum(m.values()))

    def wakeup_pref(self):
        w = self.data["wakeup"]
        tot = sum(w.values())
        if tot < 3:
            return None, 0.0
        k, v = max(w.items(), key=lambda kv: kv[1])
        return k, v / tot

    def avg_distance(self):
        pd = self.data["pref_distance"]
        return sum(pd[-200:]) / max(1, len(pd[-200:])) if pd else 350


class FighterAI:
    def __init__(self, me, opponent, difficulty="normal", profile_key="human"):
        self.me = me
        self.opp = opponent
        self.cfg = DIFFICULTY.get(difficulty, DIFFICULTY["normal"])
        self.profile = PlayerProfile(profile_key)
        self.profile.data["matches"] += 1
        # شخصیت پویا
        self.aggression = self.cfg["aggression"]
        self.patience = 0.5
        self.risk = 0.5
        # واکنش
        self.pending = deque()          # (frame_ready, action)
        self.frame = 0
        self.decision_cd = 0
        self.current_plan = None
        self.plan_t = 0
        self.last_opp_state = opponent.state
        self.last_opp_airborne = False
        self.opp_was_knocked = False
        self.opp_last_move = None
        self.combo_memory = deque(maxlen=12)   # ضربات اخیر حریف با فاصله فریمی
        self.last_opp_attack_frame = -999
        self.punish_window = 0
        self.block_intent = False
        self.crouch_intent = False
        self.hold_dir = 0      # -1 عقب, 0, +1 جلو
        self.jump_intent = None
        self.action = None
        self.debug_text = ""
        self.round_health_ratio = 1.0
        self.sequence_predictor = SequencePredictor()

    # ---------- مشاهده حریف ----------
    def observe(self):
        p = self.profile.data
        o = self.opp
        p["frames"] += 1
        if o.state == "jump_pre" and self.last_opp_state != "jump_pre":
            p["jumps"] += 1
            self._on_wakeup_choice("jump")
        if o.state in ("block", "crouch_block"):
            p["block_frames"] += 1
        if o.crouching:
            p["crouch_frames"] += 1
        if o.state == "dash" and self.last_opp_state != "dash":
            p["dashes"] += 1
            if o.dash_dir != o.dir():
                self._on_wakeup_choice("backdash")
        if o.state == "attack" and o.move and (self.last_opp_state != "attack" or self.opp_last_move is not o.move):
            name = o.move.name
            p["moves"][name] = p["moves"].get(name, 0) + 1
            if o.move.projectile:
                p["projectiles"] += 1
            if o.move.strength in ("special", "ultimate"):
                p["specials"] += 1
            self.combo_memory.append((self.frame - self.last_opp_attack_frame, name))
            self.sequence_predictor.push(name)
            self.last_opp_attack_frame = self.frame
            self._on_wakeup_choice("attack")
            self.opp_last_move = o.move
        if self.frame % 30 == 0:
            p["pref_distance"].append(abs(o.x - self.me.x))
        # wake-up tracking
        if o.is_knocked():
            self.opp_was_knocked = True
        elif self.opp_was_knocked and o.state == "idle":
            self.opp_wakeup_frame = self.frame
        self.last_opp_state = o.state
        self.last_opp_airborne = o.airborne

    def _on_wakeup_choice(self, kind):
        if getattr(self, "opp_wakeup_frame", -999) > self.frame - 20:
            self.profile.data["wakeup"][kind] += 1
            self.opp_wakeup_frame = -999

    # ---------- شخصیت پویا ----------
    def update_personality(self):
        me, o = self.me, self.opp
        hp_me = me.health / me.max_health
        hp_o = o.health / o.max_health
        base = self.cfg["aggression"]
        # عقب بودن → تهاجمی‌تر (ولی محتاطانه اگر خیلی کم)؛ جلو بودن → صبورتر
        diff = hp_me - hp_o
        target_aggr = base + (-diff * 0.4)
        if hp_me < 0.2:
            target_aggr += 0.15
        self.aggression += (max(0.15, min(0.95, target_aggr)) - self.aggression) * 0.02
        self.patience = 1 - self.aggression
        self.risk = max(0.1, min(0.9, 0.5 - diff * 0.5))

    # ---------- انتخاب اقدام ----------
    def decide(self):
        me, o, pr = self.me, self.opp, self.profile
        dist = abs(o.x - me.x)
        adapt = self.cfg["adapt"]
        opts = {}

        fav_move, fav_share = pr.favorite_move()
        jump_heavy = pr.jump_rate > 2.5
        block_heavy = pr.block_ratio > 0.22
        zoner = pr.projectile_rate > 1.2
        wake_pref, wake_share = pr.wakeup_pref()
        predicted = self.sequence_predictor.predict()

        opp_attacking = o.state == "attack" and o.move is not None
        opp_recovering = opp_attacking and o.state_t > o.move.startup + o.move.active
        opp_startup = opp_attacking and o.state_t < o.move.startup
        opp_air = o.airborne
        proj_incoming = any((p.x - me.x) * (1 if p.vx > 0 else -1) < 0 and abs(p.x - me.x) < 420 for p in o.projectiles)
        my_meter = me.meter

        # --- گزینه‌های حرکتی ---
        opts["approach"] = 0.35 + self.aggression * 0.5 - (0.3 if dist < 150 else 0)
        opts["retreat"] = 0.2 + self.patience * 0.3 + (0.3 if dist < 120 and o.state == "attack" else 0)
        opts["wait"] = 0.25 + self.patience * 0.2
        opts["dash_in"] = (0.3 if dist > 350 else 0.0) + (0.35 * adapt if zoner else 0) + self.aggression * 0.2
        opts["jump_in"] = (0.15 if 250 < dist < 450 else 0.0) + (0.3 * adapt if zoner and dist > 300 else 0)
        opts["crouch"] = 0.05

        # --- دفاعی ---
        opts["block"] = 0.0
        if opp_startup or opp_attacking:
            opts["block"] = 0.75 + (0.25 if o.move.strength in ("heavy", "special") else 0)
        if proj_incoming:
            opts["block"] = max(opts["block"], 0.7)
            opts["jump_in"] += 0.35 * adapt
            if me.slug == "gojo" and me.meter >= 20:
                opts["block"] += 0.2   # Infinity
        if predicted and dist < 260 and not opp_attacking:
            # پیش‌بینی ضربه بعدی کمبوی ثابت حریف → از قبل گارد بگیر
            opts["block"] += 0.35 * adapt

        # --- ضد هوایی ---
        if opp_air and dist < 260 and (o.x - me.x) * me.dir() > 0:
            opts["anti_air"] = 0.8 + (0.3 * adapt if jump_heavy else 0)
        elif jump_heavy and dist < 300 and o.state == "jump_pre":
            opts["anti_air"] = 0.6 * adapt

        # --- تنبیه ---
        if opp_recovering and dist < 220:
            opts["punish"] = 0.95
        if o.is_knocked():
            # اوکیزمه: بر اساس ترجیح بیداری حریف
            if wake_pref == "attack" and wake_share > 0.45:
                opts["meaty_block"] = 0.8 * adapt      # منتظر بمان و گارد بگیر، بعد تنبیه
            elif wake_pref == "block" and wake_share > 0.45:
                opts["throw_pressure"] = 0.75 * adapt  # ضربه پایین/ویژه گاردشکن
            elif wake_pref == "jump" and wake_share > 0.4:
                opts["anti_air_wait"] = 0.7 * adapt
            else:
                opts["approach"] += 0.4
        # --- تهاجمی ---
        if dist < 130 and me.actionable():
            opts["light"] = 0.45 + self.aggression * 0.3
            opts["low"] = 0.3 + (0.45 * adapt if block_heavy and not o.crouching else 0)
            opts["heavy"] = 0.2 + self.risk * 0.3
        elif dist < 200:
            opts["medium"] = 0.4 + self.aggression * 0.3
            opts["low"] = 0.25 + (0.35 * adapt if block_heavy else 0)
        # ویژه‌ها
        sr = self.cfg["special_rate"]
        for name, score in self._special_options(dist, opp_air, opp_attacking, block_heavy, zoner).items():
            opts[name] = score * sr
        # نویز انسانی
        for k in opts:
            opts[k] += random.uniform(-0.12, 0.12)
        best = max(opts.items(), key=lambda kv: kv[1])
        self.debug_text = f"{best[0]} ({best[1]:.2f}) aggr={self.aggression:.2f} fav={fav_move} pred={predicted}"
        return best[0]

    def _special_options(self, dist, opp_air, opp_attacking, block_heavy, zoner):
        me = self.me
        m = me.meter
        opts = {}
        if me.slug == "gojo":
            if 250 < dist < 700 and not opp_air:
                opts["sp_blue"] = 0.55
            if dist < 260 and (opp_attacking or block_heavy):
                opts["sp_red"] = 0.6
            if m >= 200 and dist > 300:
                opts["sp_purple"] = 0.7 + (0.2 if block_heavy else 0)
            if m >= 300 and dist < 500:
                opts["sp_domain"] = 0.95
        elif me.slug == "naruto":
            if dist > 380:
                opts["sp_clone"] = 0.55 + (0.2 if zoner else 0)
            if 120 < dist < 320 and not opp_air:
                opts["sp_rasengan"] = 0.6
            if dist < 200 and opp_attacking is False:
                opts["sp_barrage"] = 0.45
            if m >= 200 and dist > 250:
                opts["sp_rasenshuriken"] = 0.7
            if m >= 300 and me.health < me.max_health * 0.6:
                opts["sp_kurama"] = 0.9
        return opts

    # ---------- اجرا ----------
    SPECIAL_MAP = {
        "sp_blue": "blue", "sp_red": "red", "sp_purple": "purple", "sp_domain": "domain",
        "sp_clone": "clone", "sp_rasengan": "rasengan", "sp_barrage": "barrage",
        "sp_rasenshuriken": "rasenshuriken", "sp_kurama": "kurama",
    }

    def update(self):
        """هر فریم صدا زده می‌شود؛ مستقیم روی Fighter عمل می‌کند (بدون InputSource)."""
        self.frame += 1
        me, o = self.me, self.opp
        self.observe()
        self.update_personality()
        if me.dead or o.dead:
            return
        me.input = None

        # واکنش با تأخیر: تصمیم‌ها در صف با تأخیر reaction اجرا می‌شوند
        if self.decision_cd > 0:
            self.decision_cd -= 1
        else:
            action = self.decide()
            self.pending.append((self.frame + self.cfg["reaction"] + random.randint(-2, 3), action))
            self.decision_cd = random.randint(4, 10)

        while self.pending and self.pending[0][0] <= self.frame:
            _, action = self.pending.popleft()
            self.action = action
            self.plan_t = 0
        self.plan_t += 1
        self._execute()

    def _execute(self):
        me, o = self.me, self.opp
        a = self.action
        dist = abs(o.x - me.x)
        fwd = 1 if o.x > me.x else -1
        me.face_opponent()
        me.blocking = False
        if not me.actionable():
            return
        err = random.random() < self.cfg["error"]

        if a in ("block", "meaty_block"):
            if err and a == "block":
                self._idle()
                return
            # نوع گارد بر اساس ضربه‌ی حریف
            low = o.move.hits_low if (o.state == "attack" and o.move) else (random.random() < 0.4)
            me.crouching = low
            me.blocking = True
            me.set_state("crouch_block" if low else "block") if me.state not in ("block", "crouch_block") else None
            me.vx = 0
        elif a == "approach":
            me.crouching = False
            me.vx = me.d.walk_speed * fwd
            if me.state != "walk":
                me.set_state("walk")
            me.facing_right = fwd > 0
        elif a == "retreat":
            me.crouching = False
            me.vx = -me.d.back_speed * fwd
            if me.state != "walk_back":
                me.set_state("walk_back")
        elif a == "dash_in":
            me.dash_dir = fwd
            me.set_state("dash")
        elif a == "jump_in":
            me.vx = me.d.jump_forward * fwd
            me.set_state("jump_pre")
        elif a == "crouch":
            me.crouching = True
            me.set_state("crouch") if me.state != "crouch" else None
            me.vx = 0
        elif a in ("anti_air", "anti_air_wait"):
            if o.airborne and dist < 260:
                me.start_move("heavy_punch")
            else:
                self._idle()
        elif a == "punish":
            if not err:
                me.start_move("heavy_kick" if dist > 140 else "heavy_punch")
        elif a == "throw_pressure":
            if dist < 160:
                me.start_move("light_kick")
            else:
                me.vx = me.d.walk_speed * fwd
                me.set_state("walk") if me.state != "walk" else None
        elif a == "light":
            me.start_move("light_punch")
        elif a == "medium":
            me.start_move("medium_kick" if dist > 150 else "medium_punch")
        elif a == "low":
            me.crouching = True
            me.start_move("light_kick")
        elif a == "heavy":
            me.start_move("heavy_punch" if random.random() < 0.5 else "heavy_kick")
        elif a in self.SPECIAL_MAP:
            if not me.start_move(self.SPECIAL_MAP[a]):
                self._idle()
        else:
            self._idle()

    def _idle(self):
        me = self.me
        me.vx = 0
        me.crouching = False
        if me.state not in ("idle",):
            me.set_state("idle")

    def on_round_end(self):
        self.profile.save()


class SequencePredictor:
    """پیش‌بینی ضربه‌ی بعدی حریف از روی n-gram های اخیر (کمبوهای تکراری)."""

    def __init__(self):
        self.hist = deque(maxlen=60)
        self.bigrams = Counter()

    def push(self, name):
        if self.hist:
            self.bigrams[(self.hist[-1], name)] += 1
        self.hist.append(name)

    def predict(self):
        if not self.hist:
            return None
        last = self.hist[-1]
        cands = [(k[1], v) for k, v in self.bigrams.items() if k[0] == last]
        if not cands:
            return None
        nxt, cnt = max(cands, key=lambda kv: kv[1])
        total = sum(v for _, v in cands)
        return nxt if cnt >= 3 and cnt / total > 0.5 else None
