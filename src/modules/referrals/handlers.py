"""
Обработчики команд реферальной системы с рейтингом
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from .system import referral_system
from src.modules.auth.keyboards import MainKeyboards
from src.modules.finance.token_system import token_system

logger = logging.getLogger(__name__)

router = Router()

def format_progress_bar(percentage: int, length: int = 10) -> str:
    """Создание прогресс-бара"""
    filled = int(length * percentage / 100)
    empty = length - filled
    return "█" * filled + "░" * empty

@router.callback_query(F.data == "menu_referrals")
@router.callback_query(F.data == "back_referrals")
async def callback_referral(callback: CallbackQuery):
    """Показ реферальной системы с рейтингом"""
    
    telegram_id = callback.from_user.id
    
    # Получаем статистику рефералов
    stats = referral_system.get_referral_stats(telegram_id)
    
    # Получаем реферальную ссылку
    referral_link = referral_system.get_referral_link(telegram_id)
    
    # Форматируем токены
    formatted_earned = token_system._format_tokens(stats['total_earned_tokens'])
    
    # Рейтинговая информация
    rank_info = stats['rank_info']
    progress_bar = format_progress_bar(rank_info['progress_percentage'])
    
    # Формируем сообщение
    text = (
        f"👤 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n\n"
        
        f"🏆 <b>Ваш ранг:</b> {rank_info['current_rank']}\n"
        f"📊 <b>Прогресс до следующего ранга:</b>\n"
        f"{progress_bar} {rank_info['progress_percentage']}%\n"
        f"({rank_info['current_count']}/{rank_info['next_count']} рефералов)\n\n"
        
        f"📈 <b>Статистика:</b>\n"
        f"👥 Приглашено рефералов: {stats['referrals_count']}\n"
        f"💰 Заработано на рефералах: {formatted_earned} токенов\n"
        f"✅ Активных рефералов: {stats['active_referrals']}\n"
        f"📊 Конверсия: {stats['conversion_rate']:.1f}%\n\n"
        
        f"⚙️ <b>Ваша реф. ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"🎁 <b>Бонусы:</b>\n"
        f"• Вам: 10 токенов за каждого друга\n"
        f"• Другу: 3 токена при регистрации\n\n"
        
        f"<i>Токены начисляются сразу после регистрации реферала</i>\n"
    )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Поделиться"
    builder.row(
        InlineKeyboardButton(
            text="📤 Поделиться",
            callback_data="referral_share"
        )
    )
    
    # Кнопки статистики
    if stats['referrals_count'] > 0:
        builder.row(
            InlineKeyboardButton(
                text="📋 Мои рефералы",
                callback_data="referral_list"
            ),
            InlineKeyboardButton(
                text="🏆 Мои достижения",
                callback_data="referral_achievements"
            )
        )
    
    # Кнопка таблицы лидеров
    builder.row(
        InlineKeyboardButton(
            text="🏅 Топ приглашателей",
            callback_data="referral_leaderboard"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="back_main"
        )
    )
    
    if callback.message.text != text:
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(F.text == "👥 Рефералы")
@router.message(Command("referral"))
async def cmd_referral(message: Message):
    """Команда реферальной системы из чата"""
    # Создаем fake callback для использования существующего кода
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await callback_referral(fake_callback)

@router.callback_query(F.data == "referral_achievements")
async def callback_referral_achievements(callback: CallbackQuery):
    """Достижения рефералов"""
    
    telegram_id = callback.from_user.id
    
    # Получаем достижения
    achievements = referral_system.get_user_referral_achievements(telegram_id)
    
    if not achievements:
        text = "🏆 <b>ВАШИ ДОСТИЖЕНИЯ РЕФЕРАЛОВ</b>\n\n"
        text += "У вас пока нет достижений в реферальной системе.\n\n"
        text += "🎯 <b>Как получить достижения:</b>\n"
        text += "• Приглашайте друзей по реферальной ссылке\n"
        text += "• За каждого реферала вы получаете бонусы\n"
        text += "• Разблокируйте все достижения!\n"
    else:
        text = "🏆 <b>ВАШИ ДОСТИЖЕНИЯ РЕФЕРАЛОВ</b>\n\n"
        
        for i, ach in enumerate(achievements, 1):
            date = ach['unlocked_at'][:10] if ach['unlocked_at'] else "Недавно"
            
            text += (
                f"{i}. <b>{ach['name']}</b>\n"
                f"   📝 {ach['description']}\n"
                f"   📅 Получено: {date}\n"
                f"   ✅ Прогресс: {ach['progress']}%\n\n"
            )
    
    # Получаем статистику для отображения прогресса
    stats = referral_system.get_referral_stats(telegram_id)
    rank_info = stats['rank_info']
    
    text += (
        f"📊 <b>Текущий прогресс:</b>\n"
        f"• Приглашено: {stats['referrals_count']} рефералов\n"
        f"• Текущий ранг: {rank_info['current_rank']}\n"
        f"• До следующего ранга: {rank_info['needed_for_next']} рефералов\n"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад в реферальную систему",
            callback_data="back_referrals"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "referral_leaderboard")
async def callback_referral_leaderboard(callback: CallbackQuery):
    """Таблица лидеров по рефералам"""
    
    # Получаем топ приглашателей
    leaderboard = referral_system.get_top_referrers_leaderboard(limit=15)
    
    if not leaderboard:
        text = "🏅 <b>ТОП ПРИГЛАШАТЕЛЕЙ</b>\n\n"
        text += "Таблица лидеров пуста.\n"
        text += "Будьте первым, кто пригласит друзей!"
    else:
        text = "🏅 <b>ТОП ПРИГЛАШАТЕЛЕЙ</b>\n\n"
        
        for entry in leaderboard:
            medal = ""
            if entry['rank'] == 1:
                medal = "🥇"
            elif entry['rank'] == 2:
                medal = "🥈"
            elif entry['rank'] == 3:
                medal = "🥉"
            else:
                medal = f"{entry['rank']}."
            
            # Обрезаем длинные никнеймы
            nickname = entry['nickname']
            if len(nickname) > 15:
                nickname = nickname[:12] + "..."
            
            text += (
                f"{medal} <b>{nickname}</b>\n"
                f"   🏆 {entry['rank_title']}\n"
                f"   👥 Рефералов: {entry['referrals_count']}\n"
                f"   💰 Токенов: {entry['balance']:,.0f}\n\n"
            )
    
    # Добавляем статистику текущего пользователя
    telegram_id = callback.from_user.id
    stats = referral_system.get_referral_stats(telegram_id)
    
    user_rank = None
    for i, entry in enumerate(leaderboard, 1):
        if entry['telegram_id'] == telegram_id:
            user_rank = i
            break
    
    if user_rank:
        text += f"\n📊 <b>Ваше место:</b> {user_rank} из {len(leaderboard)}"
    else:
        text += f"\n📊 <b>Ваше место:</b> >{len(leaderboard)} (приглашено {stats['referrals_count']})"
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="referral_leaderboard"
        ),
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_referrals"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "referral_share")
async def callback_referral_share(callback: CallbackQuery):
    """Поделиться реферальной ссылкой"""
    
    telegram_id = callback.from_user.id
    
    # Получаем реферальную ссылку
    referral_link = referral_system.get_referral_link(telegram_id)
    
    # Получаем пользователя для имени
    user = referral_system.db.get_user(telegram_id)
    nickname = user['nickname'] if user and 'nickname' in user.keys() else "друг"
    
    text = (
        f"📤 <b>ПОДЕЛИТЬСЯ РЕФЕРАЛЬНОЙ ССЫЛКОЙ</b>\n\n"
        f"🎯 <b>Ваша ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"📝 <b>Пример сообщения для друга:</b>\n"
        f"Привет! Присоединяйся к GromFit - боту для спортивных дуэлей! "
        f"Соревнуйся с друзьями, отслеживай прогресс и зарабатывай награды! "
        f"Регистрируйся по моей ссылке и получи бонус 3 токена! 🏋️‍♂️\n\n"
        
        f"<code>{referral_link}</code>\n\n"
        
        f"🎁 <b>Что получит ваш друг:</b>\n"
        f"• 3 токена сразу после регистрации\n"
        f"• Доступ ко всем функциям бота\n"
        f"• Возможность участвовать в дуэлях\n\n"
        
        f"💰 <b>Что получите вы:</b>\n"
        f"• 10 токенов за каждого друга\n"
        f"• Повышение ранга в реферальной системе\n"
        f"• Достижения и награды\n"
    )
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔗 Скопировать ссылку",
            callback_data="referral_copy"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_referrals"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "referral_copy")
async def callback_referral_copy(callback: CallbackQuery):
    """Копирование реферальной ссылки"""
    
    telegram_id = callback.from_user.id
    referral_link = referral_system.get_referral_link(telegram_id)
    
    await callback.answer(
        f"Ссылка скопирована в буфер обмена!\n\n{referral_link}",
        show_alert=True
    )

@router.callback_query(F.data == "referral_list")
async def callback_referral_list(callback: CallbackQuery):
    """Список рефералов пользователя"""
    
    telegram_id = callback.from_user.id
    
    # Получаем список рефералов
    stats = referral_system.get_referral_stats(telegram_id)
    referrals_list = stats.get('referrals_list', [])
    
    if not referrals_list:
        text = "📋 <b>МОИ РЕФЕРАЛЫ</b>\n\n"
        text += "У вас пока нет приглашенных друзей.\n\n"
        text += "🎯 <b>Как пригласить друзей:</b>\n"
        text += "1. Поделитесь вашей реферальной ссылкой\n"
        text += "2. Друг переходит по ссылке и регистрируется\n"
        text += "3. Вы получаете 10 токенов, друг получает 3 токена\n"
        text += "4. Друг отображается в этом списке\n"
    else:
        text = f"📋 <b>МОИ РЕФЕРАЛЫ</b> ({len(referrals_list)})\n\n"
        
        for i, referral in enumerate(referrals_list, 1):
            # Обрезаем длинные никнеймы
            nickname = referral.get('nickname', f"Пользователь {referral.get('telegram_id')}")
            if len(nickname) > 15:
                nickname = nickname[:12] + "..."
            
            # Форматируем дату
            reg_date = referral.get('registered_at', 'Неизвестно')
            if reg_date and len(reg_date) > 10:
                reg_date = reg_date[:10]
            
            # Статус реферала
            status_emoji = "✅" if referral.get('is_active', False) else "⏳"
            status_text = "Активен" if referral.get('is_active', False) else "Неактивен"
            
            # Количество дуэлей
            duels_count = referral.get('duels_participated', 0)
            
            # Бонус токенов
            tokens_earned = referral.get('tokens_earned_for_referrer', 0)
            
            text += (
                f"{i}. <b>{nickname}</b>\n"
                f"   📅 Регистрация: {reg_date}\n"
                f"   🏆 Статус: {status_emoji} {status_text}\n"
                f"   ⚔️ Дуэлей: {duels_count}\n"
                f"   💰 Бонус вам: {tokens_earned} токенов\n\n"
            )
    
    # Добавляем статистику
    formatted_earned = token_system._format_tokens(stats['total_earned_tokens'])
    
    text += (
        f"📊 <b>Общая статистика:</b>\n"
        f"• Всего приглашено: {stats['referrals_count']}\n"
        f"• Активных рефералов: {stats['active_referrals']}\n"
        f"• Заработано на рефералах: {formatted_earned} токенов\n"
        f"• Конверсия: {stats['conversion_rate']:.1f}%\n\n"
        
        f"<i>Активным считается реферал, который хотя бы раз участвовал в дуэли</i>"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Если есть рефералы, добавляем кнопки фильтрации
    if referrals_list:
        builder.row(
            InlineKeyboardButton(
                text="✅ Только активные",
                callback_data="referral_list_active"
            ),
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data="referral_list"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад в реферальную систему",
            callback_data="back_referrals"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "referral_list_active")
async def callback_referral_list_active(callback: CallbackQuery):
    """Список только активных рефералов"""
    
    telegram_id = callback.from_user.id
    
    # Получаем список рефералов
    stats = referral_system.get_referral_stats(telegram_id)
    referrals_list = stats.get('referrals_list', [])
    
    # Фильтруем только активных рефералов
    active_referrals = [r for r in referrals_list if r.get('is_active', False)]
    
    if not active_referrals:
        text = "✅ <b>АКТИВНЫЕ РЕФЕРАЛЫ</b>\n\n"
        text += "У вас пока нет активных рефералов.\n\n"
        text += "🎯 <b>Как сделать реферала активным:</b>\n"
        text += "• Приглашенный друг должен зарегистрироваться\n"
        text += "• Он должен принять участие хотя бы в одной дуэли\n"
        text += "• После этого он станет активным рефералом\n"
    else:
        text = f"✅ <b>АКТИВНЫЕ РЕФЕРАЛЫ</b> ({len(active_referrals)} из {len(referrals_list)})\n\n"
        
        for i, referral in enumerate(active_referrals, 1):
            # Обрезаем длинные никнеймы
            nickname = referral.get('nickname', f"Пользователь {referral.get('telegram_id')}")
            if len(nickname) > 15:
                nickname = nickname[:12] + "..."
            
            # Форматируем дату
            reg_date = referral.get('registered_at', 'Неизвестно')
            if reg_date and len(reg_date) > 10:
                reg_date = reg_date[:10]
            
            # Количество дуэлей
            duels_count = referral.get('duels_participated', 0)
            
            # Бонус токенов
            tokens_earned = referral.get('tokens_earned_for_referrer', 0)
            
            text += (
                f"{i}. <b>{nickname}</b>\n"
                f"   📅 Регистрация: {reg_date}\n"
                f"   ⚔️ Дуэлей: {duels_count}\n"
                f"   💰 Бонус вам: {tokens_earned} токенов\n\n"
            )
    
    # Добавляем статистику по активным рефералам
    total_tokens_from_active = sum(r.get('tokens_earned_for_referrer', 0) for r in active_referrals)
    formatted_tokens = token_system._format_tokens(total_tokens_from_active)
    
    text += (
        f"📊 <b>Статистика по активным рефералам:</b>\n"
        f"• Активных рефералов: {len(active_referrals)}\n"
        f"• Заработано от активных: {formatted_tokens} токенов\n"
        f"• Средняя активность: {stats.get('average_duels_per_referral', 0):.1f} дуэлей\n\n"
        
        f"<i>Активным считается реферал, который хотя бы раз участвовал в дуэли</i>"
    )
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Все рефералы",
            callback_data="referral_list"
        ),
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="referral_list_active"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад в реферальную систему",
            callback_data="back_referrals"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )