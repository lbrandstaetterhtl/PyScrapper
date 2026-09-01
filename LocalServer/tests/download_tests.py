"""Auth- und Robustheitstests fuer den PyScrapper Download-Endpoint.

Beispiele:
    python download_tests.py quick
    python download_tests.py normal --base-url http://127.0.0.1:8765
    python download_tests.py --mode intense

Modi:
    quick   - Auth + wichtigste Schema-/Security-Checks
    normal  - quick + komplette bisherige Negativtest-Suite
    intense - normal + weitere Grenz-, Schema- und Pfadfaelle
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from test_common import (
        Reporter,
        TestOutcome,
        add_common_arguments,
        load_env_value,
        mask_secret,
        mode_at_least,
        perform_request,
        selected_mode,
    )
except ImportError as exc:
    print(f"Test-Hilfsmodul konnte nicht geladen werden: {exc}")
    sys.exit(2)

TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
PROJECT_ROOT = SERVER_DIR.parent
LOG_FILE = TESTS_DIR / "download_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
DEFAULT_ENDPOINT = "/download/video-audio"

VALID_PAYLOAD = {
    "provider": "youtube",
    "url": "https://example.com/x",
    "mediatype": ".mp3",
    "filename": "test",
}

QUICK_CASES = [
    ("leerer Body", {}, "reject"),
    ("voellig falsche Felder", {"foo": "bar", "banana": 42}, "reject"),
    ("null-Werte in Pflichtfeldern", {"provider": None, "url": None, "mediatype": None, "filename": None}, "reject"),
    ("file://-Schema", {"provider": "youtube", "url": "file:///etc/passwd", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("falsche Typen", {"provider": 12345, "url": ["not", "a", "string"], "mediatype": True, "filename": {"nested": "object"}}, "reject"),
]

NORMAL_CASES = QUICK_CASES + [
    ("unbekannter Provider", {"provider": "totallynotaprovider", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("leerer Provider", {"provider": "", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("http statt https", {"provider": "youtube", "url": "http://example.com/x", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("keine URL, nur Text", {"provider": "youtube", "url": "das ist keine url", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("nicht erlaubter Media-Type", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".exe", "filename": "test"}, "reject"),
    ("Path-Traversal Windows", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "..\\..\\..\\windows\\system32\\evil"}, "reject"),
    ("Path-Traversal Unix", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "../../../../etc/cron.d/x"}, "reject"),
    ("absoluter Windows-Pfad", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "C:\\Windows\\evil"}, "reject"),
    ("Windows Reserved Name CON", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "CON"}, "reject"),
    ("extrem langer Dateiname", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "A" * 5000}, "reject"),
]

INTENSE_CASES = NORMAL_CASES + [
    ("leerer Dateiname", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": ""}, "reject"),
    ("Dateiname nur Whitespace", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "   "}, "reject"),
    ("Dateiname Punkt", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "."}, "reject"),
    ("Dateiname Doppelpunkt", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": ".."}, "reject"),
    ("absoluter Unix-Pfad", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "/etc/passwd"}, "reject"),
    ("UNC-Pfad", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "\\\\server\\share\\evil"}, "reject"),
    ("NUL im Dateinamen", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "evil\u0000.mp3"}, "reject"),
    ("Reserved Name AUX", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "AUX"}, "reject"),
    ("Reserved Name COM1", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3", "filename": "COM1"}, "reject"),
    ("ftp://-Schema", {"provider": "youtube", "url": "ftp://example.com/x", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("data:-Schema", {"provider": "youtube", "url": "data:text/plain,hello", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("javascript:-Schema", {"provider": "youtube", "url": "javascript:alert(1)", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("fehlender Provider", {"url": "https://example.com/x", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("fehlende URL", {"provider": "youtube", "mediatype": ".mp3", "filename": "test"}, "reject"),
    ("fehlender Media-Type", {"provider": "youtube", "url": "https://example.com/x", "filename": "test"}, "reject"),
    ("fehlender Dateiname", {"provider": "youtube", "url": "https://example.com/x", "mediatype": ".mp3"}, "reject"),
]


def evaluate(status: int, expectation: str, response_text: str) -> TestOutcome:
    if expectation == "unauth":
        if status in (401, 403):
            return TestOutcome("PASS", f"Auth blockiert den Request mit HTTP {status}.")
        return TestOutcome("FAIL", f"Auth sollte vor der Endpoint-Logik mit 401/403/404 blockieren, bekam aber HTTP {status}.")

    if expectation == "reject":
        if 400 <= status < 500:
            return TestOutcome("PASS", f"Ungueltiger Request wurde sauber clientseitig abgelehnt (HTTP {status}).")
        if 500 <= status:
            lower = response_text.lower()
            if "url" in lower or "reach" in lower or "resolve" in lower:
                return TestOutcome(
                    "FAIL",
                    "Der Request passierte die fruehe Eingabevalidierung und erreichte offenbar URL-/Media-Aufloesung; dort entstand ein 5xx. Erwartet war ein sauberer 4xx vor tieferer Verarbeitung.",
                )
            return TestOutcome("FAIL", "Ungueltiger Input fuehrte zu einem Serverfehler (5xx) statt zu einem kontrollierten 4xx.")
        return TestOutcome("FAIL", f"Ungueltiger Input wurde mit HTTP {status} akzeptiert; erwartet war 4xx.")

    if expectation == "note":
        return TestOutcome("NOTE", f"HTTP {status}; dieser Fall wird nur beobachtet und nicht bewertet.")

    if 200 <= status < 300:
        return TestOutcome("PASS", f"Request wurde wie erwartet akzeptiert (HTTP {status}).")
    return TestOutcome("FAIL", f"Erwartet war 2xx, erhalten wurde HTTP {status}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auth- und Robustheitstest fuer den Download-Endpoint")
    add_common_arguments(parser)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Endpoint-Pfad (Default: {DEFAULT_ENDPOINT})")
    args = parser.parse_args()
    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")
    endpoint = "/" + args.endpoint.strip("/")
    target = f"{base_url}{endpoint}"

    reporter = Reporter("PyScrapper download tests", mode, base_url, LOG_FILE)
    reporter.banner(target, Path(__file__), ENV_FILE)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.log(f"ABORT | ADMIN_KEY nicht in {ENV_FILE} gefunden. Input-Tests waeren sonst nur Auth-Fehler.")
        sys.exit(2)
    reporter.log(f"ADMIN_KEY  : {mask_secret(admin_key)}")

    valid_headers = {HEADER_NAME: admin_key}
    bad_headers = {HEADER_NAME: "definitiv-falscher-key"}

    reporter.section("AUTH")
    auth_cases = [
        ("kein Admin-Key", {}),
        ("falscher Admin-Key", bad_headers),
        ("leerer Admin-Key", {HEADER_NAME: ""}),
    ]
    for name, headers in auth_cases:
        perform_request(
            reporter,
            name=name,
            method="POST",
            url=target,
            headers=headers,
            body=VALID_PAYLOAD,
            expectation="401/403 before endpoint logic",
            evaluator=lambda status, _expectation, text: evaluate(status, "unauth", text),
            timeout=10,
            header_name=HEADER_NAME,
        )
        time.sleep(0.08)

    reporter.section(f"INPUT VALIDATION ({mode})")
    cases = QUICK_CASES if mode == "quick" else NORMAL_CASES if mode == "normal" else INTENSE_CASES
    for name, payload, expectation in cases:
        perform_request(
            reporter,
            name=name,
            method="POST",
            url=target,
            headers=valid_headers,
            body=payload,
            expectation="4xx rejection" if expectation == "reject" else expectation,
            evaluator=lambda status, _expectation, text, exp=expectation: evaluate(status, exp, text),
            timeout=10,
            header_name=HEADER_NAME,
        )
        time.sleep(0.08 if mode == "quick" else 0.12)

    if mode_at_least(mode, "normal"):
        reporter.log("")
        reporter.log("INFO | Filename-Faelle verwenden absichtlich keine echte Media-URL. Ein 5xx aus URL-Aufloesung zeigt daher, dass der Request bereits zu tief in die Verarbeitung gelangt ist; er beweist nicht isoliert eine Filename-Luecke.")

    sys.exit(reporter.summary())


if __name__ == "__main__":
    main()
