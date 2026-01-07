"""
Клавиатуры для процесса регистрации (упрощенные)
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

class AuthKeyboards:
    """Клавиатуры для аутентификации"""
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура только с кнопкой отмены"""
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="❌ Отмена регистрации"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура Да/Нет"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="✅ Да"))
        builder.row(KeyboardButton(text="❌ Нет"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_main_regions_keyboard() -> ReplyKeyboardMarkup:
        """Основные регионы (только текст, без кнопок)"""
        # Эта функция теперь возвращает пустую клавиатуру
        # так как мы перешли на ручной ввод
        builder = ReplyKeyboardBuilder()
        return builder.as_markup(resize_keyboard=True, selective=True)