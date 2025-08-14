#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be available
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run Django migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Start the main Gunicorn process
exec "$@"
