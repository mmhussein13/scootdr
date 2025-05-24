"""
Entry point for Replit to serve our Django application.
This file imports the WSGI application from the Django project.
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scooterrentals.settings')

from scooterrentals.wsgi import application as app