"""
Обработчики ежедневного бонуса - исправленная версия
Работает с обновленной базой данных
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, date, timedelta

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "🎁 Ежедневный бонус")
@router.message(Command("bonus"))
async def handle_daily_bonus(message: Message):
    """Обработчик ежедневного бонуса"""
    
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы.\n"
            "Используйте /start для регистрации",
            reply_markup=MainKeyboards.get_main_menu()
        )
        return
    
    # Получаем текущую дату
    today = date.today()
    
    # Получаем последнюю дату получения бонуса
    last_bonus_date = user.get('last_streak_date')
    daily_streak = user.get('daily_streak', 0)
    
    # Проверяем, получал ли пользователь бонус сегодня
    if last_bonus_date and isinstance(last_bonus_date, str):
        try:
            last_date = datetime.strptime(last_bonus_date, '%Y-%m-%d').date()
        except:
            last_date = None
    elif last_bonus_date and isinstance(last_bonus_date, date):
        last_date = last_bonus_date
    else:
        last_date = None
    
    can_claim = False
    streak_reset = False
    next_bonus_text = ""
    
    if last_date:
        days_diff = (today - last_date).days
        
        if days_diff == 0:
            # Уже получал бонус сегодня
            can_claim = False
            next_bonus_text = "завтра"
        elif days_diff == 1:
            # Пропустил один день - продолжаем серию
            can_claim = True
            daily_streak += 1
            next_bonus_text = "завтра"
        else:
            # Пропустил больше одного дня - сбрасываем серию
            can_claim = True
            daily_streak = 1
            streak_reset = True
            next_bonus_text = "завтра"
    else:
        # Первый раз получает бонус
        can_claim = True
        daily_streak = 1
        next_bonus_text = "завтра"
    
    if can_claim:
        # Рассчитываем бонус
        base_bonus = 10
        streak_bonus = min(daily_streak * 2, 50)  # Максимум 50 за серию
        total_bonus = base_bonus + streak_bonus
        
        # Начисляем бонус
        current_balance = user['balance_tokens']
        new_balance = current_balance + total_bonus
        
        # Обновляем данные пользователя
        db.update_user(
            user_id=user_id,
            data={
                'balance_tokens': new_balance,
                'last_streak_date': today.isoformat(),
                'daily_streak': daily_streak,
                'last_bonus_claim': datetime.now().isoformat()
            }
        )
        
        # Сообщение об успешном получении
        if streak_reset:
            streak_message = "🔁 Серия сброшена. Начинаем новую серию!"
        else:
            streak_message = f"🔥 Серия дней: {daily_streak}"
        
        await message.answer(
            f"🎉 <b>Ежедневный бонус получен!</b>\n\n"
            f"💰 Начислено: <b>{total_bonus}</b> токенов\n"
            f"• Базовая награда: {base_bonus}\n"
            f"• Бонус за серию: {streak_bonus}\n\n"
            f"{streak_message}\n"
            f"💵 Новый баланс: <b>{new_balance}</b> токенов\n\n"
            f"🔄 Следующий бонус: {next_bonus_text}"
        )
        
        # Добавляем запись в транзакции
        db.add_transaction(
            user_id=user_id,
            transaction_type='daily_bonus',
            amount=total_bonus,
            description=f'Ежедневный бонус (серия: {daily_streak} дней)'
        )
        
    else:
        # Бонус уже получен сегодня
        next_bonus_time = "00:00"  # Время следующего бонуса
        
        await message.answer(
            f"⏳ <b>Бонус уже получен сегодня!</b>\n\n"
            f"🔥 Текущая серия: <b>{daily_streak}</b> дней\n"
            f"💰 Следующий бонус: {next_bonus_text} в {next_bonus_time}\n\n"
            f"💡 Возвращайтесь завтра для продолжения серии!"
        )
    
    # Показываем кнопку "Главное меню"
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="bonus_back_to_menu")
    
    await message.answer(
        "📱 Вернуться в главное меню:",
        reply_markup=builder.as_markup()
    )

# Кнопка для быстрого получения бонуса
@router.callback_query(F.data == "claim_daily_bonus")
async def handle_claim_bonus_callback(callback: CallbackQuery):
    """Обработчик кнопки получения бонуса"""
    await handle_daily_bonus(callback.message)
    await callback.answer()

# Обработчик возврата в главное меню
@router.callback_query(F.data == "bonus_back_to_menu")
async def handle_bonus_back_to_menu(callback: CallbackQuery):
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
    
    # Нижнее меню уже висит, не нужно показывать снова
    await callback.answer()