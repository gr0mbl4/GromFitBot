"""
Система токенов как внутренней валюты бота
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from src.core.database import db

logger = logging.getLogger(__name__)

class TokenSystem:
    """Система управления токенами"""
    
    def __init__(self):
        self.db = db
    
    # ========== ОСНОВНЫЕ ОПЕРАЦИИ ==========
    
    def get_balance(self, telegram_id: int) -> Dict:
        """Получение полной информации о балансе токенов"""
        user = db.get_user(telegram_id)
        
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Безопасное получение значений
        balance = float(user['balance_tokens']) if 'balance_tokens' in user.keys() else 0.00
        total_earned = float(user['total_earned_tokens']) if 'total_earned_tokens' in user.keys() else 0.00
        total_spent = float(user['total_spent_tokens']) if 'total_spent_tokens' in user.keys() else 0.00
        
        return {
            "balance": balance,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "available": balance,
            "formatted_balance": self._format_tokens(balance),
            "formatted_earned": self._format_tokens(total_earned),
            "formatted_spent": self._format_tokens(total_spent)
        }
    
    def award_referral_bonus(self, referrer_id: int, referral_id: int) -> Dict:
        """Начисление реферального бонуса в токенах"""
        
        # ФИКСИРОВАННЫЕ БОНУСЫ:
        # Реферер: 10 токенов
        # Реферал: 3 токена
        referrer_bonus = 10.00
        referral_bonus = 3.00
        
        # Начисляем рефереру
        referrer_success = self._add_tokens(
            telegram_id=referrer_id,
            amount=referrer_bonus,
            transaction_type="referral_bonus",
            description="Бонус за приглашение друга"
        )
        
        # Начисляем рефералу
        referral_success = self._add_tokens(
            telegram_id=referral_id,
            amount=referral_bonus,
            transaction_type="welcome_bonus",
            description="Приветственный бонус за регистрацию"
        )
        
        if not referrer_success or not referral_success:
            return {"error": "Ошибка начисления реферальных бонусов"}
        
        return {
            "success": True,
            "referrer_bonus": referrer_bonus,
            "referral_bonus": referral_bonus,
            "message": f"🎉 Бонусы начислены!"
        }
    
    def award_daily_bonus(self, telegram_id: int) -> Dict:
        """Начисление ежедневного бонуса (фиксированный: 5 токенов)"""
        
        daily_bonus = 5.00
        
        success = self._add_tokens(
            telegram_id=telegram_id,
            amount=daily_bonus,
            transaction_type="daily_bonus",
            description="Ежедневный бонус за активность"
        )
        
        if not success:
            return {"error": "Ошибка начисления бонуса"}
        
        return {
            "success": True,
            "amount": daily_bonus,
            "message": f"🎁 Получен ежедневный бонус: {self._format_tokens(daily_bonus)}!"
        }
    
    def award_achievement_bonus(self, telegram_id: int, amount: float, achievement_name: str) -> Dict:
        """Награда за достижение"""
        return self._add_tokens_with_message(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type="achievement",
            description=f"Награда за достижение: {achievement_name}",
            success_message=f"🏆 Получено {self._format_tokens(amount)} токенов за достижение '{achievement_name}'!"
        )
    
    def deduct_for_shop(self, telegram_id: int, amount: float, item_name: str) -> Dict:
        """Списание токенов за покупку в магазине"""
        return self._deduct_tokens_with_message(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type="shop_purchase",
            description=f"Покупка: {item_name}",
            error_message="Недостаточно токенов для покупки"
        )
    
    def _add_tokens(self, telegram_id: int, amount: float, 
                   transaction_type: str, description: str = "") -> bool:
        """Внутренний метод добавления токенов"""
        try:
            # Получаем текущий баланс
            cursor = self.db.execute(
                "SELECT balance_tokens, total_earned_tokens FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_tokens']) if user['balance_tokens'] is not None else 0.00
            balance_after = balance_before + amount
            
            # Обновляем баланс
            self.db.execute('''
                UPDATE users 
                SET balance_tokens = ?, 
                    total_earned_tokens = total_earned_tokens + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, telegram_id))
            
            # Генерируем ID транзакции
            transaction_id = f"tk_{int(datetime.now().timestamp())}_{telegram_id}"
            
            # Записываем транзакцию
            self.db.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding tokens: {e}")
            return False
    
    def _deduct_tokens(self, telegram_id: int, amount: float, 
                      transaction_type: str, description: str = "") -> bool:
        """Внутренний метод списания токенов"""
        try:
            # Получаем текущий баланс
            cursor = self.db.execute(
                "SELECT balance_tokens, total_spent_tokens FROM users WHERE telegram_id = ?",
                (telegram_id,)
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
            self.db.execute('''
                UPDATE users 
                SET balance_tokens = ?, 
                    total_spent_tokens = total_spent_tokens + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, telegram_id))
            
            # Генерируем ID транзакции
            transaction_id = f"tk_{int(datetime.now().timestamp())}_{telegram_id}"
            
            # Записываем транзакцию
            self.db.execute('''
                INSERT INTO token_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deducting tokens: {e}")
            return False
    
    def _add_tokens_with_message(self, telegram_id: int, amount: float,
                                transaction_type: str, description: str,
                                success_message: str) -> Dict:
        """Добавление токенов с возвратом сообщения"""
        success = self._add_tokens(telegram_id, amount, transaction_type, description)
        
        if not success:
            return {"error": "Ошибка начисления токенов"}
        
        new_balance = self.get_balance(telegram_id)
        
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "message": success_message
        }
    
    def _deduct_tokens_with_message(self, telegram_id: int, amount: float,
                                   transaction_type: str, description: str,
                                   error_message: str) -> Dict:
        """Списание токенов с возвратом сообщения"""
        success = self._deduct_tokens(telegram_id, amount, transaction_type, description)
        
        if not success:
            return {"error": error_message}
        
        new_balance = self.get_balance(telegram_id)
        
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "message": f"Списано {self._format_tokens(amount)} токенов"
        }
    
    # ========== УТИЛИТЫ ==========
    
    def _format_tokens(self, amount: float) -> str:
        """Форматирование количества токенов"""
        if isinstance(amount, (int, float)) and amount.is_integer():
            return f"{int(amount):,}₮".replace(",", " ")
        elif isinstance(amount, (int, float)):
            return f"{amount:,.2f}₮".replace(",", " ").replace(".", ",")
        else:
            return "0₮"
    
    def get_transaction_history(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получение истории транзакций токенов"""
        
        try:
            transactions = self.db.get_transaction_history(telegram_id, limit)
            
            formatted_transactions = []
            for tx in transactions:
                amount = float(tx['amount']) if tx['amount'] else 0.00
                is_positive = amount >= 0
                
                # Определяем иконку по типу транзакции
                icon = "🟢" if is_positive else "🔴"
                tx_type = tx['transaction_type'] or ""
                if "referral" in tx_type:
                    icon = "👥"
                elif "bonus" in tx_type:
                    icon = "🎁"
                elif "achievement" in tx_type:
                    icon = "🏆"
                elif "shop" in tx_type:
                    icon = "🛒"
                
                formatted_transactions.append({
                    "id": tx.get('transaction_id', 'unknown'),
                    "amount": amount,
                    "formatted_amount": f"{'+' if is_positive else ''}{self._format_tokens(amount)}",
                    "type": tx_type,
                    "description": tx.get('description', 'Без описания'),
                    "date": tx.get('created_at', ''),
                    "balance_before": float(tx['balance_before']) if tx['balance_before'] else 0.00,
                    "balance_after": float(tx['balance_after']) if tx['balance_after'] else 0.00,
                    "is_positive": is_positive,
                    "icon": icon
                })
            
            return formatted_transactions
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []

# Глобальный экземпляр системы токенов
token_system = TokenSystem()