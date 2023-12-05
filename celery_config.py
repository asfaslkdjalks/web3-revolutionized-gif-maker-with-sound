from celery import Celery
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

celery_app = Celery(
    __name__,
    broker='amqp://guest:guest@rabbitmq:5672//',
    backend='rpc://',
    include=['tasks']
)

# You can also add other Celery configurations here
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone='Europe/London',
    enable_utc=True,
)

# Ensure the logger is configured for use in Celery tasks
celery_app.log.setup_task_loggers()

# Export the logger so it can be imported in other modules
__all__ = ['celery_app', 'logger']