"""
Точка входа в приложение GromFitBot
Полная версия с инициализацией всех компонентов
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Добавляем корневую директорию в путь для импортов
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Настройка логирования до импорта других модулей
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Настройка окружения и проверка зависимостей"""
    logger.info("=" * 60)
    logger.info("Настройка окружения GromFitBot")
    logger.info("=" * 60)
    
    # Проверка Python версии
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        logger.error(f"Требуется Python 3.9 или выше. У вас: {python_version.major}.{python_version.minor}")
        return False
    
    logger.info(f"✅ Python версия: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Проверка необходимых директорий
    required_dirs = ['data', 'logs', 'temp']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Создана директория: {dir_path}")
            except Exception as e:
                logger.error(f"❌ Не удалось создать директорию {dir_path}: {e}")
                return False
        else:
            logger.info(f"✅ Директория существует: {dir_path}")
    
    # Проверка необходимых файлов
    required_files = ['.env']
    for file_name in required_files:
        file_path = Path(file_name)
        if not file_path.exists():
            logger.warning(f"⚠️ Файл не найден: {file_path}")
            
            # Создаем пример .env файла если он отсутствует
            if file_name == '.env':
                try:
                    create_example_env()
                    logger.info(f"✅ Создан пример файла: {file_path}.example")
                except Exception as e:
                    logger.error(f"❌ Не удалось создать пример .env файла: {e}")
        else:
            logger.info(f"✅ Файл существует: {file_path}")
    
    # Проверка виртуального окружения
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.info("✅ Виртуальное окружение активировано")
    else:
        logger.warning("⚠️ Виртуальное окружение не активировано")
    
    logger.info("✅ Настройка окружения завершена")
    return True

def create_example_env():
    """Создание примера .env файла"""
    env_example_content = """# Токен бота Telegram (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# Настройки базы данных
DB_PATH=data/users.db

# Настройки Redis (опционально)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Веб-настройки (для будущего веб-интерфейса)
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_SECRET=your_secret_key_here

# Настройки S3 для бэкапов (опционально)
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_REGION=

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
ERROR_LOG_FILE=logs/errors.log

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# Режимы работы
DEBUG_MODE=False
MAINTENANCE_MODE=False

# Настройки бота
BOT_USERNAME=
BOT_NAME=GromFitBot
BOT_DESCRIPTION=Спортивные дуэли на токенах

# Экономические настройки
START_TOKENS=50.0
REFERRAL_BONUS=10.0
DAILY_BONUS_BASE=5.0
DAILY_STREAK_MULTIPLIER=1.2

# Настройки регистрации
MIN_NICKNAME_LENGTH=3
MAX_NICKNAME_LENGTH=20
ALLOWED_REGIONS=Москва,Санкт-Петербург,Новосибирск,Екатеринбург,Казань

# Настройки магазина
SHOP_ENABLED=True
MAX_PURCHASE_PER_DAY=10
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example_content)

def init_message_manager_in_modules(bot):
    """Инициализация менеджера сообщений во всех модулях"""
    logger.info("Инициализация менеджера сообщений в модулях...")
    
    try:
        # Импортируем функции инициализации из каждого модуля
        from modules.referrals.handlers import init_message_manager as init_ref
        from modules.profile.handlers import init_message_manager as init_prof
        from modules.shop.handlers import init_message_manager as init_shop
        from modules.bonus.handlers import init_message_manager as init_bonus
        
        # Инициализируем менеджер сообщений в каждом модуле
        init_ref(bot)
        init_prof(bot)
        init_shop(bot)
        init_bonus(bot)
        
        logger.info("✅ Менеджер сообщений инициализирован во всех модулях")
        return True
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта при инициализации модулей: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации менеджера сообщений: {e}")
        return False

def check_database():
    """Проверка базы данных"""
    try:
        from core.database import Database
        db = Database()
        
        if db.test_connection():
            user_count = db.get_user_count()
            logger.info(f"✅ База данных подключена. Пользователей: {user_count}")
            return True
        else:
            logger.error("❌ Не удалось подключиться к базе данных")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка проверки базы данных: {e}")
        return False

async def main_async():
    """Асинхронная точка входа"""
    logger.info("=" * 60)
    logger.info("Запуск GromFitBot v4.1")
    logger.info("=" * 60)
    
    # Настройка окружения
    if not setup_environment():
        logger.error("❌ Не удалось настроить окружение. Завершение работы.")
        return
    
    # Проверка базы данных
    if not check_database():
        logger.warning("⚠️ Проблемы с базой данных. Бот может работать некорректно.")
    
    # Импортируем основной класс бота
    from core.bot import GromFitBot
    
    try:
        # Создаем экземпляр бота
        bot_instance = GromFitBot()
        logger.info("✅ Экземпляр бота создан")
        
        # Инициализируем менеджер сообщений в модулях
        if not init_message_manager_in_modules(bot_instance.bot):
            logger.warning("⚠️ Не удалось инициализировать менеджер сообщений в модулях")
        
        # Запускаем бота
        logger.info("🚀 Запуск бота...")
        await bot_instance.start()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        logger.info("Проверьте, что все зависимости установлены:")
        logger.info("pip install -r requirements.txt")
        return
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        logger.exception("Детали ошибки:")
        raise
    finally:
        logger.info("✅ Работа бота завершена")

def main():
    """Основная точка входа"""
    try:
        # Запускаем асинхронную функцию
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        raise

if __name__ == "__main__":
    main()