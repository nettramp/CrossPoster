from pinterest import Pinterest
from typing import Dict, List, Optional

class PinterestClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.pinterest = Pinterest(access_token=access_token)
    
    def get_latest_pins(self, board_id: str, count: int = 10) -> List[Dict]:
        """Получить последние пины с доски"""
        try:
            pins = self.pinterest.boards.pins(board_id=board_id, page_size=count)
            return pins if pins else []
        except Exception as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при получении пинов с Pinterest"
            print(f"Error getting Pinterest pins: {error_message}")
            return []
    
    def create_pin(self, board_id: str, title: str, description: str, 
                   image_url: str, link: Optional[str] = None) -> Dict:
        """Создать новый пин"""
        try:
            pin_data = {
                'board_id': board_id,
                'title': title,
                'description': description,
                'media': {'source': {'url': image_url}}
            }
            
            if link:
                pin_data['link'] = link
            
            result = self.pinterest.pins.create(pin_data)
            return result if result else {"error": "Не удалось создать пин в Pinterest"}
        except Exception as e:
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка при создании пина в Pinterest"
            print(f"Error creating Pinterest pin: {error_message}")
            return {"error": error_message}

    def validate_token(self) -> Dict:
        """Проверить валидность токена Pinterest"""
        try:
            # Пытаемся получить информацию о текущем пользователе
            user_info = self.pinterest.users.get()
            return {
                "valid": True,
                "user_id": user_info.get("id"),
                "username": user_info.get("username"),
                "message": "Токен валиден"
            }
        except Exception as e:
            error_message = str(e)
            if "401" in error_message or "unauthorized" in error_message.lower():
                return {
                    "valid": False,
                    "error": "Недействительный токен",
                    "message": "Токен истёк или неверен"
                }
            else:
                return {
                    "valid": False,
                    "error": "Ошибка проверки токена",
                    "message": error_message
                }