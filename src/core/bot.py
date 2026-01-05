"""
Главный класс бота GromFit
Исправленная версия с правильной настройкой клавиатур
"""

import asyncio
import logging
import sys
import os
from typing import Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message
from aiogram.filters import Command
from aiogram import F

from src.core.config import Config
from src.core.database import Database
from src.modules.auth.registration import router as auth_router
from src.modules.profile.handlers import router as profile_router
from src.modules.referrals.handlers import router as referrals_router
from src.modules.bonus.handlers import router as bonus_router
from src.modules.shop.handlers import router as shop_router
from src.modules.keyboards.main_keyboards import MainKeyboards

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class GromFitBot:
    """Основной класс бота GromFit"""
    
    def __init__(self):
        """Инициализация бота"""
        self.config = Config()
        self.bot = None
        self.dp = None
        self.db = Database()
        
        # Валидируем конфигурацию
        self._validate_config()
        
        # Инициализация асинхронных объектов
        self._init_async_objects()
    
    def _validate_config(self):
        """Валидация конфигурации"""
        try:
            Config.validate()
            logger.info("✅ Конфигурация проверена")
        except ValueError as e:
            logger.error(f"❌ Ошибка конфигурации: {e}")
            raise
    
    def _init_async_objects(self):
        """Инициализация асинхронных объектов"""
        self.bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Используем MemoryStorage для состояний
        storage = MemoryStorage()
        self.dp = Dispatcher(storage=storage)
    
    def _setup_routers(self):
        """Настройка роутеров"""
        # Создаем общий роутер для обработки кнопки "Главное меню"
        common_router = Router()
        
        @common_router.message(F.text == "🏠 Главное меню")
        async def handle_main_menu_button(message: Message):
            """Обработчик кнопки 'Главное меню'"""
            telegram_id = message.from_user.id
            
            user = self.db.get_user(telegram_id)
            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
                return
            
            text = (
                "🏠 <b>ГЛАВНОЕ МЕНЮ GROMFIT</b>\n\n"
                "Выберите раздел для навигации:\n\n"
                "• 🏋️‍♂️ <b>ПРОФИЛЬ</b> - ваши данные и статистика\n"
                "• ⚔️ <b>ДУЭЛИ</b> - спортивные соревнования (скоро)\n"
                "• 📊 <b>ТРЕНИРОВКИ</b> - запись тренировок (скоро)\n"
                "• 🎯 <b>ДОСТИЖЕНИЯ</b> - ваши награды и ачивки (скоро)\n"
                "• 💰 <b>МАГАЗИН</b> - покупка товаров за токены\n"
                "• 👥 <b>РЕФЕРАЛЫ</b> - приглашение друзей и бонусы\n"
                "• 🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b> - ежедневная награда\n\n"
                "<i>Основные кнопки всегда доступны ниже ↓</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        @common_router.message(Command("menu"))
        async def handle_menu_command(message: Message):
            """Обработчик команды /menu"""
            telegram_id = message.from_user.id
            
            user = self.db.get_user(telegram_id)
            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
                return
            
            text = (
                "🏠 <b>ГЛАВНОЕ МЕНЮ GROMFIT</b>\n\n"
                "Выберите раздел для навигации:\n\n"
                "• 🏋️‍♂️ <b>ПРОФИЛЬ</b> - ваши данные и статистика\n"
                "• ⚔️ <b>ДУЭЛИ</b> - спортивные соревнования (скоро)\n"
                "• 📊 <b>ТРЕНИРОВКИ</b> - запись тренировок (скоро)\n"
                "• 🎯 <b>ДОСТИЖЕНИЯ</b> - ваши награды и ачивки (скоро)\n"
                "• 💰 <b>МАГАЗИН</b> - покупка товаров за токены\n"
                "• 👥 <b>РЕФЕРАЛЫ</b> - приглашение друзей и бонусы\n"
                "• 🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b> - ежедневная награда\n\n"
                "<i>Основные кнопки всегда доступны ниже ↓</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        @common_router.message(F.text == "⬅️ Назад")
        async def handle_back_button(message: Message):
            """Обработчик кнопки 'Назад'"""
            await handle_main_menu_button(message)
        
        @common_router.message(F.text == "📝 Записать результат")
        async def handle_record_result(message: Message):
            """Обработчик кнопки 'Записать результат'"""
            text = (
                "📝 <b>ЗАПИСЬ РЕЗУЛЬТАТА</b>\n\n"
                "Функция записи результатов тренировок будет доступна в ближайшем обновлении!\n\n"
                "А пока вы можете:\n"
                "• Посмотреть свой профиль\n"
                "• Пригласить друзей\n"
                "• Получить ежедневный бонус\n"
                "• Посетить магазин\n\n"
                "<i>Следите за обновлениями!</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_bottom_keyboard())
        
        @common_router.message(F.text == "⚔️ ДУЭЛИ")
        async def handle_duels(message: Message):
            """Обработчик кнопки 'ДУЭЛИ'"""
            text = (
                "⚔️ <b>СИСТЕМА ДУЭЛЕЙ</b>\n\n"
                "Система спортивных дуэлей находится в разработке!\n\n"
                "<b>Скоро вы сможете:</b>\n"
                "• Бросать вызовы друзьям\n"
                "• Участвовать в соревнованиях\n"
                "• Делать ставки токенами\n"
                "• Зарабатывать награды\n\n"
                "<i>Оставайтесь на связи!</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        @common_router.message(F.text == "📊 ТРЕНИРОВКИ")
        async def handle_trainings(message: Message):
            """Обработчик кнопки 'ТРЕНИРОВКИ'"""
            text = (
                "📊 <b>СИСТЕМА ТРЕНИРОВОК</b>\n\n"
                "Система учета тренировок находится в разработке!\n\n"
                "<b>Скоро вы сможете:</b>\n"
                "• Записывать свои тренировки\n"
                "• Следить за прогрессом\n"
                "• Получать достижения\n"
                "• Сравнивать результаты\n\n"
                "<i>Оставайтесь на связи!</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        @common_router.message(F.text == "🎯 ДОСТИЖЕНИЯ")
        async def handle_achievements(message: Message):
            """Обработчик кнопки 'ДОСТИЖЕНИЯ'"""
            text = (
                "🎯 <b>СИСТЕМА ДОСТИЖЕНИЙ</b>\n\n"
                "Система достижений находится в разработке!\n\n"
                "<b>Скоро вы сможете:</b>\n"
                "• Получать награды за активность\n"
                "• Собирать коллекцию достижений\n"
                "• Показывать свои успехи\n"
                "• Соревноваться с друзьями\n\n"
                "<i>Оставайтесь на связи!</i>"
            )
            
            await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        # Регистрация всех роутеров в правильном порядке
        self.dp.include_router(auth_router)
        self.dp.include_router(profile_router)
        self.dp.include_router(referrals_router)
        self.dp.include_router(bonus_router)
        self.dp.include_router(shop_router)
        self.dp.include_router(common_router)  # Общие обработчики должны быть последними
    
    async def setup_bot_commands(self):
        """Настройка команд бота"""
        commands = [
            BotCommand(command="start", description="🚀 Запустить бота"),
            BotCommand(command="profile", description="👤 Профиль пользователя"),
            BotCommand(command="referrals", description="👥 Реферальная система"),
            BotCommand(command="shop", description="🛒 Магазин"),
            BotCommand(command="bonus", description="🎁 Ежедневный бонус"),
            BotCommand(command="menu", description="🏠 Главное меню"),
            BotCommand(command="help", description="❓ Помощь"),
        ]
        
        try:
            await self.bot.set_my_commands(commands)
            logger.info("✅ Команды бота настроены")
        except Exception as e:
            logger.error(f"❌ Ошибка настройки команд бота: {e}")
    
    async def setup_middlewares(self):
        """Настройка middleware"""
        # Здесь можно добавить middleware при необходимости
        pass
    
    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("🚀 Запуск GromFit Bot...")
        
        try:
            # Инициализация базы данных
            self.db.initialize()
            logger.info("✅ База данных инициализирована")
            
            # Настройка команд
            await self.setup_bot_commands()
            
            # Настройка middleware
            await self.setup_middlewares()
            
            # Настройка роутеров
            self._setup_routers()
            
            logger.info("✅ Бот успешно запущен и готов к работе")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
    
    async def on_shutdown(self):
        """Действия при остановке бота"""
        logger.info("🛑 Остановка GromFit Bot...")
        
        try:
            # Закрываем соединения
            await self.bot.session.close()
            logger.info("✅ Сессия бота закрыта")
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    async def start(self):
        """Запуск бота"""
        try:
            # Действия при запуске
            await self.on_startup()
            
            # Запуск поллинга
            logger.info("📡 Ожидание сообщений...")
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            await self.on_shutdown()
    
    async def stop(self):
        """Остановка бота"""
        await self.on_shutdown()