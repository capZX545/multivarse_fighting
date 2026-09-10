"""
Sasuke Uchiha — Naruto Shippuden (Hebi/Taka outfit)
حرکات طبق منبع:
  • Fire Release: Great Fireball Jutsu (↓↘→ + Punch): پرتابه‌ی گلوله‌ی آتش بزرگ.
  • Chidori (↓↙← + Punch): هجوم برق‌آسا با دست پر از رعد؛ گارد ایستاده را می‌شکند و پرتاب می‌کند.
  • Chidori Senbon / Sharp Spear (→↓↘ + Kick): نیزه‌ی رعد بلندبرد (برد بلند، ضربه‌ی تکی).
  • Kirin (↓↘→ + Special, 200 Meter): صاعقه از آسمان روی حریف؛ غیرقابل‌گارد، تأخیر دارد.
  • Amaterasu (↓↓ + Special, 150 Meter): شعله‌های سیاه روی حریف — سوختن ادامه‌دار.
  • Susanoo (↓↓ + Punch+Kick / Ultimate, 300 Meter): ۱۰ ثانیه زره Susanoo: زره (armor) دائمی، ضربات بزرگ‌تر، آسیب کمتر.
    در حالت Susanoo: Special → Indra's Arrow (تیر عظیم، Ultimate کانونی).
"""
from .base import FighterDef, Move, Hitbox, SpecialInput, basic_moves


def build():
    moves = basic_moves(atk_scale=1.08, reach=1.0)

    moves["fireball"] = Move(
        "Fire Release: Great Fireball", "fireball", 16, 6, 24, 120,
        Hitbox(60, -230, 40, 40), "special", 24, 18, 9.0, meter_gain=12,
        projectile={"kind": "fireball", "speed": 8.5, "life": 75, "radius": 52, "hits": 1, "y": -220,
                    "color": (255, 120, 30), "core": (255, 235, 150)},
    )
    moves["chidori"] = Move(
        "Chidori", "chidori", 12, 16, 24, 170,
        Hitbox(40, -240, 130, 120), "special", 30, 20, 20.0, launch=-12.0, knockdown=True,
        move_forward=12.0, meter_gain=16, armor_frames=10, hits_high=True, tags=["multi_hit_2"],
    )
    moves["chidori_spear"] = Move(
        "Chidori Sharp Spear", "chidori", 14, 8, 26, 110,
        Hitbox(50, -235, 320, 50), "special", 22, 16, 12.0, meter_gain=12,
    )
    moves["kirin"] = Move(
        "Kirin", "chidori", 36, 8, 34, 300,
        Hitbox(140, -700, 220, 700), "ultimate", 40, 26, 8.0, launch=-15.0, knockdown=True,
        meter_cost=200, invuln_frames=10, tags=["unblockable", "fx_kirin"],
    )
    moves["amaterasu"] = Move(
        "Amaterasu", "amaterasu", 24, 6, 30, 90,
        Hitbox(120, -320, 220, 320), "ultimate", 24, 20, 4.0,
        meter_cost=150, invuln_frames=6, tags=["unblockable", "burn_240_2", "fx_amaterasu"],
    )
    moves["susanoo"] = Move(
        "Susanoo", "susanoo", 30, 4, 20, 0,
        Hitbox(0, 0, 0, 0), "ultimate", 0, 0, 0.0,
        meter_cost=300, invuln_frames=40, tags=["transform_susanoo_600", "cinematic"],
    )
    moves["indra_arrow"] = Move(
        "Indra's Arrow", "susanoo", 26, 8, 30, 260,
        Hitbox(60, -260, 40, 40), "ultimate", 40, 30, 20.0, launch=-14.0, knockdown=True,
        meter_cost=100, invuln_frames=8,
        projectile={"kind": "indra_arrow", "speed": 16.0, "life": 70, "radius": 60, "hits": 1, "y": -250,
                    "color": (120, 60, 220), "core": (240, 230, 255), "pierce": True, "unblockable": True},
    )

    specials = [
        SpecialInput(["down", "downfwd", "fwd"], "punch", "fireball"),
        SpecialInput(["down", "downback", "back"], "punch", "chidori"),
        SpecialInput(["fwd", "down", "downfwd"], "kick", "chidori_spear"),
        SpecialInput(["down", "downfwd", "fwd"], "special", "kirin"),
        SpecialInput(["down", "down"], "special", "amaterasu"),
        SpecialInput(["down", "downback", "back"], "special", "susanoo"),
    ]

    return FighterDef(
        slug="sasuke", display_name="Sasuke Uchiha",
        walk_speed=5.2, back_speed=4.0, dash_speed=13.0,
        jump_velocity=-22.5, jump_forward=7.0, weight=0.95,
        health=960, width=64, height=295, crouch_height=175,
        moves=moves, specials=specials, ultimate="susanoo",
        aura_color=(150, 90, 255), passive="sharingan",
        costumes=["Hebi / Taka", "Konoha Genin (Part I)", "The Last (Wandering Cloak)"],
        voice_lines={"intro": "You're annoying.", "win": "Foolish."},
    )
