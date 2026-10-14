#!/bin/bash

# Start Server Script für Linux
# Startet den FastAPI Server mit Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Starte PyScrapper Server mit Docker Compose..."
docker-compose -f docker/compose.yaml up