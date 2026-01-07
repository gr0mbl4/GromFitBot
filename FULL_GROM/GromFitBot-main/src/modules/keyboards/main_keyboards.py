"""
Полный модуль клавиатур для GromFitBot
Содержит все клавиатуры для навигации и взаимодействия
"""

from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import Optional, List, Tuple, Dict, Any

class MainKeyboards:
    """Основные клавиатуры бота - полный набор"""
    
    # ==================== REPLY КЛАВИАТУРЫ (ОСНОВНЫЕ МЕНЮ) ====================
    
    @staticmethod
    def get_main_menu() -> ReplyKeyboardMarkup:
        """
        Главное меню - ПОКАЗЫВАЕТСЯ ПОД СООБЩЕНИЕМ
        НЕ ДОЛЖНО ИМЕТЬ persistent=True
        """
        builder = ReplyKeyboardBuilder()
        
        # Первый ряд
        builder.row(
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="📊 Статистика")
        )
        
        # Второй ряд
        builder.row(
            KeyboardButton(text="🤼 Дуэли"),
            KeyboardButton(text="🎯 Достижения")
        )
        
        # Третий ряд
        builder.row(
            KeyboardButton(text="📈 Топы"),
            KeyboardButton(text="🤝 Рефералы")
        )
        
        # Четвертый ряд
        builder.row(
            KeyboardButton(text="🎁 Бонусы"),
            KeyboardButton(text="🛒 Магазин")
        )
        
        # Важно: БЕЗ persistent=True - показывается только под текущим сообщением
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=False,
            input_field_placeholder="Выберите раздел..."
        )
    
    @staticmethod
    def get_bottom_keyboard() -> ReplyKeyboardMarkup:
        """
        Кнопки под чатом - ВСЕГДА ВИДНЫ
        ДОЛЖНО ИМЕТЬ persistent=True
        """
        builder = ReplyKeyboardBuilder()
        
        builder.row(
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="📝 Записать результат")
        )
        
        builder.row(
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="🏠 Главное меню")
        )
        
        # Важно: С persistent=True для постоянного отображения под чатом
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=False,
            persistent=True,
            input_field_placeholder="Быстрые действия..."
        )
    
    @staticmethod
    def get_registration_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура для процесса регистрации"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="Взять из Telegram"))
        builder.row(KeyboardButton(text="Пропустить"))
        
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура с кнопкой отмены"""
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="❌ Отмена"))
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    
    # ==================== INLINE КЛАВИАТУРЫ (ПОДМЕНЮ И ДЕЙСТВИЯ) ====================
    
    @staticmethod
    def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
        """Инлайн-кнопка для возврата в главное меню"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Главное меню", callback_data="back_to_main")
        return builder.as_markup()
    
    @staticmethod
    def get_back_keyboard(target: str) -> InlineKeyboardMarkup:
        """Инлайн-кнопка 'Назад' для указанной цели"""
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data=f"back_to_{target}")
        builder.button(text="🏠 Главное меню", callback_data="back_to_main")
        return builder.as_markup()
    
    @staticmethod
    def get_navigation_keyboard(back_target: str, extra_buttons: List[Tuple[str, str]] = None) -> InlineKeyboardMarkup:
        """
        Клавиатура навигации (Назад + Главное меню + дополнительные кнопки)
        
        Args:
            back_target: Цель для кнопки "Назад"
            extra_buttons: Дополнительные кнопки [(текст, callback_data), ...]
        """
        builder = InlineKeyboardBuilder()
        
        # Основные кнопки навигации
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_{back_target}"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        # Добавляем дополнительные кнопки если есть
        if extra_buttons:
            for text, callback_data in extra_buttons:
                builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
        
        return builder.as_markup()
    
    @staticmethod
    def get_profile_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для профиля пользователя"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats"),
            InlineKeyboardButton(text="🎯 Достижения", callback_data="profile_achievements")
        )
        
        builder.row(
            InlineKeyboardButton(text="💳 Баланс", callback_data="profile_balance"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="profile_settings")
        )
        
        builder.row(
            InlineKeyboardButton(text="📈 Тренировки", callback_data="profile_trainings"),
            InlineKeyboardButton(text="🤼 Дуэли", callback_data="profile_duels")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_profile_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_referrals_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для реферальной системы"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data="referral_stats"),
            InlineKeyboardButton(text="🏆 Лидеры", callback_data="referral_leaders")
        )
        
        builder.row(
            InlineKeyboardButton(text="📋 Список рефералов", callback_data="referral_list"),
            InlineKeyboardButton(text="🎁 Бонусы", callback_data="referral_bonuses")
        )
        
        builder.row(
            InlineKeyboardButton(text="📢 Поделиться", callback_data="referral_share"),
            InlineKeyboardButton(text="ℹ️ Правила", callback_data="referral_rules")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_referrals_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_shop_categories_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура категорий магазина"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="💎 Премиум", callback_data="shop_category_premium"),
            InlineKeyboardButton(text="🎨 Оформление", callback_data="shop_category_design")
        )
        
        builder.row(
            InlineKeyboardButton(text="⚡️ Бустеры", callback_data="shop_category_boosters"),
            InlineKeyboardButton(text="🎁 Подарки", callback_data="shop_category_gifts")
        )
        
        builder.row(
            InlineKeyboardButton(text="🛠️ Инструменты", callback_data="shop_category_tools"),
            InlineKeyboardButton(text="🎭 Эмоции", callback_data="shop_category_emotions")
        )
        
        builder.row(
            InlineKeyboardButton(text="📦 Все товары", callback_data="shop_category_all"),
            InlineKeyboardButton(text="🛒 Мои покупки", callback_data="shop_my_purchases")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_shop_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_shop_items_keyboard(category: str, items: List[Dict[str, Any]], 
                               page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
        """Клавиатура товаров магазина с пагинацией"""
        builder = InlineKeyboardBuilder()
        
        # Вычисляем индексы для текущей страницы
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        # Добавляем кнопки товаров
        for item in page_items:
            builder.row(
                InlineKeyboardButton(
                    text=f"{item.get('icon', '🛒')} {item['name']} - {item['price_tokens']} токенов",
                    callback_data=f"shop_item_{item['item_id']}"
                )
            )
        
        # Добавляем пагинацию если нужно
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            pagination_buttons = []
            
            if page > 0:
                pagination_buttons.append(
                    InlineKeyboardButton(text="◀️", callback_data=f"shop_page_{category}_{page-1}")
                )
            
            pagination_buttons.append(
                InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="shop_page_current")
            )
            
            if page < total_pages - 1:
                pagination_buttons.append(
                    InlineKeyboardButton(text="▶️", callback_data=f"shop_page_{category}_{page+1}")
                )
            
            builder.row(*pagination_buttons)
        
        # Кнопки навигации
        builder.row(
            InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="back_to_shop_categories"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_shop_item_detail_keyboard(item_id: str, price_tokens: float, 
                                     user_balance: float) -> InlineKeyboardMarkup:
        """Клавиатура деталей товара"""
        builder = InlineKeyboardBuilder()
        
        # Основные действия
        builder.row(
            InlineKeyboardButton(text="🛒 Купить", callback_data=f"shop_buy_{item_id}"),
            InlineKeyboardButton(text="📦 Купить x3", callback_data=f"shop_buy3_{item_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="📦 Купить x5", callback_data=f"shop_buy5_{item_id}"),
            InlineKeyboardButton(text="🎁 Подарить", callback_data=f"shop_gift_{item_id}")
        )
        
        # Информация о балансе
        if user_balance < price_tokens:
            builder.row(
                InlineKeyboardButton(
                    text=f"❌ Недостаточно токенов (нужно {price_tokens})",
                    callback_data="shop_insufficient_funds"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text=f"✅ Достаточно токенов (есть {user_balance})",
                    callback_data="shop_sufficient_funds"
                )
            )
        
        # Навигация
        builder.row(
            InlineKeyboardButton(text="◀️ Назад к товарам", callback_data="back_to_shop_items"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_bonus_keyboard(can_claim: bool, streak: int = 0) -> InlineKeyboardMarkup:
        """Клавиатура для бонусов"""
        builder = InlineKeyboardBuilder()
        
        if can_claim:
            builder.row(
                InlineKeyboardButton(
                    text="🎁 Получить ежедневный бонус",
                    callback_data="bonus_claim_daily"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="⏳ Бонус уже получен сегодня",
                    callback_data="bonus_already_claimed"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="📊 Статистика бонусов", callback_data="bonus_stats"),
            InlineKeyboardButton(text="🏆 Рекорды", callback_data="bonus_records")
        )
        
        if streak > 0:
            builder.row(
                InlineKeyboardButton(
                    text=f"🔥 Серия дней: {streak}",
                    callback_data="bonus_streak_info"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_bonus_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_duels_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для дуэлей"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="⚔️ Бросить вызов", callback_data="duel_challenge"),
            InlineKeyboardButton(text="🛡️ Принять вызов", callback_data="duel_accept")
        )
        
        builder.row(
            InlineKeyboardButton(text="📋 Активные дуэли", callback_data="duel_active"),
            InlineKeyboardButton(text="📊 История дуэлей", callback_data="duel_history")
        )
        
        builder.row(
            InlineKeyboardButton(text="🏆 Мои победы", callback_data="duel_wins"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="duel_stats")
        )
        
        builder.row(
            InlineKeyboardButton(text="📋 Правила", callback_data="duel_rules"),
            InlineKeyboardButton(text="🎯 Упражнения", callback_data="duel_exercises")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_duels_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_achievements_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для достижений"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🏆 Все достижения", callback_data="achievements_all"),
            InlineKeyboardButton(text="🎯 В процессе", callback_data="achievements_in_progress")
        )
        
        builder.row(
            InlineKeyboardButton(text="📊 По категориям", callback_data="achievements_categories"),
            InlineKeyboardButton(text="🏅 Редкие", callback_data="achievements_rare")
        )
        
        builder.row(
            InlineKeyboardButton(text="📈 Прогресс", callback_data="achievements_progress"),
            InlineKeyboardButton(text="🎁 Награды", callback_data="achievements_rewards")
        )
        
        builder.row(
            InlineKeyboardButton(text="🏆 Последние", callback_data="achievements_recent"),
            InlineKeyboardButton(text="⭐️ Избранные", callback_data="achievements_favorite")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_achievements_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_tops_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура для топов"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🥇 По токенам", callback_data="top_tokens"),
            InlineKeyboardButton(text="🤝 По рефералам", callback_data="top_referrals")
        )
        
        builder.row(
            InlineKeyboardButton(text="💪 По тренировкам", callback_data="top_trainings"),
            InlineKeyboardButton(text="🏆 По победам", callback_data="top_wins")
        )
        
        builder.row(
            InlineKeyboardButton(text="📈 По очкам", callback_data="top_points"),
            InlineKeyboardButton(text="🎯 По достижениям", callback_data="top_achievements")
        )
        
        builder.row(
            InlineKeyboardButton(text="🔥 По активности", callback_data="top_activity"),
            InlineKeyboardButton(text="⭐️ По уровню", callback_data="top_level")
        )
        
        builder.row(
            InlineKeyboardButton(text="📊 Общий рейтинг", callback_data="top_overall"),
            InlineKeyboardButton(text="📋 Мое место", callback_data="top_my_position")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_tops_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_confirmation_keyboard(action: str, confirm_text: str = "✅ Подтвердить", 
                                 cancel_text: str = "❌ Отменить") -> InlineKeyboardMarkup:
        """Клавиатура подтверждения действия"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text=confirm_text, callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text=cancel_text, callback_data=f"cancel_{action}")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_settings_keyboard() -> InlineKeyboardMarkup:
        """Клавиатура настроек"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton(text="🎨 Тема", callback_data="settings_theme")
        )
        
        builder.row(
            InlineKeyboardButton(text="🌐 Язык", callback_data="settings_language"),
            InlineKeyboardButton(text="🔒 Безопасность", callback_data="settings_security")
        )
        
        builder.row(
            InlineKeyboardButton(text="📊 Конфиденциальность", callback_data="settings_privacy"),
            InlineKeyboardButton(text="🔄 Синхронизация", callback_data="settings_sync")
        )
        
        builder.row(
            InlineKeyboardButton(text="🗑️ Очистить данные", callback_data="settings_clear"),
            InlineKeyboardButton(text="📋 Экспорт данных", callback_data="settings_export")
        )
        
        builder.row(
            InlineKeyboardButton(text="ℹ️ О боте", callback_data="settings_about"),
            InlineKeyboardButton(text="🆘 Помощь", callback_data="settings_help")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_yes_no_keyboard(yes_callback: str, no_callback: str, 
                           yes_text: str = "✅ Да", no_text: str = "❌ Нет") -> InlineKeyboardMarkup:
        """Клавиатура Да/Нет"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text=yes_text, callback_data=yes_callback),
            InlineKeyboardButton(text=no_text, callback_data=no_callback)
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_list_keyboard(items: List[Tuple[str, str]], 
                         items_per_row: int = 2) -> InlineKeyboardMarkup:
        """Клавиатура для списка элементов"""
        builder = InlineKeyboardBuilder()
        
        for i in range(0, len(items), items_per_row):
            row_items = items[i:i + items_per_row]
            buttons = [
                InlineKeyboardButton(text=text, callback_data=callback_data)
                for text, callback_data in row_items
            ]
            builder.row(*buttons)
        
        return builder.as_markup()
    
    @staticmethod
    def get_pagination_keyboard(current_page: int, total_pages: int, 
                               callback_prefix: str, extra_buttons: List[Tuple[str, str]] = None) -> InlineKeyboardMarkup:
        """Клавиатура пагинации"""
        builder = InlineKeyboardBuilder()
        
        # Кнопки пагинации
        pagination_buttons = []
        
        if current_page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(text="◀️", callback_data=f"{callback_prefix}_{current_page-1}")
            )
        
        pagination_buttons.append(
            InlineKeyboardButton(text=f"{current_page+1}/{total_pages}", callback_data=f"{callback_prefix}_current")
        )
        
        if current_page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(text="▶️", callback_data=f"{callback_prefix}_{current_page+1}")
            )
        
        builder.row(*pagination_buttons)
        
        # Дополнительные кнопки
        if extra_buttons:
            for text, callback_data in extra_buttons:
                builder.row(InlineKeyboardButton(text=text, callback_data=callback_data))
        
        return builder.as_markup()

class AuthKeyboards:
    """Клавиатуры для авторизации и регистрации"""
    
    @staticmethod
    def get_username_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура с кнопкой имени пользователя Telegram"""
        builder = ReplyKeyboardBuilder()
        
        # Кнопка с именем пользователя (если есть)
        builder.row(KeyboardButton(
            text="Взять из Telegram",
            request_contact=False
        ))
        
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_region_selection_keyboard(regions: List[str]) -> ReplyKeyboardMarkup:
        """Клавиатура для выбора региона"""
        builder = ReplyKeyboardBuilder()
        
        # Добавляем кнопки с регионами (по 2 в ряд)
        for i in range(0, len(regions), 2):
            row_regions = regions[i:i+2]
            buttons = [KeyboardButton(text=region) for region in row_regions]
            builder.row(*buttons)
        
        # Кнопка "Другой город"
        builder.row(KeyboardButton(text="🏙️ Другой город"))
        
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_registration_complete_keyboard() -> ReplyKeyboardMarkup:
        """Клавиатура после завершения регистрации"""
        builder = ReplyKeyboardBuilder()
        
        builder.row(KeyboardButton(text="🎉 Начать использовать бота!"))
        
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

class AdminKeyboards:
    """Клавиатуры для администраторов"""
    
    @staticmethod
    def get_admin_main_menu() -> InlineKeyboardMarkup:
        """Главное меню администратора"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        )
        
        builder.row(
            InlineKeyboardButton(text="💰 Экономика", callback_data="admin_economy"),
            InlineKeyboardButton(text="🛠️ Техническое", callback_data="admin_technical")
        )
        
        builder.row(
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
        )
        
        builder.row(
            InlineKeyboardButton(text="🔧 Управление БД", callback_data="admin_database"),
            InlineKeyboardButton(text="📈 Мониторинг", callback_data="admin_monitoring")
        )
        
        builder.row(
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main"),
            InlineKeyboardButton(text="🚪 Выход", callback_data="admin_logout")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def get_user_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
        """Клавиатура управления пользователем"""
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text="👁️ Просмотр", callback_data=f"admin_view_user_{user_id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_user_{user_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="💰 Изменить баланс", callback_data=f"admin_edit_balance_{user_id}"),
            InlineKeyboardButton(text="🎁 Наградить", callback_data=f"admin_reward_user_{user_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="⚠️ Предупредить", callback_data=f"admin_warn_user_{user_id}"),
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_ban_user_{user_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_delete_user_{user_id}"),
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"admin_user_stats_{user_id}")
        )
        
        builder.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_users"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")
        )
        
        return builder.as_markup()