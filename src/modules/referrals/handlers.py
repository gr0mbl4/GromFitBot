"""
Обработчики реферальной системы
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.database import Database
from src.core.config import Config, REFERRAL_RANKS
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "👥 Рефералы")
@router.message(Command("referrals"))
async def handle_referrals(message: Message):
    """Обработчик реферальной системы"""
    
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы.\n"
            "Используйте /start для регистрации"
        )
        return
    
    # Получаем статистику рефералов
    referrals_count = db.get_referrals_count(user_id)
    
    # Определяем текущий ранг
    current_rank = "Новичок"
    next_rank = None
    next_rank_count = None
    progress = 0
    
    sorted_ranks = sorted(REFERRAL_RANKS.items())
    for i, (count, rank_name) in enumerate(sorted_ranks):
        if referrals_count >= count:
            current_rank = rank_name
            
            # Определяем следующий ранг
            if i + 1 < len(sorted_ranks):
                next_rank_count, next_rank = sorted_ranks[i + 1]
                progress = min(int((referrals_count - count) / (next_rank_count - count) * 100), 100) if next_rank_count > count else 100
        else:
            break
    
    # Получаем рефералов
    referrals = db.get_referrals(user_id)[:10]  # Ограничиваем 10 рефералами
    
    # Формируем текст с рефералами
    referrals_text = ""
    if referrals:
        for i, ref in enumerate(referrals, 1):
            referrals_text += f"{i}. {ref['nickname']} - {ref['created_at'][:10] if ref['created_at'] else 'N/A'}\n"
    else:
        referrals_text = "Пока нет приглашенных друзей"
    
    # Формируем реферальную ссылку
    referral_link = f"https://t.me/{(await message.bot.get_me()).username}?start={user_id}"
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список рефералов", callback_data="referrals_list")
    builder.button(text="📊 Статистика", callback_data="referrals_stats")
    builder.button(text="🏆 Лидеры", callback_data="referrals_leaders")
    builder.button(text="🔗 Моя ссылка", callback_data="referrals_link")
    builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
    builder.adjust(2, 2, 1)
    
    await message.answer(
        f"👥 <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n\n"
        f"🎯 <b>Ваша статистика:</b>\n"
        f"• Приглашено друзей: <b>{referrals_count}</b>\n"
        f"• Текущий ранг: <b>{current_rank}</b>\n\n"
        
        f"📈 <b>Прогресс до следующего ранга:</b>\n"
        f"{'█' * int(progress/5)}{'░' * (20 - int(progress/5))} {progress}%\n\n"
        
        f"{(f'🎯 До ранга <b>{next_rank}</b> осталось: <b>{next_rank_count - referrals_count}</b> приглашений' if next_rank else '🎉 Вы достигли максимального ранга!')}\n\n"
        
        f"💰 <b>Бонусы:</b>\n"
        f"• За пригласившего: <b>{Config.REFERRER_BONUS} токенов</b>\n"
        f"• За приглашенного: <b>{Config.REFERRED_BONUS} токенов</b>\n\n"
        
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>",
        reply_markup=builder.as_markup()
    )

# Обработчики кнопок реферальной системы
@router.callback_query(F.data == "referrals_list")
async def handle_referrals_list(callback: CallbackQuery):
    """Список рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    referrals = db.get_referrals(user_id)
    
    if not referrals:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_to_referrals")
        builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
        builder.adjust(1, 1)
        
        await callback.message.edit_text(
            "📋 <b>СПИСОК РЕФЕРАЛОВ</b>\n\n"
            "😔 У вас пока нет приглашенных друзей.\n\n"
            "🎁 Приглашайте друзей и получайте бонусы!\n"
            f"• Вы получите: <b>{Config.REFERRER_BONUS} токенов</b>\n"
            f"• Друг получит: <b>{Config.REFERRED_BONUS} токенов</b>",
            reply_markup=builder.as_markup()
        )
    else:
        # Разбиваем на страницы по 5 рефералов
        page_size = 5
        pages = [referrals[i:i + page_size] for i in range(0, len(referrals), page_size)]
        
        # Текущая страница (показываем первую)
        current_page = 0
        
        referrals_text = ""
        for i, ref in enumerate(pages[current_page], 1):
            created_date = ref['created_at'][:10] if ref['created_at'] else "N/A"
            referrals_text += f"{i}. {ref['nickname']} - {created_date}\n"
        
        builder = InlineKeyboardBuilder()
        
        # Кнопки навигации по страницам
        if len(pages) > 1:
            builder.button(text="◀️", callback_data=f"referrals_page_{current_page-1}")
            builder.button(text=f"{current_page+1}/{len(pages)}", callback_data="referrals_page_info")
            builder.button(text="▶️", callback_data=f"referrals_page_{current_page+1}")
            builder.adjust(3)
        
        builder.row()
        builder.button(text="🔙 Назад", callback_data="back_to_referrals")
        builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
        builder.adjust(2)
        
        await callback.message.edit_text(
            f"📋 <b>ВАШИ РЕФЕРАЛЫ</b> ({len(referrals)} чел.)\n\n"
            f"{referrals_text}\n\n"
            f"🎁 <b>Бонусы за приглашение:</b>\n"
            f"• Вы получаете: <b>{Config.REFERRER_BONUS} токенов</b>\n"
            f"• Друг получает: <b>{Config.REFERRED_BONUS} токенов</b>",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "referrals_stats")
async def handle_referrals_stats(callback: CallbackQuery):
    """Статистика рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Получаем статистику
    referrals_count = db.get_referrals_count(user_id)
    stats = db.get_referral_stats(user_id)
    
    # Получаем достижения рефералов
    referrals = db.get_referrals(user_id)
    active_count = stats['active_referrals']
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_referrals")
    builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
    builder.adjust(1, 1)
    
    await callback.message.edit_text(
        f"📊 <b>СТАТИСТИКА РЕФЕРАЛОВ</b>\n\n"
        f"👥 <b>Общая статистика:</b>\n"
        f"• Всего рефералов: <b>{stats['total_referrals']}</b>\n"
        f"• Активных рефералов: <b>{active_count}</b>\n"
        f"• Конверсия: <b>{stats['conversion_rate']}%</b>\n\n"
        
        f"💰 <b>Финансовая статистика:</b>\n"
        f"• Получено бонусов: <b>{referrals_count * Config.REFERRER_BONUS} токенов</b>\n"
        f"• Роздано бонусов: <b>{referrals_count * Config.REFERRED_BONUS} токенов</b>\n\n"
        
        f"🏆 <b>Ранговая система:</b>\n",
        reply_markup=builder.as_markup()
    )
    
    # Добавляем информацию о рангах
    ranks_text = ""
    for count, rank_name in REFERRAL_RANKS.items():
        if referrals_count >= count:
            ranks_text += f"✅ {rank_name} ({count}+ рефералов)\n"
        else:
            ranks_text += f"◻️ {rank_name} ({count}+ рефералов)\n"
    
    await callback.message.answer(
        f"🎯 <b>Прогресс по рангам:</b>\n\n{ranks_text}",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()

@router.callback_query(F.data == "referrals_leaders")
async def handle_referrals_leaders(callback: CallbackQuery):
    """Таблица лидеров"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    try:
        conn = db._get_connection()
        cursor = conn.cursor()
        
        # Получаем топ-10 пользователей по количеству рефералов
        cursor.execute('''
            SELECT nickname, referrals_count 
            FROM users 
            WHERE referrals_count > 0 
            ORDER BY referrals_count DESC 
            LIMIT 10
        ''')
        
        leaders = cursor.fetchall()
        
        leaders_text = "🏆 <b>ТОП-10 ПРИГЛАШАТЕЛЕЙ</b>\n\n"
        
        if leaders:
            for i, leader in enumerate(leaders, 1):
                leaders_text += f"{i}. {leader['nickname']} - {leader['referrals_count']} реф.\n"
        else:
            leaders_text += "😔 Пока нет данных о лидерах.\n\n🎯 Станьте первым!"
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_to_referrals")
        builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
        builder.adjust(1, 1)
        
        await callback.message.edit_text(
            leaders_text,
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_to_referrals")
        builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
        builder.adjust(1, 1)
        
        await callback.message.edit_text(
            "❌ Ошибка при загрузке таблицы лидеров",
            reply_markup=builder.as_markup()
        )
    
    await callback.answer()

@router.callback_query(F.data == "referrals_link")
async def handle_referrals_link(callback: CallbackQuery):
    """Реферальная ссылка"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    referral_link = f"https://t.me/{(await callback.bot.get_me()).username}?start={user_id}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Поделиться", url=f"https://t.me/share/url?url={referral_link}&text=Присоединяйся%20к%20GromFit%20Bot!")
    builder.button(text="🔙 Назад", callback_data="back_to_referrals")
    builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
    builder.adjust(1, 1, 1)
    
    await callback.message.edit_text(
        f"🔗 <b>ВАША РЕФЕРАЛЬНАЯ ССЫЛКА</b>\n\n"
        f"Отправьте эту ссылку друзьям:\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"🎁 <b>Что получите:</b>\n"
        f"• Вы: <b>{Config.REFERRER_BONUS} токенов</b>\n"
        f"• Друг: <b>{Config.REFERRED_BONUS} токенов</b>\n\n"
        f"💡 <b>Как использовать:</b>\n"
        f"1. Отправьте ссылку другу\n"
        f"2. Друг переходит по ссылке\n"
        f"3. Регистрируется в боте\n"
        f"4. Бонусы начисляются автоматически!",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("referrals_page_"))
async def handle_referrals_page(callback: CallbackQuery):
    """Навигация по страницам списка рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    try:
        page_num = int(callback.data.split("_")[-1])
        referrals = db.get_referrals(user_id)
        
        if not referrals:
            await callback.answer("Нет рефералов")
            return
        
        page_size = 5
        pages = [referrals[i:i + page_size] for i in range(0, len(referrals), page_size)]
        
        # Проверяем границы
        if page_num < 0:
            page_num = 0
        elif page_num >= len(pages):
            page_num = len(pages) - 1
        
        referrals_text = ""
        for i, ref in enumerate(pages[page_num], 1):
            created_date = ref['created_at'][:10] if ref['created_at'] else "N/A"
            referrals_text += f"{i + page_num * page_size}. {ref['nickname']} - {created_date}\n"
        
        builder = InlineKeyboardBuilder()
        
        # Кнопки навигации
        if len(pages) > 1:
            builder.button(text="◀️", callback_data=f"referrals_page_{page_num-1}")
            builder.button(text=f"{page_num+1}/{len(pages)}", callback_data="referrals_page_info")
            builder.button(text="▶️", callback_data=f"referrals_page_{page_num+1}")
            builder.adjust(3)
        
        builder.row()
        builder.button(text="🔙 Назад", callback_data="back_to_referrals")
        builder.button(text="🏠 Главное меню", callback_data="referrals_back_to_menu")
        builder.adjust(2)
        
        await callback.message.edit_text(
            f"📋 <b>ВАШИ РЕФЕРАЛЫ</b> ({len(referrals)} чел.)\n\n"
            f"{referrals_text}\n\n"
            f"🎁 <b>Бонусы за приглашение:</b>\n"
            f"• Вы получаете: <b>{Config.REFERRER_BONUS} токенов</b>\n"
            f"• Друг получает: <b>{Config.REFERRED_BONUS} токенов</b>",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        await callback.answer("❌ Ошибка при загрузке страницы")
    
    await callback.answer()

@router.callback_query(F.data == "back_to_referrals")
async def handle_back_to_referrals(callback: CallbackQuery):
    """Возврат в меню рефералов"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await handle_referrals(callback.message)
    await callback.answer()

@router.callback_query(F.data == "referrals_back_to_menu")
async def handle_referrals_back_to_menu(callback: CallbackQuery):
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