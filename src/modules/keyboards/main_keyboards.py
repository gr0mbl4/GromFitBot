"""
Клавиатуры для главного меню и кнопок под чатом
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

class MainKeyboards:
    """Клавиатуры главного меню и кнопок под чатом"""
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Главное меню (крупные кнопки, по одной в ряд)"""
        builder = ReplyKeyboardBuilder()
        
        # Крупные кнопки (по 1 в ряд)
        builder.row(KeyboardButton(text="🏋️‍♂️ ПРОФИЛЬ"))
        builder.row(KeyboardButton(text="⚔️ ДУЭЛИ"))
        builder.row(KeyboardButton(text="📊 ТРЕНИРОВКИ"))
        builder.row(KeyboardButton(text="🎯 ДОСТИЖЕНИЯ"))
        builder.row(KeyboardButton(text="💰 МАГАЗИН"))
        builder.row(KeyboardButton(text="👥 РЕФЕРАЛЫ"))
        builder.row(KeyboardButton(text="🎁 ЕЖЕДНЕВНЫЙ БОНУС"))
        
        return builder.as_markup(resize_keyboard=True, persistent=True)
    
    @staticmethod
    def get_bottom_keyboard() -> ReplyKeyboardMarkup:
        """Кнопки под чатом (всегда видны)"""
        builder = ReplyKeyboardBuilder()
        
        # Первый ряд
        builder.row(
            KeyboardButton(text="👤 Личный кабинет"),
            KeyboardButton(text="📝 Записать результат")
        )
        
        # Второй ряд
        builder.row(
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="🏠 Главное меню")
        )
        
        return builder.as_markup(
            resize_keyboard=True,
            persistent=True,
            input_field_placeholder="Выберите действие или используйте меню"
        )
    
    @staticmethod
    def get_inline_main_menu() -> InlineKeyboardMarkup:
        """Инлайн меню для команд"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="⚔️ Дуэли", callback_data="duels")
        )
        
        builder.row(
            InlineKeyboardButton(text="📊 Тренировки", callback_data="workouts"),
            InlineKeyboardButton(text="🎯 Достижения", callback_data="achievements")
        )
        
        builder.row(
            InlineKeyboardButton(text="💰 Магазин", callback_data="shop"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="referrals")
        )
        
        builder.row(
            InlineKeyboardButton(text="🎁 Ежедневный бонус", callback_data="daily_bonus")
        )
        
        return builder.as_markup()