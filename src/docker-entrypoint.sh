#!/bin/bash

# Apply database migrations
poetry run python manage.py migrate

# Run API
poetry run gunicorn --bind 0.0.0.0:80 sample.wsgi
