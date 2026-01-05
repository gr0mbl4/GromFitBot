"""
Базовый модуль магазина
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from src.core.database import db
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()

@router.message(Command("shop"))
async def cmd_shop(message: Message):
    """Обработчик команды /shop"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
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

@router.message(F.text == "🛒 Магазин")
async def handle_shop_button(message: Message):
    """Обработчик кнопки магазина под чатом"""
    await cmd_shop(message)