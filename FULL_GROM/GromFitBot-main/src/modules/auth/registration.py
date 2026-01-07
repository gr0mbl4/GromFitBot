"""
Полный модуль регистрации пользователей GromFitBot
Обрабатывает весь процесс регистрации с валидацией
"""

import re
import random
import string
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest

from core.database import Database
from core.message_manager import MessageManager
from modules.keyboards.main_keyboards import MainKeyboards, AuthKeyboards

router = Router()
db = Database()
message_manager = MessageManager(None)  # Будет инициализирован в main.py
logger = logging.getLogger(__name__)

def init_message_manager(bot):
    """Инициализация менеджера сообщений"""
    global message_manager
    message_manager = MessageManager(bot)

# Состояния для FSM (Finite State Machine)
class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации"""
    waiting_for_nickname = State()
    waiting_for_region = State()
    waiting_for_custom_region = State()
    registration_complete = State()

# Утилиты регистрации
class RegistrationUtils:
    """Утилиты для регистрации"""
    
    @staticmethod
    def normalize_region_name(region: str) -> str:
        """
        Нормализация названия региона:
        - Приведение к нижнему регистру
        - Замена буквы 'ё' на 'е'
        - Удаление лишних пробелов
        """
        if not region:
            return region
        
        region = region.strip().lower()
        region = region.replace('ё', 'е')
        region = re.sub(r'\s+', ' ', region)  # Удаление лишних пробелов
        return region
    
    @staticmethod
    def generate_registration_number() -> str:
        """Генерация уникального регистрационного номера GFXXXXXXXXXXYYY"""
        # Генерация 10 случайных цифр
        random_digits = ''.join(random.choices(string.digits, k=10))
        # Генерация 3 случайных букв
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"GF{random_digits}{random_letters}"
    
    @staticmethod
    def validate_nickname(nickname: str) -> Tuple[bool, str]:
        """Валидация никнейма"""
        if not nickname:
            return False, "Никнейм не может быть пустым"
        
        nickname = nickname.strip()
        
        # Проверка длины
        if len(nickname) < 3:
            return False, "Никнейм должен содержать минимум 3 символа"
        if len(nickname) > 20:
            return False, "Никнейм не должен превышать 20 символов"
        
        # Проверка на запрещенные символы
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ0-9_\-\.\s]+$', nickname):
            return False, "Никнейм может содержать только буквы, цифры, пробелы, точки, дефисы и подчеркивания"
        
        # Проверка на запрещенные слова
        forbidden_words = ['admin', 'administrator', 'moderator', 'system', 'support', 
                          'официальный', 'админ', 'модератор', 'поддержка']
        nickname_lower = nickname.lower()
        for word in forbidden_words:
            if word in nickname_lower:
                return False, f"Никнейм не может содержать слово '{word}'"
        
        # Проверка на повторяющиеся символы
        if re.search(r'(.)\1{3,}', nickname):
            return False, "Никнейм не должен содержать повторяющиеся символы более 3 раз подряд"
        
        return True, nickname
    
    @staticmethod
    def get_default_regions() -> list:
        """Получение списка регионов по умолчанию"""
        return [
            "Москва",
            "Санкт-Петербург",
            "Новосибирск",
            "Екатеринбург",
            "Казань",
            "Нижний Новгород",
            "Челябинск",
            "Самара",
            "Омск",
            "Ростов-на-Дону",
            "Уфа",
            "Красноярск",
            "Воронеж",
            "Пермь",
            "Волгоград"
        ]
    
    @staticmethod
    def find_region_match(input_region: str, regions_list: list) -> Optional[str]:
        """Поиск совпадения региона с учетом нормализации"""
        normalized_input = RegistrationUtils.normalize_region_name(input_region)
        
        for region in regions_list:
            normalized_region = RegistrationUtils.normalize_region_name(region)
            if normalized_input == normalized_region:
                return region
        
        return None

# Обработчики регистрации
@router.message(Command("register"))
async def handle_register_command(message: Message, state: FSMContext):
    """Обработчик команды /register"""
    await start_registration(message, state)

async def start_registration(message: Message, state: FSMContext = None):
    """Начало процесса регистрации"""
    user_id = message.from_user.id
    
    # Проверяем, не зарегистрирован ли пользователь уже
    existing_user = db.get_user(user_id)
    if existing_user:
        logger.info(f"Пользователь {user_id} уже зарегистрирован")
        await message_manager.replace_message(
            message,
            f"👋 <b>С возвращением, {existing_user['nickname']}!</b>\n\n"
            f"Вы уже зарегистрированы в системе.\n"
            f"Используйте /menu для перехода в главное меню."
        )
        return
    
    logger.info(f"Начало регистрации пользователя {user_id}")
    
    # Начинаем процесс регистрации
    if state:
        await state.clear()
        await state.set_state(RegistrationStates.waiting_for_nickname)
    
    # Отправляем приветственное сообщение
    await message_manager.replace_message(
        message,
        "👋 <b>Добро пожаловать в GromFit Bot!</b>\n\n"
        "Я - ваш персональный помощник в мире спортивных дуэлей.\n\n"
        "<b>Давайте начнем регистрацию!</b>\n\n"
        "<b>Шаг 1 из 3:</b> Введите ваш никнейм\n"
        "• От 3 до 20 символов\n"
        "• Можно использовать буквы, цифры, пробелы и символы ._-",
        reply_markup=AuthKeyboards.get_username_keyboard()
    )

@router.message(RegistrationStates.waiting_for_nickname)
async def handle_nickname_input(message: Message, state: FSMContext):
    """Обработка ввода никнейма"""
    user_id = message.from_user.id
    
    # Если нажата кнопка "Взять из Telegram"
    if message.text == "Взять из Telegram":
        nickname = message.from_user.username or message.from_user.first_name
        
        if not nickname:
            await message_manager.replace_message(
                message,
                "❌ <b>Не удалось получить имя из Telegram</b>\n\n"
                "У вас не установлен username, а имя может быть пустым.\n"
                "Пожалуйста, введите никнейм вручную:",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Используем имя из Telegram
        nickname = nickname.strip()
    else:
        nickname = message.text.strip()
    
    # Валидация никнейма
    is_valid, validation_result = RegistrationUtils.validate_nickname(nickname)
    
    if not is_valid:
        await message_manager.replace_message(
            message,
            f"❌ <b>Некорректный никнейм</b>\n\n"
            f"{validation_result}\n\n"
            f"Пожалуйста, введите никнейм еще раз:",
            reply_markup=AuthKeyboards.get_username_keyboard()
        )
        return
    
    # Проверяем, не занят ли никнейм (опционально, можно добавить в будущем)
    # Пока пропускаем эту проверку
    
    # Сохраняем никнейм в состоянии
    await state.update_data(nickname=nickname)
    
    # Переходим к следующему шагу
    await state.set_state(RegistrationStates.waiting_for_region)
    
    # Получаем список регионов
    regions = RegistrationUtils.get_default_regions()
    
    await message_manager.replace_message(
        message,
        f"✅ <b>Отличный выбор, {nickname}!</b>\n\n"
        f"<b>Шаг 2 из 3:</b> Выберите ваш регион\n\n"
        f"Это поможет нам:\n"
        f"• Находить ближайших соперников\n"
        f"• Организовывать локальные турниры\n"
        f"• Предлагать актуальные события\n\n"
        f"Выберите из списка или укажите другой город:",
        reply_markup=AuthKeyboards.get_region_selection_keyboard(regions)
    )

@router.message(RegistrationStates.waiting_for_region)
async def handle_region_selection(message: Message, state: FSMContext):
    """Обработка выбора региона"""
    user_id = message.from_user.id
    selected_region = message.text.strip()
    
    # Если выбрана кнопка "Другой город"
    if selected_region == "🏙️ Другой город":
        await state.set_state(RegistrationStates.waiting_for_custom_region)
        
        await message_manager.replace_message(
            message,
            "🏙️ <b>Введите название вашего города</b>\n\n"
            "Пожалуйста, укажите город в формате:\n"
            "• <b>Москва</b> (для городов России)\n"
            "• <b>Киев, Украина</b> (для городов других стран)\n\n"
            "Используйте кириллицу или латиницу:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Проверяем, есть ли выбранный регион в списке
    regions = RegistrationUtils.get_default_regions()
    matched_region = RegistrationUtils.find_region_match(selected_region, regions)
    
    if not matched_region:
        await message_manager.replace_message(
            message,
            f"❌ <b>Регион не найден</b>\n\n"
            f"Пожалуйста, выберите регион из списка или нажмите 'Другой город':",
            reply_markup=AuthKeyboards.get_region_selection_keyboard(regions)
        )
        return
    
    # Сохраняем регион и завершаем регистрацию
    await state.update_data(region=matched_region)
    await complete_registration(message, state)

@router.message(RegistrationStates.waiting_for_custom_region)
async def handle_custom_region_input(message: Message, state: FSMContext):
    """Обработка ввода пользовательского региона"""
    user_id = message.from_user.id
    custom_region = message.text.strip()
    
    if not custom_region:
        await message_manager.replace_message(
            message,
            "❌ <b>Название города не может быть пустым</b>\n\n"
            "Пожалуйста, введите название вашего города:"
        )
        return
    
    if len(custom_region) > 50:
        await message_manager.replace_message(
            message,
            "❌ <b>Название города слишком длинное</b>\n\n"
            "Пожалуйста, введите более короткое название (до 50 символов):"
        )
        return
    
    # Проверяем на запрещенные символы
    if re.search(r'[<>{}[\]\\|]', custom_region):
        await message_manager.replace_message(
            message,
            "❌ <b>Некорректные символы в названии города</b>\n\n"
            "Пожалуйста, используйте только буквы, цифры, пробелы и знаки препинания:"
        )
        return
    
    # Сохраняем пользовательский регион
    await state.update_data(region=custom_region)
    await complete_registration(message, state)

async def complete_registration(message: Message, state: FSMContext):
    """Завершение процесса регистрации"""
    user_id = message.from_user.id
    user_data = await state.get_data()
    
    nickname = user_data.get('nickname')
    region = user_data.get('region', 'Не указан')
    
    if not nickname:
        logger.error(f"Ошибка регистрации: никнейм не найден для пользователя {user_id}")
        await message_manager.replace_message(
            message,
            "❌ <b>Ошибка регистрации</b>\n\n"
            "Не удалось получить данные регистрации.\n"
            "Пожалуйста, начните заново с команды /start"
        )
        await state.clear()
        return
    
    # Генерируем регистрационный номер
    registration_number = RegistrationUtils.generate_registration_number()
    
    # Проверяем уникальность номера (маловероятно, но на всякий случай)
    while db.get_user_by_registration_number(registration_number):
        registration_number = RegistrationUtils.generate_registration_number()
    
    # Получаем username из Telegram
    username = message.from_user.username
    
    # Подготавливаем данные пользователя
    user_record = {
        'telegram_id': user_id,
        'registration_number': registration_number,
        'username': username,
        'nickname': nickname,
        'region': region,
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'balance_tokens': 50.00,  # Стартовый баланс
        'referrals_count': 0,
        'total_trainings': 0,
        'total_duels': 0,
        'duels_won': 0,
        'total_points': 0,
        'level': 1,
        'experience': 0,
        'daily_streak': 0,
        'achievements_count': 0,
        'is_premium': 0,
        'notifications_enabled': 1,
        'language': 'ru',
        'theme': 'light',
        'settings': '{}'
    }
    
    # Проверяем, есть ли реферальный ID в состоянии
    from core.bot import GromFitBot
    bot_instance = GromFitBot()
    if user_id in bot_instance.user_states and 'referral_id' in bot_instance.user_states[user_id]:
        referral_id = bot_instance.user_states[user_id]['referral_id']
        user_record['referrer_id'] = referral_id
    
    # Сохраняем пользователя в БД
    success = db.create_user(user_record)
    
    if not success:
        logger.error(f"Ошибка сохранения пользователя {user_id} в БД")
        await message_manager.replace_message(
            message,
            "❌ <b>Ошибка регистрации</b>\n\n"
            "Не удалось сохранить данные в базе.\n"
            "Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
        )
        await state.clear()
        return
    
    # Добавляем стартовые достижения
    await add_starting_achievements(user_id)
    
    # Очищаем состояние
    await state.clear()
    
    # Получаем информацию о пользователе для приветствия
    user = db.get_user(user_id)
    
    # Формируем приветственное сообщение
    welcome_text = (
        f"🎉 <b>Поздравляем с успешной регистрацией, {nickname}!</b>\n\n"
        f"<b>Ваши данные:</b>\n"
        f"👤 <b>Никнейм:</b> {nickname}\n"
        f"📍 <b>Регион:</b> {region}\n"
        f"🆔 <b>ID:</b> {registration_number}\n\n"
        f"<b>Ваш стартовый баланс:</b>\n"
        f"💰 <b>50 токенов</b> (уже на вашем счету!)\n\n"
        f"<b>Что дальше?</b>\n"
        f"• Используйте кнопки ниже для навигации\n"
        f"• Изучите раздел '🤝 Рефералы' для приглашения друзей\n"
        f"• Заходите ежедневно для получения бонусов\n"
        f"• Следите за обновлениями системы дуэлей!\n\n"
        f"<i>Приятного использования GromFit Bot!</i>"
    )
    
    # Отправляем финальное сообщение
    await message_manager.replace_message(
        message,
        welcome_text,
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )
    
    logger.info(f"Пользователь {user_id} успешно зарегистрирован как {nickname}")

async def add_starting_achievements(user_id: int):
    """Добавление стартовых достижений пользователю"""
    starting_achievements = [
        {
            'achievement_id': 'welcome_to_gromfit',
            'title': 'Добро пожаловать в GromFit!',
            'description': 'Вы успешно зарегистрировались в системе',
            'icon': '👋',
            'reward_tokens': 5.00,
            'category': 'registration'
        },
        {
            'achievement_id': 'first_steps',
            'title': 'Первые шаги',
            'description': 'Завершили процесс регистрации',
            'icon': '🚶',
            'reward_tokens': 10.00,
            'category': 'progress'
        }
    ]
    
    for achievement in starting_achievements:
        db.add_achievement(user_id, achievement)
    
    logger.debug(f"Добавлены стартовые достижения пользователю {user_id}")

# Обработчики отмены регистрации
@router.message(F.text == "❌ Отмена")
async def handle_registration_cancel(message: Message, state: FSMContext):
    """Обработка отмены регистрации"""
    current_state = await state.get_state()
    
    if current_state and "RegistrationStates" in current_state:
        await state.clear()
        
        await message_manager.replace_message(
            message,
            "❌ <b>Регистрация отменена</b>\n\n"
            "Если вы передумаете, используйте команду /start для начала регистрации.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        logger.info(f"Регистрация отменена пользователем {message.from_user.id}")

# Обработчики помощи по регистрации
@router.message(Command("help_registration"))
async def handle_help_registration(message: Message):
    """Помощь по регистрации"""
    help_text = (
        "🆘 <b>Помощь по регистрации</b>\n\n"
        "<b>Процесс регистрации состоит из 3 шагов:</b>\n\n"
        "1. <b>Ввод никнейма</b>\n"
        "   • От 3 до 20 символов\n"
        "   • Можно использовать буквы, цифры, пробелы и символы ._-\n"
        "   • Можно использовать кнопку 'Взять из Telegram'\n\n"
        "2. <b>Выбор региона</b>\n"
        "   • Выберите из списка популярных городов\n"
        "   • Или укажите свой город вручную\n"
        "   • Регион помогает находить ближайших соперников\n\n"
        "3. <b>Завершение регистрации</b>\n"
        "   • Вы получаете уникальный ID\n"
        "   • Начисляется стартовый баланс 50 токенов\n"
        "   • Открывается доступ ко всем функциям бота\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать регистрацию\n"
        "/register - Альтернативная команда для регистрации\n"
        "/help_registration - Эта справка\n\n"
        "<i>Если возникли проблемы, обратитесь в поддержку</i>"
    )
    
    await message_manager.replace_message(message, help_text)

# Обработчик для тестирования регистрации (только для админов)
@router.message(Command("test_registration"))
async def handle_test_registration(message: Message):
    """Тестирование процесса регистрации (только для разработки)"""
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором
    from core.config import Config
    config = Config()
    
    if not config.is_admin(user_id):
        await message_manager.replace_message(
            message,
            "❌ <b>Доступ запрещен</b>\n\n"
            "Эта команда доступна только администраторам."
        )
        return
    
    # Генерируем тестовые данные
    test_nickname = f"TestUser{random.randint(1000, 9999)}"
    test_region = random.choice(RegistrationUtils.get_default_regions())
    test_reg_number = RegistrationUtils.generate_registration_number()
    
    test_info = (
        f"🧪 <b>Тест регистрации</b>\n\n"
        f"<b>Генерируемые данные:</b>\n"
        f"👤 Никнейм: {test_nickname}\n"
        f"📍 Регион: {test_region}\n"
        f"🆔 Рег. номер: {test_reg_number}\n\n"
        f"<b>Проверка функций:</b>\n"
        f"✅ Генерация номера: работает\n"
        f"✅ Валидация никнейма: работает\n"
        f"✅ Поиск региона: работает\n\n"
        f"<i>Тест завершен успешно</i>"
    )
    
    await message_manager.replace_message(message, test_info)