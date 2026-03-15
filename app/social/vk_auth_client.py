import vk_api
from vk_api.vk_api import VkApi
from typing import Dict, Optional
import requests
import re
from urllib.parse import urlparse, parse_qs


class VKAuthClient:
    """
    Модуль для получения токена доступа к ВКонтакте
    """
    
    def __init__(self):
        self.app_id = '7362610'  # Standalone приложение для получения токена
        self.scope = 'wall,groups,photos,video,audio,docs,notes,pages,status,offers,questions,notifications,stats,ads,market'
        self.auth_url = 'https://oauth.vk.com/authorize'
        self.token_url = 'https://oauth.vk.com/access_token'
    
    def get_access_token(self, login: str, password: str) -> Dict:
        """
        Получить access token ВКонтакте по логину и паролю
        
        Args:
            login: Логин ВКонтакте (email или телефон)
            password: Пароль ВКонтакте
            
        Returns:
            Словарь с токеном и информацией о пользователе
        """
        try:
            # Используем vk_api для аутентификации
            vk_session = vk_api.VkApi(login, password)
            
            # Авторизуемся
            vk_session.auth(token_only=True)
            
            # Получаем токен
            token = vk_session.token['access_token']
            
            # Создаем API объект для проверки токена
            vk = vk_session.get_api()
            
            # Получаем информацию о пользователе
            user_info = vk.users.get()[0]
            
            return {
                'access_token': token,
                'user_id': user_info['id'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'screen_name': user_info.get('screen_name', ''),
                'expires_in': vk_session.token.get('expires_in', 0),
                'success': True,
                'message': 'Токен успешно получен'
            }
            
        except vk_api.AuthError as e:
            return {
                'success': False,
                'error': 'Ошибка аутентификации',
                'message': str(e)
            }
        except vk_api.Captcha as captcha:
            return {
                'success': False,
                'error': 'Требуется ввод капчи',
                'captcha_sid': captcha.sid,
                'captcha_img': captcha.img,
                'message': 'Требуется ввести капчу для авторизации'
            }
        except vk_api.TwoFactorError as e:
            return {
                'success': False,
                'error': 'Требуется двухфакторная аутентификация',
                'message': 'Для авторизации требуется ввести код двухфакторной аутентификации'
            }
        except Exception as e:
            error_str = str(e)
            # Проверяем, содержит ли ошибка специфическое сообщение "no sid"
            if 'no sid' in error_str.lower() or ('auth' in error_str.lower() and 'sid' in error_str.lower()):
                return {
                    'success': False,
                    'error': 'Ошибка получения токена: AUTH; no sid',
                    'message': 'Не удалось получить SID для аутентификации. Это может быть связано с ограничениями безопасности ВКонтакте. Пожалуйста, используйте альтернативный метод получения токена или проверьте учетные данные.'
                }
            else:
                return {
                    'success': False,
                    'error': 'Ошибка получения токена',
                    'message': str(e)
                }
    
    def validate_token(self, token: str) -> Dict:
        """
        Проверить валидность токена ВКонтакте
        
        Args:
            token: Access token для проверки
            
        Returns:
            Словарь с результатом проверки
        """
        try:
            vk_session = VkApi(token=token)
            vk = vk_session.get_api()
            
            # Получаем информацию о пользователе через users.get
            user_info = vk.users.get()
            if user_info and len(user_info) > 0:
                user = user_info[0]
                return {
                    'valid': True,
                    'user_id': user.get('id'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'screen_name': user.get('screen_name', ''),
                    'message': 'Токен валиден'
                }
            else:
                return {
                    'valid': False,
                    'error': 'Пользователь не найден',
                    'message': 'Не удалось получить информацию о пользователе'
                }
        except Exception as e:
            return {
                'valid': False,
                'error': 'Ошибка проверки токена',
                'message': str(e)
            }


# Альтернативный метод получения токена через OAuth flow
def get_token_via_oauth(login: str, password: str, app_id: str = '7362610') -> Dict:
    """
    Альтернативный способ получения токена через OAuth flow
    
    Args:
        login: Логин ВКонтакте
        password: Пароль ВКонтакте
        app_id: ID приложения ВКонтакте
        
    Returns:
        Словарь с токеном
    """
    try:
        # URL для получения токена
        url = 'https://oauth.vk.com/token'
        
        params = {
            'grant_type': 'password',
            'client_id': app_id,
            'client_secret': 'Ml7GnpMGyj4GYNYHDNrl',  # Это публичный ключ, не является секретным
            'username': login,
            'password': password,
            'scope': 'offline,wall,groups,photos,video,audio,docs,notes,pages,status,offers,questions,notifications,stats,ads,market',
            '2fa_supported': 1
        }
        
        response = requests.post(url, data=params)
        data = response.json()
        
        if 'access_token' in data:
            return {
                'access_token': data['access_token'],
                'user_id': data.get('user_id'),
                'expires_in': data.get('expires_in'),
                'success': True,
                'message': 'Токен успешно получен'
            }
        else:
            return {
                'success': False,
                'error': data.get('error', 'Unknown error'),
                'error_description': data.get('error_description', 'No description'),
                'message': data.get('error_description', 'Не удалось получить токен')
            }
    except Exception as e:
        return {
            'success': False,
            'error': 'Ошибка получения токена',
            'message': str(e)
        }