"""
Полный модуль обработчиков профиля пользователя GromFitBot
Обрабатывает все команды и действия связанные с профилем
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

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

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ ПРОФИЛЯ ====================

@router.message(F.text == "👤 Профиль")
async def handle_profile(message: Message):
    """Основной обработчик кнопки 'Профиль'"""
    user_id = message.from_user.id
    logger.info(f"Запрос профиля от пользователя {user_id}")
    
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации в боте."
        )
        return
    
    await show_profile(message, user)

async def show_profile(message: Message, user: Dict[str, Any]):
    """Отображение профиля пользователя"""
    user_id = user['telegram_id']
    
    # Форматируем дату регистрации
    created_at = user.get('created_at')
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            reg_date = created_at.strftime("%d.%m.%Y %H:%M")
        except:
            reg_date = "Неизвестно"
    else:
        reg_date = "Неизвестно"
    
    # Получаем дополнительные данные
    referrals_count = user.get('referrals_count', 0)
    achievements_count = user.get('achievements_count', 0)
    
    # Получаем тренировки за последние 7 дней
    trainings_stats = db.get_training_stats(user_id, days=7)
    
    # Получаем реферера
    referrer = db.get_referrer(user_id)
    referrer_info = "Не указан"
    if referrer:
        referrer_info = f"{referrer['nickname']} (ID: {referrer['registration_number']})"
    
    # Формируем текст профиля
    profile_text = (
        f"👤 <b>Профиль пользователя</b>\n\n"
        
        f"<b>Основная информация:</b>\n"
        f"🆔 <b>ID:</b> {user['registration_number']}\n"
        f"👤 <b>Никнейм:</b> {user['nickname']}\n"
        f"📍 <b>Регион:</b> {user.get('region', 'Не указан')}\n"
        f"📅 <b>Дата регистрации:</b> {reg_date}\n\n"
        
        f"<b>Экономика:</b>\n"
        f"💰 <b>Токены:</b> {user.get('balance_tokens', 0):.0f}\n"
        f"💎 <b>Алмазы:</b> {user.get('balance_diamonds', 0):.0f}\n"
        f"🤝 <b>Реферер:</b> {referrer_info}\n\n"
        
        f"<b>Статистика:</b>\n"
        f"🏋️ <b>Тренировки:</b> {user.get('total_trainings', 0)} (за 7 дней: {trainings_stats['recent_trainings']})\n"
        f"🤼 <b>Дуэли:</b> {user.get('total_duels', 0)} / Побед: {user.get('duels_won', 0)}\n"
        f"🎯 <b>Достижения:</b> {achievements_count}\n"
        f"📈 <b>Очки:</b> {user.get('total_points', 0)}\n\n"
        
        f"<b>Прогресс:</b>\n"
        f"⭐️ <b>Уровень:</b> {user.get('level', 1)}\n"
        f"📊 <b>Опыт:</b> {user.get('experience', 0)}/1000\n"
        f"🔥 <b>Серия дней:</b> {user.get('daily_streak', 0)}\n\n"
        
        f"<i>Используйте кнопки ниже для управления профилем</i>"
    )
    
    await message_manager.replace_message(
        message,
        profile_text,
        MainKeyboards.get_profile_keyboard()
    )

@router.callback_query(F.data == "profile_stats")
async def handle_profile_stats(callback: CallbackQuery):
    """Обработчик кнопки 'Статистика' в профиле"""
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
    trainings_stats = db.get_training_stats(user_id, days=30)
    transaction_stats = db.get_transaction_summary(user_id, days=30)
    referrals_count = db.get_referral_count(user_id)
    achievements = db.get_user_achievements(user_id)
    
    # Вычисляем процент побед в дуэлях
    total_duels = user.get('total_duels', 0)
    duels_won = user.get('duels_won', 0)
    win_rate = (duels_won / total_duels * 100) if total_duels > 0 else 0
    
    # Получаем последнюю тренировку
    trainings = db.get_user_trainings(user_id, limit=1)
    last_training = trainings[0] if trainings else None
    
    stats_text = (
        f"📊 <b>Расширенная статистика</b>\n\n"
        
        f"<b>🏋️ Тренировки (за 30 дней):</b>\n"
        f"• Количество: {trainings_stats['recent_trainings']}\n"
        f"• Всего минут: {trainings_stats['total_minutes']}\n"
        f"• Сожжено калорий: {trainings_stats['total_calories']}\n"
        f"• Любимый тип: {trainings_stats['favorite_type']}\n\n"
        
        f"<b>🤼 Дуэли:</b>\n"
        f"• Всего: {total_duels}\n"
        f"• Побед: {duels_won}\n"
        f"• Процент побед: {win_rate:.1f}%\n\n"
        
        f"<b>💰 Финансы (за 30 дней):</b>\n"
        f"• Пополнений: {transaction_stats['total_income']:.0f} токенов\n"
        f"• Расходов: {abs(transaction_stats['total_expense']):.0f} токенов\n"
        f"• Транзакций: {transaction_stats['transaction_count']}\n\n"
        
        f"<b>🤝 Социальное:</b>\n"
        f"• Приглашено друзей: {referrals_count}\n"
        f"• Достижений: {len(achievements)}/200\n\n"
        
        f"<b>📈 Активность:</b>\n"
        f"• Уровень: {user.get('level', 1)}\n"
        f"• Опыт: {user.get('experience', 0)}/1000\n"
        f"• Серия дней: {user.get('daily_streak', 0)}\n"
        f"• Всего очков: {user.get('total_points', 0)}\n\n"
        
        f"<b>⏰ Последняя активность:</b>\n"
    )
    
    if last_training:
        training_date = datetime.fromisoformat(last_training['training_date'].replace('Z', '+00:00'))
        stats_text += f"• Тренировка: {training_date.strftime('%d.%m.%Y %H:%M')}\n"
    else:
        stats_text += "• Тренировок еще не было\n"
    
    last_active = user.get('last_active')
    if last_active:
        last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
        stats_text += f"• Вход в бота: {last_active_date.strftime('%d.%m.%Y %H:%M')}\n"
    
    await message_manager.edit_message_with_menu(
        callback,
        stats_text,
        MainKeyboards.get_back_keyboard("profile")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "profile_achievements")
async def handle_profile_achievements(callback: CallbackQuery):
    """Обработчик кнопки 'Достижения' в профиле"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    achievements = db.get_user_achievements(user_id)
    
    if not achievements:
        await message_manager.edit_message_with_menu(
            callback,
            "🎯 <b>Ваши достижения</b>\n\n"
            "У вас пока нет достижений.\n\n"
            "<i>Выполняйте задания, тренируйтесь и участвуйте в дуэлях, чтобы получать достижения!</i>",
            MainKeyboards.get_back_keyboard("profile")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    # Группируем достижения по категориям
    categories = {}
    for achievement in achievements:
        category = achievement.get('category', 'general')
        if category not in categories:
            categories[category] = []
        categories[category].append(achievement)
    
    # Формируем текст
    achievements_text = "🎯 <b>Ваши достижения</b>\n\n"
    
    for category, category_achievements in categories.items():
        achievements_text += f"<b>{category.capitalize()}:</b> {len(category_achievements)}\n"
    
    achievements_text += f"\n<b>Всего достижений:</b> {len(achievements)}/200\n\n"
    
    # Показываем последние 5 достижений
    recent_achievements = sorted(achievements, key=lambda x: x.get('unlocked_at', ''), reverse=True)[:5]
    
    achievements_text += "<b>Последние достижения:</b>\n"
    for achievement in recent_achievements:
        icon = achievement.get('icon', '🏆')
        title = achievement.get('title', 'Без названия')
        unlocked_at = achievement.get('unlocked_at', '')
        
        if unlocked_at:
            try:
                unlocked_date = datetime.fromisoformat(unlocked_at.replace('Z', '+00:00'))
                date_str = unlocked_date.strftime("%d.%m.%Y")
            except:
                date_str = "Неизвестно"
        else:
            date_str = "Неизвестно"
        
        achievements_text += f"{icon} <b>{title}</b> ({date_str})\n"
    
    achievements_text += "\n<i>Продолжайте в том же духе!</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        achievements_text,
        MainKeyboards.get_back_keyboard("profile")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "profile_balance")
async def handle_profile_balance(callback: CallbackQuery):
    """Обработчик кнопки 'Баланс' в профиле"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем последние транзакции
    transactions = db.get_user_transactions(user_id, limit=10)
    
    balance_text = (
        f"💳 <b>Ваш баланс</b>\n\n"
        
        f"<b>Текущие средства:</b>\n"
        f"💰 <b>Токены:</b> {user.get('balance_tokens', 0):.2f}\n"
        f"💎 <b>Алмазы:</b> {user.get('balance_diamonds', 0):.2f}\n\n"
        
        f"<b>Способы пополнения:</b>\n"
        f"1. Ежедневные бонусы\n"
        f"2. Приглашение друзей\n"
        f"3. Победы в дуэлях\n"
        f"4. Достижения\n"
        f"5. Покупки в магазине\n\n"
        
        f"<b>История транзакций (последние 10):</b>\n"
    )
    
    if not transactions:
        balance_text += "Транзакций пока нет\n"
    else:
        for i, transaction in enumerate(transactions, 1):
            amount = transaction['amount']
            description = transaction['description'] or "Без описания"
            created_at = transaction['created_at']
            
            if isinstance(created_at, str):
                try:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = created_date.strftime("%d.%m %H:%M")
                except:
                    date_str = "Неизвестно"
            else:
                date_str = "Неизвестно"
            
            amount_str = f"+{amount:.2f}" if amount > 0 else f"{amount:.2f}"
            balance_text += f"{i}. {date_str}: {amount_str} - {description}\n"
    
    balance_text += "\n<i>Баланс обновляется в реальном времени</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        balance_text,
        MainKeyboards.get_back_keyboard("profile")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "profile_settings")
async def handle_profile_settings(callback: CallbackQuery):
    """Обработчик кнопки 'Настройки' в профиле"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Получаем текущие настройки
    settings = user.get('settings', '{}')
    try:
        settings_dict = json.loads(settings)
    except:
        settings_dict = {}
    
    notifications_enabled = user.get('notifications_enabled', 1)
    language = user.get('language', 'ru')
    theme = user.get('theme', 'light')
    
    settings_text = (
        f"⚙️ <b>Настройки профиля</b>\n\n"
        
        f"<b>Текущие настройки:</b>\n"
        f"🔔 Уведомления: {'Включены ✅' if notifications_enabled else 'Выключены ❌'}\n"
        f"🌐 Язык: {language.upper()}\n"
        f"🎨 Тема: {'Светлая 🌞' if theme == 'light' else 'Темная 🌙'}\n\n"
        
        f"<b>Дополнительные настройки:</b>\n"
        f"• Конфиденциальность\n"
        f"• Синхронизация данных\n"
        f"• Экспорт данных\n"
        f"• Очистка истории\n\n"
        
        f"<i>Используйте кнопки ниже для изменения настроек</i>"
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        settings_text,
        MainKeyboards.get_settings_keyboard()
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "profile_trainings")
async def handle_profile_trainings(callback: CallbackQuery):
    """Обработчик кнопки 'Тренировки' в профиле"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    trainings = db.get_user_trainings(user_id, limit=5)
    
    trainings_text = (
        f"📈 <b>История тренировок</b>\n\n"
        
        f"<b>Общая статистика:</b>\n"
        f"• Всего тренировок: {user.get('total_trainings', 0)}\n"
        f"• Всего очков: {user.get('total_points', 0)}\n"
        f"• Последняя тренировка: "
    )
    
    last_training_date = user.get('last_training_date')
    if last_training_date:
        try:
            last_date = datetime.fromisoformat(last_training_date.replace('Z', '+00:00'))
            trainings_text += f"{last_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        except:
            trainings_text += "Неизвестно\n\n"
    else:
        trainings_text += "Еще не было\n\n"
    
    if not trainings:
        trainings_text += "<b>Последние тренировки:</b>\n"
        trainings_text += "Тренировок еще не было\n"
    else:
        trainings_text += f"<b>Последние {len(trainings)} тренировок:</b>\n"
        
        for i, training in enumerate(trainings, 1):
            training_type = training.get('training_type', 'Неизвестно')
            duration = training.get('duration_minutes', 0)
            calories = training.get('calories_burned', 0)
            training_date = training.get('training_date', '')
            
            if training_date:
                try:
                    date_obj = datetime.fromisoformat(training_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%d.%m %H:%M")
                except:
                    date_str = "Неизвестно"
            else:
                date_str = "Неизвестно"
            
            calories_str = f", {calories} ккал" if calories else ""
            trainings_text += f"{i}. {date_str}: {training_type} ({duration} мин{calories_str})\n"
    
    trainings_text += "\n<i>Регулярные тренировки - залог успеха!</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        trainings_text,
        MainKeyboards.get_back_keyboard("profile")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "profile_duels")
async def handle_profile_duels(callback: CallbackQuery):
    """Обработчик кнопки 'Дуэли' в профиле"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    duels = db.get_user_duels(user_id)
    
    # Фильтруем завершенные дуэли
    completed_duels = [duel for duel in duels if duel.get('status') == 'completed']
    active_duels = [duel for duel in duels if duel.get('status') == 'active']
    pending_duels = [duel for duel in duels if duel.get('status') == 'pending']
    
    # Сортируем завершенные дуэли по дате окончания
    completed_duels.sort(key=lambda x: x.get('ended_at', ''), reverse=True)
    
    duels_text = (
        f"🤼 <b>История дуэлей</b>\n\n"
        
        f"<b>Общая статистика:</b>\n"
        f"• Всего дуэлей: {user.get('total_duels', 0)}\n"
        f"• Побед: {user.get('duels_won', 0)}\n"
        f"• Поражений: {user.get('total_duels', 0) - user.get('duels_won', 0)}\n"
        f"• Процент побед: {((user.get('duels_won', 0) / user.get('total_duels', 0)) * 100) if user.get('total_duels', 0) > 0 else 0:.1f}%\n\n"
    )
    
    # Активные и ожидающие дуэли
    duels_text += f"<b>Активные дуэли:</b> {len(active_duels)}\n"
    duels_text += f"<b>Ожидающие ответа:</b> {len(pending_duels)}\n\n"
    
    # Последние завершенные дуэли
    duels_text += f"<b>Последние завершенные дуэли (до 5):</b>\n"
    
    if not completed_duels:
        duels_text += "Завершенных дуэлей еще не было\n"
    else:
        for i, duel in enumerate(completed_duels[:5], 1):
            exercise_type = duel.get('exercise_type', 'Неизвестно')
            winner_id = duel.get('winner_id')
            ended_at = duel.get('ended_at', '')
            
            # Определяем результат для текущего пользователя
            if winner_id == user_id:
                result = "🏆 Победа"
            else:
                result = "💔 Поражение"
            
            if ended_at:
                try:
                    end_date = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
                    date_str = end_date.strftime("%d.%m %H:%M")
                except:
                    date_str = "Неизвестно"
            else:
                date_str = "Неизвестно"
            
            duels_text += f"{i}. {date_str}: {exercise_type} - {result}\n"
    
    duels_text += "\n<i>Бросайте вызовы и побеждайте!</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        duels_text,
        MainKeyboards.get_back_keyboard("profile")
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ НАСТРОЕК ====================

@router.callback_query(F.data == "settings_notifications")
async def handle_settings_notifications(callback: CallbackQuery):
    """Обработчик настройки уведомлений"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    current_status = user.get('notifications_enabled', 1)
    new_status = 0 if current_status else 1
    
    # Обновляем настройку
    db.update_user_field(user_id, 'notifications_enabled', new_status)
    
    status_text = "включены ✅" if new_status else "выключены ❌"
    
    await message_manager.edit_message_with_menu(
        callback,
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"Уведомления теперь <b>{status_text}</b>\n\n"
        f"<i>Изменения сохранены</i>",
        MainKeyboards.get_back_keyboard("settings")
    )
    
    await message_manager.answer_callback_with_notification(
        callback,
        f"Уведомления {status_text}",
        show_alert=False
    )

@router.callback_query(F.data == "settings_theme")
async def handle_settings_theme(callback: CallbackQuery):
    """Обработчик смены темы"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    current_theme = user.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    # Обновляем тему
    db.update_user_field(user_id, 'theme', new_theme)
    
    theme_text = "светлая 🌞" if new_theme == 'light' else "темная 🌙"
    
    await message_manager.edit_message_with_menu(
        callback,
        f"🎨 <b>Настройки темы</b>\n\n"
        f"Тема изменена на <b>{theme_text}</b>\n\n"
        f"<i>Изменения вступят в силу при следующем обновлении интерфейса</i>",
        MainKeyboards.get_back_keyboard("settings")
    )
    
    await message_manager.answer_callback_with_notification(
        callback,
        f"Тема изменена на {theme_text}",
        show_alert=False
    )

@router.callback_query(F.data == "settings_language")
async def handle_settings_language(callback: CallbackQuery):
    """Обработчик смены языка"""
    await message_manager.edit_message_with_menu(
        callback,
        "🌐 <b>Настройки языка</b>\n\n"
        "В настоящее время доступен только русский язык (RU).\n\n"
        "<i>Поддержка других языков появится в будущих обновлениях</i>",
        MainKeyboards.get_back_keyboard("settings")
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "settings_about")
async def handle_settings_about(callback: CallbackQuery):
    """Обработчик информации о боте"""
    about_text = (
        "ℹ️ <b>О боте GromFit</b>\n\n"
        
        "<b>Версия:</b> 4.1\n"
        "<b>Статус:</b> Рабочая версия\n"
        "<b>Дата обновления:</b> 2026-01-07\n\n"
        
        "<b>Описание:</b>\n"
        "GromFit Bot - это инновационная система спортивных дуэлей на токенах. "
        "Бот помогает спортсменам соревноваться, отслеживать прогресс и мотивировать друг друга.\n\n"
        
        "<b>Основные функции:</b>\n"
        "• Система регистрации с валидацией\n"
        "• Реферальная система с рангами\n"
        "• Профили пользователей с полной статистикой\n"
        "• Система достижений (200+ достижений)\n"
        "• Экономическая система с токенами\n"
        "• Магазин с покупками\n"
        "• Ежедневные бонусы\n\n"
        
        "<b>Разработчик:</b> Команда GromFit\n"
        "<b>Поддержка:</b> @GromFitSupport\n\n"
        
        "<i>Бот находится в активной разработке</i>"
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        about_text,
        MainKeyboards.get_back_keyboard("settings")
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ НАВИГАЦИИ ====================

@router.callback_query(F.data == "back_to_profile")
async def handle_back_to_profile(callback: CallbackQuery):
    """Возврат в профиль"""
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
        text="👤 Профиль",
        from_user=callback.from_user
    )
    msg.bot = callback.bot
    
    # Показываем профиль
    await show_profile(msg, user)
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "back_to_profile_menu")
async def handle_back_to_profile_menu(callback: CallbackQuery):
    """Возврат в меню профиля"""
    await handle_back_to_profile(callback)

@router.callback_query(F.data == "back_to_settings")
async def handle_back_to_settings(callback: CallbackQuery):
    """Возврат в настройки"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    await message_manager.edit_message_with_menu(
        callback,
        "⚙️ <b>Настройки профиля</b>\n\n"
        "Выберите настройку для изменения:",
        MainKeyboards.get_settings_keyboard()
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main_from_profile(callback: CallbackQuery):
    """Возврат в главное меню из профиля"""
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

# ==================== КОМАНДЫ ДЛЯ ПРОФИЛЯ ====================

@router.message(Command("profile"))
async def handle_profile_command(message: Message):
    """Обработчик команды /profile"""
    await handle_profile(message)

@router.message(Command("stats"))
async def handle_stats_command(message: Message):
    """Обработчик команды /stats"""
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
            self.data = "profile_stats"
            self.bot = message.bot
    
    temp_callback = TempCallback(message)
    await handle_profile_stats(temp_callback)

@router.message(Command("balance"))
async def handle_balance_command(message: Message):
    """Обработчик команды /balance"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    await message_manager.replace_message(
        message,
        f"💰 <b>Ваш баланс</b>\n\n"
        f"• Токены: <b>{user.get('balance_tokens', 0):.2f}</b>\n"
        f"• Алмазы: <b>{user.get('balance_diamonds', 0):.2f}</b>\n\n"
        f"<i>Для просмотра истории транзакций используйте профиль</i>",
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("settings"))
async def handle_settings_command(message: Message):
    """Обработчик команды /settings"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    await message_manager.replace_message(
        message,
        "⚙️ <b>Настройки профиля</b>\n\n"
        "Выберите настройку для изменения:",
        MainKeyboards.get_settings_keyboard()
    )

# ==================== УТИЛИТЫ ДЛЯ ПРОФИЛЯ ====================

def format_date(date_str: str) -> str:
    """Форматирование даты для отображения"""
    if not date_str:
        return "Неизвестно"
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = date_str
        
        return date_obj.strftime("%d.%m.%Y %H:%M")
    except:
        return "Неизвестно"

def calculate_level(experience: int) -> Tuple[int, int, int]:
    """Расчет уровня на основе опыта"""
    base_exp = 1000
    level = (experience // base_exp) + 1
    current_exp = experience % base_exp
    next_level_exp = base_exp - current_exp
    
    return level, current_exp, next_level_exp

def get_achievement_progress(user_id: int) -> Dict[str, Any]:
    """Получение прогресса по достижениям"""
    achievements = db.get_user_achievements(user_id)
    
    if not achievements:
        return {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'progress_percentage': 0
        }
    
    total = len(achievements)
    completed = sum(1 for a in achievements if a.get('progress', 0) >= 100)
    in_progress = total - completed
    
    return {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'progress_percentage': (completed / 200) * 100 if total > 0 else 0
    }