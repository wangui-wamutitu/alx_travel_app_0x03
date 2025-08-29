import os
from celery import Celery

# Set the default Django settings module 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

app = Celery('alx_travel_app')

# Configure Celery to use RabbitMQ as the broker
# Default RabbitMQ credentials: guest/guest on localhost:5672
app.conf.broker_url = "amqp://guest:guest@localhost:5672//"


# Load custom config from Django settings (keys prefixed with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
