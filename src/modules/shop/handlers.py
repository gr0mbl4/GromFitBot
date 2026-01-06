"""
Обработчики магазина - исправленная версия
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.database import Database
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
db = Database()

# Единый обработчик для магазина
@router.message(F.text.in_(["💰 Магазин", "🛒 Магазин"]))
@router.message(Command("shop"))
async def handle_shop(message: Message):
    """Обработчик магазина из любого места (главное меню или нижнее меню)"""
    
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы. Используйте /start",
            reply_markup=MainKeyboards.get_main_menu()
        )
        return
    
    # Получаем баланс пользователя
    balance = user['balance_tokens']
    diamonds = user.get('balance_diamonds', 0)
    
    # Создаем клавиатуру магазина
    builder = InlineKeyboardBuilder()
    
    # Категории товаров
    builder.button(text="💪 Бусты для тренировок", callback_data="shop_category_boosts")
    builder.button(text="🎨 Стили и темы", callback_data="shop_category_styles")
    builder.button(text="⚡ Премиум-статус", callback_data="shop_category_premium")
    builder.button(text="🎁 Подарочные наборы", callback_data="shop_category_gifts")
    
    builder.adjust(1)  # По одной кнопке в ряд
    
    # Кнопки навигации
    builder.row()
    builder.button(text="🏠 Главное меню", callback_data="shop_back_to_menu")
    
    await message.answer(
        f"🛒 <b>Магазин GromFit</b>\n\n"
        f"💰 Ваш баланс: <b>{balance}</b> токенов\n"
        f"💎 Алмазов: <b>{diamonds}</b>\n\n"
        f"Выберите категорию:",
        reply_markup=builder.as_markup()
    )

# Обработчик покупки бустов
@router.callback_query(F.data == "shop_category_boosts")
async def handle_boosts_category(callback: CallbackQuery):
    """Показывает бусты для тренировок"""
    
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    builder = InlineKeyboardBuilder()
    
    # Товары-бусты с проверкой цены
    boosts = [
        ("2x Опыт на 1 час", 50, "boost_xp_1h"),
        ("2x Токены на 1 час", 75, "boost_tokens_1h"),
        ("Авто-разминка", 100, "boost_warmup"),
        ("Защита от травм", 150, "boost_protection"),
    ]
    
    for name, price, data in boosts:
        # Проверяем, хватает ли денег
        can_afford = user['balance_tokens'] >= price
        button_text = f"{name} - {price} токенов"
        
        if not can_afford:
            button_text += " ❌"
            builder.button(text=button_text, callback_data="shop_insufficient_funds")
        else:
            builder.button(text=button_text, callback_data=f"shop_buy_{data}")
    
    builder.adjust(1)
    
    # Кнопки навигации
    builder.row()
    builder.button(text="🔙 Назад в магазин", callback_data="shop_back")
    builder.button(text="🏠 Главное меню", callback_data="shop_back_to_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(
        "💪 <b>Бусты для тренировок</b>\n\n"
        f"💰 Ваш баланс: <b>{user['balance_tokens']}</b> токенов\n\n"
        "Усильте свои тренировки с помощью бустов:",
        reply_markup=builder.as_markup()
    )
    
    await callback.answer()

# Обработчик недостатка средств
@router.callback_query(F.data == "shop_insufficient_funds")
async def handle_insufficient_funds(callback: CallbackQuery):
    """Обработчик недостатка средств"""
    await callback.answer("❌ Недостаточно средств на балансе!", show_alert=True)

# Обработчик покупки
@router.callback_query(F.data.startswith("shop_buy_"))
async def handle_buy_item(callback: CallbackQuery):
    """Обработчик покупки товара"""
    
    item_id = callback.data.replace("shop_buy_", "")
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Ошибка: пользователь не найден")
        return
    
    # Определяем цену товара
    prices = {
        "boost_xp_1h": 50,
        "boost_tokens_1h": 75,
        "boost_warmup": 100,
        "boost_protection": 150,
    }
    
    price = prices.get(item_id, 0)
    
    if price == 0:
        await callback.answer("❌ Товар не найден")
        return
    
    # Проверяем баланс
    if user['balance_tokens'] < price:
        await callback.answer("❌ Недостаточно средств на балансе!", show_alert=True)
        return
    
    # Списываем средства
    new_balance = user['balance_tokens'] - price
    db.update_user(user_id, {'balance_tokens': new_balance})
    
    # Добавляем транзакцию
    item_names = {
        "boost_xp_1h": "Буст опыта x2 (1 час)",
        "boost_tokens_1h": "Буст токенов x2 (1 час)",
        "boost_warmup": "Авто-разминка",
        "boost_protection": "Защита от травм",
    }
    
    item_name = item_names.get(item_id, "Неизвестный товар")
    db.add_transaction(
        user_id=user_id,
        transaction_type='shop_purchase',
        amount=-price,
        description=f'Покупка: {item_name}'
    )
    
    await callback.answer("✅ Товар куплен!")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Продолжить покупки", callback_data="shop_back")
    builder.button(text="🏠 Главное меню", callback_data="shop_back_to_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"✅ <b>Покупка успешно завершена!</b>\n\n"
        f"🎁 Товар: <b>{item_name}</b>\n"
        f"💸 Стоимость: <b>{price}</b> токенов\n"
        f"💰 Новый баланс: <b>{new_balance}</b> токенов\n\n"
        "Товар добавлен в ваш инвентарь.\n"
        "Используйте его в следующих тренировках!",
        reply_markup=builder.as_markup()
    )

# Обработчик возврата в меню
@router.callback_query(F.data == "shop_back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    from src.modules.profile.handlers import handle_back_to_main_menu
    await handle_back_to_main_menu(callback)

# Обработчик возврата в магазин
@router.callback_query(F.data == "shop_back")
async def handle_back_to_shop(callback: CallbackQuery):
    """Возврат в главное меню магазина"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await handle_shop(callback.message)
    await callback.answer()