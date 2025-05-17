#!/bin/bash

# Exit on any error
set -e

echo "Starting deployment process..."

# Install only core Django dependencies instead of all requirements to speed up deployment
echo "Installing minimal Python dependencies for Django..."
/nix/store/wqhkxzzlaswkj3gimqign99sshvllcg6-python-wrapped-0.1.0/bin/python -m pip install Django==5.2 django-bootstrap4 django-crispy-forms django-widget-tweaks python-dotenv psycopg2-binary

# Check if package.json exists and install dependencies if it does
if [ -f package.json ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Apply database migrations for full functionality
echo "Applying database migrations..."
/nix/store/wqhkxzzlaswkj3gimqign99sshvllcg6-python-wrapped-0.1.0/bin/python manage.py migrate

# This is a Django application as identified in the source files
echo "Starting Django application on port 5000..."
/nix/store/wqhkxzzlaswkj3gimqign99sshvllcg6-python-wrapped-0.1.0/bin/python manage.py runserver 0.0.0.0:5000

echo "Deployment completed!"