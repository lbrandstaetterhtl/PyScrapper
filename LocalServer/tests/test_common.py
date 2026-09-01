"""
test_common.py
==============
Gemeinsame Basis der PyScrapper-Endpoint-Tests.

Enthaelt Argumentparser, .env-Zugriff, HTTP-Client (urllib, keine externen
Pakete) und die Ergebnisausgabe.

Ausgabe pro Fall ist eine Zeile:

    <symbol> <nr>  <name>                    <status>  <dauer>  <urteil>

Details (Request, Antwort, geprueftes Verhalten) erscheinen nur bei
Auffaelligkeiten - oder bei allen Faellen mit --verbose. Am Ende steht eine
Tabelle pro Abschnitt und eine Wiederholung aller Auffaelligkeiten.

Das Logfile enthaelt dasselbe ohne Farbcodes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from urllib import error as urllib_error
from urllib import request as urllib_request

MODES = ("quick", "normal", "intense")
RANK = {"quick": 0, "normal": 1, "intense": 2}

MODE_HELP = {
    "quick":   "Auth und die wichtigsten Schemafaelle - wenige Sekunden",
    "normal":  "Auth und vollstaendige Eingabepruefung - Standard",
    "intense": "zusaetzlich Grenzwerte, Pfade, Unicode und Lastfaelle",
}


# ==========================================================================
# Farben
# ==========================================================================
class C:
    on = False
    RESET = "\033[0m"; BOLD = "\033[1m"
    RED = "\033[31m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    BLUE = "\033[34m"; CYAN = "\033[36m"; GREY = "\033[90m"

    @classmethod
    def p(cls, text, *codes):
        return "".join(codes) + text + cls.RESET if cls.on else text


ANSI = re.compile(r"\033\[[0-9;]*m")


def enable_colors(force_off: bool = False) -> None:
    if force_off or os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        C.on = False
        return
    if os.name == "nt":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.SetConsoleMode(handle, 7)
        except Exception:
            C.on = False
            return
    C.on = True


# ==========================================================================
# Argumente
# ==========================================================================
def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("mode", nargs="?", choices=MODES,
                        help="Testtiefe: quick, normal oder intense (Default: normal)")
    parser.add_argument("--mode", dest="mode_flag", choices=MODES,
                        help="alternative Schreibweise fuer den Modus")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765",
                        help="Basis-URL des Servers (Default: http://127.0.0.1:8765)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Detailblock zu jedem Fall, nicht nur zu Auffaelligkeiten")
    parser.add_argument("--only", metavar="TEXT",
                        help="nur Faelle ausfuehren, deren Name diesen Text enthaelt")
    parser.add_argument("--allow-external", action="store_true",
                        help="auch Faelle ausfuehren, die echte externe Anfragen ausloesen "
                             "(in intense automatisch aktiv)")
    parser.add_argument("--fail-fast", action="store_true",
                        help="beim ersten auffaelligen Fall abbrechen")
    parser.add_argument("--no-color", action="store_true", help="ohne Farben ausgeben")


def selected_mode(args: argparse.Namespace) -> str:
    return args.mode_flag or args.mode or "normal"


def mode_at_least(mode: str, required: str) -> bool:
    return RANK[mode] >= RANK[required]


# ==========================================================================
# .env
# ==========================================================================
def load_env_value(env_file: Path, key: str) -> str | None:
    try:
        from dotenv import dotenv_values
        value = dotenv_values(env_file).get(key)
        if value:
            return str(value)
    except ImportError:
        pass

    if not env_file.exists():
        return None
    for raw in env_file.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        current, _, value = line.partition("=")
        if current.strip() == key:
            return value.strip().strip('"').strip("'")
    return None


def mask_secret(value: str) -> str:
    return f"{value[:3]}***{value[-2:]}" if len(value) > 6 else "***"


# ==========================================================================
# Fall
# ==========================================================================
@dataclass(slots=True)
class Case:
    """Ein Testfall.

    expect  : "unauth" 401/403 | "reject" 4xx | "accept" 2xx | "note" nur notieren
    level   : ab welchem Modus der Fall laeuft
    external: True, wenn ein gueltiger Request echte externe Anfragen ausloest
    checks  : was der Fall inhaltlich prueft (erscheint bei Auffaelligkeiten)
    """
    name: str
    expect: str
    section: str = "TESTS"
    body: Any = None
    path: str = ""
    headers: dict = field(default_factory=dict)
    level: str = "normal"
    external: bool = False
    checks: str = ""
    method: str = "POST"


@dataclass(slots=True)
class TestOutcome:
    state: str      # PASS / FAIL / NOTE
    reason: str


@dataclass(slots=True)
class HttpResponse:
    status_code: int
    text: str
    headers: Mapping[str, str]

    def detail(self) -> str:
        """Gibt das FastAPI-detail kompakt zurueck, sonst den Rohtext."""
        try:
            parsed = json.loads(self.text)
        except ValueError:
            return self.text
        if isinstance(parsed, dict) and "detail" in parsed:
            d = parsed["detail"]
            if isinstance(d, list):
                parts = []
                for item in d:
                    if isinstance(item, dict):
                        loc = ".".join(str(x) for x in item.get("loc", [])[1:])
                        parts.append(f"{loc}: {item.get('msg', '')}")
                    else:
                        parts.append(str(item))
                return " | ".join(parts)
            return str(d)
        return json.dumps(parsed, ensure_ascii=False)


# ==========================================================================
# HTTP
# ==========================================================================
def _decode(raw: bytes, headers: Mapping[str, str]) -> str:
    charset = "utf-8"
    for part in headers.get("content-type", "").split(";")[1:]:
        key, sep, value = part.strip().partition("=")
        if sep and key.lower() == "charset" and value.strip():
            charset = value.strip().strip('"')
            break
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def http_call(method: str, url: str, headers: Mapping[str, str],
              body: Any, timeout: float) -> HttpResponse:
    request_headers = dict(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        if not any(k.lower() == "content-type" for k in request_headers):
            request_headers["Content-Type"] = "application/json"

    req = urllib_request.Request(url=url, data=data,
                                 headers=request_headers, method=method.upper())
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            head = {k.lower(): v for k, v in resp.headers.items()}
            return HttpResponse(resp.status, _decode(resp.read(), head), head)
    except urllib_error.HTTPError as exc:
        # 4xx/5xx sind hier normale Antworten und werden bewertet, nicht geworfen.
        head = {k.lower(): v for k, v in exc.headers.items()}
        return HttpResponse(exc.code, _decode(exc.read(), head), head)


# ==========================================================================
# Standardbewertung
# ==========================================================================
def evaluate(status: int, expect: str) -> TestOutcome:
    if expect == "unauth":
        if status in (401, 403):
            return TestOutcome("PASS", f"Auth greift ({status})")
        if status == 404:
            return TestOutcome("FAIL", "404 - Pfad existiert nicht, Auth ungeprueft")
        return TestOutcome("FAIL", f"erwartet 401 · bekommen {status} · Endpoint ungeschuetzt")

    if expect == "reject":
        if status == 404:
            return TestOutcome("FAIL", "404 - Pfad existiert nicht, Validierung ungeprueft")
        if 400 <= status < 500:
            return TestOutcome("PASS", f"korrekt abgelehnt ({status})")
        if status >= 500:
            return TestOutcome("FAIL", f"5xx statt 4xx · Fehler wurde nicht abgefangen ({status})")
        return TestOutcome("FAIL", f"erwartet 4xx · bekommen {status} · angenommen statt abgelehnt")

    if expect == "accept":
        if 200 <= status < 300:
            return TestOutcome("PASS", f"korrekt angenommen ({status})")
        return TestOutcome("FAIL", f"erwartet 2xx · bekommen {status}")

    return TestOutcome("NOTE", f"nur notiert ({status})")


# ==========================================================================
# Ausgabe
# ==========================================================================
class Reporter:
    def __init__(self, suite: str, mode: str, base_url: str, log_file: Path,
                 verbose: bool = False):
        self.suite = suite
        self.mode = mode
        self.base_url = base_url.rstrip("/")
        self.log_file = log_file
        self.verbose = verbose
        self.started = time.perf_counter()
        self.index = 0
        self.passed = self.failed = self.noted = 0
        self.section_name = "-"
        self.rows: list[tuple] = []      # (nr, state, name, section, method, path, reason, checks)
        self.sections: dict[str, list[int]] = {}
        self.durations: list[tuple[float, str]] = []
        log_file.parent.mkdir(parents=True, exist_ok=True)
        self._fh = log_file.open("w", encoding="utf-8")
        self._fh.write(f"{suite} | mode={mode} | started={datetime.now().isoformat()}\n")

    # ------------------------------------------------------------ basis
    def out(self, text: str = "") -> None:
        print(text)
        self._fh.write(ANSI.sub("", text) + "\n")
        self._fh.flush()

    # alte API beibehalten
    def log(self, message: str = "") -> None:
        self.out(message)

    def rule(self, char: str = "─") -> None:
        self.out(C.p(char * 78, C.GREY))

    def banner(self, target: str, script: Path, env_file: Path,
               planned: int = 0, total: int = 0, extra: dict | None = None) -> None:
        self.out()
        self.out(C.p("═" * 78, C.CYAN))
        self.out(C.p(f" {self.suite}", C.BOLD, C.CYAN))
        self.out(C.p("═" * 78, C.CYAN))
        rows = {
            "Ziel": target,
            "Modus": f"{self.mode}  -  {MODE_HELP[self.mode]}",
            "Skript": str(script.resolve()),
            "ENV": str(env_file.resolve()),
            "Log": str(self.log_file.resolve()),
        }
        if extra:
            rows.update(extra)
        for key, value in rows.items():
            self.out(f" {C.p(key.ljust(11), C.GREY)}{value}")
        if total:
            line = f" {C.p('Faelle'.ljust(11), C.GREY)}{planned} von {total}"
            if total - planned:
                line += C.p(f"   ({total - planned} durch Modus/Filter uebersprungen)", C.GREY)
            self.out(line)
        self.rule()

    def section(self, title: str) -> None:
        self.section_name = title
        self.sections.setdefault(title, [])
        self.out()
        self.out(C.p(f"▌ {title}", C.BOLD))

    def info(self, text: str) -> None:
        self.out(C.p(f"  i  {text}", C.BLUE))

    # ------------------------------------------------------------ fall
    def record(self, *, name: str, method: str, url: str, expectation: str,
               headers: Mapping[str, str], request_body: Any,
               outcome: TestOutcome, elapsed: float,
               response: HttpResponse | None = None, error: Exception | None = None,
               header_name: str = "X-Admin-Key", checks: str = "") -> str:
        self.index += 1
        state = outcome.state
        if state == "PASS":
            self.passed += 1
            symbol, color = "✓", C.GREEN
        elif state == "FAIL":
            self.failed += 1
            symbol, color = "✗", C.RED
        else:
            self.noted += 1
            symbol, color = "·", C.YELLOW

        status = str(response.status_code) if response else "---"
        path = url[len(self.base_url):] or "/"
        self.sections.setdefault(self.section_name, []).append(self.index)
        self.rows.append((self.index, state, name, self.section_name,
                          method, path, outcome.reason, checks))
        self.durations.append((elapsed, name))

        self.out(
            f"  {C.p(symbol, color, C.BOLD)} "
            f"{C.p(f'{self.index:03d}', C.GREY)}  "
            f"{name[:44].ljust(44)} "
            f"{C.p(status.rjust(3), color)} "
            f"{C.p(f'{elapsed * 1000:>7.0f}ms', C.GREY)}  "
            f"{C.p(outcome.reason, color if state != 'PASS' else C.RESET)}"
        )

        if state == "FAIL" or self.verbose:
            pad = "         "
            self.out(C.p(f"{pad}{method} {path}", C.GREY))
            if checks:
                self.out(C.p(f"{pad}prueft   {checks}", C.GREY))
            self.out(C.p(f"{pad}auth     {header_name}="
                         f"{'gesetzt' if header_name in headers else 'fehlt'}", C.GREY))
            if request_body is not None:
                self.out(C.p(f"{pad}gesendet {clip(json.dumps(request_body, ensure_ascii=False))}",
                             C.GREY))
            if response is not None:
                self.out(C.p(f"{pad}Antwort  {clip(response.detail())}", C.GREY))
            if error is not None:
                self.out(C.p(f"{pad}Fehler   {type(error).__name__}: {error}", C.RED))
        return state

    # ------------------------------------------------------------ ende
    def summary(self) -> int:
        elapsed = time.perf_counter() - self.started
        total = self.passed + self.failed + self.noted

        self.out()
        self.out(C.p("═" * 78, C.CYAN))
        self.out(C.p(" ERGEBNIS", C.BOLD, C.CYAN))
        self.rule()
        self.out(C.p(f" {'Abschnitt'.ljust(40)}{'ok'.rjust(6)}"
                     f"{'auffaellig'.rjust(12)}{'notiert'.rjust(10)}{'gesamt'.rjust(9)}", C.GREY))

        by_index = {row[0]: row for row in self.rows}
        for name, indexes in self.sections.items():
            if not indexes:
                continue
            states = [by_index[i][1] for i in indexes]
            a = states.count("PASS"); b = states.count("FAIL"); n = states.count("NOTE")
            self.out(f" {name[:40].ljust(40)}"
                     f"{C.p(str(a).rjust(6), C.GREEN if a else C.GREY)}"
                     f"{C.p(str(b).rjust(12), C.RED if b else C.GREY)}"
                     f"{C.p(str(n).rjust(10), C.YELLOW if n else C.GREY)}"
                     f"{str(a + b + n).rjust(9)}")
        self.rule()
        self.out(f" {C.p('Gesamt'.ljust(40), C.BOLD)}"
                 f"{C.p(str(self.passed).rjust(6), C.GREEN, C.BOLD)}"
                 f"{C.p(str(self.failed).rjust(12), C.RED if self.failed else C.GREY, C.BOLD)}"
                 f"{C.p(str(self.noted).rjust(10), C.YELLOW if self.noted else C.GREY)}"
                 f"{str(total).rjust(9)}")

        if self.durations:
            slowest, slow_name = max(self.durations)
            average = sum(d for d, _ in self.durations) / len(self.durations)
            self.out(f" {C.p('Dauer'.ljust(40), C.GREY)}{elapsed:.1f}s gesamt, "
                     f"{average * 1000:.0f}ms im Schnitt, langsamster "
                     f"{slowest * 1000:.0f}ms ({clip(slow_name, 40)})")
        self.out(f" {C.p('Modus'.ljust(40), C.GREY)}{self.mode}")
        self.out(f" {C.p('Log'.ljust(40), C.GREY)}{self.log_file.resolve()}")

        if self.failed:
            self.out()
            self.out(C.p(" AUFFAELLIG", C.RED, C.BOLD))
            for nr, state, name, section, method, path, reason, checks in self.rows:
                if state != "FAIL":
                    continue
                self.out(C.p(f"  ✗ {nr:03d}  {name}", C.RED))
                self.out(C.p(f"         {section} · {method} {path}", C.GREY))
                self.out(C.p(f"         {reason}", C.GREY))
                if checks:
                    self.out(C.p(f"         prueft {checks}", C.GREY))

        if self.noted:
            self.out()
            self.out(C.p(" NOTIERT - dokumentiertes Verhalten, nicht bewertet", C.YELLOW))
            for nr, state, name, section, method, path, reason, checks in self.rows:
                if state == "NOTE":
                    self.out(C.p(f"  · {nr:03d}  {section} · {name}  →  {reason}", C.GREY))

        self.out()
        if self.failed == 0:
            self.out(C.p(" OK - kein bewerteter Fall weicht ab.", C.GREEN, C.BOLD))
        else:
            self.out(C.p(f" {self.failed} von {total} Faellen weichen ab.", C.RED, C.BOLD))
        self.out()
        self._fh.close()
        return 0 if self.failed == 0 else 1


def clip(text: Any, limit: int = 300) -> str:
    text = str(text).replace("\r", "\\r").replace("\n", "\\n")
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[:limit]} … (+{len(text) - limit} Zeichen)"


# ==========================================================================
# Ausfuehrung
# ==========================================================================
def perform_request(reporter: Reporter, *, name: str, method: str, url: str,
                    headers: Mapping[str, str], expectation: str,
                    evaluator: Callable[[int, str, str], TestOutcome] | None = None,
                    body: Any = None, timeout: float = 10.0,
                    header_name: str = "X-Admin-Key", checks: str = "") -> str:
    started = time.perf_counter()
    try:
        response = http_call(method, url, headers, body, timeout)
        elapsed = time.perf_counter() - started
        outcome = (evaluator(response.status_code, expectation, response.text)
                   if evaluator else evaluate(response.status_code, expectation))
        return reporter.record(name=name, method=method, url=url, expectation=expectation,
                               headers=headers, request_body=body, outcome=outcome,
                               elapsed=elapsed, response=response,
                               header_name=header_name, checks=checks)
    except (socket.timeout, TimeoutError) as exc:
        elapsed = time.perf_counter() - started
        outcome = TestOutcome("FAIL", f"Timeout nach {timeout:g}s - keine Antwort")
        return reporter.record(name=name, method=method, url=url, expectation=expectation,
                               headers=headers, request_body=body, outcome=outcome,
                               elapsed=elapsed, error=exc, header_name=header_name, checks=checks)
    except urllib_error.URLError as exc:
        elapsed = time.perf_counter() - started
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            outcome = TestOutcome("FAIL", f"Timeout nach {timeout:g}s - keine Antwort")
        else:
            outcome = TestOutcome("FAIL", "Server nicht erreichbar")
        return reporter.record(name=name, method=method, url=url, expectation=expectation,
                               headers=headers, request_body=body, outcome=outcome,
                               elapsed=elapsed, error=exc, header_name=header_name, checks=checks)
    except Exception as exc:
        elapsed = time.perf_counter() - started
        outcome = TestOutcome("FAIL", "unerwarteter Fehler im Test selbst")
        return reporter.record(name=name, method=method, url=url, expectation=expectation,
                               headers=headers, request_body=body, outcome=outcome,
                               elapsed=elapsed, error=exc, header_name=header_name, checks=checks)


def select_cases(cases: list[Case], mode: str, args: argparse.Namespace) -> list[Case]:
    """Filtert nach Modus, --only und externem Traffic."""
    allow_external = args.allow_external or mode == "intense"
    out = []
    for case in cases:
        if not mode_at_least(mode, case.level):
            continue
        if case.external and not allow_external:
            continue
        if args.only and args.only.lower() not in case.name.lower():
            continue
        out.append(case)
    return out


def check_server(reporter: Reporter, base_url: str, headers: Mapping[str, str],
                 timeout: float = 5.0) -> bool:
    try:
        response = http_call("GET", base_url.rstrip("/") + "/health", headers, None, timeout)
        text = (C.p(f"erreichbar (HTTP {response.status_code})", C.GREEN)
                if response.status_code < 400
                else C.p(f"antwortet mit HTTP {response.status_code}", C.YELLOW))
        reporter.out(f" {C.p('Server'.ljust(11), C.GREY)}{text}")
        return response.status_code < 400
    except Exception as exc:
        reporter.out(f" {C.p('Server'.ljust(11), C.GREY)}"
                     f"{C.p('nicht erreichbar - laeuft er?', C.RED)}  ({type(exc).__name__})")
        return False


def run_suite(reporter: Reporter, base_url: str, cases: list[Case],
              default_path: str, valid_headers: dict, args: argparse.Namespace,
              timeout: float, pause: float, sections: dict[str, str] | None = None) -> None:
    """Fuehrt die Faelle aus und gruppiert sie nach ihrem Abschnitt."""
    grouped: dict[str, list[Case]] = {}
    for case in cases:
        grouped.setdefault(case.section, []).append(case)

    for section_name, section_cases in grouped.items():
        reporter.section(section_name)
        for case in section_cases:
            url = base_url.rstrip("/") + (case.path or default_path)
            headers = case.headers if case.expect == "unauth" else valid_headers
            perform_request(reporter, name=case.name, method=case.method, url=url,
                            headers=headers, expectation=case.expect, body=case.body,
                            timeout=timeout, checks=case.checks)
            if args.fail_fast and reporter.rows and reporter.rows[-1][1] == "FAIL":
                reporter.out(C.p("\n  Abbruch wegen --fail-fast.", C.RED))
                return
            if pause:
                time.sleep(pause)
