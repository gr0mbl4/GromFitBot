"""
Обработчики ежедневных бонусов
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "🎁 ЕЖЕДНЕВНЫЙ БОНУС")
@router.message(Command("bonus"))
async def cmd_bonus(message: Message):
    """Обработчик ежедневного бонуса"""
    telegram_id = message.from_user.id
    
    # Получаем информацию о бонусе
    success, amount, streak = db.claim_daily_bonus(telegram_id)
    
    if success:
        text = (
            f"🎁 <b>ЕЖЕДНЕВНЫЙ БОНУС ПОЛУЧЕН!</b>\n\n"
            f"💰 <b>Начислено:</b> {amount:.2f} GFT\n"
            f"🔥 <b>Серия дней:</b> {streak}\n\n"
        )
        
        # Бонус за серию
        if streak >= 7:
            text += f"🎯 <b>Отличная серия!</b> Продолжайте в том же духе!\n\n"
        elif streak >= 30:
            text += f"🏆 <b>Невероятно!</b> 30 дней подряд! Вы чемпион!\n\n"
        
        text += "<i>Возвращайтесь завтра за новым бонусом!</i>"
    else:
        # Получаем информацию о следующем бонусе
        info = db.get_daily_bonus_info(telegram_id)
        
        if info.get('last_claim'):
            text = (
                f"⏳ <b>ЕЖЕДНЕВНЫЙ БОНУС</b>\n\n"
                f"Вы уже получали бонус сегодня.\n"
                f"🔥 <b>Текущая серия:</b> {info.get('streak', 0)} дней\n\n"
            )
            
            if info.get('next_claim'):
                text += f"🕐 <b>Следующий бонус:</b> {info['next_claim'][11:16]}\n\n"
            
            text += "<i>Возвращайтесь завтра!</i>"
        else:
            text = (
                f"❌ <b>ОШИБКА</b>\n\n"
                f"Не удалось получить ежедневный бонус.\n"
                f"Пожалуйста, попробуйте позже.\n\n"
                f"<i>Или обратитесь в поддержку</i>"
            )
    
    await message.answer(text, reply_markup=MainKeyboards.get_main_menu())