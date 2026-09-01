"""Auth- und Robustheitstest fuer den PyScrapper /search-Endpoint.

Beispiele:
    python search_tests.py quick
    python search_tests.py normal --base-url http://127.0.0.1:8765
    python search_tests.py intense --verbose

Der Body folgt SearchRequest aus PythonModule/models/requests.py:
    provider   str
    search     str
    top        int = 5
    filters    { creator: str, tags: list[str] }

Ein Feld mediatype gibt es nicht - es wurde vom Server stillschweigend
ignoriert, weshalb die frueheren Faelle dazu echte Suchen ausgeloest haben
statt eine Ablehnung zu pruefen.

Faelle, die mit gueltigem Provider und gueltigem Suchbegriff durchlaufen,
loesen echten Traffic zu YouTube und Co. aus. Sie sind mit external=True
markiert und laufen nur in intense oder mit --allow-external.
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
LOG_FILE = TESTS_DIR / "search_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
DEFAULT_ENDPOINT = "/search"

TIMEOUT = {"quick": 10, "normal": 20, "intense": 35}
PAUSE = {"quick": 0.0, "normal": 0.1, "intense": 0.2}

VALID = {"provider": "youtube", "search": "test", "top": 3,
         "filters": {"creator": "", "tags": []}}

S_AUTH = "AUTH"
S_SCHEMA = "SCHEMA"
S_PROVIDER = "PROVIDER"
S_QUERY = "SUCHBEGRIFF"
S_TOP = "TOP"
S_FILTER = "FILTER"
S_EDGE = "GRENZWERTE"


def build_cases(admin_key: str) -> list[Case]:
    def body(**overrides):
        return {**VALID, **overrides}

    return [
        # ---------------------------------------------------------- AUTH
        Case("kein Admin-Key", "unauth", S_AUTH, VALID, headers={}, level="quick",
             checks="Endpoint haengt an require_admin"),
        Case("falscher Admin-Key", "unauth", S_AUTH, VALID,
             headers={HEADER_NAME: "definitiv-falscher-key"}, level="quick",
             checks="fremder Key darf nicht durchkommen"),
        Case("leerer Admin-Key", "unauth", S_AUTH, VALID,
             headers={HEADER_NAME: ""}, level="quick",
             checks="leerer Header ist kein gueltiger Key"),
        Case("Key mit Leerzeichen am Rand", "unauth", S_AUTH, VALID,
             headers={HEADER_NAME: f" {admin_key} "}, level="intense",
             checks="compare_digest trimmt nicht"),

        # -------------------------------------------------------- SCHEMA
        Case("leerer Body", "reject", S_SCHEMA, {}, level="quick",
             checks="provider und search fehlen"),
        Case("voellig falsche Felder", "reject", S_SCHEMA,
             {"foo": "bar", "banana": 42}, level="quick",
             checks="keine Pflichtfelder vorhanden"),
        Case("altes Schema query statt search", "reject", S_SCHEMA,
             {"provider": "youtube", "query": "test", "mediatype": ".mp3"},
             level="quick", checks="Regression: Modell erwartet search, nicht query"),
        Case("null in Pflichtfeldern", "reject", S_SCHEMA,
             {"provider": None, "search": None}, level="normal",
             checks="None ist fuer str nicht zulaessig"),
        Case("falsche Typen", "reject", S_SCHEMA,
             {"provider": 123, "search": ["a", "b"]}, level="quick",
             checks="Pydantic-Typpruefung"),
        Case("search als Objekt", "reject", S_SCHEMA,
             {"provider": "youtube", "search": {"q": "test"}}, level="normal",
             checks="search muss ein String sein"),
        Case("fehlender Provider", "reject", S_SCHEMA, {"search": "test"},
             level="normal", checks="provider ist Pflichtfeld"),
        Case("fehlendes search", "reject", S_SCHEMA, {"provider": "youtube"},
             level="normal", checks="search ist Pflichtfeld"),
        Case("Body ist ein String", "reject", S_SCHEMA, "einfach nur text",
             level="normal", checks="Body muss ein JSON-Objekt sein"),

        # ------------------------------------------------------ PROVIDER
        Case("unbekannter Provider", "reject", S_PROVIDER,
             body(provider="totallynotaprovider"), level="quick",
             checks="kein Alias trifft zu - erwartet wird 4xx, nicht 5xx"),
        Case("leerer Provider", "reject", S_PROVIDER, body(provider=""),
             level="normal", checks="leerer String trifft keinen Provider"),
        Case("Provider nur Whitespace", "reject", S_PROVIDER, body(provider="   "),
             level="normal", checks="Whitespace darf keinen Provider treffen"),
        Case("Provider mit Steuerzeichen", "reject", S_PROVIDER,
             body(provider="youtube\n"), level="intense",
             checks="Alias-Vergleich soll Steuerzeichen nicht dulden"),
        Case("Provider ohne Suchfunktion (default)", "reject", S_PROVIDER,
             body(provider="default"), level="normal",
             checks="default steht nur im Getresults-Mapping"),
        Case("Provider ohne Suchfunktion (wcoflix)", "reject", S_PROVIDER,
             body(provider="wcoflix"), level="normal",
             checks="wcoflix hat keine search-Funktion"),
        Case("suno - Suche ist Platzhalter", "note", S_PROVIDER,
             body(provider="suno"), level="normal",
             checks="Verhalten der Platzhalter-Suche dokumentieren"),

        # --------------------------------------------------- SUCHBEGRIFF
        Case("leerer Suchbegriff", "reject", S_QUERY, body(search=""),
             level="quick",
             checks="leere Suche soll vor dem Provideraufruf abgelehnt werden"),
        Case("Suchbegriff nur Whitespace", "reject", S_QUERY, body(search="     "),
             level="normal", checks="Whitespace ist kein Suchbegriff"),
        Case("SQL-artige Zeichen", "note", S_QUERY,
             body(search="'; DROP TABLE Users;--"), level="normal", external=True,
             checks="muss als harmloser String behandelt werden"),
        Case("HTML im Suchbegriff", "note", S_QUERY,
             body(search="<script>alert(1)</script>"), level="intense", external=True,
             checks="darf nicht ungefiltert weitergereicht werden"),
        Case("Newline im Suchbegriff", "note", S_QUERY,
             body(search="test\r\nX-Injected: 1"), level="intense", external=True,
             checks="Header-Injection in den ausgehenden Aufruf"),

        # ----------------------------------------------------------- TOP
        Case("top negativ", "reject", S_TOP, body(top=-5), level="normal",
             checks="negative Trefferzahl ergibt keinen Sinn"),
        Case("top als String", "note", S_TOP, body(top="5"), level="intense",
             external=True, checks="Pydantic wandelt numerische Strings um"),
        Case("top absurd hoch", "reject", S_TOP, body(top=1_000_000),
             level="intense", checks="Obergrenze fuer aufgeloeste Ergebnisse"),

        # -------------------------------------------------------- FILTER
        Case("filters als String", "reject", S_FILTER,
             body(filters="keine-struktur"), level="normal",
             checks="filters muss ein Objekt sein"),
        Case("tags als String statt Liste", "reject", S_FILTER,
             body(filters={"creator": "", "tags": "track"}), level="normal",
             checks="tags ist list[str]"),
        Case("tags mit Nicht-Strings", "reject", S_FILTER,
             body(filters={"creator": "", "tags": [1, None]}), level="intense",
             checks="jeder Tag muss ein String sein"),
        Case("unbekannter Tag", "note", S_FILTER,
             body(filters={"creator": "", "tags": ["gibtsnicht"]}),
             level="normal", external=True,
             checks="unbekannter Tag filtert alles weg - leeres Ergebnis erwartet"),

        # ---------------------------------------------------- GRENZWERTE
        Case("extrem langer Suchbegriff", "note", S_EDGE, body(search="A" * 10000),
             level="normal", external=True,
             checks="10000 Zeichen gehen ungefiltert an den Anbieter"),
        Case("sehr viele Tags", "note", S_EDGE,
             body(filters={"creator": "", "tags": [f"t{i}" for i in range(2000)]}),
             level="intense", external=True, checks="grosse Filterliste"),
        Case("Unicode im Suchbegriff", "note", S_EDGE, body(search="Musik Test"),
             level="intense", external=True,
             checks="nicht-lateinische Zeichen im Suchbegriff"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auth- und Robustheitstest fuer /search")
    add_common_arguments(parser)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help=f"Endpoint-Pfad (Default: {DEFAULT_ENDPOINT})")
    args = parser.parse_args()
    enable_colors(args.no_color)

    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")
    endpoint = "/" + args.endpoint.strip("/")

    reporter = Reporter("PyScrapper · Search-Endpoint", mode, base_url,
                        LOG_FILE, verbose=args.verbose)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.banner(base_url + endpoint, Path(__file__), ENV_FILE)
        reporter.out(f"\n ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        sys.exit(2)

    all_cases = build_cases(admin_key)
    cases = select_cases(all_cases, mode, args)
    external = sum(1 for c in cases if c.external)
    reporter.banner(base_url + endpoint, Path(__file__), ENV_FILE,
                    planned=len(cases), total=len(all_cases),
                    extra={"Admin-Key": mask_secret(admin_key)})
    check_server(reporter, base_url, {HEADER_NAME: admin_key})

    if not cases:
        reporter.out("\n Kein Fall passt zu Modus und Filter.")
        sys.exit(2)
    if external:
        reporter.info(f"{external} Faelle loesen echte Suchanfragen beim Anbieter aus "
                      f"(ohne --allow-external nur in intense).")

    run_suite(reporter, base_url, cases, endpoint, {HEADER_NAME: admin_key},
              args, TIMEOUT[mode], PAUSE[mode])
    sys.exit(reporter.summary())


if __name__ == "__main__":
    main()
