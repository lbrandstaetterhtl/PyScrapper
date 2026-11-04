ocr - Captcha-Erkennung fuer den Bandcamp-Provider
==================================================

Rust-Erweiterung fuer Python. Python importiert sie als "ocr" und ruft eine
Funktion auf:

    import ocr
    kandidaten = ocr.img_to_text("captcha.jpeg", "PythonModule/providers/ocr")

Zurueck kommt eine Liste mit bis zu max_candidates (aktuell 3) Strings, der
wahrscheinlichste zuerst. Fehler kommen als ValueError.

Ohne dieses Modul startet der Server nicht: providers/Bandcamp/bandcamp_search.py
importiert es beim Laden, und providers/__init__.py laedt alle Provider.

Ausfuehrliche Doku: HTML_Doku/CaptchaOCR.html im Repository-Root.


Was wo liegt
------------

  captcha_ocr_source/            Dieser Ordner: der Rust-Code (src/), Cargo.toml,
                                 pyproject.toml fuer maturin, test.py
  PythonModule/providers/ocr/    Modellordner (ocr_dir): config.json,
                                 model.safetensors und ein fertiges Windows-Wheel
  LocalServer/docker/Dockerfile  Baut das Modul in der ersten Stufe gleich mit

Das Wheel enthaelt nur den Code. Das Modell wird zur Laufzeit aus ocr_dir
geladen. Fehlt model.safetensors dort, gibt es KEINE Fehlermeldung, das Netz
rechnet dann mit Zufallsgewichten und liefert Unsinn.


Variante 1: Windows, fertiges Wheel (kein Rust noetig)
======================================================

# Im Repository-Root, mit aktiviertem venv des Servers:
pip install --force-reinstall PythonModule\providers\ocr\ocr-0.1.0-cp39-abi3-win_amd64.whl

# Pruefen:
python -c "import ocr; print(ocr.img_to_text)"

Das Wheel laeuft mit jedem Python ab 3.9 (abi3), aber nur auf Windows x64.


Variante 2: Linux (Ubuntu/Debian) ohne Docker
=============================================

--- Einmalig: Werkzeuge ---------------------------------

# Compiler, Python-Header und venv-Unterstuetzung installieren.
sudo apt install -y build-essential python3-dev python3-venv curl

# Rust installieren (wird nur zum Bauen gebraucht).
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal

# Rust in der aktuellen Shell verfuegbar machen.
source "$HOME/.cargo/env"


--- venv anlegen und Abhaengigkeiten installieren -------

cd ~/PyScrapper

# venv anlegen (nur beim ersten Mal noetig) und aktivieren.
python3 -m venv .venv
source .venv/bin/activate

# PyScrapper-Abhaengigkeiten und maturin (Build-Tool fuer Rust-Python-Pakete).
pip install -r LocalServer/requirements.txt
pip install --upgrade pip maturin


--- Bauen und installieren (Kurzweg) --------------------

# Baut und installiert direkt in das aktive venv, ohne .whl-Datei.
# Der erste Build dauert einige Minuten (candle, image).
cd ~/PyScrapper/LocalServer/docker/captcha_ocr_source
maturin develop --release


--- Alternativ: als .whl-Datei bauen --------------------

cd ~/PyScrapper/LocalServer/docker/captcha_ocr_source

# Alte Builds entfernen, damit sicher die neue .whl installiert wird.
rm -f target/wheels/*.whl

# Wheel bauen. Name: ocr-0.1.0-cp39-abi3-<plattform>.whl
maturin build --release
ls target/wheels/

# In das aktive venv installieren (ueberschreibt eine alte Version).
pip install --force-reinstall target/wheels/ocr-*.whl


--- Pruefen ---------------------------------------------

python -c "import ocr; print(ocr.img_to_text)"


--- Nach Aenderungen am Rust-Code -----------------------

# Erneut bauen (maturin develop --release oder Wheel neu bauen und
# installieren), danach den Server neu starten, z.B.:
sudo systemctl restart pyscrapper


Variante 3: Windows, selbst bauen
=================================

Nur noetig, wenn der Rust-Code geaendert wurde. Voraussetzungen: Rust ueber
https://rustup.rs und die "Visual Studio Build Tools" (C++-Workload).

# PowerShell, im aktivierten venv des Servers:
pip install --upgrade maturin
Set-Location LocalServer\docker\captcha_ocr_source
maturin develop --release

# Oder als Wheel, z.B. um das Wheel im Repository zu ersetzen:
maturin build --release
pip install --force-reinstall (Get-ChildItem target\wheels\ocr-*.whl | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
Copy-Item target\wheels\ocr-*.whl ..\..\..\PythonModule\providers\ocr\


Variante 4: Docker
==================

Das Server-Image baut das Modul in einer eigenen Stufe (Rust + maturin) und
installiert nur das fertige Wheel. Rust landet nicht im finalen Image.

cd ~/PyScrapper/LocalServer/docker
docker compose up -d --build

Kurzform zum Aktualisieren:
cd ~/PyScrapper && git pull && cd LocalServer/docker && docker compose up -d --build


Testen
======

test.py liest ein einzelnes Captcha und gibt die Kandidaten und die Laufzeit aus:

python test.py captcha.jpeg --ocr-dir ../../../PythonModule/providers/ocr

Ohne --ocr-dir wird die Umgebungsvariable OCR_DIR genommen, sonst ein fest
eingetragener Pfad vom Rechner des Autors. -n begrenzt die Ausgabe, mehr als
max_candidates Kandidaten liefert das Modul aber nie.


Haeufige Fehler
===============

ModuleNotFoundError: No module named 'ocr'
    Das Modul ist nicht in dem Python installiert, mit dem der Server laeuft.
    Mit genau diesem Interpreter "python -c "import ocr"" pruefen.

"... is not a supported wheel on this platform"
    Das Windows-Wheel auf Linux/macOS oder auf ARM. Selbst bauen (Variante 2).

Kandidaten sehen zufaellig aus
    model.safetensors wurde nicht gefunden (falscher ocr_dir oder model_name
    in config.json). Das Netz laeuft dann ohne trainierte Gewichte.

"Model returns N classes, vocab has M characters"
    vocab_str in config.json passt nicht zum trainierten Modell.

"unknown device" / Fehler bei cuda oder metal
    device in config.json auf "cpu" lassen. cuda und metal brauchen candle
    mit den passenden Features, die in Cargo.toml nicht aktiviert sind.

Ergebnis hat immer einen Buchstaben zu wenig
    Zwei Buchstaben beruehren sich im Captcha und werden als einer erkannt.
    Die Schwellwerte stehen in src/lib.rs (siehe HTML-Doku, "image to letters").
