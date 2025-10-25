#!/bin/bash
# Simple script to run Physica service with venv

cd "$(dirname "$0")/service"
# Use --debug by default for development (uses session D-Bus bus)
exec ../venv/bin/python -u main.py --debug "$@"

