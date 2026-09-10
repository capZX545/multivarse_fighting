"""
سیستم ورودی: کیبورد (۲ بازیکن) + گیم‌پد + لمسی (اندروید).
خروجی هر فریم یک InputState است: جهت‌ها + دکمه‌های فشرده/تازه‌فشرده + تاریخچه برای حرکات ویژه.
"""
import pygame
from collections import deque
from pyfighter import settings

BUTTONS = ("punch", "kick", "special", "block", "dash", "start")

P1_KEYS = {
    "up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d,
    "punch": pygame.K_j, "kick": pygame.K_k, "special": pygame.K_l, "block": pygame.K_u,
    "dash": pygame.K_i, "start": pygame.K_RETURN,
}
P2_KEYS = {
    "up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
    "punch": pygame.K_KP1, "kick": pygame.K_KP2, "special": pygame.K_KP3, "block": pygame.K_KP4,
    "dash": pygame.K_KP5, "start": pygame.K_KP_ENTER,
}
# جایگزین P2 روی لپ‌تاپ بدون numpad
P2_ALT = {"punch": pygame.K_COMMA, "kick": pygame.K_PERIOD, "special": pygame.K_SLASH,
          "block": pygame.K_m, "dash": pygame.K_n, "start": pygame.K_BACKSPACE}

PAD_BUTTONS = {0: "punch", 2: "kick", 3: "special", 1: "block", 5: "dash", 7: "start"}  # X/A/Y/B/RB/Start


class InputState:
    __slots__ = ("up", "down", "left", "right", "held", "pressed", "released", "dir_history", "press_history")

    def __init__(self):
        self.up = self.down = self.left = self.right = False
        self.held = {b: False for b in BUTTONS}
        self.pressed = {b: False for b in BUTTONS}
        self.released = {b: False for b in BUTTONS}
        self.dir_history = deque(maxlen=40)     # (frame, direction) — نسبت به جهت نگاه
        self.press_history = deque(maxlen=20)   # (frame, button)

    def direction(self, facing_right: bool) -> str:
        """جهت ۸گانه نسبت به جلو: neutral/fwd/back/up/down/upfwd/upback/downfwd/downback"""
        h = 0
        if self.left:
            h -= 1
        if self.right:
            h += 1
        if not facing_right:
            h = -h
        v = 0
        if self.up:
            v -= 1
        if self.down:
            v += 1
        if v == 0 and h == 0:
            return "neutral"
        if v == 0:
            return "fwd" if h > 0 else "back"
        if h == 0:
            return "up" if v < 0 else "down"
        if v < 0:
            return "upfwd" if h > 0 else "upback"
        return "downfwd" if h > 0 else "downback"

    def fwd(self, facing_right):
        return self.right if facing_right else self.left

    def back(self, facing_right):
        return self.left if facing_right else self.right


class InputSource:
    """یک منبع ورودی برای یک بازیکن."""

    def __init__(self, player_index: int, keys: dict = None, joystick=None, touch=None):
        self.index = player_index
        self.keys = keys or (P1_KEYS if player_index == 0 else P2_KEYS)
        self.alt = P2_ALT if player_index == 1 else {}
        self.joystick = joystick
        self.touch = touch
        self.state = InputState()
        self.frame = 0
        self._prev_held = {b: False for b in BUTTONS}
        self._last_dir = "neutral"

    def poll(self, pressed_keys, facing_right: bool, events=None):
        s = self.state
        k = self.keys
        s.up = pressed_keys[k["up"]]
        s.down = pressed_keys[k["down"]]
        s.left = pressed_keys[k["left"]]
        s.right = pressed_keys[k["right"]]
        held = {b: pressed_keys[k[b]] or (b in self.alt and pressed_keys[self.alt[b]]) for b in BUTTONS}

        if self.joystick is not None:
            j = self.joystick
            try:
                ax = j.get_axis(0)
                ay = j.get_axis(1)
                hx, hy = j.get_hat(0) if j.get_numhats() else (0, 0)
                s.left |= ax < -0.5 or hx < 0
                s.right |= ax > 0.5 or hx > 0
                s.up |= ay < -0.5 or hy > 0
                s.down |= ay > 0.5 or hy < 0
                for bi, name in PAD_BUTTONS.items():
                    if bi < j.get_numbuttons() and j.get_button(bi):
                        held[name] = True
            except pygame.error:
                pass

        if self.touch is not None:
            t = self.touch.read()
            s.left |= t["left"]
            s.right |= t["right"]
            s.up |= t["up"]
            s.down |= t["down"]
            for b in BUTTONS:
                held[b] = held[b] or t.get(b, False)

        for b in BUTTONS:
            s.pressed[b] = held[b] and not self._prev_held[b]
            s.released[b] = (not held[b]) and self._prev_held[b]
            s.held[b] = held[b]
            if s.pressed[b]:
                s.press_history.append((self.frame, b))
        self._prev_held = held

        d = s.direction(facing_right)
        if d != self._last_dir:
            s.dir_history.append((self.frame, d))
            self._last_dir = d
        self.frame += 1

    # ---- تشخیص حرکات ویژه ----
    def match_motion(self, motion, button, window=settings.MOTION_WINDOW) -> bool:
        s = self.state
        if not s.pressed.get(button):
            return False
        now = self.frame
        seq = [d for f, d in s.dir_history if now - f <= window]
        # باید motion به ترتیب (نه لزوماً متوالی) در seq ظاهر شده باشد؛ آخرین عنصر اخیر باشد
        i = 0
        for d in seq:
            if i < len(motion) and (d == motion[i] or _dir_equiv(d, motion[i])):
                i += 1
        if i < len(motion):
            return False
        # برای حرکاتی مثل down,down باید neutral بین دو down باشد
        if len(motion) >= 2 and motion[0] == motion[1]:
            cnt = 0
            for d in seq:
                if d == motion[0]:
                    cnt += 1
            return cnt >= 2
        return True

    def double_tap(self, direction: str, facing_right: bool) -> bool:
        s = self.state
        now = self.frame
        taps = [(f, d) for f, d in s.dir_history if now - f <= settings.DOUBLE_TAP_WINDOW * 2]
        seq = [d for f, d in taps]
        # الگوی fwd, neutral, fwd
        for i in range(len(seq) - 2):
            if seq[i] == direction and seq[i + 1] in ("neutral",) and seq[i + 2] == direction:
                if now - taps[i + 2][0] <= 2:
                    return True
        return False

    def clear_history(self):
        self.state.dir_history.clear()
        self.state.press_history.clear()


def _dir_equiv(d, want):
    """downfwd را برای down یا fwd هم قبول کن (تحمل خطای ورودی)."""
    if want == "down":
        return d in ("down", "downfwd", "downback")
    if want == "fwd":
        return d in ("fwd", "downfwd", "upfwd")
    if want == "back":
        return d in ("back", "downback", "upback")
    if want == "downfwd":
        return d in ("downfwd",)
    if want == "downback":
        return d in ("downback",)
    return d == want
