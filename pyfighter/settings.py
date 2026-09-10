"""
تنظیمات سراسری بازی (Global settings & constants).
همه اعداد جادویی اینجا هستند تا تنظیم بازی آسان باشد.
"""

TITLE = "PyFighter"
VERSION = "0.1.0"

# --- نمایش ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- استیج ---
STAGE_WIDTH = 2000          # عرض کل استیج (بزرگتر از صفحه؛ دوربین حرکت می‌کند)
FLOOR_Y = 620               # مختصات y زمین
WALL_MARGIN = 60            # فاصله دیوارهای نامرئی از لبه استیج
MAX_PLAYER_DISTANCE = 1000  # حداکثر فاصله دو بازیکن (قفل دوربین)

# --- فیزیک ---
GRAVITY = 0.9
MAX_FALL_SPEED = 22

# --- مبارزه ---
ROUND_TIME = 99             # ثانیه
ROUNDS_TO_WIN = 2           # بهترین از ۳
MAX_HEALTH = 1000
MAX_METER = 300             # سه خانه‌ی ۱۰۰ تایی
METER_PER_HIT_DEALT = 18
METER_PER_HIT_TAKEN = 10
METER_PER_BLOCK = 4
METER_PER_SPECIAL = 12
CHIP_DAMAGE_RATIO = 0.12    # آسیب هنگام گارد گرفتن روی ضربه ویژه
PUSHBACK_ON_HIT = 6
PUSHBACK_ON_BLOCK = 9
HITSTOP_LIGHT = 4           # فریم‌های توقف هنگام ضربه
HITSTOP_MEDIUM = 7
HITSTOP_HEAVY = 11
COMBO_DAMAGE_SCALING = [1.0, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
COMBO_MIN_SCALING = 0.25
PRE_ROUND_FREEZE_FRAMES = 150   # "ROUND 1 ... FIGHT!"
KO_SLOWMO_FRAMES = 90
INPUT_BUFFER_FRAMES = 12        # پنجره‌ی ثبت ورودی برای حرکات ویژه
SPECIAL_INPUT_WINDOW = 18       # فریم‌های مجاز برای اجرای ترکیب ویژه (مثلاً ↓↘→)

# --- رنگ‌ها ---
WHITE = (245, 245, 245)
BLACK = (10, 10, 14)
GRAY = (90, 90, 100)
DARK_GRAY = (35, 35, 45)
RED = (220, 50, 50)
GREEN = (60, 200, 90)
YELLOW = (250, 210, 60)
BLUE = (60, 120, 230)
ORANGE = (250, 140, 40)
CYAN = (70, 220, 240)
PURPLE = (170, 80, 230)
HEALTH_GREEN = (80, 220, 100)
HEALTH_RED = (200, 40, 40)
HEALTH_DAMAGE = (240, 200, 60)
METER_BLUE = (70, 160, 255)
METER_FULL = (255, 230, 90)

# --- دیباگ ---
DEBUG_HITBOXES = False
