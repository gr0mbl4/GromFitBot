"""
Полный модуль обработчиков магазина GromFitBot
Обрабатывает все команды и действия связанные с магазином
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

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

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ МАГАЗИНА ====================

@router.message(F.text == "🛒 Магазин")
async def handle_shop(message: Message):
    """Основной обработчик кнопки 'Магазин'"""
    user_id = message.from_user.id
    logger.info(f"Запрос магазина от пользователя {user_id}")
    
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации в боте."
        )
        return
    
    await show_shop_categories(message, user)

async def show_shop_categories(message: Message, user: Dict[str, Any]):
    """Отображение категорий магазина"""
    user_id = user['telegram_id']
    
    # Получаем баланс пользователя
    balance_tokens = user.get('balance_tokens', 0)
    balance_diamonds = user.get('balance_diamonds', 0)
    
    # Получаем категории товаров
    categories = get_shop_categories()
    
    shop_text = (
        f"🛒 <b>Магазин GromFit</b>\n\n"
        
        f"<b>Ваш баланс:</b>\n"
        f"💰 <b>Токены:</b> {balance_tokens:.0f}\n"
        f"💎 <b>Алмазы:</b> {balance_diamonds:.0f}\n\n"
        
        f"<b>Категории товаров:</b>\n"
    )
    
    # Описание категорий
    for category in categories:
        shop_text += f"{category['icon']} <b>{category['name']}</b> - {category['description']}\n"
    
    shop_text += "\n<i>Выберите категорию для просмотра товаров</i>"
    
    await message_manager.replace_message(
        message,
        shop_text,
        MainKeyboards.get_shop_categories_keyboard()
    )

def get_shop_categories() -> List[Dict[str, str]]:
    """Получение списка категорий магазина"""
    return [
        {
            'id': 'premium',
            'name': '💎 Премиум',
            'icon': '💎',
            'description': 'Премиум статусы и привилегии'
        },
        {
            'id': 'design',
            'name': '🎨 Оформление',
            'icon': '🎨',
            'description': 'Темы, аватары, оформление'
        },
        {
            'id': 'boosters',
            'name': '⚡️ Бустеры',
            'icon': '⚡️',
            'description': 'Ускорители и усилители'
        },
        {
            'id': 'gifts',
            'name': '🎁 Подарки',
            'icon': '🎁',
            'description': 'Подарки для друзей'
        },
        {
            'id': 'tools',
            'name': '🛠️ Инструменты',
            'icon': '🛠️',
            'description': 'Полезные инструменты'
        },
        {
            'id': 'emotions',
            'name': '🎭 Эмоции',
            'icon': '🎭',
            'description': 'Стикеры и эмоции'
        },
        {
            'id': 'all',
            'name': '📦 Все товары',
            'icon': '📦',
            'description': 'Все доступные товары'
        }
    ]

# ==================== ОБРАБОТЧИКИ КАТЕГОРИЙ ====================

@router.callback_query(F.data.startswith("shop_category_"))
async def handle_shop_category(callback: CallbackQuery):
    """Обработчик выбора категории магазина"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    category_id = callback.data.replace("shop_category_", "")
    
    if category_id == "all":
        # Показать все товары
        items = db.get_shop_items(active_only=True)
        category_name = "Все товары"
        category_icon = "📦"
    else:
        # Показать товары конкретной категории
        items = db.get_shop_items(category=category_id, active_only=True)
        category_info = get_category_info(category_id)
        category_name = category_info['name']
        category_icon = category_info['icon']
    
    if not items:
        await message_manager.edit_message_with_menu(
            callback,
            f"{category_icon} <b>{category_name}</b>\n\n"
            "В этой категории пока нет товаров.\n\n"
            "<i>Загляните позже, ассортимент обновляется регулярно!</i>",
            MainKeyboards.get_back_keyboard("shop_categories")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    await show_shop_items(callback, user, items, category_id, 0)

def get_category_info(category_id: str) -> Dict[str, str]:
    """Получение информации о категории"""
    categories = get_shop_categories()
    for category in categories:
        if category['id'] == category_id:
            return category
    
    return {'name': 'Неизвестная категория', 'icon': '❓'}

async def show_shop_items(callback: CallbackQuery, user: Dict[str, Any], 
                         items: List[Dict[str, Any]], category_id: str, page: int):
    """Отображение товаров категории с пагинацией"""
    user_id = user['telegram_id']
    items_per_page = 5
    
    # Вычисляем общее количество страниц
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    if page >= total_pages:
        page = total_pages - 1
    
    # Получаем товары для текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    category_info = get_category_info(category_id)
    
    items_text = (
        f"{category_info['icon']} <b>{category_info['name']}</b>\n\n"
        f"<b>Товары:</b> {len(items)} | <b>Страница:</b> {page + 1}/{total_pages}\n\n"
    )
    
    for i, item in enumerate(page_items, start_idx + 1):
        item_name = item.get('name', 'Без названия')
        item_price = item.get('price_tokens', 0)
        item_icon = item.get('icon', '🛒')
        item_description = item.get('description', 'Без описания')
        
        # Обрезаем длинное описание
        if len(item_description) > 50:
            item_description = item_description[:47] + "..."
        
        items_text += (
            f"<b>{i}. {item_icon} {item_name}</b>\n"
            f"   {item_description}\n"
            f"   💰 <b>Цена:</b> {item_price:.0f} токенов\n\n"
        )
    
    items_text += "<i>Выберите товар для покупки</i>"
    
    # Создаем клавиатуру с товарами
    keyboard = MainKeyboards.get_shop_items_keyboard(category_id, items, page)
    
    await message_manager.edit_message_with_menu(
        callback,
        items_text,
        keyboard
    )
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data.startswith("shop_page_"))
async def handle_shop_page(callback: CallbackQuery):
    """Обработчик пагинации в магазине"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    data_parts = callback.data.split("_")
    
    if len(data_parts) < 4:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Ошибка пагинации",
            show_alert=True
        )
        return
    
    category_id = data_parts[2]
    page = int(data_parts[3])
    
    if category_id == "current":
        # Остаемся на текущей странице
        await message_manager.answer_callback_with_notification(
            callback,
            f"Страница {page + 1}",
            show_alert=False
        )
        return
    
    # Получаем товары категории
    if category_id == "all":
        items = db.get_shop_items(active_only=True)
    else:
        items = db.get_shop_items(category=category_id, active_only=True)
    
    await show_shop_items(callback, user, items, category_id, page)

# ==================== ОБРАБОТЧИКИ ТОВАРОВ ====================

@router.callback_query(F.data.startswith("shop_item_"))
async def handle_shop_item(callback: CallbackQuery):
    """Обработчик выбора товара"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    item_id = callback.data.replace("shop_item_", "")
    
    # Получаем информацию о товаре
    item = db.get_shop_item(item_id)
    
    if not item:
        await message_manager.edit_message_with_menu(
            callback,
            "❌ <b>Товар не найден</b>\n\n"
            "Этот товар больше не доступен в магазине.",
            MainKeyboards.get_back_keyboard("shop_items")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    await show_item_details(callback, user, item)

async def show_item_details(callback: CallbackQuery, user: Dict[str, Any], item: Dict[str, Any]):
    """Отображение деталей товара"""
    user_id = user['telegram_id']
    
    item_name = item.get('name', 'Без названия')
    item_description = item.get('description', 'Без описания')
    item_price_tokens = item.get('price_tokens', 0)
    item_price_diamonds = item.get('price_diamonds', 0)
    item_icon = item.get('icon', '🛒')
    item_category = item.get('category', 'general')
    available_quantity = item.get('available_quantity', -1)
    purchased_count = item.get('purchased_count', 0)
    
    # Получаем информацию о категории
    category_info = get_category_info(item_category)
    
    # Проверяем баланс пользователя
    user_balance_tokens = user.get('balance_tokens', 0)
    user_balance_diamonds = user.get('balance_diamonds', 0)
    
    has_enough_tokens = user_balance_tokens >= item_price_tokens
    has_enough_diamonds = user_balance_diamonds >= item_price_diamonds
    can_purchase = has_enough_tokens and has_enough_diamonds
    
    item_text = (
        f"{item_icon} <b>{item_name}</b>\n\n"
        
        f"<b>Описание:</b>\n{item_description}\n\n"
        
        f"<b>Категория:</b> {category_info['icon']} {category_info['name']}\n"
        f"<b>Куплено раз:</b> {purchased_count}\n"
    )
    
    if available_quantity != -1:
        item_text += f"<b>В наличии:</b> {available_quantity} шт.\n"
    
    item_text += "\n<b>Цена:</b>\n"
    
    if item_price_tokens > 0:
        item_text += f"💰 <b>Токены:</b> {item_price_tokens:.0f}\n"
    
    if item_price_diamonds > 0:
        item_text += f"💎 <b>Алмазы:</b> {item_price_diamonds:.0f}\n"
    
    item_text += f"\n<b>Ваш баланс:</b>\n"
    item_text += f"💰 <b>Токены:</b> {user_balance_tokens:.0f} "
    item_text += f"{'✅ Достаточно' if has_enough_tokens else '❌ Недостаточно'}\n"
    
    if item_price_diamonds > 0:
        item_text += f"💎 <b>Алмазы:</b> {user_balance_diamonds:.0f} "
        item_text += f"{'✅ Достаточно' if has_enough_diamonds else '❌ Недостаточно'}\n"
    
    if not can_purchase:
        item_text += "\n❌ <b>Недостаточно средств для покупки</b>\n"
    
    item_text += "\n<i>Выберите количество для покупки</i>"
    
    # Создаем клавиатуру
    keyboard = MainKeyboards.get_shop_item_detail_keyboard(
        item['item_id'], 
        item_price_tokens, 
        user_balance_tokens
    )
    
    await message_manager.edit_message_with_menu(
        callback,
        item_text,
        keyboard
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ ПОКУПОК ====================

@router.callback_query(F.data.startswith("shop_buy"))
async def handle_shop_buy(callback: CallbackQuery):
    """Обработчик покупки товара"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    data_parts = callback.data.split("_")
    
    if len(data_parts) < 3:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Ошибка покупки",
            show_alert=True
        )
        return
    
    item_id = data_parts[2]
    quantity = 1
    
    # Проверяем количество
    if len(data_parts) > 3:
        quantity_str = data_parts[3]
        if quantity_str.startswith("x"):
            try:
                quantity = int(quantity_str[1:])
            except:
                quantity = 1
    
    # Получаем информацию о товаре
    item = db.get_shop_item(item_id)
    
    if not item:
        await message_manager.edit_message_with_menu(
            callback,
            "❌ <b>Товар не найден</b>\n\n"
            "Этот товар больше не доступен в магазине.",
            MainKeyboards.get_back_keyboard("shop_items")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    # Проверяем доступность
    available_quantity = item.get('available_quantity', -1)
    if available_quantity != -1 and available_quantity < quantity:
        await message_manager.edit_message_with_menu(
            callback,
            f"❌ <b>Недостаточно товара</b>\n\n"
            f"В наличии только {available_quantity} шт.\n"
            f"Вы пытаетесь купить {quantity} шт.",
            MainKeyboards.get_back_keyboard("shop_item")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    # Выполняем покупку
    purchase_result = db.purchase_item(user_id, item_id, quantity)
    
    if not purchase_result['success']:
        error_message = purchase_result.get('error', 'Неизвестная ошибка')
        
        await message_manager.edit_message_with_menu(
            callback,
            f"❌ <b>Ошибка покупки</b>\n\n"
            f"{error_message}\n\n"
            f"<i>Попробуйте позже или выберите другой товар</i>",
            MainKeyboards.get_back_keyboard("shop_item")
        )
        
        await message_manager.answer_callback_with_notification(
            callback,
            f"Ошибка: {error_message}",
            show_alert=True
        )
        return
    
    # Покупка успешна
    item_name = item.get('name', 'Без названия')
    total_tokens = purchase_result['total_tokens']
    total_diamonds = purchase_result['total_diamonds']
    new_balance_tokens = purchase_result['new_balance_tokens']
    new_balance_diamonds = purchase_result['new_balance_diamonds']
    
    success_text = (
        f"✅ <b>Покупка успешна!</b>\n\n"
        
        f"<b>Куплено:</b> {item_name} x{quantity}\n\n"
        
        f"<b>Списано:</b>\n"
    )
    
    if total_tokens > 0:
        success_text += f"💰 <b>Токены:</b> {total_tokens:.0f}\n"
    
    if total_diamonds > 0:
        success_text += f"💎 <b>Алмазы:</b> {total_diamonds:.0f}\n"
    
    success_text += (
        f"\n<b>Новый баланс:</b>\n"
        f"💰 <b>Токены:</b> {new_balance_tokens:.0f}\n"
    )
    
    if total_diamonds > 0:
        success_text += f"💎 <b>Алмазы:</b> {new_balance_diamonds:.0f}\n"
    
    success_text += "\n<i>Товар добавлен в вашу коллекцию</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        success_text,
        MainKeyboards.get_back_keyboard("shop_items")
    )
    
    await message_manager.answer_callback_with_notification(
        callback,
        f"✅ Куплено {item_name} x{quantity}",
        show_alert=True
    )

@router.callback_query(F.data == "shop_insufficient_funds")
async def handle_insufficient_funds(callback: CallbackQuery):
    """Обработчик недостатка средств"""
    await message_manager.answer_callback_with_notification(
        callback,
        "❌ Недостаточно средств для покупки",
        show_alert=True
    )

@router.callback_query(F.data == "shop_sufficient_funds")
async def handle_sufficient_funds(callback: CallbackQuery):
    """Обработчик достаточности средств"""
    await message_manager.answer_callback_with_notification(
        callback,
        "✅ Средств достаточно для покупки",
        show_alert=False
    )

@router.callback_query(F.data == "shop_gift_")
async def handle_shop_gift(callback: CallbackQuery):
    """Обработчик подарка товара"""
    # Временная заглушка - функция в разработке
    await message_manager.answer_callback_with_notification(
        callback,
        "🎁 Функция подарков появится в следующем обновлении",
        show_alert=True
    )

# ==================== ОБРАБОТЧИКИ ДРУГИХ ФУНКЦИЙ МАГАЗИНА ====================

@router.callback_query(F.data == "shop_my_purchases")
async def handle_shop_my_purchases(callback: CallbackQuery):
    """Обработчик кнопки 'Мои покупки'"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    purchases = db.get_user_purchases(user_id, limit=20)
    
    if not purchases:
        await message_manager.edit_message_with_menu(
            callback,
            "🛍️ <b>Мои покупки</b>\n\n"
            "У вас пока нет покупок.\n\n"
            "<i>Загляните в магазин и выберите что-нибудь для себя!</i>",
            MainKeyboards.get_back_keyboard("shop_categories")
        )
        await message_manager.answer_callback_with_notification(callback)
        return
    
    purchases_text = "🛍️ <b>Мои покупки</b>\n\n"
    
    total_spent_tokens = 0
    total_spent_diamonds = 0
    
    for i, purchase in enumerate(purchases, 1):
        item_name = purchase.get('item_name', 'Без названия')
        quantity = purchase.get('quantity', 1)
        price_tokens = purchase.get('price_tokens', 0)
        price_diamonds = purchase.get('price_diamonds', 0)
        purchase_date = purchase.get('purchase_date', '')
        
        # Форматируем дату
        if purchase_date:
            try:
                if isinstance(purchase_date, str):
                    date_obj = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                else:
                    date_obj = purchase_date
                
                date_str = date_obj.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = "Неизвестно"
        else:
            date_str = "Неизвестно"
        
        purchases_text += f"<b>{i}. {item_name} x{quantity}</b>\n"
        purchases_text += f"   📅 {date_str}\n"
        
        if price_tokens > 0:
            purchases_text += f"   💰 {price_tokens:.0f} токенов\n"
            total_spent_tokens += price_tokens
        
        if price_diamonds > 0:
            purchases_text += f"   💎 {price_diamonds:.0f} алмазов\n"
            total_spent_diamonds += price_diamonds
        
        purchases_text += "\n"
    
    purchases_text += f"<b>Всего потрачено:</b>\n"
    
    if total_spent_tokens > 0:
        purchases_text += f"💰 <b>Токены:</b> {total_spent_tokens:.0f}\n"
    
    if total_spent_diamonds > 0:
        purchases_text += f"💎 <b>Алмазы:</b> {total_spent_diamonds:.0f}\n"
    
    purchases_text += f"\n<b>Всего покупок:</b> {len(purchases)}"
    
    await message_manager.edit_message_with_menu(
        callback,
        purchases_text,
        MainKeyboards.get_back_keyboard("shop_categories")
    )
    
    await message_manager.answer_callback_with_notification(callback)

# ==================== ОБРАБОТЧИКИ НАВИГАЦИИ ====================

@router.callback_query(F.data == "back_to_shop")
async def handle_back_to_shop(callback: CallbackQuery):
    """Возврат в магазин"""
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
        text="🛒 Магазин",
        from_user=callback.from_user
    )
    msg.bot = callback.bot
    
    # Показываем категории магазина
    await show_shop_categories(msg, user)
    
    await message_manager.answer_callback_with_notification(callback)

@router.callback_query(F.data == "back_to_shop_menu")
async def handle_back_to_shop_menu(callback: CallbackQuery):
    """Возврат в меню магазина (алиас)"""
    await handle_back_to_shop(callback)

@router.callback_query(F.data == "back_to_shop_categories")
async def handle_back_to_shop_categories(callback: CallbackQuery):
    """Возврат к категориям магазина"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    await show_shop_categories_from_callback(callback, user)

async def show_shop_categories_from_callback(callback: CallbackQuery, user: Dict[str, Any]):
    """Отображение категорий магазина из callback"""
    user_id = user['telegram_id']
    
    # Получаем баланс пользователя
    balance_tokens = user.get('balance_tokens', 0)
    balance_diamonds = user.get('balance_diamonds', 0)
    
    # Получаем категории товаров
    categories = get_shop_categories()
    
    shop_text = (
        f"🛒 <b>Магазин GromFit</b>\n\n"
        
        f"<b>Ваш баланс:</b>\n"
        f"💰 <b>Токены:</b> {balance_tokens:.0f}\n"
        f"💎 <b>Алмазы:</b> {balance_diamonds:.0f}\n\n"
        
        f"<b>Категории товаров:</b>\n"
    )
    
    # Описание категорий
    for category in categories:
        shop_text += f"{category['icon']} <b>{category['name']}</b> - {category['description']}\n"
    
    shop_text += "\n<i>Выберите категорию для просмотра товаров</i>"
    
    await message_manager.edit_message_with_menu(
        callback,
        shop_text,
        MainKeyboards.get_shop_categories_keyboard()
    )

@router.callback_query(F.data == "back_to_shop_items")
async def handle_back_to_shop_items(callback: CallbackQuery):
    """Возврат к списку товаров"""
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.answer_callback_with_notification(
            callback,
            "❌ Вы не зарегистрированы",
            show_alert=True
        )
        return
    
    # Нужно определить из какой категории был переход
    # Для простоты возвращаем в категории
    await show_shop_categories_from_callback(callback, user)

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main_from_shop(callback: CallbackQuery):
    """Возврат в главное меню из магазина"""
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

# ==================== КОМАНДЫ ДЛЯ МАГАЗИНА ====================

@router.message(Command("shop"))
async def handle_shop_command(message: Message):
    """Обработчик команды /shop"""
    await handle_shop(message)

@router.message(Command("buy"))
async def handle_buy_command(message: Message):
    """Обработчик команды /buy"""
    await message_manager.replace_message(
        message,
        "🛒 <b>Покупка товаров</b>\n\n"
        "Для покупки товаров используйте магазин:\n"
        "1. Нажмите кнопку '🛒 Магазин'\n"
        "2. Выберите категорию\n"
        "3. Выберите товар\n"
        "4. Нажмите 'Купить'\n\n"
        "<i>Или используйте команду /shop для перехода в магазин</i>",
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("purchases"))
async def handle_purchases_command(message: Message):
    """Обработчик команды /purchases"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    purchases = db.get_user_purchases(user_id, limit=10)
    
    if not purchases:
        await message_manager.replace_message(
            message,
            "🛍️ <b>Мои покупки</b>\n\n"
            "У вас пока нет покупок.\n\n"
            "<i>Загляните в магазин и выберите что-нибудь для себя!</i>",
            MainKeyboards.get_back_to_main_keyboard()
        )
        return
    
    purchases_text = "🛍️ <b>Мои покупки</b>\n\n"
    
    for i, purchase in enumerate(purchases[:5], 1):
        item_name = purchase.get('item_name', 'Без названия')
        quantity = purchase.get('quantity', 1)
        purchase_date = purchase.get('purchase_date', '')
        
        # Форматируем дату
        if purchase_date:
            try:
                if isinstance(purchase_date, str):
                    date_obj = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                else:
                    date_obj = purchase_date
                
                date_str = date_obj.strftime("%d.%m")
            except:
                date_str = "Неизвестно"
        else:
            date_str = "Неизвестно"
        
        purchases_text += f"{i}. {item_name} x{quantity} ({date_str})\n"
    
    if len(purchases) > 5:
        purchases_text += f"\n... и еще {len(purchases) - 5} покупок"
    
    purchases_text += f"\n\n<b>Всего покупок:</b> {len(purchases)}"
    
    await message_manager.replace_message(
        message,
        purchases_text,
        MainKeyboards.get_back_to_main_keyboard()
    )

@router.message(Command("balance"))
async def handle_balance_shop_command(message: Message):
    """Обработчик команды /balance для магазина"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if not user:
        await message_manager.replace_message(
            message,
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Используйте команду /start для регистрации."
        )
        return
    
    balance_tokens = user.get('balance_tokens', 0)
    balance_diamonds = user.get('balance_diamonds', 0)
    
    await message_manager.replace_message(
        message,
        f"💰 <b>Ваш баланс</b>\n\n"
        f"• Токены: <b>{balance_tokens:.0f}</b>\n"
        f"• Алмазы: <b>{balance_diamonds:.0f}</b>\n\n"
        f"<i>Используйте токены для покупок в магазине</i>",
        MainKeyboards.get_back_to_main_keyboard()
    )