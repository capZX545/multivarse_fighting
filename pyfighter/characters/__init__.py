"""رجیستری تعریف کاراکترهای قابل‌بازی (فایتینگ)."""
import importlib

_REGISTRY = {}
_MODULES = ["gojo", "naruto"]


def get_def(slug: str):
    if slug not in _REGISTRY:
        mod = importlib.import_module(f"pyfighter.characters.{slug}")
        _REGISTRY[slug] = mod.build()
    return _REGISTRY[slug]


def available() -> list:
    return list(_MODULES)
