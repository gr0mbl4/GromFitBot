"""
Модуль регистрации пользователей с обновленными бонусами и приветствием
"""

import logging
import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.core.database import db
from src.core.config import config
from src.modules.referrals.system import referral_system
from .keyboards import AuthKeyboards
from src.modules.keyboards.main_keyboards import MainKeyboards

logger = logging.getLogger(__name__)

router = Router()

class RegistrationStates(StatesGroup):
    """Состояния для процесса регистрации"""
    waiting_nickname = State()
    waiting_region = State()

def contains_bad_words(text: str) -> bool:
    """Проверяет текст на наличие запрещенных слов"""
    text_lower = text.lower()
    for word in config.BAD_WORDS:
        if word in text_lower:
            return True
    return False

def normalize_city_name(city_name: str) -> str:
    """Нормализует название города для сравнения"""
    normalized = city_name.lower()
    normalized = normalized.replace('ё', 'е')
    normalized = ' '.join(normalized.split())
    normalized = normalized.replace('-', ' ')
    return normalized

def city_exists(city_name: str) -> str:
    """Проверяет, существует ли город в базе"""
    normalized_input = normalize_city_name(city_name)
    
    for city in config.RUSSIAN_CITIES:
        normalized_city = normalize_city_name(city)
        if normalized_input == normalized_city:
            return city
    
    return None

def get_welcome_keyboard_after_registration() -> ReplyKeyboardMarkup:
    """Клавиатура после регистрации"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(KeyboardButton(text="🛒 Магазин"))
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    
    return builder.as_markup(resize_keyboard=True, persistent=True)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start с поддержкой рефералов"""
    
    await asyncio.sleep(0.1)  # Небольшая задержка для стабильности
    
    telegram_id = message.from_user.id
    username = message.from_user.username
    command_args = message.text.split()
    
    # Проверяем, есть ли реферальный код в команде
    referrer_id = None
    referral_code = None
    
    if len(command_args) > 1:
        referral_code = command_args[1]
        # Проверяем, это реферальный код или что-то еще
        if referral_code.startswith('r-'):
            # Обрабатываем реферальный код
            result = referral_system.process_referral_start(telegram_id, referral_code)
            if result["success"]:
                referrer_id = result["referrer_id"]
                logger.info(f"Реферал {telegram_id} приглашен пользователем {referrer_id}")
            else:
                logger.warning(f"Ошибка обработки реферального кода: {result['message']}")
    
    if db.user_exists(telegram_id):
        # Пользователь уже зарегистрирован
        db.update_user_activity(telegram_id)
        user = db.get_user(telegram_id)
        
        # Безопасное получение данных
        nickname = user['nickname'] if 'nickname' in user.keys() else "Не установлен"
        region = user['region'] if 'region' in user.keys() else "no region"
        reg_number = user['registration_number'] if 'registration_number' in user.keys() else "N/A"
        tokens = float(user['balance_tokens']) if 'balance_tokens' in user.keys() and user['balance_tokens'] is not None else 0
        
        welcome_text = (
            f"🏋️‍♂️ <b>ПРИВЕТ! Я - GROMFIT BOT!</b>\n\n"
            f"🎯 <b>ЧТО Я УМЕЮ:</b>\n"
            f"⚔️ Спортивные дуэли – Бросай вызов друзьям\n"
            f"📊 Трекер прогресса – Отслеживай свои результаты\n"
            f"🏆 Рейтинги и достижения – Стань лучшим в своем регионе\n"
            f"💰 Награды и бонусы – Зарабатывай за тренировки\n"
            f"👥 Сообщество – Найди единомышленников\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 <b>С ВОЗВРАЩЕНИЕМ!</b>\n\n"
            f"<b>🎭 Ваш ник:</b> {nickname}\n"
            f"<b>📍 Регион:</b> {region if region != 'no region' else 'не указан'}\n"
            f"<b>🆔 ID:</b> {reg_number}\n"
            f"<b>💎 Баланс:</b> {tokens:.0f} токенов\n\n"
            f"👇 <b>ВЫБЕРИТЕ ДЕЙСТВИЕ В МЕНЮ:</b>"
        )
        
        # Если был реферальный переход и еще не обработан
        if referrer_id and 'referrer_id' in user.keys() and not user['referrer_id']:
            # Устанавливаем реферера
            db.execute(
                "UPDATE users SET referrer_id = ? WHERE telegram_id = ?",
                (referrer_id, telegram_id)
            )
            db.commit()
            
            # Завершаем реферальную регистрацию с новыми бонусами
            from src.modules.finance.token_system import token_system
            referral_system.set_token_system(token_system)
            referral_system.complete_referral_registration(referrer_id, telegram_id)
            
            welcome_text += f"\n\n🎉 <b>Вы приглашены по реферальной ссылке! Получены бонусы (50 токенов)!</b>"
        
        try:
            await message.answer(
                welcome_text,
                reply_markup=MainKeyboards.get_bottom_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            # Пробуем отправить без форматирования
            simple_text = f"С возвращением, {nickname}! Используйте меню для навигации."
            await message.answer(
                simple_text,
                reply_markup=MainKeyboards.get_bottom_keyboard()
            )
    else:
        # Новый пользователь - сохраняем реферера в состояние
        await state.set_state(RegistrationStates.waiting_nickname)
        await state.update_data(
            referrer_id=referrer_id,
            referral_code=referral_code
        )
        
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        welcome_new = (
            f"🏋️‍♂️ <b>ПРИВЕТ! Я - GROMFIT BOT!</b>\n\n"
            f"🎯 <b>ЧТО Я УМЕЮ:</b>\n"
            f"⚔️ Спортивные дуэли – Бросай вызов друзьям\n"
            f"📊 Трекер прогресса – Отслеживай свои результаты\n"
            f"🏆 Рейтинги и достижения – Стань лучшим в своем регионе\n"
            f"💰 Награды и бонусы – Зарабатывай за тренировки\n"
            f"👥 Сообщество – Найди единомышленников\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>КАК МНЕ К ВАМ ОБРАЩАТЬСЯ❓</b>\n\n"
            f"👇 <b>Выберите имя из профиля или введите свой вариант:</b>"
        )
        
        try:
            await message.answer(
                welcome_new,
                reply_markup=AuthKeyboards.get_nickname_keyboard(first_name, last_name),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки приветствия: {e}")
            simple_text = "Добро пожаловать! Как мне к вам обращаться? Выберите имя или введите свой вариант."
            await message.answer(
                simple_text,
                reply_markup=AuthKeyboards.get_nickname_keyboard(first_name, last_name)
            )

@router.callback_query(F.data.startswith("nickname_"))
async def process_nickname_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора никнейма из кнопок"""
    
    await asyncio.sleep(0.1)  # Небольшая задержка
    
    nickname = callback.data.replace("nickname_", "")
    
    # Проверка никнейма
    if len(nickname) < 3:
        await callback.answer("❌ Никнейм должен содержать минимум 3 символа", show_alert=True)
        return
    
    if len(nickname) > 20:
        await callback.answer("❌ Никнейм не должен превышать 20 символов", show_alert=True)
        return
    
    if contains_bad_words(nickname):
        await callback.answer("❌ Никнейм содержит запрещенные слова", show_alert=True)
        return
    
    # Сохраняем никнейм и переходим к выбору региона
    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationStates.waiting_region)
    
    region_text = (
        "📍 <b>ВВЕДИТЕ ВАШ ГОРОД ИЛИ РЕГИОН</b>\n\n"
        "🏙️ <b>ДЛЯ ИНДИВИДУАЛЬНЫХ ПРЕДЛОЖЕНИЙ И ЛОКАЛЬНЫХ РЕЙТИНГОВ:</b>\n"
        "• Это поможет находить соперников рядом с вами\n"
        "• Участвовать в региональных рейтингах\n"
        "• Получать локальные события и скидки\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Введите название города или пропустите этот шаг:</b>"
    )
    
    try:
        await callback.message.answer(
            region_text,
            reply_markup=AuthKeyboards.get_region_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки запроса региона: {e}")
        simple_text = f"Введите ваш город или нажмите 'Пропустить регион'"
        await callback.message.answer(
            simple_text,
            reply_markup=AuthKeyboards.get_region_keyboard()
        )
    
    await callback.answer()

@router.message(RegistrationStates.waiting_nickname)
async def process_nickname_message(message: Message, state: FSMContext):
    """Обработка ввода никнейма вручную"""
    
    await asyncio.sleep(0.1)
    
    nickname = message.text.strip()
    
    # Проверка валидности
    if len(nickname) < 3:
        await message.answer("❌ Никнейм должен содержать минимум 3 символа")
        return
    
    if len(nickname) > 20:
        await message.answer("❌ Никнейм не должен превышать 20 символов")
        return
    
    # Проверка на эмодзи и специальные символы
    if re.search(r'[^\w\s-]', nickname):
        await message.answer(
            "❌ Никнейм не должен содержать эмодзи или специальные символы\n"
            "Можно использовать только буквы, цифры, пробелы и дефисы"
        )
        return
    
    if contains_bad_words(nickname):
        await message.answer("❌ Никнейм содержит запрещенные слова")
        return
    
    # Сохраняем никнейм и переходим к выбору региона
    await state.update_data(nickname=nickname)
    await state.set_state(RegistrationStates.waiting_region)
    
    region_text = (
        "📍 <b>ВВЕДИТЕ ВАШ ГОРОД ИЛИ РЕГИОН</b>\n\n"
        "🏙️ <b>ДЛЯ ИНДИВИДУАЛЬНЫХ ПРЕДЛОЖЕНИЙ И ЛОКАЛЬНЫХ РЕЙТИНГОВ:</b>\n"
        "• Это поможет находить соперников рядом с вами\n"
        "• Участвовать в региональных рейтингах\n"
        "• Получать локальные события и скидки\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Введите название города или пропустите этот шаг:</b>"
    )
    
    try:
        await message.answer(
            region_text,
            reply_markup=AuthKeyboards.get_region_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки запроса региона: {e}")
        simple_text = f"Введите ваш город или нажмите 'Пропустить регион'"
        await message.answer(
            simple_text,
            reply_markup=AuthKeyboards.get_region_keyboard()
        )

@router.callback_query(F.data == "region_skip")
async def skip_region(callback: CallbackQuery, state: FSMContext):
    """Пропуск ввода региона"""
    
    await asyncio.sleep(0.1)
    
    telegram_id = callback.from_user.id
    user_data = await state.get_data()
    nickname = user_data.get('nickname')
    referrer_id = user_data.get('referrer_id')
    referral_code = user_data.get('referral_code')
    
    if not nickname:
        await callback.answer("Ошибка: никнейм не сохранен", show_alert=True)
        return
    
    # Создаем пользователя и начисляем 50 токенов за регистрацию
    username = callback.from_user.username
    region = "no region"
    
    # Используем обновленный метод с бонусами
    user = db.create_user_with_bonus(
        telegram_id=telegram_id,
        nickname=nickname,
        username=username,
        region=region,
        referrer_id=referrer_id
    )
    
    # Если был реферальный код, обрабатываем бонусы (дополнительные 50 токенов для приглашенного)
    if referrer_id and referral_code:
        from src.modules.finance.token_system import token_system
        referral_system.set_token_system(token_system)
        referral_system.complete_referral_registration(referrer_id, telegram_id)
        
        # Отправляем специальное сообщение для приглашенных пользователей
        await show_registration_success_with_offer(callback.message, nickname, region, referrer_id)
    else:
        # Отправляем обычное сообщение для самостоятельной регистрации
        await show_registration_success_without_offer(callback.message, nickname, region)
    
    await state.clear()
    await callback.answer()

@router.message(RegistrationStates.waiting_region)
async def process_region(message: Message, state: FSMContext):
    """Обработка ввода региона"""
    
    await asyncio.sleep(0.1)
    
    telegram_id = message.from_user.id
    user_input = message.text.strip()
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    nickname = user_data.get('nickname')
    referrer_id = user_data.get('referrer_id')
    referral_code = user_data.get('referral_code')
    
    if not nickname:
        await message.answer("❌ Ошибка: сначала введите никнейм. Используйте /start")
        return
    
    if user_input.lower() == "пропустить":
        region = "no region"
    else:
        city = city_exists(user_input)
        if city:
            region = city
        else:
            error_text = (
                "❌ <b>Город не найден в базе</b>\n\n"
                "Пожалуйста, введите название города из России "
                "(с населением более 100,000 человек) или нажмите 'Пропустить регион'"
            )
            
            try:
                await message.answer(
                    error_text,
                    reply_markup=AuthKeyboards.get_region_keyboard(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения об ошибке: {e}")
                simple_text = "Город не найден. Введите другой или пропустите."
                await message.answer(
                    simple_text,
                    reply_markup=AuthKeyboards.get_region_keyboard()
                )
            return
    
    # Создаем пользователя и начисляем 50 токенов за регистрацию
    username = message.from_user.username
    
    # Используем обновленный метод с бонусами
    user = db.create_user_with_bonus(
        telegram_id=telegram_id,
        nickname=nickname,
        username=username,
        region=region,
        referrer_id=referrer_id
    )
    
    # Если был реферальный код, обрабатываем бонусы (дополнительные 50 токенов для приглашенного)
    if referrer_id and referral_code:
        from src.modules.finance.token_system import token_system
        referral_system.set_token_system(token_system)
        referral_system.complete_referral_registration(referrer_id, telegram_id)
        
        # Отправляем специальное сообщение для приглашенных пользователей
        await show_registration_success_with_offer(message, nickname, region, referrer_id)
    else:
        # Отправляем обычное сообщение для самостоятельной регистрации
        await show_registration_success_without_offer(message, nickname, region)
    
    await state.clear()

async def show_registration_success_with_offer(message: Message, nickname: str, region: str, referrer_id: int = None):
    """Показ сообщения об успешной регистрации для приглашенных пользователей"""
    
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    # Безопасное получение данных
    balance_tokens = float(user['balance_tokens']) if user and 'balance_tokens' in user.keys() else 100.00  # 50 за регистрацию + 50 за приглашение
    reg_number = user['registration_number'] if user and 'registration_number' in user.keys() else 'N/A'
    
    # Получаем имя реферера
    referrer_name = "друг"
    if referrer_id:
        cursor = db.execute(
            "SELECT nickname FROM users WHERE telegram_id = ?",
            (referrer_id,)
        )
        referrer = cursor.fetchone()
        if referrer and 'nickname' in referrer.keys():
            referrer_name = referrer['nickname']
    
    success_text = (
        f"🎉 <b>ПОЗДРАВЛЯЕМ, {nickname}!</b>\n\n"
        f"✅ <b>РЕГИСТРАЦИЯ ЗАВЕРШЕНА!</b>\n\n"
        f"📋 <b>ВАШИ ДАННЫЕ:</b>\n"
        f"• 🎭 Имя: {nickname}\n"
        f"• 📍 Регион: {region if region != 'no region' else 'не указан'}\n"
        f"• 🆔 ID: {reg_number}\n\n"
        f"💰 <b>Спасибо за регистрацию, на ваш баланс поступило 100 токенов!</b>\n"
        f"• 50 токенов за регистрацию\n"
        f"• 50 токенов за приглашение от друга {referrer_name}\n\n"
        f"✨ <b>СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ НОВИЧКОВ:</b>\n"
        f"3 дня безлимитных голосовых + 1 анализ\n\n"
        f"👇 <b>Перейдите в</b> <b>Магазин</b><b>, чтобы активировать предложение за 50 токенов!</b>"
    )
    
    # Создаем клавиатуру для нового пользователя
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛒 Магазин"))
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    
    keyboard = builder.as_markup(resize_keyboard=True, persistent=True)
    
    # Отправляем сообщение с специальной клавиатурой
    await message.answer(
        success_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def show_registration_success_without_offer(message: Message, nickname: str, region: str):
    """Показ сообщения об успешной регистрации для самостоятельных пользователей"""
    
    telegram_id = message.from_user.id
    user = db.get_user(telegram_id)
    
    # Безопасное получение данных
    balance_tokens = float(user['balance_tokens']) if user and 'balance_tokens' in user.keys() else 50.00  # 50 за регистрацию
    reg_number = user['registration_number'] if user and 'registration_number' in user.keys() else 'N/A'
    
    success_text = (
        f"🎉 <b>ПОЗДРАВЛЯЕМ, {nickname}!</b>\n\n"
        f"✅ <b>РЕГИСТРАЦИЯ ЗАВЕРШЕНА!</b>\n\n"
        f"📋 <b>ВАШИ ДАННЫЕ:</b>\n"
        f"• 🎭 Имя: {nickname}\n"
        f"• 📍 Регион: {region if region != 'no region' else 'не указан'}\n"
        f"• 🆔 ID: {reg_number}\n\n"
        f"💰 <b>Спасибо за регистрацию, на ваш баланс поступило 50 токенов!</b>\n\n"
        f"✨ <b>СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ НОВИЧКОВ:</b>\n"
        f"3 дня безлимитных голосовых + 1 анализ\n\n"
        f"👇 <b>Перейдите в</b> <b>Магазин</b><b>, чтобы активировать предложение за 50 токенов!</b>"
    )
    
    # Создаем клавиатуру для нового пользователя
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛒 Магазин"))
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    
    keyboard = builder.as_markup(resize_keyboard=True, persistent=True)
    
    # Отправляем сообщение с специальной клавиатурой
    await message.answer(
        success_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )