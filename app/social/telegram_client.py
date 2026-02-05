from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, List, Optional
import asyncio

class TelegramClient:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
    
    async def get_latest_posts(self, chat_id: str, limit: int = 10) -> List[Dict]:
        """Получить последние посты из Telegram канала"""
        try:
            messages = await self.bot.get_chat_history(chat_id, limit=limit)
            posts = []
            async for message in messages:
                post = {
                    'id': message.message_id,
                    'text': message.text,
                    'date': message.date,
                    'media': []
                }
                
                # Проверка на наличие медиа
                if message.photo:
                    post['media'] = [photo.file_id for photo in message.photo]
                elif message.video:
                    post['media'] = [message.video.file_id]
                
                posts.append(post)
            
            return posts
        except TelegramError as e:
            print(f"Error getting Telegram posts: {e}")
            return []
    
    async def post_to_channel(self, chat_id: str, text: str, media: Optional[List[str]] = None) -> Dict:
        """Опубликовать пост в Telegram канал"""
        try:
            if media:
                # Публикация с медиа - обрабатываем только первое медиа, т.к. Telegram не поддерживает альбомы в этом методе
                media_item = media[0]  # Берем первое медиа
                # Telegram Bot API позволяет напрямую использовать URL-адреса, но для надежности скачаем файл
                if media_item.startswith(('http://', 'https://')):
                    # Это URL, скачиваем файл локально для отправки
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
                        os.unlink(downloaded_path)
                    else:
                        # Если не удалось скачать, пробуем отправить URL напрямую
                        if media_item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            result = await self.bot.send_photo(chat_id=chat_id, photo=media_item, caption=text)
                        elif media_item.lower().endswith(('.mp4', '.mov', '.avi')):
                            result = await self.bot.send_video(chat_id=chat_id, video=media_item, caption=text)
                        else:
                            result = await self.bot.send_document(chat_id=chat_id, document=media_item, caption=text)
                elif media_item.startswith('/tmp/') or media_item.startswith('./'):
                    # Это локальный файл, отправляем его
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
                'date': result.date
            }
        except TelegramError as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при публикации в Telegram"
            print(f"Error posting to Telegram: {error_message}")
            return {"error": error_message}