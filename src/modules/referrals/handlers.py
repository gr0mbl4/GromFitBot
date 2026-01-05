"""
Обработчики реферальной системы
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "👥 РЕФЕРАЛЫ")
@router.message(Command("referrals"))
async def cmd_referrals(message: Message):
    """Обработчик команды рефералов"""
    telegram_id = message.from_user.id
    
    # Получаем статистику рефералов
    referrals_count = db.get_referrals_count(telegram_id)
    stats = db.get_referral_stats(telegram_id)
    
    # Получаем информацию о пользователе для ссылки
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Генерируем реферальную ссылку
    referral_link = f"https://t.me/gromfitbot?start=ref{telegram_id}"
    
    # Определяем текущий ранг
    ranks = {
        0: ("Новичок", "🥚"),
        3: ("Бронза", "🥉"),
        10: ("Серебро", "🥈"),
        25: ("Золото", "🥇"),
        50: ("Платина", "🏆"),
        100: ("Легенда", "👑")
    }
    
    current_rank = "Новичок"
    current_icon = "🥚"
    next_rank = "Бронза"
    next_required = 3
    progress_percentage = 0
    
    # Находим текущий и следующий ранг
    sorted_requirements = sorted(ranks.keys())
    for i, required in enumerate(sorted_requirements):
        if referrals_count >= required:
            current_rank, current_icon = ranks[required]
            
            # Определяем следующий ранг
            if i + 1 < len(sorted_requirements):
                next_required = sorted_requirements[i + 1]
                next_rank = ranks[next_required][0]
                
                # Вычисляем прогресс
                prev_required = required
                progress = referrals_count - prev_required
                total_needed = next_required - prev_required
                
                if total_needed > 0:
                    progress_percentage = min(100, int((progress / total_needed) * 100))
    
    text = (
        f"{current_icon} <b>РЕФЕРАЛЬНАЯ СИСТЕМА</b>\n\n"
        
        f"📊 <b>Общая статистика:</b>\n"
        f"• Приглашено друзей: {referrals_count}\n"
        f"• Активных рефералов: {stats.get('active_referrals', 0)}\n"
        f"• Заработано токенов: {stats.get('total_earned_tokens', 0.0):.2f} GFT\n"
        f"• Ожидает бонусов: {stats.get('pending_bonuses', 0.0):.2f} GFT\n"
        f"• Конверсия: {stats.get('conversion_rate', 0.0)}%\n\n"
        
        f"🎯 <b>Ваш ранг:</b> {current_rank} {current_icon}\n"
    )
    
    if next_rank and next_required > referrals_count:
        text += (
            f"• Следующий ранг: {next_rank}\n"
            f"• Нужно пригласить: {next_required - referrals_count} человек\n"
            f"• Прогресс: {progress_percentage}%\n\n"
        )
    
    text += (
        f"💰 <b>Бонусы:</b>\n"
        f"• За каждого приглашенного: {25} GFT\n"
        f"• Приглашенному другу: {50} GFT\n\n"
        
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        f"<i>Приглашайте друзей и получайте бонусы!</i>"
    )
    
    await message.answer(text, reply_markup=MainKeyboards.get_main_menu())

@router.message(F.text == "📋 Список рефералов")
async def show_referrals_list(message: Message):
    """Показать список рефералов"""
    telegram_id = message.from_user.id
    
    referrals_list = db.get_referrals_list(telegram_id)
    
    if not referrals_list:
        text = "📭 <b>СПИСОК РЕФЕРАЛОВ</b>\n\nУ вас пока нет приглашенных друзей."
        await message.answer(text, reply_markup=MainKeyboards.get_bottom_keyboard())
        return
    
    text = f"📋 <b>МОИ РЕФЕРАЛЫ</b> ({len(referrals_list)})\n\n"
    
    for i, ref in enumerate(referrals_list[:10], 1):  # Ограничиваем 10 записями
        nickname = ref.get('nickname', 'Без имени')
        region = ref.get('region', 'Не указан')
        created_at = ref.get('created_at', 'Неизвестно')
        balance = float(ref.get('balance_tokens', 0))
        
        if len(created_at) > 10:
            created_at = created_at[:10]
        
        status = "✅ Активен" if balance > 0 else "💤 Неактивен"
        
        text += (
            f"{i}. <b>{nickname}</b>\n"
            f"   🌍 {region} | {status}\n"
            f"   📅 {created_at} | 💰 {balance:.2f} GFT\n\n"
        )
    
    if len(referrals_list) > 10:
        text += f"... и еще {len(referrals_list) - 10} рефералов\n\n"
    
    await message.answer(text, reply_markup=MainKeyboards.get_bottom_keyboard())