"""
Обработчики магазина
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

@router.message(F.text == "💰 МАГАЗИН")
@router.message(Command("shop"))
async def cmd_shop(message: Message):
    """Обработчик команды /shop"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    # Получаем балансы
    balances = db.get_user_balance(telegram_id)
    tokens = balances.get('tokens', 0.0)
    diamonds = balances.get('diamonds', 0.0)
    
    # Получаем товары
    shop_items = db.get_shop_items()
    
    if not shop_items:
        text = (
            f"🛒 <b>МАГАЗИН GROMFIT</b>\n\n"
            f"💰 <b>Ваш баланс:</b>\n"
            f"• Токены: {tokens:.2f} GFT\n"
            f"• Алмазы: {diamonds:.2f} 💎\n\n"
            f"❌ <b>Товары временно отсутствуют</b>\n\n"
            f"<i>Загляните позже!</i>"
        )
    else:
        text = (
            f"🛒 <b>МАГАЗИН GROMFIT</b>\n\n"
            f"💰 <b>Ваш баланс:</b>\n"
            f"• Токены: {tokens:.2f} GFT\n"
            f"• Алмазы: {diamonds:.2f} 💎\n\n"
            f"📦 <b>Доступные товары:</b>\n\n"
        )
        
        # Группируем товары по категориям
        categories = {}
        for item in shop_items[:10]:  # Ограничиваем 10 товарами
            item_type = item.get('item_type', 'other')
            if item_type not in categories:
                categories[item_type] = []
            categories[item_type].append(item)
        
        # Выводим товары по категориям
        for category, items in categories.items():
            category_name = {
                'tokens_pack': '💰 Пакеты токенов',
                'premium': '👑 Премиум статус',
                'boost': '⚡ Бусты',
                'cosmetic': '🎨 Косметика',
                'other': '🎁 Разное'
            }.get(category, '🎁 Товары')
            
            text += f"<b>{category_name}:</b>\n"
            
            for item in items:
                name = item.get('name', 'Без названия')
                description = item.get('description', '')
                price_tokens = float(item.get('price_tokens', 0))
                price_diamonds = float(item.get('price_diamonds', 0))
                icon = item.get('icon', '🛍️')
                
                price_text = ""
                if price_tokens > 0:
                    price_text += f"{price_tokens:.0f} GFT"
                if price_diamonds > 0:
                    if price_text:
                        price_text += " + "
                    price_text += f"{price_diamonds:.0f} 💎"
                
                text += f"{icon} <b>{name}</b> - {price_text}\n"
                if description:
                    text += f"   <i>{description[:50]}...</i>\n"
            
            text += "\n"
        
        text += "<i>Для покупки товара напишите его название</i>"
    
    await message.answer(text, reply_markup=MainKeyboards.get_main_menu())