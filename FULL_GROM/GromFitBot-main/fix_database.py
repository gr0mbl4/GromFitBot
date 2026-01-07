"""
Скрипт для исправления структуры базы данных
"""

import sqlite3
from pathlib import Path

def fix_database():
    """Исправление структуры базы данных"""
    print("🔧 Исправление структуры базы данных...")
    
    db_path = Path('data/users.db')
    
    if not db_path.exists():
        print("❌ База данных не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы achievements
        cursor.execute("PRAGMA table_info(achievements)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Колонки в таблице achievements: {column_names}")
        
        # Если нет колонки achievement_id, пересоздаем таблицу
        if 'achievement_id' not in column_names:
            print("❌ Отсутствует колонка achievement_id")
            print("🔄 Пересоздание таблицы achievements...")
            
            # Удаляем старую таблицу
            cursor.execute("DROP TABLE IF EXISTS achievements")
            
            # Создаем новую таблицу с правильной структурой
            cursor.execute("""
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
            """)
            
            print("✅ Таблица achievements пересоздана")
        
        # Создаем индекс для achievements
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user_id ON achievements(user_id)")
        
        conn.commit()
        conn.close()
        
        print("✅ Структура базы данных исправлена")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

if __name__ == "__main__":
    fix_database()