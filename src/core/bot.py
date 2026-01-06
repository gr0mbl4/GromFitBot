"""
Главный класс бота GromFit
Объединяет все модули и обработчики
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

logger = logging.getLogger(__name__)

class GromFitBot:
    """Основной класс бота GromFit"""
    
    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.db = Database()
        self.common_router = Router()
        
    def setup(self):
        """Настройка всех роутеров и обработчиков"""
        self._setup_routers()
        
    def _setup_routers(self):
        """Настройка всех роутеров"""
        logger.info("🔄 Настройка роутеров...")
        
        # Импортируем модульные роутеры
        from src.modules.auth.registration import router as auth_router
        from src.modules.profile.handlers import router as profile_router
        from src.modules.referrals.handlers import router as referrals_router
        from src.modules.bonus.handlers import router as bonus_router
        from src.modules.shop.handlers import router as shop_router
        
        # ОБЩИЕ ОБРАБОТЧИКИ
        
        @self.common_router.message(Command("help"))
        async def handle_help(message: Message):
            await message.answer(
                "📚 <b>Помощь по GromFit Bot</b>\n\n"
                "Основные команды:\n"
                "/start - Начать/перезапустить бота\n"
                "/profile - Ваш профиль\n"
                "/referrals - Реферальная система\n"
                "/shop - Магазин\n"
                "/bonus - Ежедневный бонус\n"
                "/help - Эта справка\n\n"
                "📱 Используйте кнопки меню для навигации",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(Command("profile"))
        async def handle_profile_command(message: Message):
            """Обработчик команды /profile"""
            try:
                from src.modules.profile.handlers import handle_profile
                await handle_profile(message)
            except Exception as e:
                logger.error(f"Ошибка в обработчике профиля: {e}")
                await message.answer("❌ Ошибка при загрузке профиля")
        
        @self.common_router.message(Command("referrals"))
        async def handle_referrals_command(message: Message):
            """Обработчик команды /referrals"""
            try:
                from src.modules.referrals.handlers import handle_referrals
                await handle_referrals(message)
            except Exception as e:
                logger.error(f"Ошибка в обработчике рефералов: {e}")
                await message.answer("❌ Ошибка при загрузке рефералов")
        
        @self.common_router.message(Command("shop"))
        async def handle_shop_command(message: Message):
            """Обработчик команды /shop"""
            try:
                from src.modules.shop.handlers import handle_shop
                await handle_shop(message)
            except Exception as e:
                logger.error(f"Ошибка в обработчике магазина: {e}")
                await message.answer("❌ Ошибка при загрузке магазина")
        
        @self.common_router.message(Command("bonus"))
        async def handle_bonus_command(message: Message):
            """Обработчик команды /bonus"""
            try:
                from src.modules.bonus.handlers import handle_daily_bonus
                await handle_daily_bonus(message)
            except Exception as e:
                logger.error(f"Ошибка в обработчике бонуса: {e}")
                await message.answer("❌ Ошибка при загрузке бонуса")
        
        @self.common_router.message(Command("stats"))
        async def handle_stats_command(message: Message):
            """Обработчик команды /stats - статистика бота"""
            user_id = message.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer("❌ Вы не зарегистрированы. Используйте /start")
                return
            
            # Получаем общую статистику
            total_users = self.db.get_total_users_count()
            total_referrals = self.db.get_total_referrals_count()
            total_transactions = self.db.get_total_transactions_count()
            
            await message.answer(
                f"📊 <b>Статистика GromFit Bot</b>\n\n"
                f"👥 Всего пользователей: <b>{total_users}</b>\n"
                f"🤝 Всего рефералов: <b>{total_referrals}</b>\n"
                f"💰 Транзакций: <b>{total_transactions}</b>\n\n"
                f"🆔 Ваш ID: <code>{user['registration_number']}</code>",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(Command("balance"))
        async def handle_balance_command(message: Message):
            """Обработчик команды /balance - проверка баланса"""
            user_id = message.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer("❌ Вы не зарегистрированы. Используйте /start")
                return
            
            balance = user['balance_tokens']
            diamonds = user.get('balance_diamonds', 0)
            
            await message.answer(
                f"💰 <b>Ваш баланс</b>\n\n"
                f"🪙 Токены: <b>{balance}</b>\n"
                f"💎 Алмазы: <b>{diamonds}</b>\n\n"
                f"💡 Пополнить баланс можно в магазине",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        # Обработчики нижнего меню
        @self.common_router.message(F.text == "🏠 Главное меню")
        async def handle_main_menu_button(message: Message):
            """Обработчик кнопки 'Главное меню' из нижнего меню"""
            user_id = message.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer(
                    "❌ Вы не зарегистрированы.\n"
                    "Используйте /start для регистрации",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
            
            # Показываем главное меню ПОД СООБЩЕНИЕМ
            await message.answer(
                f"🏠 <b>Главное меню</b>\n\n"
                f"Приветствуем, {user['nickname']}!\n"
                f"Выберите раздел:",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(F.text == "🏋️‍♂️ Профиль")
        async def handle_personal_cabinet(message: Message):
            """Обработчик кнопки 'Профиль' из нижнего меню"""
            try:
                from src.modules.profile.handlers import handle_profile
                await handle_profile(message)
            except Exception as e:
                logger.error(f"Ошибка при открытии профиля из нижнего меню: {e}")
                await message.answer("❌ Ошибка при открытии профиля")
        
        @self.common_router.message(F.text == "📝 Записать результат")
        async def handle_record_result(message: Message):
            """Обработчик кнопки 'Записать результат'"""
            await message.answer(
                "📝 <b>Запись результата тренировки</b>\n\n"
                "Эта функция находится в разработке.\n"
                "Скоро вы сможете записывать свои тренировки и участвовать в дуэлях!",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(F.text == "💰 Магазин")
        async def handle_shop_bottom_menu(message: Message):
            """Обработчик кнопки 'Магазин' из нижнего меню"""
            try:
                from src.modules.shop.handlers import handle_shop
                await handle_shop(message)
            except Exception as e:
                logger.error(f"Ошибка при открытии магазина из нижнего меню: {e}")
                await message.answer("❌ Ошибка при открытии магазина")
        
        # Обработчики главного меню
        @self.common_router.message(F.text == "🏋️‍♂️ Профиль")
        async def handle_profile_main_menu(message: Message):
            """Обработчик кнопки 'Профиль' из главного меню"""
            await handle_personal_cabinet(message)
        
        @self.common_router.message(F.text == "⚔️ Дуэли")
        async def handle_duels_main_menu(message: Message):
            """Обработчик кнопки 'Дуэли' из главного меню"""
            await message.answer(
                "⚔️ <b>Система дуэлей</b>\n\n"
                "Бросайте вызовы другим пользователям на выполнение упражнений!\n\n"
                "🎯 <b>Как это работает:</b>\n"
                "1. Выбираете соперника\n"
                "2. Ставите токены\n"
                "3. Выполняете упражнение\n"
                "4. Победитель забирает ставку\n\n"
                "⚠️ <i>Функция в разработке. Скоро будет доступна!</i>",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(F.text == "📊 Тренировки")
        async def handle_trainings_main_menu(message: Message):
            """Обработчик кнопки 'Тренировки' из главного меню"""
            await message.answer(
                "📊 <b>Мои тренировки</b>\n\n"
                "Здесь будет отображаться ваша статистика тренировок:\n\n"
                "• Количество тренировок\n"
                "• Потраченное время\n"
                "• Сожженные калории\n"
                "• Прогресс по упражнениям\n\n"
                "⚠️ <i>Функция в разработке. Скоро будет доступна!</i>",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(F.text == "🎯 Достижения")
        async def handle_achievements_main_menu(message: Message):
            """Обработчик кнопки 'ДОСТИЖЕНИЯ' из главного меню"""
            user_id = message.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer("❌ Вы не зарегистрированы. Используйте /start")
                return
            
            achievements_count = user.get('achievements_count', 0)
            total_achievements = 200  # Всего доступно достижений
            
            await message.answer(
                f"🎯 <b>Достижения</b>\n\n"
                f"Ваш прогресс: <b>{achievements_count}/{total_achievements}</b>\n\n"
                f"🏆 <b>Последние полученные:</b>\n"
                f"• Первые шаги - ✅ Получено\n"
                f"• Активный пользователь - ⏳ В процессе\n"
                f"• Мастер приглашений - 🔒 Заблокировано\n\n"
                f"📈 <i>Выполняйте задания и открывайте новые достижения!</i>",
                reply_markup=MainKeyboards.get_main_menu()
            )
        
        @self.common_router.message(F.text == "💰 Магазин")
        async def handle_shop_main_menu(message: Message):
            """Обработчик кнопки 'МАГАЗИН' из главного меню"""
            await handle_shop_bottom_menu(message)
        
        @self.common_router.message(F.text == "👥 Рефералы")
        async def handle_referrals_main_menu(message: Message):
            """Обработчик кнопки 'РЕФЕРАЛЫ' из главного меню"""
            await handle_referrals_command(message)
        
        @self.common_router.message(F.text == "🎁 Ежедневный бонус")
        async def handle_bonus_main_menu(message: Message):
            """Обработчик кнопки 'ЕЖЕДНЕВНЫЙ БОНУС' из главного меню"""
            await handle_bonus_command(message)
        
        # Обработчик для любых сообщений без обработчика
        @self.common_router.message()
        async def handle_unknown_message(message: Message):
            """Обработчик неизвестных команд"""
            user_id = message.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await message.answer(
                    "❌ Вы не зарегистрированы.\n"
                    "Используйте /start для регистрации",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
            
            # Если пользователь зарегистрирован, показываем главное меню
            await message.answer(
                f"🤔 Не понял ваше сообщение: <b>{message.text}</b>\n\n"
                f"Используйте кнопки меню или команды:",
                reply_markup=MainKeyboards.get_main_menu()
            )
            
            # Также показываем нижнее меню
            await message.answer(
                "📱 Доступные действия:",
                reply_markup=MainKeyboards.get_bottom_keyboard()
            )
        
        # Глобальный обработчик возврата в главное меню
        @self.common_router.callback_query(F.data.endswith("_back_to_menu"))
        async def handle_global_back_to_menu(callback: CallbackQuery):
            """Глобальный обработчик возврата в главное меню"""
            user_id = callback.from_user.id
            user = self.db.get_user_by_telegram_id(user_id)
            
            if not user:
                await callback.answer("❌ Пользователь не найден")
                return
            
            # Удаляем сообщение с инлайн-клавиатурой
            try:
                await callback.message.delete()
            except:
                pass
            
            # Показываем главное меню ПОД СООБЩЕНИЕМ
            await callback.message.answer(
                f"🏠 <b>Главное меню</b>\n\n"
                f"Приветствуем, {user['nickname']}!\n"
                f"Выберите раздел:",
                reply_markup=MainKeyboards.get_main_menu()
            )
            
            # Нижнее меню уже висит, не нужно показывать снова
            await callback.answer()
        
        # ДОБАВЛЯЕМ ВСЕ РОУТЕРЫ В ДИСПЕТЧЕР
        logger.info("🔄 Добавление роутеров...")
        
        # Включаем модульные роутеры
        self.dp.include_router(auth_router)
        self.dp.include_router(profile_router)
        self.dp.include_router(referrals_router)
        self.dp.include_router(bonus_router)
        self.dp.include_router(shop_router)
        
        # Включаем общий роутер ПОСЛЕ модульных
        self.dp.include_router(self.common_router)
        
        logger.info("✅ Все роутеры успешно настроены")
        
    def setup_middlewares(self):
        """Настройка middleware (можно добавить позже)"""
        pass
        
    async def start(self):
        """Запуск бота"""
        logger.info("🚀 Запуск GromFitBot...")
        
        try:
            # Настраиваем роутеры
            self._setup_routers()
            
            # Настраиваем middleware
            self.setup_middlewares()
            
            logger.info("✅ Бот готов к работе")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise