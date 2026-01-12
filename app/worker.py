from app.tasks.monitoring import celery_app
from app.core.config import settings

if __name__ == "__main__":
    celery_app.start()