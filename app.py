"""
Direct server to run the Django application on Replit.
"""

import os
import sys
import subprocess

# Set up environment variables
os.environ['DJANGO_SECRET_KEY'] = 'django-insecure-temporary-key-for-deployment-purposes-only'
os.environ['DATABASE_URL'] = 'sqlite:///database.db'

def main():
    # Set up the database first
    try:
        print("Setting up database...")
        subprocess.run([sys.executable, "manage.py", "migrate"], 
                      check=True)
        print("Database migrations applied")
        
        # Try to create a superuser if one doesn't exist
        print("Checking if a superuser exists...")
        create_superuser_script = """
import os
os.environ['DJANGO_SECRET_KEY'] = 'django-insecure-temporary-key-for-deployment-purposes-only'
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created: username=admin, password=admin123")
else:
    print("Superuser already exists")
"""
        with open("create_superuser.py", "w") as f:
            f.write(create_superuser_script)
        
        subprocess.run([sys.executable, "create_superuser.py"])
    except Exception as e:
        print(f"Error during setup: {e}")
    
    # Run the Django development server directly
    print("Starting Django server on 0.0.0.0:5000...")
    subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:5000"])

if __name__ == '__main__':
    main()