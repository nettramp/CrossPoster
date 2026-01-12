from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Dict, List, Optional
import os

class YouTubeClient:
    def __init__(self, api_key: str, client_secrets_file: Optional[str] = None):
        self.api_key = api_key
        self.client_secrets_file = client_secrets_file
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_latest_videos(self, channel_id: str, count: int = 10) -> List[Dict]:
        """Получить последние видео с канала"""
        try:
            request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                order='date',
                type='video',
                maxResults=count
            )
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video = {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'thumbnail_url': item['snippet']['thumbnails']['default']['url']
                }
                videos.append(video)
            
            return videos
        except Exception as e:
            print(f"Error getting YouTube videos: {e}")
            return []
    
    def upload_short(self, video_path: str, title: str, description: str, 
                     tags: Optional[List[str]] = None) -> Dict:
        """Загрузить короткое видео на YouTube"""
        try:
            # Создание объекта видео
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags if tags else [],
                    'categoryId': '22'  # Категория "Люди и блоги"
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Загрузка видео
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
            
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = request.execute()
            return {
                'video_id': response['id'],
                'url': f"https://www.youtube.com/shorts/{response['id']}"
            }
        except Exception as e:
            print(f"Error uploading YouTube short: {e}")
            return {}