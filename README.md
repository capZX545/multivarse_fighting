# Multivarse Fighting

بازی دو حالته با پایتون / Pygame-CE — دسکتاپ و اندروید.

- **Versus** — مبارزه رو در رو (سبک MK / Street Fighter) با AI تطبیق‌پذیر
- **Dungeon** — روگ‌لایک از بالا (سبک Soul Knight) — در حال ساخت

## اجرا (دسکتاپ)
```bash
pip install -r requirements.txt
python main.py
```

## کنترل‌ها
| | P1 | P2 |
|---|---|---|
| حرکت | W A S D | جهت‌ها |
| مشت | J | Num1 یا , |
| لگد | K | Num2 یا . |
| ویژه | L | Num3 یا / |
| گارد | U | Num4 یا M |
| دَش | I | Num5 یا N |
| ضربه سنگین | گارد + مشت/لگد | |

`ESC` توقف — `F11` تمام‌صفحه — `F1` نمایش هیت‌باکس — `TAB` در صفحه انتخاب: سختی CPU

گیم‌پد و کنترل لمسی (اندروید) پشتیبانی می‌شود.

## حرکات ویژه
**Gojo:** Blue `↓↘→+P` · Red `↓↙←+P` · Hollow Purple `→↓↘+S` (200) · Unlimited Void `↓↓+S` (300) · Infinity: گارد + Meter پرتابه‌ها را متوقف می‌کند
**Naruto:** Shadow Clone `↓↙←+P` · Rasengan `↓↘→+P` · Uzumaki Barrage `→↓↘+K` · Rasenshuriken `↓↘→+S` (200) · Kurama Mode `↓↓+S` (300)

## ساخت
- دسکتاپ: `pyinstaller multivarse.spec`
- اندروید: `buildozer android debug`
- GitHub Actions با هر تگ `v*` هر سه نسخه را می‌سازد و Release می‌کند.

## ساختار
```
pyfighter/
  characters/   تعریف کاراکترها (حرکات، فریم‌دیتا، ویژه‌ها)
  entities/     Fighter, Projectile, Clone
  systems/      input, touch, adaptive_ai, audio, save
  scenes/       menu, select, fight, shop, ...
  gfx/          sprites, stage, effects
  ui/           hud, fonts, widgets
  data/         characters.json (640 کاراکتر)
assets/characters/<slug>/   اسپرایت‌ها
tools/          پایپ‌لاین اسپرایت و ساخت دیتابیس
```
