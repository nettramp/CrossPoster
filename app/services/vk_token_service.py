import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.social_account import SocialAccount as SocialAccountModel
from app.social.vk_auth_client import VKAuthClient, get_token_via_oauth
from app.database import SessionLocal


class VKTokenService:
    """
    Сервис для отслеживания и обновления токенов ВКонтакте
    """
    
    def __init__(self):
        self.auth_client = VKAuthClient()
        self.check_interval = 3600  # Проверять каждые час (в секундах)
    
    def validate_and_refresh_token(self, account: SocialAccountModel) -> Dict:
        """
        Проверить токен и обновить его при необходимости
        
        Args:
            account: Объект социального аккаунта ВКонтакте
            
        Returns:
            Словарь с результатом проверки и обновления
        """
        if account.platform != 'vk':
            return {
                'success': False,
                'message': 'Аккаунт не является аккаунтом ВКонтакте'
            }
        
        # Проверяем валидность текущего токена
        validation_result = self.auth_client.validate_token(account.access_token)
        
        if validation_result['valid']:
            return {
                'success': True,
                'token_valid': True,
                'message': 'Токен действителен',
                'user_info': {
                    'user_id': validation_result['user_id'],
                    'first_name': validation_result['first_name'],
                    'last_name': validation_result['last_name']
                }
            }
        else:
            # Токен недействителен, пробуем обновить
            settings = account.settings or {}
            
            # Проверяем, есть ли сохраненные учетные данные для обновления токена
            login = settings.get('login')
            password = settings.get('password')
            
            if not login or not password:
                return {
                    'success': False,
                    'token_valid': False,
                    'message': 'Нет сохраненных учетных данных для обновления токена'
                }
            
            # Получаем новый токен через альтернативный метод
            new_token_result = get_token_via_oauth(login, password)
            
            if new_token_result['success']:
                # Обновляем токен в базе данных
                db = SessionLocal()
                try:
                    account.access_token = new_token_result['access_token']
                    account.updated_at = datetime.utcnow()
                    
                    db.add(account)
                    db.commit()
                    db.refresh(account)
                    
                    return {
                        'success': True,
                        'token_valid': True,
                        'token_refreshed': True,
                        'message': 'Токен успешно обновлен',
                        'user_info': {
                            'user_id': new_token_result['user_id'],
                            'first_name': new_token_result['first_name'],
                            'last_name': new_token_result['last_name']
                        }
                    }
                except Exception as e:
                    db.rollback()
                    return {
                        'success': False,
                        'token_valid': False,
                        'message': f'Ошибка обновления токена в базе данных: {str(e)}'
                    }
                finally:
                    db.close()
            else:
                return {
                    'success': False,
                    'token_valid': False,
                    'message': f'Не удалось получить новый токен: {new_token_result["message"]}'
                }
    
    def schedule_token_check(self):
        """
        Запланировать регулярную проверку токенов
        """
        # Запускаем фоновую задачу проверки токенов
        asyncio.create_task(self._check_tokens_periodically())
    
    async def _check_tokens_periodically(self):
        """
        Периодическая проверка токенов
        """
        while True:
            try:
                # Получаем все аккаунты ВКонтакте
                db = SessionLocal()
                try:
                    vk_accounts = db.query(SocialAccountModel).filter(
                        SocialAccountModel.platform == 'vk',
                        SocialAccountModel.is_active == True
                    ).all()
                    
                    for account in vk_accounts:
                        result = self.validate_and_refresh_token(account)
                        
                        # Логируем результат проверки
                        print(f"Проверка токена для аккаунта {account.id}: {result['message']}")
                        
                except Exception as e:
                    print(f"Ошибка при проверке токенов: {str(e)}")
                finally:
                    db.close()
                
                # Ждем заданный интервал перед следующей проверкой
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Ошибка в фоновой задаче проверки токенов: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def manual_token_refresh(self, account_id: int) -> Dict:
        """
        Ручное обновление токена для конкретного аккаунта
        
        Args:
            account_id: ID аккаунта для обновления токена
            
        Returns:
            Словарь с результатом обновления
        """
        db = SessionLocal()
        try:
            account = db.query(SocialAccountModel).filter(
                SocialAccountModel.id == account_id,
                SocialAccountModel.platform == 'vk'
            ).first()
            
            if not account:
                return {
                    'success': False,
                    'message': 'Аккаунт не найден или не является аккаунтом ВКонтакте'
                }
            
            return self.validate_and_refresh_token(account)
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при обновлении токена: {str(e)}'
            }
        finally:
            db.close()


# Глобальный экземпляр сервиса
vk_token_service = VKTokenService()