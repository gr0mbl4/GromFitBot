"""
Основной файл бота GromFitBot - полная версия
Исправления всех критических ошибок навигации
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.exceptions import TelegramAPIError

from core.config import Config
from core.database import Database
from modules.keyboards.main_keyboards import MainKeyboards
from core.message_manager import MessageManager

# Импорт всех модулей
from modules.auth.registration import router as auth_router
from modules.profile.handlers import router as profile_router
from modules.referrals.handlers import router as referrals_router
from modules.shop.handlers import router as shop_router
from modules.bonus.handlers import router as bonus_router
from modules.auth.registration import start_registration

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class GromFitBot:
    """Основной класс бота GromFit - полная реализация"""
    
    def __init__(self):
        """Полная инициализация бота"""
        self.config = Config()
        self.bot = Bot(token=self.config.BOT_TOKEN)
        self.dp = Dispatcher()
        self.db = Database(self.config.DB_PATH)
        
        # Инициализируем менеджер сообщений
        self.message_manager = MessageManager(self.bot)
        
        # Основной роутер для общих команд
        self.common_router = Router()
        
        # Хранилище состояний пользователей (для навигации)
        self.user_states: Dict[int, Dict[str, Any]] = {}
        
        # Регистрация всех роутеров
        self._register_routers()
        
        # Регистрация общих обработчиков
        self._register_common_handlers()
        
        # Регистрация обработчиков команд
        self._register_command_handlers()
        
        # Инициализация модулей
        self._init_modules()
    
    def _register_routers(self):
        """Регистрация всех роутеров системы"""
        logger.info("Регистрация роутеров...")
        
        # Порядок важен: общий роутер должен быть первым
        self.dp.include_router(self.common_router)
        self.dp.include_router(auth_router)
        self.dp.include_router(profile_router)
        self.dp.include_router(referrals_router)
        self.dp.include_router(shop_router)
        self.dp.include_router(bonus_router)
        
        logger.info(f"Зарегистрировано роутеров: 6")
    
    def _register_common_handlers(self):
        """Регистрация общих обработчиков кнопок и сообщений"""
        
        # ==================== ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ ====================
        
        @self.common_router.message(F.text == "🏠 Главное меню")
        async def handle_main_menu_button(message: Message):
            """Обработчик кнопки 'Главное меню' из любого места"""
            logger.info(f"Кнопка 'Главное меню' от пользователя {message.from_user.id}")
            await self._show_main_menu(message)
        
        @self.common_router.message(F.text == "📝 Записать результат")
        async def handle_record_result(message: Message):
            """Обработчик кнопки 'Записать результат' - только сообщение"""
            logger.info(f"Кнопка 'Записать результат' от пользователя {message.from_user.id}")
            await self._handle_record_result(message)
        
        @self.common_router.message(F.text == "🛒 Магазин")
        async def handle_shop_button(message: Message):
            """Обработчик кнопки 'Магазин' из нижнего меню"""
            logger.info(f"Кнопка 'Магазин' от пользователя {message.from_user.id}")
            await self._redirect_to_module(message, "shop")
        
        @self.common_router.message(F.text == "👤 Профиль")
        async def handle_profile_button(message: Message):
            """Обработчик кнопки 'Профиль' из нижнего меню"""
            logger.info(f"Кнопка 'Профиль' от пользователя {message.from_user.id}")
            await self._redirect_to_module(message, "profile")
        
        @self.common_router.message(F.text == "📊 Статистика")
        async def handle_statistics_button(message: Message):
            """Обработчик кнопки 'Статистика'"""
            logger.info(f"Кнопка 'Статистика' от пользователя {message.from_user.id}")
            await self._handle_statistics(message)
        
        @self.common_router.message(F.text == "🤼 Дуэли")
        async def handle_duels_button(message: Message):
            """Обработчик кнопки 'Дуэли'"""
            logger.info(f"Кнопка 'Дуэли' от пользователя {message.from_user.id}")
            await self._handle_duels(message)
        
        @self.common_router.message(F.text == "🎯 Достижения")
        async def handle_achievements_button(message: Message):
            """Обработчик кнопки 'Достижения'"""
            logger.info(f"Кнопка 'Достижения' от пользователя {message.from_user.id}")
            await self._handle_achievements(message)
        
        @self.common_router.message(F.text == "📈 Топы")
        async def handle_tops_button(message: Message):
            """Обработчик кнопки 'Топы'"""
            logger.info(f"Кнопка 'Топы' от пользователя {message.from_user.id}")
            await self._handle_tops(message)
        
        @self.common_router.message(F.text == "🤝 Рефералы")
        async def handle_referrals_button(message: Message):
            """Обработчик кнопки 'Рефералы'"""
            logger.info(f"Кнопка 'Рефералы' от пользователя {message.from_user.id}")
            await self._redirect_to_module(message, "referrals")
        
        @self.common_router.message(F.text == "🎁 Бонусы")
        async def handle_bonuses_button(message: Message):
            """Обработчик кнопки 'Бонусы'"""
            logger.info(f"Кнопка 'Бонусы' от пользователя {message.from_user.id}")
            await self._redirect_to_module(message, "bonus")
        
        # ==================== ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ ====================
        
        @self.common_router.callback_query(F.data == "back_to_main")
        async def handle_back_to_main_callback(callback: CallbackQuery):
            """Обработчик callback 'Назад в главное меню'"""
            logger.info(f"Callback 'back_to_main' от пользователя {callback.from_user.id}")
            await self._handle_back_to_main_callback(callback)
        
        # ==================== ОБРАБОТЧИКИ ТЕКСТОВЫХ КОМАНД ====================
        
        @self.common_router.message(F.text == "/menu")
        async def handle_menu_command(message: Message):
            """Обработчик команды /menu"""
            await self._show_main_menu(message)
        
        @self.common_router.message(F.text == "/help")
        async def handle_help_command(message: Message):
            """Обработчик команды /help"""
            await self._show_help(message)
        
        logger.info("Общие обработчики зарегистрированы")
    
    def _register_command_handlers(self):
        """Регистрация обработчиков команд"""
        
        @self.common_router.message(CommandStart())
        async def handle_start_command(message: Message):
            """Обработчик команды /start"""
            logger.info(f"Команда /start от пользователя {message.from_user.id}")
            await self._handle_start_command(message)
        
        @self.common_router.message(Command("id"))
        async def handle_id_command(message: Message):
            """Обработчик команды /id"""
            await message.answer(f"Ваш Telegram ID: <code>{message.from_user.id}</code>")
        
        @self.common_router.message(Command("ping"))
        async def handle_ping_command(message: Message):
            """Обработчик команды /ping"""
            await message.answer("🏓 Pong! Бот работает.")
    
    def _init_modules(self):
        """Инициализация всех модулей с менеджером сообщений"""
        try:
            # Импортируем функции инициализации из модулей
            from modules.referrals.handlers import init_message_manager as init_ref
            from modules.profile.handlers import init_message_manager as init_prof
            from modules.shop.handlers import init_message_manager as init_shop
            from modules.bonus.handlers import init_message_manager as init_bonus
            
            # Инициализируем менеджер сообщений в каждом модуле
            init_ref(self.bot)
            init_prof(self.bot)
            init_shop(self.bot)
            init_bonus(self.bot)
            
            logger.info("Модули инициализированы с менеджером сообщений")
        except ImportError as e:
            logger.error(f"Ошибка импорта при инициализации модулей: {e}")
        except Exception as e:
            logger.error(f"Ошибка инициализации модулей: {e}")
    
    async def _handle_start_command(self, message: Message):
        """Полная обработка команды /start"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        # Проверяем параметры команды (для реферальных ссылок)
        command_args = message.text.split()
        referral_id = None
        
        if len(command_args) > 1 and command_args[1].startswith("ref"):
            try:
                referral_id = int(command_args[1][3:])
                logger.info(f"Реферальная ссылка обнаружена: {referral_id}")
            except ValueError:
                logger.warning(f"Неверный формат реферальной ссылки: {command_args[1]}")
        
        if user:
            # Пользователь зарегистрирован
            logger.info(f"Пользователь {user_id} уже зарегистрирован")
            
            # Обновляем последнюю активность
            self.db.update_user_last_active(user_id)
            
            # Обрабатываем реферальную ссылку (если есть и пользователь новый)
            if referral_id and not user.get('referrer_id'):
                self.db.update_user_field(user_id, 'referrer_id', referral_id)
                referrer = self.db.get_user(referral_id)
                if referrer:
                    # Обновляем счетчик рефералов у реферера
                    new_count = referrer.get('referrals_count', 0) + 1
                    self.db.update_user_field(referral_id, 'referrals_count', new_count)
                    logger.info(f"Реферер {referral_id} получил нового реферала {user_id}")
            
            # Показываем главное меню
            await self._show_main_menu(message)
        else:
            # Пользователь не зарегистрирован - запускаем регистрацию
            logger.info(f"Пользователь {user_id} не зарегистрирован, запуск регистрации")
            
            # Сохраняем referral_id в состоянии пользователя для использования при регистрации
            if referral_id:
                self.user_states[user_id] = {'referral_id': referral_id}
            
            await start_registration(message)
    
    async def _show_main_menu(self, message: Message):
        """Показ главного меню с заменой сообщения"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            # Пользователь не найден - предлагаем регистрацию
            logger.warning(f"Пользователь {user_id} не найден при показе главного меню")
            await self.message_manager.replace_message(
                message,
                "❌ <b>Вы не зарегистрированы</b>\n\n"
                "Используйте команду /start для регистрации в боте."
            )
            return
        
        # Формируем текст главного меню
        menu_text = (
            f"🏠 <b>Главное меню</b>\n\n"
            f"Приветствуем, <b>{user['nickname']}</b>!\n"
            f"<i>ID: {user['registration_number']}</i>\n\n"
            f"💎 <b>Баланс:</b> {user.get('balance_tokens', 0):.0f} токенов\n"
            f"📊 <b>Уровень:</b> {user.get('level', 1)}\n"
            f"🤝 <b>Рефералов:</b> {user.get('referrals_count', 0)}\n\n"
            f"Выберите раздел:"
        )
        
        # Получаем клавиатуру главного меню
        main_keyboard = MainKeyboards.get_main_menu()
        
        # Заменяем сообщение главным меню
        await self.message_manager.replace_message(
            message,
            menu_text,
            main_keyboard
        )
        
        logger.info(f"Главное меню показано пользователю {user_id}")
    
    async def _handle_record_result(self, message: Message):
        """Обработка кнопки 'Записать результат' - ТОЛЬКО сообщение"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.message_manager.replace_message(
                message,
                "❌ <b>Вы не зарегистрированы</b>\n\n"
                "Используйте команду /start для регистрации."
            )
            return
        
        # ТОЛЬКО сообщение, БЕЗ главного меню
        await self.message_manager.replace_message(
            message,
            "📝 <b>Запись результата тренировки</b>\n\n"
            "🚧 <b>Эта функция находится в активной разработке</b>\n\n"
            "Скоро вы сможете:\n"
            "• Записывать свои тренировки\n"
            "• Участвовать в спортивных дуэлях\n"
            "• Бросать вызовы друзьям\n"
            "• Зарабатывать токены за достижения\n\n"
            "<i>Следите за обновлениями!</i>"
        )
        
        logger.info(f"Пользователь {user_id} запросил запись результата")
    
    async def _redirect_to_module(self, message: Message, module_name: str):
        """Перенаправление в указанный модуль"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.message_manager.replace_message(
                message,
                "❌ <b>Вы не зарегистрированы</b>\n\n"
                "Используйте команду /start для регистрации."
            )
            return
        
        # Обновляем последнюю активность
        self.db.update_user_last_active(user_id)
        
        logger.info(f"Перенаправление пользователя {user_id} в модуль {module_name}")
        
        # В зависимости от модуля вызываем соответствующий обработчик
        try:
            if module_name == "profile":
                from modules.profile.handlers import handle_profile
                await handle_profile(message)
            elif module_name == "referrals":
                from modules.referrals.handlers import handle_referrals
                await handle_referrals(message)
            elif module_name == "shop":
                from modules.shop.handlers import handle_shop
                await handle_shop(message)
            elif module_name == "bonus":
                from modules.bonus.handlers import handle_bonus
                await handle_bonus(message)
            else:
                await self.message_manager.replace_message(
                    message,
                    f"❌ Модуль '{module_name}' не найден"
                )
        except ImportError as e:
            logger.error(f"Ошибка импорта модуля {module_name}: {e}")
            await self.message_manager.replace_message(
                message,
                f"❌ Ошибка загрузки модуля {module_name}"
            )
        except Exception as e:
            logger.error(f"Ошибка выполнения модуля {module_name}: {e}")
            await self.message_manager.replace_message(
                message,
                f"❌ Ошибка в модуле {module_name}"
            )
    
    async def _handle_statistics(self, message: Message):
        """Обработчик кнопки 'Статистика'"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.message_manager.replace_message(
                message,
                "❌ <b>Вы не зарегистрированы</b>\n\n"
                "Используйте команду /start для регистрации."
            )
            return
        
        # Формируем статистику
        stats_text = (
            f"📊 <b>Ваша статистика</b>\n\n"
            f"<b>Основное:</b>\n"
            f"• Тренировок: <b>{user.get('total_trainings', 0)}</b>\n"
            f"• Дуэлей: <b>{user.get('total_duels', 0)}</b>\n"
            f"• Побед: <b>{user.get('duels_won', 0)}</b>\n"
            f"• Поражений: <b>{user.get('total_duels', 0) - user.get('duels_won', 0)}</b>\n\n"
            f"<b>Прогресс:</b>\n"
            f"• Уровень: <b>{user.get('level', 1)}</b>\n"
            f"• Опыт: <b>{user.get('experience', 0)}/1000</b>\n"
            f"• Очков: <b>{user.get('total_points', 0)}</b>\n\n"
            f"<b>Достижения:</b>\n"
            f"• Получено: <b>{user.get('achievements_count', 0)}/200</b>\n"
            f"• Серия дней: <b>{user.get('daily_streak', 0)}</b>\n"
        )
        
        await self.message_manager.replace_message(
            message,
            stats_text,
            MainKeyboards.get_navigation_keyboard("statistics")
        )
    
    async def _handle_duels(self, message: Message):
        """Обработчик кнопки 'Дуэли'"""
        await self.message_manager.replace_message(
            message,
            "🤼 <b>Спортивные дуэли</b>\n\n"
            "🚧 <b>Раздел в разработке</b>\n\n"
            "Скоро вы сможете:\n"
            "• Бросать вызовы другим спортсменам\n"
            "• Участвовать в групповых соревнованиях\n"
            "• Ставить токены на победу\n"
            "• Получать уникальные достижения\n\n"
            "<i>Готовьтесь к бою!</i>",
            MainKeyboards.get_navigation_keyboard("duels")
        )
    
    async def _handle_achievements(self, message: Message):
        """Обработчик кнопки 'Достижения'"""
        user_id = message.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.message_manager.replace_message(
                message,
                "❌ <b>Вы не зарегистрированы</b>\n\n"
                "Используйте команду /start для регистрации."
            )
            return
        
        # Получаем достижения пользователя
        achievements = self.db.get_user_achievements(user_id)
        
        if achievements:
            achievements_text = "\n".join([f"🏆 {ach['title']}" for ach in achievements[:5]])
            if len(achievements) > 5:
                achievements_text += f"\n... и ещё {len(achievements) - 5}"
        else:
            achievements_text = "Пока нет достижений"
        
        await self.message_manager.replace_message(
            message,
            f"🎯 <b>Ваши достижения</b>\n\n"
            f"Всего получено: <b>{len(achievements)}/200</b>\n\n"
            f"<b>Последние достижения:</b>\n"
            f"{achievements_text}\n\n"
            f"<i>Выполняйте задания и получайте новые достижения!</i>",
            MainKeyboards.get_navigation_keyboard("achievements")
        )
    
    async def _handle_tops(self, message: Message):
        """Обработчик кнопки 'Топы'"""
        # Получаем топ пользователей по разным критериям
        top_tokens = self.db.get_top_users_by_field('balance_tokens', limit=5)
        top_referrals = self.db.get_top_referrers(limit=5)
        top_trainings = self.db.get_top_users_by_field('total_trainings', limit=5)
        
        # Формируем текст топа
        tops_text = "📈 <b>Топы GromFit</b>\n\n"
        
        tops_text += "<b>🥇 По токенам:</b>\n"
        for i, user in enumerate(top_tokens, 1):
            tops_text += f"{i}. {user['nickname']} - {user['balance_tokens']:.0f} токенов\n"
        
        tops_text += "\n<b>🤝 По рефералам:</b>\n"
        for i, user in enumerate(top_referrals, 1):
            tops_text += f"{i}. {user['nickname']} - {user['referrals_count']} чел.\n"
        
        tops_text += "\n<b>💪 По тренировкам:</b>\n"
        for i, user in enumerate(top_trainings, 1):
            tops_text += f"{i}. {user['nickname']} - {user['total_trainings']} тренировок\n"
        
        tops_text += "\n<i>Соревнуйтесь и попадайте в топы!</i>"
        
        await self.message_manager.replace_message(
            message,
            tops_text,
            MainKeyboards.get_navigation_keyboard("tops")
        )
    
    async def _handle_back_to_main_callback(self, callback: CallbackQuery):
        """Обработчик callback 'Назад в главное меню'"""
        user_id = callback.from_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.message_manager.answer_callback_with_notification(
                callback,
                "❌ Вы не зарегистрированы",
                show_alert=True
            )
            return
        
        # Создаем Message объект из callback
        msg = Message(
            message_id=callback.message.message_id,
            date=callback.message.date,
            chat=callback.message.chat,
            from_user=callback.from_user,
            text="🏠 Главное меню"
        )
        msg.bot = callback.bot
        
        # Показываем главное меню
        await self._show_main_menu(msg)
        
        # Отвечаем на callback
        await self.message_manager.answer_callback_with_notification(callback)
    
    async def _show_help(self, message: Message):
        """Показать помощь"""
        help_text = (
            "🆘 <b>Помощь по боту GromFit</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Начать работу с ботом\n"
            "/menu - Главное меню\n"
            "/help - Эта справка\n"
            "/id - Показать ваш ID\n\n"
            "<b>Навигация:</b>\n"
            "• Используйте кнопки в меню для навигации\n"
            "• Кнопки под чатом всегда доступны\n"
            "• Для возврата используйте кнопку 'Назад'\n\n"
            "<b>Поддержка:</b>\n"
            "По вопросам работы бота обращайтесь к @admin\n\n"
            "<i>Бот находится в активной разработке</i>"
        )
        
        await self.message_manager.replace_message(message, help_text)
    
    async def start(self):
        """Полный запуск бота"""
        logger.info("=" * 50)
        logger.info("Запуск GromFitBot v4.1")
        logger.info("=" * 50)
        
        # Проверка конфигурации
        if not self.config.validate():
            logger.error("❌ Неверная конфигурация бота!")
            return
        
        # Проверка соединения с БД
        if not self.db.test_connection():
            logger.error("❌ Не удалось подключиться к базе данных!")
            return
        
        # Проверка токена бота
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"✅ Бот авторизован как: @{bot_info.username}")
            logger.info(f"✅ ID бота: {bot_info.id}")
            logger.info(f"✅ Имя бота: {bot_info.first_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка авторизации бота: {e}")
            return
        
        # Проверка количества пользователей
        user_count = self.db.get_user_count()
        logger.info(f"📊 Пользователей в базе: {user_count}")
        
        logger.info("✅ Все проверки пройдены успешно")
        logger.info("🚀 Бот запускается...")
        
        try:
            # Запуск polling
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                handle_signals=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен пользователем (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
            raise
        finally:
            # Завершение работы
            await self.bot.session.close()
            logger.info("✅ Сессия бота закрыта")

def main():
    """Точка входа в приложение"""
    bot = GromFitBot()
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        raise

if __name__ == "__main__":
    main()