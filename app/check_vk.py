import os
from app.core.config import settings
import vk_api

def check_vk_api():
    try:
        # Создаем сессию VK API
        vk_session = vk_api.VkApi(token=settings.vk_api_token)
        vk = vk_session.get_api()
        
        # Получаем информацию о текущем пользователе
        user_info = vk.users.get()
        print("VK API connection successful")
        print(f"User: {user_info[0]['first_name']} {user_info[0]['last_name']}")
        
        # Получаем список групп пользователя
        groups = vk.groups.get()
        print(f"User is member of {groups['count']} groups")
        
        # Проверяем, есть ли группы, в которых можно публиковать
        if groups['count'] > 0:
            group_id = groups['items'][0]
            try:
                # Пытаемся получить информацию о группе
                group_info = vk.groups.getById(group_id=group_id)
                print(f"Group: {group_info[0]['name']}")
            except Exception as e:
                print(f"Could not get group info: {e}")
        else:
            print("User is not a member of any groups")
            
    except Exception as e:
        print(f"VK API connection failed: {e}")

if __name__ == "__main__":
    check_vk_api()