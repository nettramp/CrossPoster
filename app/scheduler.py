import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.tasks.monitoring import check_vk_posts, check_telegram_posts, check_instagram_posts, repost_to_telegram
from app.core.config import settings
import logging
import pytz

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация планировщика
scheduler = AsyncIOScheduler(timezone=pytz.UTC)

@scheduler.scheduled_job(IntervalTrigger(minutes=1))
async def check_all_social_media():
    """Проверить все социальные сети на наличие новых постов"""
    logger.info("Starting social media check...")
    
    # TODO: Получить список активных аккаунтов из базы данных
    # TODO: Для каждого аккаунта запустить соответствующую задачу проверки
    
    # Пример запуска задач для проверки (нужно заменить на реальные данные из БД)
    # check_vk_posts.delay(account_id, access_token, owner_id)
    # check_telegram_posts.delay(account_id, bot_token, chat_id)
    # check_instagram_posts.delay(account_id, username, password, user_id)
    
    logger.info("Social media check completed")

if __name__ == "__main__":
    # Запуск планировщика
    scheduler.start()
    logger.info("Scheduler started")
    
    try:
        # Держим приложение запущенным
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
        scheduler.shutdown()