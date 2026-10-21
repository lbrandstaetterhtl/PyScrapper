import sys
from pathlib import Path

import captcha_ocr

FONTS = r"C:\Users\brand\RustroverProjects\captcha_ocr\fonts"
MODEL = r"C:\Users\brand\RustroverProjects\captcha_ocr\model.safetensors"

if len(sys.argv) < 2:
    raise SystemExit("Aufruf: python testing.py <Captcha-Ordner>")
CAPTCHAS = Path(sys.argv[1])


def solution_from_name(path: Path) -> str | None:
    """'...Captcha-1_vnpsY.png' -> 'vnpsY'; None wenn keine Loesung im Namen."""
    tail = path.stem.rsplit("_", 1)[-1]
    return tail if len(tail) == 5 and tail.isalnum() else None


# 1. Einmal trainieren
if not Path(MODEL).exists():
    acc = captcha_ocr.train(FONTS, MODEL, 10)
    print(f"Training fertig, Genauigkeit auf Trainingsdaten: {acc:.1%}\n")

# 2. Captchas sammeln
files = sorted(CAPTCHAS.glob("*.jp*g")) + sorted(CAPTCHAS.glob("*.png"))
if not files:
    raise SystemExit(f"Keine .jpg/.jpeg/.png in {CAPTCHAS} gefunden - Pfad pruefen")

# 3. Lesen und vergleichen
first_ok = top3_ok = total = 0
for path in files:
    texts = captcha_ocr.img_to_text(str(path), MODEL, 10)
    expected = solution_from_name(path)
    if expected is None:
        print(f"{path.name}: {texts}   (keine Loesung im Dateinamen)")
        continue
    total += 1
    first_ok += texts[0] == expected
    top3_ok += expected in texts
    rank = texts.index(expected) + 1 if expected in texts else "-"
    print(f"{path.name}: {texts}   (richtig: {expected}, Platz {rank})")

if total:
    print(f"\nPlatz 1 richtig: {first_ok}/{total} ({first_ok / total:.0%})"
          f"   Unter den Top 10: {top3_ok}/{total} ({top3_ok / total:.0%})")
else:
    print("\nKein Captcha mit Loesung im Dateinamen gefunden - nichts zu bewerten.")
