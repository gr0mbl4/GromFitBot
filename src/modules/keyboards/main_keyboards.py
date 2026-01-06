"""
Клавиатуры главного меню и кнопок под чатом
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

class MainKeyboards:
    """Клавиатуры главного меню и кнопок под чатом"""
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """Главное меню - ПОКАЗЫВАЕТСЯ ПОД СООБЩЕНИЕМ, исчезает после выбора"""
        builder = ReplyKeyboardBuilder()
        
        # Крупные кнопки (по 1 в ряд)
        builder.row(KeyboardButton(text="🏋️‍♂️ Профиль"))
        builder.row(KeyboardButton(text="⚔️ Дуэли"))
        builder.row(KeyboardButton(text="📊 Тренировки"))
        builder.row(KeyboardButton(text="🎯 Достижения"))
        builder.row(KeyboardButton(text="💰 Магазин"))
        builder.row(KeyboardButton(text="👥 Рефералы"))
        builder.row(KeyboardButton(text="🎁 Ежедневный бонус"))
        
        # БЕЗ persistent=True - клавиатура показывается под сообщением
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_bottom_keyboard() -> ReplyKeyboardMarkup:
        """Кнопки под чатом - ВСЕГДА ВИДНЫ (4 основные кнопки)"""
        builder = ReplyKeyboardBuilder()
        
        # Первый ряд
        builder.row(
            KeyboardButton(text="🏋️‍♂️ Профиль"),
            KeyboardButton(text="📝 Записать результат")
        )
        
        # Второй ряд
        builder.row(
            KeyboardButton(text="💰 Магазин"),
            KeyboardButton(text="🏠 Главное меню")
        )
        
        # persistent=True ТОЛЬКО ЗДЕСЬ - эти кнопки всегда видны
        return builder.as_markup(resize_keyboard=True, persistent=True)
    
    @staticmethod
    def get_profile_inline_keyboard() -> InlineKeyboardBuilder:
        """Инлайн клавиатура для профиля"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="profile_stats")
        builder.button(text="📈 Прогресс", callback_data="profile_progress")
        builder.button(text="⚙️ Настройки", callback_data="profile_settings")
        builder.button(text="🏠 Главное меню", callback_data="profile_back_to_menu")
        builder.adjust(2, 1, 1)
        return builder
    
    @staticmethod
    def get_back_to_menu_inline_keyboard() -> InlineKeyboardBuilder:
        """Инлайн клавиатура с кнопкой Главное меню"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Главное меню", callback_data="back_to_main_menu")
        return builder
    
    @staticmethod
    def get_remove_keyboard() -> ReplyKeyboardRemove:
        """Удаление клавиатуры"""
        return ReplyKeyboardRemove()