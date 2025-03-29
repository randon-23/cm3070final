#!/bin/bash

echo "Starting Celery..."
celery -A volontera worker --loglevel=INFO &

# Start Nginx (media server) in the background
echo "Starting Nginx..."
nginx


# Start Daphne (application) in the foreground
echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8000 volontera.asgi:application