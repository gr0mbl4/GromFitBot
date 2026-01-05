"""
Клавиатуры для главного меню и кнопок под чатом
Исправленная версия с правильным разделением:
- Главное меню: показывается под сообщением, исчезает после выбора
- Кнопки под чатом: всегда видны (4 основные кнопки)
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

class MainKeyboards:
    """Клавиатуры главного меню и кнопок под чатом"""
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """
        Главное меню - ПОКАЗЫВАЕТСЯ ПОД СООБЩЕНИЕМ
        Исчезает после выбора пункта меню
        """
        builder = ReplyKeyboardBuilder()
        
        # Крупные кнопки (по 1 в ряд)
        builder.row(KeyboardButton(text="🏋️‍♂️ ПРОФИЛЬ"))
        builder.row(KeyboardButton(text="⚔️ ДУЭЛИ"))
        builder.row(KeyboardButton(text="📊 ТРЕНИРОВКИ"))
        builder.row(KeyboardButton(text="🎯 ДОСТИЖЕНИЯ"))
        builder.row(KeyboardButton(text="💰 МАГАЗИН"))
        builder.row(KeyboardButton(text="👥 РЕФЕРАЛЫ"))
        builder.row(KeyboardButton(text="🎁 ЕЖЕДНЕВНЫЙ БОНУС"))
        
        # БЕЗ persistent=True - клавиатура показывается под сообщением и исчезает после выбора
        return builder.as_markup(
            resize_keyboard=True,
            selective=True,  # Показывать только тому, кто вызвал
            input_field_placeholder="Выберите пункт меню"
        )
    
    @staticmethod
    def get_bottom_keyboard() -> ReplyKeyboardMarkup:
        """
        Кнопки под чатом - ВСЕГДА ВИДНЫ
        Эти 4 кнопки остаются всегда внизу чата
        """
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
        
        # persistent=True ЗДЕСЬ - эти кнопки всегда видны под чатом
        return builder.as_markup(
            resize_keyboard=True,
            persistent=True,  # ЭТИ КНОПКИ ВСЕГДА ВИДНЫ ПОД ЧАТОМ
            selective=True,
            input_field_placeholder="Выберите действие или используйте меню"
        )
    
    @staticmethod
    def get_back_only() -> ReplyKeyboardMarkup:
        """Только кнопка Назад (для навигации)"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(
            resize_keyboard=True,
            selective=True
        )
    
    @staticmethod
    def get_duels_menu() -> ReplyKeyboardMarkup:
        """Меню дуэлей"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="⚔️ Создать дуэль"))
        builder.row(KeyboardButton(text="📋 Мои дуэли"))
        builder.row(KeyboardButton(text="🏆 Активные дуэли"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_trainings_menu() -> ReplyKeyboardMarkup:
        """Меню тренировок"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="➕ Добавить тренировку"))
        builder.row(KeyboardButton(text="📊 Статистика"))
        builder.row(KeyboardButton(text="📅 Календарь"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_achievements_menu() -> ReplyKeyboardMarkup:
        """Меню достижений"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="🏆 Все достижения"))
        builder.row(KeyboardButton(text="✅ Полученные"))
        builder.row(KeyboardButton(text="🎯 Цели"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_profile_menu() -> ReplyKeyboardMarkup:
        """Меню профиля"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="📊 Статистика"))
        builder.row(KeyboardButton(text="🎖️ Награды"))
        builder.row(KeyboardButton(text="⚙️ Настройки"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_shop_menu() -> ReplyKeyboardMarkup:
        """Меню магазина"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="🛍️ Товары"))
        builder.row(KeyboardButton(text="💰 Пополнить баланс"))
        builder.row(KeyboardButton(text="💳 История покупок"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_referrals_menu() -> ReplyKeyboardMarkup:
        """Меню рефералов"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="📋 Список рефералов"))
        builder.row(KeyboardButton(text="🏆 Таблица лидеров"))
        builder.row(KeyboardButton(text="📤 Поделиться ссылкой"))
        builder.row(KeyboardButton(text="⬅️ Назад"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)
    
    @staticmethod
    def get_clear_keyboard() -> ReplyKeyboardMarkup:
        """Пустая клавиатура (скрывает все кнопки)"""
        return ReplyKeyboardRemove()
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Только кнопка Отмена"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="❌ Отмена"))
        
        return builder.as_markup(resize_keyboard=True, selective=True)