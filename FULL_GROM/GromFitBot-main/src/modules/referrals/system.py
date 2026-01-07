"""
Система рефералов и рангов
Исправленная версия без ошибок .get()
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import os

from src.core.database import Database

logger = logging.getLogger(__name__)

class ReferralSystem:
    """Система рефералов и рангов"""
    
    def __init__(self):
        self.db = Database()
        
        # Бонусы за приглашение
        self.REFERRER_BONUS = 25
        self.REFERRED_BONUS = 50
        
        # Ранговая система (минимум приглашенных: название)
        self.REFERRAL_RANKS = {
            0: "Новичок",
            3: "Бронза",
            10: "Серебро",
            25: "Золото",
            50: "Платина",
            100: "Легенда"
        }
    
    def get_referral_link(self, telegram_id: int) -> str:
        """Генерация реферальной ссылки"""
        return f"https://t.me/gromfitbot?start=ref{telegram_id}"
    
    def get_referral_stats(self, telegram_id: int) -> Dict:
        """Получение полной статистики рефералов"""
        
        # Основная статистика
        referrals_count = self.db.get_referrals_count(telegram_id)
        
        # Получение заработанных токенов
        total_earned_tokens = 0.0
        
        try:
            db_path = 'data/users.db'
            if not os.path.exists(db_path):
                logger.error(f"База данных не найдена: {db_path}")
                # Создаем пустую базу если не существует
                return self._get_empty_stats(telegram_id)
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referral_connections'")
            if not cursor.fetchone():
                logger.warning("Таблица referral_connections не найдена")
                conn.close()
                return self._get_empty_stats(telegram_id)
            
            cursor.execute('''
                SELECT SUM(referrer_bonus_paid) as total_earned
                FROM referral_connections
                WHERE referrer_id = ? AND bonus_paid = 1
            ''', (telegram_id,))
            
            earned_result = cursor.fetchone()
            
            # БЕЗОПАСНОЕ ОБРАЩЕНИЕ К sqlite3.Row
            if earned_result is not None and 'total_earned' in earned_result.keys():
                total_earned = earned_result['total_earned']
                if total_earned is not None:
                    total_earned_tokens = float(total_earned)
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка получения статистики рефералов: {e}")
            total_earned_tokens = 0.0
        
        # Определение ранга
        current_rank = "Новичок"
        next_rank = None
        next_rank_required = 3
        progress_percentage = 0
        
        sorted_ranks = sorted(self.REFERRAL_RANKS.items())
        
        for i, (required, rank_name) in enumerate(sorted_ranks):
            if referrals_count >= required:
                current_rank = rank_name
                
                # Следующий ранг
                if i + 1 < len(sorted_ranks):
                    next_required, next_rank_name = sorted_ranks[i + 1]
                    next_rank = next_rank_name
                    next_rank_required = next_required
                    
                    # Прогресс к следующему рангу
                    prev_required = required
                    progress = referrals_count - prev_required
                    total_needed = next_required - prev_required
                    
                    if total_needed > 0:
                        progress_percentage = min(100, int((progress / total_needed) * 100))
        
        return {
            'referrals_count': referrals_count,
            'current_rank': current_rank,
            'next_rank': next_rank,
            'next_rank_required': next_rank_required,
            'progress_percentage': progress_percentage,
            'total_earned_tokens': total_earned_tokens,
            'referral_link': self.get_referral_link(telegram_id)
        }
    
    def _get_empty_stats(self, telegram_id: int) -> Dict:
        """Получение пустой статистики при ошибке БД"""
        return {
            'referrals_count': 0,
            'current_rank': "Новичок",
            'next_rank': "Бронза",
            'next_rank_required': 3,
            'progress_percentage': 0,
            'total_earned_tokens': 0.0,
            'referral_link': self.get_referral_link(telegram_id)
        }
    
    def get_referrals_list(self, telegram_id: int) -> List[Dict]:
        """Получение списка рефералов"""
        referrals = []
        
        try:
            db_path = 'data/users.db'
            if not os.path.exists(db_path):
                return referrals
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Проверяем существование таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referral_connections'")
            if not cursor.fetchone():
                conn.close()
                return referrals
            
            cursor.execute('''
                SELECT u.nickname, u.region, u.created_at, u.balance_tokens,
                       rc.bonus_paid, rc.referrer_bonus_paid
                FROM users u
                JOIN referral_connections rc ON u.telegram_id = rc.referred_id
                WHERE rc.referrer_id = ?
                ORDER BY u.created_at DESC
            ''', (telegram_id,))
            
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows, 1):
                # БЕЗОПАСНОЕ ОБРАЩЕНИЕ К sqlite3.Row
                row_dict = dict(row)
                
                nickname = row_dict.get('nickname', 'Без имени')
                region = row_dict.get('region', 'Не указан')
                created_at = row_dict.get('created_at', 'Неизвестно')
                
                balance_tokens = 0.0
                if 'balance_tokens' in row_dict and row_dict['balance_tokens'] is not None:
                    try:
                        balance_tokens = float(row_dict['balance_tokens'])
                    except:
                        balance_tokens = 0.0
                
                bonus_paid = bool(row_dict.get('bonus_paid', False))
                
                referrer_bonus_paid = 0.0
                if 'referrer_bonus_paid' in row_dict and row_dict['referrer_bonus_paid'] is not None:
                    try:
                        referrer_bonus_paid = float(row_dict['referrer_bonus_paid'])
                    except:
                        referrer_bonus_paid = 0.0
                
                referrals.append({
                    'number': i,
                    'nickname': nickname,
                    'region': region,
                    'created_at': created_at,
                    'balance_tokens': balance_tokens,
                    'bonus_paid': bonus_paid,
                    'referrer_bonus_paid': referrer_bonus_paid
                })
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка получения списка рефералов: {e}")
        
        return referrals
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Таблица лидеров (топ рефереров)"""
        leaders = []
        
        try:
            db_path = 'data/users.db'
            if not os.path.exists(db_path):
                return leaders
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.telegram_id, u.nickname, u.region, 
                       COUNT(rc.referred_id) as referrals_count,
                       SUM(rc.referrer_bonus_paid) as total_earned
                FROM users u
                LEFT JOIN referral_connections rc ON u.telegram_id = rc.referrer_id
                GROUP BY u.telegram_id
                ORDER BY referrals_count DESC, total_earned DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for i, row in enumerate(rows, 1):
                # БЕЗОПАСНОЕ ОБРАЩЕНИЕ К sqlite3.Row
                row_dict = dict(row)
                
                telegram_id = row_dict.get('telegram_id', 0)
                nickname = row_dict.get('nickname', 'Аноним')
                region = row_dict.get('region', 'Не указан')
                referrals_count = row_dict.get('referrals_count', 0)
                
                total_earned = 0.0
                if 'total_earned' in row_dict and row_dict['total_earned'] is not None:
                    try:
                        total_earned = float(row_dict['total_earned'])
                    except:
                        total_earned = 0.0
                
                leaders.append({
                    'place': i,
                    'telegram_id': telegram_id,
                    'nickname': nickname,
                    'region': region,
                    'referrals_count': referrals_count,
                    'total_earned': total_earned
                })
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка получения таблицы лидеров: {e}")
        
        return leaders
    
    def add_referral_connection(self, referrer_id: int, referred_id: int) -> bool:
        """Добавление реферальной связи"""
        try:
            db_path = 'data/users.db'
            if not os.path.exists(db_path):
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Проверяем существование таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='referral_connections'")
            if not cursor.fetchone():
                # Создаем таблицу если не существует
                cursor.execute('''
                    CREATE TABLE referral_connections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referrer_id INTEGER NOT NULL,
                        referred_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        bonus_paid BOOLEAN DEFAULT 0,
                        referrer_bonus_paid DECIMAL(15,2) DEFAULT 0,
                        UNIQUE(referrer_id, referred_id)
                    )
                ''')
            
            # Добавляем запись
            cursor.execute('''
                INSERT OR IGNORE INTO referral_connections (referrer_id, referred_id)
                VALUES (?, ?)
            ''', (referrer_id, referred_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления реферальной связи: {e}")
            return False