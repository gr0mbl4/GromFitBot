"""
Модуль для работы с базой данных GromFitBot
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import random
import string

from src.core.config import Config

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Инициализация базы данных"""
        self.db_path = db_path or Config.DB_PATH
        self.connection = None
        self._initialize()
    
    def _get_connection(self):
        """Получение соединения с базой данных"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def _initialize(self):
        """Инициализация базы данных (создание таблиц при необходимости)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу users, если её нет
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
        
        # Создаем индексы для оптимизации
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_registration_number ON users(registration_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_referrer_id ON users(referrer_id)')
        
        # Таблица реферальных связей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                connection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bonus_paid BOOLEAN DEFAULT 0,
                FOREIGN KEY (referrer_id) REFERENCES users(id),
                FOREIGN KEY (referred_id) REFERENCES users(id),
                UNIQUE(referred_id)
            )
        ''')
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Таблица достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                achievement_description TEXT,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, achievement_id)
            )
        ''')
        
        # Таблица товаров магазина
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                item_description TEXT,
                item_type TEXT NOT NULL,
                price_tokens DECIMAL(15,2) NOT NULL,
                price_diamonds DECIMAL(15,2),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("✅ База данных инициализирована")
    
    # ==================== МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ====================
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Создание нового пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Генерируем регистрационный номер
            registration_number = generate_registration_number()
            
            cursor.execute('''
                INSERT INTO users (
                    telegram_id, registration_number, username, nickname, 
                    region, referrer_id, balance_tokens, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['telegram_id'],
                registration_number,
                user_data.get('username'),
                user_data['nickname'],
                user_data.get('region', 'Не указан'),
                user_data.get('referrer_id'),
                Config.STARTING_BALANCE,
                datetime.now().isoformat()
            ))
            
            user_id = cursor.lastrowid
            
            # Если есть реферер, обновляем его счетчик рефералов
            if user_data.get('referrer_id'):
                self._update_referrer_count(user_data['referrer_id'])
                
                # Создаем запись в таблице реферальных связей
                cursor.execute('''
                    INSERT INTO referral_connections (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (user_data['referrer_id'], user_data['telegram_id']))
            
            conn.commit()
            logger.info(f"✅ Создан пользователь: {user_data['nickname']} (ID: {registration_number})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID (совместимость со старым кодом)"""
        return self.get_user_by_telegram_id(user_id)
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по telegram_id"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя: {e}")
            return None
    
    def get_user_by_registration_number(self, reg_number: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по регистрационному номеру"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE registration_number = ?', (reg_number,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя: {e}")
            return None
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Обновление данных пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Формируем SET часть запроса
            set_parts = []
            values = []
            
            for key, value in data.items():
                set_parts.append(f"{key} = ?")
                values.append(value)
            
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(set_parts)} WHERE telegram_id = ?"
            cursor.execute(query, values)
            conn.commit()
            
            logger.info(f"✅ Обновлен пользователь с ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении пользователя: {e}")
            return False
    
    def update_user_last_active(self, telegram_id: int) -> bool:
        """Обновление времени последней активности пользователя"""
        return self.update_user(telegram_id, {'last_active': datetime.now().isoformat()})
    
    # ==================== МЕТОДЫ ДЛЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ ====================
    
    def _update_referrer_count(self, referrer_id: int):
        """Обновление счетчика рефералов"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET referrals_count = referrals_count + 1 
                WHERE telegram_id = ?
            ''', (referrer_id,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении счетчика рефералов: {e}")
    
    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Добавление реферальной связи"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Проверяем, существует ли уже такая связь
            cursor.execute('''
                SELECT id FROM referral_connections 
                WHERE referred_id = ?
            ''', (referred_id,))
            
            if cursor.fetchone():
                return False
            
            # Создаем новую связь
            cursor.execute('''
                INSERT INTO referral_connections (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении реферальной связи: {e}")
            return False
    
    def get_referrals(self, referrer_id: int) -> List[Dict[str, Any]]:
        """Получение списка рефералов пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.* FROM users u
                JOIN referral_connections rc ON u.telegram_id = rc.referred_id
                WHERE rc.referrer_id = ?
                ORDER BY rc.connection_date DESC
            ''', (referrer_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении рефералов: {e}")
            return []
    
    def get_referrals_count(self, referrer_id: int) -> int:
        """Получение количества рефералов пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) as count FROM referral_connections 
                WHERE referrer_id = ?
            ''', (referrer_id,))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении количества рефералов: {e}")
            return 0
    
    def get_referral_stats(self, referrer_id: int) -> Dict[str, Any]:
        """Получение статистики рефералов"""
        referrals = self.get_referrals(referrer_id)
        referrals_count = len(referrals)
        
        # Определяем активных рефералов (тех, кто был активен в последние 7 дней)
        active_count = 0
        week_ago = datetime.now().timestamp() - 7 * 24 * 60 * 60
        
        for referral in referrals:
            last_active = referral.get('last_active')
            if last_active:
                if isinstance(last_active, str):
                    try:
                        last_active_dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    except:
                        continue
                else:
                    last_active_dt = last_active
                
                if last_active_dt.timestamp() > week_ago:
                    active_count += 1
        
        # Расчет конверсии (процент активных от общего числа)
        conversion_rate = (active_count / referrals_count * 100) if referrals_count > 0 else 0
        
        return {
            'total_referrals': referrals_count,
            'active_referrals': active_count,
            'conversion_rate': round(conversion_rate, 2)
        }
    
    # ==================== МЕТОДЫ ДЛЯ ТРАНЗАКЦИЙ ====================
    
    def add_transaction(self, user_id: int, transaction_type: str, 
                       amount: float, description: str = "") -> bool:
        """Добавление транзакции"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions (user_id, transaction_type, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, transaction_type, amount, description))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении транзакции: {e}")
            return False
    
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение транзакций пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении транзакций: {e}")
            return []
    
    # ==================== МЕТОДЫ ДЛЯ СТАТИСТИКИ ====================
    
    def get_total_users_count(self) -> int:
        """Получение общего количества пользователей"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM users')
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении количества пользователей: {e}")
            return 0
    
    def get_total_referrals_count(self) -> int:
        """Получение общего количества реферальных связей"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM referral_connections')
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении количества рефералов: {e}")
            return 0
    
    def get_total_transactions_count(self) -> int:
        """Получение общего количества транзакций"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM transactions')
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении количества транзакций: {e}")
            return 0
    
    # ==================== МЕТОДЫ ДЛЯ МАГАЗИНА ====================
    
    def get_shop_items(self, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение товаров магазина"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if item_type:
                cursor.execute('''
                    SELECT * FROM shop_items 
                    WHERE is_active = 1 AND item_type = ?
                    ORDER BY price_tokens ASC
                ''', (item_type,))
            else:
                cursor.execute('''
                    SELECT * FROM shop_items 
                    WHERE is_active = 1 
                    ORDER BY item_type, price_tokens ASC
                ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении товаров магазина: {e}")
            return []
    
    # ==================== МЕТОДЫ ДЛЯ ДОСТИЖЕНИЙ ====================
    
    def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение достижений пользователя"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM achievements 
                WHERE user_id = ? 
                ORDER BY achieved_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении достижений: {e}")
            return []
    
    def add_achievement(self, user_id: int, achievement_id: str, 
                       name: str, description: str = "") -> bool:
        """Добавление достижения пользователю"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO achievements 
                (user_id, achievement_id, achievement_name, achievement_description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, achievement_id, name, description))
            
            if cursor.rowcount > 0:
                # Обновляем счетчик достижений
                cursor.execute('''
                    UPDATE users 
                    SET achievements_count = achievements_count + 1 
                    WHERE telegram_id = ?
                ''', (user_id,))
                conn.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении достижения: {e}")
            return False
    
    # ==================== УТИЛИТЫ ====================
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __del__(self):
        """Деструктор для закрытия соединения"""
        self.close()

# Вспомогательные функции
def generate_registration_number() -> str:
    """Генерация уникального регистрационного номера"""
    # GFXXXXXXXXXXYYY
    # GF - префикс
    # X - цифры (10 символов)
    # Y - буквы (3 символа)
    
    digits = ''.join(random.choices(string.digits, k=10))
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    
    return f"GF{digits}{letters}"