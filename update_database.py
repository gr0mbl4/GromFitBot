#!/usr/bin/env python3
"""
Скрипт для обновления базы данных GromFitBot
Добавляет недостающие колонки для системы бонусов
"""

import sqlite3
import os
from pathlib import Path

def update_database():
    """Добавляет недостающие колонки в базу данных"""
    
    # Путь к базе данных
    db_path = Path("data/users.db")
    
    if not db_path.exists():
        print("❌ База данных не найдена.")
        print("📁 Создаю новую базу данных...")
        
        # Создаем директорию, если её нет
        db_path.parent.mkdir(exist_ok=True)
        
        # Создаем новую базу данных
        create_new_database()
        return True
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Обновление базы данных...")
    
    # Проверяем существующие колонки
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"📊 Существующие колонки: {', '.join(columns)}")
    
    # Колонки для добавления
    columns_to_add = [
        ("daily_streak", "INTEGER DEFAULT 0"),
        ("last_streak_date", "DATE"),
        ("last_bonus_claim", "TIMESTAMP"),
        ("last_active", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("balance_diamonds", "DECIMAL(15,2) DEFAULT 0.00"),
        ("achievements_count", "INTEGER DEFAULT 0"),
        ("total_trainings", "INTEGER DEFAULT 0"),
        ("total_duels", "INTEGER DEFAULT 0"),
        ("duels_won", "INTEGER DEFAULT 0"),
        ("total_points", "INTEGER DEFAULT 0"),
        ("level", "INTEGER DEFAULT 1"),
        ("experience", "INTEGER DEFAULT 0"),
        ("last_training_date", "TIMESTAMP"),
        ("is_premium", "BOOLEAN DEFAULT 0"),
        ("premium_until", "TIMESTAMP"),
        ("notifications_enabled", "BOOLEAN DEFAULT 1"),
        ("language", "TEXT DEFAULT 'ru'"),
        ("theme", "TEXT DEFAULT 'light'")
    ]
    
    added_count = 0
    
    for column_name, column_type in columns_to_add:
        if column_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                print(f"✅ Добавлена колонка: {column_name} ({column_type})")
                added_count += 1
            except Exception as e:
                print(f"⚠️ Ошибка при добавлении колонки {column_name}: {e}")
        else:
            print(f"✓ Колонка {column_name} уже существует")
    
    # Обновляем таблицу transactions, если нужно
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("✅ Таблица transactions проверена/создана")
    except Exception as e:
        print(f"⚠️ Ошибка с таблицей transactions: {e}")
    
    # Таблица достижений
    try:
        cursor.execute("""
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
        """)
        print("✅ Таблица achievements проверена/создана")
    except Exception as e:
        print(f"⚠️ Ошибка с таблицей achievements: {e}")
    
    # Таблица реферальных связей
    try:
        cursor.execute("""
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
        """)
        print("✅ Таблица referral_connections проверена/создана")
    except Exception as e:
        print(f"⚠️ Ошибка с таблицей referral_connections: {e}")
    
    # Таблица товаров магазина
    try:
        cursor.execute("""
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
        """)
        print("✅ Таблица shop_items проверена/создана")
    except Exception as e:
        print(f"⚠️ Ошибка с таблицей shop_items: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Обновление завершено. Добавлено колонок: {added_count}")
    return True

def create_new_database():
    """Создает новую базу данных с полной структурой"""
    
    db_path = Path("data/users.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("📁 Создание новой базы данных...")
    
    # Основная таблица пользователей
    cursor.execute("""
        CREATE TABLE users (
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
    """)
    
    # Индексы для оптимизации
    cursor.execute("CREATE INDEX idx_telegram_id ON users(telegram_id)")
    cursor.execute("CREATE INDEX idx_registration_number ON users(registration_number)")
    cursor.execute("CREATE INDEX idx_referrer_id ON users(referrer_id)")
    
    print("✅ Таблица users создана")
    
    # Таблица транзакций
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount DECIMAL(15,2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    print("✅ Таблица transactions создана")
    
    # Таблица достижений
    cursor.execute("""
        CREATE TABLE achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            achievement_name TEXT NOT NULL,
            achievement_description TEXT,
            achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, achievement_id)
        )
    """)
    print("✅ Таблица achievements создана")
    
    # Таблица реферальных связей
    cursor.execute("""
        CREATE TABLE referral_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            connection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bonus_paid BOOLEAN DEFAULT 0,
            FOREIGN KEY (referrer_id) REFERENCES users(id),
            FOREIGN KEY (referred_id) REFERENCES users(id),
            UNIQUE(referred_id)
        )
    """)
    print("✅ Таблица referral_connections создана")
    
    # Таблица товаров магазина
    cursor.execute("""
        CREATE TABLE shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_description TEXT,
            item_type TEXT NOT NULL,
            price_tokens DECIMAL(15,2) NOT NULL,
            price_diamonds DECIMAL(15,2),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ Таблица shop_items создана")
    
    # Вставляем тестовые товары в магазин
    shop_items = [
        ("Буст опыта x2 (1 час)", "Увеличивает получаемый опыт в 2 раза на 1 час", "boost", 50.00, 0.00),
        ("Буст токенов x2 (1 час)", "Увеличивает получаемые токены в 2 раза на 1 час", "boost", 75.00, 0.00),
        ("Аватар премиум", "Эксклюзивный аватар для профиля", "avatar", 100.00, 10.00),
        ("Тема темная", "Темная тема для интерфейса", "theme", 150.00, 15.00),
        ("Премиум на 7 дней", "Премиум статус на 7 дней", "premium", 300.00, 30.00),
    ]
    
    for item in shop_items:
        cursor.execute(
            "INSERT INTO shop_items (item_name, item_description, item_type, price_tokens, price_diamonds) VALUES (?, ?, ?, ?, ?)",
            item
        )
    
    print("✅ Тестовые товары добавлены в магазин")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 Новая база данных успешно создана!")
    return True

if __name__ == "__main__":
    update_database()