"""
Работа с базой данных SQLite
Полная версия с поддержкой всех функций проекта
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from src.core.config import Config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.conn = None
        self.db_path = Config.DATABASE_PATH
        
        # Создаем директорию для базы данных если ее нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def connect(self) -> sqlite3.Connection:
        """Установка соединения с базой данных"""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
                logger.debug(f"Соединение с БД установлено: {self.db_path}")
            return self.conn
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Соединение с БД закрыто")
    
    def initialize(self):
        """Инициализация базы данных (создание всех таблиц)"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            logger.info("🔄 Инициализация структуры базы данных...")
            
            # 1. Таблица пользователей (основная)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    registration_number TEXT UNIQUE NOT NULL,
                    username TEXT,
                    nickname TEXT NOT NULL,
                    region TEXT DEFAULT 'Не указан',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referrer_id INTEGER,
                    referrals_count INTEGER DEFAULT 0,
                    balance_tokens DECIMAL(15,2) DEFAULT 50.00,
                    balance_diamonds DECIMAL(15,2) DEFAULT 0.00,
                    last_bonus_claim TIMESTAMP,
                    achievements_count INTEGER DEFAULT 0,
                    total_trainings INTEGER DEFAULT 0,
                    total_duels INTEGER DEFAULT 0,
                    duels_won INTEGER DEFAULT 0,
                    total_points INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    last_training_date TIMESTAMP,
                    daily_streak INTEGER DEFAULT 0,
                    last_streak_date DATE,
                    is_premium BOOLEAN DEFAULT 0,
                    premium_until TIMESTAMP,
                    notifications_enabled BOOLEAN DEFAULT 1,
                    language TEXT DEFAULT 'ru',
                    theme TEXT DEFAULT 'light'
                )
            ''')
            logger.debug("✅ Таблица 'users' создана/проверена")
            
            # 2. Таблица реферальных связей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bonus_paid BOOLEAN DEFAULT 0,
                    referrer_bonus_paid DECIMAL(15,2) DEFAULT 0,
                    referred_bonus_paid DECIMAL(15,2) DEFAULT 0,
                    UNIQUE(referrer_id, referred_id),
                    FOREIGN KEY (referrer_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                    FOREIGN KEY (referred_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'referral_connections' создана/проверена")
            
            # 3. Таблица достижений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT DEFAULT '🏆',
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    progress INTEGER DEFAULT 0,
                    required_progress INTEGER DEFAULT 1,
                    completed BOOLEAN DEFAULT 0,
                    reward_tokens DECIMAL(15,2) DEFAULT 0.00,
                    reward_diamonds DECIMAL(15,2) DEFAULT 0.00,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'achievements' создана/проверена")
            
            # 4. Таблица транзакций
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    currency TEXT DEFAULT 'tokens',
                    description TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    balance_before DECIMAL(15,2),
                    balance_after DECIMAL(15,2),
                    reference_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'transactions' создана/проверена")
            
            # 5. Таблица тренировок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trainings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    training_type TEXT NOT NULL,
                    duration_minutes INTEGER,
                    calories_burned INTEGER,
                    exercises_count INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    training_date DATE DEFAULT CURRENT_DATE,
                    is_completed BOOLEAN DEFAULT 1,
                    rating INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'trainings' создана/проверена")
            
            # 6. Таблица дуэлей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS duels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    opponent_id INTEGER,
                    exercise_type TEXT NOT NULL,
                    target_value INTEGER NOT NULL,
                    stake_tokens DECIMAL(15,2) DEFAULT 0.00,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    winner_id INTEGER,
                    creator_result INTEGER,
                    opponent_result INTEGER,
                    proof_photo_id TEXT,
                    proof_video_id TEXT,
                    auto_close_at TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                    FOREIGN KEY (opponent_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                    FOREIGN KEY (winner_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'duels' создана/проверена")
            
            # 7. Таблица магазина (товары)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shop_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price_tokens DECIMAL(15,2) DEFAULT 0.00,
                    price_diamonds DECIMAL(15,2) DEFAULT 0.00,
                    item_type TEXT NOT NULL,
                    icon TEXT DEFAULT '🛍️',
                    duration_days INTEGER,
                    effect_description TEXT,
                    stock_quantity INTEGER DEFAULT -1,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.debug("✅ Таблица 'shop_items' создана/проверена")
            
            # 8. Таблица покупок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    total_price_tokens DECIMAL(15,2) DEFAULT 0.00,
                    total_price_diamonds DECIMAL(15,2) DEFAULT 0.00,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'completed',
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES shop_items(id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'purchases' создана/проверена")
            
            # 9. Таблица логов действий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
                )
            ''')
            logger.debug("✅ Таблица 'action_logs' создана/проверена")
            
            # Создаем индексы для оптимизации
            self._create_indexes(cursor)
            
            # Добавляем стандартные товары в магазин
            self._seed_shop_items(cursor)
            
            conn.commit()
            logger.info("✅ Структура базы данных успешно инициализирована")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            raise
        finally:
            self.close()
    
    def _create_indexes(self, cursor):
        """Создание индексов для оптимизации запросов"""
        indexes = [
            ('idx_users_telegram_id', 'users', 'telegram_id'),
            ('idx_users_nickname', 'users', 'nickname'),
            ('idx_users_referrer', 'users', 'referrer_id'),
            ('idx_users_created_at', 'users', 'created_at'),
            ('idx_referral_connections_referrer', 'referral_connections', 'referrer_id'),
            ('idx_referral_connections_referred', 'referral_connections', 'referred_id'),
            ('idx_achievements_user', 'achievements', 'user_id'),
            ('idx_achievements_type', 'achievements', 'achievement_type'),
            ('idx_transactions_user', 'transactions', 'user_id'),
            ('idx_transactions_type', 'transactions', 'transaction_type'),
            ('idx_transactions_date', 'transactions', 'created_at'),
            ('idx_trainings_user', 'trainings', 'user_id'),
            ('idx_trainings_date', 'trainings', 'training_date'),
            ('idx_duels_creator', 'duels', 'creator_id'),
            ('idx_duels_opponent', 'duels', 'opponent_id'),
            ('idx_duels_status', 'duels', 'status'),
            ('idx_purchases_user', 'purchases', 'user_id'),
            ('idx_purchases_item', 'purchases', 'item_id'),
            ('idx_action_logs_user', 'action_logs', 'user_id'),
            ('idx_action_logs_type', 'action_logs', 'action_type')
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})')
                logger.debug(f"✅ Создан индекс: {index_name}")
            except Exception as e:
                logger.error(f"Ошибка создания индекса {index_name}: {e}")
    
    def _seed_shop_items(self, cursor):
        """Заполнение магазина стандартными товарами"""
        try:
            cursor.execute('SELECT COUNT(*) FROM shop_items')
            count = cursor.fetchone()[0]
            
            if count == 0:
                shop_items = [
                    # Токены
                    ('Пакет токенов (100)', 'Начальный пакет токенов', 0, 100, 'tokens_pack', '💰', None, 'Пополнение баланса'),
                    ('Пакет токенов (500)', 'Средний пакет токенов', 0, 450, 'tokens_pack', '💰', None, 'Пополнение баланса со скидкой'),
                    ('Пакет токенов (1000)', 'Большой пакет токенов', 0, 850, 'tokens_pack', '💰', None, 'Пополнение баланса с большой скидкой'),
                    
                    # Премиум статус
                    ('Премиум (7 дней)', 'Премиум статус на 7 дней', 100, 0, 'premium', '👑', 7, 'Доступ к эксклюзивным дуэлям, увеличенные лимиты'),
                    ('Премиум (30 дней)', 'Премиум статус на 30 дней', 350, 0, 'premium', '👑', 30, 'Доступ к эксклюзивным дуэлям, увеличенные лимиты'),
                    ('Премиум (90 дней)', 'Премиум статус на 90 дней', 900, 0, 'premium', '👑', 90, 'Доступ к эксклюзивным дуэлям, увеличенные лимиты'),
                    
                    # Бусты
                    ('Буст энергии (1 день)', '+20% к эффективности тренировок', 50, 0, 'boost', '⚡', 1, 'Увеличение эффективности тренировок'),
                    ('Буст опыта (3 дня)', '+30% опыта за тренировки', 120, 0, 'boost', '📈', 3, 'Ускорение прокачки уровня'),
                    ('Буст удачи (7 дней)', '+15% к шансу победы в дуэлях', 200, 0, 'boost', '🍀', 7, 'Увеличение шансов на победу'),
                    
                    # Внешний вид
                    ('Золотая рамка профиля', 'Эксклюзивная золотая рамка для профиля', 150, 0, 'cosmetic', '🖼️', None, 'Уникальное оформление профиля'),
                    ('Анимационный аватар', 'Анимированный аватар в профиле', 300, 0, 'cosmetic', '🎬', None, 'Выделяющийся аватар'),
                    ('Неоновый никнейм', 'Неоновое свечение никнейма', 250, 0, 'cosmetic', '✨', None, 'Яркий стиль никнейма')
                ]
                
                for name, description, price_tokens, price_diamonds, item_type, icon, duration_days, effect_description in shop_items:
                    cursor.execute('''
                        INSERT INTO shop_items (name, description, price_tokens, price_diamonds, item_type, icon, duration_days, effect_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, description, price_tokens, price_diamonds, item_type, icon, duration_days, effect_description))
                
                logger.info("✅ Магазин заполнен стандартными товарами")
            else:
                logger.debug("✅ Магазин уже содержит товары")
                
        except Exception as e:
            logger.error(f"Ошибка заполнения магазина: {e}")
    
    def get_user(self, telegram_id: int) -> Optional[sqlite3.Row]:
        """Получение пользователя по telegram_id"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
    
    def get_user_by_nickname(self, nickname: str) -> Optional[sqlite3.Row]:
        """Получение пользователя по никнейму"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE nickname = ?', (nickname,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по никнейму: {e}")
            return None
    
    def get_user_by_reg_number(self, reg_number: str) -> Optional[sqlite3.Row]:
        """Получение пользователя по номеру регистрации"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE registration_number = ?', (reg_number,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по номеру регистрации: {e}")
            return None
    
    def create_user(self, telegram_id: int, username: str, nickname: str, 
                    region: str, registration_number: str, referrer_id: int = None):
        """Создание нового пользователя"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Создаем пользователя
            cursor.execute('''
                INSERT INTO users 
                (telegram_id, username, nickname, region, registration_number, referrer_id, balance_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, nickname, region, registration_number, referrer_id, Config.REFERRED_BONUS))
            
            # Если есть реферер, добавляем связь и начисляем бонусы
            if referrer_id:
                try:
                    # Добавляем реферальную связь
                    cursor.execute('''
                        INSERT OR IGNORE INTO referral_connections 
                        (referrer_id, referred_id, referrer_bonus_paid, referred_bonus_paid)
                        VALUES (?, ?, ?, ?)
                    ''', (referrer_id, telegram_id, Config.REFERRER_BONUS, Config.REFERRED_BONUS))
                    
                    # Обновляем счетчик рефералов у реферера
                    cursor.execute('''
                        UPDATE users 
                        SET referrals_count = referrals_count + 1 
                        WHERE telegram_id = ?
                    ''', (referrer_id,))
                    
                    # Начисляем бонус рефереру
                    cursor.execute('''
                        UPDATE users 
                        SET balance_tokens = balance_tokens + ? 
                        WHERE telegram_id = ?
                    ''', (Config.REFERRER_BONUS, referrer_id))
                    
                    # Логируем транзакцию реферера
                    cursor.execute('''
                        INSERT INTO transactions 
                        (user_id, transaction_type, amount, description, balance_before, balance_after)
                        SELECT ?, ?, ?, ?, balance_tokens - ?, balance_tokens
                        FROM users WHERE telegram_id = ?
                    ''', (referrer_id, 'referral_bonus', Config.REFERRER_BONUS, 
                         f'Бонус за приглашение пользователя {nickname}', 
                         Config.REFERRER_BONUS, referrer_id))
                    
                    logger.info(f"Начислен бонус рефереру {referrer_id} за приглашение {telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка обработки реферального бонуса: {e}")
            
            # Логируем транзакцию нового пользователя (стартовый бонус)
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, description, balance_before, balance_after)
                VALUES (?, ?, ?, ?, 0, ?)
            ''', (telegram_id, 'registration_bonus', Config.REFERRED_BONUS, 
                 'Стартовый бонус за регистрацию', Config.REFERRED_BONUS))
            
            conn.commit()
            logger.info(f"✅ Создан пользователь: {nickname} (ID: {telegram_id})")
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Пользователь с telegram_id {telegram_id} уже существует")
                raise ValueError(f"Пользователь с ID {telegram_id} уже зарегистрирован")
            else:
                logger.error(f"Ошибка целостности данных при создании пользователя: {e}")
                raise
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
    
    def update_user_last_active(self, telegram_id: int):
        """Обновление времени последней активности"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_active = datetime('now') 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления времени активности: {e}")
    
    def update_user_balance(self, telegram_id: int, amount: float, currency: str = 'tokens') -> bool:
        """Обновление баланса пользователя"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Определяем поле баланса в зависимости от валюты
            balance_field = 'balance_tokens' if currency == 'tokens' else 'balance_diamonds'
            
            # Обновляем баланс
            cursor.execute(f'''
                UPDATE users 
                SET {balance_field} = {balance_field} + ? 
                WHERE telegram_id = ?
            ''', (amount, telegram_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.debug(f"Обновлен баланс пользователя {telegram_id}: {amount} {currency}")
                return True
            else:
                logger.warning(f"Пользователь {telegram_id} не найден при обновлении баланса")
                return False
            
        except Exception as e:
            logger.error(f"Ошибка обновления баланса: {e}")
            return False
    
    def get_user_balance(self, telegram_id: int) -> Dict[str, float]:
        """Получение балансов пользователя"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT balance_tokens, balance_diamonds 
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'tokens': float(result['balance_tokens']) if result['balance_tokens'] else 0.0,
                    'diamonds': float(result['balance_diamonds']) if result['balance_diamonds'] else 0.0
                }
            else:
                return {'tokens': 0.0, 'diamonds': 0.0}
                
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            return {'tokens': 0.0, 'diamonds': 0.0}
    
    def add_transaction(self, user_id: int, transaction_type: str, amount: float, 
                       description: str = '', currency: str = 'tokens') -> bool:
        """Добавление транзакции"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Получаем текущий баланс
            balance_field = 'balance_tokens' if currency == 'tokens' else 'balance_diamonds'
            cursor.execute(f'SELECT {balance_field} FROM users WHERE telegram_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Пользователь {user_id} не найден")
                return False
            
            balance_before = float(result[0]) if result[0] else 0.0
            balance_after = balance_before + amount
            
            # Добавляем запись о транзакции
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, transaction_type, amount, currency, description, 
                 balance_before, balance_after, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
            ''', (user_id, transaction_type, amount, currency, description, 
                 balance_before, balance_after))
            
            conn.commit()
            logger.debug(f"Добавлена транзакция: {user_id} - {transaction_type} - {amount} {currency}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления транзакции: {e}")
            return False
    
    def get_referrals_count(self, telegram_id: int) -> int:
        """Получение количества рефералов пользователя"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM referral_connections WHERE referrer_id = ?', (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества рефералов: {e}")
            return 0
    
    def get_referrals_list(self, telegram_id: int, limit: int = 50) -> List[Dict]:
        """Получение списка рефералов"""
        referrals = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.telegram_id, u.nickname, u.region, u.created_at, u.balance_tokens,
                       rc.bonus_paid, rc.referrer_bonus_paid, rc.created_at as referral_date
                FROM users u
                JOIN referral_connections rc ON u.telegram_id = rc.referred_id
                WHERE rc.referrer_id = ?
                ORDER BY rc.created_at DESC
                LIMIT ?
            ''', (telegram_id, limit))
            
            rows = cursor.fetchall()
            for row in rows:
                referrals.append(dict(row))
                
        except Exception as e:
            logger.error(f"Ошибка получения списка рефералов: {e}")
        
        return referrals
    
    def get_referral_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Получение полной статистики по рефералам"""
        stats = {
            'total_referrals': 0,
            'active_referrals': 0,
            'total_earned_tokens': 0.0,
            'pending_bonuses': 0.0,
            'conversion_rate': 0.0
        }
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Общее количество рефералов
            cursor.execute('SELECT COUNT(*) FROM referral_connections WHERE referrer_id = ?', (telegram_id,))
            stats['total_referrals'] = cursor.fetchone()[0] or 0
            
            # Количество активных рефералов (с балансом > 0 или активных недавно)
            cursor.execute('''
                SELECT COUNT(DISTINCT u.telegram_id)
                FROM users u
                JOIN referral_connections rc ON u.telegram_id = rc.referred_id
                WHERE rc.referrer_id = ? 
                AND (u.balance_tokens > 0 OR u.last_active > datetime('now', '-30 days'))
            ''', (telegram_id,))
            stats['active_referrals'] = cursor.fetchone()[0] or 0
            
            # Сумма заработанных токенов
            cursor.execute('''
                SELECT COALESCE(SUM(referrer_bonus_paid), 0) 
                FROM referral_connections 
                WHERE referrer_id = ? AND bonus_paid = 1
            ''', (telegram_id,))
            stats['total_earned_tokens'] = float(cursor.fetchone()[0] or 0)
            
            # Сумма ожидающих бонусов
            cursor.execute('''
                SELECT COALESCE(SUM(referrer_bonus_paid), 0) 
                FROM referral_connections 
                WHERE referrer_id = ? AND bonus_paid = 0
            ''', (telegram_id,))
            stats['pending_bonuses'] = float(cursor.fetchone()[0] or 0)
            
            # Коэффициент конверсии (активные / общие)
            if stats['total_referrals'] > 0:
                stats['conversion_rate'] = round((stats['active_referrals'] / stats['total_referrals']) * 100, 2)
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики рефералов: {e}")
        
        return stats
    
    def is_nickname_taken(self, nickname: str) -> bool:
        """Проверка, занят ли никнейм"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE nickname = ?', (nickname,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки никнейма: {e}")
            return False
    
    def add_referral_connection(self, referrer_id: int, referred_id: int) -> bool:
        """Добавление реферальной связи"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO referral_connections 
                (referrer_id, referred_id, referrer_bonus_paid, referred_bonus_paid)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, referred_id, Config.REFERRER_BONUS, Config.REFERRED_BONUS))
            
            # Обновляем счетчик рефералов
            cursor.execute('''
                UPDATE users 
                SET referrals_count = referrals_count + 1 
                WHERE telegram_id = ?
            ''', (referrer_id,))
            
            conn.commit()
            logger.info(f"✅ Добавлена реферальная связь: {referrer_id} -> {referred_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления реферальной связи: {e}")
            return False
    
    def get_leaderboard(self, limit: int = 10, criteria: str = 'referrals') -> List[Dict]:
        """Получение таблицы лидеров"""
        leaders = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if criteria == 'referrals':
                # По количеству рефералов
                cursor.execute('''
                    SELECT u.telegram_id, u.nickname, u.region, u.referrals_count,
                           COALESCE(SUM(rc.referrer_bonus_paid), 0) as total_earned
                    FROM users u
                    LEFT JOIN referral_connections rc ON u.telegram_id = rc.referrer_id
                    GROUP BY u.telegram_id
                    ORDER BY referrals_count DESC, total_earned DESC
                    LIMIT ?
                ''', (limit,))
            elif criteria == 'tokens':
                # По количеству токенов
                cursor.execute('''
                    SELECT telegram_id, nickname, region, balance_tokens, referrals_count
                    FROM users
                    ORDER BY balance_tokens DESC
                    LIMIT ?
                ''', (limit,))
            elif criteria == 'activity':
                # По активности
                cursor.execute('''
                    SELECT telegram_id, nickname, region, 
                           (total_trainings + total_duels) as total_activities,
                           total_trainings, total_duels
                    FROM users
                    ORDER BY total_activities DESC
                    LIMIT ?
                ''', (limit,))
            else:
                # По умолчанию - рефералы
                cursor.execute('''
                    SELECT telegram_id, nickname, region, referrals_count, balance_tokens
                    FROM users
                    ORDER BY referrals_count DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            for i, row in enumerate(rows, 1):
                leaders.append({
                    'place': i,
                    **dict(row)
                })
                
        except Exception as e:
            logger.error(f"Ошибка получения таблицы лидеров: {e}")
        
        return leaders
    
    def get_daily_bonus_info(self, telegram_id: int) -> Dict[str, Any]:
        """Получение информации о ежедневном бонусе"""
        info = {
            'can_claim': True,
            'last_claim': None,
            'next_claim': None,
            'streak': 0,
            'bonus_amount': Config.DAILY_BONUS_AMOUNT
        }
        
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Получаем информацию о последнем получении бонуса
            cursor.execute('''
                SELECT last_bonus_claim, daily_streak, last_streak_date 
                FROM users 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            if result:
                last_claim = result['last_bonus_claim']
                streak = result['daily_streak'] or 0
                last_streak_date = result['last_streak_date']
                
                info['streak'] = streak
                
                if last_claim:
                    info['last_claim'] = last_claim
                    
                    # Проверяем, можно ли получить бонус сегодня
                    cursor.execute('''
                        SELECT datetime(?, '+24 hours') > datetime('now') as can_claim
                    ''', (last_claim,))
                    
                    can_claim_result = cursor.fetchone()
                    if can_claim_result and can_claim_result[0] == 1:
                        info['can_claim'] = False
                        
                        # Вычисляем время следующего получения
                        cursor.execute('''
                            SELECT datetime(?, '+24 hours') as next_claim
                        ''', (last_claim,))
                        
                        next_claim_result = cursor.fetchone()
                        if next_claim_result:
                            info['next_claim'] = next_claim_result[0]
                    
                    # Проверяем непрерывность серии
                    if last_streak_date:
                        cursor.execute('''
                            SELECT date(?, '+1 day') = date('now') as is_streak_continued
                        ''', (last_streak_date,))
                        
                        streak_result = cursor.fetchone()
                        if streak_result and streak_result[0] == 1:
                            # Серия продолжается
                            info['streak'] += 1
                        else:
                            # Серия прервана
                            info['streak'] = 1
                    else:
                        info['streak'] = 1
                else:
                    info['streak'] = 1
                    
        except Exception as e:
            logger.error(f"Ошибка получения информации о ежедневном бонусе: {e}")
        
        return info
    
    def claim_daily_bonus(self, telegram_id: int) -> Tuple[bool, float, int]:
        """Получение ежедневного бонуса"""
        try:
            info = self.get_daily_bonus_info(telegram_id)
            
            if not info['can_claim']:
                return False, 0.0, info['streak']
            
            # Вычисляем бонус с учетом серии
            base_bonus = Config.DAILY_BONUS_AMOUNT
            streak_multiplier = min(1.0 + (info['streak'] * 0.1), 3.0)  # Максимум x3
            bonus_amount = round(base_bonus * streak_multiplier, 2)
            
            conn = self.connect()
            cursor = conn.cursor()
            
            # Обновляем баланс и информацию о бонусе
            cursor.execute('''
                UPDATE users 
                SET balance_tokens = balance_tokens + ?,
                    last_bonus_claim = datetime('now'),
                    daily_streak = ?,
                    last_streak_date = date('now')
                WHERE telegram_id = ?
            ''', (bonus_amount, info['streak'] + 1, telegram_id))
            
            # Добавляем запись о транзакции
            self.add_transaction(
                telegram_id, 
                'daily_bonus', 
                bonus_amount, 
                f'Ежедневный бонус (серия: {info["streak"] + 1})'
            )
            
            conn.commit()
            logger.info(f"Пользователь {telegram_id} получил ежедневный бонус: {bonus_amount} GFT")
            
            return True, bonus_amount, info['streak'] + 1
            
        except Exception as e:
            logger.error(f"Ошибка получения ежедневного бонуса: {e}")
            return False, 0.0, 0
    
    def get_shop_items(self, item_type: str = None) -> List[Dict]:
        """Получение товаров магазина"""
        items = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if item_type:
                cursor.execute('''
                    SELECT * FROM shop_items 
                    WHERE is_active = 1 AND (item_type = ? OR ? IS NULL)
                    ORDER BY item_type, price_tokens, price_diamonds
                ''', (item_type, item_type))
            else:
                cursor.execute('''
                    SELECT * FROM shop_items 
                    WHERE is_active = 1 
                    ORDER BY item_type, price_tokens, price_diamonds
                ''')
            
            rows = cursor.fetchall()
            for row in rows:
                items.append(dict(row))
                
        except Exception as e:
            logger.error(f"Ошибка получения товаров магазина: {e}")
        
        return items
    
    def purchase_item(self, user_id: int, item_id: int, quantity: int = 1) -> Tuple[bool, str]:
        """Покупка товара"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Получаем информацию о товаре
            cursor.execute('SELECT * FROM shop_items WHERE id = ? AND is_active = 1', (item_id,))
            item = cursor.fetchone()
            
            if not item:
                return False, "Товар не найден или недоступен"
            
            # Получаем баланс пользователя
            cursor.execute('SELECT balance_tokens, balance_diamonds FROM users WHERE telegram_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "Пользователь не найден"
            
            balance_tokens = float(user['balance_tokens']) if user['balance_tokens'] else 0.0
            balance_diamonds = float(user['balance_diamonds']) if user['balance_diamonds'] else 0.0
            
            item_price_tokens = float(item['price_tokens']) if item['price_tokens'] else 0.0
            item_price_diamonds = float(item['price_diamonds']) if item['price_diamonds'] else 0.0
            
            total_price_tokens = item_price_tokens * quantity
            total_price_diamonds = item_price_diamonds * quantity
            
            # Проверяем достаточно ли средств
            if balance_tokens < total_price_tokens:
                return False, f"Недостаточно токенов. Нужно: {total_price_tokens}, есть: {balance_tokens}"
            
            if balance_diamonds < total_price_diamonds:
                return False, f"Недостаточно алмазов. Нужно: {total_price_diamonds}, есть: {balance_diamonds}"
            
            # Проверяем наличие товара (если ограничено)
            if item['stock_quantity'] >= 0:
                cursor.execute('SELECT SUM(quantity) FROM purchases WHERE item_id = ?', (item_id,))
                sold = cursor.fetchone()[0] or 0
                
                if sold + quantity > item['stock_quantity']:
                    return False, f"Товара осталось: {item['stock_quantity'] - sold}"
            
            # Вычисляем дату окончания (если товар с ограниченным сроком)
            expires_at = None
            if item['duration_days']:
                cursor.execute('SELECT datetime("now", ?) as expires', (f"+{item['duration_days']} days",))
                expires_result = cursor.fetchone()
                expires_at = expires_result['expires'] if expires_result else None
            
            # Списываем средства
            cursor.execute('''
                UPDATE users 
                SET balance_tokens = balance_tokens - ?,
                    balance_diamonds = balance_diamonds - ?
                WHERE telegram_id = ?
            ''', (total_price_tokens, total_price_diamonds, user_id))
            
            # Добавляем запись о покупке
            cursor.execute('''
                INSERT INTO purchases 
                (user_id, item_id, quantity, total_price_tokens, total_price_diamonds, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, item_id, quantity, total_price_tokens, total_price_diamonds, expires_at))
            
            # Добавляем транзакции
            if total_price_tokens > 0:
                self.add_transaction(
                    user_id, 
                    'purchase', 
                    -total_price_tokens, 
                    f'Покупка: {item["name"]} x{quantity}',
                    'tokens'
                )
            
            if total_price_diamonds > 0:
                self.add_transaction(
                    user_id, 
                    'purchase', 
                    -total_price_diamonds, 
                    f'Покупка: {item["name"]} x{quantity}',
                    'diamonds'
                )
            
            # Активируем эффекты товара
            self._activate_item_effects(user_id, item, quantity, expires_at)
            
            conn.commit()
            logger.info(f"Пользователь {user_id} купил товар {item['name']} x{quantity}")
            
            return True, f"✅ Покупка успешна! Приобретен: {item['name']} x{quantity}"
            
        except Exception as e:
            logger.error(f"Ошибка покупки товара: {e}")
            return False, f"Ошибка при покупке: {str(e)}"
    
    def _activate_item_effects(self, user_id: int, item: sqlite3.Row, quantity: int, expires_at: str):
        """Активация эффектов купленного товара"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            item_type = item['item_type']
            
            if item_type == 'premium':
                # Активация премиум статуса
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 1,
                        premium_until = MAX(COALESCE(premium_until, datetime('now')), ?)
                    WHERE telegram_id = ?
                ''', (expires_at, user_id))
                
            elif item_type == 'boost':
                # Активация буста (здесь можно добавить логику бустов)
                pass
                
            elif item_type == 'tokens_pack':
                # Пакет токенов уже начислен при списании баланса
                pass
                
            elif item_type == 'cosmetic':
                # Косметические предметы (можно добавить в отдельную таблицу)
                pass
            
        except Exception as e:
            logger.error(f"Ошибка активации эффектов товара: {e}")
    
    def get_user_purchases(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Получение истории покупок пользователя"""
        purchases = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.*, si.name as item_name, si.icon as item_icon, 
                       si.item_type, si.effect_description
                FROM purchases p
                JOIN shop_items si ON p.item_id = si.id
                WHERE p.user_id = ?
                ORDER BY p.purchased_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            for row in rows:
                purchases.append(dict(row))
                
        except Exception as e:
            logger.error(f"Ошибка получения истории покупок: {e}")
        
        return purchases
    
    def get_user_transactions(self, user_id: int, limit: int = 20, 
                            transaction_type: str = None) -> List[Dict]:
        """Получение истории транзакций пользователя"""
        transactions = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if transaction_type:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE user_id = ? AND transaction_type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, transaction_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            
            rows = cursor.fetchall()
            for row in rows:
                transactions.append(dict(row))
                
        except Exception as e:
            logger.error(f"Ошибка получения истории транзакций: {e}")
        
        return transactions
    
    def add_achievement(self, user_id: int, achievement_type: str, 
                       achievement_name: str, description: str = '',
                       icon: str = '🏆', reward_tokens: float = 0.0,
                       reward_diamonds: float = 0.0) -> bool:
        """Добавление достижения пользователю"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже такое достижение
            cursor.execute('''
                SELECT id FROM achievements 
                WHERE user_id = ? AND achievement_type = ? AND achievement_name = ?
            ''', (user_id, achievement_type, achievement_name))
            
            if cursor.fetchone():
                logger.debug(f"Достижение уже есть у пользователя {user_id}: {achievement_name}")
                return False
            
            # Добавляем достижение
            cursor.execute('''
                INSERT INTO achievements 
                (user_id, achievement_type, achievement_name, description, icon,
                 reward_tokens, reward_diamonds, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (user_id, achievement_type, achievement_name, description, icon,
                 reward_tokens, reward_diamonds))
            
            # Обновляем счетчик достижений у пользователя
            cursor.execute('''
                UPDATE users 
                SET achievements_count = achievements_count + 1,
                    balance_tokens = balance_tokens + ?,
                    balance_diamonds = balance_diamonds + ?
                WHERE telegram_id = ?
            ''', (reward_tokens, reward_diamonds, user_id))
            
            # Добавляем транзакции для наград
            if reward_tokens > 0:
                self.add_transaction(
                    user_id, 
                    'achievement_reward', 
                    reward_tokens, 
                    f'Награда за достижение: {achievement_name}',
                    'tokens'
                )
            
            if reward_diamonds > 0:
                self.add_transaction(
                    user_id, 
                    'achievement_reward', 
                    reward_diamonds, 
                    f'Награда за достижение: {achievement_name}',
                    'diamonds'
                )
            
            conn.commit()
            logger.info(f"Добавлено достижение пользователю {user_id}: {achievement_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления достижения: {e}")
            return False
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Получение достижений пользователя"""
        achievements = []
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM achievements 
                WHERE user_id = ? 
                ORDER BY earned_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            for row in rows:
                achievements.append(dict(row))
                
        except Exception as e:
            logger.error(f"Ошибка получения достижений: {e}")
        
        return achievements
    
    def get_total_users_count(self) -> int:
        """Получение общего количества пользователей"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества пользователей: {e}")
            return 0
    
    def get_active_users_count(self, days: int = 7) -> int:
        """Получение количества активных пользователей за N дней"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active > datetime('now', ?)
            ''', (f'-{days} days',))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества активных пользователей: {e}")
            return 0
    
    def backup_database(self, backup_path: str) -> bool:
        """Создание резервной копии базы данных"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✅ Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка создания резервной копии: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Выполнение произвольного SQL запроса"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return []
                
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            return []
    
    def vacuum(self):
        """Оптимизация базы данных"""
        try:
            conn = self.connect()
            conn.execute('VACUUM')
            conn.commit()
            logger.info("✅ База данных оптимизирована (VACUUM)")
        except Exception as e:
            logger.error(f"Ошибка оптимизации БД: {e}")