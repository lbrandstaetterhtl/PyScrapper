"""Auth- und Robustheitstest fuer die create/delete-Endpunkte.

Beispiele:
    python create_delete_tests.py quick
    python create_delete_tests.py normal
    python create_delete_tests.py intense --base-url http://127.0.0.1:8765

Abgedeckte Endpunkte (Pfade und Modelle exakt nach server.py):
    POST /create/user/               CreateUserRequest
    POST /delete/user/{id}
    POST /create/playlist/           CreatePlaylistRequest
    POST /delete/playlist/{id}
    POST /create/downloadedmedia     CreateDownloadedMediaRequest
    POST /delete/downloadedmedia/{id}
    POST /create/settings/           CreateSettingsRequest
    POST /delete/settings/{id}
    POST /create/playlistmedia       CreatePlaylistMediaRequest
    POST /delete/playlistmedia       DeletePlaylistMediaRequest

Der Test schickt ausschliesslich ungueltige Daten und loescht nur Identifier,
die es nicht gibt. Er legt nichts an und veraendert den Bestand nicht.

Zum Loeschverhalten: SQLite loescht null Zeilen ohne Fehler, der Server
antwortet daher auch bei unbekanntem Identifier mit 200. Das ist Verhalten,
kein Fehler, und wird als NOTE gefuehrt statt als Ablehnung erwartet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_common import (Case, Reporter, add_common_arguments, check_server,
                         enable_colors, load_env_value, mask_secret,
                         run_suite, select_cases, selected_mode)

TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
PROJECT_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "crud_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
NONEXISTENT_ID = "00000000-dead-beef-0000-000000000000"

TIMEOUT = {"quick": 10, "normal": 12, "intense": 20}
PAUSE = {"quick": 0.0, "normal": 0.06, "intense": 0.1}

# Strukturell gueltige Bodies. Nur fuer die Auth-Ebene - dort greift die Auth
# vor jeder Verarbeitung, es entsteht also kein Datensatz.
# Achtung: CreateDownloadedMediaRequest heisst media_type, nicht mediatype.
VALID_BODIES = {
    "/create/user/": {"username": "pyscrapper_authtest", "password": "x"},
    "/create/playlist/": {"user_identifier": NONEXISTENT_ID,
                          "name": "authtest", "description": "x"},
    "/create/downloadedmedia": {"user_identifier": NONEXISTENT_ID,
                                "download_path": "x",
                                "downloaded_at": "2026-01-01T00:00:00",
                                "is_playable": True,
                                "url": "https://example.com/x",
                                "media_type": "audio", "title": "authtest"},
    "/create/settings/": {"user_identifier": NONEXISTENT_ID,
                          "default_download_path": "x",
                          "dark_mode_enabled": True,
                          "scan_folder_on_startup": False},
    "/create/playlistmedia": {"playlist_identifier": NONEXISTENT_ID,
                              "media_identifier": NONEXISTENT_ID},
    "/delete/playlistmedia": {"playlist_identifier": NONEXISTENT_ID,
                              "media_identifier": NONEXISTENT_ID},
}

CREATE_BODY_ENDPOINTS = ["/create/user/", "/create/playlist/",
                         "/create/downloadedmedia", "/create/settings/",
                         "/create/playlistmedia"]
DELETE_PATH_ENDPOINTS = ["/delete/user/", "/delete/playlist/",
                         "/delete/downloadedmedia/", "/delete/settings/"]
DELETE_BODY_ENDPOINTS = ["/delete/playlistmedia"]

# (Name, Body, Stufe, Zweck)
BAD_BODIES = [
    ("leerer Body", {}, "quick", "alle Pflichtfelder fehlen"),
    ("falsche Typen",
     {"username": 123, "password": [], "user_identifier": ["a"], "name": {"x": 1},
      "is_playable": "nope", "playlist_identifier": 999, "media_identifier": True,
      "dark_mode_enabled": "vielleicht", "media_type": 7, "title": []},
     "quick", "Pydantic-Typpruefung je Feld"),
    ("falsche Felder", {"foo": "bar", "banana": 42}, "normal",
     "keines der erwarteten Felder vorhanden"),
    ("null in Feldern",
     {"username": None, "password": None, "user_identifier": None, "name": None,
      "url": None, "playlist_identifier": None, "media_identifier": None,
      "default_download_path": None, "media_type": None, "title": None},
     "normal", "None ist fuer Pflichtfelder nicht zulaessig"),
    ("riesige Strings",
     {key: "A" * 10000 for key in
      ("username", "password", "name", "description", "user_identifier",
       "playlist_identifier", "media_identifier", "title", "url",
       "download_path", "default_download_path", "media_type")},
     "normal", "Laengenbegrenzung der Textfelder"),
    ("Body ist eine Liste", [1, 2, 3], "normal", "Body muss ein Objekt sein"),
    ("leere Strings",
     {"username": "", "password": "", "user_identifier": "", "name": "",
      "url": "", "playlist_identifier": "", "media_identifier": "",
      "default_download_path": "", "media_type": "", "title": ""},
     "intense", "leere Pflichtfelder"),
    ("Whitespace-Strings",
     {"username": "   ", "password": "   ", "user_identifier": "   ",
      "name": "   ", "url": "   ", "playlist_identifier": "   ",
      "media_identifier": "   ", "media_type": "   ", "title": "   "},
     "intense", "Whitespace als Inhalt"),
    ("verschachtelte Objekte",
     {"username": {"x": 1}, "password": {"x": 1}, "user_identifier": {"x": 1},
      "playlist_identifier": {"x": 1}, "media_identifier": {"x": 1}},
     "intense", "Objekte statt Strings"),
    ("Unicode und Steuerzeichen",
     {"username": "a\u0000b", "name": "zeile1\r\nzeile2", "title": "musik",
      "user_identifier": "taest"},
     "intense", "Nullbyte und Zeilenumbrueche in Textfeldern"),
    ("SQL-artige Werte",
     {"username": "'; DROP TABLE Users;--", "user_identifier": "1 OR 1=1",
      "name": '" OR ""="', "title": "admin'--"},
     "intense", "Parameterbindung muss das neutralisieren"),
]

# (Name, Pfadsuffix, Stufe, Zweck) - alle als NOTE, siehe Modulkommentar
BAD_IDS = [
    ("nicht existierende ID", NONEXISTENT_ID, "quick",
     "SQLite loescht 0 Zeilen ohne Fehler"),
    ("ID ohne UUID-Form", "not-a-valid-id", "normal",
     "Identifier sind freie Strings, keine UUIDs"),
    ("Path-Traversal in der ID", "..%2F..%2Fetc%2Fpasswd", "normal",
     "Segment wird als Identifier behandelt, nicht als Pfad"),
    ("SQL-artige ID", "1'%20OR%20'1'%3D'1", "normal",
     "Parameterbindung muss greifen"),
    ("sehr lange ID", "A" * 2048, "intense", "Laenge des Pfadsegments"),
]


def build_cases(admin_key: str) -> list[Case]:
    bad_key = {HEADER_NAME: "definitiv-falscher-key"}
    cases: list[Case] = []

    # ---------------------------------------------------------- AUTH
    for endpoint in CREATE_BODY_ENDPOINTS + DELETE_BODY_ENDPOINTS:
        body = VALID_BODIES[endpoint]
        cases.append(Case(f"{endpoint} ohne Key", "unauth", "AUTH · Body-Endpunkte",
                          body, endpoint, {}, "quick",
                          checks="Endpunkt haengt an require_admin"))
        cases.append(Case(f"{endpoint} falscher Key", "unauth", "AUTH · Body-Endpunkte",
                          body, endpoint, bad_key, "normal",
                          checks="fremder Key darf nicht durchkommen"))

    for endpoint in DELETE_PATH_ENDPOINTS:
        path = endpoint + NONEXISTENT_ID
        cases.append(Case(f"{endpoint}{{id}} ohne Key", "unauth",
                          "AUTH · Delete-Endpunkte", None, path, {}, "quick",
                          checks="Loeschen ohne Key muss scheitern"))
        cases.append(Case(f"{endpoint}{{id}} falscher Key", "unauth",
                          "AUTH · Delete-Endpunkte", None, path, bad_key, "normal",
                          checks="fremder Key darf nicht loeschen"))

    # ------------------------------------------------ INPUT je Endpunkt
    for endpoint in CREATE_BODY_ENDPOINTS + DELETE_BODY_ENDPOINTS:
        section = "INPUT · " + endpoint
        for name, body, level, checks in BAD_BODIES:
            cases.append(Case(name, "reject", section, body, endpoint,
                              level=level, checks=checks))

    # ---------------------------------------------------- Delete-IDs
    for endpoint in DELETE_PATH_ENDPOINTS:
        section = "VERHALTEN · " + endpoint + "{id}"
        for name, suffix, level, checks in BAD_IDS:
            cases.append(Case(name, "note", section, None, endpoint + suffix,
                              level=level, checks=checks))

    return cases


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auth- und Robustheitstest fuer create/delete")
    add_common_arguments(parser)
    args = parser.parse_args()
    enable_colors(args.no_color)

    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")

    reporter = Reporter("PyScrapper · CRUD-Endpunkte", mode, base_url,
                        LOG_FILE, verbose=args.verbose)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.banner(base_url, Path(__file__), ENV_FILE)
        reporter.out(f"\n ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)

    all_cases = build_cases(admin_key)
    cases = select_cases(all_cases, mode, args)
    reporter.banner(f"{base_url}  (10 Endpunkte)", Path(__file__), ENV_FILE,
                    planned=len(cases), total=len(all_cases),
                    extra={"Admin-Key": mask_secret(admin_key),
                           "Datenbank": "wird nicht veraendert - nur ungueltige Daten"})
    check_server(reporter, base_url, {HEADER_NAME: admin_key})

    if not cases:
        reporter.out("\n Kein Fall passt zu Modus und Filter.")
        sys.exit(2)

    run_suite(reporter, base_url, cases, "/", {HEADER_NAME: admin_key},
              args, TIMEOUT[mode], PAUSE[mode])
    sys.exit(reporter.summary())


if __name__ == "__main__":
    main()
