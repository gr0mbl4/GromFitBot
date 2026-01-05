"""
Обработчики профиля пользователя
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "🏋️‍♂️ ПРОФИЛЬ")
@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Преобразуем sqlite3.Row в словарь
    user_dict = dict(user)
    
    # Безопасное извлечение данных
    username = message.from_user.username or "Не указан"
    nickname = user_dict.get('nickname', 'Не указан')
    region = user_dict.get('region', 'Не указан')
    registration_number = user_dict.get('registration_number', 'Не указан')
    referrals_count = user_dict.get('referrals_count', 0)
    created_at = user_dict.get('created_at', 'Неизвестно')
    achievements_count = user_dict.get('achievements_count', 0)
    
    # Обработка баланса
    balance_tokens = float(user_dict.get('balance_tokens', 0)) if user_dict.get('balance_tokens') else 0.0
    balance_diamonds = float(user_dict.get('balance_diamonds', 0)) if user_dict.get('balance_diamonds') else 0.0
    
    # Статистика тренировок и дуэлей
    total_trainings = user_dict.get('total_trainings', 0)
    total_duels = user_dict.get('total_duels', 0)
    duels_won = user_dict.get('duels_won', 0)
    
    # Форматирование даты
    if created_at != "Неизвестно" and len(created_at) > 10:
        created_at = created_at[:10]
    
    # Расчет уровня (простая формула)
    level = user_dict.get('level', 1)
    experience = user_dict.get('experience', 0)
    exp_for_next_level = level * 100
    exp_progress = min(100, int((experience / exp_for_next_level) * 100)) if exp_for_next_level > 0 else 0
    
    text = (
        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"🏷️ <b>ID:</b> <code>{registration_number}</code>\n"
        f"👤 <b>Имя пользователя:</b> @{username}\n"
        f"🎯 <b>Никнейм:</b> {nickname}\n"
        f"🌍 <b>Регион:</b> {region}\n"
        f"📅 <b>Дата регистрации:</b> {created_at}\n\n"
        
        f"📊 <b>Статистика:</b>\n"
        f"• 🎮 <b>Уровень:</b> {level} ({exp_progress}%)\n"
        f"• 👥 <b>Приглашено друзей:</b> {referrals_count}\n"
        f"• 🏆 <b>Достижения:</b> {achievements_count}\n"
        f"• 💪 <b>Тренировки:</b> {total_trainings}\n"
        f"• ⚔️ <b>Дуэли:</b> {total_duels} (побед: {duels_won})\n\n"
        
        f"💰 <b>Баланс:</b>\n"
        f"• Токены: {balance_tokens:.2f} GFT\n"
        f"• Алмазы: {balance_diamonds:.2f} 💎\n\n"
        
        f"<i>Используйте меню для навигации</i>"
    )
    
    await message.answer(text, reply_markup=MainKeyboards.get_main_menu())

@router.message(F.text == "👤 Личный кабинет")
async def personal_account(message: Message):
    """Обработчик личного кабинета"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    user_dict = dict(user)
    
    nickname = user_dict.get('nickname', 'Не указан')
    registration_number = user_dict.get('registration_number', 'Не указан')
    
    # Получаем балансы
    balances = db.get_user_balance(telegram_id)
    tokens = balances.get('tokens', 0.0)
    diamonds = balances.get('diamonds', 0.0)
    
    # Получаем информацию о премиуме
    is_premium = user_dict.get('is_premium', False)
    premium_until = user_dict.get('premium_until', '')
    
    premium_status = "✅ Активен" if is_premium else "❌ Не активен"
    premium_info = f"до {premium_until[:10]}" if premium_until and len(premium_until) > 10 else "не приобретен"
    
    text = (
        f"🏦 <b>ЛИЧНЫЙ КАБИНЕТ</b>\n\n"
        f"👤 <b>Владелец:</b> {nickname}\n"
        f"🏷️ <b>ID:</b> <code>{registration_number}</code>\n\n"
        
        f"💰 <b>Финансы:</b>\n"
        f"• Токены GFT: {tokens:.2f}\n"
        f"• Алмазы: {diamonds:.2f} 💎\n\n"
        
        f"👑 <b>Премиум статус:</b>\n"
        f"• Статус: {premium_status}\n"
        f"• {premium_info}\n\n"
        
        f"<i>Управляйте своими финансами и подписками</i>"
    )
    
    await message.answer(text, reply_markup=MainKeyboards.get_bottom_keyboard())