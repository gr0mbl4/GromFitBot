# src/main.py
"""
Точка входа в приложение GromFit Bot
"""

import asyncio
import sys
import os
import logging

# Добавляем корневую директорию в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.bot import GromFitBot

# Простая настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Основная функция запуска"""
    
    # Создаем и запускаем бота
    bot = GromFitBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n[STOP] Бот остановлен пользователем")
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()

if __name__ == "__main__":
    # Запускаем асинхронную main функцию
    asyncio.run(main())