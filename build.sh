#!/usr/bin/env bash
# Build command para Render (Settings > Build Command: ./build.sh).
# Render no tiene fase "release" como Heroku/Railway, así que collectstatic
# y migrate tienen que correr acá, antes de que el Start Command levante gunicorn.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
