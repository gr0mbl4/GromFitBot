"""
Модуль для работы с базой данных с обновленными бонусами
"""

import sqlite3
import logging
import random
import string
from datetime import datetime
from pathlib import Path

from .config import config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных"""
        try:
            # Создаем директорию если она не существует
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            # Создаем таблицы
            self._create_tables()
            
            logger.info(f"[OK] База данных инициализирована: {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    def _create_tables(self):
        """Создание всех необходимых таблиц"""
        
        # ========== ПОЛЬЗОВАТЕЛИ ==========
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                registration_number TEXT UNIQUE NOT NULL,
                username TEXT,
                nickname TEXT NOT NULL,
                region TEXT DEFAULT 'no region',
                referral_code TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrer_id INTEGER,
                referrals_count INTEGER DEFAULT 0,
                
                -- Система токенов
                balance_tokens DECIMAL(15,2) DEFAULT 0.00,
                total_earned_tokens DECIMAL(15,2) DEFAULT 0.00,
                total_spent_tokens DECIMAL(15,2) DEFAULT 0.00,
                
                -- Ежедневный бонус
                last_bonus_claim TIMESTAMP,
                
                -- Статусы
                is_active BOOLEAN DEFAULT 1,
                
                UNIQUE(telegram_id)
            )
        ''')
        
        # ========== РЕФЕРАЛЬНЫЕ СВЯЗИ ==========
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS referral_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referral_id INTEGER NOT NULL,
                connection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bonus_paid BOOLEAN DEFAULT 0,
                bonus_paid_date TIMESTAMP,
                referrer_bonus_paid DECIMAL(10,2) DEFAULT 0.00,
                referral_bonus_paid DECIMAL(10,2) DEFAULT 0.00,
                UNIQUE(referrer_id, referral_id)
            )
        ''')
        
        # ========== ТРАНЗАКЦИИ ТОКЕНОВ ==========
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS token_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                transaction_type TEXT NOT NULL,
                -- deposit, withdrawal, referral_bonus, achievement, duel_win, duel_loss, registration_bonus, daily_bonus
                balance_before DECIMAL(15,2) NOT NULL,
                balance_after DECIMAL(15,2) NOT NULL,
                related_id TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== АЧИВКИ РЕФЕРАЛОВ ==========
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS referral_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 100,
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # ========== ИНДЕКСЫ ==========
        indexes = [
            # Пользователи
            "CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_reg_number ON users(registration_number)",
            "CREATE INDEX IF NOT EXISTS idx_referral_code ON users(referral_code)",
            "CREATE INDEX IF NOT EXISTS idx_referrer_id ON users(referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_last_bonus ON users(last_bonus_claim)",
            
            # Реферальные связи
            "CREATE INDEX IF NOT EXISTS idx_ref_connections ON referral_connections(referrer_id, referral_id)",
            "CREATE INDEX IF NOT EXISTS idx_ref_date ON referral_connections(connection_date)",
            
            # Транзакции
            "CREATE INDEX IF NOT EXISTS idx_transactions_user ON token_transactions(user_id, created_at)",
            
            # Ачивки
            "CREATE INDEX IF NOT EXISTS idx_ref_achievements ON referral_achievements(user_id, achievement_id)",
        ]
        
        for idx_sql in indexes:
            try:
                self.conn.execute(idx_sql)
            except Exception as e:
                logger.error(f"Error creating index: {e}")
        
        self.conn.commit()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполнить SQL запрос"""
        return self.conn.execute(query, params)
    
    def commit(self):
        """Сохранить изменения"""
        self.conn.commit()
    
    def close(self):
        """Закрыть соединение с БД"""
        if self.conn:
            self.conn.close()
    
    # ========== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========
    
    def generate_registration_number(self, telegram_id: int) -> str:
        """Генерация ID: GFXXXXXXXXXXYYY"""
        random_part = ''.join(random.choices(string.ascii_uppercase, k=3))
        return f"GF{telegram_id}{random_part}"
    
    def user_exists(self, telegram_id: int) -> bool:
        """Проверяет, существует ли пользователь"""
        cursor = self.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return cursor.fetchone() is not None
    
    def get_user(self, telegram_id: int):
        """Получает пользователя по telegram_id"""
        cursor = self.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return cursor.fetchone()
    
    def create_user(self, telegram_id: int, nickname: str, username: str = None, 
                   region: str = "no region", referrer_id: int = None):
        """Создает нового пользователя (старый метод)"""
        return self.create_user_with_bonus(telegram_id, nickname, username, region, referrer_id)
    
    def create_user_with_bonus(self, telegram_id: int, nickname: str, username: str = None, 
                              region: str = "no region", referrer_id: int = None):
        """Создает нового пользователя с бонусом за регистрацию"""
        
        # Проверяем, не существует ли уже пользователь
        if self.user_exists(telegram_id):
            # Обновляем данные существующего пользователя
            self.execute('''
                UPDATE users 
                SET nickname = ?, username = ?, region = ?, last_active = ?
                WHERE telegram_id = ?
            ''', (nickname, username, region, datetime.now(), telegram_id))
            
            cursor = self.execute(
                "SELECT registration_number FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            reg_number = cursor.fetchone()[0]
        else:
            # Создаем нового пользователя
            reg_number = self.generate_registration_number(telegram_id)
            
            # НАЧАЛЬНЫЙ БАЛАНС: 50 токенов за регистрацию
            initial_balance = 50.00
            
            self.execute('''
                INSERT INTO users 
                (telegram_id, registration_number, username, nickname, region, 
                 referrer_id, balance_tokens, total_earned_tokens, created_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (telegram_id, reg_number, username, nickname, region, 
                  referrer_id, initial_balance, initial_balance))
            
            # Записываем транзакцию за регистрационный бонус
            transaction_id = f"reg_bonus_{int(datetime.now().timestamp())}_{telegram_id}"
            self.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, initial_balance, "registration_bonus",
                  0.00, initial_balance, f"Бонус за регистрацию"))
            
            # Если есть реферер, увеличиваем его счетчик рефералов и начисляем 25 токенов
            if referrer_id:
                self.execute('''
                    UPDATE users 
                    SET referrals_count = referrals_count + 1 
                    WHERE telegram_id = ?
                ''', (referrer_id,))
                
                # НАЧИСЛЯЕМ ОБНОВЛЕННЫЙ БОНУС РЕФЕРЕРУ: 25 токенов
                referral_bonus = 25.00
                try:
                    # Получаем текущий баланс реферера
                    cursor = self.execute(
                        "SELECT balance_tokens, total_earned_tokens FROM users WHERE telegram_id = ?",
                        (referrer_id,)
                    )
                    referrer_user = cursor.fetchone()
                    
                    if referrer_user:
                        balance_before = float(referrer_user['balance_tokens']) if referrer_user['balance_tokens'] is not None else 0.00
                        balance_after = balance_before + referral_bonus
                        
                        # Обновляем баланс реферера
                        self.execute('''
                            UPDATE users 
                            SET balance_tokens = ?, 
                                total_earned_tokens = total_earned_tokens + ?
                            WHERE telegram_id = ?
                        ''', (balance_after, referral_bonus, referrer_id))
                        
                        # Записываем транзакцию
                        transaction_id = f"tx_ref_{int(datetime.now().timestamp())}_{referrer_id}"
                        self.execute('''
                            INSERT INTO token_transactions 
                            (transaction_id, user_id, amount, transaction_type, 
                             balance_before, balance_after, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (transaction_id, referrer_id, referral_bonus, "referral_bonus",
                              balance_before, balance_after, f"Бонус за приглашение {nickname}"))
                        
                        # НАЧИСЛЯЕМ ДОПОЛНИТЕЛЬНЫЕ 50 ТОКЕНОВ ПРИГЛАШЕННОМУ (поверх 50 за регистрацию)
                        referral_additional_bonus = 50.00
                        referrer_balance_before = initial_balance
                        referrer_balance_after = referrer_balance_before + referral_additional_bonus
                        
                        # Обновляем баланс приглашенного
                        self.execute('''
                            UPDATE users 
                            SET balance_tokens = ?, 
                                total_earned_tokens = total_earned_tokens + ?
                            WHERE telegram_id = ?
                        ''', (referrer_balance_after, referral_additional_bonus, telegram_id))
                        
                        # Записываем транзакцию для приглашенного
                        transaction_id = f"tx_ref_inv_{int(datetime.now().timestamp())}_{telegram_id}"
                        self.execute('''
                            INSERT INTO token_transactions 
                            (transaction_id, user_id, amount, transaction_type, 
                             balance_before, balance_after, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (transaction_id, telegram_id, referral_additional_bonus, "referral_invited_bonus",
                              referrer_balance_before, referrer_balance_after, f"Бонус за приглашение от друга"))
                        
                        # Создаем запись о реферальной связи с обновленными бонусами
                        try:
                            self.execute('''
                                INSERT INTO referral_connections 
                                (referrer_id, referral_id, bonus_paid, bonus_paid_date,
                                 referrer_bonus_paid, referral_bonus_paid)
                                VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
                            ''', (referrer_id, telegram_id, referral_bonus, referral_additional_bonus))
                        except sqlite3.IntegrityError:
                            # Связь уже существует
                            self.execute('''
                                UPDATE referral_connections 
                                SET bonus_paid = 1, 
                                    bonus_paid_date = CURRENT_TIMESTAMP,
                                    referrer_bonus_paid = ?,
                                    referral_bonus_paid = ?
                                WHERE referrer_id = ? AND referral_id = ?
                            ''', (referral_bonus, referral_additional_bonus, referrer_id, telegram_id))
                except Exception as e:
                    logger.error(f"Error adding referral bonus: {e}")
        
        self.commit()
        
        # Получаем данные пользователя
        return self.get_user(telegram_id)
    
    def update_user_activity(self, telegram_id: int):
        """Обновляет время последней активности"""
        self.execute(
            "UPDATE users SET last_active = ? WHERE telegram_id = ?",
            (datetime.now(), telegram_id)
        )
        self.commit()
    
    def get_referrals_count(self, telegram_id: int) -> int:
        """Получает количество приглашенных пользователей"""
        try:
            cursor = self.execute(
                "SELECT referrals_count FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            result = cursor.fetchone()
            return result['referrals_count'] if result and 'referrals_count' in result.keys() else 0
        except sqlite3.OperationalError as e:
            # Если колонки еще не существует
            logger.warning(f"Column 'referrals_count' not found: {e}")
            return 0
    
    # ========== СИСТЕМА ЕЖЕДНЕВНЫХ БОНУСОВ ==========
    
    def can_claim_daily_bonus(self, telegram_id: int) -> tuple[bool, str]:
        """Проверяет, может ли пользователь получить ежедневный бонус"""
        cursor = self.execute(
            "SELECT last_bonus_claim FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = cursor.fetchone()
        
        if not result or result['last_bonus_claim'] is None:
            return True, "Бонус доступен"
        
        last_claim = datetime.strptime(result['last_bonus_claim'], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Проверяем, прошло ли более 24 часов с момента последнего получения
        # Или наступило ли время сброса (после 03:00 по МСК)
        hours_since_last = (now - last_claim).total_seconds() / 3600
        
        # Если сейчас после 03:00 по МСК и последнее получение было до 03:00 сегодня
        # или прошло более 24 часов
        if now.hour >= 3:
            # Проверяем, было ли последнее получение до 03:00 сегодня
            today_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if last_claim < today_3am:
                return True, "Бонус доступен"
        else:
            # Если сейчас до 03:00, проверяем, было ли последнее получение до 03:00 вчера
            yesterday_3am = (now.replace(hour=3, minute=0, second=0, microsecond=0) - 
                           datetime.timedelta(days=1))
            if last_claim < yesterday_3am:
                return True, "Бонус доступен"
        
        # Рассчитываем время до следующего доступного бонуса
        if now.hour >= 3:
            next_bonus_time = (now + datetime.timedelta(days=1)).replace(hour=3, minute=0, second=0)
        else:
            next_bonus_time = now.replace(hour=3, minute=0, second=0)
        
        time_left = next_bonus_time - now
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        
        return False, f"Следующий бонус через {hours_left}ч {minutes_left}м"
    
    def claim_daily_bonus(self, telegram_id: int, bonus_amount: float = 10.00) -> bool:
        """Выдача ежедневного бонуса пользователю"""
        try:
            # Получаем текущий баланс
            cursor = self.execute(
                "SELECT balance_tokens, total_earned_tokens FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0.00
            balance_after = balance_before + bonus_amount
            
            # Обновляем баланс и время последнего получения бонуса
            self.execute('''
                UPDATE users 
                SET balance_tokens = ?, 
                    total_earned_tokens = total_earned_tokens + ?,
                    last_bonus_claim = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (balance_after, bonus_amount, telegram_id))
            
            # Записываем транзакцию
            transaction_id = f"daily_{int(datetime.now().timestamp())}_{telegram_id}"
            self.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, bonus_amount, "daily_bonus",
                  balance_before, balance_after, "Ежедневный бонус"))
            
            self.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error claiming daily bonus: {e}")
            return False
    
    # ========== СИСТЕМА ТОКЕНОВ ==========
    
    def get_balance(self, telegram_id: int) -> float:
        """Получение баланса пользователя"""
        cursor = self.execute(
            "SELECT balance_tokens FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = cursor.fetchone()
        if result and result['balance_tokens'] is not None:
            return float(result['balance_tokens'])
        return 0.00
    
    def add_tokens(self, telegram_id: int, amount: float, 
                  transaction_type: str, description: str = "") -> bool:
        """Добавление токенов пользователю"""
        return self._add_tokens_internal(telegram_id, amount, transaction_type, description)
    
    def _add_tokens_internal(self, user_id: int, amount: float, 
                           transaction_type: str, description: str = "") -> bool:
        """Внутренний метод добавления токенов"""
        try:
            # Получаем текущий баланс
            cursor = self.execute(
                "SELECT balance_tokens, total_earned_tokens FROM users WHERE telegram_id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0.00
            balance_after = balance_before + amount
            
            # Обновляем баланс
            self.execute('''
                UPDATE users 
                SET balance_tokens = ?, 
                    total_earned_tokens = total_earned_tokens + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, user_id))
            
            # Генерируем ID транзакции
            transaction_id = f"tx_{int(datetime.now().timestamp())}_{user_id}"
            
            # Записываем транзакцию
            self.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, user_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding tokens: {e}")
            return False
    
    def deduct_tokens(self, telegram_id: int, amount: float, 
                     transaction_type: str, description: str = "") -> bool:
        """Списание токенов у пользователя"""
        return self._deduct_tokens_internal(telegram_id, amount, transaction_type, description)
    
    def _deduct_tokens_internal(self, user_id: int, amount: float, 
                              transaction_type: str, description: str = "") -> bool:
        """Внутренний метод списания токенов"""
        try:
            # Получаем текущий баланс
            cursor = self.execute(
                "SELECT balance_tokens, total_spent_tokens FROM users WHERE telegram_id = ?",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0.00
            
            # Проверяем, достаточно ли средств
            if balance_before < amount:
                return False
            
            balance_after = balance_before - amount
            
            # Обновляем баланс
            self.execute('''
                UPDATE users 
                SET balance_tokens = ?, 
                    total_spent_tokens = total_spent_tokens + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, user_id))
            
            # Генерируем ID транзакции
            transaction_id = f"tx_{int(datetime.now().timestamp())}_{user_id}"
            
            # Записываем транзакцию
            self.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, user_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deducting tokens: {e}")
            return False
    
    def get_transaction_history(self, telegram_id: int, limit: int = 20):
        """Получение истории транзакций"""
        try:
            cursor = self.execute('''
                SELECT transaction_id, amount, transaction_type, 
                       balance_before, balance_after, description, created_at
                FROM token_transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (telegram_id, limit))
            
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    def get_total_tokens_in_system(self) -> float:
        """Общее количество токенов в системе"""
        try:
            cursor = self.execute(
                "SELECT SUM(balance_tokens) as total FROM users"
            )
            result = cursor.fetchone()
            if result and result['total'] is not None:
                return float(result['total'])
        except Exception as e:
            logger.error(f"Error getting total tokens: {e}")
        return 0.00
    
    # ========== РЕЙТИНГ РЕФЕРАЛОВ ==========
    
    def get_referral_rank_title(self, referrals_count: int) -> str:
        """Получение звания по количеству рефералов"""
        if referrals_count >= 100:
            return "🎖️ Легенда приглашений"
        elif referrals_count >= 50:
            return "👑 Король рефералов"
        elif referrals_count >= 30:
            return "⭐ Мастер сети"
        elif referrals_count >= 20:
            return "🚀 Лидер сообщества"
        elif referrals_count >= 15:
            return "🔥 Гуру приглашений"
        elif referrals_count >= 10:
            return "👔 Глава секты"
        elif referrals_count >= 5:
            return "🤝 Дружелюбный"
        elif referrals_count >= 3:
            return "🤗 Общительный"
        elif referrals_count >= 1:
            return "👋 Лучший друг"
        else:
            return "😊 Будущий приглашатель"
    
    def get_referral_rank_progress(self, referrals_count: int) -> dict:
        """Получение прогресса до следующего звания"""
        ranks = [
            (0, "😊 Будущий приглашатель"),
            (1, "👋 Лучший друг"),
            (3, "🤗 Общительный"),
            (5, "🤝 Дружелюбный"),
            (10, "👔 Глава секты"),
            (15, "🔥 Гуру приглашений"),
            (20, "🚀 Лидер сообщества"),
            (30, "⭐ Мастер сети"),
            (50, "👑 Король рефералов"),
            (100, "🎖️ Легенда приглашений")
        ]
        
        current_rank = ranks[0]
        next_rank = ranks[0]
        
        for count, title in ranks:
            if referrals_count >= count:
                current_rank = (count, title)
        
        # Находим следующий ранг
        for i, (count, title) in enumerate(ranks):
            if count > referrals_count:
                next_rank = (count, title)
                break
        else:
            # Если достигнут максимальный ранг
            next_rank = current_rank
        
        progress_percentage = 0
        if next_rank[0] > current_rank[0]:
            progress_percentage = int((referrals_count - current_rank[0]) / 
                                     (next_rank[0] - current_rank[0]) * 100)
        
        return {
            "current_rank": current_rank[1],
            "next_rank": next_rank[1],
            "current_count": referrals_count,
            "next_count": next_rank[0],
            "needed_for_next": max(0, next_rank[0] - referrals_count),
            "progress_percentage": min(100, progress_percentage)
        }
    
    def get_top_referrers(self, limit: int = 10):
        """Топ пользователей по количеству рефералов"""
        try:
            cursor = self.execute('''
                SELECT telegram_id, nickname, referrals_count, region,
                       balance_tokens
                FROM users
                WHERE referrals_count > 0
                ORDER BY referrals_count DESC
                LIMIT ?
            ''', (limit,))
            
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting top referrers: {e}")
            return []

# Глобальный экземпляр БД
db = Database()