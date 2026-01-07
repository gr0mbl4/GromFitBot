"""
Полный модуль обработчиков реферальной системы GromFitBot
Обрабатывает все команды и действия связанные с рефералами
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import urllib.parse

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database import Database
from core.message_manager import MessageManager
from modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()
message_manager = MessageManager(None)
logger = logging.getLogger(__name__)

def init_message_manager(bot):
    """Инициализация менеджера сообщений"""
    global message_manager
    message_manager = MessageManager(bot)

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ РЕФЕРАЛОВ ====================

@router.message(F.text == "🤝 Рефералы")
async def handle_referrals(message: Message):
    """Основной обработчик кнопки 'Рефералы'"""
    user_id = message.from_user.id
    logger.info(f"Запрос рефералов от пользователя {user_id}")
    
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации в боте."
        )
        return
    
    await show_referrals_menu(message, user)

async def show_referrals_menu(message: Message, user: Dict[str, Any]):
    """Отображение меню рефералов"""
    user_id = user['telegram_id']
    
    # Получаем реферальную статистику
    referrals_count = user.get('referrals_count', 0)
    referrals_list = db.get_referrals(user_id)
    
    # Получаем реферера
    referrer = db.get_referrer(user_id)
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    # Формируем текст
    referrals_text = (
        f"🤝 <b>Реферальная система</b>\n\n"
        
        f"<b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"<b>Статистика:</b>\n"
        f"👥 <b>Приглашено пользователей:</b> {referrals_count}\n"
        f"🎯 <b>Активных рефералов:</b> {len([r for r in referrals_list if is_user_active(r)])}\n"
        f"💰 <b>Заработано с рефералов:</b> {referrals_count * 10} токенов\n\n"
    )
    
    # Информация о реферере
    if referrer:
        referrals_text += (
            f"<b>Ваш реферер:</b>\n"
            f"👤 {referrer['nickname']} (ID: {referrer['registration_number']})\n"
            f"📅 Регистрация: {format_date(referrer['created_at'])}\n\n"
        )
    else:
        referrals_text += "<b>Ваш реферер:</b> Не указан\n\n"
    
    # Уровень реферальной программы
    rank = get_referral_rank(referrals_count)
    next_rank = get_next_rank(referrals_count)
    
    referrals_text += (
        f"<b>Ваш ранг:</b> {rank['name']} {rank['icon']}\n"
        f"<b>До следующего ранга:</b> {next_rank['required'] - referrals_count} пользователей\n\n"
    )
    
    # Прогресс-бар
    progress_width = 20
    progress = min(referrals_count / next_rank['required'], 1.0) if next_rank['required'] > 0 else 1.0
    filled = int(progress_width * progress)
    progress_bar = "█" * filled + "░" * (progress_width - filled)
    
    referrals_text += (
        f"<b>Прогресс:</b> {referrals_count}/{next_rank['required']}\n"
        f"{progress_bar} {progress*100:.0f}%\n\n"
    )
    
    referrals_text += "<i>Приглашайте друзей и получайте бонусы!</i>"
    
    await message_manager.replace_message(
        message,
        referrals_text,
        MainKeyboards.get_referrals_keyboard()
    )

def is_user_active(user: Dict[str, Any], days_threshold: int = 7) -> bool:
    """Проверка активности пользователя"""
    last_active = user.get('last_active')
    if not last_active:
        return False
    
    try:
        if isinstance(last_active, str):
            last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
        else:
            last_active_date = last_active
        
        days_inactive = (datetime.now() - last_active_date).days
        return days_inactive <= days_threshold
    except:
        return False

def get_referral_rank(referrals_count: int) -> Dict[str, Any]:
    """Определение ранга по количеству рефералов"""
    ranks = [
        {'name': 'Новичок', 'icon': '🥉', 'min': 0, 'max': 2},
        {'name': 'Бронза', 'icon': '🥉', 'min': 3, 'max': 9},
        {'name': 'Серебро', 'icon': '🥈', 'min': 10, 'max': 24},
        {'name': 'Золото', 'icon': '🥇', 'min': 25, 'max': 49},
        {'name': 'Платина', 'icon': '💎', 'min': 50, 'max': 99},
        {'name': 'Мастер', 'icon': '👑', 'min': 100, 'max': 999999}
    ]
    
    for rank in ranks:
        if rank['min'] <= referrals_count <= rank['max']:
            return {
                'name': rank['name'],
                'icon': rank['icon'],
                'min': rank['min'],
                'max': rank['max']
            }
    
    return {'name': 'Новичок', 'icon': '🥉', 'min': 0, 'max': 2}

def get_next_rank(referrals_count: int) -> Dict[str, Any]:
    """Получение информации о следующем ранге"""
    ranks = [
        {'name': 'Новичок', 'required': 3},
        {'name': 'Бронза', 'required': 10},
        {'name': 'Серебро', 'required': 25},
        {'name': 'Золото', 'required': 50},
        {'name': 'Платина', 'required': 100},
        {'name': 'Мастер', 'required': 1000}
    ]
    
    for rank in ranks:
        if referrals_count < rank['required']:
            return rank
    
    return {'name': 'Мастер', 'required': 1000}

def format_date(date_str: str) -> str:
    """Форматирование даты"""
    if not date_str:
        return "Неизвестно"
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = date_str
        
        return date_obj.strftime("%d.%m.%Y")
    except:
        return "Неизвестно"

# ==================== ОБРАБОТЧИКИ ПОДМЕНЮ РЕФЕРАЛОВ ====================

@router.callback_query(F.data == "referral_stats")
async def handle_referral_stats(callback: CallbackQuery):
    """Обработчик кнопки 'Статистика' в рефералах"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем расширенную статистику
    referrals_list = db.get_referrals(user_id)
    referrals_count = len(referrals_list)
    
    # Анализируем активность рефералов
    active_referrals = []
    inactive_referrals = []
    today = datetime.now().date()
    
    for referral in referrals_list:
        last_active = referral.get('last_active')
        if last_active:
            try:
                if isinstance(last_active, str):
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00')).date()
                else:
                    last_active_date = last_active.date()
                
                days_inactive = (today - last_active_date).days
                if days_inactive <= 7:
                    active_referrals.append(referral)
                else:
                    inactive_referrals.append(referral)
            except:
                inactive_referrals.append(referral)
        else:
            inactive_referrals.append(referral)
    
    # Конверсия (если были приглашения)
    conversion_rate = 0
    if referrals_count > 0:
        conversion_rate = (len(active_referrals) / referrals_count) * 100
    
    # Доход от рефералов
    total_income = referrals_count * 10  # По 10 токенов за каждого
    
    stats_text = (
        f"📊 <b>Подробная статистика рефералов</b>\n\n"
        
        f"<b>Основные метрики:</b>\n"
        f"👥 <b>Всего приглашено:</b> {referrals_count}\n"
        f"✅ <b>Активных:</b> {len(active_referrals)} ({conversion_rate:.1f}%)\n"
        f"❌ <b>Неактивных:</b> {len(inactive_referrals)}\n"
        f"💰 <b>Общий доход:</b> {total_income} токенов\n\n"
        
        f"<b>Активность за периоды:</b>\n"
        f"• За последние 24 часа: {count_active_by_period(referrals_list, 1)}\n"
        f"• За последние 7 дней: {count_active_by_period(referrals_list, 7)}\n"
        f"• За последние 30 дней: {count_active_by_period(referrals_list, 30)}\n\n"
    )
    
    # Топ рефералов по активности
    if referrals_list:
        # Сортируем по последней активности
        sorted_referrals = sorted(
            referrals_list,
            key=lambda x: x.get('last_active', ''),
            reverse=True
        )[:5]
        
        stats_text += "<b>Самые активные рефералы:</b>\n"
        for i, referral in enumerate(sorted_referrals, 1):
            nickname = referral.get('nickname', 'Без имени')
            last_active = referral.get('last_active', '')
            
            if last_active:
                try:
                    if isinstance(last_active, str):
                        last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    else:
                        last_active_date = last_active
                    
                    days_ago = (datetime.now() - last_active_date).days
                    if days_ago == 0:
                        activity = "сегодня"
                    elif days_ago == 1:
                        activity = "вчера"
                    else:
                        activity = f"{days_ago} дн. назад"
                except:
                    activity = "давно"
            else:
                activity = "никогда"
            
            stats_text += f"{i}. {nickname} - был {activity}\n"
    
    stats_text += "\n<i>Статистика обновляется в реальном времени</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        stats_text,
        MainKeyboards.get_back_keyboard("referrals")
    )
    
    await message_manager.answer_callback_with_notification(callback)

def count_active_by_period(referrals: List[Dict[str, Any]], days: int) -> int:
    """Подсчет активных рефералов за период"""
    count = 0
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for referral in referrals:
        last_active = referral.get('last_active')
        if last_active:
            try:
                if isinstance(last_active, str):
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                else:
                    last_active_date = last_active
                
                if last_active_date >= cutoff_date:
                    count += 1
            except:
                continue
    
    return count

@router.callback_query(F.data == "referral_leaders")
async def handle_referral_leaders(callback: CallbackQuery):
    """Обработчик кнопки 'Лидеры' в рефералах"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем топ рефереров
    leaders = db.get_top_referrers(limit=15)
    
    if not leaders:
        leaders_text = "🏆 <b>Топ рефереров</b>\n\n"
        leaders_text += "Пока нет лидеров. Будьте первым!\n\n"
        leaders_text += "<i>Приглашайте друзей и поднимайтесь в топе!</i>"
    else:
        leaders_text = "🏆 <b>Топ рефереров</b>\n\n"
        
        for i, leader in enumerate(leaders, 1):
            nickname = leader.get('nickname', 'Без имени')
            referrals_count = leader.get('referrals_count', 0)
            registration_number = leader.get('registration_number', 'N/A')
            
            # Определяем медаль
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            # Определяем ранг
            rank = get_referral_rank(referrals_count)
            
            leaders_text += f"{medal} <b>{nickname}</b>\n"
            leaders_text += f"   👥 {referrals_count} реф. | {rank['name']} {rank['icon']}\n"
            leaders_text += f"   🆔 {registration_number}\n"
            
            # Если это текущий пользователь, отмечаем его
            if leader['telegram_id'] == user_id:
                leaders_text += "   👉 <b>Это вы!</b>\n"
            
            leaders_text += "\n"
    
    # Добавляем позицию текущего пользователя
    user_position = get_user_leaderboard_position(user_id, leaders)
    if user_position > 0:
        leaders_text += f"<b>Ваша позиция в топе:</b> #{user_position}\n"
    else:
        leaders_text += "<b>Вы пока не в топе</b>\n"
    
    leaders_text += "\n<i>Топ обновляется ежедневно</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        leaders_text,
        MainKeyboards.get_back_keyboard("referrals")
    )
    
    await message_manager.answer_callback_with_notification(callback)

def get_user_leaderboard_position(user_id: int, leaders: List[Dict[str, Any]]) -> int:
    """Получение позиции пользователя в таблице лидеров"""
    for i, leader in enumerate(leaders, 1):
        if leader['telegram_id'] == user_id:
            return i
    
    return -1

@router.callback_query(F.data == "referral_list")
async def handle_referral_list(callback: CallbackQuery):
    """Обработчик кнопки 'Список рефералов'"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем список рефералов
    referrals = db.get_referrals(user_id)
    
    if not referrals:
        await message_manager.edit_message_with_menu(
            callback,
            "📋 <b>Список ваших рефералов</b>\n\n"
            "У вас пока нет рефералов.\n\n"
            "<i>Приглашайте друзей по своей реферальной ссылке!</i>",
            MainKeyboards.get_back_keyboard("referrals")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    # Группируем по активности
    active_referrals = []
    inactive_referrals = []
    today = datetime.now().date()
    
    for referral in referrals:
        last_active = referral.get('last_active')
        is_active = False
        
        if last_active:
            try:
                if isinstance(last_active, str):
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00')).date()
                else:
                    last_active_date = last_active.date()
                
                days_inactive = (today - last_active_date).days
                is_active = days_inactive <= 7
            except:
                pass
        
        if is_active:
            active_referrals.append(referral)
        else:
            inactive_referrals.append(referral)
    
    # Формируем текст
    referrals_text = "📋 <b>Список ваших рефералов</b>\n\n"
    
    referrals_text += f"<b>Всего рефералов:</b> {len(referrals)}\n"
    referrals_text += f"<b>Активных:</b> {len(active_referrals)}\n"
    referrals_text += f"<b>Неактивных:</b> {len(inactive_referrals)}\n\n"
    
    # Показываем активных рефералов
    if active_referrals:
        referrals_text += "<b>✅ Активные рефералы:</b>\n"
        for i, referral in enumerate(active_referrals[:10], 1):
            nickname = referral.get('nickname', 'Без имени')
            created_at = referral.get('created_at', '')
            
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                    else:
                        created_date = created_at.date()
                    
                    date_str = created_date.strftime("%d.%m.%Y")
                except:
                    date_str = "Неизвестно"
            else:
                date_str = "Неизвестно"
            
            referrals_text += f"{i}. {nickname} (с {date_str})\n"
        
        if len(active_referrals) > 10:
            referrals_text += f"... и еще {len(active_referrals) - 10}\n"
        
        referrals_text += "\n"
    
    # Показываем неактивных рефералов
    if inactive_referrals:
        referrals_text += "<b>❌ Неактивные рефералы:</b>\n"
        for i, referral in enumerate(inactive_referrals[:5], 1):
            nickname = referral.get('nickname', 'Без имени')
            referrals_text += f"{i}. {nickname}\n"
        
        if len(inactive_referrals) > 5:
            referrals_text += f"... и еще {len(inactive_referrals) - 5}\n"
    
    referrals_text += "\n<i>Активным считается пользователь, заходивший в бота за последние 7 дней</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        referrals_text,
        MainKeyboards.get_back_keyboard("referrals")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "referral_bonuses")
async def handle_referral_bonuses(callback: CallbackQuery):
    """Обработчик кнопки 'Бонусы' в рефералах"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем информацию о бонусах
    referrals_count = user.get('referrals_count', 0)
    total_bonus = referrals_count * 10
    
    bonuses_text = (
        f"🎁 <b>Реферальные бонусы</b>\n\n"
        
        f"<b>Текущие начисления:</b>\n"
        f"💰 <b>За каждого реферала:</b> 10 токенов\n"
        f"👥 <b>Ваших рефералов:</b> {referrals_count}\n"
        f"💵 <b>Всего заработано:</b> {total_bonus} токенов\n\n"
        
        f"<b>Уровни бонусов:</b>\n"
        f"🥉 <b>Новичок (0-2 реф.):</b> 10 токенов за каждого\n"
        f"🥉 <b>Бронза (3-9 реф.):</b> 12 токенов за каждого\n"
        f"🥈 <b>Серебро (10-24 реф.):</b> 15 токенов за каждого\n"
        f"🥇 <b>Золото (25-49 реф.):</b> 20 токенов за каждого\n"
        f"💎 <b>Платина (50-99 реф.):</b> 25 токенов за каждого\n"
        f"👑 <b>Мастер (100+ реф.):</b> 30 токенов за каждого\n\n"
        
        f"<b>Дополнительные бонусы:</b>\n"
        f"• При достижении 10 рефералов: +100 токенов\n"
        f"• При достижении 50 рефералов: +500 токенов\n"
        f"• При достижении 100 рефералов: +1000 токенов\n\n"
        
        f"<b>Ваш текущий уровень:</b>\n"
    )
    
    # Определяем текущий ранг и бонус
    rank = get_referral_rank(referrals_count)
    bonus_per_referral = get_bonus_per_referral(rank['name'])
    
    bonuses_text += f"{rank['name']} {rank['icon']} - {bonus_per_referral} токенов за реферала\n\n"
    
    # Проверяем, какие бонусы уже получены
    achievements = db.get_user_achievements(user_id)
    achievement_ids = [a['achievement_id'] for a in achievements]
    
    if referrals_count >= 10 and 'referral_10' not in achievement_ids:
        bonuses_text += "🎯 <b>Доступно:</b> Бонус за 10 рефералов (+100 токенов)\n"
    
    if referrals_count >= 50 and 'referral_50' not in achievement_ids:
        bonuses_text += "🎯 <b>Доступно:</b> Бонус за 50 рефералов (+500 токенов)\n"
    
    if referrals_count >= 100 and 'referral_100' not in achievement_ids:
        bonuses_text += "🎯 <b>Доступно:</b> Бонус за 100 рефералов (+1000 токенов)\n"
    
    bonuses_text += "\n<i>Бонусы начисляются автоматически при регистрации реферала</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        bonuses_text,
        MainKeyboards.get_back_keyboard("referrals")
    )
    
    await message_manager.answer_callback_with_notification(callback)

def get_bonus_per_referral(rank_name: str) -> int:
    """Получение размера бонуса за реферала в зависимости от ранга"""
    bonuses = {
        'Новичок': 10,
        'Бронза': 12,
        'Серебро': 15,
        'Золото': 20,
        'Платина': 25,
        'Мастер': 30
    }
    return bonuses.get(rank_name, 10)

@router.callback_query(F.data == "referral_share")
async def handle_referral_share(callback: CallbackQuery):
    """Обработчик кнопки 'Поделиться' в рефералах"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Генерируем реферальную ссылку
    bot_username = (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    # Текст для шаринга
    share_text = (
        f"🤝 <b>Поделиться реферальной ссылкой</b>\n\n"
        
        f"<b>Ваша ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"<b>Текст для приглашения:</b>\n"
        f"Привет! Присоединяйся ко мне в GromFit Bot - крутом боте для спортивных дуэлей! 🏋️‍♂️\n\n"
        f"С ним ты сможешь:\n"
        f"• Участвовать в спортивных соревнованиях\n"
        f"• Зарабатывать токены за тренировки\n"
        f"• Бросать вызовы друзьям\n"
        f"• Получать достижения и награды\n\n"
        f"Регистрируйся по моей ссылке и получи бонусные токены! 🎁\n"
        f"{referral_link}\n\n"
        
        f"<b>Способы поделиться:</b>\n"
        f"1. Скопируйте ссылку выше\n"
        f"2. Отправьте друзьям в Telegram\n"
        f"3. Поделитесь в соцсетях\n"
        f"4. Добавьте в свою подпись\n\n"
        
        f"<i>За каждого приглашенного друга вы получите 10 токенов!</i>"
    )
    
    # Создаем клавиатуру с кнопкой поделиться
    builder = InlineKeyboardBuilder()
    
    # Кнопка для копирования ссылки
    builder.button(text="📋 Скопировать ссылку", callback_data=f"copy_referral_{user_id}")
    
    # Кнопка для шаринга в Telegram
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote('Присоединяйся ко мне в GromFit Bot! 🏋️‍♂️')}"
    builder.button(text="📢 Поделиться в Telegram", url=share_url)
    
    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_referrals"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        share_text,
        builder.as_markup()
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data.startswith("copy_referral_"))
async def handle_copy_referral(callback: CallbackQuery):
    """Обработчик копирования реферальной ссылки"""
    # В Telegram нельзя программно копировать в буфер обмена,
    # поэтому просто показываем уведомление
    await message_manager.answer_callback_with_notification(
        callback,
        "📋 Ссылка готова для копирования из сообщения выше",
        show_alert=True
    )

@router.callback_query(F.data == "referral_rules")
async def handle_referral_rules(callback: CallbackQuery):
    """Обработчик кнопки 'Правила' в рефералах"""
    rules_text = (
        f"📜 <b>Правила реферальной программы</b>\n\n"
        
        f"<b>Основные положения:</b>\n"
        f"1. Реферальная программа доступна всем зарегистрированным пользователям\n"
        f"2. За каждого приглашенного друга вы получаете 10 токенов\n"
        f"3. Друг должен пройти полную регистрацию по вашей ссылке\n"
        f"4. Бонусы начисляются мгновенно после регистрации реферала\n\n"
        
        f"<b>Условия участия:</b>\n"
        f"• Реферал должен быть новым пользователем\n"
        f"• Один пользователь может быть рефералом только один раз\n"
        f"• Запрещено создание фейковых аккаунтов\n"
        f"• Запрещено использование ботов для накрутки\n\n"
        
        f"<b>Уровни программы:</b>\n"
        f"• Уровень повышается с количеством рефералов\n"
        f"• На более высоких уровнях увеличивается бонус\n"
        f"• Достижение уровней приносит дополнительные награды\n\n"
        
        f"<b>Нарушения и санкции:</b>\n"
        f"• Нарушение правил ведет к обнулению рефералов\n"
        f"• Могут быть заблокированы токены\n"
        f"• В особых случаях - блокировка аккаунта\n\n"
        
        f"<b>Дополнительно:</b>\n"
        f"• Статистика обновляется в реальном времени\n"
        f"• Топ рефереров обновляется ежедневно\n"
        f"• Все споры решаются администрацией\n\n"
        
        f"<i>Программа действует бессрочно и может быть изменена</i>"
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        rules_text,
        MainKeyboards.get_back_keyboard("referrals")
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ НАВИГАЦИИ ====================

@router.callback_query(F.data == "back_to_referrals")
async def handle_back_to_referrals(callback: CallbackQuery):
    """Возврат в меню рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        await callback.message.answer(
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Создаем Message объект из callback
    msg = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        text="🤝 Рефералы",
        from_user=callback.from_user
    )
    msg.bot = callback.bot
    
    # Показываем меню рефералов
    await show_referrals_menu(msg, user)
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "back_to_referrals_menu")
async def handle_back_to_referrals_menu(callback: CallbackQuery):
    """Возврат в меню рефералов (алиас)"""
    await handle_back_to_referrals(callback)

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main_from_referrals(callback: CallbackQuery):
    """Возврат в главное меню из рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        await callback.message.answer(
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Создаем Message объект из callback
    msg = Message(
        message_id=callback.message.message_id,
        date=callback.message.date,
        chat=callback.message.chat,
        text="🏠 Главное меню",
        from_user=callback.from_user
    )
    msg.bot = callback.bot
    
    # Используем обработчик главного меню из основного бота
    from core.bot import GromFitBot
    bot_instance = GromFitBot()
    await bot_instance._show_main_menu(msg)
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== КОМАНДЫ ДЛЯ РЕФЕРАЛОВ ====================

@router.message(Command("referral"))
async def handle_referral_command(message: Message):
    """Обработчик команды /referral"""
    await handle_referrals(message)

@router.message(Command("myref"))
async def handle_myref_command(message: Message):
    """Обработчик команды /myref - показывает реферальную ссылку"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Генерируем реферальную ссылку
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    await message_manager.replace_message(
        message,
        f"🤝 <b>Ваша реферальная ссылка</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"<b>Статистика:</b>\n"
        f"• Приглашено: {user.get('referrals_count', 0)} пользователей\n"
        f"• Заработано: {user.get('referrals_count', 0) * 10} токенов\n\n"
        f"<i>Делитесь ссылкой с друзьями и получайте бонусы!</i>",
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("referrals"))
async def handle_referrals_command(message: Message):
    """Обработчик команды /referrals"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    referrals = db.get_referrals(user_id)
    
    if not referrals:
        await message_manager.replace_message(
            message,
            "📋 <b>Ваши рефералы</b>\n\n"
            "У вас пока нет рефералов.\n\n"
            "<i>Используйте команду /myref чтобы получить свою реферальную ссылку</i>",
            MainKeyboards.get_back_to_main_keyboard()
        )
        return
    
    referrals_text = "📋 <b>Ваши рефералы</b>\n\n"
    
    for i, referral in enumerate(referrals[:10], 1):
        nickname = referral.get('nickname', 'Без имени')
        created_at = referral.get('created_at', '')
        
        if created_at:
            try:
                if isinstance(created_at, str):
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
                else:
                    created_date = created_at.date()
                
                date_str = created_date.strftime("%d.%m.%Y")
            except:
                date_str = "Неизвестно"
        else:
            date_str = "Неизвестно"
        
        referrals_text += f"{i}. {nickname} (с {date_str})\n"
    
    if len(referrals) > 10:
        referrals_text += f"\n... и еще {len(referrals) - 10} рефералов"
    
    referrals_text += f"\n\n<b>Всего:</b> {len(referrals)} рефералов"
    
    await message_manager.replace_message(
        message,
        referrals_text,
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("leaders"))
async def handle_leaders_command(message: Message):
    """Обработчик команды /leaders - показывает топ рефереров"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Получаем топ рефереров
    leaders = db.get_top_referrers(limit=10)
    
    if not leaders:
        leaders_text = "🏆 <b>Топ рефереров</b>\n\n"
        leaders_text += "Пока нет лидеров.\n"
        leaders_text += "<i>Будьте первым - приглашайте друзей!</i>"
    else:
        leaders_text = "🏆 <b>Топ рефереров</b>\n\n"
        
        for i, leader in enumerate(leaders, 1):
            nickname = leader.get('nickname', 'Без имени')
            referrals_count = leader.get('referrals_count', 0)
            
            # Определяем медаль
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            leaders_text += f"{medal} <b>{nickname}</b> - {referrals_count} реф.\n"
        
        # Добавляем позицию текущего пользователя
        user_position = get_user_leaderboard_position(user_id, leaders)
        if user_position > 0:
            leaders_text += f"\n<b>Ваша позиция:</b> #{user_position}\n"
        else:
            leaders_text += f"\n<b>Ваша позиция:</b> не в топе\n"
        
        leaders_text += f"<b>Ваших рефералов:</b> {user.get('referrals_count', 0)}\n"
    
    await message_manager.replace_message(
        message,
        leaders_text,
        MainKeyboards.get_back_to_main_keyboard()
    )