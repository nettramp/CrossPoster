import sys
sys.path.append('/app')

from app.social.vk_client import VKClient
from app.social.telegram_client import TelegramClient
from app.core.config import settings
import asyncio

async def test_repost_async():
    try:
        # Инициализируем клиенты
        vk = VKClient(settings.vk_api_token)
        telegram = TelegramClient(settings.telegram_bot_token)
        
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
                
                # Репостим в Telegram
                # Используем ваш Telegram канал
                chat_id = "@CrossPoster68"
                
                # Асинхронный вызов
                result = await telegram.post_to_channel(chat_id, f"Repost from VK:\n\n{post_text}")
                
                print(f"Repost result: {result}")
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

def test_repost():
    # Запускаем асинхронную функцию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(test_repost_async())
    loop.close()
    return result

if __name__ == "__main__":
    test_repost()