from cryptography.fernet import Fernet
import os

# Генерация ключа шифрования (в реальном приложении лучше хранить в переменной окружения)
def generate_key():
    return Fernet.generate_key()

# Ключ шифрования (в продакшене использовать переменную окружения)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_data(data: str) -> str:
    """
    Шифрование данных
    """
    if not data:
        return ""
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Расшифровка данных
    """
    if not encrypted_data:
        return ""
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
    return decrypted_data.decode()

def validate_token(platform: str, token: str) -> bool:
    """
    Проверка валидности токена для конкретной платформы
    """
    # В реальном приложении здесь будет проверка токена через API соответствующей платформы
    if not token or len(token) < 10:
        return False
    
    # Простая проверка формата токенов для разных платформ
    if platform == "vk" and not token.startswith("vk"):
        return False
    elif platform == "telegram" and not token.endswith(":"):
        # Telegram токены обычно заканчиваются на ":"
        return False
    elif platform == "instagram" and len(token) < 20:
        return False
    elif platform == "pinterest" and len(token) < 15:
        return False
    elif platform == "youtube" and not token.startswith("ya"):
        return False
    
    return True