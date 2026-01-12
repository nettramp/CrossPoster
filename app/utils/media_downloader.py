import requests
import os
from typing import Optional

def download_media(url: str, save_path: str) -> Optional[str]:
    """Скачать медиафайл по URL и сохранить по указанному пути"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Создание директории, если она не существует
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Сохранение файла
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        return save_path
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None

def get_file_extension(url: str) -> str:
    """Получить расширение файла из URL"""
    try:
        return url.split('?')[0].split('.')[-1].lower()
    except:
        return 'jpg'  # По умолчанию

def is_video_file(filename: str) -> bool:
    """Проверить, является ли файл видео"""
    video_extensions = ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm']
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    return extension in video_extensions

def is_image_file(filename: str) -> bool:
    """Проверить, является ли файл изображением"""
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    extension = filename.split('.')[-1].lower() if '.' in filename else ''
    return extension in image_extensions