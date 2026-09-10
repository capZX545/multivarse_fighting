"""مسیرهای فایل — سازگار با دسکتاپ، PyInstaller و اندروید."""
import os
import sys

if getattr(sys, "frozen", False):          # PyInstaller
    ROOT = sys._MEIPASS                      # type: ignore[attr-defined]
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "pyfighter", "data")
CHAR_ASSETS = os.path.join(ASSETS, "characters")
STAGE_ASSETS = os.path.join(ASSETS, "stages")
FONT_DIR = os.path.join(ASSETS, "fonts")


def save_dir() -> str:
    """پوشه ذخیره‌سازی (روی اندروید داخل storage اپ)."""
    if "ANDROID_ARGUMENT" in os.environ:
        base = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
    elif sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "MultivarseFighting")
    else:
        base = os.path.join(os.path.expanduser("~"), ".multivarse_fighting")
    os.makedirs(base, exist_ok=True)
    return base
