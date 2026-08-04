"""
search_endpoint_test.py
-----------------------
Robustheits- und Negativtest fuer den PyScrapper /search-Endpoint.

Liegt in: LocalServer/tests/
Zweck: pruefen, ob die serverseitige Auth UND Input-Validierung halten.

Getestet werden zwei Ebenen:
  1. AUTH   - fehlender / falscher X-Admin-Key -> 401 erwartet
  2. INPUT  - mit gueltigem Key: kaputter/unsinniger Body -> 4xx erwartet

Der ADMIN_KEY wird aus LocalServer/.env geladen und als Header
"X-Admin-Key" mitgeschickt.

HINWEIS: Ein GUELTIGER /search-Request loest eine echte externe Suche aus
(YouTube/Bandcamp/Archive). Die Nonsense-Faelle hier sollen an der
Validierung scheitern, BEVOR echtes Scraping passiert. Kommt ein Fall doch
mit 2xx durch (und dauert lange), hat er echten Traffic erzeugt - das ist
dann selbst ein Hinweis, dass die Validierung zu spaet greift.

Nutzung:
    python search_endpoint_test.py
    python search_endpoint_test.py --base-url http://127.0.0.1:8765
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
# Pfade - skript-relativ (LocalServer/tests/)
# --------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
REPO_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "search_endpoint_test.log"
ENV_FILE = SERVER_DIR / ".env"

HEADER_NAME = "X-Admin-Key"


# --------------------------------------------------------------------------
# ADMIN_KEY aus LocalServer/.env laden
# --------------------------------------------------------------------------
def load_admin_key():
    try:
        from dotenv import dotenv_values
        vals = dotenv_values(ENV_FILE)
        if vals.get("ADMIN_KEY"):
            return vals["ADMIN_KEY"]
    except ImportError:
        pass

    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "ADMIN_KEY":
                return val.strip().strip('"').strip("'")
    return None


def log(msg, to_file=True):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if to_file:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# --------------------------------------------------------------------------
# Gueltiger Basis-Payload fuer die Auth-Tests.
# Bewusst ein Provider mit funktionierender Suche (nicht suno).
# --------------------------------------------------------------------------
VALID_PAYLOAD = {
    "provider": "youtube",
    "query": "test",
    "mediatype": ".mp3",
}


# --------------------------------------------------------------------------
# INPUT-Testfaelle (jeweils MIT gueltigem Key gesendet)
#   (name, payload, expectation)
# Feldnamen (provider/query/mediatype) ggf. an dein SearchRequest-Modell
# anpassen - manche Backends nutzen "search_query" o.ae.
# --------------------------------------------------------------------------
INPUT_CASES = [
    # ---- Voelliger Nonsense ------------------------------------------
    ("leerer Body", {}, "reject"),
    ("voellig falsche Felder", {"foo": "bar", "banana": 42}, "reject"),
    ("null-Werte in Pflichtfeldern",
     {"provider": None, "query": None, "mediatype": None}, "reject"),

    # ---- Ungueltiger Provider ----------------------------------------
    ("unbekannter Provider",
     {"provider": "totallynotaprovider", "query": "test", "mediatype": ".mp3"}, "reject"),
    ("leerer Provider",
     {"provider": "", "query": "test", "mediatype": ".mp3"}, "reject"),

    # ---- Query-spezifisch --------------------------------------------
    ("leere Query",
     {"provider": "youtube", "query": "", "mediatype": ".mp3"}, "reject"),
    ("Query nur Whitespace",
     {"provider": "youtube", "query": "     ", "mediatype": ".mp3"}, "reject"),
    ("extrem lange Query",
     {"provider": "youtube", "query": "A" * 10000, "mediatype": ".mp3"}, "reject"),

    # ---- Ungueltiger Media-Type --------------------------------------
    ("nicht erlaubter Media-Type",
     {"provider": "youtube", "query": "test", "mediatype": ".exe"}, "reject"),
    ("Media-Type fehlt ganz",
     {"provider": "youtube", "query": "test"}, "reject"),

    # ---- Suno-Sonderfall (Suche ist Platzhalter) ---------------------
    # Erwartung offen gelassen als "note": kann je nach Implementierung
    # leeres 2xx oder ein 4xx sein. Wird nur protokolliert, nicht bewertet.
    ("suno-Suche (Platzhalter im Backend)",
     {"provider": "suno", "query": "test", "mediatype": ".mp3"}, "note"),

    # ---- Typfehler ---------------------------------------------------
    ("falscher Typ (Zahl/Liste/Objekt)",
     {"provider": 123, "query": ["a", "b"], "mediatype": {"x": 1}}, "reject"),

    # ---- Injection-artige Query (soll als harmloser String behandelt
    #      werden, nicht crashen) ---------------------------------------
    ("SQL-artige Zeichen in Query",
     {"provider": "youtube", "query": "'; DROP TABLE Users;--", "mediatype": ".mp3"}, "note"),
]


def post(base_url, payload, headers):
    return requests.post(f"{base_url}/search", json=payload,
                         headers=headers, timeout=20)


def evaluate(status, expectation):
    """Gibt (ok: bool|None, note: str). ok=None -> nur protokollieren."""
    if expectation == "unauth":
        if status == 401:
            return True, "OK - 401 wie erwartet (Auth greift)"
        if status == 403:
            return True, "OK - 403 (Auth greift, wenn auch 403 statt 401)"
        return False, (f"PROBLEM - erwartete 401, bekam {status}. "
                       "-> Endpoint ist NICHT durch den Key geschuetzt!")
    if expectation == "reject":
        if 400 <= status < 500:
            return True, "OK - korrekt abgelehnt (4xx wie erwartet)"
        if status >= 500:
            return False, ("PROBLEM - Server-Crash (5xx). Sollte 4xx sein! "
                           "-> Validierung faengt diesen Fall nicht sauber ab.")
        return False, ("PROBLEM - Server hat AKZEPTIERT (2xx), obwohl er "
                       "ablehnen sollte! -> Luecke (evtl. echter Traffic ausgeloest).")
    if expectation == "note":
        return None, f"NOTIZ - Status {status}, nur zur Info (nicht bewertet)"
    # accept
    if 200 <= status < 300:
        return True, "OK - korrekt angenommen (2xx wie erwartet)"
    return False, f"unerwartet - erwartete 2xx, bekam {status}"


def run_case(base_url, name, payload, expectation, headers):
    log("-" * 70)
    log(f"TEST: {name}")
    log(f"  Payload: {json.dumps(payload, ensure_ascii=False)[:200]}")
    log(f"  Header {HEADER_NAME}: {'gesetzt' if HEADER_NAME in headers else 'NICHT gesetzt'}")

    t0 = time.time()
    try:
        resp = post(base_url, payload, headers)
    except requests.exceptions.ConnectionError:
        log(f"  ERGEBNIS: FEHLER - Server nicht erreichbar auf {base_url}.")
        return False
    except requests.exceptions.Timeout:
        log("  ERGEBNIS: TIMEOUT - keine Antwort innerhalb 20s "
            "(evtl. echte Suche ausgeloest).")
        return False
    except Exception as e:
        log(f"  ERGEBNIS: UNERWARTETER FEHLER - {type(e).__name__}: {e}")
        return False

    dt = time.time() - t0
    body_preview = resp.text[:300].replace("\n", " ")
    log(f"  HTTP {resp.status_code}  ({dt:.2f}s)  |  Body: {body_preview}")
    if dt > 3.0 and 200 <= resp.status_code < 300:
        log("  HINWEIS: langsame 2xx-Antwort -> hier lief vermutlich eine "
            "echte externe Suche.")

    ok, note = evaluate(resp.status_code, expectation)
    log(f"  ERGEBNIS: {note}")
    return ok  # kann True/False/None sein


def main():
    parser = argparse.ArgumentParser(description="Auth- und Robustheitstest fuer /search")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765",
                        help="Basis-URL (Default: http://127.0.0.1:8765)")
    args = parser.parse_args()

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"PyScrapper /search Auth+Robustheitstest - {datetime.now()}\n")

    log("=" * 70)
    log(f"Skript:     {Path(__file__).resolve()}")
    log(f"Server-Dir: {SERVER_DIR}")
    log(f"Ziel:       {args.base_url}/search")

    admin_key = load_admin_key()
    if not admin_key:
        log(f"ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)
    masked = admin_key[:3] + "***" + admin_key[-2:] if len(admin_key) > 5 else "***"
    log(f"ADMIN_KEY aus .env geladen (maskiert): {masked}")

    valid_headers = {HEADER_NAME: admin_key}
    passed = failed = noted = 0

    # ---- EBENE 1: AUTH ------------------------------------------------
    log("=" * 70)
    log("EBENE 1 - AUTH (Endpoint muss ohne/mit falschem Key ablehnen)")
    auth_cases = [
        ("kein Key im Header", VALID_PAYLOAD, {}, "unauth"),
        ("falscher Key", VALID_PAYLOAD, {HEADER_NAME: "definitiv-falscher-key"}, "unauth"),
        ("leerer Key", VALID_PAYLOAD, {HEADER_NAME: ""}, "unauth"),
    ]
    for name, payload, hdr, exp in auth_cases:
        ok = run_case(args.base_url, name, payload, exp, hdr)
        if ok is True:
            passed += 1
        elif ok is False:
            failed += 1
        time.sleep(0.2)

    # ---- EBENE 2: INPUT-VALIDIERUNG -----------------------------------
    log("=" * 70)
    log("EBENE 2 - INPUT-VALIDIERUNG (mit gueltigem Key)")
    try:
        h = requests.get(f"{args.base_url}/health",
                         headers=valid_headers, timeout=5)
        log(f"Health-Check: HTTP {h.status_code}")
    except Exception:
        log("WARNUNG: /health nicht erreichbar - laeuft der Server?")

    for name, payload, exp in INPUT_CASES:
        ok = run_case(args.base_url, name, payload, exp, valid_headers)
        if ok is True:
            passed += 1
        elif ok is False:
            failed += 1
        else:  # None -> note
            noted += 1
        time.sleep(0.2)

    total = len(auth_cases) + len(INPUT_CASES)
    log("=" * 70)
    log(f"ZUSAMMENFASSUNG: {passed} wie erwartet, {failed} auffaellig, "
        f"{noted} nur notiert (von {total})")
    if failed:
        log("-> Auffaellige Faelle oben pruefen: echte Luecke oder Sonderfall.")
    log(f"Volles Log: {LOG_FILE}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()