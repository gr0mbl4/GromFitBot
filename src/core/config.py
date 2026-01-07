"""
Конфигурация системы GromFitBot
Полная версия с валидацией и настройками
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Config:
    """Полный класс конфигурации"""
    
    def __init__(self):
        # Загружаем .env файл
        self._load_env()
        
        # Основные настройки бота
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        
        # Настройки базы данных
        self.DB_PATH = os.getenv('DB_PATH', 'data/users.db')
        
        # Настройки Redis (если используется)
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
        self.REDIS_DB = int(os.getenv('REDIS_DB', '0'))
        
        # Веб-настройки
        self.WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
        self.WEB_PORT = int(os.getenv('WEB_PORT', '8080'))
        self.WEB_SECRET = os.getenv('WEB_SECRET', '')
        
        # Настройки S3 (для бэкапов)
        self.S3_ENDPOINT = os.getenv('S3_ENDPOINT', '')
        self.S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY', '')
        self.S3_SECRET_KEY = os.getenv('S3_SECRET_KEY', '')
        self.S3_BUCKET = os.getenv('S3_BUCKET', '')
        self.S3_REGION = os.getenv('S3_REGION', '')
        
        # Настройки логирования
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
        self.ERROR_LOG_FILE = os.getenv('ERROR_LOG_FILE', 'logs/errors.log')
        
        # Настройки безопасности
        self.ADMIN_IDS = self._parse_admin_ids(os.getenv('ADMIN_IDS', ''))
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'
        
        # Настройки бота
        self.BOT_USERNAME = os.getenv('BOT_USERNAME', '')
        self.BOT_NAME = os.getenv('BOT_NAME', 'GromFitBot')
        self.BOT_DESCRIPTION = os.getenv('BOT_DESCRIPTION', 'Спортивные дуэли на токенах')
        
        # Экономические настройки
        self.START_TOKENS = float(os.getenv('START_TOKENS', '50.0'))
        self.REFERRAL_BONUS = float(os.getenv('REFERRAL_BONUS', '10.0'))
        self.DAILY_BONUS_BASE = float(os.getenv('DAILY_BONUS_BASE', '5.0'))
        self.DAILY_STREAK_MULTIPLIER = float(os.getenv('DAILY_STREAK_MULTIPLIER', '1.2'))
        
        # Настройки регистрации
        self.MIN_NICKNAME_LENGTH = int(os.getenv('MIN_NICKNAME_LENGTH', '3'))
        self.MAX_NICKNAME_LENGTH = int(os.getenv('MAX_NICKNAME_LENGTH', '20'))
        self.ALLOWED_REGIONS = self._parse_allowed_regions(os.getenv('ALLOWED_REGIONS', ''))
        
        # Настройки магазина
        self.SHOP_ENABLED = os.getenv('SHOP_ENABLED', 'True').lower() == 'true'
        self.MAX_PURCHASE_PER_DAY = int(os.getenv('MAX_PURCHASE_PER_DAY', '10'))
        
        # Пути к файлам
        self._setup_paths()
        
        logger.info("Конфигурация загружена")
    
    def _load_env(self):
        """Загрузка переменных окружения из .env файла"""
        env_path = Path('.env')
        
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Файл .env загружен: {env_path.absolute()}")
        else:
            # Ищем в родительских директориях
            parent_env = Path('..') / '.env'
            if parent_env.exists():
                load_dotenv(parent_env)
                logger.info(f"Файл .env загружен из родительской директории: {parent_env.absolute()}")
            else:
                logger.warning("Файл .env не найден. Используются значения по умолчанию.")
    
    def _setup_paths(self):
        """Настройка путей к директориям"""
        # Основные директории
        self.BASE_DIR = Path.cwd()
        self.SRC_DIR = self.BASE_DIR / 'src'
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.LOGS_DIR = self.BASE_DIR / 'logs'
        self.TEMP_DIR = self.BASE_DIR / 'temp'
        
        # Создаем необходимые директории
        for directory in [self.DATA_DIR, self.LOGS_DIR, self.TEMP_DIR]:
            directory.mkdir(exist_ok=True)
    
    def _parse_admin_ids(self, admin_ids_str: str) -> list:
        """Парсинг ID администраторов"""
        if not admin_ids_str:
            return []
        
        try:
            ids = [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
            return ids
        except ValueError:
            logger.warning(f"Неверный формат ADMIN_IDS: {admin_ids_str}")
            return []
    
    def _parse_allowed_regions(self, regions_str: str) -> list:
        """Парсинг разрешенных регионов"""
        if not regions_str:
            return ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань']
        
        return [region.strip() for region in regions_str.split(',') if region.strip()]
    
    def validate(self) -> bool:
        """Валидация конфигурации"""
        errors = []
        
        # Проверка токена бота
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN не установлен")
        elif not self.BOT_TOKEN.startswith('8') or ':' not in self.BOT_TOKEN:
            errors.append("Неверный формат BOT_TOKEN")
        
        # Проверка пути к БД
        if not self.DB_PATH:
            errors.append("DB_PATH не установлен")
        
        # Проверка обязательных директорий
        if not self.DATA_DIR.exists():
            errors.append(f"Директория данных не найдена: {self.DATA_DIR}")
        
        # Проверка администраторов
        if not self.ADMIN_IDS:
            logger.warning("ADMIN_IDS не установлены. Админ-панель недоступна.")
        
        if errors:
            for error in errors:
                logger.error(f"❌ Ошибка конфигурации: {error}")
            return False
        
        logger.info("✅ Конфигурация валидна")
        return True
    
    def get_database_url(self) -> str:
        """Получение URL для подключения к БД"""
        return f"sqlite:///{self.DB_PATH}"
    
    def get_redis_url(self) -> str:
        """Получение URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.ADMIN_IDS
    
    def get_logging_config(self) -> dict:
        """Конфигурация логирования"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.LOG_LEVEL,
                    'formatter': 'standard',
                    'stream': sys.stdout
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': self.LOG_LEVEL,
                    'formatter': 'detailed',
                    'filename': self.LOG_FILE,
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf-8'
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'detailed',
                    'filename': self.ERROR_LOG_FILE,
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file', 'error_file'],
                    'level': self.LOG_LEVEL,
                    'propagate': True
                },
                'aiogram': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False
                },
                'sqlalchemy': {
                    'handlers': ['console', 'file'],
                    'level': 'WARNING',
                    'propagate': False
                }
            }
        }
    
    def __str__(self) -> str:
        """Строковое представление конфигурации (без секретов)"""
        return (
            f"Config(\n"
            f"  BOT_TOKEN: {'*' * 10}{self.BOT_TOKEN[-5:] if self.BOT_TOKEN else ''}\n"
            f"  DB_PATH: {self.DB_PATH}\n"
            f"  ADMIN_IDS: {self.ADMIN_IDS}\n"
            f"  DEBUG_MODE: {self.DEBUG_MODE}\n"
            f"  START_TOKENS: {self.START_TOKENS}\n"
            f"  REFERRAL_BONUS: {self.REFERRAL_BONUS}\n"
            f"  ALLOWED_REGIONS: {self.ALLOWED_REGIONS[:3]}...\n"
            f")"
        )