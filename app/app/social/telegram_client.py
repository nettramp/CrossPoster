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
                # Публикация с медиа
                if media[0].endswith(('.jpg', '.jpeg', '.png')):
                    result = await self.bot.send_photo(chat_id=chat_id, photo=media[0], caption=text)
                elif media[0].endswith(('.mp4', '.mov')):
                    result = await self.bot.send_video(chat_id=chat_id, video=media[0], caption=text)
                else:
                    result = await self.bot.send_document(chat_id=chat_id, document=media[0], caption=text)
            else:
                # Публикация только текста
                result = await self.bot.send_message(chat_id=chat_id, text=text)
            
            # Преобразуем результат в словарь
            return {
                'message_id': result.message_id,
                'date': result.date
            }
        except TelegramError as e:
            print(f"Error posting to Telegram: {e}")
            return {}