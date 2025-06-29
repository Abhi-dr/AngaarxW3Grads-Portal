# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')

# Create Celery instance
app = Celery('angaar_hai')

# Load settings from Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks in Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
