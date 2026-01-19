import sys
sys.path.append('/app')

from app.social.vk_client import VKClient
from app.core.config import settings
from telegram import Bot
import os
import uuid
from app.utils.media_downloader import download_media, get_file_extension

def test_repost_final():
    try:
        # Инициализируем VK клиент
        vk = VKClient(settings.vk_api_token)
        from telegram.ext import Application
        app = Application.builder().token(settings.telegram_bot_token).build()
        bot = app.bot
        
        # Получаем информацию о пользователе VK
        user_info = vk.vk.users.get()
        user_id = user_info[0]['id']
        print(f"User ID: {user_id}")
        
        # Получаем список групп пользователя
        groups = vk.vk.groups.get(userId=user_id, extended=1)
        if groups['count'] > 0:
            # Берем первую группу
            group = groups['items'][0]
            group_id = group['id']
            group_name = group['name']
            print(f"Testing group: {group_name} (ID: {group_id})")
            
            # Получаем последние посты из группы
            posts = vk.get_latest_posts(f"-{group_id}", count=1)
            if posts:
                post = posts[0]
                post_text = post.get('text', '')
                post_id = post.get('id', 'N/A')
                print(f"Reposting post ID: {post_id}")
                print(f"Post text: {post_text[:100]}...")
                
                # Обрабатываем вложения
                media_files = []
                if 'attachments' in post:
                    for attachment in post['attachments']:
                        if attachment['type'] == 'photo':
                            # Берем фото самого большого размера
                            sizes = attachment['photo']['sizes']
                            max_size_photo = max(sizes, key=lambda x: x['width'])
                            photo_url = max_size_photo['url']
                            
                            # Скачиваем фото
                            file_extension = get_file_extension(photo_url)
                            temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"
                            downloaded_path = download_media(photo_url, temp_filename)
                            if downloaded_path:
                                media_files.append(downloaded_path)
                
                # Репостим в Telegram
                # Используем ваш Telegram канал
                chat_id = "@CrossPoster68"
                
                if media_files:
                    # Отправляем с медиа
                    media_file = media_files[0]  # Берем первое фото
                    with open(media_file, 'rb') as photo:
                        message = f"Repost from VK:\n\n{post_text}"
                        import asyncio
                        result = asyncio.run(bot.send_photo(chat_id=chat_id, photo=photo, caption=message))
                    
                    # Удаляем временный файл
                    os.remove(media_file)
                else:
                    # Отправляем только текст
                    message = f"Repost from VK:\n\n{post_text}"
                    import asyncio
                    result = asyncio.run(bot.send_message(chat_id=chat_id, text=message))
                
                print(f"Repost successful!")
                print(f"Message ID: {result.message_id}")
                print(f"Message date: {result.date}")
                return result
            else:
                print("No posts found")
                return None
        else:
            print("No groups found")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_repost_final()