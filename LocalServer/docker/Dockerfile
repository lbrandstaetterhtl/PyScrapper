FROM python:3.11-slim

WORKDIR /app

# Installiere System Dependencies
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

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