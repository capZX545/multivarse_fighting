"""دسترسی به دیتابیس ۶۴۰ کاراکتر + تعیین این‌که کدام‌ها گرافیک/موست کامل دارند."""
import json
import os
import re

from pyfighter import paths

_DB = None
_BY_SLUG = {}


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


# نگاشت دستی نام -> پوشه اسپرایت (اگر با slug خودکار فرق دارد)
SLUG_OVERRIDES = {
    "satoru_gojo": "gojo",
    "naruto_uzumaki": "naruto",
    "sasuke_uchiha": "sasuke",
}


def load():
    global _DB
    if _DB is None:
        with open(os.path.join(paths.DATA, "characters.json"), encoding="utf-8") as f:
            _DB = json.load(f)
        for c in _DB:
            s = slugify(c["name"])
            c["slug"] = SLUG_OVERRIDES.get(s, s)
            c["asset_dir"] = os.path.join(paths.CHAR_ASSETS, c["slug"])
            c["playable"] = os.path.isfile(os.path.join(c["asset_dir"], "idle_0.png"))
            _BY_SLUG[c["slug"]] = c
    return _DB


def get(slug: str) -> dict:
    load()
    return _BY_SLUG[slug]


def playable() -> list:
    return [c for c in load() if c["playable"]]


def all_sorted() -> list:
    """قابل‌بازی‌ها اول، سپس بقیه بر اساس سطح آنلاک."""
    return sorted(load(), key=lambda c: (not c["playable"], c["unlock_level"], c["id"]))
