"""
Главный класс бота GromFit с кнопками под чатом
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Импортируем модули
from src.modules.auth.registration import router as auth_router
from src.modules.profile.handlers import router as profile_router
from src.modules.referrals.handlers import router as referral_router
from src.modules.finance.handlers import router as finance_router

# Импортируем новые модули
try:
    from src.modules.bonus.handlers import router as bonus_router
    HAS_BONUS_MODULE = True
except ImportError:
    HAS_BONUS_MODULE = False
    print("⚠️ Модуль бонусов не найден, пропускаем...")

try:
    from src.modules.shop.handlers import router as shop_router
    HAS_SHOP_MODULE = True
except ImportError:
    HAS_SHOP_MODULE = False
    print("⚠️ Модуль магазина не найден, пропускаем...")

# Импортируем системы
from src.modules.referrals.system import referral_system
from src.modules.finance.token_system import token_system

# Загружаем переменные окружения
load_dotenv()

class GromFitBot:
    """Главный класс бота GromFit"""
    
    def __init__(self):
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
        
        # Получаем токен из .env
        self.TOKEN = os.getenv("BOT_TOKEN", "")
        
        if not self.TOKEN:
            self.logger.error("[ERROR] Токен бота не найден! Укажите BOT_TOKEN в .env файле")
            exit(1)
        
        # Инициализация бота с увеличенными таймаутами
        self.bot = Bot(
            token=self.TOKEN,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True  # Отключаем предпросмотр ссылок для уменьшения нагрузки
            )
        )
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        
        # Настройка систем
        self._setup_systems()
        
        # Регистрация модулей
        self._register_modules()
        
        # Установка команд бота
        self._set_commands()
        
        self.logger.info("[OK] Бот GromFit инициализирован")
    
    def _setup_systems(self):
        """Настройка взаимодействия систем"""
        # Передаем систему токенов в реферальную систему
        referral_system.set_token_system(token_system)
        
        # Бонусы уже установлены в token_system (25 токенов пригласившему, 50 приглашенному)
        self.logger.info("[OK] Системы настроены")
    
    def _register_modules(self):
        """Регистрация всех модулей бота"""
        
        # Модуль авторизации и регистрации
        self.dp.include_router(auth_router)
        
        # Модуль профиля
        self.dp.include_router(profile_router)
        
        # Модуль реферальной системы
        self.dp.include_router(referral_router)
        
        # Модуль финансовой системы
        self.dp.include_router(finance_router)
        
        # Модуль ежедневных бонусов (если существует)
        if HAS_BONUS_MODULE:
            self.dp.include_router(bonus_router)
            self.logger.info("[OK] Модуль бонусов зарегистрирован")
        else:
            self.logger.info("[INFO] Модуль бонусов не найден, пропускаем")
        
        # Модуль магазина (если существует)
        if HAS_SHOP_MODULE:
            self.dp.include_router(shop_router)
            self.logger.info("[OK] Модуль магазина зарегистрирован")
        else:
            self.logger.info("[INFO] Модуль магазина не найден, пропускаем")
        
        self.logger.info("[OK] Модули зарегистрированы")
    
    def _set_commands(self):
        """Установка команд бота"""
        from aiogram.types import BotCommand, BotCommandScopeDefault
        
        commands = [
            BotCommand(command="/start", description="Запустить бота"),
            BotCommand(command="/profile", description="Мой профиль"),
            BotCommand(command="/menu", description="Главное меню"),
            BotCommand(command="/referrals", description="Реферальная система"),
        ]
        
        # Добавляем команду /bonus только если модуль существует
        if HAS_BONUS_MODULE:
            commands.append(BotCommand(command="/bonus", description="Ежедневный бонус"))
        
        # Добавляем команду /shop только если модуль существует
        if HAS_SHOP_MODULE:
            commands.append(BotCommand(command="/shop", description="Магазин"))
        
        async def set_bot_commands():
            try:
                await self.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
                self.logger.info("[OK] Команды бота установлены")
            except Exception as e:
                self.logger.error(f"Ошибка установки команд: {e}")
        
        # Запускаем установку команд
        asyncio.create_task(set_bot_commands())
    
    async def start(self):
        """Запуск бота"""
        self.logger.info("[START] Запуск бота GromFit...")
        
        try:
            # Удаляем вебхук (если был)
            await self.bot.delete_webhook(drop_pending_updates=True)
            
            # Запускаем polling с настройкой обработки обновлений
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                skip_updates=True,
                handle_signals=True
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска бота: {e}")
            raise
    
    async def stop(self):
        """Остановка бота"""
        self.logger.info("[STOP] Остановка бота GromFit...")
        await self.bot.session.close()