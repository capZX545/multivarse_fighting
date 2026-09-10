"""تنظیمات سراسری بازی."""
import os
import sys

TITLE = "Multivarse Fighting"
VERSION = "0.1.0"

# --- نمایش (رزولوشن منطقی؛ روی هر صفحه‌ای مقیاس می‌شود) ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- پلتفرم ---
IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_BOOTLOGO" in os.environ or hasattr(sys, "getandroidapilevel")

# --- استیج ---
STAGE_WIDTH = 1900
FLOOR_Y = 640
WALL_MARGIN = 40
MAX_PLAYER_DISTANCE = 1050

# --- فیزیک ---
GRAVITY = 1.0
MAX_FALL_SPEED = 24

# --- مبارزه ---
ROUND_TIME = 99
ROUNDS_TO_WIN = 2
MAX_HEALTH = 1000
MAX_METER = 300
METER_PER_HIT_DEALT = 16
METER_PER_HIT_TAKEN = 9
METER_PER_BLOCK = 4
CHIP_DAMAGE_RATIO = 0.12
PUSHBACK_ON_HIT = 7
PUSHBACK_ON_BLOCK = 10
HITSTOP = {"light": 4, "medium": 7, "heavy": 11, "special": 9, "ultimate": 14}
COMBO_SCALING = [1.0, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
COMBO_MIN_SCALING = 0.25
PRE_ROUND_FRAMES = 140
KO_SLOWMO_FRAMES = 80
INPUT_BUFFER_FRAMES = 10
MOTION_WINDOW = 20      # فریم‌های مجاز برای وارد کردن حرکات (مثل ↓↘→)
DOUBLE_TAP_WINDOW = 12  # دَش با دوبار زدن جهت

# --- ارتفاع رندر کاراکتر (پیکسل) ---
CHAR_HEIGHT = 330

# --- رنگ‌ها ---
WHITE = (245, 245, 245)
BLACK = (10, 10, 14)
GRAY = (90, 90, 100)
DARK = (22, 22, 30)
RED = (220, 50, 50)
GREEN = (60, 200, 90)
YELLOW = (250, 210, 60)
BLUE = (60, 120, 230)
ORANGE = (250, 140, 40)
CYAN = (70, 220, 240)
PURPLE = (170, 80, 230)
HEALTH_GREEN = (90, 225, 110)
HEALTH_DAMAGE = (240, 200, 60)
METER_BLUE = (70, 160, 255)
METER_FULL = (255, 230, 90)

DEBUG_HITBOXES = False
