from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database import db

router = Router()

@router.message(F.text == "🏆 Рейтинг")
async def show_rating(message: Message):
    """Показ рейтинга"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Общий рейтинг", callback_data="rating_global")],
        [InlineKeyboardButton(text="📍 Мой регион", callback_data="rating_regional")],
        [InlineKeyboardButton(text="👑 Мое место", callback_data="rating_my")]
    ])
    
    await message.answer(
        "🏆 **Рейтинговая система**\n\n"
        "Рейтинг основан на общем поднятом весе.\n"
        "Выберите тип рейтинга:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "rating_global")
async def show_global_rating(callback: CallbackQuery):
    """Показ общего рейтинга"""
    ratings = db.get_global_rating(limit=15)
    
    if not ratings:
        await callback.message.edit_text("📭 Пока никто не добавил тренировок.")
        return
    
    text = "🌍 **ОБЩИЙ РЕЙТИНГ**\n\n"
    
    for i, row in enumerate(ratings[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        name = row['display_name'] or row['telegram_username'] or f"Игрок #{row['rank']}"
        region = f"({row['region']})" if row['region'] else ""
        
        text += f"{medal} **{name}** {region}\n"
        text += f"   🏋️ {row['total_workouts']} тр. | "
        text += f"📦 {row['total_weight_lifted'] / 1000:.1f} т\n"
    
    # Добавляем кнопку "Обновить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="rating_global")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "rating_regional")
async def show_regional_rating(callback: CallbackQuery):
    """Показ регионального рейтинга"""
    user = db.get_user_by_telegram(callback.from_user.id)
    
    if not user or not user['region']:
        await callback.answer("У вас не указан регион", show_alert=True)
        return
    
    ratings = db.get_regional_rating(user['region'], limit=15)
    
    if not ratings:
        text = f"📍 **РЕЙТИНГ ПО РЕГИОНУ: {user['region']}**\n\n"
        text += "Пока никто из вашего региона не добавил тренировок.\nБудьте первым!"
    else:
        text = f"📍 **РЕЙТИНГ ПО РЕГИОНУ: {user['region']}**\n\n"
        
        for i, row in enumerate(ratings[:10], 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            name = row['display_name'] or row['telegram_username'] or f"Игрок #{row['rank']}"
            
            text += f"{medal} **{name}**\n"
            text += f"   🏋️ {row['total_workouts']} тр. | "
            text += f"📦 {row['total_weight_lifted'] / 1000:.1f} т\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="rating_regional")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "rating_my")
async def show_my_rating(callback: CallbackQuery):
    """Показ места пользователя в рейтинге"""
    user = db.get_user_by_telegram(callback.from_user.id)
    
    if not user:
        await callback.answer("Сначала зарегистрируйтесь", show_alert=True)
        return
    
    # Получаем общий рейтинг для поиска своего места
    all_ratings = db.get_global_rating(limit=1000)
    
    my_rank = None
    for i, row in enumerate(all_ratings, 1):
        if row['telegram_username'] == user['telegram_username'] or \
           row['display_name'] == user['display_name']:
            my_rank = i
            break
    
    text = "👑 **МОЕ МЕСТО В РЕЙТИНГЕ**\n\n"
    
    if my_rank:
        text += f"🌍 **Общий рейтинг:** #{my_rank}\n"
    else:
        text += "🌍 **Общий рейтинг:** пока нет тренировок\n"
    
    # Региональный рейтинг
    if user['region']:
        regional_ratings = db.get_regional_rating(user['region'], limit=1000)
        
        regional_rank = None
        for i, row in enumerate(regional_ratings, 1):
            if row['telegram_username'] == user['telegram_username'] or \
               row['display_name'] == user['display_name']:
                regional_rank = i
                break
        
        if regional_rank:
            text += f"📍 **{user['region']}:** #{regional_rank}\n"
        else:
            text += f"📍 **{user['region']}:** пока нет тренировок\n"
    
    text += f"\n🏋️ Ваши тренировки: {user['total_workouts']}\n"
    text += f"📦 Поднято тонн: {user['total_weight_lifted'] / 1000:.1f}\n"
    text += f"🔥 Текущая серия: {user['current_streak']} дней\n\n"
    text += "💪 **Продолжайте тренироваться, чтобы подниматься в рейтинге!**"
    
    await callback.message.edit_text(text, parse_mode="Markdown")