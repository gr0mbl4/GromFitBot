#!/usr/bin/env python3
"""
Скрипт для удаления пользователя из базы данных
"""

import sqlite3
import sys
from pathlib import Path

def remove_user_from_db(telegram_id: int):
    """Удаление пользователя из базы данных"""
    
    db_path = Path("data/users.db")
    
    if not db_path.exists():
        print("❌ База данных не найдена")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id, nickname FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
            return False
        
        print(f"🔍 Найден пользователь: ID={user[0]}, Никнейм={user[1]}")
        
        # Удаляем пользователя и все связанные данные
        cursor.execute("DELETE FROM referral_connections WHERE referrer_id = ? OR referred_id = ?", (telegram_id, telegram_id))
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (telegram_id,))
        cursor.execute("DELETE FROM achievements WHERE user_id = ?", (telegram_id,))
        cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        
        conn.commit()
        
        print(f"✅ Пользователь с telegram_id={telegram_id} удален из базы данных")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователя: {e}")
        return False
    finally:
        conn.close()

def list_all_users():
    """Показать всех пользователей"""
    
    db_path = Path("data/users.db")
    
    if not db_path.exists():
        print("❌ База данных не найдена")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT telegram_id, nickname, registration_number, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        print(f"👥 Всего пользователей: {len(users)}")
        print("-" * 50)
        
        for i, user in enumerate(users, 1):
            print(f"{i}. ID: {user[0]}, Ник: {user[1]}, Рег.номер: {user[2]}, Регистрация: {user[3]}")
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка пользователей: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🛠️  Утилита управления пользователями GromFitBot")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_all_users()
        elif sys.argv[1] == "remove":
            if len(sys.argv) > 2:
                try:
                    telegram_id = int(sys.argv[2])
                    remove_user_from_db(telegram_id)
                except ValueError:
                    print("❌ Неверный формат ID. Используйте число.")
            else:
                print("❌ Укажите telegram_id для удаления: python remove_user.py remove <telegram_id>")
        else:
            print("❌ Неизвестная команда")
    else:
        print("📋 Доступные команды:")
        print("  python remove_user.py list - показать всех пользователей")
        print("  python remove_user.py remove <telegram_id> - удалить пользователя")
        print("\n💡 Чтобы узнать свой telegram_id, отправьте боту @userinfobot в Telegram")