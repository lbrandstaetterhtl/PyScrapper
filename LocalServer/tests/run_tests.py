"""Alle PyScrapper-Test-Suites mit einem gemeinsamen Modus starten."""
from __future__ import annotations
import argparse, subprocess, sys, time
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SUITES = ["download_tests.py", "search_tests.py", "create_delete_tests.py"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Alle Endpoint-Tests ausfuehren")
    parser.add_argument("mode", nargs="?", choices=("quick", "normal", "intense"), default="normal")
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    args = parser.parse_args()
    print(f"=== PyScrapper test run | mode={args.mode} | base-url={args.base_url} ===", flush=True)
    started = time.perf_counter()
    results = []
    for suite in SUITES:
        path = TESTS_DIR / suite
        print(f"\n>>> {suite} [{args.mode}]", flush=True)
        result = subprocess.run([sys.executable, str(path), args.mode, "--base-url", args.base_url], cwd=TESTS_DIR)
        results.append((suite, result.returncode))
    print("\n=== OVERALL SUMMARY ===", flush=True)
    for suite, code in results:
        state = "PASS" if code == 0 else "ABORT" if code == 2 else "FAIL"
        print(f"[{state:<5}] {suite} | exit={code}")
    failed = sum(code != 0 for _, code in results)
    print(f"TOTAL={len(results)} | OK={len(results)-failed} | FAILED/ABORTED={failed} | duration={time.perf_counter()-started:.2f}s")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
