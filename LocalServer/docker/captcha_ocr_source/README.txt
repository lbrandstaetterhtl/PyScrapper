captcha_ocr bauen und in die venv installieren (Ubuntu) OHNE DOCKER
========================================================

--- Einmalig: Werkzeuge ---------------------------------

# Compiler, Python-Header und venv-Unterstuetzung installieren.
sudo apt install -y build-essential python3-dev python3-venv curl

# Rust installieren (wird zum Bauen gebraucht).
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal

# Rust in der aktuellen Shell verfuegbar machen.
source "$HOME/.cargo/env"


--- venv anlegen und maturin installieren ---------------

# In das Projekt wechseln.
cd ~/PyScrapper

# venv anlegen (nur beim ersten Mal noetig).
python3 -m venv .venv

# venv aktivieren
source .venv/bin/activate

# PyScrapper-Abhaengigkeiten in die venv installieren.
cd ~/PyScrapper
pip install -r LocalServer/requirements.txt

# maturin (Build-Tool fuer Rust-Python-Pakete) in die venv installieren.
pip install --upgrade pip maturin


--- Paket bauen -----------------------------------------

# In den Ordner mit der Cargo.toml wechseln.
cd ~/PyScrapper/LocalServer/docker/captcha_ocr_source

# Alte Builds entfernen, damit spaeter sicher die neue .whl installiert wird.
rm -f target/wheels/*.whl

# Paket als .whl bauen (dauert beim ersten Mal einige Minuten).
maturin build --release

# Pruefen, dass die .whl entstanden ist.
ls target/wheels/


--- In die venv installieren ----------------------------

# Gebaute .whl in die aktive venv installieren (ueberschreibt alte Version).
pip install --force-reinstall target/wheels/captcha_ocr-*.whl

# Testen, ob das Paket importiert werden kann.
python -c "import captcha_ocr; print(captcha_ocr.img_to_text)"


--- Kurzweg (bauen + installieren in einem Schritt) -----

# Baut und installiert direkt in die aktive venv, ohne .whl-Datei.
cd ~/PyScrapper/LocalServer/docker/captcha_ocr_source && maturin develop --release


--- Nach Aenderungen am Rust-Code -----------------------

# Ab "Paket bauen" wiederholen, danach den Server neu starten.
sudo systemctl restart pyscrapper


captcha_ocr bauen und in die venv installieren (Ubuntu) MIT DOCKER
========================================================


--- Bauen und starten -----------------------------------
 
# In den Ordner mit der compose.yaml wechseln.
cd ~/PyScrapper/LocalServer/docker
 
# Image bauen (inkl. captcha_ocr) und Container im Hintergrund starten.
docker compose up -d --build


SCHNELLLLLLLLLLLL!!!!!!!
cd ~/PyScrapper && git pull && cd LocalServer/docker && docker compose up -d --build