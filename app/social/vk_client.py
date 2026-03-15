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
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при получении постов из VK"
            print(f"Error getting VK posts: {error_message}")
            return [{"error": error_message}]

    def validate_token(self) -> Dict:
        """Проверить валидность токена VK"""
        try:
            # Получаем информацию о пользователе через users.get (более надежный метод)
            user_info = self.vk.users.get()
            if user_info and len(user_info) > 0:
                user = user_info[0]
                return {
                    "valid": True,
                    "user_id": user.get("id"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "screen_name": user.get("screen_name", ""),
                    "message": "Токен валиден"
                }
            else:
                return {
                    "valid": False,
                    "error": "Пользователь не найден",
                    "message": "Не удалось получить информацию о пользователе"
                }
        except vk_api.exceptions.VkApiError as e:
            error_code = e.code if hasattr(e, 'code') else None
            error_msg = str(e)

            if error_code == 5:
                return {
                    "valid": False,
                    "error": "Недействительный токен",
                    "message": "Токен истёк или неверен"
                }
            elif error_code == 15:
                return {
                    "valid": False,
                    "error": "Доступ запрещён",
                    "message": "Нет доступа к профилю"
                }
            elif error_code == 28:
                return {
                    "valid": False,
                    "error": "Неверный запрос (код 28)",
                    "message": "Метод account.getProfileInfo устарел. Используйте users.get"
                }
            else:
                return {
                    "valid": False,
                    "error": f"Ошибка VK API (код {error_code})",
                    "message": error_msg
                }
        except Exception as e:
            return {
                "valid": False,
                "error": "Ошибка проверки токена",
                "message": str(e)
            }

    def post_to_wall(
        self,
        owner_id: str,
        message: str,
        attachments: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
    ) -> Dict:
        """
        Опубликовать пост в VK.

        Параметры:
            owner_id    — ID владельца стены (группа со знаком «-» или пользователь).
            message     — Текст поста.
            attachments — Уже готовые attachment-строки вида «photo-123_456».
            media_urls  — URL медиафайлов, которые нужно скачать и загрузить в VK.
                          Если переданы оба параметра, media_urls обрабатываются первыми
                          и добавляются к attachments.
        """
        try:
            post_data = {
                'owner_id': owner_id,
                'message': message,
            }

            all_attachments = list(attachments) if attachments else []

            if media_urls:
                import uuid
                from app.utils.media_downloader import download_media, get_file_extension

                # Убираем минус из ID группы для загрузки фото
                group_id = owner_id.lstrip('-') if owner_id.startswith('-') else None

                for media_url in media_urls:
                    file_extension = get_file_extension(media_url)
                    temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"

                    downloaded_path = download_media(media_url, temp_filename)
                    if downloaded_path:
                        attachment = self.upload_photo(downloaded_path, group_id)
                        if attachment:
                            all_attachments.append(attachment)

            if all_attachments:
                post_data['attachments'] = ','.join(all_attachments)

            result = self.vk.wall.post(**post_data)
            return result
        except Exception as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при публикации в VK"
            print(f"Error posting to VK: {error_message}")
            return {"error": error_message}

    def upload_photo(self, photo_path: str, group_id: Optional[str] = None) -> str:
        """Загрузить фото в VK и вернуть attachment строку"""
        try:
            upload = vk_api.VkUpload(self.vk_session)
            if group_id:
                photo = upload.photo_wall(photo_path, group_id=group_id)
            else:
                photo = upload.photo_wall(photo_path)
            owner_id = photo[0]['owner_id']
            photo_id = photo[0]['id']
            return f'photo{owner_id}_{photo_id}'
        except Exception as e:
            print(f"Error uploading photo to VK: {e}")
            return ""
