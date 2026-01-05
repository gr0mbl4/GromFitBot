"""
Обработчики профиля и кнопок под чатом
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.core.database import db
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем статистику пользователя
    referrals_count = user.get('referrals_count', 0)
    tokens = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0
    
    # Определяем уровень активности
    duels_count = user.get('duels_count', 0)
    achievements_count = user.get('achievements_count', 0)
    total_achievements = user.get('total_achievements', 200)
    
    # Определяем реферальный ранг
    if referrals_count >= 100:
        ref_rank = "🎖️ Легенда"
    elif referrals_count >= 50:
        ref_rank = "👑 Король"
    elif referrals_count >= 25:
        ref_rank = "⭐ Мастер"
    elif referrals_count >= 10:
        ref_rank = "🔥 Лидер"
    elif referrals_count >= 5:
        ref_rank = "🤝 Активный"
    elif referrals_count >= 1:
        ref_rank = "👋 Начинающий"
    else:
        ref_rank = "😊 Новичок"
    
    text = (
        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"🎭 <b>Никнейм:</b> {user['nickname']}\n"
        f"📍 <b>Регион:</b> {user['region'] if user['region'] != 'no region' else 'не указан'}\n"
        f"🆔 <b>ID:</b> {user['registration_number']}\n"
        f"📅 <b>Регистрация:</b> {user['created_at'][:10] if user['created_at'] else 'Неизвестно'}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• 💰 Баланс: {tokens:.0f} токенов\n"
        f"• 👥 Приглашено друзей: {referrals_count}\n"
        f"• 🏆 Реферальный ранг: {ref_rank}\n"
        f"• ⚔️ Проведено дуэлей: {duels_count}\n"
        f"• 🎯 Достижений: {achievements_count}/{total_achievements}\n\n"
        f"📈 <b>Последняя активность:</b> {user['last_active'][:19] if user['last_active'] else 'Недавно'}\n\n"
        f"<i>Используйте меню для навигации</i>"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )

@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    """Обработчик кнопки профиля"""
    await cmd_profile(callback.message)
    await callback.answer()

@router.message(F.text == "🏋️‍♂️ ПРОФИЛЬ")
async def handle_profile_button(message: Message):
    """Обработчик кнопки профиля в главном меню"""
    await cmd_profile(message)

@router.message(F.text == "👤 Личный кабинет")
async def cmd_personal_account(message: Message):
    """Обработчик кнопки 'Личный кабинет' под чатом"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем статистику пользователя
    referrals_count = user.get('referrals_count', 0)
    tokens = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0
    
    # Получаем информацию о рефералах
    cursor = db.execute('''
        SELECT COUNT(*) as active_refs
        FROM referral_connections 
        WHERE referrer_id = ? AND bonus_paid = 1
    ''', (telegram_id,))
    result = cursor.fetchone()
    active_referrals = result['active_refs'] if result else 0
    
    # Считаем конверсию
    conversion_rate = (active_referrals / referrals_count * 100) if referrals_count > 0 else 0
    
    # Получаем общий заработок с рефералов
    cursor = db.execute('''
        SELECT SUM(referrer_bonus_paid) as total_earned
        FROM referral_connections 
        WHERE referrer_id = ? AND bonus_paid = 1
    ''', (telegram_id,))
    result = cursor.fetchone()
    total_referral_earnings = result['total_earned'] if result and result['total_earned'] else 0
    
    # Определяем статус активности
    last_active = user.get('last_active', '')
    if last_active:
        from datetime import datetime
        try:
            last_active_dt = datetime.strptime(last_active[:19], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            days_since_active = (now - last_active_dt).days
            
            if days_since_active == 0:
                activity_status = "✅ Сегодня активен"
            elif days_since_active == 1:
                activity_status = "🟡 Вчера активен"
            elif days_since_active <= 7:
                activity_status = f"🟡 Активен {days_since_active} дней назад"
            else:
                activity_status = f"⭕ Неактивен {days_since_active} дней"
        except:
            activity_status = "❓ Неизвестно"
    else:
        activity_status = "❓ Неизвестно"
    
    # Проверяем наличие ежедневного бонуса
    try:
        from src.modules.bonus.handlers import DailyBonusSystem
        can_claim_bonus = DailyBonusSystem.can_claim_bonus(user.get('last_bonus_claim'))
        bonus_status = "🎁 Бонус доступен" if can_claim_bonus else "⏳ Бонус получен"
    except:
        bonus_status = "🎁 Бонус доступен"
    
    text = (
        f"👤 <b>ЛИЧНЫЙ КАБИНЕТ</b>\n\n"
        f"🎭 <b>Никнейм:</b> {user['nickname']}\n"
        f"📍 <b>Регион:</b> {user['region'] if user['region'] != 'no region' else 'не указан'}\n"
        f"🆔 <b>ID:</b> {user['registration_number']}\n"
        f"📅 <b>Регистрация:</b> {user['created_at'][:10] if user['created_at'] else 'Неизвестно'}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• 💰 Баланс токенов: {tokens:.0f}\n"
        f"• 🎁 Ежедневный бонус: {bonus_status}\n"
        f"• 👥 Приглашено друзей: {referrals_count}\n"
        f"• ✅ Активных рефералов: {active_referrals}\n"
        f"• 📈 Конверсия: {conversion_rate:.1f}%\n"
        f"• 💵 Заработано на рефералах: {total_referral_earnings:.0f} токенов\n"
        f"• ⚔️ Дуэлей проведено: {user.get('duels_count', 0)}\n"
        f"• 🎯 Достижений: {user.get('achievements_count', 0)}\n\n"
        f"📱 <b>Статус:</b> {activity_status}\n\n"
        f"<i>Используйте меню для навигации</i>"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )

@router.message(F.text == "📝 Записать результат")
async def cmd_record_result(message: Message):
    """Обработчик кнопки 'Записать результат' под чатом"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    text = (
        "📝 <b>ЗАПИСАТЬ РЕЗУЛЬТАТ ТРЕНИРОВКИ</b>\n\n"
        "Этот функционал находится в разработке.\n\n"
        "Скоро вы сможете:\n"
        "• 📊 Записывать свои тренировки\n"
        "• 🏋️‍♂️ Отслеживать прогресс по упражнениям\n"
        "• 📈 Анализировать результаты\n"
        "• 🎯 Ставить цели и достигать их\n\n"
        "Оставайтесь на связи! Функционал появится в ближайшем обновлении."
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )

@router.message(F.text == "🛒 Магазин")
async def cmd_shop(message: Message):
    """Обработчик кнопки 'Магазин' под чатом"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем баланс пользователя
    tokens = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0
    
    text = (
        "🛒 <b>МАГАЗИН GROMFIT</b>\n\n"
        "🏆 <b>ТОВАРЫ И УСЛУГИ:</b>\n\n"
        "1. <b>НОВИЧКАМ</b>\n"
        "   • 3 дня безлимитных голосовых + 1 анализ\n"
        "   • Цена: <b>50 токенов</b> (специальное предложение!)\n\n"
        "2. <b>ПРЕМИУМ СТАТУС</b>\n"
        "   • Доступ на 1 месяц\n"
        "   • Эксклюзивные возможности\n"
        "   • Цена: 100 токенов\n\n"
        "3. <b>ДОПОЛНИТЕЛЬНЫЕ ГОЛОСА</b>\n"
        "   • Пакет из 5 голосов для дуэлей\n"
        "   • Цена: 10 токенов\n\n"
        "4. <b>ЭКСКЛЮЗИВНЫЕ ДОСТИЖЕНИЯ</b>\n"
        "   • Уникальные ачивки для профиля\n"
        "   • Цена: 50 токенов\n\n"
        "5. <b>УСКОРЕНИЕ ВОССТАНОВЛЕНИЯ</b>\n"
        "   • Быстрое восстановление после тренировок\n"
        "   • Цена: 25 токенов\n\n"
        f"💳 <b>ВАШ БАЛАНС:</b> {tokens:.0f} токенов\n\n"
        "<i>Функционал магазина будет доступен в ближайшем обновлении!\n"
        "Следите за анонсами в боте.</i>"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_bottom_keyboard()
    )

@router.message(F.text == "🏠 Главное меню")
async def cmd_main_menu(message: Message):
    """Обработчик кнопки 'Главное меню' под чатом"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем баланс для приветствия
    tokens = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0
    
    text = (
        f"🏠 <b>ГЛАВНОЕ МЕНЮ GROMFIT</b>\n\n"
        f"👋 Привет, {user['nickname']}!\n"
        f"💰 Ваш баланс: {tokens:.0f} токенов\n\n"
        f"👇 <b>ВЫБЕРИТЕ РАЗДЕЛ:</b>"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_main_menu()
    )

@router.message(F.text == "⚔️ ДУЭЛИ")
async def handle_duels_button(message: Message):
    """Обработчик кнопки дуэлей в главном меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "⚔️ <b>СИСТЕМА ДУЭЛЕЙ</b>\n\n"
        "Этот функционал находится в разработке.\n\n"
        "Скоро вы сможете:\n"
        "• 🎯 Бросать вызовы друзьям\n"
        "• 🏆 Участвовать в спортивных соревнованиях\n"
        "• 💰 Делать ставки токенами\n"
        "• 📊 Отслеживать результаты дуэлей\n\n"
        "Следите за обновлениями!",
        reply_markup=MainKeyboards.get_main_menu()
    )

@router.message(F.text == "📊 ТРЕНИРОВКИ")
async def handle_workouts_button(message: Message):
    """Обработчик кнопки тренировок в главном меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "📊 <b>ТРЕНИРОВКИ И ПРОГРЕСС</b>\n\n"
        "Этот функционал находится в разработке.\n\n"
        "Скоро вы сможете:\n"
        "• 🏋️‍♂️ Планировать тренировки\n"
        "• 📈 Отслеживать прогресс\n"
        "• 🎯 Ставить спортивные цели\n"
        "• 📊 Анализировать результаты\n\n"
        "Функционал появится в ближайшем обновлении.",
        reply_markup=MainKeyboards.get_main_menu()
    )

@router.message(F.text == "🎯 ДОСТИЖЕНИЯ")
async def handle_achievements_button(message: Message):
    """Обработчик кнопки достижений в главном меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем достижения пользователя
    achievements_count = user.get('achievements_count', 0)
    
    text = (
        f"🎯 <b>СИСТЕМА ДОСТИЖЕНИЙ</b>\n\n"
        f"У вас разблокировано: {achievements_count} достижений\n\n"
        "🏆 <b>Категории достижений:</b>\n"
        "• 🏋️‍♂️ Тренировочные\n"
        "• ⚔️ Дуэльные\n"
        "• 👥 Социальные\n"
        "• 💰 Финансовые\n"
        "• ⭐ Эксклюзивные\n\n"
        "Этот функционал находится в разработке.\n"
        "Следите за обновлениями!"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_main_menu()
    )

@router.message(F.text == "💰 МАГАЗИН")
async def handle_shop_main_button(message: Message):
    """Обработчик кнопки магазина в главном меню"""
    await cmd_shop(message)

@router.message(F.text == "👥 РЕФЕРАЛЫ")
async def handle_referrals_button(message: Message):
    """Обработчик кнопки рефералов в главном меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    from src.modules.referrals.system import referral_system
    
    # Получаем статистику рефералов
    stats = referral_system.get_referral_stats(telegram_id)
    referrals_count = stats.get('referrals_count', 0)
    total_earned = stats.get('total_earned_tokens', 0)
    active_refs = stats.get('active_referrals', 0)
    conversion_rate = stats.get('conversion_rate', 0)
    rank_info = stats.get('rank_info', {})
    
    # Получаем реферальную ссылку
    ref_link = referral_system.get_referral_link(telegram_id)
    
    text = (
        f"👥 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n\n"
        f"📊 <b>СТАТИСТИКА:</b>\n"
        f"• Всего приглашено: {referrals_count}\n"
        f"• Активных рефералов: {active_refs}\n"
        f"• Конверсия: {conversion_rate:.1f}%\n"
        f"• Заработано: {total_earned:.0f} токенов\n\n"
        f"🏆 <b>ТЕКУЩИЙ РАНГ:</b> {rank_info.get('current_rank', 'Новичок')}\n"
        f"📈 <b>ПРОГРЕСС:</b> {rank_info.get('progress_percentage', 0)}%\n"
        f"🎯 <b>ДО СЛЕДУЮЩЕГО РАНГА:</b> {rank_info.get('needed_for_next', 0)} рефералов\n\n"
        f"🔗 <b>ВАША РЕФЕРАЛЬНАЯ ССЫЛКА:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"👥 <b>Поделитесь ссылкой с друзьями!</b>\n"
        f"За каждого приглашенного друга вы получаете 25 токенов, а друг получает 50 токенов!"
    )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_main_menu()
    )

@router.message(F.text == "🎁 ЕЖЕДНЕВНЫЙ БОНУС")
async def handle_daily_bonus_main_button(message: Message):
    """Обработчик кнопки ежедневного бонуса в главном меню"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    from src.modules.bonus.handlers import DailyBonusSystem
    
    last_claim_time = user.get('last_bonus_claim')
    
    if DailyBonusSystem.can_claim_bonus(last_claim_time):
        text = (
            "🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"
            "💰 <b>Бонус доступен!</b>\n"
            "Получите 10 токенов за сегодняшний бонус.\n\n"
            "⏰ <b>Время сброса:</b> 03:00 по МСК\n\n"
            "👇 <b>Используйте команду /bonus для получения</b>"
        )
    else:
        time_until = DailyBonusSystem.get_time_until_next_bonus(last_claim_time)
        text = (
            "🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"
            "⏳ <b>Бонус уже получен сегодня</b>\n\n"
            "⏰ <b>Следующий бонус будет доступен через:</b>\n"
            f"{time_until} (в 03:00 по МСК)\n\n"
            "💰 <b>Размер бонуса:</b> 10 токенов ежедневно"
        )
    
    await message.answer(
        text,
        reply_markup=MainKeyboards.get_main_menu()
    )