import vk_api
from typing import Dict, List, Optional
from datetime import datetime

class VKClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.vk_session = vk_api.VkApi(token=access_token)
        self.vk = self.vk_session.get_api()
    
    def get_latest_posts(self, owner_id: str, count: int = 10) -> List[Dict]:
        """Получить последние посты из VK"""
        try:
            posts = self.vk.wall.get(owner_id=owner_id, count=count)
            return posts['items']
        except Exception as e:
            print(f"Error getting VK posts: {e}")
            return []
    
    def post_to_wall(self, owner_id: str, message: str, media_urls: Optional[List[str]] = None) -> Dict:
        """Опубликовать пост в VK"""
        try:
            post_data = {
                'owner_id': owner_id,
                'message': message
            }
            
            attachments = []
            if media_urls:
                # Обработка URL-адресов медиафайлов
                import uuid
                from app.utils.media_downloader import download_media, get_file_extension
                
                for media_url in media_urls:
                    file_extension = get_file_extension(media_url)
                    temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"
                    
                    downloaded_path = download_media(media_url, temp_filename)
                    if downloaded_path:
                        # Загружаем в VK
                        attachment = self.upload_photo(downloaded_path, owner_id.lstrip('-'))  # Убираем минус из ID группы
                        if attachment:
                            attachments.append(attachment)
            
            if attachments:
                post_data['attachments'] = ','.join(attachments)
            
            result = self.vk.wall.post(**post_data)
            return result
        except Exception as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при публикации в VK"
            print(f"Error posting to VK: {error_message}")
            return {"error": error_message}
    
    def upload_photo(self, photo_path: str, group_id: Optional[str] = None) -> str:
        """Загрузить фото в VK и вернуть attachment строку"""
        try:
            if group_id:
                upload = vk_api.VkUpload(self.vk_session)
                photo = upload.photo_wall(photo_path, group_id=group_id)
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                return f'photo{owner_id}_{photo_id}'
            else:
                # Загрузка на стену пользователя
                upload = vk_api.VkUpload(self.vk_session)
                photo = upload.photo_wall(photo_path)
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                return f'photo{owner_id}_{photo_id}'
        except Exception as e:
            print(f"Error uploading photo to VK: {e}")
            return ""