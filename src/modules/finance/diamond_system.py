"""
Система алмазов как внешней валюты (1 алмаз = 1 звезда Telegram)
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from src.core.database import db

logger = logging.getLogger(__name__)

class DiamondSystem:
    """Система управления алмазами"""
    
    def __init__(self):
        self.db = db
        self.MIN_WITHDRAWAL = 100  # Минимальный вывод: 100 алмазов
        self.WITHDRAWAL_FEE = 0.10  # Комиссия на вывод 10%
    
    # ========== ОСНОВНЫЕ ОПЕРАЦИИ ==========
    
    def get_balance(self, telegram_id: int) -> Dict:
        """Получение полной информации о балансе алмазов"""
        user = db.get_user(telegram_id)
        
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Безопасное получение значений
        balance = float(user['balance_diamonds']) if 'balance_diamonds' in user.keys() else 0.00
        total_earned = float(user['total_earned_diamonds']) if 'total_earned_diamonds' in user.keys() else 0.00
        total_spent = float(user['total_spent_diamonds']) if 'total_spent_diamonds' in user.keys() else 0.00
        
        return {
            "balance": balance,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "available": balance,
            "formatted_balance": self._format_diamonds(balance),
            "formatted_earned": self._format_diamonds(total_earned),
            "formatted_spent": self._format_diamonds(total_spent)
        }
    
    def deposit(self, telegram_id: int, amount: float, 
                source: str = "stars", description: str = "") -> Dict:
        """Пополнение алмазов (покупка за звезды)"""
        
        if amount <= 0:
            return {"error": "Сумма должна быть положительной"}
        
        success = self._add_diamonds(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type=f"deposit_{source}",
            description=description or f"Покупка алмазов за {source}"
        )
        
        if not success:
            return {"error": "Ошибка при пополнении алмазов"}
        
        # Получаем обновленный баланс
        new_balance = self.get_balance(telegram_id)
        
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "transaction_id": f"diamond_deposit_{int(datetime.now().timestamp())}",
            "message": f"✅ Баланс алмазов пополнен на {self._format_diamonds(amount)}"
        }
    
    def withdraw(self, telegram_id: int, amount: float, 
                 method: str = "stars", description: str = "") -> Dict:
        """Вывод алмазов в звезды"""
        
        if amount <= 0:
            return {"error": "Сумма должна быть положительной"}
        
        # Проверяем минимальную сумму вывода (100 алмазов)
        if amount < self.MIN_WITHDRAWAL:
            return {"error": f"Минимальная сумма вывода: {self.MIN_WITHDRAWAL} алмазов"}
        
        # Проверяем баланс
        balance_info = self.get_balance(telegram_id)
        if "error" in balance_info:
            return balance_info
        
        if balance_info["balance"] < amount:
            return {"error": f"Недостаточно алмазов. Доступно: {balance_info['formatted_balance']}"}
        
        success = self._deduct_diamonds(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type=f"withdrawal_{method}",
            description=description or f"Вывод алмазов в {method}"
        )
        
        if not success:
            return {"error": "Ошибка при выводе алмазов"}
        
        # Получаем обновленный баланс
        new_balance = self.get_balance(telegram_id)
        
        # Комиссия 10%
        fee = amount * self.WITHDRAWAL_FEE
        net_amount = amount - fee
        
        return {
            "success": True,
            "amount": amount,
            "net_amount": net_amount,
            "fee": fee,
            "method": method,
            "new_balance": new_balance,
            "transaction_id": f"diamond_withdraw_{int(datetime.now().timestamp())}",
            "message": f"✅ Заявка на вывод {self._format_diamonds(amount)} алмазов принята\n"
                      f"💸 Комиссия (10%): {self._format_diamonds(fee)}\n"
                      f"💰 К зачислению: {net_amount} звезд"
        }
    
    def award_duel_win(self, telegram_id: int, amount: float, duel_id: str = "") -> Dict:
        """Награда за победу в дуэли"""
        return self._add_diamonds_with_message(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type="duel_win",
            description=f"Победа в дуэли {duel_id}" if duel_id else "Победа в дуэли",
            success_message=f"🏆 Получено {self._format_diamonds(amount)} алмазов за победу в дуэли!"
        )
    
    def deduct_duel_entry(self, telegram_id: int, amount: float, duel_id: str = "") -> Dict:
        """Списание за вход в дуэль"""
        return self._deduct_diamonds_with_message(
            telegram_id=telegram_id,
            amount=amount,
            transaction_type="duel_entry",
            description=f"Вход в дуэль {duel_id}" if duel_id else "Вход в дуэль",
            error_message="Недостаточно алмазов для участия в дуэли"
        )
    
    def _add_diamonds(self, telegram_id: int, amount: float, 
                     transaction_type: str, description: str = "") -> bool:
        """Внутренний метод добавления алмазов"""
        try:
            # Получаем текущий баланс
            cursor = self.db.execute(
                "SELECT balance_diamonds, total_earned_diamonds FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_diamonds']) if user['balance_diamonds'] is not None else 0.00
            balance_after = balance_before + amount
            
            # Обновляем баланс
            self.db.execute('''
                UPDATE users 
                SET balance_diamonds = ?, 
                    total_earned_diamonds = total_earned_diamonds + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, telegram_id))
            
            # Генерируем ID транзакции
            transaction_id = f"dm_{int(datetime.now().timestamp())}_{telegram_id}"
            
            # Записываем транзакцию
            self.db.execute('''
                INSERT INTO diamond_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding diamonds: {e}")
            return False
    
    def _deduct_diamonds(self, telegram_id: int, amount: float, 
                        transaction_type: str, description: str = "") -> bool:
        """Внутренний метод списания алмазов"""
        try:
            # Получаем текущий баланс
            cursor = self.db.execute(
                "SELECT balance_diamonds, total_spent_diamonds FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False
            
            balance_before = float(user['balance_diamonds']) if user['balance_diamonds'] is not None else 0.00
            
            # Проверяем, достаточно ли средств
            if balance_before < amount:
                return False
            
            balance_after = balance_before - amount
            
            # Обновляем баланс
            self.db.execute('''
                UPDATE users 
                SET balance_diamonds = ?, 
                    total_spent_diamonds = total_spent_diamonds + ?
                WHERE telegram_id = ?
            ''', (balance_after, amount, telegram_id))
            
            # Генерируем ID транзакции
            transaction_id = f"dm_{int(datetime.now().timestamp())}_{telegram_id}"
            
            # Записываем транзакцию
            self.db.execute('''
                INSERT INTO diamond_transactions 
                (transaction_id, user_id, amount, transaction_type, 
                 balance_before, balance_after, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, telegram_id, amount, transaction_type,
                  balance_before, balance_after, description))
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deducting diamonds: {e}")
            return False
    
    def _add_diamonds_with_message(self, telegram_id: int, amount: float,
                                  transaction_type: str, description: str,
                                  success_message: str) -> Dict:
        """Добавление алмазов с возвратом сообщения"""
        success = self._add_diamonds(telegram_id, amount, transaction_type, description)
        
        if not success:
            return {"error": "Ошибка начисления алмазов"}
        
        new_balance = self.get_balance(telegram_id)
        
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "message": success_message
        }
    
    def _deduct_diamonds_with_message(self, telegram_id: int, amount: float,
                                     transaction_type: str, description: str,
                                     error_message: str) -> Dict:
        """Списание алмазов с возвратом сообщения"""
        success = self._deduct_diamonds(telegram_id, amount, transaction_type, description)
        
        if not success:
            return {"error": error_message}
        
        new_balance = self.get_balance(telegram_id)
        
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "message": f"Списано {self._format_diamonds(amount)} алмазов"
        }
    
    # ========== УТИЛИТЫ ==========
    
    def _format_diamonds(self, amount: float) -> str:
        """Форматирование количества алмазов"""
        if isinstance(amount, (int, float)) and amount.is_integer():
            return f"{int(amount):,}💎".replace(",", " ")
        elif isinstance(amount, (int, float)):
            return f"{amount:,.2f}💎".replace(",", " ").replace(".", ",")
        else:
            return "0💎"
    
    def get_transaction_history(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Получение истории транзакций алмазов"""
        
        try:
            cursor = self.db.execute('''
                SELECT transaction_id, amount, transaction_type, 
                       balance_before, balance_after, description, created_at
                FROM diamond_transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (telegram_id, limit))
            
            transactions = cursor.fetchall()
            
            formatted_transactions = []
            for tx in transactions:
                amount = float(tx['amount']) if tx['amount'] else 0.00
                is_positive = amount >= 0
                
                # Определяем иконку по типу транзакции
                icon = "💎" if is_positive else "🔴"
                tx_type = tx['transaction_type'] or ""
                if "duel_win" in tx_type:
                    icon = "🏆"
                elif "deposit" in tx_type:
                    icon = "💳"
                elif "withdrawal" in tx_type:
                    icon = "🏧"
                elif "purchase" in tx_type:
                    icon = "🛒"
                
                formatted_transactions.append({
                    "id": tx.get('transaction_id', 'unknown'),
                    "amount": amount,
                    "formatted_amount": f"{'+' if is_positive else ''}{self._format_diamonds(amount)}",
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
            logger.error(f"Error getting diamond transaction history: {e}")
            return []

# Глобальный экземпляр системы алмазов
diamond_system = DiamondSystem()