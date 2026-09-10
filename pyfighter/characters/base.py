"""
ساختار داده‌ی تعریف کاراکتر برای حالت فایتینگ.

هر کاراکتر یک FighterDef دارد: آمار حرکت، لیست حرکات (Move) با فریم‌دیتا و هیت‌باکس،
و ورودی حرکات ویژه. پرتابه‌ها/افکت‌ها با کلاس‌های سیستم مبارزه ساخته می‌شوند.
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class Hitbox:
    """مستطیل نسبت به مبدأ کاراکتر (پاها، وسط). x به سمت جلو مثبت است."""
    x: float
    y: float          # منفی = بالا (از زمین)
    w: float
    h: float


@dataclass
class Move:
    name: str
    anim: str
    startup: int                  # فریم تا فعال شدن
    active: int                   # فریم‌های فعال
    recovery: int                 # فریم‌های ریکاوری
    damage: int
    hitbox: Hitbox
    strength: str = "light"       # light/medium/heavy/special/ultimate
    hitstun: int = 14
    blockstun: int = 10
    knockback: float = 6.0
    launch: float = 0.0           # سرعت عمودی به حریف (منفی = بالا)
    knockdown: bool = False
    hits_low: bool = False        # باید نشسته گارد بگیرد
    hits_high: bool = False       # فقط ایستاده گارد
    cancel_into_special: bool = True
    meter_cost: int = 0
    meter_gain: int = 0
    move_forward: float = 0.0     # جابه‌جایی جلو حین حرکت (px/frame در startup+active)
    airborne_ok: bool = False
    projectile: Optional[dict] = None   # {"kind":..., "speed":..., "life":..., ...}
    on_start: Optional[Callable] = None  # hook برای رفتار سفارشی (مثلاً کلون، تلپورت)
    invuln_frames: int = 0
    armor_frames: int = 0
    self_heal: int = 0
    tags: List[str] = field(default_factory=list)

    @property
    def total(self):
        return self.startup + self.active + self.recovery


@dataclass
class SpecialInput:
    """ورودی حرکت ویژه: توالی جهت‌ها + دکمه."""
    motion: List[str]     # مثلاً ["down","downfwd","fwd"]
    button: str           # "punch" | "kick" | "special"
    move: str             # نام Move


@dataclass
class FighterDef:
    slug: str
    display_name: str
    walk_speed: float
    back_speed: float
    dash_speed: float
    jump_velocity: float
    jump_forward: float
    weight: float                 # ضریب knockback دریافتی
    health: int
    width: int                    # عرض بدن برای push
    height: int
    crouch_height: int
    moves: dict                   # name -> Move
    specials: List[SpecialInput]
    ultimate: str                 # نام Move
    aura_color: tuple = (120, 180, 255)
    passive: Optional[str] = None
    per_frame: Optional[Callable] = None  # hook هر فریم (برای پسیوها)
    costumes: List[str] = field(default_factory=lambda: ["default"])
    voice_lines: dict = field(default_factory=dict)

    def move(self, name):
        return self.moves[name]


# --- سازنده‌های سریع برای ضربات پایه (مشترک همه؛ اعداد با آمار کاراکتر تنظیم می‌شوند) ---
def basic_moves(atk_scale=1.0, reach=1.0):
    r = reach
    return {
        "light_punch": Move("Jab", "light_punch", 3, 3, 7, int(45 * atk_scale), Hitbox(40 * r, -230, 95 * r, 60),
                            "light", 12, 9, 4.5),
        "medium_punch": Move("Straight", "medium_punch", 6, 4, 12, int(75 * atk_scale), Hitbox(45 * r, -225, 120 * r, 70),
                             "medium", 17, 13, 6.5),
        "heavy_punch": Move("Hook > Uppercut", "heavy_punch", 9, 6, 18, int(115 * atk_scale), Hitbox(40 * r, -260, 110 * r, 130),
                            "heavy", 22, 16, 8.0, launch=-14.0),
        "light_kick": Move("Low Kick", "light_kick", 4, 3, 9, int(50 * atk_scale), Hitbox(40 * r, -60, 120 * r, 60),
                           "light", 13, 10, 4.5, hits_low=True),
        "medium_kick": Move("Side Kick", "medium_kick", 7, 5, 14, int(85 * atk_scale), Hitbox(50 * r, -170, 150 * r, 70),
                            "medium", 18, 14, 8.0),
        "heavy_kick": Move("Roundhouse", "heavy_kick", 11, 6, 20, int(125 * atk_scale), Hitbox(50 * r, -250, 150 * r, 90),
                           "heavy", 24, 17, 12.0, knockdown=True),
        "crouch_punch": Move("Crouch Jab", "crouch_punch", 3, 3, 8, int(40 * atk_scale), Hitbox(40 * r, -120, 100 * r, 50),
                             "light", 12, 9, 4.0),
        "jump_kick": Move("Jump Kick", "medium_kick", 5, 8, 6, int(80 * atk_scale), Hitbox(30 * r, -120, 130 * r, 90),
                          "medium", 18, 14, 6.0, hits_high=True, airborne_ok=True),
        "jump_punch": Move("Jump Punch", "light_punch", 4, 8, 5, int(60 * atk_scale), Hitbox(30 * r, -150, 100 * r, 80),
                           "light", 14, 11, 5.0, hits_high=True, airborne_ok=True),
    }
