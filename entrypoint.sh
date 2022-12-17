#!/bin/ash

set -e

echo Running migrations
alembic upgrade head

echo Running app
python3 server.py
