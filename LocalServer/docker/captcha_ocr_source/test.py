"""
Captcha-model testen.

Aufruf:
    python test_ocr.py captcha.jpeg
    python test_ocr.py captcha.jpeg --ocr-dir C:\\pfad\\zum\\ocr_dir
    python test_ocr.py captcha.jpeg -n 10

Den Modellordner entweder mit --ocr-dir angeben, in der Umgebungsvariable
OCR_DIR setzen oder unten bei DEFAULT_OCR_DIR eintragen.
"""

import argparse
import os
import sys
import time

import ocr

DEFAULT_OCR_DIR = r"C:\Users\p50232\RustroverProjects\pyscrapper_ocr\model"


def main() -> int:
    parser = argparse.ArgumentParser(description="Captcha-Bild erkennen")
    parser.add_argument("image", help="Pfad zur Bilddatei")
    parser.add_argument("--ocr-dir", default=os.environ.get("OCR_DIR", DEFAULT_OCR_DIR),
                        help="Modellordner (Standard: OCR_DIR oder DEFAULT_OCR_DIR)")
    parser.add_argument("-n", type=int, default=5, help="Anzahl angezeigter Kandidaten (Standard: 5)")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"Datei nicht gefunden: {args.image}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    try:
        candidates = ocr.img_to_text(args.image, args.ocr_dir)
    except ValueError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1
    elapsed = time.perf_counter() - start

    if not candidates:
        print("Keine Kandidaten erhalten", file=sys.stderr)
        return 1

    print(candidates[0])

    if args.n > 1:
        print()
        for i, c in enumerate(candidates[:args.n]):
            print(f"  {i + 1}. {c}")
        print(f"\n{elapsed:.2f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())