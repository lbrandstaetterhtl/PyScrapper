"""
download_endpoint_test.py
--------------------------
Robustheits- und Negativtest fuer den PyScrapper /download-Endpoint.

Liegt in: LocalServer/tests/
Zweck: pruefen, ob die serverseitige Auth UND Input-Validierung halten.

Getestet werden zwei Ebenen:
  1. AUTH   - fehlender / falscher X-Admin-Key -> 401 erwartet
  2. INPUT  - mit gueltigem Key: kaputter/unsinniger Body -> 4xx erwartet

Der ADMIN_KEY wird aus LocalServer/.env geladen und als Header
"X-Admin-Key" mitgeschickt.

Nutzung (aus beliebigem Verzeichnis, Pfade sind skript-relativ):
    python download_endpoint_test.py
    python download_endpoint_test.py --base-url http://127.0.0.1:8765
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Bitte 'requests' installieren: pip install requests")
    sys.exit(1)


# --------------------------------------------------------------------------
# Pfade - skript-relativ
#   Skript:      LocalServer/tests/download_endpoint_test.py
#   TESTS_DIR:   LocalServer/tests
#   SERVER_DIR:  LocalServer      <- hier liegt die .env
#   REPO_ROOT:   PyScrapper
# --------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
REPO_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "download_endpoint_test.log"
ENV_FILE = SERVER_DIR / ".env"

HEADER_NAME = "X-Admin-Key"


# --------------------------------------------------------------------------
# .env laden: ADMIN_KEY aus LocalServer/.env
# Bevorzugt python-dotenv, faellt auf simplen Eigenparser zurueck.
# --------------------------------------------------------------------------
def load_admin_key():
    # 1) python-dotenv, falls installiert
    try:
        from dotenv import dotenv_values
        vals = dotenv_values(ENV_FILE)
        if vals.get("ADMIN_KEY"):
            return vals["ADMIN_KEY"]
    except ImportError:
        pass

    # 2) simpler Eigenparser
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "ADMIN_KEY":
                # umschliessende Quotes entfernen
                return val.strip().strip('"').strip("'")
    return None


def log(msg, to_file=True):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if to_file:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# --------------------------------------------------------------------------
# Ein gueltiger Basis-Payload (wird fuer die Auth-Tests wiederverwendet)
# --------------------------------------------------------------------------
VALID_PAYLOAD = {
    "provider": "youtube",
    "url": "https://example.com/x",
    "mediatype": ".mp3",
    "filename": "test",
}


# --------------------------------------------------------------------------
# INPUT-Testfaelle (jeweils MIT gueltigem Key gesendet)
#   (name, payload, expectation)
# --------------------------------------------------------------------------
INPUT_CASES = [
    ("leerer Body", {}, "reject"),
    ("voellig falsche Felder", {"foo": "bar", "banana": 42}, "reject"),
    ("null-Werte in Pflichtfeldern",
     {"provider": None, "url": None, "mediatype": None, "filename": None}, "reject"),

    ("unbekannter Provider",
     {"provider": "totallynotaprovider", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("leerer Provider",
     {"provider": "", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "test"}, "reject"),

    ("http statt https",
     {"provider": "youtube", "url": "http://example.com/x",
      "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("gar keine URL, nur Text",
     {"provider": "youtube", "url": "das ist keine url",
      "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("file://-Schema (lokaler Zugriff)",
     {"provider": "youtube", "url": "file:///etc/passwd",
      "mediatype": ".mp3", "filename": "test"}, "reject"),

    ("nicht erlaubter Media-Type",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".exe", "filename": "test"}, "reject"),

    ("Path-Traversal im Dateinamen",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "..\\..\\..\\windows\\system32\\evil"}, "reject"),
    ("Path-Traversal unix-style",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "../../../../etc/cron.d/x"}, "reject"),
    ("absoluter Pfad als Dateiname",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "C:\\Windows\\evil"}, "reject"),
    ("Windows-Reserved-Name (CON)",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "CON"}, "reject"),

    ("extrem langer Dateiname",
     {"provider": "youtube", "url": "https://example.com/x",
      "mediatype": ".mp3", "filename": "A" * 5000}, "reject"),
    ("falscher Typ (Zahl statt String)",
     {"provider": 12345, "url": ["not", "a", "string"],
      "mediatype": True, "filename": {"nested": "object"}}, "reject"),
]


# --------------------------------------------------------------------------
# HTTP-Aufruf
# --------------------------------------------------------------------------
def post(base_url, payload, headers):
    return requests.post(f"{base_url}/download", json=payload,
                         headers=headers, timeout=10)


def evaluate(status, expectation):
    """Gibt (ok: bool, note: str) zurueck."""
    if expectation == "reject":
        if 400 <= status < 500:
            return True, "OK - korrekt abgelehnt (4xx wie erwartet)"
        if status >= 500:
            return False, ("PROBLEM - Server-Crash (5xx). Sollte 4xx sein! "
                           "-> Validierung faengt diesen Fall nicht sauber ab.")
        return False, ("PROBLEM - Server hat AKZEPTIERT (2xx), obwohl er "
                       "ablehnen sollte! -> Luecke.")
    if expectation == "unauth":
        if status == 401:
            return True, "OK - 401 wie erwartet (Auth greift)"
        if status == 403:
            return True, "OK - 403 (Auth greift, wenn auch 403 statt 401)"
        return False, (f"PROBLEM - erwartete 401, bekam {status}. "
                       "-> Endpoint ist NICHT durch den Key geschuetzt!")
    # accept
    if 200 <= status < 300:
        return True, "OK - korrekt angenommen (2xx wie erwartet)"
    return False, f"unerwartet - erwartete 2xx, bekam {status}"


def run_case(base_url, name, payload, expectation, headers):
    log("-" * 70)
    log(f"TEST: {name}")
    log(f"  Payload: {json.dumps(payload, ensure_ascii=False)[:200]}")
    has_key = HEADER_NAME in headers
    log(f"  Header {HEADER_NAME}: {'gesetzt' if has_key else 'NICHT gesetzt'}")

    try:
        resp = post(base_url, payload, headers)
    except requests.exceptions.ConnectionError:
        log(f"  ERGEBNIS: FEHLER - Server nicht erreichbar auf {base_url}.")
        return False
    except requests.exceptions.Timeout:
        log("  ERGEBNIS: TIMEOUT - keine Antwort innerhalb 10s.")
        return False
    except Exception as e:
        log(f"  ERGEBNIS: UNERWARTETER FEHLER - {type(e).__name__}: {e}")
        return False

    body_preview = resp.text[:300].replace("\n", " ")
    log(f"  HTTP {resp.status_code}  |  Body: {body_preview}")
    ok, note = evaluate(resp.status_code, expectation)
    log(f"  ERGEBNIS: {note}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Auth- und Robustheitstest fuer /download")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765",
                        help="Basis-URL (Default: http://127.0.0.1:8765)")
    args = parser.parse_args()

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"PyScrapper /download Auth+Robustheitstest - {datetime.now()}\n")

    log("=" * 70)
    log(f"Skript:     {Path(__file__).resolve()}")
    log(f"Server-Dir: {SERVER_DIR}")
    log(f"Ziel:       {args.base_url}/download")

    admin_key = load_admin_key()
    if not admin_key:
        log(f"ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden. "
            "Ohne Key koennen die Input-Tests nicht sinnvoll laufen "
            "(alles wuerde 401 liefern).")
        sys.exit(2)
    # Key nicht im Klartext loggen - nur bestaetigen und maskieren
    masked = admin_key[:3] + "***" + admin_key[-2:] if len(admin_key) > 5 else "***"
    log(f"ADMIN_KEY aus .env geladen (maskiert): {masked}")

    valid_headers = {HEADER_NAME: admin_key}
    passed = failed = 0

    # ---- EBENE 1: AUTH -------------------------------------------------
    log("=" * 70)
    log("EBENE 1 - AUTH (Endpoint muss ohne/mit falschem Key ablehnen)")
    auth_cases = [
        ("kein Key im Header", VALID_PAYLOAD, {}, "unauth"),
        ("falscher Key", VALID_PAYLOAD, {HEADER_NAME: "definitiv-falscher-key"}, "unauth"),
        ("leerer Key", VALID_PAYLOAD, {HEADER_NAME: ""}, "unauth"),
    ]
    for name, payload, hdr, exp in auth_cases:
        ok = run_case(args.base_url, name, payload, exp, hdr)
        passed += ok
        failed += not ok
        time.sleep(0.2)

    # ---- EBENE 2: INPUT-VALIDIERUNG (mit gueltigem Key) ---------------
    log("=" * 70)
    log("EBENE 2 - INPUT-VALIDIERUNG (mit gueltigem Key)")
    # Health-Check
    try:
        h = requests.get(f"{args.base_url}/health",
                         headers=valid_headers, timeout=5)
        log(f"Health-Check: HTTP {h.status_code}")
    except Exception:
        log("WARNUNG: /health nicht erreichbar - laeuft der Server?")

    for name, payload, exp in INPUT_CASES:
        ok = run_case(args.base_url, name, payload, exp, valid_headers)
        passed += ok
        failed += not ok
        time.sleep(0.2)

    total = len(auth_cases) + len(INPUT_CASES)
    log("=" * 70)
    log(f"ZUSAMMENFASSUNG: {passed} wie erwartet, {failed} auffaellig (von {total})")
    if failed:
        log("-> Auffaellige Faelle oben pruefen: echte Luecke oder Sonderfall.")
    log(f"Volles Log: {LOG_FILE}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()