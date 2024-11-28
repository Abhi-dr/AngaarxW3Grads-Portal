import os
import io
import django
from django.core.management import call_command

# Step 1: Set DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')  # Replace 'your_project_name' with your Django project name

# Step 2: Setup Django
django.setup()

# Step 3: Dump Data
with io.open('data.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', '--natural-primary', '--natural-foreign', '--indent', '4', stdout=f)
