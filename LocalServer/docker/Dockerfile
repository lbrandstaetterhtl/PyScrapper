FROM python:3.11-slim

WORKDIR /app

# Installiere System Dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Kopiere Requirements
COPY requirements.txt .

# Installiere Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Projekt
COPY . .

# Expose Port
EXPOSE 8000

# Starte Server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]