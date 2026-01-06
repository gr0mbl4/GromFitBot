"""
Обработчики профиля пользователя
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "🏋️‍♂️ Профиль")
@router.message(Command("profile"))
async def handle_profile(message: Message):
    """Обработчик профиля пользователя (из главного меню и нижнего меню)"""
    
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы.\n"
            "Используйте /start для регистрации"
        )
        return
    
    # Форматируем дату регистрации
    from datetime import datetime
    created_at = user['created_at']
    if isinstance(created_at, str):
        try:
            reg_date = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
        except:
            try:
                reg_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%d.%m.%Y')
            except:
                reg_date = str(created_at)[:10]
    else:
        reg_date = str(created_at)[:10]
    
    # Форматируем последнюю активность
    last_active = user.get('last_active')
    if last_active:
        if isinstance(last_active, str):
            try:
                last_active_date = datetime.strptime(last_active, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            except:
                try:
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00')).strftime('%d.%m.%Y %H:%M')
                except:
                    last_active_date = str(last_active)[:16]
        else:
            last_active_date = str(last_active)[:16]
    else:
        last_active_date = "Неизвестно"
    
    # Определяем реферальный ранг
    referrals_count = user['referrals_count']
    referrer_rank = "Новичок"
    
    if referrals_count >= 100:
        referrer_rank = "Легенда"
    elif referrals_count >= 50:
        referrer_rank = "Платина"
    elif referrals_count >= 25:
        referrer_rank = "Золото"
    elif referrals_count >= 10:
        referrer_rank = "Серебро"
    elif referrals_count >= 3:
        referrer_rank = "Бронза"
    
    # Получаем клавиатуру для профиля
    keyboard = MainKeyboards.get_profile_inline_keyboard()
    
    # Формируем сообщение
    profile_text = (
        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"🆔 ID: <code>{user['registration_number']}</code>\n"
        f"👋 Никнейм: <b>{user['nickname']}</b>\n"
        f"🌍 Регион: <b>{user['region']}</b>\n"
        f"📅 Регистрация: <b>{reg_date}</b>\n"
        f"🕐 Последняя активность: <b>{last_active_date}</b>\n\n"
        f"💰 <b>Баланс:</b>\n"
        f"• Токены: <b>{user['balance_tokens']}</b>\n"
        f"• Алмазы: <b>{user.get('balance_diamonds', 0)}</b>\n\n"
        f"🏆 <b>Статистика:</b>\n"
        f"• Уровень: <b>{user.get('level', 1)}</b>\n"
        f"• Опыт: <b>{user.get('experience', 0)}</b>\n"
        f"• Достижений: <b>{user.get('achievements_count', 0)}</b>\n"
        f"• Рефералов: <b>{referrals_count}</b> ({referrer_rank})\n"
        f"• Серия дней: <b>{user.get('daily_streak', 0)}</b>\n\n"
        f"🎯 <b>Тренировки:</b>\n"
        f"• Всего тренировок: <b>{user.get('total_trainings', 0)}</b>\n"
        f"• Дуэлей: <b>{user.get('total_duels', 0)}</b>\n"
        f"• Побед: <b>{user.get('duels_won', 0)}</b>\n"
        f"• Очков: <b>{user.get('total_points', 0)}</b>"
    )
    
    await message.answer(
        profile_text,
        reply_markup=keyboard.as_markup()
    )

# Обработчики кнопок профиля
@router.callback_query(F.data == "profile_stats")
async def handle_profile_stats(callback: CallbackQuery):
    """Статистика профиля"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Получаем транзакции
    transactions = db.get_user_transactions(user_id, 5)
    
    transactions_text = ""
    if transactions:
        for i, tx in enumerate(transactions, 1):
            amount = tx['amount']
            tx_type = tx['transaction_type']
            description = tx.get('description', '')
            date_str = tx['created_at'][:10] if tx['created_at'] else ""
            
            sign = "➕" if amount > 0 else "➖"
            transactions_text += f"{i}. {sign} {abs(amount)} ({tx_type}) - {description} {date_str}\n"
    else:
        transactions_text = "Нет транзакций"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в профиль", callback_data="back_to_profile")
    builder.button(text="🏠 Главное меню", callback_data="profile_back_to_menu")
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"
        f"👤 Пользователь: <b>{user['nickname']}</b>\n\n"
        f"💸 <b>Последние транзакции:</b>\n{transactions_text}\n\n"
        f"🎮 <b>Игровая активность:</b>\n"
        f"• Тренировок: {user.get('total_trainings', 0)}\n"
        f"• Дуэлей: {user.get('total_duels', 0)}\n"
        f"• Побед: {user.get('duels_won', 0)}\n"
        f"• Винрейт: {round((user.get('duels_won', 0) / user.get('total_duels', 1)) * 100, 1) if user.get('total_duels', 0) > 0 else 0}%\n\n"
        f"🔥 <b>Серия:</b>\n"
        f"• Текущая серия: {user.get('daily_streak', 0)} дней\n"
        f"• Последний бонус: {user.get('last_streak_date', 'Никогда')}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_progress")
async def handle_profile_progress(callback: CallbackQuery):
    """Прогресс пользователя"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    level = user.get('level', 1)
    experience = user.get('experience', 0)
    
    # Расчет опыта для следующего уровня
    exp_needed = level * 100
    progress_percent = min(int((experience / exp_needed) * 100), 100)
    
    # Прогресс-бар
    progress_bar_length = 20
    filled = int(progress_percent / 100 * progress_bar_length)
    progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в профиль", callback_data="back_to_profile")
    builder.button(text="🏠 Главное меню", callback_data="profile_back_to_menu")
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"📈 <b>ПРОГРЕСС И УРОВЕНЬ</b>\n\n"
        f"🎮 Текущий уровень: <b>{level}</b>\n"
        f"⭐ Опыт: <b>{experience}/{exp_needed}</b>\n\n"
        f"{progress_bar} {progress_percent}%\n\n"
        f"📊 <b>Достижения:</b>\n"
        f"• Получено: {user.get('achievements_count', 0)}\n"
        f"• Всего доступно: 200\n\n"
        f"🏋️ <b>Тренировки:</b>\n"
        f"• Всего тренировок: {user.get('total_trainings', 0)}\n"
        f"• Последняя тренировка: {user.get('last_training_date', 'Никогда')}\n\n"
        f"💪 <b>Следующий уровень через:</b> {exp_needed - experience} опыта",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_settings")
async def handle_profile_settings(callback: CallbackQuery):
    """Настройки профиля"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Язык", callback_data="settings_language")
    builder.button(text="🎨 Тема", callback_data="settings_theme")
    builder.button(text="🔔 Уведомления", callback_data="settings_notifications")
    builder.button(text="🔙 Назад в профиль", callback_data="back_to_profile")
    builder.button(text="🏠 Главное меню", callback_data="profile_back_to_menu")
    builder.adjust(2, 1, 2)
    
    await callback.message.edit_text(
        "⚙️ <b>НАСТРОЙКИ ПРОФИЛЯ</b>\n\n"
        "Здесь вы можете настроить:\n\n"
        "🌐 <b>Язык</b> - изменить язык интерфейса\n"
        "🎨 <b>Тема</b> - светлая/темная тема\n"
        "🔔 <b>Уведомления</b> - настройки оповещений\n\n"
        "Выберите настройку для изменения:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_profile")
async def handle_back_to_profile(callback: CallbackQuery):
    """Возврат в профиль"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await handle_profile(callback.message)
    await callback.answer()

@router.callback_query(F.data == "profile_back_to_menu")
async def handle_profile_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню из профиля"""
    await handle_back_to_main_menu(callback)

# Общий обработчик возврата в главное меню
@router.callback_query(F.data == "back_to_main_menu")
async def handle_back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
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
    
    # Показываем нижнее меню
    await callback.message.answer(
        "📱 Основные действия:",
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )
    
    await callback.answer()