PyScrapper endpoint tests
========================

Alle Suites:
  python run_tests.py quick
  python run_tests.py normal
  python run_tests.py intense

Einzelne Suite:
  python download_tests.py quick
  python search_tests.py normal
  python create_delete_tests.py intense

Alternativ ist auch --mode erlaubt:
  python download_tests.py --mode intense

Optionen:
  --base-url http://127.0.0.1:8765
  download_tests.py zusaetzlich: --endpoint /download
  search_tests.py zusaetzlich:   --endpoint /search

Modi:
  quick   = Auth + wichtigste Schema-/Security-Checks
  normal  = volle bisherige Negativtest-Abdeckung
  intense = normal + weitere Grenz-, Typ-, Pfad- und Security-Faelle

Output:
  [PASS] / [FAIL] / [NOTE]
  Testnummer, Name, Methode, URL, Erwartung, HTTP-Status, Laufzeit,
  Grund, Auth-Status, Request, Content-Type und Response-Preview.

Hinweis:
  serach_tests.py bleibt als Compatibility-Wrapper erhalten.
  Die eigentliche Datei heisst jetzt korrekt search_tests.py.

Abhaengigkeiten:
  Keine externen HTTP-Pakete notwendig. Die Tests verwenden urllib aus der Python-Standardbibliothek.
  python-dotenv ist optional; ohne das Paket wird .env direkt eingelesen.


Projektstruktur:
  PyScrapper/.env
  PyScrapper/LocalServer/tests/*.py

Die Tests bestimmen PROJECT_ROOT automatisch aus __file__ und lesen ADMIN_KEY aus PyScrapper/.env.
