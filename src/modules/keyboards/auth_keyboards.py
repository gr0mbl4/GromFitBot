"""
Клавиатуры для модуля авторизации и регистрации
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from src.core.config import REGIONS

class AuthKeyboards:
    """Клавиатуры для регистрации и авторизации"""
    
    @staticmethod
    def get_regions_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура с регионами (основные города)"""
        builder = ReplyKeyboardBuilder()
        
        # Основные города (первые 12 для компактности)
        main_regions = REGIONS[:12]
        
        # Создаем кнопки по 2 в ряд
        for i in range(0, len(main_regions), 2):
            row = main_regions[i:i+2]
            builder.row(*[KeyboardButton(text=city) for city in row])
        
        # Кнопка "Другие города"
        builder.row(KeyboardButton(text="🌍 Другие города"))
        
        # Кнопка отмены
        builder.row(KeyboardButton(text="❌ Отмена регистрации"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True,
            input_field_placeholder="Выберите регион или введите название"
        )
    
    @staticmethod
    def get_all_regions_keyboard() -> ReplyKeyboardMarkup:
        """Полная клавиатура со всеми регионами"""
        builder = ReplyKeyboardBuilder()
        
        # Разбиваем на строки по 3 города
        for i in range(0, len(REGIONS), 3):
            row = REGIONS[i:i+3]
            builder.row(*[KeyboardButton(text=city) for city in row])
        
        # Кнопка "Назад к основным"
        builder.row(KeyboardButton(text="⬅️ Назад к основным городам"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура с кнопкой отмены"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="❌ Отмена"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )
    
    @staticmethod
    def get_skip_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура с кнопкой пропуска"""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="⏭️ Пропустить"),
            KeyboardButton(text="❌ Отмена")
        )
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )
    
    @staticmethod
    def get_start_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура для команды /start"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="🚀 Начать регистрацию"))
        builder.row(KeyboardButton(text="ℹ️ О проекте"))
        builder.row(KeyboardButton(text="📋 Правила"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )
    
    @staticmethod
    def get_registration_confirmation() -> InlineKeyboardMarkup:
        """Инлайн клавиатура для подтверждения регистрации"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_registration"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_registration")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_terms_acceptance() -> InlineKeyboardMarkup:
        """Инлайн клавиатура для принятия правил"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✅ Принимаю правила", callback_data="accept_terms"),
            InlineKeyboardButton(text="❌ Не принимаю", callback_data="reject_terms")
        )
        
        builder.row(
            InlineKeyboardButton(text="📄 Прочитать правила", url="https://t.me/gromfitbot/rules")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура для возврата в меню"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="⬅️ Вернуться в меню"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )