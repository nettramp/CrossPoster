import sys
sys.path.append('/app')

from app.social.vk_client import VKClient
from app.core.config import settings

def test_vk_posts():
    try:
        # Инициализируем VK клиент
        vk = VKClient(settings.vk_api_token)
        
        # Получаем информацию о пользователе
        user_info = vk.vk.users.get()
        user_id = user_info[0]['id']
        print(f"User ID: {user_id}")
        
        # Получаем последние посты со стены пользователя
        posts = vk.get_latest_posts(f"-{user_id}", count=5)
        print(f"Found {len(posts)} posts")
        
        # Выводим информацию о постах
        for i, post in enumerate(posts):
            print(f"Post {i+1}:")
            print(f"  ID: {post.get('id', 'N/A')}")
            print(f"  Date: {post.get('date', 'N/A')}")
            print(f"  Text: {post.get('text', '')[:100]}...")
            print()
            
        return posts
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_vk_posts()