from instagrapi import Client
from typing import Dict, List, Optional
import os

class InstagramClient:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.client = Client()
        self.login()
    
    def login(self):
        """Авторизация в Instagram"""
        try:
            self.client.login(self.username, self.password)
        except Exception as e:
            print(f"Error logging into Instagram: {e}")
    
    def get_latest_posts(self, user_id: str, count: int = 10) -> List[Dict]:
        """Получить последние посты из Instagram"""
        try:
            medias = self.client.user_medias(user_id, count)
            posts = []
            
            for media in medias:
                post = {
                    'id': media.id,
                    'caption': media.caption_text,
                    'timestamp': media.taken_at,
                    'media_type': media.media_type,
                    'thumbnail_url': media.thumbnail_url,
                    'video_url': media.video_url if hasattr(media, 'video_url') else None
                }
                posts.append(post)
            
            return posts
        except Exception as e:
            print(f"Error getting Instagram posts: {e}")
            return []
    
    def post_photo(self, photo_path: str, caption: str) -> Dict:
        """Опубликовать фото в Instagram"""
        try:
            result = self.client.photo_upload(photo_path, caption)
            return {
                'media_id': result.id,
                'url': f"https://www.instagram.com/p/{result.code}/"
            }
        except Exception as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при публикации в Instagram"
            print(f"Error posting photo to Instagram: {error_message}")
            return {"error": error_message}
    
    def post_video(self, video_path: str, caption: str, thumbnail_path: Optional[str] = None) -> Dict:
        """Опубликовать видео в Instagram"""
        try:
            if thumbnail_path:
                result = self.client.video_upload(video_path, caption, thumbnail=thumbnail_path)
            else:
                result = self.client.video_upload(video_path, caption)
            
            return {
                'media_id': result.id,
                'url': f"https://www.instagram.com/p/{result.code}/"
            }
        except Exception as e:
            print(f"Error posting video to Instagram: {e}")
            return {}