import sys
sys.path.append('/app')

from app.social.vk_client import VKClient
from app.core.config import settings

def test_vk_groups():
    try:
        # Инициализируем VK клиент
        vk = VKClient(settings.vk_api_token)
        
        # Получаем информацию о пользователе
        user_info = vk.vk.users.get()
        user_id = user_info[0]['id']
        print(f"User ID: {user_id}")
        
        # Получаем список групп пользователя
        groups = vk.vk.groups.get(userId=user_id, extended=1)
        print(f"Found {groups['count']} groups")
        
        # Выводим информацию о первых 5 группах
        for i, group in enumerate(groups['items'][:5]):
            print(f"Group {i+1}:")
            print(f"  ID: {group.get('id', 'N/A')}")
            print(f"  Name: {group.get('name', 'N/A')}")
            print(f"  Screen name: {group.get('screen_name', 'N/A')}")
            print()
            
        return groups['items'] if groups['count'] > 0 else []
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_vk_groups()