"""Auth- und Robustheitstest fuer den PyScrapper Download-Endpoint.

Beispiele:
    python download_tests.py quick
    python download_tests.py normal --base-url http://127.0.0.1:8765
    python download_tests.py intense --verbose

Der Body folgt DownloadRequest aus PythonModule/models/requests.py:
    provider            str
    urls                list[str]
    filenames           list[str]     gleiche Laenge wie urls
    download_strategie  stream | local | cached_stream     (Default stream)
    preferred_type      audio | video | None
    preferred_file      Endung ohne Punkt, z.B. mp3
    extra_headers       dict | None
    download_path       str           nur bei local geprueft
    auto_convert        bool

Die frueheren Felder url / filename / mediatype existieren im Modell nicht.
Mit ihnen antwortete der Server auf jeden Fall mit 422 "Field required",
wodurch die Suite gruen war, ohne je die Validierung dahinter zu erreichen.
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
LOG_FILE = TESTS_DIR / "download_endpoint_test.log"
ENV_FILE = PROJECT_ROOT / ".env"
HEADER_NAME = "X-Admin-Key"
DEFAULT_ENDPOINT = "/download/video-audio"

TIMEOUT = {"quick": 10, "normal": 15, "intense": 30}
PAUSE = {"quick": 0.0, "normal": 0.1, "intense": 0.15}

# Strukturell gueltiger Body. Nur fuer die Auth-Ebene - dort greift die Auth
# vor jeder Verarbeitung, es wird also nichts heruntergeladen.
VALID = {
    "provider": "youtube",
    "urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    "filenames": ["pyscrapper_authtest"],
    "download_strategie": "stream",
    "preferred_type": "audio",
    "preferred_file": "mp3",
}

S_AUTH = "AUTH"
S_SCHEMA = "SCHEMA"
S_PROVIDER = "PROVIDER"
S_URL = "URLS"
S_FILE = "DATEINAMEN"
S_OPT = "OPTIONEN"
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
        Case("Key im Authorization-Header", "unauth", S_AUTH, VALID,
             headers={"Authorization": admin_key}, level="normal",
             checks="nur X-Admin-Key zaehlt"),
        Case("Key als Query-Parameter", "unauth", S_AUTH, VALID, headers={},
             path=f"{DEFAULT_ENDPOINT}?key={admin_key}", level="intense",
             checks="alter Aufrufstil mit Key im Pfad darf nicht greifen"),

        # -------------------------------------------------------- SCHEMA
        Case("leerer Body", "reject", S_SCHEMA, {}, level="quick",
             checks="provider, urls und filenames fehlen"),
        Case("voellig falsche Felder", "reject", S_SCHEMA,
             {"foo": "bar", "banana": 42}, level="quick",
             checks="keines der Pflichtfelder vorhanden"),
        Case("altes Schema url/filename/mediatype", "reject", S_SCHEMA,
             {"provider": "youtube", "url": "https://example.com/x",
              "mediatype": ".mp3", "filename": "test"}, level="quick",
             checks="Regression: Modell erwartet urls und filenames als Listen"),
        Case("null in Pflichtfeldern", "reject", S_SCHEMA,
             {"provider": None, "urls": None, "filenames": None}, level="normal",
             checks="None ist fuer str und list[str] nicht zulaessig"),
        Case("falsche Typen", "reject", S_SCHEMA,
             {"provider": 12345, "urls": "keine liste", "filenames": {"a": 1}},
             level="quick", checks="Pydantic-Typpruefung je Feld"),
        Case("urls als String statt Liste", "reject", S_SCHEMA,
             {"provider": "youtube", "urls": "https://example.com/x",
              "filenames": ["a"]}, level="normal",
             checks="urls muss list[str] sein"),
        Case("Liste mit Nicht-Strings", "reject", S_SCHEMA,
             {"provider": "youtube", "urls": [123, None], "filenames": ["a", "b"]},
             level="normal", checks="validateListStr prueft jeden Eintrag"),
        Case("Body ist eine Liste", "reject", S_SCHEMA, [1, 2, 3], level="normal",
             checks="Body muss ein JSON-Objekt sein"),
        Case("fehlendes filenames", "reject", S_SCHEMA,
             {"provider": "youtube", "urls": ["https://example.com/x"]},
             level="normal", checks="filenames ist Pflichtfeld"),

        # ------------------------------------------------------ PROVIDER
        Case("unbekannter Provider", "reject", S_PROVIDER,
             body(provider="totallynotaprovider"), level="quick",
             checks="validateProviders findet keinen Alias"),
        Case("leerer Provider", "reject", S_PROVIDER, body(provider=""),
             level="normal", checks="leerer String trifft keinen Provider"),
        Case("Provider nur Whitespace", "reject", S_PROVIDER, body(provider="   "),
             level="intense", checks="Whitespace darf keinen Provider treffen"),
        Case("Provider mit Steuerzeichen", "reject", S_PROVIDER,
             body(provider="youtube\n"), level="intense",
             checks="Alias-Vergleich soll Steuerzeichen nicht dulden"),
        Case("Provider mit Pfadanteil", "reject", S_PROVIDER,
             body(provider="../youtube"), level="intense",
             checks="Alias-Lookup darf keine Pfade dulden"),

        # ---------------------------------------------------------- URLS
        Case("leere URL-Liste", "reject", S_URL, body(urls=[], filenames=[]),
             level="normal", checks="ohne URL gibt es nichts aufzuloesen"),
        Case("urls und filenames unterschiedlich lang", "reject", S_URL,
             body(urls=["https://example.com/a", "https://example.com/b"],
                  filenames=["nur_einer"]), level="quick",
             checks="ArgumentErrorCompare in model_post_init"),
        Case("http statt https", "reject", S_URL,
             body(urls=["http://example.com/x"]), level="quick",
             checks="validateHostDefault erlaubt nur https"),
        Case("file://-Schema", "reject", S_URL,
             body(urls=["file:///etc/passwd"]), level="quick",
             checks="lokaler Dateizugriff ueber die URL"),
        Case("ftp://-Schema", "reject", S_URL,
             body(urls=["ftp://example.com/x"]), level="normal",
             checks="nur http-Schemata sind vorgesehen"),
        Case("data:-Schema", "reject", S_URL,
             body(urls=["data:text/plain,hello"]), level="normal",
             checks="Datenschema ist keine abrufbare Ressource"),
        Case("javascript:-Schema", "reject", S_URL,
             body(urls=["javascript:alert(1)"]), level="normal",
             checks="Skriptschema darf nicht akzeptiert werden"),
        Case("kein URL-Format, nur Text", "reject", S_URL,
             body(urls=["das ist keine url"]), level="normal",
             checks="urlparse liefert kein Schema"),
        Case("localhost als Ziel", "reject", S_URL,
             body(urls=["https://127.0.0.1:8765/health"]), level="intense",
             checks="SSRF auf den eigenen Server"),
        Case("interne IP als Ziel", "reject", S_URL,
             body(urls=["https://192.168.0.1/admin"]), level="intense",
             checks="SSRF ins lokale Netz"),
        Case("Zugangsdaten in der URL", "reject", S_URL,
             body(urls=["https://user:pass@example.com/x"]), level="intense",
             checks="Credentials im URL-Teil"),

        # ---------------------------------------------------- DATEINAMEN
        Case("Path-Traversal Windows", "reject", S_FILE,
             body(filenames=["..\\..\\..\\windows\\system32\\evil"]), level="quick",
             checks="Ausbruch aus dem Zielordner"),
        Case("Path-Traversal Unix", "reject", S_FILE,
             body(filenames=["../../../../etc/cron.d/x"]), level="quick",
             checks="Ausbruch aus dem Zielordner"),
        Case("absoluter Windows-Pfad", "reject", S_FILE,
             body(filenames=["C:\\Windows\\evil"]), level="normal",
             checks="os.path.join ignoriert den Zielordner"),
        Case("absoluter Unix-Pfad", "reject", S_FILE,
             body(filenames=["/etc/passwd"]), level="normal",
             checks="fuehrender Slash setzt den Zielordner ausser Kraft"),
        Case("UNC-Pfad", "reject", S_FILE,
             body(filenames=["\\\\server\\share\\evil"]), level="intense",
             checks="Netzwerkfreigabe als Ziel"),
        Case("Reservename CON", "reject", S_FILE, body(filenames=["CON"]),
             level="normal", checks="reservierte Geraetenamen unter Windows"),
        Case("Reservename COM1", "reject", S_FILE, body(filenames=["COM1"]),
             level="intense", checks="reservierte Geraetenamen unter Windows"),
        Case("leerer Dateiname", "reject", S_FILE, body(filenames=[""]),
             level="normal", checks="Name ohne Stamm"),
        Case("Dateiname nur Whitespace", "reject", S_FILE, body(filenames=["   "]),
             level="intense", checks="Whitespace als Dateiname"),
        Case("Dateiname ist ein Punkt", "reject", S_FILE, body(filenames=["."]),
             level="intense", checks="Punkt verweist auf den Ordner selbst"),
        Case("Nullbyte im Dateinamen", "reject", S_FILE,
             body(filenames=["evil\u0000.mp3"]), level="intense",
             checks="Nullbyte kann Pfadpruefungen abschneiden"),
        Case("Steuerzeichen im Dateinamen", "reject", S_FILE,
             body(filenames=["a\r\nb"]), level="intense",
             checks="Zeilenumbrueche in Pfaden und Logs"),

        # ------------------------------------------------------ OPTIONEN
        Case("unbekannte Strategie", "reject", S_OPT,
             body(download_strategie="teleport"), level="normal",
             checks="Enum kennt nur stream, local und cached_stream"),
        Case("preferred_type ungueltig", "reject", S_OPT,
             body(preferred_type="hologram"), level="normal",
             checks="erlaubt sind nur audio und video"),
        Case("preferred_file nicht unterstuetzt", "reject", S_OPT,
             body(preferred_file="exe"), level="quick",
             checks="Endung steht nicht in SUPPORTED_EXTENSIONS"),
        Case("preferred_file mit fuehrendem Punkt", "note", S_OPT,
             body(preferred_file=".mp3"), level="intense",
             checks="removeprefix('.') soll das abfangen - Verhalten dokumentieren"),
        Case("extra_headers als String", "reject", S_OPT,
             body(extra_headers="nicht-dict"), level="normal",
             checks="extra_headers muss ein Objekt sein"),
        Case("local mit nicht existentem Pfad", "reject", S_OPT,
             body(download_strategie="local", download_path="Z:\\gibt\\es\\nicht"),
             level="normal",
             checks="bei local wird der Zielordner auf Existenz und Schreibrecht geprueft"),
        Case("local mit Systemordner", "reject", S_OPT,
             body(download_strategie="local", download_path="C:\\Windows\\System32"),
             level="intense", checks="Schreibversuch in einen Systemordner"),
        Case("auto_convert als String", "reject", S_OPT,
             body(download_strategie="local", auto_convert="ja"), level="intense",
             checks="bool wird erwartet"),

        # ---------------------------------------------------- GRENZWERTE
        Case("extrem langer Dateiname", "reject", S_EDGE,
             body(filenames=["A" * 5000]), level="normal",
             checks="Pfadlaengenbegrenzung des Dateisystems"),
        Case("extrem lange URL", "reject", S_EDGE,
             body(urls=["https://example.com/" + "a" * 20000]), level="intense",
             checks="sehr langer Eingabewert"),
        Case("500 URLs auf einmal", "reject", S_EDGE,
             body(urls=[f"https://example.com/{i}" for i in range(500)],
                  filenames=[f"f{i}" for i in range(500)]), level="intense",
             checks="Obergrenze fuer die Anzahl Kontexte"),
        Case("Unicode und Emoji im Dateinamen", "note", S_EDGE,
             body(filenames=["taest_uenicode_musik"]), level="intense",
             checks="Sonderzeichen im Zielnamen - Verhalten dokumentieren"),
        Case("verschachteltes extra_headers", "note", S_EDGE,
             body(extra_headers={"a": {"b": {"c": {"d": "e"}}}}), level="intense",
             checks="verschachtelte Struktur in extra_headers"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auth- und Robustheitstest fuer den Download-Endpoint")
    add_common_arguments(parser)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help=f"Endpoint-Pfad (Default: {DEFAULT_ENDPOINT})")
    args = parser.parse_args()
    enable_colors(args.no_color)

    mode = selected_mode(args)
    base_url = args.base_url.rstrip("/")
    endpoint = "/" + args.endpoint.strip("/")

    reporter = Reporter("PyScrapper · Download-Endpoint", mode, base_url,
                        LOG_FILE, verbose=args.verbose)

    admin_key = load_env_value(ENV_FILE, "ADMIN_KEY")
    if not admin_key:
        reporter.banner(base_url + endpoint, Path(__file__), ENV_FILE)
        reporter.out(f"\n ABBRUCH: ADMIN_KEY nicht in {ENV_FILE} gefunden.")
        reporter.out(" Ohne Key antwortet jeder Fall mit 401 und sagt nichts aus.")
        sys.exit(2)

    all_cases = build_cases(admin_key)
    cases = select_cases(all_cases, mode, args)
    reporter.banner(base_url + endpoint, Path(__file__), ENV_FILE,
                    planned=len(cases), total=len(all_cases),
                    extra={"Admin-Key": mask_secret(admin_key)})
    check_server(reporter, base_url, {HEADER_NAME: admin_key})

    if not cases:
        reporter.out("\n Kein Fall passt zu Modus und Filter.")
        sys.exit(2)

    run_suite(reporter, base_url, cases, endpoint, {HEADER_NAME: admin_key},
              args, TIMEOUT[mode], PAUSE[mode])
    sys.exit(reporter.summary())


if __name__ == "__main__":
    main()
