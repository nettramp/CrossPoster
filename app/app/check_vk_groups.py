import sys
sys.path.append('/app')

from app.social.vk_client import VKClient
from app.core.config import settings

def check_vk_groups():
    try:
        vk = VKClient(settings.vk_api_token)
        groups = vk.get_user_groups()
        print(f"Found {len(groups)} groups")
        for group in groups[:5]:
            print(f"Group: {group[1]} (ID: {group[0]})")
        return groups
    except Exception as e:
        print(f"Error getting VK groups: {e}")
        return []

if __name__ == "__main__":
    check_vk_groups()