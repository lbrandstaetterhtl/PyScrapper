"""Auth- und Robustheitstests fuer den PyScrapper /search-Endpoint."""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
from test_common import Reporter, TestOutcome, add_common_arguments, load_env_value, mask_secret, perform_request, selected_mode

TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
PROJECT_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "search_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
DEFAULT_ENDPOINT = "/search"

# Das alte Testpaket nutzte irrtuemlich `query`. Die vorhandenen Logs zeigen
# eindeutig, dass das Backend das Pflichtfeld `search` erwartet.
VALID_PAYLOAD = {"provider": "youtube", "search": "test", "mediatype": ".mp3"}

QUICK_CASES = [
    ("leerer Body", {}, "reject"),
    ("voellig falsche Felder", {"foo": "bar", "banana": 42}, "reject"),
    ("null-Werte", {"provider": None, "search": None, "mediatype": None}, "reject"),
    ("unbekannter Provider", {"provider": "totallynotaprovider", "search": "test", "mediatype": ".mp3"}, "reject"),
    ("falsche Typen", {"provider": 123, "search": ["a", "b"], "mediatype": {"x": 1}}, "reject"),
]

NORMAL_CASES = QUICK_CASES + [
    ("leerer Provider", {"provider": "", "search": "test", "mediatype": ".mp3"}, "reject"),
    ("leere Suche", {"provider": "youtube", "search": "", "mediatype": ".mp3"}, "reject"),
    ("Suche nur Whitespace", {"provider": "youtube", "search": "     ", "mediatype": ".mp3"}, "reject"),
    ("extrem lange Suche", {"provider": "youtube", "search": "A" * 10000, "mediatype": ".mp3"}, "reject"),
    ("nicht erlaubter Media-Type", {"provider": "youtube", "search": "test", "mediatype": ".exe"}, "reject"),
    ("Media-Type fehlt", {"provider": "youtube", "search": "test"}, "reject"),
    ("Suno Platzhalter", {"provider": "suno", "search": "test", "mediatype": ".mp3"}, "note"),
    ("SQL-artige Suchzeichen", {"provider": "youtube", "search": "'; DROP TABLE Users;--", "mediatype": ".mp3"}, "note"),
]

INTENSE_CASES = NORMAL_CASES + [
    ("Provider nur Whitespace", {"provider": "   ", "search": "test", "mediatype": ".mp3"}, "reject"),
    ("Provider mit Steuerzeichen", {"provider": "youtube\n", "search": "test", "mediatype": ".mp3"}, "reject"),
    ("fehlender Provider", {"search": "test", "mediatype": ".mp3"}, "reject"),
    ("fehlende Suche", {"provider": "youtube", "mediatype": ".mp3"}, "reject"),
    ("Suche als Objekt", {"provider": "youtube", "search": {"q": "test"}, "mediatype": ".mp3"}, "reject"),
    ("Media-Type als Liste", {"provider": "youtube", "search": "test", "mediatype": [".mp3"]}, "reject"),
    ("Unicode-Suche", {"provider": "youtube", "search": "äöü 日本語 🎵", "mediatype": ".mp3"}, "note"),
]


def evaluate(status: int, expectation: str, response_text: str) -> TestOutcome:
    if expectation == "unauth":
        return TestOutcome("PASS", f"Auth blockiert mit HTTP {status}.") if status in (401,403) else TestOutcome("FAIL", f"Erwartet 401/403 vor Endpoint-Logik, erhalten HTTP {status}.")
    if expectation == "reject":
        if 400 <= status < 500:
            return TestOutcome("PASS", f"Ungueltiger Request sauber abgelehnt (HTTP {status}).")
        if status >= 500:
            return TestOutcome("FAIL", "Ungueltiger Input fuehrte zu 5xx statt kontrolliertem 4xx.")
        return TestOutcome("FAIL", f"Ungueltiger Input wurde mit HTTP {status} akzeptiert; moeglicherweise wurde echte externe Suche gestartet.")
    if expectation == "note":
        return TestOutcome("NOTE", f"HTTP {status}; Beobachtungsfall, nicht bewertet.")
    return TestOutcome("PASS", f"HTTP {status}.") if 200 <= status < 300 else TestOutcome("FAIL", f"Erwartet 2xx, erhalten HTTP {status}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auth- und Robustheitstest fuer /search")
    add_common_arguments(parser)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    args = parser.parse_args()
    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")
    endpoint = "/" + args.endpoint.strip("/")
    target = base_url + endpoint
    reporter = Reporter("PyScrapper search tests", mode, base_url, LOG_FILE)
    reporter.banner(target, Path(__file__), ENV_FILE)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.log(f"ABORT | ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)
    reporter.log(f"ADMIN_KEY  : {mask_secret(admin_key)}")
    reporter.log("SCHEMA FIX : Test-Payload nutzt jetzt `search` statt des alten falschen Felds `query`.")

    valid_headers = {HEADER_NAME: admin_key}
    reporter.section("AUTH")
    for name, headers in [
        ("kein Admin-Key", {}),
        ("falscher Admin-Key", {HEADER_NAME: "definitiv-falscher-key"}),
        ("leerer Admin-Key", {HEADER_NAME: ""}),
    ]:
        perform_request(reporter, name=name, method="POST", url=target, headers=headers, body=VALID_PAYLOAD,
                        expectation="401/403 before endpoint logic",
                        evaluator=lambda s,_e,t: evaluate(s,"unauth",t), timeout=20, header_name=HEADER_NAME)
        time.sleep(.08)

    reporter.section(f"INPUT VALIDATION ({mode})")
    cases = QUICK_CASES if mode == "quick" else NORMAL_CASES if mode == "normal" else INTENSE_CASES
    for name, payload, exp in cases:
        perform_request(reporter, name=name, method="POST", url=target, headers=valid_headers, body=payload,
                        expectation="4xx rejection" if exp == "reject" else "observation only",
                        evaluator=lambda s,_e,t,exp=exp: evaluate(s,exp,t), timeout=20, header_name=HEADER_NAME)
        time.sleep(.08 if mode == "quick" else .12)

    if mode == "intense":
        reporter.log("INFO | NOTE-Faelle mit gueltigem Provider koennen bei Akzeptanz echte externe Suchanfragen ausloesen.")
    sys.exit(reporter.summary())

if __name__ == "__main__":
    main()
