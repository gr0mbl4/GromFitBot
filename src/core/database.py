"""
Полный модуль работы с базой данных GromFitBot
Поддерживает все таблицы и операции
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any, Tuple, Union
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class Database:
    """Полный класс для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = Path(db_path)
        self._ensure_database()
        self._create_tables()
        self._create_indexes()
        logger.info(f"База данных инициализирована: {self.db_path}")
    
    def _ensure_database(self):
        """Создание директории и файла БД если не существует"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        if not self.db_path.exists():
            logger.info(f"Создание новой базы данных: {self.db_path}")
    
    def _create_tables(self):
        """Создание всех таблиц базы данных"""
        tables = [
            # Основная таблица пользователей
            """
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
                theme TEXT DEFAULT 'light',
                settings TEXT DEFAULT '{}'
            )
            """,
            
            # Таблица реферальных связей
            """
            CREATE TABLE IF NOT EXISTS referral_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                connection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bonus_paid BOOLEAN DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users(telegram_id),
                FOREIGN KEY (referred_id) REFERENCES users(telegram_id)
            )
            """,
            
            # Таблица транзакций
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
            """,
            
            # Таблица достижений
            """
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                icon TEXT DEFAULT '🏆',
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 100,
                total_required INTEGER DEFAULT 100,
                category TEXT DEFAULT 'general',
                reward_tokens DECIMAL(15,2) DEFAULT 0.00,
                reward_diamonds DECIMAL(15,2) DEFAULT 0.00,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
            """,
            
            # Таблица товаров магазина
            """
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_tokens DECIMAL(15,2) NOT NULL,
                price_diamonds DECIMAL(15,2) DEFAULT 0.00,
                category TEXT NOT NULL,
                icon TEXT DEFAULT '🛒',
                available_quantity INTEGER DEFAULT -1,
                purchased_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
            """,
            
            # Таблица покупок
            """
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                price_tokens DECIMAL(15,2) NOT NULL,
                price_diamonds DECIMAL(15,2) DEFAULT 0.00,
                quantity INTEGER DEFAULT 1,
                status TEXT DEFAULT 'completed',
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (item_id) REFERENCES shop_items(item_id)
            )
            """,
            
            # Таблица тренировок
            """
            CREATE TABLE IF NOT EXISTS trainings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                training_type TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                calories_burned INTEGER,
                exercises_count INTEGER DEFAULT 0,
                training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
            """,
            
            # Таблица дуэлей
            """
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duel_id TEXT UNIQUE NOT NULL,
                challenger_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                exercise_type TEXT NOT NULL,
                target_value INTEGER NOT NULL,
                wager_tokens DECIMAL(15,2) DEFAULT 0.00,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                winner_id INTEGER,
                challenger_result INTEGER,
                opponent_result INTEGER,
                FOREIGN KEY (challenger_id) REFERENCES users(telegram_id),
                FOREIGN KEY (opponent_id) REFERENCES users(telegram_id),
                FOREIGN KEY (winner_id) REFERENCES users(telegram_id)
            )
            """,
            
            # Таблица уведомлений
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_url TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
            """
        ]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for table_sql in tables:
                try:
                    cursor.execute(table_sql)
                except sqlite3.Error as e:
                    logger.error(f"Ошибка создания таблицы: {e}")
            conn.commit()
        
        logger.info("Таблицы базы данных созданы/проверены")
    
    def _create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_registration_number ON users(registration_number)",
            "CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_referral_connections_referrer ON referral_connections(referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_referral_connections_referred ON referral_connections(referred_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_shop_items_category ON shop_items(category)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_trainings_user_date ON trainings(user_id, training_date)",
            "CREATE INDEX IF NOT EXISTS idx_duels_status ON duels(status)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)"
        ]
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except sqlite3.Error as e:
                    logger.error(f"Ошибка создания индекса: {e}")
            conn.commit()
        
        logger.info("Индексы базы данных созданы/проверены")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получение соединения с базой данных"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Возвращает словари вместо кортежей
        return conn
    
    def test_connection(self) -> bool:
        """Тестирование соединения с базой данных"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Ошибка соединения с БД: {e}")
            return False
    
    # ==================== ОСНОВНЫЕ МЕТОДЫ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ====================
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = ?",
                    (telegram_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя {telegram_id}: {e}")
            return None
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Алиас для get_user"""
        return self.get_user(telegram_id)
    
    def get_user_by_registration_number(self, reg_number: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по регистрационному номеру"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE registration_number = ?",
                    (reg_number,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по номеру {reg_number}: {e}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Создание нового пользователя"""
        required_fields = ['telegram_id', 'registration_number', 'nickname']
        
        if not all(field in user_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Подготавливаем поля и значения
                fields = []
                placeholders = []
                values = []
                
                for field, value in user_data.items():
                    fields.append(field)
                    placeholders.append('?')
                    values.append(value)
                
                sql = f"INSERT INTO users ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, values)
                
                # Если есть referrer_id, создаем реферальную связь
                referrer_id = user_data.get('referrer_id')
                if referrer_id:
                    referral_data = {
                        'referrer_id': referrer_id,
                        'referred_id': user_data['telegram_id']
                    }
                    self.create_referral_connection(referral_data)
                    
                    # Начисляем бонус рефереру
                    self.add_transaction(
                        user_id=referrer_id,
                        transaction_type='referral_bonus',
                        amount=10.00,
                        description=f'Бонус за приглашение пользователя {user_data["nickname"]}'
                    )
                    
                    # Обновляем баланс реферера
                    self.update_user_balance(referrer_id, 10.00)
                
                conn.commit()
                logger.info(f"Создан пользователь: {user_data['nickname']} (ID: {user_data['telegram_id']})")
                return True
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Пользователь с telegram_id {user_data['telegram_id']} уже существует")
            else:
                logger.error(f"Ошибка целостности при создании пользователя: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return False
    
    def update_user(self, telegram_id: int, update_data: Dict[str, Any]) -> bool:
        """Обновление данных пользователя"""
        if not update_data:
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Подготавливаем SET часть запроса
                set_clauses = []
                values = []
                
                for field, value in update_data.items():
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
                
                values.append(telegram_id)  # Для WHERE условия
                
                sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE telegram_id = ?"
                cursor.execute(sql, values)
                
                conn.commit()
                logger.debug(f"Обновлен пользователь {telegram_id}: {list(update_data.keys())}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя {telegram_id}: {e}")
            return False
    
    def update_user_field(self, telegram_id: int, field: str, value: Any) -> bool:
        """Обновление одного поля пользователя"""
        return self.update_user(telegram_id, {field: value})
    
    def update_user_balance(self, telegram_id: int, amount_change: float) -> bool:
        """Обновление баланса токенов пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Используем атомарное обновление
                cursor.execute(
                    "UPDATE users SET balance_tokens = balance_tokens + ? WHERE telegram_id = ?",
                    (amount_change, telegram_id)
                )
                
                conn.commit()
                logger.debug(f"Баланс пользователя {telegram_id} изменен на {amount_change}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления баланса пользователя {telegram_id}: {e}")
            return False
    
    def update_user_last_active(self, telegram_id: int) -> bool:
        """Обновление времени последней активности"""
        return self.update_user_field(telegram_id, 'last_active', datetime.now().isoformat())
    
    def delete_user(self, telegram_id: int) -> bool:
        """Удаление пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
                conn.commit()
                
                logger.info(f"Удален пользователь {telegram_id}")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя {telegram_id}: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Получение общего количества пользователей"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Ошибка получения количества пользователей: {e}")
            return 0
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение списка всех пользователей"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    def get_top_users_by_field(self, field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ пользователей по указанному полю"""
        allowed_fields = ['balance_tokens', 'referrals_count', 'total_trainings', 'total_points', 'level']
        
        if field not in allowed_fields:
            logger.error(f"Поле {field} не разрешено для топа")
            return []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT * FROM users ORDER BY {field} DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения топа по полю {field}: {e}")
            return []
    
    # ==================== МЕТОДЫ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================
    
    def create_referral_connection(self, connection_data: Dict[str, Any]) -> bool:
        """Создание реферальной связи"""
        required_fields = ['referrer_id', 'referred_id']
        
        if not all(field in connection_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля реферальной связи: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO referral_connections (referrer_id, referred_id)
                    VALUES (?, ?)
                    """,
                    (connection_data['referrer_id'], connection_data['referred_id'])
                )
                
                # Обновляем счетчик рефералов у реферера
                cursor.execute(
                    "UPDATE users SET referrals_count = referrals_count + 1 WHERE telegram_id = ?",
                    (connection_data['referrer_id'],)
                )
                
                conn.commit()
                logger.info(f"Создана реферальная связь: {connection_data['referrer_id']} -> {connection_data['referred_id']}")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"Реферальная связь уже существует: {connection_data['referrer_id']} -> {connection_data['referred_id']}")
            return False
        except Exception as e:
            logger.error(f"Ошибка создания реферальной связи: {e}")
            return False
    
    def get_referrals(self, referrer_id: int) -> List[Dict[str, Any]]:
        """Получение списка рефералов пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT u.* FROM users u
                    JOIN referral_connections rc ON u.telegram_id = rc.referred_id
                    WHERE rc.referrer_id = ?
                    ORDER BY rc.connection_date DESC
                    """,
                    (referrer_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения рефералов пользователя {referrer_id}: {e}")
            return []
    
    def get_referral_count(self, referrer_id: int) -> int:
        """Получение количества рефералов пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM referral_connections WHERE referrer_id = ?",
                    (referrer_id,)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Ошибка получения количества рефералов пользователя {referrer_id}: {e}")
            return 0
    
    def get_referrer(self, referred_id: int) -> Optional[Dict[str, Any]]:
        """Получение реферера пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT u.* FROM users u
                    JOIN referral_connections rc ON u.telegram_id = rc.referrer_id
                    WHERE rc.referred_id = ?
                    """,
                    (referred_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения реферера пользователя {referred_id}: {e}")
            return None
    
    def get_top_referrers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ рефереров"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT u.*, COUNT(rc.id) as referrals_count
                    FROM users u
                    LEFT JOIN referral_connections rc ON u.telegram_id = rc.referrer_id
                    GROUP BY u.telegram_id
                    ORDER BY referrals_count DESC, u.created_at
                    LIMIT ?
                    """,
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения топ рефереров: {e}")
            return []
    
    # ==================== МЕТОДЫ ТРАНЗАКЦИЙ ====================
    
    def add_transaction(self, user_id: int, transaction_type: str, amount: float, 
                       description: str = "", metadata: Dict = None) -> bool:
        """Добавление транзакции"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata or {})
                
                cursor.execute(
                    """
                    INSERT INTO transactions (user_id, transaction_type, amount, description, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, transaction_type, amount, description, metadata_json)
                )
                
                conn.commit()
                logger.debug(f"Добавлена транзакция: {user_id}, {transaction_type}, {amount}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления транзакции: {e}")
            return False
    
    def get_user_transactions(self, user_id: int, limit: int = 20, 
                             offset: int = 0) -> List[Dict[str, Any]]:
        """Получение транзакций пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM transactions 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения транзакций пользователя {user_id}: {e}")
            return []
    
    def get_transaction_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение сводки по транзакциям"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Общий доход
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) as total_income
                    FROM transactions
                    WHERE user_id = ? AND amount > 0
                    AND created_at >= datetime('now', '-' || ? || ' days')
                    """,
                    (user_id, days)
                )
                total_income = cursor.fetchone()[0] or 0
                
                # Общие расходы
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0) as total_expense
                    FROM transactions
                    WHERE user_id = ? AND amount < 0
                    AND created_at >= datetime('now', '-' || ? || ' days')
                    """,
                    (user_id, days)
                )
                total_expense = cursor.fetchone()[0] or 0
                
                # Количество транзакций
                cursor.execute(
                    """
                    SELECT COUNT(*) as transaction_count
                    FROM transactions
                    WHERE user_id = ?
                    AND created_at >= datetime('now', '-' || ? || ' days')
                    """,
                    (user_id, days)
                )
                transaction_count = cursor.fetchone()[0] or 0
                
                return {
                    'total_income': total_income,
                    'total_expense': total_expense,
                    'transaction_count': transaction_count,
                    'net_change': total_income + total_expense  # expense отрицательный
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения сводки транзакций пользователя {user_id}: {e}")
            return {'total_income': 0, 'total_expense': 0, 'transaction_count': 0, 'net_change': 0}
    
    # ==================== МЕТОДЫ ДОСТИЖЕНИЙ ====================
    
    def add_achievement(self, user_id: int, achievement_data: Dict[str, Any]) -> bool:
        """Добавление достижения пользователю"""
        required_fields = ['achievement_id', 'title', 'description']
        
        if not all(field in achievement_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля достижения: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем, есть ли уже такое достижение
                cursor.execute(
                    "SELECT id FROM achievements WHERE user_id = ? AND achievement_id = ?",
                    (user_id, achievement_data['achievement_id'])
                )
                existing = cursor.fetchone()
                
                if existing:
                    logger.debug(f"Достижение {achievement_data['achievement_id']} уже есть у пользователя {user_id}")
                    return False
                
                # Добавляем достижение
                cursor.execute(
                    """
                    INSERT INTO achievements (
                        user_id, achievement_id, title, description, icon,
                        progress, total_required, category,
                        reward_tokens, reward_diamonds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        achievement_data['achievement_id'],
                        achievement_data['title'],
                        achievement_data['description'],
                        achievement_data.get('icon', '🏆'),
                        achievement_data.get('progress', 100),
                        achievement_data.get('total_required', 100),
                        achievement_data.get('category', 'general'),
                        achievement_data.get('reward_tokens', 0),
                        achievement_data.get('reward_diamonds', 0)
                    )
                )
                
                # Обновляем счетчик достижений пользователя
                cursor.execute(
                    "UPDATE users SET achievements_count = achievements_count + 1 WHERE telegram_id = ?",
                    (user_id,)
                )
                
                # Начисляем награду если есть
                reward_tokens = achievement_data.get('reward_tokens', 0)
                reward_diamonds = achievement_data.get('reward_diamonds', 0)
                
                if reward_tokens > 0:
                    self.update_user_balance(user_id, reward_tokens)
                    self.add_transaction(
                        user_id=user_id,
                        transaction_type='achievement_reward',
                        amount=reward_tokens,
                        description=f'Награда за достижение: {achievement_data["title"]}'
                    )
                
                conn.commit()
                logger.info(f"Добавлено достижение {achievement_data['achievement_id']} пользователю {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления достижения пользователю {user_id}: {e}")
            return False
    
    def get_user_achievements(self, user_id: int, category: str = None) -> List[Dict[str, Any]]:
        """Получение достижений пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute(
                        """
                        SELECT * FROM achievements 
                        WHERE user_id = ? AND category = ?
                        ORDER BY unlocked_at DESC
                        """,
                        (user_id, category)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM achievements 
                        WHERE user_id = ?
                        ORDER BY unlocked_at DESC
                        """,
                        (user_id,)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения достижений пользователя {user_id}: {e}")
            return []
    
    def get_achievement_progress(self, user_id: int, achievement_id: str) -> Optional[Dict[str, Any]]:
        """Получение прогресса по достижению"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM achievements WHERE user_id = ? AND achievement_id = ?",
                    (user_id, achievement_id)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения прогресса достижения {achievement_id} пользователя {user_id}: {e}")
            return None
    
    def update_achievement_progress(self, user_id: int, achievement_id: str, 
                                  progress: int, total_required: int = None) -> bool:
        """Обновление прогресса достижения"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if total_required:
                    cursor.execute(
                        """
                        UPDATE achievements 
                        SET progress = ?, total_required = ?, unlocked_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND achievement_id = ?
                        """,
                        (progress, total_required, user_id, achievement_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE achievements 
                        SET progress = ?, unlocked_at = CURRENT_TIMESTAMP
                        WHERE user_id = ? AND achievement_id = ?
                        """,
                        (progress, user_id, achievement_id)
                    )
                
                conn.commit()
                logger.debug(f"Обновлен прогресс достижения {achievement_id} пользователя {user_id}: {progress}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления прогресса достижения: {e}")
            return False
    
    # ==================== МЕТОДЫ МАГАЗИНА ====================
    
    def add_shop_item(self, item_data: Dict[str, Any]) -> bool:
        """Добавление товара в магазин"""
        required_fields = ['item_id', 'name', 'description', 'price_tokens', 'category']
        
        if not all(field in item_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля товара: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(item_data.get('metadata', {}))
                
                cursor.execute(
                    """
                    INSERT INTO shop_items (
                        item_id, name, description, price_tokens, price_diamonds,
                        category, icon, available_quantity, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_data['item_id'],
                        item_data['name'],
                        item_data['description'],
                        item_data['price_tokens'],
                        item_data.get('price_diamonds', 0),
                        item_data['category'],
                        item_data.get('icon', '🛒'),
                        item_data.get('available_quantity', -1),
                        metadata_json
                    )
                )
                
                conn.commit()
                logger.info(f"Добавлен товар в магазин: {item_data['item_id']} - {item_data['name']}")
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f"Товар с item_id {item_data['item_id']} уже существует")
            return False
        except Exception as e:
            logger.error(f"Ошибка добавления товара: {e}")
            return False
    
    def get_shop_items(self, category: str = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """Получение товаров магазина"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if category:
                    if active_only:
                        cursor.execute(
                            """
                            SELECT * FROM shop_items 
                            WHERE category = ? AND is_active = 1
                            ORDER BY price_tokens ASC
                            """,
                            (category,)
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT * FROM shop_items 
                            WHERE category = ?
                            ORDER BY price_tokens ASC
                            """,
                            (category,)
                        )
                else:
                    if active_only:
                        cursor.execute(
                            "SELECT * FROM shop_items WHERE is_active = 1 ORDER BY category, price_tokens ASC"
                        )
                    else:
                        cursor.execute("SELECT * FROM shop_items ORDER BY category, price_tokens ASC")
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения товаров магазина: {e}")
            return []
    
    def get_shop_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Получение товара по ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shop_items WHERE item_id = ?", (item_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения товара {item_id}: {e}")
            return None
    
    def purchase_item(self, user_id: int, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Покупка товара"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем информацию о товаре
                item = self.get_shop_item(item_id)
                if not item:
                    return {'success': False, 'error': 'Товар не найден'}
                
                # Проверяем доступность
                if item['available_quantity'] != -1 and item['available_quantity'] < quantity:
                    return {'success': False, 'error': 'Недостаточно товара в наличии'}
                
                # Получаем информацию о пользователе
                user = self.get_user(user_id)
                if not user:
                    return {'success': False, 'error': 'Пользователь не найден'}
                
                # Проверяем баланс
                total_price_tokens = item['price_tokens'] * quantity
                total_price_diamonds = item['price_diamonds'] * quantity
                
                if user['balance_tokens'] < total_price_tokens:
                    return {'success': False, 'error': 'Недостаточно токенов'}
                
                if user['balance_diamonds'] < total_price_diamonds:
                    return {'success': False, 'error': 'Недостаточно алмазов'}
                
                # Выполняем покупку
                # 1. Обновляем баланс пользователя
                cursor.execute(
                    """
                    UPDATE users 
                    SET balance_tokens = balance_tokens - ?,
                        balance_diamonds = balance_diamonds - ?
                    WHERE telegram_id = ?
                    """,
                    (total_price_tokens, total_price_diamonds, user_id)
                )
                
                # 2. Добавляем запись о покупке
                cursor.execute(
                    """
                    INSERT INTO purchases (user_id, item_id, price_tokens, price_diamonds, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, item_id, total_price_tokens, total_price_diamonds, quantity)
                )
                
                # 3. Обновляем количество доступного товара
                if item['available_quantity'] != -1:
                    cursor.execute(
                        """
                        UPDATE shop_items 
                        SET available_quantity = available_quantity - ?,
                            purchased_count = purchased_count + ?
                        WHERE item_id = ?
                        """,
                        (quantity, quantity, item_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE shop_items 
                        SET purchased_count = purchased_count + ?
                        WHERE item_id = ?
                        """,
                        (quantity, item_id)
                    )
                
                # 4. Добавляем транзакцию
                self.add_transaction(
                    user_id=user_id,
                    transaction_type='purchase',
                    amount=-total_price_tokens,
                    description=f'Покупка: {item["name"]} x{quantity}'
                )
                
                conn.commit()
                
                logger.info(f"Пользователь {user_id} купил товар {item_id} x{quantity}")
                
                return {
                    'success': True,
                    'item_name': item['name'],
                    'quantity': quantity,
                    'total_tokens': total_price_tokens,
                    'total_diamonds': total_price_diamonds,
                    'new_balance_tokens': user['balance_tokens'] - total_price_tokens,
                    'new_balance_diamonds': user['balance_diamonds'] - total_price_diamonds
                }
                
        except Exception as e:
            logger.error(f"Ошибка покупки товара {item_id} пользователем {user_id}: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка при покупке'}
    
    def get_user_purchases(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение покупок пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT p.*, s.name as item_name, s.description as item_description
                    FROM purchases p
                    JOIN shop_items s ON p.item_id = s.item_id
                    WHERE p.user_id = ?
                    ORDER BY p.purchase_date DESC
                    LIMIT ?
                    """,
                    (user_id, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения покупок пользователя {user_id}: {e}")
            return []
    
    # ==================== МЕТОДЫ БОНУСОВ ====================
    
    def claim_daily_bonus(self, user_id: int) -> Dict[str, Any]:
        """Получение ежедневного бонуса"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем информацию о пользователе
                user = self.get_user(user_id)
                if not user:
                    return {'success': False, 'error': 'Пользователь не найден'}
                
                current_date = date.today().isoformat()
                last_bonus_date = user.get('last_bonus_claim')
                daily_streak = user.get('daily_streak', 0)
                last_streak_date = user.get('last_streak_date')
                
                # Проверяем, получал ли пользователь бонус сегодня
                if last_bonus_date:
                    last_date = datetime.fromisoformat(last_bonus_date.replace('Z', '+00:00')).date()
                    if last_date == date.today():
                        return {'success': False, 'error': 'Бонус уже получен сегодня'}
                
                # Вычисляем размер бонуса
                base_bonus = 5.0
                streak_multiplier = 1.2
                
                # Проверяем серию дней
                if last_streak_date:
                    last_streak = datetime.fromisoformat(last_streak_date.replace('Z', '+00:00')).date()
                    days_diff = (date.today() - last_streak).days
                    
                    if days_diff == 1:
                        # Серия продолжается
                        daily_streak += 1
                    elif days_diff == 0:
                        # Уже получал сегодня
                        return {'success': False, 'error': 'Бонус уже получен сегодня'}
                    else:
                        # Серия прервана
                        daily_streak = 1
                else:
                    # Первый бонус
                    daily_streak = 1
                
                # Вычисляем бонус с учетом серии
                bonus_amount = base_bonus * (streak_multiplier ** min(daily_streak - 1, 7))
                bonus_amount = round(bonus_amount, 2)
                
                # Обновляем данные пользователя
                cursor.execute(
                    """
                    UPDATE users 
                    SET balance_tokens = balance_tokens + ?,
                        last_bonus_claim = ?,
                        daily_streak = ?,
                        last_streak_date = ?
                    WHERE telegram_id = ?
                    """,
                    (bonus_amount, datetime.now().isoformat(), daily_streak, current_date, user_id)
                )
                
                # Добавляем транзакцию
                self.add_transaction(
                    user_id=user_id,
                    transaction_type='daily_bonus',
                    amount=bonus_amount,
                    description=f'Ежедневный бонус (серия: {daily_streak} дней)'
                )
                
                conn.commit()
                
                logger.info(f"Пользователь {user_id} получил ежедневный бонус: {bonus_amount} (серия: {daily_streak})")
                
                return {
                    'success': True,
                    'bonus_amount': bonus_amount,
                    'daily_streak': daily_streak,
                    'next_bonus_multiplier': streak_multiplier ** min(daily_streak, 7),
                    'new_balance': user['balance_tokens'] + bonus_amount
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения ежедневного бонуса пользователем {user_id}: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка'}
    
    def can_claim_bonus(self, user_id: int) -> bool:
        """Проверка, может ли пользователь получить бонус"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        last_bonus_date = user.get('last_bonus_claim')
        if not last_bonus_date:
            return True
        
        try:
            last_date = datetime.fromisoformat(last_bonus_date.replace('Z', '+00:00')).date()
            return last_date < date.today()
        except:
            return True
    
    # ==================== МЕТОДЫ ТРЕНИРОВОК ====================
    
    def add_training(self, user_id: int, training_data: Dict[str, Any]) -> bool:
        """Добавление записи о тренировке"""
        required_fields = ['training_type', 'duration_minutes']
        
        if not all(field in training_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля тренировки: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO trainings (
                        user_id, training_type, duration_minutes, 
                        calories_burned, exercises_count, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        training_data['training_type'],
                        training_data['duration_minutes'],
                        training_data.get('calories_burned'),
                        training_data.get('exercises_count', 0),
                        training_data.get('notes', '')
                    )
                )
                
                # Обновляем статистику пользователя
                cursor.execute(
                    """
                    UPDATE users 
                    SET total_trainings = total_trainings + 1,
                        last_training_date = ?,
                        total_points = total_points + ?
                    WHERE telegram_id = ?
                    """,
                    (
                        datetime.now().isoformat(),
                        training_data.get('points_earned', 10),
                        user_id
                    )
                )
                
                conn.commit()
                logger.info(f"Добавлена тренировка пользователя {user_id}: {training_data['training_type']}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления тренировки пользователя {user_id}: {e}")
            return False
    
    def get_user_trainings(self, user_id: int, limit: int = 20, 
                          offset: int = 0) -> List[Dict[str, Any]]:
        """Получение тренировок пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM trainings 
                    WHERE user_id = ?
                    ORDER BY training_date DESC
                    LIMIT ? OFFSET ?
                    """,
                    (user_id, limit, offset)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения тренировок пользователя {user_id}: {e}")
            return []
    
    def get_training_stats(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение статистики тренировок"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Общее количество тренировок
                cursor.execute(
                    "SELECT COUNT(*) FROM trainings WHERE user_id = ?",
                    (user_id,)
                )
                total_trainings = cursor.fetchone()[0] or 0
                
                # Тренировки за период
                cursor.execute(
                    """
                    SELECT COUNT(*) as recent_count,
                           SUM(duration_minutes) as total_minutes,
                           SUM(calories_burned) as total_calories
                    FROM trainings
                    WHERE user_id = ?
                    AND training_date >= datetime('now', '-' || ? || ' days')
                    """,
                    (user_id, days)
                )
                recent_stats = cursor.fetchone()
                
                # Самый популярный тип тренировки
                cursor.execute(
                    """
                    SELECT training_type, COUNT(*) as count
                    FROM trainings
                    WHERE user_id = ?
                    GROUP BY training_type
                    ORDER BY count DESC
                    LIMIT 1
                    """,
                    (user_id,)
                )
                favorite_type_row = cursor.fetchone()
                
                return {
                    'total_trainings': total_trainings,
                    'recent_trainings': recent_stats['recent_count'] or 0 if recent_stats else 0,
                    'total_minutes': recent_stats['total_minutes'] or 0 if recent_stats else 0,
                    'total_calories': recent_stats['total_calories'] or 0 if recent_stats else 0,
                    'favorite_type': favorite_type_row['training_type'] if favorite_type_row else 'Нет данных',
                    'favorite_type_count': favorite_type_row['count'] if favorite_type_row else 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики тренировок пользователя {user_id}: {e}")
            return {
                'total_trainings': 0,
                'recent_trainings': 0,
                'total_minutes': 0,
                'total_calories': 0,
                'favorite_type': 'Нет данных',
                'favorite_type_count': 0
            }
    
    # ==================== МЕТОДЫ ДУЭЛЕЙ ====================
    
    def create_duel(self, duel_data: Dict[str, Any]) -> bool:
        """Создание новой дуэли"""
        required_fields = ['duel_id', 'challenger_id', 'opponent_id', 'exercise_type', 'target_value']
        
        if not all(field in duel_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля дуэли: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO duels (
                        duel_id, challenger_id, opponent_id, exercise_type,
                        target_value, wager_tokens, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        duel_data['duel_id'],
                        duel_data['challenger_id'],
                        duel_data['opponent_id'],
                        duel_data['exercise_type'],
                        duel_data['target_value'],
                        duel_data.get('wager_tokens', 0),
                        duel_data.get('status', 'pending')
                    )
                )
                
                conn.commit()
                logger.info(f"Создана дуэль {duel_data['duel_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка создания дуэли: {e}")
            return False
    
    def get_duel(self, duel_id: str) -> Optional[Dict[str, Any]]:
        """Получение дуэли по ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM duels WHERE duel_id = ?", (duel_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения дуэли {duel_id}: {e}")
            return None
    
    def update_duel_result(self, duel_id: str, winner_id: int, 
                          challenger_result: int, opponent_result: int) -> bool:
        """Обновление результата дуэли"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем информацию о дуэли
                duel = self.get_duel(duel_id)
                if not duel:
                    return False
                
                # Обновляем результат дуэли
                cursor.execute(
                    """
                    UPDATE duels 
                    SET status = 'completed',
                        winner_id = ?,
                        challenger_result = ?,
                        opponent_result = ?,
                        ended_at = ?
                    WHERE duel_id = ?
                    """,
                    (winner_id, challenger_result, opponent_result, datetime.now().isoformat(), duel_id)
                )
                
                # Обновляем статистику пользователей
                cursor.execute(
                    """
                    UPDATE users 
                    SET total_duels = total_duels + 1
                    WHERE telegram_id IN (?, ?)
                    """,
                    (duel['challenger_id'], duel['opponent_id'])
                )
                
                # Обновляем статистику побед у победителя
                cursor.execute(
                    "UPDATE users SET duels_won = duels_won + 1 WHERE telegram_id = ?",
                    (winner_id,)
                )
                
                # Обрабатываем ставки
                wager = duel.get('wager_tokens', 0)
                if wager > 0:
                    # Переводим ставки победителю
                    loser_id = duel['challenger_id'] if winner_id == duel['opponent_id'] else duel['opponent_id']
                    
                    cursor.execute(
                        """
                        UPDATE users 
                        SET balance_tokens = balance_tokens + ?
                        WHERE telegram_id = ?
                        """,
                        (wager * 2, winner_id)
                    )
                    
                    cursor.execute(
                        """
                        UPDATE users 
                        SET balance_tokens = balance_tokens - ?
                        WHERE telegram_id = ?
                        """,
                        (wager, loser_id)
                    )
                    
                    # Добавляем транзакции
                    self.add_transaction(
                        user_id=winner_id,
                        transaction_type='duel_win',
                        amount=wager * 2,
                        description=f'Победа в дуэли {duel_id}'
                    )
                    
                    self.add_transaction(
                        user_id=loser_id,
                        transaction_type='duel_loss',
                        amount=-wager,
                        description=f'Проигрыш в дуэли {duel_id}'
                    )
                
                conn.commit()
                logger.info(f"Обновлен результат дуэли {duel_id}: победитель {winner_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления результата дуэли {duel_id}: {e}")
            return False
    
    def get_user_duels(self, user_id: int, status: str = None) -> List[Dict[str, Any]]:
        """Получение дуэлей пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute(
                        """
                        SELECT * FROM duels 
                        WHERE (challenger_id = ? OR opponent_id = ?)
                        AND status = ?
                        ORDER BY created_at DESC
                        """,
                        (user_id, user_id, status)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM duels 
                        WHERE challenger_id = ? OR opponent_id = ?
                        ORDER BY created_at DESC
                        """,
                        (user_id, user_id)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения дуэлей пользователя {user_id}: {e}")
            return []
    
    # ==================== МЕТОДЫ УВЕДОМЛЕНИЙ ====================
    
    def add_notification(self, user_id: int, notification_data: Dict[str, Any]) -> bool:
        """Добавление уведомления"""
        required_fields = ['notification_type', 'title', 'message']
        
        if not all(field in notification_data for field in required_fields):
            logger.error(f"Отсутствуют обязательные поля уведомления: {required_fields}")
            return False
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(notification_data.get('metadata', {}))
                
                cursor.execute(
                    """
                    INSERT INTO notifications (
                        user_id, notification_type, title, message, action_url, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        notification_data['notification_type'],
                        notification_data['title'],
                        notification_data['message'],
                        notification_data.get('action_url', ''),
                        metadata_json
                    )
                )
                
                conn.commit()
                logger.debug(f"Добавлено уведомление пользователю {user_id}: {notification_data['title']}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления уведомления пользователю {user_id}: {e}")
            return False
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                              limit: int = 20) -> List[Dict[str, Any]]:
        """Получение уведомлений пользователя"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if unread_only:
                    cursor.execute(
                        """
                        SELECT * FROM notifications 
                        WHERE user_id = ? AND is_read = 0
                        ORDER BY created_at DESC
                        LIMIT ?
                        """,
                        (user_id, limit)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM notifications 
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                        """,
                        (user_id, limit)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения уведомлений пользователя {user_id}: {e}")
            return []
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Пометить уведомление как прочитанное"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notifications SET is_read = 1 WHERE id = ?",
                    (notification_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка пометки уведомления {notification_id} как прочитанного: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id: int) -> bool:
        """Пометить все уведомления пользователя как прочитанные"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка пометки всех уведомлений пользователя {user_id} как прочитанных: {e}")
            return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Получение количества непрочитанных уведомлений"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
                    (user_id,)
                )
                return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества непрочитанных уведомлений пользователя {user_id}: {e}")
            return 0
    
    # ==================== АДМИНИСТРАТИВНЫЕ МЕТОДЫ ====================
    
    def backup_database(self, backup_path: str) -> bool:
        """Создание резервной копии базы данных"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Создана резервная копия базы данных: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return False
    
    def execute_sql(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполнение произвольного SQL запроса (только для админов)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                
                if sql.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return [{'affected_rows': cursor.rowcount}]
        except Exception as e:
            logger.error(f"Ошибка выполнения SQL: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Размер базы данных
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size'] = cursor.fetchone()[0]
                
                # Количество записей в таблицах
                tables = ['users', 'referral_connections', 'transactions', 'achievements', 
                         'shop_items', 'purchases', 'trainings', 'duels', 'notifications']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Последние действия
                cursor.execute("SELECT MAX(created_at) FROM users")
                stats['last_user_registration'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(created_at) FROM transactions")
                stats['last_transaction'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Очистка старых данных"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                deleted_counts = {}
                
                # Очистка старых уведомлений
                cursor.execute(
                    """
                    DELETE FROM notifications 
                    WHERE created_at < datetime('now', '-' || ? || ' days')
                    AND is_read = 1
                    """,
                    (days,)
                )
                deleted_counts['notifications'] = cursor.rowcount
                
                # Очистка старых транзакций (кроме важных)
                cursor.execute(
                    """
                    DELETE FROM transactions 
                    WHERE created_at < datetime('now', '-' || ? || ' days')
                    AND transaction_type NOT IN ('purchase', 'duel_win', 'duel_loss', 'referral_bonus')
                    """,
                    (days * 2,)
                )
                deleted_counts['transactions'] = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Очищены старые данные: {deleted_counts}")
                return deleted_counts
                
        except Exception as e:
            logger.error(f"Ошибка очистки старых данных: {e}")
            return {}