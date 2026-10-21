
 # ---------- Stufe 1: captcha_ocr bauen ----------
FROM python:3.11-slim AS captcha-build
    
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*
    
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"
    
RUN pip install --no-cache-dir maturin
    
WORKDIR /build
COPY LocalServer/docker/captcha_ocr_source/ .
RUN maturin build --release --out /wheels
    
    
    # ---------- Stufe 2: PyScrapper ----------
FROM python:3.11-slim
    
WORKDIR /app
    
    # Installiere System Dependencies
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# captcha_ocr aus Stufe 1 installieren
COPY --from=captcha-build /wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

# Kopiere gesamtes PyScrapper Projekt
COPY . .

# Installiere Python Dependencies
RUN pip install --no-cache-dir -r LocalServer/requirements.txt

# Setze Workdir auf LocalServer
WORKDIR /app/LocalServer

# Expose Port
EXPOSE 8000

# Starte Server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]