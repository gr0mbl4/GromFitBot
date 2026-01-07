"""
Клавиатуры для авторизации и главного меню (только InlineKeyboard)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class AuthKeyboards:
    """Клавиатуры для процесса регистрации"""
    
    @staticmethod
    def get_nickname_keyboard(first_name: str, last_name: str = "") -> InlineKeyboardMarkup:
        """Клавиатура для выбора никнейма"""
        builder = InlineKeyboardBuilder()
        
        full_name = f"{first_name} {last_name}".strip()
        
        if full_name:
            builder.row(
                InlineKeyboardButton(
                    text=f"👤 {full_name}",
                    callback_data=f"nickname_{full_name}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(
                text="✏️ Ввести свой вариант",
                callback_data="nickname_custom"
            )
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_region_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для выбора региона"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(
                text="⏩ Пропустить регион",
                callback_data="region_skip"
            )
        )
        
        return builder.as_markup()

class MainKeyboards:
    """Главное меню бота (только InlineKeyboard)"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Главное меню бота"""
        builder = InlineKeyboardBuilder()
        
        # Основные кнопки (по 2 в ряд)
        builder.row(
            InlineKeyboardButton(text="⚔️ Дуэли", callback_data="menu_duels"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
        )
        builder.row(
            InlineKeyboardButton(text="🏆 Достижения", callback_data="menu_achievements"),
            InlineKeyboardButton(text="💰 Баланс", callback_data="menu_balance")
        )
        builder.row(
            InlineKeyboardButton(text="👤 Профиль", callback_data="menu_profile"),
            InlineKeyboardButton(text="👥 Рефералы", callback_data="menu_referrals")
        )
        
        # Дополнительные кнопки
        builder.row(
            InlineKeyboardButton(text="🛒 Магазин", callback_data="menu_shop"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="menu_help")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_back_keyboard(back_to: str = "main") -> InlineKeyboardMarkup:
        """Клавиатура с кнопкой 'Назад'"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_{back_to}")
        )
        return builder.as_markup()
    
    @staticmethod
    def get_profile_keyboard() -> InlineKeyboardMarkup:
        """Инлайн клавиатура для профиля"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="profile_edit"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")
        )
        builder.row(
            InlineKeyboardButton(text="🔗 Поделиться", callback_data="profile_share"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="profile_settings")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")
        )
        
        return builder.as_markup()