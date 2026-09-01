"""Alle PyScrapper-Test-Suites mit einem gemeinsamen Modus starten.

    python run_tests.py quick
    python run_tests.py normal
    python run_tests.py intense --base-url http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_common import C, MODES, MODE_HELP, enable_colors  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
SUITES = [("Download", "download_tests.py", "download_endpoint_test.log"),
          ("Search", "search_tests.py", "search_endpoint_test.log"),
          ("CRUD", "create_delete_tests.py", "crud_endpoint_test.log")]

COUNT_RE = re.compile(r"^\s*Gesamt\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$", re.M)


def counts_from_log(path: Path):
    if not path.exists():
        return None
    match = COUNT_RE.search(path.read_text(encoding="utf-8", errors="replace"))
    return tuple(int(x) for x in match.groups()) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Alle Endpoint-Tests ausfuehren")
    parser.add_argument("mode", nargs="?", choices=MODES, default="normal")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--allow-external", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    enable_colors(args.no_color)

    print()
    print(C.p("═" * 78, C.CYAN))
    print(C.p(f" PyScrapper · alle Endpoint-Tests · Modus {args.mode}", C.BOLD, C.CYAN))
    print(C.p(f" {MODE_HELP[args.mode]}", C.GREY))
    print(C.p(f" Ziel {args.base_url}", C.GREY))
    print(C.p("═" * 78, C.CYAN))

    results = []
    started = time.perf_counter()
    for label, script, log_name in SUITES:
        command = [sys.executable, str(TESTS_DIR / script), args.mode,
                   "--base-url", args.base_url]
        if args.verbose:
            command.append("--verbose")
        if args.allow_external:
            command.append("--allow-external")
        if args.no_color:
            command.append("--no-color")
        begin = time.perf_counter()
        code = subprocess.call(command, cwd=TESTS_DIR)
        results.append((label, code, time.perf_counter() - begin,
                        counts_from_log(TESTS_DIR / log_name)))

    print()
    print(C.p("═" * 78, C.CYAN))
    print(C.p(" GESAMTERGEBNIS", C.BOLD, C.CYAN))
    print(C.p("─" * 78, C.GREY))
    print(C.p(f" {'Suite'.ljust(14)}{'Status'.ljust(24)}{'ok'.rjust(6)}"
              f"{'auffaellig'.rjust(12)}{'notiert'.rjust(10)}{'Dauer'.rjust(10)}", C.GREY))

    total_bad = 0
    for label, code, duration, counts in results:
        if code == 0:
            state = C.p("alles wie erwartet", C.GREEN)
        elif code == 1:
            state = C.p("Auffaelligkeiten", C.RED)
        else:
            state = C.p("nicht ausgefuehrt", C.YELLOW)
        if counts:
            ok, bad, note, _ = counts
            total_bad += bad
            numbers = (C.p(str(ok).rjust(6), C.GREEN if ok else C.GREY)
                       + C.p(str(bad).rjust(12), C.RED if bad else C.GREY)
                       + C.p(str(note).rjust(10), C.YELLOW if note else C.GREY))
        else:
            numbers = C.p("-".rjust(6) + "-".rjust(12) + "-".rjust(10), C.GREY)
        pad = 24 + (len(state) - len(re.sub(r"\033\[[0-9;]*m", "", state)))
        print(f" {label.ljust(14)}{state.ljust(pad)}{numbers}"
              f"{C.p(f'{duration:.1f}s'.rjust(10), C.GREY)}")

    print(C.p("─" * 78, C.GREY))
    print(f" {'Dauer'.ljust(14)}{time.perf_counter() - started:.1f}s")
    worst = max(code for _, code, _, _ in results)
    if worst == 0:
        print(C.p("\n Alle Suiten ohne Auffaelligkeit.\n", C.GREEN, C.BOLD))
    else:
        print(C.p(f"\n {total_bad} auffaellige Faelle insgesamt - Details oben.\n",
                  C.RED, C.BOLD))
    sys.exit(worst)


if __name__ == "__main__":
    main()
