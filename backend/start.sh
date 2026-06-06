#!/bin/sh
set -e

echo "==> Running database migrations …"
python migrate.py

echo "==> Seeding tournament matches …"
python -m app.seed.seeder

echo "==> Starting server …"
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
