"""
Satoru Gojo — Jujutsu Kaisen
Limitless / Six Eyes. حرکات طبق منبع:
  • Infinity (پسیو): وقتی گارد ایستاده گرفته و Meter دارد، پرتابه‌ها قبل از رسیدن متوقف می‌شوند (Meter مصرف می‌شود).
  • Cursed Technique Lapse: Blue  (↓↘→ + Punch): کره‌ی آبی که حریف را به سمت خود می‌کشد و منفجر می‌شود.
  • Cursed Technique Reversal: Red (↓↙← + Punch): انفجار قرمز دافعه، حریف را به عقب پرتاب می‌کند.
  • Hollow Purple (→↓↘ + Special, 200 Meter): پرتابه‌ی بنفش نابودگر، تمام صفحه، گارد را می‌شکند.
  • Domain Expansion: Unlimited Void (↓↓ + Special, 300 Meter — Ultimate): حریف را چند ثانیه فلج می‌کند + آسیب.
"""
from .base import FighterDef, Move, Hitbox, SpecialInput, basic_moves


def build():
    moves = basic_moves(atk_scale=1.05, reach=1.05)

    moves["blue"] = Move(
        "Cursed Technique Lapse: Blue", "blue", 14, 30, 22, 90,
        Hitbox(60, -220, 40, 40), "special", 20, 16, 2.0,
        meter_gain=14,
        projectile={"kind": "blue_orb", "speed": 7.0, "life": 60, "radius": 46, "pull": 3.2,
                    "color": (60, 140, 255), "core": (200, 235, 255), "explode_damage": 70,
                    "hits": 1, "y": -215},
    )
    moves["red"] = Move(
        "Cursed Technique Reversal: Red", "red", 16, 8, 26, 150,
        Hitbox(50, -260, 260, 200), "special", 26, 20, 26.0, launch=-8.0, knockdown=True,
        meter_gain=16, invuln_frames=6,
    )
    moves["purple"] = Move(
        "Hollow Technique: Purple", "purple", 34, 40, 30, 330,
        Hitbox(80, -240, 50, 50), "ultimate", 40, 30, 22.0, launch=-16.0, knockdown=True,
        meter_cost=200,
        projectile={"kind": "purple_beam", "speed": 13.0, "life": 90, "radius": 78, "unblockable": True,
                    "color": (150, 60, 220), "core": (240, 200, 255), "hits": 1, "y": -230, "pierce": True},
        invuln_frames=12,
    )
    moves["domain"] = Move(
        "Domain Expansion: Unlimited Void", "domain", 48, 6, 40, 380,
        Hitbox(-2000, -2000, 4000, 2000), "ultimate", 150, 150, 0.0, knockdown=False,
        meter_cost=300, invuln_frames=54, tags=["domain", "cinematic", "stun_180"],
    )

    specials = [
        SpecialInput(["down", "downfwd", "fwd"], "punch", "blue"),
        SpecialInput(["down", "downback", "back"], "punch", "red"),
        SpecialInput(["fwd", "down", "downfwd"], "special", "purple"),
        SpecialInput(["down", "down"], "special", "domain"),
    ]

    return FighterDef(
        slug="gojo", display_name="Satoru Gojo",
        walk_speed=4.6, back_speed=3.6, dash_speed=11.0,
        jump_velocity=-21.0, jump_forward=6.0, weight=1.0,
        health=1000, width=70, height=300, crouch_height=180,
        moves=moves, specials=specials, ultimate="domain",
        aura_color=(90, 160, 255), passive="infinity",
        costumes=["Jujutsu High Uniform", "Blindfold Off (Shibuya)", "Sunglasses (Hidden Inventory)"],
        voice_lines={"intro": "Nah, I'd win.", "win": "Throughout Heaven and Earth, I alone am the honored one."},
    )
