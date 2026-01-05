"""
Модуль регистрации и авторизации пользователей
Исправленная версия без ошибок .get()
"""

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import string
import logging

from src.core.database import Database
from src.core.config import REGIONS
from src.modules.keyboards.main_keyboards import MainKeyboards
from src.modules.keyboards.auth_keyboards import AuthKeyboards  # Исправленный импорт

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()
db = Database()

class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации"""
    waiting_for_nickname = State()
    waiting_for_region = State()

def validate_nickname(nickname: str) -> tuple[bool, str]:
    """Валидация никнейма"""
    # Проверка длины
    if len(nickname) < 3 or len(nickname) > 20:
        return False, "❌ Никнейм должен быть от 3 до 20 символов"
    
    # Проверка на запрещенные символы
    forbidden_chars = ['<', '>', '&', '"', "'", '`', '\\', '/', '|', '{', '}', '[', ']']
    for char in forbidden_chars:
        if char in nickname:
            return False, f"❌ Никнейм содержит запрещенный символ: {char}"
    
    # Проверка на запрещенные слова
    forbidden_words = ['admin', 'root', 'moderator', 'administrator', 'support', 'help']
    for word in forbidden_words:
        if word in nickname.lower():
            return False, "❌ Никнейм содержит запрещенное слово"
    
    return True, "✅ Никнейм принят"

def generate_registration_number() -> str:
    """Генерация уникального номера регистрации GFXXXXXXXXXXYYY"""
    # 10 случайных цифр
    digits = ''.join(random.choices(string.digits, k=10))
    # 3 случайные буквы
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    
    return f"GF{digits}{letters}"

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    telegram_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    # Проверяем реферальную ссылку
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].startswith('ref'):
        try:
            referrer_id = int(args[1][3:])
        except:
            pass
    
    # Проверяем наличие пользователя в базе
    user = db.get_user(telegram_id)
    
    if user:
        # Пользователь уже зарегистрирован
        # БЕЗОПАСНОЕ ОБРАЩЕНИЕ К sqlite3.Row
        user_dict = dict(user) if user else {}
        
        nickname = user_dict.get('nickname', 'Без имени')
        registration_number = user_dict.get('registration_number', 'Неизвестно')
        
        text = (
            f"👋 С возвращением, <b>{nickname}</b>!\n\n"
            f"🏷️ Ваш ID: <code>{registration_number}</code>\n\n"
            f"<i>Используйте меню для навигации</i>"
        )
        
        # Показываем главное меню под сообщением
        await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        # И ОТДЕЛЬНО показываем кнопки под чатом (всегда видимые)
        await message.answer(
            "⬇️ <b>Основные кнопки всегда доступны ниже:</b>",
            reply_markup=MainKeyboards.get_bottom_keyboard()
        )
        
        await state.clear()
        return
    
    # Новый пользователь - начинаем регистрацию
    if referrer_id:
        await state.update_data(referrer_id=referrer_id)
    
    await state.set_state(RegistrationStates.waiting_for_nickname)
    
    text = (
        f"👋 Привет, <b>{first_name}</b>!\n\n"
        f"Добро пожаловать в <b>GromFit Bot</b> — лучшего помощника для спортивных дуэлей!\n\n"
        f"🎯 <b>Что умеет бот:</b>\n"
        f"• ⚔️ Система спортивных дуэлей\n"
        f"• 📊 Трекинг тренировок\n"
        f"• 🏆 Достижения и награды\n"
        f"• 👥 Реферальная система\n"
        f"• 🛒 Магазин с токенами\n\n"
        f"📝 Для начала <b>придумайте себе никнейм</b> (3-20 символов):"
    )
    
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

@router.message(RegistrationStates.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    """Обработка ввода никнейма"""
    nickname = message.text.strip()
    
    # Валидация никнейма
    is_valid, error_msg = validate_nickname(nickname)
    
    if not is_valid:
        await message.answer(error_msg)
        return
    
    # Проверяем, занят ли никнейм
    if db.is_nickname_taken(nickname):
        await message.answer("❌ Этот никнейм уже занят. Выберите другой:")
        return
    
    # Сохраняем никнейм и переходим к выбору региона
    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationStates.waiting_for_region)
    
    text = (
        f"✅ Отличный выбор, <b>{nickname}</b>!\n\n"
        f"🌍 Теперь выберите ваш регион из списка ниже:\n\n"
        f"<i>Используйте кнопки или напишите название города</i>"
    )
    
    await message.answer(text, reply_markup=AuthKeyboards.get_regions_keyboard())

@router.message(RegistrationStates.waiting_for_region, F.text.in_(REGIONS))
@router.message(RegistrationStates.waiting_for_region)
async def process_region(message: Message, state: FSMContext):
    """Обработка выбора региона"""
    region = message.text.strip()
    
    # Проверяем, есть ли регион в списке
    if region not in REGIONS:
        # Проверяем похожие регионы
        suggestions = [r for r in REGIONS if region.lower() in r.lower()]
        
        if suggestions:
            text = f"❌ Регион '{region}' не найден.\n\nВозможно вы имели в виду:\n" + "\n".join(suggestions[:5])
        else:
            text = f"❌ Регион '{region}' не найден. Пожалуйста, выберите регион из списка кнопок."
        
        await message.answer(text)
        return
    
    # Получаем сохраненные данные
    data = await state.get_data()
    nickname = data.get('nickname')
    referrer_id = data.get('referrer_id')
    
    # Генерируем уникальный ID
    registration_number = generate_registration_number()
    
    # Регистрируем пользователя
    try:
        telegram_id = message.from_user.id
        username = message.from_user.username or ""
        
        # Создаем пользователя
        db.create_user(
            telegram_id=telegram_id,
            username=username,
            nickname=nickname,
            region=region,
            registration_number=registration_number,
            referrer_id=referrer_id
        )
        
        # Если был реферер, добавляем связь
        if referrer_id:
            try:
                db.add_referral_connection(referrer_id, telegram_id)
            except Exception as e:
                logger.error(f"Ошибка добавления реферальной связи: {e}")
        
        # Завершаем регистрацию
        text = (
            f"🎉 <b>РЕГИСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!</b>\n\n"
            f"👤 <b>Никнейм:</b> {nickname}\n"
            f"🌍 <b>Регион:</b> {region}\n"
            f"🏷️ <b>Ваш ID:</b> <code>{registration_number}</code>\n\n"
            f"💰 <b>Стартовый бонус:</b> 50 GFT\n\n"
            f"<i>Теперь у вас есть доступ ко всем функциям бота!</i>"
        )
        
        # Показываем главное меню
        await message.answer(text, reply_markup=MainKeyboards.get_main_menu())
        
        # Показываем кнопки под чатом
        await message.answer(
            "⬇️ <b>Основные кнопки всегда доступны ниже:</b>",
            reply_markup=MainKeyboards.get_bottom_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте снова с помощью /start"
        )
        await state.clear()

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu для отображения главного меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    text = (
        "🏠 <b>ГЛАВНОЕ МЕНЮ GROMFIT</b>\n\n"
        "Выберите раздел для навигации:\n\n"
        "• 🏋️‍♂️ <b>ПРОФИЛЬ</b> - ваши данные и статистика\n"
        "• ⚔️ <b>ДУЭЛИ</b> - спортивные соревнования\n"
        "• 📊 <b>ТРЕНИРОВКИ</b> - запись и статистика тренировок\n"
        "• 🎯 <b>ДОСТИЖЕНИЯ</b> - ваши награды и ачивки\n"
        "• 💰 <b>МАГАЗИН</b> - покупка товаров за токены\n"
        "• 👥 <b>РЕФЕРАЛЫ</b> - приглашение друзей и бонусы\n"
        "• 🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b> - ежедневная награда\n\n"
        "<i>Основные кнопки всегда доступны ниже ↓</i>"
    )
    
    await message.answer(text, reply_markup=MainKeyboards.get_main_menu())