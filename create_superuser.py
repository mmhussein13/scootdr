
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
