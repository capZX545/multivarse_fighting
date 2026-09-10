"""صداهای پروسیجرال (بدون فایل خارجی) با numpy — ضربه، گارد، منو، ویژه."""
import math
import pygame

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


class Audio:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.volume = 0.6
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.ok = np is not None
        except pygame.error:
            self.ok = False
        if self.ok:
            try:
                self._build()
            except Exception:
                self.ok = False

    def _tone(self, freq, dur, kind="sine", decay=6.0, noise=0.0, slide=0.0):
        sr = 22050
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        f = freq + slide * t
        if kind == "sine":
            w = np.sin(2 * math.pi * f * t)
        elif kind == "square":
            w = np.sign(np.sin(2 * math.pi * f * t))
        elif kind == "saw":
            w = 2 * ((f * t) % 1) - 1
        else:
            w = np.zeros(n)
        if noise:
            w = w * (1 - noise) + np.random.uniform(-1, 1, n) * noise
        env = np.exp(-decay * t)
        out = (w * env * 32767 * 0.5).astype(np.int16)
        init = pygame.mixer.get_init()
        if init and init[2] >= 2:
            out = np.column_stack([out] * init[2])
        return pygame.sndarray.make_sound(np.ascontiguousarray(out))

    def _build(self):
        self.sounds["hit_light"] = self._tone(180, 0.12, "square", 20, noise=0.5, slide=-600)
        self.sounds["hit_heavy"] = self._tone(90, 0.25, "saw", 10, noise=0.6, slide=-200)
        self.sounds["block"] = self._tone(600, 0.08, "square", 30, noise=0.2)
        self.sounds["menu_move"] = self._tone(880, 0.05, "square", 40)
        self.sounds["menu_select"] = self._tone(660, 0.15, "sine", 12, slide=800)
        self.sounds["special"] = self._tone(200, 0.4, "saw", 5, noise=0.3, slide=900)
        self.sounds["ko"] = self._tone(60, 0.8, "saw", 3, noise=0.5, slide=-40)
        self.sounds["coin"] = self._tone(1200, 0.12, "sine", 15, slide=1500)
        self.sounds["buy"] = self._tone(500, 0.3, "sine", 6, slide=700)
        self.sounds["error"] = self._tone(150, 0.2, "square", 10)

    def play(self, name):
        if not self.ok:
            return
        s = self.sounds.get(name)
        if s:
            s.set_volume(self.volume)
            s.play()
