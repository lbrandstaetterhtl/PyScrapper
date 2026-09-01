PyScrapper Endpoint-Tests
=========================

Alle Suites:
  python run_tests.py quick
  python run_tests.py normal
  python run_tests.py intense

Einzelne Suite:
  python download_tests.py quick
  python search_tests.py normal
  python create_delete_tests.py intense

--mode ist ebenfalls erlaubt:
  python download_tests.py --mode intense


Modi
----
  quick    Auth und die wichtigsten Schemafaelle - wenige Sekunden
  normal   Auth und vollstaendige Eingabepruefung - Standard
  intense  zusaetzlich Grenzwerte, Pfade, Unicode und Lastfaelle


Optionen
--------
  --base-url http://127.0.0.1:8765   Zielserver
  --verbose / -v                     Detailblock zu jedem Fall, nicht nur zu Fehlern
  --only TEXT                        nur Faelle, deren Name TEXT enthaelt
  --allow-external                   auch Faelle, die echte Suchanfragen ausloesen
                                     (in intense automatisch aktiv)
  --fail-fast                        beim ersten auffaelligen Fall abbrechen
  --no-color                         ohne Farben
  --endpoint /pfad                   nur download_tests.py und search_tests.py


Ausgabe
-------
Eine Zeile pro Fall:

  ✓ 004  leerer Body                     422     25ms  korrekt abgelehnt (422)
  ✗ 013  unbekannter Provider            500    192ms  5xx statt 4xx
         POST /search
         prueft   kein Alias trifft zu - erwartet wird 4xx, nicht 5xx
         auth     X-Admin-Key=gesetzt
         gesendet {"provider":"totallynotaprovider","search":"test",...}
         Antwort  Invalid provider was given

  ✓ = wie erwartet    ✗ = auffaellig    · = notiert, nicht bewertet

Der Detailblock erscheint nur bei ✗ - oder bei allen Faellen mit --verbose.
Am Ende steht eine Tabelle pro Abschnitt, danach alle Auffaelligkeiten und
alle Notizen noch einmal einzeln. Das Logfile enthaelt dasselbe ohne Farben.


Bodies entsprechen den echten Modellen
--------------------------------------
  /download/video-audio   provider, urls[], filenames[], download_strategie,
                          preferred_type, preferred_file, extra_headers,
                          download_path, auto_convert
  /search                 provider, search, top, filters{creator, tags[]}
  /create/downloadedmedia media_type  (nicht mediatype)

Die frueheren Felder url / filename / mediatype gibt es in keinem Modell.


Abhaengigkeiten
---------------
Keine. Die Tests nutzen urllib aus der Standardbibliothek.
python-dotenv ist optional; ohne das Paket wird die .env direkt gelesen.


Projektstruktur
---------------
  PyScrapper/.env                    ADMIN_KEY
  PyScrapper/LocalServer/tests/*.py  diese Dateien

PROJECT_ROOT wird aus __file__ bestimmt, ADMIN_KEY aus PyScrapper/.env gelesen.
serach_tests.py bleibt als Wrapper erhalten; die Datei heisst search_tests.py.
