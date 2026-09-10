"""
Naruto Uzumaki — Naruto Shippuden
حرکات طبق منبع:
  • Shadow Clone Jutsu (↓↙← + Punch): یک کلون احضار می‌شود که به سمت حریف می‌دود و ضربه می‌زند (بعد از ضربه/خوردن، puff می‌شود).
  • Rasengan (↓↘→ + Punch): هجوم جلو با کره‌ی چاکرا؛ چند ضربه‌ای، حریف را پرتاب می‌کند.
  • Uzumaki Barrage (→↓↘ + Kick): کمبوی هوایی «U-zu-ma-ki!» با لگدهای پی‌درپی.
  • Sage Art: Rasenshuriken (↓↘→ + Special, 200 Meter): پرتابه‌ی چرخان بزرگ، بعد از برخورد به کره‌ی برشی منبسط می‌شود (چند ضربه).
  • Kurama Chakra Mode (↓↓ + Special, 300 Meter — Ultimate): ۱۰ ثانیه: سرعت و آسیب بالا، بازسازی سلامتی، ضربات با بازوی چاکرا برد بیشتر؛ Heavy Punch → Tailed Beast Bomb.
"""
from .base import FighterDef, Move, Hitbox, SpecialInput, basic_moves


def build():
    moves = basic_moves(atk_scale=1.0, reach=0.95)

    moves["clone"] = Move(
        "Shadow Clone Jutsu", "clone", 12, 4, 18, 0,
        Hitbox(0, 0, 0, 0), "special", 0, 0, 0.0, meter_gain=8,
        tags=["summon_clone"],
    )
    moves["rasengan"] = Move(
        "Rasengan", "rasengan", 10, 18, 22, 160,
        Hitbox(50, -240, 120, 110), "special", 28, 20, 18.0, launch=-13.0, knockdown=True,
        move_forward=9.0, meter_gain=16, armor_frames=8, tags=["multi_hit_3"],
    )
    moves["barrage"] = Move(
        "Uzumaki Naruto Barrage", "heavy_kick", 8, 20, 18, 140,
        Hitbox(40, -230, 130, 200), "special", 24, 18, 10.0, launch=-17.0, knockdown=True,
        move_forward=6.0, meter_gain=14, tags=["multi_hit_4"],
    )
    moves["rasenshuriken"] = Move(
        "Sage Art: Wind Release Rasenshuriken", "shuriken", 26, 10, 30, 280,
        Hitbox(60, -260, 40, 40), "ultimate", 40, 26, 14.0, launch=-12.0, knockdown=True,
        meter_cost=200, invuln_frames=8,
        projectile={"kind": "rasenshuriken", "speed": 11.0, "life": 80, "radius": 56, "expand_radius": 115,
                    "color": (150, 220, 255), "core": (255, 255, 255), "hits": 4, "y": -240, "pierce": False},
    )
    moves["kurama"] = Move(
        "Kurama Chakra Mode", "kurama", 30, 4, 20, 0,
        Hitbox(0, 0, 0, 0), "ultimate", 0, 0, 0.0,
        meter_cost=300, invuln_frames=40, tags=["transform_kurama_600", "cinematic"],
    )

    moves["bijuu_dama"] = Move(
        "Tailed Beast Bomb", "kurama", 22, 6, 28, 220,
        Hitbox(60, -240, 40, 40), "special", 30, 22, 16.0, launch=-10.0, knockdown=True,
        meter_cost=100,
        projectile={"kind": "bijuu_dama", "speed": 9.0, "life": 90, "radius": 64, "hits": 1, "y": -230,
                    "color": (60, 20, 80), "core": (255, 200, 80)},
    )

    specials = [
        SpecialInput(["down", "downback", "back"], "punch", "clone"),
        SpecialInput(["down", "downfwd", "fwd"], "punch", "rasengan"),
        SpecialInput(["fwd", "down", "downfwd"], "kick", "barrage"),
        SpecialInput(["down", "downfwd", "fwd"], "special", "rasenshuriken"),
        SpecialInput(["down", "down"], "special", "kurama"),
    ]

    return FighterDef(
        slug="naruto", display_name="Naruto Uzumaki",
        walk_speed=5.0, back_speed=3.8, dash_speed=12.0,
        jump_velocity=-22.0, jump_forward=6.5, weight=1.0,
        health=1050, width=66, height=290, crouch_height=175,
        moves=moves, specials=specials, ultimate="kurama",
        aura_color=(255, 170, 40), passive="kurama_regen",
        costumes=["Shippuden", "Sage Mode", "Kurama Chakra Mode"],
        voice_lines={"intro": "Dattebayo!", "win": "I never go back on my word. That's my nindo!"},
    )
