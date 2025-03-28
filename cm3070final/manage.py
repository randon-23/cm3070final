#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import environ


def main():
    """Run administrative tasks."""

    # Initialize environment variables
    env = environ.Env()
    environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "volontera.settings.prod" if env("DJANGO_ENV", default="development") == "production" else "volontera.settings.dev"
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
