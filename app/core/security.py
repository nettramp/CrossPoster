from cryptography.fernet import Fernet
import os
import base64
import hashlib
from passlib.context import CryptContext

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _get_encryption_key() -> bytes:
    """
    Получить ключ шифрования из переменной окружения.
    Если ENCRYPTION_KEY не задан, генерируем детерминированный ключ из SECRET_KEY,
    чтобы он не менялся при каждом перезапуске приложения.
    """
    raw_key = os.getenv("ENCRYPTION_KEY")
    if raw_key:
        # Если ключ задан явно — используем его напрямую (должен быть валидным Fernet-ключом)
        try:
            # Проверяем, что это уже валидный Fernet-ключ (32 байта в base64url)
            decoded = base64.urlsafe_b64decode(raw_key + "==")
            if len(decoded) == 32:
                return raw_key.encode()
        except Exception:
            pass
        # Иначе — деривируем из него Fernet-ключ
        key_bytes = hashlib.sha256(raw_key.encode()).digest()
        return base64.urlsafe_b64encode(key_bytes)

    # Деривируем ключ из SECRET_KEY (стабильный между перезапусками)
    secret = os.getenv("SECRET_KEY", "crossposter_secret_key")
    key_bytes = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


ENCRYPTION_KEY = _get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


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
    if not token or len(token) < 10:
        return False

    # Простая проверка формата токенов для разных платформ
    if platform == "vk" and not token.startswith("vk"):
        return False
    elif platform == "telegram":
        # Telegram bot-токены имеют формат: <bot_id>:<hash>
        # Например: 123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
        if ":" not in token:
            return False
    elif platform == "instagram" and len(token) < 20:
        return False
    elif platform == "pinterest" and len(token) < 15:
        return False
    elif platform == "youtube" and not token.startswith("ya"):
        return False

    return True
