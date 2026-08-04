"""
crud_endpoint_test.py
---------------------
Auth- und Robustheitstest fuer die create/delete-Endpoints des
PyScrapper-Backends.

Liegt in: LocalServer/tests/

Abgedeckte Endpoints (exakt nach server.py):
  POST /create/user/            (Body: CreateUserRequest)
  POST /delete/user/{id}
  POST /create/playlist/        (Body: CreatePlaylistRequest)
  POST /delete/playlist/{id}
  POST /create/downloadedmedia  (Body: CreateDownloadedMediaRequest)
  POST /delete/downloadedmedia/{id}
  POST /create/settings/        (Body: CreateSettingsRequest)
  POST /delete/settings/{id}
  POST /create/playlistmedia    (Body: CreatePlaylistMediaRequest)
  POST /delete/playlistmedia    (Body: DeletePlaylistMediaRequest)

Zwei Ebenen:
  1. AUTH  - fehlender / falscher X-Admin-Key -> 401 erwartet
  2. INPUT - mit gueltigem Key: kaputte Bodies -> 4xx erwartet

ADMIN_KEY wird aus LocalServer/.env geladen, Header "X-Admin-Key".

WICHTIG: Dieser Test schickt bewusst NUR kaputte/unsinnige Daten. Er legt
KEINE echten, gueltigen Datensaetze an und loescht keine echten. Die
"accept"-Faelle sind absichtlich weggelassen, damit der Test deine DB nicht
veraendert. (Ein reiner Negativ-/Auth-Test.)

Nutzung:
    python crud_endpoint_test.py
    python crud_endpoint_test.py --base-url http://127.0.0.1:8765
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


TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
LOG_FILE = TESTS_DIR / "crud_endpoint_test.log"
ENV_FILE = SERVER_DIR / ".env"

HEADER_NAME = "X-Admin-Key"

# Eine Identifier-Form, die garantiert nicht existiert (fuer Delete-Tests)
NONEXISTENT_ID = "00000000-dead-beef-0000-000000000000"


# --------------------------------------------------------------------------
# ADMIN_KEY laden
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
            k, _, v = line.partition("=")
            if k.strip() == "ADMIN_KEY":
                return v.strip().strip('"').strip("'")
    return None


def log(msg, to_file=True):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    if to_file:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


# --------------------------------------------------------------------------
# Endpoint-Definitionen. method_path baut die volle URL.
# 'style' sagt, wie der kaputte Input reinkommt:
#   "body"      -> JSON-Body (create-Endpoints + playlistmedia)
#   "path_id"   -> Identifier im Pfad (delete user/playlist/media/settings)
# --------------------------------------------------------------------------

# Gueltige Beispiel-Bodies je create-Endpoint (Feldnamen exakt aus den
# Request-Modellen). Werden fuer die AUTH-Tests als "sonst valider" Body
# genutzt - die Datensaetze werden aber nie wirklich angelegt, weil ohne/mit
# falschem Key vorher 401 kommt.
VALID_BODIES = {
    "/create/user/": {
        "username": "authtest_dummy", "password": "x"},
    "/create/playlist/": {
        "user_identifier": NONEXISTENT_ID, "name": "authtest", "description": "x"},
    "/create/downloadedmedia": {
        "user_identifier": NONEXISTENT_ID, "url": "https://example.com/x",
        "mediatype": ".mp3", "downloaded_at": "2026-01-01T00:00:00",
        "download_path": "x", "is_playable": True, "title": "authtest"},
    "/create/settings/": {
        "user_identifier": NONEXISTENT_ID, "default_download_path": "x",
        "dark_mode_enabled": True, "scan_folder_on_startup": False},
    "/create/playlistmedia": {
        "playlist_identifier": NONEXISTENT_ID, "media_identifier": NONEXISTENT_ID},
    "/delete/playlistmedia": {
        "playlist_identifier": NONEXISTENT_ID, "media_identifier": NONEXISTENT_ID},
}


# create-Endpoints mit Body: hier testen wir kaputte Bodies
CREATE_BODY_ENDPOINTS = [
    "/create/user/",
    "/create/playlist/",
    "/create/downloadedmedia",
    "/create/settings/",
    "/create/playlistmedia",
]

# delete-Endpoints mit ID im Pfad
DELETE_PATH_ENDPOINTS = [
    "/delete/user/",
    "/delete/playlist/",
    "/delete/downloadedmedia/",
    "/delete/settings/",
]

# delete mit Body
DELETE_BODY_ENDPOINTS = [
    "/delete/playlistmedia",
]


# Kaputte Bodies, die JEDER create-/body-Endpoint ablehnen sollte
BAD_BODIES = [
    ("leerer Body", {}),
    ("falsche Felder", {"foo": "bar", "banana": 42}),
    ("null in Feldern", {"username": None, "user_identifier": None,
                         "name": None, "url": None, "playlist_identifier": None,
                         "media_identifier": None}),
    ("falsche Typen", {"username": 123, "user_identifier": ["a"],
                       "name": {"x": 1}, "is_playable": "nope",
                       "playlist_identifier": 999, "media_identifier": True}),
    ("riesige Strings", {"username": "A" * 10000, "name": "A" * 10000,
                         "user_identifier": "A" * 10000,
                         "playlist_identifier": "A" * 10000,
                         "media_identifier": "A" * 10000}),
]


def evaluate(status, expectation):
    if expectation == "unauth":
        if status in (401, 403):
            return True, f"OK - {status} (Auth greift)"
        return False, (f"PROBLEM - erwartete 401, bekam {status}. "
                       "-> Endpoint NICHT durch Key geschuetzt!")
    if expectation == "reject":
        if 400 <= status < 500:
            return True, "OK - korrekt abgelehnt (4xx)"
        if status >= 500:
            return False, ("PROBLEM - 5xx Crash statt sauberem 4xx. "
                           "-> unbehandelter Fehler in der Validierung.")
        return False, ("PROBLEM - 2xx akzeptiert, obwohl ablehnen erwartet. "
                       "-> Luecke.")
    if expectation == "note":
        return None, f"NOTIZ - Status {status} (nur zur Info)"
    return None, f"Status {status}"


def call(base_url, endpoint, headers, body=None, path_suffix=""):
    url = f"{base_url}{endpoint}{path_suffix}"
    return requests.post(url, json=body, headers=headers, timeout=10), url


def run(base_url, name, endpoint, headers, expectation,
        body=None, path_suffix=""):
    log("-" * 70)
    log(f"TEST: {name}")
    full = f"{endpoint}{path_suffix}"
    log(f"  POST {full}")
    if body is not None:
        log(f"  Body: {json.dumps(body, ensure_ascii=False)[:180]}")
    log(f"  Header {HEADER_NAME}: {'gesetzt' if HEADER_NAME in headers else 'NICHT gesetzt'}")

    try:
        resp, _ = call(base_url, endpoint, headers, body, path_suffix)
    except requests.exceptions.ConnectionError:
        log(f"  ERGEBNIS: FEHLER - Server nicht erreichbar auf {base_url}.")
        return False
    except requests.exceptions.Timeout:
        log("  ERGEBNIS: TIMEOUT (>10s).")
        return False
    except Exception as e:
        log(f"  ERGEBNIS: UNERWARTETER FEHLER - {type(e).__name__}: {e}")
        return False

    body_preview = resp.text[:250].replace("\n", " ")
    log(f"  HTTP {resp.status_code}  |  Body: {body_preview}")
    ok, note = evaluate(resp.status_code, expectation)
    log(f"  ERGEBNIS: {note}")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Auth-/Robustheitstest fuer create+delete")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    args = parser.parse_args()

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"PyScrapper create/delete Auth+Robustheitstest - {datetime.now()}\n")

    log("=" * 70)
    log(f"Skript: {Path(__file__).resolve()}")
    log(f"Ziel:   {args.base_url}")

    admin_key = load_admin_key()
    if not admin_key:
        log(f"ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)
    masked = admin_key[:3] + "***" + admin_key[-2:] if len(admin_key) > 5 else "***"
    log(f"ADMIN_KEY geladen (maskiert): {masked}")

    valid = {HEADER_NAME: admin_key}
    passed = failed = noted = 0

    def tally(ok):
        nonlocal passed, failed, noted
        if ok is True:
            passed += 1
        elif ok is False:
            failed += 1
        else:
            noted += 1

    # ================================================================
    # EBENE 1 - AUTH: jeder Endpoint muss ohne/mit falschem Key ablehnen
    # ================================================================
    log("=" * 70)
    log("EBENE 1 - AUTH (kein Key / falscher Key -> 401 erwartet)")

    bad_key = {HEADER_NAME: "definitiv-falscher-key"}

    # create-body-Endpoints
    for ep in CREATE_BODY_ENDPOINTS:
        b = VALID_BODIES.get(ep, {})
        tally(run(args.base_url, f"{ep} ohne Key", ep, {}, "unauth", body=b))
        time.sleep(0.15)
        tally(run(args.base_url, f"{ep} falscher Key", ep, bad_key, "unauth", body=b))
        time.sleep(0.15)

    # delete-path-Endpoints
    for ep in DELETE_PATH_ENDPOINTS:
        tally(run(args.base_url, f"{ep}{{id}} ohne Key", ep, {}, "unauth",
                  path_suffix=NONEXISTENT_ID))
        time.sleep(0.15)
        tally(run(args.base_url, f"{ep}{{id}} falscher Key", ep, bad_key, "unauth",
                  path_suffix=NONEXISTENT_ID))
        time.sleep(0.15)

    # delete-body-Endpoints
    for ep in DELETE_BODY_ENDPOINTS:
        b = VALID_BODIES.get(ep, {})
        tally(run(args.base_url, f"{ep} ohne Key", ep, {}, "unauth", body=b))
        time.sleep(0.15)
        tally(run(args.base_url, f"{ep} falscher Key", ep, bad_key, "unauth", body=b))
        time.sleep(0.15)

    # ================================================================
    # EBENE 2 - INPUT: mit gueltigem Key kaputte Bodies -> 4xx
    # ================================================================
    log("=" * 70)
    log("EBENE 2 - INPUT-VALIDIERUNG (gueltiger Key, kaputte Bodies)")

    try:
        h = requests.get(f"{args.base_url}/health", headers=valid, timeout=5)
        log(f"Health-Check: HTTP {h.status_code}")
    except Exception:
        log("WARNUNG: /health nicht erreichbar - laeuft der Server?")

    # create-body-Endpoints: alle BAD_BODIES durchspielen
    for ep in CREATE_BODY_ENDPOINTS:
        log("#" * 50)
        log(f"# Endpoint: {ep}")
        for bad_name, bad_body in BAD_BODIES:
            tally(run(args.base_url, f"{ep} | {bad_name}", ep, valid, "reject",
                      body=bad_body))
            time.sleep(0.15)

    # delete-body-Endpoint (playlistmedia): kaputte Bodies
    for ep in DELETE_BODY_ENDPOINTS:
        log("#" * 50)
        log(f"# Endpoint: {ep}")
        for bad_name, bad_body in BAD_BODIES:
            tally(run(args.base_url, f"{ep} | {bad_name}", ep, valid, "reject",
                      body=bad_body))
            time.sleep(0.15)

    # delete-path-Endpoints: Loeschen einer nicht-existenten ID.
    # ACHTUNG: Deine Handler geben hier vermutlich 200 zurueck (SQLite
    # loescht 0 Zeilen ohne Fehler). Das ist KEIN Bug, nur Verhalten ->
    # daher als "note", nicht als "reject" bewertet.
    log("#" * 50)
    log("# delete/{id} mit nicht-existenter ID (Verhalten, nicht Fehler)")
    for ep in DELETE_PATH_ENDPOINTS:
        tally(run(args.base_url, f"{ep}{{nonexistent}}", ep, valid, "note",
                  path_suffix=NONEXISTENT_ID))
        time.sleep(0.15)

    total = passed + failed + noted
    log("=" * 70)
    log(f"ZUSAMMENFASSUNG: {passed} wie erwartet, {failed} auffaellig, "
        f"{noted} nur notiert (gesamt {total})")
    if failed:
        log("-> Auffaellige Faelle oben pruefen.")
    log(f"Volles Log: {LOG_FILE}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()