# import necessary libraries
from celery import Celery  # import the celery class for task management
import logging  # import the logging module for logging configuration

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # create a logger instance with the current module's name


# create a celery application instance
celery_app = Celery(
    __name__,  
    broker='amqp://guest:guest@rabbitmq:5672//',  # rabbitmq message broker configuration
    backend='rpc://',  # result backend configuration using rpc
    include=['tasks']  # list of modules to include for tasks
)

# you can also add other celery configurations here
celery_app.conf.update(
    task_serializer='json',  
    accept_content=['json'],  
    result_serializer='json',  
    timezone='europe/london',  
    enable_utc=True,
)

celery_app.log.setup_task_loggers() # ensure the logger is configured for use in celery tasks

__all__ = ['celery_app', 'logger']  # export 'celery_app' and 'logger' for use in other modules
