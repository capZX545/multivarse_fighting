"""ذخیره‌ی پیشرفت بازیکن (طلا، الماس، XP، آنلاک‌ها، ارتقاها)."""
import json
import os
from pyfighter import paths

FILE = os.path.join(paths.save_dir(), "save.json")

DEFAULT = {
    "gold": 300,
    "gems": 5,
    "xp": 0,
    "level": 1,
    "unlocked": ["gojo", "naruto"],
    "costumes": {},          # slug -> [indices]
    "upgrades": {},          # slug -> {"hp":0,"atk":0,"def":0,"spd":0,"tech":0}
    "stats": {"wins": 0, "losses": 0, "dungeon_best_floor": 0, "kills": 0},
    "settings": {"difficulty": "normal", "touch_opacity": 120},
}


def load_state() -> dict:
    st = json.loads(json.dumps(DEFAULT))
    try:
        with open(FILE, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(st.get(k), dict):
                st[k].update(v)
            else:
                st[k] = v
    except (OSError, ValueError):
        pass
    return st


def save_state(st: dict):
    st["level"] = 1 + st.get("xp", 0) // 200
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=1)
    except OSError:
        pass
