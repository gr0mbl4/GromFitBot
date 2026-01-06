"""
Модуль регистрации пользователей
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from datetime import datetime

from src.core.database import Database
from src.core.config import REGIONS
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

# Состояния регистрации
class RegistrationStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_region = State()

# Нормализация названия города
def normalize_city_name(city: str) -> str:
    """Нормализация названия города для сравнения"""
    city = city.strip().lower()
    
    # Заменяем ё на е
    city = city.replace('ё', 'е')
    
    # Удаляем лишние пробелы
    city = ' '.join(city.split())
    
    return city

# Поиск города в базе
def find_city_in_regions(city_input: str) -> str:
    """Поиск города в базе регионов"""
    normalized_input = normalize_city_name(city_input)
    
    for city in REGIONS:
        normalized_city = normalize_city_name(city)
        if normalized_input == normalized_city:
            return city
    
    # Если не нашли точное совпадение, ищем частичное
    for city in REGIONS:
        normalized_city = normalize_city_name(city)
        if normalized_input in normalized_city or normalized_city in normalized_input:
            return city
    
    return None

# Обработчик команды /start
@router.message(Command("start"))
async def command_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    
    user_id = message.from_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    user = db.get_user_by_telegram_id(user_id)
    
    if user:
        # Пользователь уже зарегистрирован
        await message.answer(
            f"👋 С возвращением, {user['nickname']}!\n"
            f"Ваш баланс: {user['balance_tokens']} токенов\n\n"
            f"Что хотите сделать?",
            reply_markup=MainKeyboards.get_main_menu()
        )
        
        # Показываем нижнее меню
        await message.answer(
            "📱 Доступные действия:",
            reply_markup=MainKeyboards.get_bottom_keyboard()
        )
        
        # Обновляем last_active
        db.update_user_last_active(user_id)
        
        return
    
    # Новый пользователь - начинаем регистрацию
    referrer_id = None
    
    # Проверяем реферальную ссылку
    if len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
            # Проверяем существование реферера
            referrer = db.get_user_by_telegram_id(referrer_id)
            if not referrer:
                referrer_id = None
        except:
            referrer_id = None
    
    # Сохраняем referrer_id в состоянии
    await state.update_data(referrer_id=referrer_id)
    
    # Получаем имя из Telegram
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    
    # Определяем предложенное имя
    suggested_name = ""
    if first_name:
        suggested_name = first_name
    elif username:
        suggested_name = username
    
    if suggested_name:
        # Создаем клавиатуру с именем из Telegram
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text=suggested_name))
        keyboard = builder.as_markup(resize_keyboard=True, persistent=True)
        
        await message.answer(
            f"👋 Добро пожаловать в GromFit!\n\n"
            f"Как к вам обращаться?\n"
            f"Можно использовать имя из Telegram:\n\n"
            f"<b>{suggested_name}</b>\n\n"
            f"Если хотите использовать это имя - нажмите кнопку ниже\n"
            f"Если хотите другой ник - просто введите его вручную",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать в GromFit!\n\n"
            f"Как к вам обращаться?\n"
            f"Введите ваш никнейм (3-20 символов):",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.set_state(RegistrationStates.waiting_for_nickname)

# Обработка ввода никнейма
@router.message(RegistrationStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    """Обработка ввода никнейма"""
    
    nickname = message.text.strip()
    
    # Валидация никнейма
    if len(nickname) < 3 or len(nickname) > 20:
        await message.answer(
            "❌ Никнейм должен быть от 3 до 20 символов.\n"
            "Пожалуйста, введите еще раз:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Проверка на запрещенные слова
    forbidden_words = ['админ', 'admin', 'модератор', 'root', 'бот', 'система']
    if any(word in nickname.lower() for word in forbidden_words):
        await message.answer(
            "❌ Никнейм содержит запрещенные слова.\n"
            "Пожалуйста, введите другой никнейм:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Сохраняем никнейм в состоянии
    await state.update_data(nickname=nickname)
    
    # Переходим к выбору региона
    await state.set_state(RegistrationStates.waiting_for_region)
    
    await message.answer(
        f"✅ Отличный выбор, <b>{nickname}</b>!\n\n"
        f"🌍 Теперь введите ваш город:\n\n"
        f"<i>Просто напишите название города (например: Москва, Санкт-Петербург, Орел)</i>",
        reply_markup=ReplyKeyboardRemove()  # Убираем все клавиатуры
    )

# Обработка выбора региона
@router.message(RegistrationStates.waiting_for_region)
async def process_region(message: Message, state: FSMContext):
    """Обработка ввода региона"""
    
    city_input = message.text.strip()
    data = await state.get_data()
    
    # Ищем город в базе
    city = find_city_in_regions(city_input)
    
    if not city:
        # Город не найден
        await message.answer(
            f"❌ Город <b>{city_input}</b> не найден в нашей базе.\n\n"
            f"Пожалуйста, введите другой город.\n"
            f"<i>Убедитесь, что название написано правильно.</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Регион найден - продолжаем регистрацию
    nickname = data['nickname']
    referrer_id = data.get('referrer_id')
    
    # Регистрируем пользователя
    user_data = {
        'telegram_id': message.from_user.id,
        'username': message.from_user.username,
        'nickname': nickname,
        'region': city,
        'referrer_id': referrer_id
    }
    
    success = db.create_user(user_data)
    
    if not success:
        await message.answer(
            "❌ Произошла ошибка при регистрации.\n"
            "Пожалуйста, попробуйте еще раз /start",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    # Если есть реферер - начисляем бонусы
    if referrer_id:
        db.add_referral(referrer_id, message.from_user.id)
    
    # Получаем пользователя для отображения данных
    user = db.get_user_by_telegram_id(message.from_user.id)
    
    await message.answer(
        f"🎉 <b>Поздравляем с регистрацией, {nickname}!</b>\n\n"
        f"📋 Ваши данные:\n"
        f"• ID: <code>{user['registration_number']}</code>\n"
        f"• Никнейм: <b>{nickname}</b>\n"
        f"• Регион: <b>{city}</b>\n"
        f"• Баланс: <b>50.00</b> токенов\n\n"
        f"🎁 Вы получили стартовый бонус: 50 токенов!",
        reply_markup=MainKeyboards.get_main_menu()
    )
    
    # Показываем нижнее меню
    await message.answer(
        "📱 Теперь вы можете пользоваться всеми функциями бота!",
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )
    
    # Очищаем состояние
    await state.clear()

# Отмена регистрации
@router.message(Command("cancel"))
@router.message(F.text.lower() == "отмена")
async def cancel_registration(message: Message, state: FSMContext):
    """Отмена регистрации"""
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n"
        "Для начала регистрации используйте /start",
        reply_markup=ReplyKeyboardRemove()
    )