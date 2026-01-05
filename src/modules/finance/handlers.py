"""
Обработчики команд финансовой системы (две валюты: токены и алмазы)
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from .token_system import token_system
from .diamond_system import diamond_system
from src.modules.auth.keyboards import MainKeyboards

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "menu_balance")
@router.callback_query(F.data == "back_balance")
async def callback_balance(callback: CallbackQuery):
    """Показ баланса пользователя (обе валюты)"""
    
    telegram_id = callback.from_user.id
    
    # Получаем информацию о балансе токенов
    token_balance = token_system.get_balance(telegram_id)
    diamond_balance = diamond_system.get_balance(telegram_id)
    
    if "error" in token_balance or "error" in diamond_balance:
        await callback.answer("Ошибка получения баланса", show_alert=True)
        return
    
    # Минимальный вывод алмазов
    min_withdrawal = diamond_system.MIN_WITHDRAWAL
    
    # Форматируем сообщение
    text = (
        f"💰 <b>ВАШ БАЛАНС</b>\n\n"
        f"💎 <b>Доступно токенов:</b> {token_balance['formatted_balance']}\n"
        f"💠 <b>Доступно алмазов:</b> {diamond_balance['formatted_balance']}\n\n"
        
        f"📈 <b>Статистика токенов:</b>\n"
        f"• 📥 Всего заработано: {token_balance['formatted_earned']}\n"
        f"• 📤 Всего потрачено: {token_balance['formatted_spent']}\n\n"
        
        f"📊 <b>Статистика алмазов:</b>\n"
        f"• 📥 Всего заработано: {diamond_balance['formatted_earned']}\n"
        f"• 📤 Всего потрачено: {diamond_balance['formatted_spent']}\n\n"
        
        f"⚡️ <b>1 алмаз = 1 звезда</b>\n"
        f"🏧 <b>Минимальный вывод:</b> {min_withdrawal}💎\n"
        f"💸 <b>Комиссия на вывод:</b> 10%\n\n"
        f"<i>Токены и алмазы можно использовать для участия в дуэлях, покупки в магазине</i>"
    )
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💎 Алмазы",
            callback_data="balance_diamonds"
        ),
        InlineKeyboardButton(
            text="💎 Токены",
            callback_data="balance_tokens"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 История операций",
            callback_data="balance_history"
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

@router.callback_query(F.data == "balance_diamonds")
async def callback_balance_diamonds(callback: CallbackQuery):
    """Управление алмазами"""
    
    telegram_id = callback.from_user.id
    diamond_balance = diamond_system.get_balance(telegram_id)
    
    if "error" in diamond_balance:
        await callback.answer(diamond_balance['error'], show_alert=True)
        return
    
    min_withdrawal = diamond_system.MIN_WITHDRAWAL
    
    text = (
        f"💎 <b>УПРАВЛЕНИЕ АЛМАЗАМИ</b>\n\n"
        f"💰 <b>Баланс:</b> {diamond_balance['formatted_balance']}\n"
        f"🏆 <b>Всего заработано:</b> {diamond_balance['formatted_earned']}\n"
        f"💸 <b>Всего потрачено:</b> {diamond_balance['formatted_spent']}\n\n"
        
        f"⚡️ <b>1 алмаз = 1 звезда Telegram</b>\n"
        f"🏧 <b>Минимальный вывод:</b> {min_withdrawal}💎\n"
        f"💳 <b>Комиссия на вывод:</b> 10%\n\n"
        
        f"<i>Алмазы можно заработать в дуэлях или купить за звезды</i>"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки для алмазов
    builder.row(
        InlineKeyboardButton(
            text="💳 Купить алмазы",
            callback_data="diamonds_buy"
        ),
        InlineKeyboardButton(
            text="🏧 Вывести алмазы",
            callback_data="diamonds_withdraw"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 История алмазов",
            callback_data="diamonds_history"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к балансу",
            callback_data="back_balance"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "balance_tokens")
async def callback_balance_tokens(callback: CallbackQuery):
    """Управление токенами"""
    
    telegram_id = callback.from_user.id
    token_balance = token_system.get_balance(telegram_id)
    
    if "error" in token_balance:
        await callback.answer(token_balance['error'], show_alert=True)
        return
    
    text = (
        f"💎 <b>УПРАВЛЕНИЕ ТОКЕНАМИ</b>\n\n"
        f"💰 <b>Баланс:</b> {token_balance['formatted_balance']}\n"
        f"🏆 <b>Всего заработано:</b> {token_balance['formatted_earned']}\n"
        f"💸 <b>Всего потрачено:</b> {token_balance['formatted_spent']}\n\n"
        
        f"🎯 <b>Как получить токены:</b>\n"
        f"• Приглашайте друзей (реферальная система)\n"
        f"• Получайте ежедневные бонусы\n"
        f"• Завоевывайте достижения\n"
        f"• Участвуйте в дуэлях\n\n"
        
        f"<i>Токены - внутренняя валюта, их нельзя вывести или обменять на алмазы</i>"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Кнопки для токенов
    builder.row(
        InlineKeyboardButton(
            text="👥 Реферальная система",
            callback_data="menu_referrals"
        ),
        InlineKeyboardButton(
            text="🎁 Ежедневный бонус",
            callback_data="tokens_daily_bonus"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 История токенов",
            callback_data="tokens_history"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к балансу",
            callback_data="back_balance"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "tokens_daily_bonus")
async def callback_tokens_daily_bonus(callback: CallbackQuery):
    """Получение ежедневного бонуса токенов"""
    
    telegram_id = callback.from_user.id
    
    result = token_system.award_daily_bonus(telegram_id)
    
    if "error" in result:
        await callback.answer(result['error'], show_alert=True)
    else:
        # Получаем обновленный баланс
        balance_info = token_system.get_balance(telegram_id)
        
        await callback.message.edit_text(
            f"🎉 <b>{result['message']}</b>\n\n"
            f"💰 <b>Текущий баланс токенов:</b> {balance_info['formatted_balance']}\n\n"
            f"Заходите завтра за новым бонусом!",
            parse_mode="HTML"
        )
        
        # Кнопка назад
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к токенам",
                callback_data="balance_tokens"
            )
        )
        
        await callback.message.answer(
            "👇",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "diamonds_buy")
async def callback_diamonds_buy(callback: CallbackQuery):
    """Покупка алмазов за звезды"""
    
    text = (
        "💎 <b>ПОКУПКА АЛМАЗОВ ЗА ЗВЕЗДЫ</b>\n\n"
        
        "⭐️ <b>Курс обмена:</b> 1 алмаз = 1 звезда\n\n"
        
        "📦 <b>Пакеты алмазов:</b>\n\n"
        
        "1. <b>100 алмазов</b> - 100 звезд\n"
        "   • Идеально для начала\n"
        "   • Мгновенное зачисление\n\n"
        
        "2. <b>500 алмазов</b> - 500 звезд\n"
        "   • Выгодный пакет\n"
        "   • +50 алмазов в подарок\n\n"
        
        "3. <b>1000 алмазов</b> - 1000 звезд\n"
        "   • Максимальная выгода\n"
        "   • +150 алмазов в подарок\n"
        "   • VIP статус на 7 дней\n\n"
        
        "4. <b>5000 алмазов</b> - 5000 звезд\n"
        "   • Для профессионалов\n"
        "   • +1000 алмазов в подарок\n"
        "   • Премиум статус на 30 дней\n\n"
        
        "👇 <b>Выберите пакет для покупки:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Пакеты алмазов
    packages = [
        (100, "100💎 - 100⭐"),
        (500, "500💎 - 500⭐"),
        (1000, "1000💎 - 1000⭐"),
        (5000, "5000💎 - 5000⭐")
    ]
    
    for amount, label in packages:
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"diamonds_buy_{amount}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к алмазам",
            callback_data="balance_diamonds"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("diamonds_buy_"))
async def callback_diamonds_buy_process(callback: CallbackQuery):
    """Обработка покупки алмазов"""
    
    try:
        amount = int(callback.data.replace("diamonds_buy_", ""))
    except:
        await callback.answer("Ошибка обработки запроса", show_alert=True)
        return
    
    telegram_id = callback.from_user.id
    
    await callback.message.edit_text(
        f"💎 <b>ПОКУПКА {amount} АЛМАЗОВ</b>\n\n"
        f"Для покупки {amount} алмазов вам потребуется {amount} звезд.\n\n"
        f"<i>Покупка алмазов за звезды будет реализована после подключения платежной системы.</i>\n\n"
        f"📞 По вопросам покупки алмазов обращайтесь к @gromfit_support",
        parse_mode="HTML"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="diamonds_buy"
        )
    )
    
    await callback.message.answer(
        "👇",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "diamonds_withdraw")
async def callback_diamonds_withdraw(callback: CallbackQuery):
    """Вывод алмазов в звезды"""
    
    telegram_id = callback.from_user.id
    
    # Получаем баланс
    balance_info = diamond_system.get_balance(telegram_id)
    if "error" in balance_info:
        await callback.answer(balance_info['error'], show_alert=True)
        return
    
    balance = balance_info['balance']
    min_withdrawal = diamond_system.MIN_WITHDRAWAL
    
    if balance < min_withdrawal:
        await callback.answer(
            f"❌ Минимальная сумма вывода: {min_withdrawal}💎\n"
            f"Ваш баланс: {balance_info['formatted_balance']}",
            show_alert=True
        )
        return
    
    text = (
        f"💎 <b>ВЫВОД АЛМАЗОВ В ЗВЕЗДЫ</b>\n\n"
        f"💰 <b>Доступно для вывода:</b> {balance_info['formatted_balance']}\n"
        f"⭐️ <b>Минимальная сумма:</b> {min_withdrawal}💎\n"
        f"💸 <b>Комиссия:</b> 10%\n\n"
        
        f"<b>Способы получения:</b>\n\n"
        f"1. <b>Баланс Telegram Stars</b>\n"
        f"   • Моментальное зачисление\n"
        f"   • Без дополнительных комиссий\n\n"
        
        f"👇 <b>Выберите сумму для вывода:</b>"
    )
    
    builder = InlineKeyboardBuilder()
    
    # Рекомендуемые суммы вывода
    suggested_amounts = [100, 500, 1000, 5000]
    
    for amount in suggested_amounts:
        if balance >= amount:
            # Рассчитываем сумму после комиссии
            fee = amount * 0.10
            net_amount = amount - fee
            
            builder.row(
                InlineKeyboardButton(
                    text=f"💎 Вывести {amount} алмазов → {int(net_amount)}⭐",
                    callback_data=f"diamonds_withdraw_{amount}"
                )
            )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Ввести свою сумму",
            callback_data="diamonds_withdraw_custom"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к алмазам",
            callback_data="balance_diamonds"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("diamonds_withdraw_"))
async def callback_diamonds_withdraw_process(callback: CallbackQuery):
    """Обработка вывода алмазов"""
    
    data = callback.data.replace("diamonds_withdraw_", "")
    
    if data == "custom":
        await callback.answer("Функция ввода своей суммы будет реализована позже", show_alert=True)
        return
    
    try:
        amount = int(data)
    except:
        await callback.answer("Ошибка обработки запроса", show_alert=True)
        return
    
    telegram_id = callback.from_user.id
    
    # Выполняем вывод
    result = diamond_system.withdraw(
        telegram_id=telegram_id,
        amount=amount,
        method="stars",
        description=f"Вывод алмазов в звезды"
    )
    
    if "error" in result:
        await callback.answer(f"❌ {result['error']}", show_alert=True)
    else:
        await callback.message.edit_text(
            f"✅ <b>ЗАЯВКА НА ВЫВОД ПРИНЯТА!</b>\n\n"
            f"💎 <b>Сумма вывода:</b> {result['amount']} алмазов\n"
            f"💸 <b>Комиссия (10%):</b> {result['fee']:.0f} алмазов\n"
            f"⭐️ <b>К зачислению:</b> {result['net_amount']:.0f} звезд\n"
            f"💰 <b>Способ получения:</b> Баланс Telegram Stars\n\n"
            f"⏳ <b>Сроки зачисления:</b> 1-24 часа\n\n"
            f"📞 <b>По всем вопросам:</b> @gromfit_support\n\n"
            f"💎 <b>Новый баланс алмазов:</b> {diamond_system._format_diamonds(result['new_balance']['balance'])}",
            parse_mode="HTML"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="🔙 Назад к алмазам",
                callback_data="balance_diamonds"
            )
        )
        
        await callback.message.answer(
            "👇",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data == "balance_history")
async def callback_balance_history(callback: CallbackQuery):
    """История операций (обе валюты)"""
    
    telegram_id = callback.from_user.id
    
    text = "📋 <b>ВЫБЕРИТЕ ИСТОРИЮ ОПЕРАЦИЙ</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💎 История алмазов",
            callback_data="diamonds_history"
        ),
        InlineKeyboardButton(
            text="💎 История токенов",
            callback_data="tokens_history"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к балансу",
            callback_data="back_balance"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "diamonds_history")
async def callback_diamonds_history(callback: CallbackQuery):
    """История операций алмазов"""
    
    telegram_id = callback.from_user.id
    
    transactions = diamond_system.get_transaction_history(telegram_id, limit=10)
    
    if not transactions:
        text = "📋 <b>ИСТОРИЯ ОПЕРАЦИЙ АЛМАЗОВ</b>\n\n"
        text += "У вас еще нет операций с алмазами.\n"
        text += "Зарабатывайте алмазы в дуэлях или покупайте их за звезды!"
    else:
        text = "📋 <b>ИСТОРИЯ ОПЕРАЦИЙ АЛМАЗОВ</b>\n\n"
        
        for tx in transactions:
            amount_display = tx['formatted_amount']
            date = tx['date'][:16] if tx['date'] else ""
            
            text += (
                f"{tx['icon']} <b>{amount_display}</b>\n"
                f"   {tx['description']}\n"
                f"   <code>{date}</code>\n"
                f"   Баланс: {diamond_system._format_diamonds(tx['balance_after'])}\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 История токенов",
            callback_data="tokens_history"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к истории",
            callback_data="balance_history"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "tokens_history")
async def callback_tokens_history(callback: CallbackQuery):
    """История операций токенов"""
    
    telegram_id = callback.from_user.id
    
    transactions = token_system.get_transaction_history(telegram_id, limit=10)
    
    if not transactions:
        text = "📋 <b>ИСТОРИЯ ОПЕРАЦИЙ ТОКЕНОВ</b>\n\n"
        text += "У вас еще нет операций с токенами.\n"
        text += "Получайте токены за рефералов, ежедневные бонусы и достижения!"
    else:
        text = "📋 <b>ИСТОРИЯ ОПЕРАЦИЙ ТОКЕНОВ</b>\n\n"
        
        for tx in transactions:
            amount_display = tx['formatted_amount']
            date = tx['date'][:16] if tx['date'] else ""
            
            text += (
                f"{tx['icon']} <b>{amount_display}</b>\n"
                f"   {tx['description']}\n"
                f"   <code>{date}</code>\n"
                f"   Баланс: {token_system._format_tokens(tx['balance_after'])}\n\n"
            )
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📋 История алмазов",
            callback_data="diamonds_history"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад к истории",
            callback_data="balance_history"
        )
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# ========== ОБРАБОТЧИКИ НАВИГАЦИИ ==========

@router.callback_query(F.data.startswith("back_"))
async def callback_back_handler(callback: CallbackQuery):
    """Универсальный обработчик кнопки Назад"""
    
    target = callback.data.replace("back_", "")
    
    if target == "main":
        await show_main_menu(callback)
    elif target == "balance":
        await callback_balance(callback)
    else:
        await callback.answer("Навигация не реализована", show_alert=True)

async def show_main_menu(callback: CallbackQuery):
    """Показ главного меню"""
    text = "🏋️‍♂️ <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите действие:"
    
    await callback.message.edit_text(
        text,
        reply_markup=MainKeyboards.get_main_menu(),
        parse_mode="HTML"
    )

# Обработчики для команд в чате
@router.message(F.text == "💰 Баланс")
@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """Команда баланса из чата"""
    # Создаем fake callback для использования существующего кода
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await callback_balance(fake_callback)