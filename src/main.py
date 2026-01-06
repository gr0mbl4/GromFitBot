"""
Главный файл бота GromFit
Точка входа в приложение
"""

import asyncio
import logging
import logging.config
import os
import sys

# Добавляем путь к родительской директории для импорта src
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.core.config import BOT_TOKEN, LOGGING_CONFIG

# Настройка логирования
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    
    logger.info("🚀 Запуск GromFitBot...")
    
    try:
        # Проверяем токен бота (смягченная проверка для тестирования)
        if not BOT_TOKEN:
            logger.error("❌ Токен бота не установлен.")
            print("❌ ОШИБКА: Токен бота не установлен!")
            print("Проверьте файл .env и убедитесь, что BOT_TOKEN установлен.")
            return
        
        logger.info(f"🤖 Бот инициализирован с токеном: {BOT_TOKEN[:10]}...")
        
        # Создаем экземпляр бота
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Создаем диспетчер
        dp = Dispatcher()
        
        # Импортируем и инициализируем бота
        from src.core.bot import GromFitBot
        gromfit_bot = GromFitBot(bot, dp)
        
        # Настраиваем роутеры
        gromfit_bot.setup()
        
        logger.info("✅ Бот инициализирован. Начинаем polling...")
        print("=" * 50)
        print("🤖 GROMFIT BOT ЗАПУЩЕН!")
        print("=" * 50)
        print("Статус: 🟢 АКТИВЕН")
        print(f"Токен: {BOT_TOKEN[:10]}...")
        print("Ожидание сообщений...")
        print("=" * 50)
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Проверьте логи в папке logs/")
        raise
    finally:
        logger.info("🛑 Бот остановлен")
        print("\n🛑 Бот остановлен")

def check_environment():
    """Проверка окружения перед запуском"""
    print("🔍 Проверка окружения...")
    
    # Проверяем наличие .env файла
    env_file = os.path.join(parent_dir, '.env')
    if not os.path.exists(env_file):
        print("⚠️ Файл .env не найден. Используются значения по умолчанию.")
        # Создаем .env файл с тестовым токеном
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("BOT_TOKEN=8170901723:AAFCJDYlQqvcKxiNVvQrM3n1R9snzWljeC8\n")
                f.write("REDIS_HOST=localhost\n")
                f.write("REDIS_PORT=6379\n")
                f.write("WEB_HOST=0.0.0.0\n")
                f.write("WEB_PORT=8080\n")
            print("✅ Создан файл .env с тестовым токеном")
        except Exception as e:
            print(f"⚠️ Не удалось создать .env файл: {e}")
    
    # Проверяем наличие базы данных
    db_dir = os.path.join(parent_dir, 'data')
    if not os.path.exists(db_dir):
        print("📁 Создаю директорию data...")
        os.makedirs(db_dir, exist_ok=True)
    
    # Проверяем наличие логов
    logs_dir = os.path.join(parent_dir, 'logs')
    if not os.path.exists(logs_dir):
        print("📁 Создаю директорию logs...")
        os.makedirs(logs_dir, exist_ok=True)
    
    print("✅ Окружение проверено")
    return True

if __name__ == "__main__":
    # Проверяем окружение перед запуском
    if not check_environment():
        print("❌ Запуск отменен из-за проблем с окружением")
        sys.exit(1)
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ Непредвиденная ошибка: {e}")
        sys.exit(1)