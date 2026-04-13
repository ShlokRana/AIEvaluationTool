#!/bin/bash

# Auth Service Runner
echo "Starting Auth Service..."

# Set environment variables (must match TDMS verifier keys)
export AUTH_SECRET_KEY="${AUTH_SECRET_KEY:-@cerai}"
export AUTH_REFRESH_SECRET_KEY="${AUTH_REFRESH_SECRET_KEY:-@cerai_refresh}"

# Database configuration
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-3306}"
export DB_USER="${DB_USER:-root}"
export DB_PASSWORD="${DB_PASSWORD:-}"
export DB_NAME="${DB_NAME:-aievaluation}"

# Run the service
python main.py