"""Auth- und Robustheitstests fuer create/delete-Endpunkte.

Beispiele:
    python create_delete_tests.py quick
    python create_delete_tests.py normal
    python create_delete_tests.py intense --base-url http://127.0.0.1:8765
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
from test_common import Reporter, TestOutcome, add_common_arguments, load_env_value, mask_secret, perform_request, selected_mode

TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
PROJECT_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "crud_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
NONEXISTENT_ID = "00000000-dead-beef-0000-000000000000"

VALID_BODIES = {
    "/create/user/": {"username": "authtest_dummy", "password": "x"},
    "/create/playlist/": {"user_identifier": NONEXISTENT_ID, "name": "authtest", "description": "x"},
    "/create/downloadedmedia": {"user_identifier": NONEXISTENT_ID, "url": "https://example.com/x", "mediatype": ".mp3", "downloaded_at": "2026-01-01T00:00:00", "download_path": "x", "is_playable": True, "title": "authtest"},
    "/create/settings/": {"user_identifier": NONEXISTENT_ID, "default_download_path": "x", "dark_mode_enabled": True, "scan_folder_on_startup": False},
    "/create/playlistmedia": {"playlist_identifier": NONEXISTENT_ID, "media_identifier": NONEXISTENT_ID},
    "/delete/playlistmedia": {"playlist_identifier": NONEXISTENT_ID, "media_identifier": NONEXISTENT_ID},
}
CREATE_BODY_ENDPOINTS = ["/create/user/", "/create/playlist/", "/create/downloadedmedia", "/create/settings/", "/create/playlistmedia"]
DELETE_PATH_ENDPOINTS = ["/delete/user/", "/delete/playlist/", "/delete/downloadedmedia/", "/delete/settings/"]
DELETE_BODY_ENDPOINTS = ["/delete/playlistmedia"]

QUICK_BAD_BODIES = [
    ("leerer Body", {}),
    ("falsche Typen", {"username": 123, "user_identifier": ["a"], "name": {"x": 1}, "is_playable": "nope", "playlist_identifier": 999, "media_identifier": True}),
]
NORMAL_BAD_BODIES = QUICK_BAD_BODIES + [
    ("falsche Felder", {"foo": "bar", "banana": 42}),
    ("null in Feldern", {"username": None, "user_identifier": None, "name": None, "url": None, "playlist_identifier": None, "media_identifier": None}),
    ("riesige Strings", {"username": "A" * 10000, "name": "A" * 10000, "user_identifier": "A" * 10000, "playlist_identifier": "A" * 10000, "media_identifier": "A" * 10000}),
]
INTENSE_BAD_BODIES = NORMAL_BAD_BODIES + [
    ("leere Strings", {"username": "", "password": "", "user_identifier": "", "name": "", "url": "", "playlist_identifier": "", "media_identifier": ""}),
    ("Whitespace Strings", {"username": "   ", "password": "   ", "user_identifier": "   ", "name": "   ", "url": "   ", "playlist_identifier": "   ", "media_identifier": "   "}),
    ("verschachtelte Objekte", {"username": {"x": 1}, "password": {"x": 1}, "user_identifier": {"x": 1}, "playlist_identifier": {"x": 1}, "media_identifier": {"x": 1}}),
    ("Listen statt Strings", {"username": [], "password": [], "user_identifier": [], "name": [], "playlist_identifier": [], "media_identifier": []}),
]


def evaluate(status: int, expectation: str, _response_text: str) -> TestOutcome:
    if expectation == "unauth":
        if status in (401, 403):
            return TestOutcome("PASS", f"Auth blockiert den Request mit HTTP {status}.")
        return TestOutcome("FAIL", f"Endpoint sollte durch Admin-Key geschuetzt sein; erhalten wurde HTTP {status} statt 401/403.")
    if expectation == "reject":
        if 400 <= status < 500:
            return TestOutcome("PASS", f"Ungueltiger Input sauber abgelehnt (HTTP {status}).")
        if status >= 500:
            return TestOutcome("FAIL", "Ungueltiger Input verursachte 5xx statt kontrolliertem 4xx.")
        return TestOutcome("FAIL", f"Ungueltiger Input wurde mit HTTP {status} akzeptiert.")
    if expectation == "note":
        return TestOutcome("NOTE", f"HTTP {status}; Verhalten wird nur dokumentiert.")
    return TestOutcome("PASS", f"HTTP {status}.") if 200 <= status < 300 else TestOutcome("FAIL", f"Erwartet 2xx, erhalten HTTP {status}.")


def run_post(reporter, base_url, name, endpoint, headers, expectation, body=None, suffix=""):
    url = f"{base_url}{endpoint}{suffix}"
    perform_request(reporter, name=name, method="POST", url=url, headers=headers, body=body,
                    expectation="401/403" if expectation == "unauth" else "4xx rejection" if expectation == "reject" else "observation only",
                    evaluator=lambda s,_e,t,exp=expectation: evaluate(s,exp,t), timeout=10, header_name=HEADER_NAME)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auth-/Robustheitstest fuer create/delete")
    add_common_arguments(parser)
    args = parser.parse_args()
    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")
    reporter = Reporter("PyScrapper create/delete tests", mode, base_url, LOG_FILE)
    reporter.banner(base_url, Path(__file__), ENV_FILE)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.log(f"ABORT | ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)
    reporter.log(f"ADMIN_KEY  : {mask_secret(admin_key)}")
    valid = {HEADER_NAME: admin_key}
    bad_key = {HEADER_NAME: "definitiv-falscher-key"}

    reporter.section("AUTH - jeder geschuetzte Endpoint")
    for ep in CREATE_BODY_ENDPOINTS:
        body = VALID_BODIES[ep]
        run_post(reporter, base_url, f"{ep} ohne Key", ep, {}, "unauth", body)
        run_post(reporter, base_url, f"{ep} falscher Key", ep, bad_key, "unauth", body)
    for ep in DELETE_PATH_ENDPOINTS:
        run_post(reporter, base_url, f"{ep}{{id}} ohne Key", ep, {}, "unauth", suffix=NONEXISTENT_ID)
        run_post(reporter, base_url, f"{ep}{{id}} falscher Key", ep, bad_key, "unauth", suffix=NONEXISTENT_ID)
    for ep in DELETE_BODY_ENDPOINTS:
        body = VALID_BODIES[ep]
        run_post(reporter, base_url, f"{ep} ohne Key", ep, {}, "unauth", body)
        run_post(reporter, base_url, f"{ep} falscher Key", ep, bad_key, "unauth", body)

    reporter.section(f"INPUT VALIDATION ({mode})")
    bad_bodies = QUICK_BAD_BODIES if mode == "quick" else NORMAL_BAD_BODIES if mode == "normal" else INTENSE_BAD_BODIES
    body_endpoints = CREATE_BODY_ENDPOINTS + DELETE_BODY_ENDPOINTS
    for ep in body_endpoints:
        for case_name, body in bad_bodies:
            run_post(reporter, base_url, f"{ep} | {case_name}", ep, valid, "reject", body)
            time.sleep(.05 if mode == "quick" else .08)

    if mode != "quick":
        reporter.section("DELETE NONEXISTENT ID - Verhalten")
        for ep in DELETE_PATH_ENDPOINTS:
            run_post(reporter, base_url, f"{ep}{{nonexistent}}", ep, valid, "note", suffix=NONEXISTENT_ID)

    if mode == "intense":
        reporter.section("MALFORMED PATH IDS")
        for ep in DELETE_PATH_ENDPOINTS:
            for label, value in [("leer-aehnlich", "not-a-valid-id"), ("sehr lang", "A" * 2048), ("encoded traversal", "%2e%2e%2fetc%2fpasswd")]:
                run_post(reporter, base_url, f"{ep} malformed id | {label}", ep, valid, "reject", suffix=value)

    sys.exit(reporter.summary())

if __name__ == "__main__":
    main()
