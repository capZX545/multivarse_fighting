"""بارگذاری اسپرایت‌ها و انیمیشن‌ها با کش، مقیاس‌بندی و آینه."""
import os
import glob
import pygame

from pyfighter import paths, settings

_cache = {}


def _load(path: str) -> pygame.Surface:
    if path not in _cache:
        _cache[path] = pygame.image.load(path).convert_alpha()
    return _cache[path]


def load_frames(char_dir: str, prefix: str) -> list:
    files = sorted(glob.glob(os.path.join(char_dir, f"{prefix}_*.png")),
                   key=lambda p: int(p.rsplit("_", 1)[1].split(".")[0]))
    return [_load(p) for p in files]


class Animation:
    """یک انیمیشن: لیست فریم‌ها + مدت هر فریم (به فریم‌های بازی، ۶۰fps)."""

    def __init__(self, frames, durations, loop=True):
        self.frames = frames
        self.durations = durations if isinstance(durations, list) else [durations] * len(frames)
        self.loop = loop
        self.total = sum(self.durations)

    def frame_at(self, t: int):
        """فریم در زمان t (فریم بازی از شروع انیمیشن). خروجی (surface, index)."""
        if not self.frames:
            return None, 0
        if self.loop:
            t %= max(1, self.total)
        else:
            t = min(t, self.total - 1)
        acc = 0
        for i, d in enumerate(self.durations):
            acc += d
            if t < acc:
                return self.frames[i], i
        return self.frames[-1], len(self.frames) - 1

    def finished(self, t: int) -> bool:
        return (not self.loop) and t >= self.total


class CharacterSprites:
    """
    همه‌ی انیمیشن‌های یک کاراکتر، مقیاس‌شده به ارتفاع استاندارد.
    فریم‌ها بر اساس ارتفاع فریم idle نرمال می‌شوند تا نسبت‌ها بین حالت‌ها حفظ شود.
    """

    def __init__(self, slug: str, target_height=settings.CHAR_HEIGHT):
        self.slug = slug
        self.dir = os.path.join(paths.CHAR_ASSETS, slug)
        idle = load_frames(self.dir, "idle")
        if not idle:
            raise FileNotFoundError(f"no idle sprite for {slug}")
        self.scale = target_height / idle[0].get_height()
        self.target_height = target_height
        self.meta = {"heights": {}, "widths": {}}
        mp = os.path.join(self.dir, "meta.json")
        if os.path.isfile(mp):
            import json
            with open(mp, encoding="utf-8") as f:
                self.meta.update(json.load(f))
        self.anims = {}
        self.flipped = {}
        self._build()
        self.portrait = self._load_portrait()

    def _scaled(self, frames, keys=None):
        """مقیاس: پیش‌فرض نسبت idle؛ اگر در meta برای این فریم ضریب ارتفاع/عرض تعریف شده، به آن نرمال می‌شود."""
        out = []
        for i, f in enumerate(frames):
            w, h = f.get_size()
            sc = self.scale
            key = keys[i] if keys else None
            if key:
                base = key.rsplit("_", 1)[0]
                hk = self.meta["heights"].get(key, self.meta["heights"].get(base))
                wk = self.meta["widths"].get(key, self.meta["widths"].get(base))
                if hk is not None:
                    sc = self.target_height * hk / h
                elif wk is not None:
                    sc = self.target_height * wk / w
            out.append(pygame.transform.smoothscale(f, (max(1, int(w * sc)), max(1, int(h * sc)))))
        return out

    def _add(self, name, prefix, durations, loop, indices=None):
        frames = load_frames(self.dir, prefix)
        idx = list(range(len(frames))) if indices is None else [i for i in indices if i < len(frames)]
        frames = [frames[i] for i in idx]
        if not frames:
            return False
        frames = self._scaled(frames, keys=[f"{prefix}_{i}" for i in idx])
        self.anims[name] = Animation(frames, durations, loop)
        self.flipped[name] = Animation([pygame.transform.flip(f, True, False) for f in frames], durations, loop)
        return True

    def _build(self):
        a = self._add
        a("idle", "idle", 8, True)
        a("walk", "walk", 6, True)
        # عقب رفتن = راه رفتن معکوس
        if "walk" in self.anims:
            w = self.anims["walk"]
            self.anims["walk_back"] = Animation(list(reversed(w.frames)), 6, True)
            self.flipped["walk_back"] = Animation(list(reversed(self.flipped["walk"].frames)), 6, True)
        # jump: 0 crouch, 1 launch, 2 apex, 3 fall, 4 land (اگر ۷ فریم بود، ۳ تای اول crouch هستند)
        jf = load_frames(self.dir, "jump")
        if len(jf) >= 7:
            a("jump_pre", "jump", 3, False, [0, 1, 2])
            a("jump_up", "jump", 6, False, [3])
            a("jump_apex", "jump", 6, False, [4])
            a("jump_fall", "jump", 6, False, [5])
            a("jump_land", "jump", 5, False, [6])
        elif len(jf) >= 5:
            a("jump_pre", "jump", 4, False, [0])
            a("jump_up", "jump", 6, False, [1])
            a("jump_apex", "jump", 6, False, [2])
            a("jump_fall", "jump", 6, False, [3])
            a("jump_land", "jump", 5, False, [4])
        # cb: 0 crouch, 1 crouch punch, 2 block, 3 crouch block
        a("crouch", "cb", 8, True, [0])
        a("crouch_punch", "cb", [3, 6, 4], False, [0, 1, 0])
        a("block", "cb", 8, True, [2])
        a("crouch_block", "cb", 8, True, [3])
        # punch: 0 guard, 1 jab, 2 straight, 3 hook, 4 uppercut
        a("light_punch", "punch", [2, 5, 3], False, [0, 1, 0])
        a("medium_punch", "punch", [3, 7, 5], False, [0, 2, 0])
        a("heavy_punch", "punch", [4, 4, 9, 6], False, [0, 3, 4, 0])
        # kick: 0 stance, 1 low, 2 mid, 3 knee, 4 high
        a("light_kick", "kick", [2, 6, 3], False, [0, 1, 0])
        a("medium_kick", "kick", [3, 8, 5], False, [0, 2, 0])
        a("heavy_kick", "kick", [4, 4, 10, 6], False, [0, 3, 4, 0])
        # hit: 0 head, 1 body, 2 fly, 3 down, 4 getup
        a("hit_high", "hit", 10, False, [0])
        a("hit_low", "hit", 10, False, [1])
        a("knockdown", "hit", 30, False, [2])
        a("lying", "hit", 40, False, [3])
        a("getup", "hit", 16, False, [4])
        a("ko", "hit", [24, 60], False, [2, 3])
        # قدرت‌های ویژه: هر پوشه‌ی اسپرایت با نام دلخواه (توسط تعریف کاراکتر ارجاع می‌شود)
        for p in glob.glob(os.path.join(self.dir, "*_0.png")):
            name = os.path.basename(p)[:-6]
            if name not in ("idle", "walk", "jump", "cb", "punch", "kick", "hit"):
                # حرکت ویژه: چند فریم پشت‌سرهم؛ زمان‌بندی واقعی در Fighter بر اساس طول حرکت کشیده می‌شود
                a(name, name, 6, False)
        # جایگزین‌ها
        for missing, fallback in [("walk", "idle"), ("walk_back", "walk"), ("crouch", "idle"), ("block", "idle"),
                                  ("crouch_block", "crouch"), ("crouch_punch", "light_punch"),
                                  ("jump_pre", "idle"), ("jump_up", "idle"), ("jump_apex", "jump_up"),
                                  ("jump_fall", "jump_apex"), ("jump_land", "jump_pre"),
                                  ("hit_high", "idle"), ("hit_low", "hit_high"), ("knockdown", "hit_low"),
                                  ("lying", "knockdown"), ("getup", "idle"), ("ko", "lying"),
                                  ("light_punch", "idle"), ("medium_punch", "light_punch"), ("heavy_punch", "medium_punch"),
                                  ("light_kick", "light_punch"), ("medium_kick", "light_kick"), ("heavy_kick", "medium_kick")]:
            if missing not in self.anims and fallback in self.anims:
                self.anims[missing] = self.anims[fallback]
                self.flipped[missing] = self.flipped[fallback]

    def _load_portrait(self):
        p = os.path.join(self.dir, "portrait.png")
        if os.path.isfile(p):
            return _load(p)
        # از فریم idle یک پرتره بساز (سر و سینه)
        f = self.anims["idle"].frames[0]
        w, h = f.get_size()
        crop = f.subsurface(pygame.Rect(0, 0, w, int(h * 0.42))).copy()
        surf = pygame.Surface((256, 256), pygame.SRCALPHA)
        surf.fill((24, 28, 48))
        s = 256 / crop.get_height()
        c = pygame.transform.smoothscale(crop, (int(w * s), 256))
        surf.blit(c, ((256 - c.get_width()) // 2, 0))
        return surf

    def get(self, name: str, facing_right: bool) -> Animation:
        table = self.anims if facing_right else self.flipped
        return table.get(name) or table["idle"]

    def has(self, name: str) -> bool:
        return name in self.anims


_sprite_cache = {}


def get_character_sprites(slug: str) -> CharacterSprites:
    if slug not in _sprite_cache:
        _sprite_cache[slug] = CharacterSprites(slug)
    return _sprite_cache[slug]
