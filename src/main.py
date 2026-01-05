"""
Точка входа в приложение GromFit Bot
Исправленная версия с правильной инициализацией
"""

import asyncio
import sys
import os
import logging

# Добавляем корневую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Настройка логирования ДО импорта модулей
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска"""
    
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК GROMFIT BOT")
    logger.info("=" * 50)
    
    try:
        # Импортируем здесь, чтобы логирование уже было настроено
        from src.core.bot import GromFitBot
        
        # Создаем и запускаем бота
        bot = GromFitBot()
        
        logger.info("✅ Бот инициализирован")
        logger.info("🔄 Запуск основного цикла...")
        
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Ждем перед выходом, чтобы лог успел записаться
        await asyncio.sleep(1)
        
        # Перезапуск через 5 секунд при критической ошибке
        logger.info("♻️ Перезапуск бота через 5 секунд...")
        await asyncio.sleep(5)
        
        # Рекурсивный перезапуск
        await main()
    finally:
        logger.info("=" * 50)
        logger.info("📴 БОТ ОСТАНОВЛЕН")
        logger.info("=" * 50)

def create_required_dirs():
    """Создание необходимых директорий"""
    required_dirs = [
        'logs',
        'data',
        'users_data',
        'media/photos',
        'media/videos',
        'media/thumbnails',
        'media/documents',
        'backups/daily',
        'backups/weekly',
        'backups/manual'
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Директория создана/проверена: {dir_path}")

def check_environment():
    """Проверка окружения"""
    logger.info("🔍 Проверка окружения...")
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        logger.warning("⚠️ Файл .env не найден! Создайте его из .env.example")
        
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            logger.info("✅ Файл .env создан из .env.example")
        else:
            logger.error("❌ Файл .env.example также не найден!")
            return False
    
    # Читаем токен из .env
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'BOT_TOKEN' not in content:
                logger.error("❌ BOT_TOKEN не найден в .env файле!")
                logger.info("📋 Добавьте строку: BOT_TOKEN=ваш_токен_бота")
                return False
    except Exception as e:
        logger.error(f"❌ Ошибка чтения .env файла: {e}")
        return False
    
    # Проверяем наличие базы данных
    if not os.path.exists('data/users.db'):
        logger.warning("⚠️ База данных не найдена!")
        logger.info("   Запустите: python create_database.py")
        return False
    
    logger.info("✅ Окружение проверено")
    return True

if __name__ == "__main__":
    # Создаем необходимые директории
    create_required_dirs()
    
    # Проверяем окружение
    if not check_environment():
        logger.error("❌ Ошибка проверки окружения. Проверьте наличие всех файлов.")
        sys.exit(1)
    
    # Запускаем асинхронную main функцию
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 До свидания!")
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)