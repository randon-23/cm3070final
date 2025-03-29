#!/bin/bash

# Start Daphne in background
echo "Starting Daphne..."
daphne -b 0.0.0.0 -p 8001 volontera.asgi:application &

# Start Celery in background
echo "Starting Celery..."
celery -A volontera worker --loglevel=INFO &

# Start NGINX in foreground (takes over as PID 1)
echo "Starting NGINX..."
exec nginx -g "daemon off;"