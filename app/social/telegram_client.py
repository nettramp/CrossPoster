from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, List, Optional
import asyncio

class TelegramClient:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)

    async def get_latest_posts(self, chat_id: str, limit: int = 10) -> List[Dict]:
        """
        Получить последние обновления из Telegram канала/чата.

        Примечание: Bot API не предоставляет прямого метода для получения истории
        сообщений канала. Используем getUpdates для получения последних входящих
        обновлений (работает только для ботов, добавленных в группы/каналы как admin).
        """
        try:
            updates = await self.bot.get_updates(limit=limit, timeout=10)
            posts = []
            for update in updates:
                message = update.message or update.channel_post
                if not message:
                    continue

                # Фильтруем по chat_id если указан
                if chat_id and str(message.chat_id) != str(chat_id):
                    continue

                post = {
                    'id': message.message_id,
                    'text': message.text or message.caption or '',
                    'date': message.date,
                    'media': [],
                    'media_url': None,
                }

                # Проверка на наличие медиа
                if message.photo:
                    # Берём фото наибольшего размера
                    largest_photo = max(message.photo, key=lambda p: p.file_size or 0)
                    post['media'] = [largest_photo.file_id]
                    post['media_url'] = largest_photo.file_id
                elif message.video:
                    post['media'] = [message.video.file_id]
                    post['media_url'] = message.video.file_id

                posts.append(post)

            return posts
        except TelegramError as e:
            print(f"Error getting Telegram posts: {e}")
            return []

    async def post_to_channel(self, chat_id: str, text: str, media: Optional[List[str]] = None) -> Dict:
        """Опубликовать пост в Telegram канал"""
        try:
            result = None

            if media:
                # Публикация с медиа — обрабатываем только первое медиа
                media_item = media[0]

                if media_item.startswith(('http://', 'https://')):
                    # Это URL — скачиваем файл локально для отправки
                    import uuid
                    from app.utils.media_downloader import download_media, get_file_extension

                    file_extension = get_file_extension(media_item)
                    temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"

                    downloaded_path = download_media(media_item, temp_filename)
                    if downloaded_path:
                        with open(downloaded_path, 'rb') as f:
                            if media_item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                result = await self.bot.send_photo(chat_id=chat_id, photo=f, caption=text)
                            elif media_item.lower().endswith(('.mp4', '.mov', '.avi')):
                                result = await self.bot.send_video(chat_id=chat_id, video=f, caption=text)
                            else:
                                result = await self.bot.send_document(chat_id=chat_id, document=f, caption=text)
                        # Удаляем временный файл после отправки
                        import os
                        try:
                            os.unlink(downloaded_path)
                        except OSError:
                            pass
                    else:
                        # Если не удалось скачать, пробуем отправить URL напрямую
                        if media_item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            result = await self.bot.send_photo(chat_id=chat_id, photo=media_item, caption=text)
                        elif media_item.lower().endswith(('.mp4', '.mov', '.avi')):
                            result = await self.bot.send_video(chat_id=chat_id, video=media_item, caption=text)
                        else:
                            result = await self.bot.send_document(chat_id=chat_id, document=media_item, caption=text)

                elif media_item.startswith('/tmp/') or media_item.startswith('./'):
                    # Это локальный файл
                    with open(media_item, 'rb') as f:
                        if media_item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            result = await self.bot.send_photo(chat_id=chat_id, photo=f, caption=text)
                        elif media_item.lower().endswith(('.mp4', '.mov', '.avi')):
                            result = await self.bot.send_video(chat_id=chat_id, video=f, caption=text)
                        else:
                            result = await self.bot.send_document(chat_id=chat_id, document=f, caption=text)
                else:
                    # Это file_id или другой формат
                    if media_item.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        result = await self.bot.send_photo(chat_id=chat_id, photo=media_item, caption=text)
                    elif media_item.endswith(('.mp4', '.mov', '.avi')):
                        result = await self.bot.send_video(chat_id=chat_id, video=media_item, caption=text)
                    else:
                        result = await self.bot.send_document(chat_id=chat_id, document=media_item, caption=text)
            else:
                # Публикация только текста
                result = await self.bot.send_message(chat_id=chat_id, text=text)

            return {
                'message_id': result.message_id,
                'date': result.date,
            }
        except TelegramError as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при публикации в Telegram"
            print(f"Error posting to Telegram: {error_message}")
            return {"error": error_message}

    async def validate_token(self) -> Dict:
        """Проверить валидность токена бота Telegram"""
        try:
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            return {
                "valid": True,
                "bot_id": bot_info.id,
                "bot_name": bot_info.first_name,
                "username": bot_info.username,
                "message": "Токен валиден"
            }
        except TelegramError as e:
            error_code = e.error_code if hasattr(e, 'error_code') else None
            if error_code == 401:
                return {
                    "valid": False,
                    "error": "Недействительный токен",
                    "message": "Токен бота неверен или отозван"
                }
            else:
                return {
                    "valid": False,
                    "error": f"Ошибка Telegram API (код {error_code})",
                    "message": str(e)
                }
        except Exception as e:
            return {
                "valid": False,
                "error": "Ошибка проверки токена",
                "message": str(e)
            }
