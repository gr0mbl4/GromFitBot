"""
Полный модуль обработчиков бонусов GromFitBot
Обрабатывает все команды и действия связанные с бонусами
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

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

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ БОНУСОВ ====================

@router.message(F.text == "🎁 Бонусы")
async def handle_bonus(message: Message):
    """Основной обработчик кнопки 'Бонусы'"""
    user_id = message.from_user.id
    logger.info(f"Запрос бонусов от пользователя {user_id}")
    
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации в боте."
        )
        return
    
    await show_bonus_menu(message, user)

async def show_bonus_menu(message: Message, user: Dict[str, Any]):
    """Отображение меню бонусов"""
    user_id = user['telegram_id']
    
    # Проверяем, может ли пользователь получить бонус
    can_claim = db.can_claim_bonus(user_id)
    daily_streak = user.get('daily_streak', 0)
    
    # Получаем информацию о следующем бонусе
    next_bonus_info = calculate_next_bonus(daily_streak)
    
    bonus_text = (
        f"🎁 <b>Ежедневные бонусы</b>\n\n"
        
        f"<b>Текущая серия дней:</b> {daily_streak}\n"
        f"<b>Множитель бонуса:</b> x{next_bonus_info['multiplier']:.1f}\n\n"
    )
    
    if can_claim:
        bonus_text += (
            f"✅ <b>Бонус доступен!</b>\n"
            f"💰 <b>Размер бонуса:</b> {next_bonus_info['amount']:.0f} токенов\n\n"
            
            f"<b>Как получить:</b>\n"
            f"1. Нажмите кнопку 'Получить ежедневный бонус'\n"
            f"2. Бонус будет начислен на ваш баланс\n"
            f"3. Серия дней увеличится на 1\n\n"
        )
    else:
        # Получаем информацию о последнем бонусе
        last_bonus_date = user.get('last_bonus_claim')
        
        if last_bonus_date:
            try:
                if isinstance(last_bonus_date, str):
                    last_date = datetime.fromisoformat(last_bonus_date.replace('Z', '+00:00')).date()
                else:
                    last_date = last_bonus_date.date()
                
                today = date.today()
                
                if last_date == today:
                    # Бонус уже получен сегодня
                    next_claim_date = today + timedelta(days=1)
                    days_until_next = 1
                    
                    bonus_text += (
                        f"⏳ <b>Бонус уже получен сегодня</b>\n"
                        f"💰 <b>Получено:</b> {next_bonus_info['amount']:.0f} токенов\n\n"
                        
                        f"<b>Следующий бонус:</b>\n"
                        f"📅 {next_claim_date.strftime('%d.%m.%Y')}\n"
                        f"⏰ Через {days_until_next} день\n\n"
                    )
                else:
                    # Бонус не получен, но время еще есть
                    bonus_text += "⚠️ <b>Бонус доступен, но не получен</b>\n\n"
            except:
                bonus_text += "ℹ️ <b>Информация о бонусе недоступна</b>\n\n"
        else:
            # Никогда не получал бонус
            bonus_text += "🎉 <b>Первый бонус ждет вас!</b>\n\n"
    
    # Информация о системе бонусов
    bonus_text += (
        f"<b>Система бонусов:</b>\n"
        f"• Заходите ежедневно для получения бонусов\n"
        f"• Серия дней увеличивает множитель бонуса\n"
        f"• Максимальный множитель: x{get_max_multiplier():.1f}\n"
        f"• Серия сбрасывается при пропуске дня\n\n"
        
        f"<i>Не пропускайте дни для максимальных бонусов!</i>"
    )
    
    await message_manager.replace_message(
        message,
        bonus_text,
        MainKeyboards.get_bonus_keyboard(can_claim, daily_streak)
    )

def calculate_next_bonus(streak: int) -> Dict[str, Any]:
    """Расчет следующего бонуса"""
    base_bonus = 5.0
    multiplier = min(1.2 ** min(streak, 7), get_max_multiplier())
    amount = base_bonus * multiplier
    
    return {
        'base': base_bonus,
        'multiplier': multiplier,
        'amount': amount,
        'streak': streak + 1
    }

def get_max_multiplier() -> float:
    """Получение максимального множителя"""
    return 3.0  # Максимальный множитель x3.0

# ==================== ОБРАБОТЧИКИ ПОЛУЧЕНИЯ БОНУСОВ ====================

@router.callback_query(F.data == "bonus_claim_daily")
async def handle_bonus_claim_daily(callback: CallbackQuery):
    """Обработчик получения ежедневного бонуса"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Пытаемся получить бонус
    claim_result = db.claim_daily_bonus(user_id)
    
    if not claim_result['success']:
        error_message = claim_result.get('error', 'Неизвестная ошибка')
        
        await message_manager.answer_callback_with_notification(
            callback,
            f"❌ {error_message}",
            show_alert=True
        )
        
        # Обновляем меню бонусов
        await show_bonus_menu_from_callback(callback, user)
        return
    
    # Бонус успешно получен
    bonus_amount = claim_result['bonus_amount']
    daily_streak = claim_result['daily_streak']
    new_balance = claim_result['new_balance']
    
    # Показываем анимацию получения бонуса
    await show_bonus_animation(callback, bonus_amount, daily_streak)
    
    # Обновляем меню бонусов
    await asyncio.sleep(2)  # Пауза для анимации
    
    # Обновляем информацию о пользователе
    user = db.get_user(user_id)
    await show_bonus_menu_from_callback(callback, user)

async def show_bonus_animation(callback: CallbackQuery, bonus_amount: float, streak: int):
    """Показ анимации получения бонуса"""
    animation_text = (
        f"🎉 <b>Бонус получен!</b>\n\n"
        
        f"<b>Начислено:</b>\n"
        f"💰 <b>{bonus_amount:.0f} токенов</b>\n\n"
        
        f"<b>Серия дней:</b> {streak} 🔥\n\n"
    )
    
    # Добавляем прогресс-бар для серии
    max_streak_for_max_multiplier = 7
    progress_width = 20
    progress = min(streak / max_streak_for_max_multiplier, 1.0)
    filled = int(progress_width * progress)
    progress_bar = "█" * filled + "░" * (progress_width - filled)
    
    animation_text += (
        f"<b>Прогресс к максимальному множителю:</b>\n"
        f"{progress_bar} {progress*100:.0f}%\n\n"
    )
    
    # Информация о следующем бонусе
    next_bonus = calculate_next_bonus(streak)
    animation_text += (
        f"<b>Следующий бонус:</b>\n"
        f"💰 {next_bonus['amount']:.0f} токенов (x{next_bonus['multiplier']:.1f})\n\n"
        
        f"<i>Не пропускайте завтрашний день!</i>"
    )
    
    # Временное сообщение с анимацией
    temp_message = await callback.message.answer(animation_text)
    
    # Удаляем временное сообщение через 2 секунды
    await asyncio.sleep(2)
    await temp_message.delete()

async def show_bonus_menu_from_callback(callback: CallbackQuery, user: Dict[str, Any]):
    """Отображение меню бонусов из callback"""
    user_id = user['telegram_id']
    
    # Проверяем, может ли пользователь получить бонус
    can_claim = db.can_claim_bonus(user_id)
    daily_streak = user.get('daily_streak', 0)
    
    # Получаем информацию о следующем бонусе
    next_bonus_info = calculate_next_bonus(daily_streak)
    
    bonus_text = (
        f"🎁 <b>Ежедневные бонусы</b>\n\n"
        
        f"<b>Текущая серия дней:</b> {daily_streak}\n"
        f"<b>Множитель бонуса:</b> x{next_bonus_info['multiplier']:.1f}\n\n"
    )
    
    if can_claim:
        bonus_text += (
            f"✅ <b>Бонус доступен!</b>\n"
            f"💰 <b>Размер бонуса:</b> {next_bonus_info['amount']:.0f} токенов\n\n"
        )
    else:
        bonus_text += "⏳ <b>Бонус уже получен сегодня</b>\n\n"
    
    bonus_text += (
        f"<b>Система бонусов:</b>\n"
        f"• Заходите ежедневно для получения бонусов\n"
        f"• Серия дней увеличивает множитель бонуса\n"
        f"• Максимальный множитель: x{get_max_multiplier():.1f}\n"
        f"• Серия сбрасывается при пропуске дня\n\n"
        
        f"<i>Не пропускайте дни для максимальных бонусов!</i>"
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        bonus_text,
        MainKeyboards.get_bonus_keyboard(can_claim, daily_streak)
    )

@router.callback_query(F.data == "bonus_already_claimed")
async def handle_bonus_already_claimed(callback: CallbackQuery):
    """Обработчик попытки получения уже полученного бонуса"""
    await message_manager.answer_callback_with_notification(
        callback,
        "⏳ Бонус уже получен сегодня. Зайдите завтра!",
        show_alert=True
    )

# ==================== ОБРАБОТЧИКИ СТАТИСТИКИ БОНУСОВ ====================

@router.callback_query(F.data == "bonus_stats")
async def handle_bonus_stats(callback: CallbackQuery):
    """Обработчик кнопки 'Статистика бонусов'"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем историю транзакций (только бонусы)
    transactions = db.get_user_transactions(user_id, limit=50)
    bonus_transactions = [t for t in transactions if t['transaction_type'] == 'daily_bonus']
    
    # Анализируем статистику
    total_bonuses = len(bonus_transactions)
    total_tokens = sum(t['amount'] for t in bonus_transactions)
    
    # Вычисляем средний бонус
    avg_bonus = total_tokens / total_bonuses if total_bonuses > 0 else 0
    
    # Находим максимальный бонус
    max_bonus = max((t['amount'] for t in bonus_transactions), default=0)
    
    # Анализируем по месяцам
    monthly_stats = analyze_monthly_bonuses(bonus_transactions)
    
    # Текущая серия
    current_streak = user.get('daily_streak', 0)
    max_streak = calculate_max_streak(bonus_transactions)
    
    stats_text = (
        f"📊 <b>Статистика бонусов</b>\n\n"
        
        f"<b>Общая статистика:</b>\n"
        f"🎁 <b>Всего получено бонусов:</b> {total_bonuses}\n"
        f"💰 <b>Всего получено токенов:</b> {total_tokens:.0f}\n"
        f"📈 <b>Средний бонус:</b> {avg_bonus:.1f} токенов\n"
        f"🏆 <b>Максимальный бонус:</b> {max_bonus:.0f} токенов\n\n"
        
        f"<b>Серии дней:</b>\n"
        f"🔥 <b>Текущая серия:</b> {current_streak} дней\n"
        f"🏅 <b>Максимальная серия:</b> {max_streak} дней\n\n"
    )
    
    # Статистика по месяцам
    if monthly_stats:
        stats_text += "<b>Статистика по месяцам:</b>\n"
        
        for month, data in list(monthly_stats.items())[-3:]:  # Последние 3 месяца
            stats_text += f"• {month}: {data['count']} бонусов, {data['total']:.0f} токенов\n"
        
        stats_text += "\n"
    
    # Последние бонусы
    if bonus_transactions:
        stats_text += "<b>Последние бонусы:</b>\n"
        
        for i, transaction in enumerate(bonus_transactions[:5], 1):
            amount = transaction['amount']
            created_at = transaction['created_at']
            
            if created_at:
                try:
                    if isinstance(created_at, str):
                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        date_obj = created_at
                    
                    date_str = date_obj.strftime("%d.%m")
                except:
                    date_str = "Неизвестно"
            else:
                date_str = "Неизвестно"
            
            stats_text += f"{i}. {date_str}: {amount:.0f} токенов\n"
    
    stats_text += "\n<i>Статистика обновляется в реальном времени</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        stats_text,
        MainKeyboards.get_back_keyboard("bonus")
    )
    
    await message_manager.answer_callback_with_notification(callback)

def analyze_monthly_bonuses(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Анализ бонусов по месяцам"""
    monthly_stats = {}
    
    for transaction in transactions:
        created_at = transaction['created_at']
        amount = transaction['amount']
        
        if not created_at:
            continue
        
        try:
            if isinstance(created_at, str):
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                date_obj = created_at
            
            month_key = date_obj.strftime("%Y-%m")
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'count': 0,
                    'total': 0,
                    'max': 0
                }
            
            monthly_stats[month_key]['count'] += 1
            monthly_stats[month_key]['total'] += amount
            
            if amount > monthly_stats[month_key]['max']:
                monthly_stats[month_key]['max'] = amount
        except:
            continue
    
    return monthly_stats

def calculate_max_streak(transactions: List[Dict[str, Any]]) -> int:
    """Вычисление максимальной серии дней"""
    if not transactions:
        return 0
    
    # Сортируем транзакции по дате
    sorted_transactions = sorted(
        transactions,
        key=lambda x: x.get('created_at', ''),
        reverse=True
    )
    
    max_streak = 0
    current_streak = 0
    prev_date = None
    
    for transaction in sorted_transactions:
        created_at = transaction['created_at']
        
        if not created_at:
            continue
        
        try:
            if isinstance(created_at, str):
                current_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date()
            else:
                current_date = created_at.date()
            
            if prev_date is None:
                current_streak = 1
            else:
                days_diff = (prev_date - current_date).days
                
                if days_diff == 1:
                    current_streak += 1
                elif days_diff > 1:
                    # Проверяем, не является ли это началом новой серии
                    if current_streak > max_streak:
                        max_streak = current_streak
                    current_streak = 1
                else:
                    # Тот же день - пропускаем
                    continue
            
            prev_date = current_date
        except:
            continue
    
    # Проверяем последнюю серию
    if current_streak > max_streak:
        max_streak = current_streak
    
    return max_streak

@router.callback_query(F.data == "bonus_records")
async def handle_bonus_records(callback: CallbackQuery):
    """Обработчик кнопки 'Рекорды'"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем историю транзакций (только бонусы)
    transactions = db.get_user_transactions(user_id, limit=100)
    bonus_transactions = [t for t in transactions if t['transaction_type'] == 'daily_bonus']
    
    if not bonus_transactions:
        await message_manager.edit_message_with_menu(
            callback,
            "🏆 <b>Рекорды бонусов</b>\n\n"
            "У вас пока нет полученных бонусов.\n\n"
            "<i>Получите первый бонус, чтобы установить рекорды!</i>",
            MainKeyboards.get_back_keyboard("bonus")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    # Находим рекорды
    records = calculate_bonus_records(bonus_transactions)
    
    records_text = (
        f"🏆 <b>Рекорды бонусов</b>\n\n"
        
        f"<b>Самый большой бонус:</b>\n"
        f"💰 <b>{records['max_bonus']['amount']:.0f} токенов</b>\n"
        f"📅 {records['max_bonus']['date']}\n"
        f"🔥 Серия дней: {records['max_bonus']['streak']}\n\n"
        
        f"<b>Самый маленький бонус:</b>\n"
        f"💰 <b>{records['min_bonus']['amount']:.0f} токенов</b>\n"
        f"📅 {records['min_bonus']['date']}\n\n"
        
        f"<b>Самая длинная серия:</b>\n"
        f"🔥 <b>{records['max_streak']} дней</b>\n"
        f"📅 {records['max_streak_period']}\n\n"
        
        f"<b>Общее количество бонусов:</b> {records['total_count']}\n"
        f"<b>Общая сумма бонусов:</b> {records['total_amount']:.0f} токенов\n"
        f"<b>Средний бонус:</b> {records['average_bonus']:.1f} токенов\n\n"
        
        f"<b>Последние достижения:</b>\n"
    )
    
    # Добавляем последние рекорды
    for record in records['recent_achievements'][:3]:
        records_text += f"• {record}\n"
    
    records_text += "\n<i>Ставьте новые рекорды каждый день!</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        records_text,
        MainKeyboards.get_back_keyboard("bonus")
    )
    
    await message_manager.answer_callback_with_notification(callback)

def calculate_bonus_records(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Вычисление рекордов бонусов"""
    if not transactions:
        return {}
    
    # Находим самый большой и маленький бонусы
    max_bonus = max(transactions, key=lambda x: x['amount'])
    min_bonus = min(transactions, key=lambda x: x['amount'])
    
    # Вычисляем максимальную серию
    max_streak = calculate_max_streak(transactions)
    
    # Общая статистика
    total_count = len(transactions)
    total_amount = sum(t['amount'] for t in transactions)
    average_bonus = total_amount / total_count if total_count > 0 else 0
    
    # Форматируем даты
    def format_bonus_date(transaction):
        created_at = transaction.get('created_at')
        if not created_at:
            return "Неизвестно"
        
        try:
            if isinstance(created_at, str):
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                date_obj = created_at
            
            return date_obj.strftime("%d.%m.%Y")
        except:
            return "Неизвестно"
    
    # Определяем период максимальной серии (упрощенно)
    max_streak_period = "Неизвестно"
    if transactions:
        try:
            first_date = datetime.fromisoformat(transactions[0]['created_at'].replace('Z', '+00:00'))
            last_date = datetime.fromisoformat(transactions[-1]['created_at'].replace('Z', '+00:00'))
            
            if (last_date - first_date).days >= max_streak:
                max_streak_period = f"{first_date.strftime('%d.%m')}-{last_date.strftime('%d.%m.%Y')}"
        except:
            pass
    
    # Определяем серию для максимального бонуса (упрощенно)
    max_bonus_streak = 1
    for i, t in enumerate(transactions):
        if t['id'] == max_bonus['id'] and i > 0:
            # Проверяем предыдущие дни
            current_date = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')).date()
            streak_count = 1
            
            for j in range(i-1, -1, -1):
                prev_date = datetime.fromisoformat(transactions[j]['created_at'].replace('Z', '+00:00')).date()
                days_diff = (current_date - prev_date).days
                
                if days_diff == streak_count:
                    streak_count += 1
                else:
                    break
            
            max_bonus_streak = streak_count
            break
    
    # Собираем недавние достижения
    recent_achievements = []
    if total_count >= 10:
        recent_achievements.append(f"Получено 10 бонусов")
    if total_count >= 25:
        recent_achievements.append(f"Получено 25 бонусов")
    if total_count >= 50:
        recent_achievements.append(f"Получено 50 бонусов")
    if total_amount >= 100:
        recent_achievements.append(f"Заработано 100 токенов с бонусов")
    if total_amount >= 500:
        recent_achievements.append(f"Заработано 500 токенов с бонусов")
    if max_streak >= 7:
        recent_achievements.append(f"Достигнута серия из 7 дней")
    if max_streak >= 30:
        recent_achievements.append(f"Достигнута серия из 30 дней")
    
    return {
        'max_bonus': {
            'amount': max_bonus['amount'],
            'date': format_bonus_date(max_bonus),
            'streak': max_bonus_streak
        },
        'min_bonus': {
            'amount': min_bonus['amount'],
            'date': format_bonus_date(min_bonus)
        },
        'max_streak': max_streak,
        'max_streak_period': max_streak_period,
        'total_count': total_count,
        'total_amount': total_amount,
        'average_bonus': average_bonus,
        'recent_achievements': recent_achievements
    }

@router.callback_query(F.data == "bonus_streak_info")
async def handle_bonus_streak_info(callback: CallbackQuery):
    """Обработчик информации о серии дней"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    daily_streak = user.get('daily_streak', 0)
    
    streak_text = (
        f"🔥 <b>Система серий дней</b>\n\n"
        
        f"<b>Ваша текущая серия:</b> {daily_streak} дней\n\n"
        
        f"<b>Как работает система:</b>\n"
        f"1. Каждый день вы получаете бонус\n"
        f"2. За каждый день серии множитель увеличивается\n"
        f"3. Максимальный множитель достигается на 7-й день\n"
        f"4. Если пропустить день - серия сбрасывается\n\n"
        
        f"<b>Множители по дням:</b>\n"
    )
    
    # Показываем множители для первых 7 дней
    for day in range(1, 8):
        multiplier = min(1.2 ** (day - 1), get_max_multiplier())
        bonus_amount = 5.0 * multiplier
        
        if day == daily_streak + 1:
            streak_text += f"👉 <b>День {day}:</b> x{multiplier:.1f} = {bonus_amount:.0f} токенов\n"
        elif day <= daily_streak:
            streak_text += f"✅ <b>День {day}:</b> x{multiplier:.1f} = {bonus_amount:.0f} токенов\n"
        else:
            streak_text += f"○ <b>День {day}:</b> x{multiplier:.1f} = {bonus_amount:.0f} токенов\n"
    
    if daily_streak > 7:
        multiplier = get_max_multiplier()
        bonus_amount = 5.0 * multiplier
        streak_text += f"\n<b>День {daily_streak}+:</b> x{multiplier:.1f} = {bonus_amount:.0f} токенов\n"
    
    streak_text += (
        f"\n<b>Рекомендации:</b>\n"
        f"• Не пропускайте дни для поддержания серии\n"
        f"• Старайтесь заходить в одно и то же время\n"
        f"• Установите напоминание, если нужно\n\n"
        
        f"<i>Держите серию для максимальных бонусов!</i>"
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        streak_text,
        MainKeyboards.get_back_keyboard("bonus")
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ НАВИГАЦИИ ====================

@router.callback_query(F.data == "back_to_bonus")
async def handle_back_to_bonus(callback: CallbackQuery):
    """Возврат в меню бонусов"""
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
        text="🎁 Бонусы",
        from_user=callback.from_user
    )
    msg.bot = callback.bot
    
    # Показываем меню бонусов
    await show_bonus_menu(msg, user)
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "back_to_bonus_menu")
async def handle_back_to_bonus_menu(callback: CallbackQuery):
    """Возврат в меню бонусов (алиас)"""
    await handle_back_to_bonus(callback)

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main_from_bonus(callback: CallbackQuery):
    """Возврат в главное меню из бонусов"""
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

# ==================== КОМАНДЫ ДЛЯ БОНУСОВ ====================

@router.message(Command("bonus"))
async def handle_bonus_command(message: Message):
    """Обработчик команды /bonus"""
    await handle_bonus(message)

@router.message(Command("daily"))
async def handle_daily_command(message: Message):
    """Обработчик команды /daily - получение ежедневного бонуса"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Проверяем, может ли пользователь получить бонус
    can_claim = db.can_claim_bonus(user_id)
    
    if not can_claim:
        # Получаем информацию о следующем бонусе
        daily_streak = user.get('daily_streak', 0)
        next_bonus_info = calculate_next_bonus(daily_streak)
        
        # Получаем информацию о последнем бонусе
        last_bonus_date = user.get('last_bonus_claim')
        next_claim_date = None
        
        if last_bonus_date:
            try:
                if isinstance(last_bonus_date, str):
                    last_date = datetime.fromisoformat(last_bonus_date.replace('Z', '+00:00')).date()
                else:
                    last_date = last_bonus_date.date()
                
                next_claim_date = last_date + timedelta(days=1)
            except:
                pass
        
        if next_claim_date:
            await message_manager.replace_message(
                message,
                f"⏳ <b>Бонус уже получен сегодня</b>\n\n"
                f"Следующий бонус можно будет получить:\n"
                f"📅 <b>{next_claim_date.strftime('%d.%m.%Y')}</b>\n\n"
                f"<b>Размер следующего бонуса:</b>\n"
                f"💰 {next_bonus_info['amount']:.0f} токенов (x{next_bonus_info['multiplier']:.1f})\n\n"
                f"<i>Не пропустите завтрашний день!</i>",
                MainKeyboards.get_back_to_main_keyboard()
            )
        else:
            await message_manager.replace_message(
                message,
                "⏳ <b>Бонус уже получен сегодня</b>\n\n"
                "<i>Заходите завтра за новым бонусом!</i>",
                MainKeyboards.get_back_to_main_keyboard()
            )
        return
    
    # Пытаемся получить бонус
    claim_result = db.claim_daily_bonus(user_id)
    
    if not claim_result['success']:
        error_message = claim_result.get('error', 'Неизвестная ошибка')
        
        await message_manager.replace_message(
            message,
            f"❌ <b>Ошибка получения бонуса</b>\n\n"
            f"{error_message}\n\n"
            f"<i>Попробуйте позже или обратитесь в поддержку</i>",
            MainKeyboards.get_back_to_main_keyboard()
        )
        return
    
    # Бонус успешно получен
    bonus_amount = claim_result['bonus_amount']
    daily_streak = claim_result['daily_streak']
    new_balance = claim_result['new_balance']
    
    success_text = (
        f"🎉 <b>Ежедневный бонус получен!</b>\n\n"
        
        f"<b>Начислено:</b>\n"
        f"💰 <b>{bonus_amount:.0f} токенов</b>\n\n"
        
        f"<b>Серия дней:</b> {daily_streak} 🔥\n"
        f"<b>Новый баланс:</b> {new_balance:.0f} токенов\n\n"
        
        f"<b>Следующий бонус:</b>\n"
    )
    
    # Рассчитываем следующий бонус
    next_bonus_info = calculate_next_bonus(daily_streak)
    success_text += f"💰 {next_bonus_info['amount']:.0f} токенов (x{next_bonus_info['multiplier']:.1f})\n\n"
    
    success_text += "<i>Не пропускайте завтрашний день для увеличения серии!</i>"
    
    await message_manager.replace_message(
        message,
        success_text,
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("streak"))
async def handle_streak_command(message: Message):
    """Обработчик команды /streak - информация о серии дней"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    daily_streak = user.get('daily_streak', 0)
    last_bonus_date = user.get('last_bonus_claim')
    
    streak_text = (
        f"🔥 <b>Ваша серия дней</b>\n\n"
        
        f"<b>Текущая серия:</b> {daily_streak} дней\n"
    )
    
    if last_bonus_date:
        try:
            if isinstance(last_bonus_date, str):
                last_date = datetime.fromisoformat(last_bonus_date.replace('Z', '+00:00')).date()
            else:
                last_date = last_bonus_date.date()
            
            today = date.today()
            days_since_last = (today - last_date).days
            
            if days_since_last == 0:
                streak_text += f"<b>Последний бонус:</b> сегодня\n"
            elif days_since_last == 1:
                streak_text += f"<b>Последний бонус:</b> вчера\n"
            else:
                streak_text += f"<b>Последний бонус:</b> {days_since_last} дней назад\n"
            
            # Проверяем, не сбросится ли серия
            if days_since_last >= 2:
                streak_text += f"⚠️ <b>Внимание:</b> Серия будет сброшена, если не получить бонус сегодня!\n\n"
            else:
                streak_text += f"✅ <b>Статус:</b> Серия активна\n\n"
        except:
            streak_text += f"<b>Последний бонус:</b> Неизвестно\n\n"
    else:
        streak_text += f"<b>Последний бонус:</b> Никогда\n\n"
    
    # Рассчитываем следующий бонус
    next_bonus_info = calculate_next_bonus(daily_streak)
    
    streak_text += (
        f"<b>Следующий бонус:</b>\n"
        f"💰 {next_bonus_info['amount']:.0f} токенов (x{next_bonus_info['multiplier']:.1f})\n\n"
        
        f"<b>Рекомендации:</b>\n"
        f"• Получайте бонус каждый день\n"
        f"• Старайтесь заходить в одно время\n"
        f"• Не пропускайте дни для максимальных бонусов\n\n"
        
        f"<i>Используйте /daily для получения бонуса</i>"
    )
    
    await message_manager.replace_message(
        message,
        streak_text,
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("bonus_stats_cmd"))
async def handle_bonus_stats_command(message: Message):
    """Обработчик команды /bonus_stats_cmd"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    # Создаем временный callback для отображения статистики
    class TempCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
            self.id = "temp"
            self.data = "bonus_stats"
            self.bot = message.bot
    
    temp_callback = TempCallback(message)
    await handle_bonus_stats(temp_callback)