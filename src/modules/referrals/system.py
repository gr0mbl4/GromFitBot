"""
Ядро реферальной системы с обновленными бонусами
"""

import logging
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from src.core.database import db
from src.core.config import config

logger = logging.getLogger(__name__)

class ReferralSystem:
    """Система управления рефералами с обновленными бонусами"""
    
    def __init__(self, db_connection = None):
        self.db = db_connection or db.conn
        self.token_system = None  # Будет установлено извне
    
    def set_token_system(self, token_system):
        """Установка системы токенов"""
        self.token_system = token_system
    
    def generate_referral_code(self, telegram_id: int) -> str:
        """Генерация уникального реферального кода"""
        # Формат: r-XXXXXX где XXXXXX - хэш от telegram_id
        seed = f"{telegram_id}-gromfit-2026"
        hash_obj = hashlib.md5(seed.encode()).hexdigest()[:6].upper()
        return f"r-{hash_obj}"
    
    def get_or_create_referral_code(self, telegram_id: int) -> str:
        """Получение или создание реферального кода для пользователя"""
        
        # Проверяем, есть ли уже код у пользователя
        cursor = self.db.execute(
            "SELECT referral_code FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        result = cursor.fetchone()
        
        if result and result['referral_code']:
            return result['referral_code']
        
        # Генерируем новый код
        referral_code = self.generate_referral_code(telegram_id)
        
        # Сохраняем в БД
        self.db.execute(
            "UPDATE users SET referral_code = ? WHERE telegram_id = ?",
            (referral_code, telegram_id)
        )
        self.db.commit()
        
        return referral_code
    
    def get_referral_link(self, telegram_id: int) -> str:
        """Получение реферальной ссылки"""
        code = self.get_or_create_referral_code(telegram_id)
        bot_username = "GromFit_bot"  # Можно получить из конфига или API
        return f"https://t.me/{bot_username}?start={code}"
    
    def process_referral_start(self, telegram_id: int, referral_code: str) -> Dict:
        """Обработка перехода по реферальной ссылке"""
        
        # Проверяем валидность кода
        if not referral_code.startswith('r-') or len(referral_code) != 8:
            return {"success": False, "message": "Неверный реферальный код"}
        
        # Находим реферера по коду
        cursor = self.db.execute(
            "SELECT telegram_id, nickname FROM users WHERE referral_code = ?",
            (referral_code,)
        )
        referrer = cursor.fetchone()
        
        if not referrer:
            return {"success": False, "message": "Реферальный код не найден"}
        
        referrer_id = referrer['telegram_id']
        referrer_name = referrer['nickname']
        
        # Проверяем, не пытается ли пользователь пригласить себя
        if referrer_id == telegram_id:
            return {"success": False, "message": "Нельзя использовать свою реферальную ссылку"}
        
        return {
            "success": True,
            "referrer_id": referrer_id,
            "referrer_name": referrer_name,
            "referral_code": referral_code,
            "message": f"Вы приглашены пользователем {referrer_name}"
        }
    
    def complete_referral_registration(self, referrer_id: int, referral_id: int) -> Dict:
        """Завершение реферальной регистрации с начислением обновленных бонусов"""
        
        # Записываем реферальную связь
        self._record_referral_connection(referrer_id, referral_id)
        
        # Начисляем обновленные бонусы: 25 токенов пригласившему, 50 токенов приглашенному
        if self.token_system:
            bonus_result = self.token_system.award_referral_bonus_updated(referrer_id, referral_id)
            
            # Проверяем и разблокируем достижения реферера (без бонусных токенов)
            self._check_referral_achievements(referrer_id)
            
            return {
                "success": True,
                "bonus_result": bonus_result,
                "message": f"Реферальная регистрация завершена. Бонусы начислены."
            }
        
        return {
            "success": True,
            "message": "Реферальная регистрация завершена (система токенов не подключена)"
        }
    
    def _record_referral_connection(self, referrer_id: int, referral_id: int):
        """Запись реферальной связи в отдельную таблицу с новыми бонусами"""
        
        # Добавляем запись о реферальной связи
        try:
            self.db.execute('''
                INSERT INTO referral_connections (referrer_id, referral_id, 
                referrer_bonus_paid, referral_bonus_paid)
                VALUES (?, ?, ?, ?)
            ''', (referrer_id, referral_id, 25.00, 50.00))
            self.db.commit()
            
            # Обновляем счетчик рефералов у пользователя
            self.db.execute('''
                UPDATE users 
                SET referrals_count = referrals_count + 1 
                WHERE telegram_id = ?
            ''', (referrer_id,))
            self.db.commit()
            
        except sqlite3.IntegrityError:
            # Связь уже существует
            pass
    
    def get_referral_stats(self, telegram_id: int) -> Dict:
        """Получение полной статистики рефералов"""
        
        # Основная статистика
        referrals_count = db.get_referrals_count(telegram_id)
        
        # Заработано на рефералах (в токенах) - обновленные бонусы
        cursor = self.db.execute('''
            SELECT SUM(referrer_bonus_paid) as total_earned
            FROM referral_connections
            WHERE referrer_id = ? AND bonus_paid = 1
        ''', (telegram_id,))
        
        earned_result = cursor.fetchone()
        total_earned_tokens = float(earred_result['total_earned'] or 0)
        
        # Рейтинг и прогресс
        rank_info = db.get_referral_rank_progress(referrals_count)
        
        # Список рефералов с деталями
        cursor = self.db.execute('''
            SELECT u.telegram_id, u.nickname, u.region, u.balance_tokens,
                   rc.connection_date, rc.bonus_paid, rc.bonus_paid_date,
                   rc.referrer_bonus_paid, rc.referral_bonus_paid
            FROM referral_connections rc
            JOIN users u ON rc.referral_id = u.telegram_id
            WHERE rc.referrer_id = ?
            ORDER BY rc.connection_date DESC
            LIMIT 50
        ''', (telegram_id,))
        
        referrals_list = cursor.fetchall()
        
        # Статистика по дням (последние 7 дней)
        cursor = self.db.execute('''
            SELECT DATE(connection_date) as day, COUNT(*) as count,
                   SUM(referrer_bonus_paid) as daily_earned
            FROM referral_connections
            WHERE referrer_id = ?
            GROUP BY DATE(connection_date)
            ORDER BY day DESC
            LIMIT 7
        ''', (telegram_id,))
        
        daily_stats = cursor.fetchall()
        
        # Общая эффективность
        active_referrals = len([r for r in referrals_list if r['bonus_paid']])
        conversion_rate = (active_referrals / referrals_count * 100) if referrals_count > 0 else 0
        
        return {
            "referrals_count": referrals_count,
            "total_earned_tokens": total_earned_tokens,
            "active_referrals": active_referrals,
            "conversion_rate": conversion_rate,
            "rank_info": rank_info,
            "referrals_list": referrals_list,
            "daily_stats": daily_stats,
            "referral_link": self.get_referral_link(telegram_id)
        }
    
    def _check_referral_achievements(self, user_id: int):
        """Проверка и разблокировка достижений рефералов (без бонусных токенов)"""
        
        referrals_count = db.get_referrals_count(user_id)
        
        # Список достижений рефералов
        referral_achievements = [
            (1, "ref_first", "👋 Первый реферал", "Пригласите первого друга"),
            (3, "ref_three", "🤗 Трое друзей", "Пригласите 3 друзей"),
            (5, "ref_five", "🤝 Пятерка", "Пригласите 5 друзей"),
            (10, "ref_ten", "👔 Десять последователей", "Пригласите 10 друзей"),
            (15, "ref_fifteen", "🔥 Команда мечты", "Пригласите 15 друзей"),
            (20, "ref_twenty", "🚀 Лидер команды", "Пригласите 20 друзей"),
            (30, "ref_thirty", "⭐ Создатель сети", "Пригласите 30 друзей"),
            (50, "ref_fifty", "👑 Король рефералов", "Пригласите 50 друзей"),
            (100, "ref_hundred", "🎖️ Легенда приглашений", "Пригласите 100 друзей"),
        ]
        
        # Проверяем каждое достижение
        for count, ach_id, ach_name, ach_desc in referral_achievements:
            if referrals_count >= count:
                self._unlock_referral_achievement(user_id, ach_id, ach_name, ach_desc)
    
    def _unlock_referral_achievement(self, user_id: int, achievement_id: str, 
                                    name: str, description: str):
        """Разблокировка достижения реферала (без бонусных токенов)"""
        
        # Проверяем, не разблокировано ли уже
        cursor = self.db.execute('''
            SELECT 1 FROM referral_achievements 
            WHERE user_id = ? AND achievement_id = ?
        ''', (user_id, achievement_id))
        
        if cursor.fetchone():
            return  # Уже разблокировано
        
        # Разблокируем достижение (без начисления токенов)
        self.db.execute('''
            INSERT INTO referral_achievements (user_id, achievement_id)
            VALUES (?, ?)
        ''', (user_id, achievement_id))
        
        self.db.commit()
        
        # Логируем разблокировку
        logger.info(f"Пользователь {user_id} разблокировал достижение рефералов: {name}")
    
    def get_user_referral_achievements(self, telegram_id: int) -> List[Dict]:
        """Получение достижений рефералов пользователя"""
        
        cursor = self.db.execute('''
            SELECT ra.achievement_id, ra.unlocked_at, ra.progress
            FROM referral_achievements ra
            WHERE ra.user_id = ?
            ORDER BY ra.unlocked_at
        ''', (telegram_id,))
        
        achievements = cursor.fetchall()
        
        # Маппинг ID достижений на названия
        achievement_map = {
            "ref_first": {"name": "👋 Первый реферал", "description": "Пригласите первого друга"},
            "ref_three": {"name": "🤗 Трое друзей", "description": "Пригласите 3 друзей"},
            "ref_five": {"name": "🤝 Пятерка", "description": "Пригласите 5 друзей"},
            "ref_ten": {"name": "👔 Десять последователей", "description": "Пригласите 10 друзей"},
            "ref_fifteen": {"name": "🔥 Команда мечты", "description": "Пригласите 15 друзей"},
            "ref_twenty": {"name": "🚀 Лидер команды", "description": "Пригласите 20 друзей"},
            "ref_thirty": {"name": "⭐ Создатель сети", "description": "Пригласите 30 друзей"},
            "ref_fifty": {"name": "👑 Король рефералов", "description": "Пригласите 50 друзей"},
            "ref_hundred": {"name": "🎖️ Легенда приглашений", "description": "Пригласите 100 друзей"},
        }
        
        formatted_achievements = []
        for ach in achievements:
            ach_info = achievement_map.get(ach['achievement_id'], {})
            formatted_achievements.append({
                "id": ach['achievement_id'],
                "name": ach_info.get("name", "Неизвестное достижение"),
                "description": ach_info.get("description", ""),
                "unlocked_at": ach['unlocked_at'],
                "progress": ach['progress']
            })
        
        return formatted_achievements
    
    def get_top_referrers_leaderboard(self, limit: int = 20) -> List[Dict]:
        """Таблица лидеров по рефералам"""
        
        top_users = db.get_top_referrers(limit)
        
        leaderboard = []
        for i, user in enumerate(top_users, 1):
            rank_title = db.get_referral_rank_title(user['referrals_count'])
            
            leaderboard.append({
                "rank": i,
                "telegram_id": user['telegram_id'],
                "nickname": user['nickname'],
                "region": user['region'],
                "referrals_count": user['referrals_count'],
                "rank_title": rank_title,
                "balance": float(user['balance_tokens']),
                "rating": user.get('rating_points', 0)
            })
        
        return leaderboard

# Глобальный экземпляр реферальной системы
referral_system = ReferralSystem()