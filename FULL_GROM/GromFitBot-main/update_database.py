"""
Скрипт обновления базы данных GromFitBot
Создает/обновляет структуру базы данных
"""

import sys
import os
import sqlite3
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/database_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_database_path():
    """Получение пути к базе данных"""
    # Проверяем .env файл
    env_path = Path('.env')
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('DB_PATH='):
                        db_path = line.strip().split('=', 1)[1].strip()
                        if db_path:
                            return Path(db_path)
        except Exception as e:
            logger.warning(f"Не удалось прочитать DB_PATH из .env: {e}")
    
    # Путь по умолчанию
    return Path('data/users.db')

def create_tables(conn):
    """Создание всех таблиц базы данных"""
    cursor = conn.cursor()
    
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
    
    for i, table_sql in enumerate(tables, 1):
        try:
            cursor.execute(table_sql)
            logger.info(f"Таблица {i} создана/проверена")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблицы {i}: {e}")
    
    conn.commit()
    
    return len(tables)

def create_indexes(conn):
    """Создание индексов для оптимизации запросов"""
    cursor = conn.cursor()
    
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
    
    for i, index_sql in enumerate(indexes, 1):
        try:
            cursor.execute(index_sql)
            logger.info(f"Индекс {i} создан/проверен")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания индекса {i}: {e}")
    
    conn.commit()
    
    return len(indexes)

def add_sample_data(conn):
    """Добавление тестовых данных (опционально)"""
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже тестовые данные
    cursor.execute("SELECT COUNT(*) FROM shop_items")
    shop_items_count = cursor.fetchone()[0]
    
    if shop_items_count > 0:
        logger.info("Тестовые данные уже существуют, пропускаем добавление")
        return 0
    
    # Добавляем тестовые товары в магазин
    sample_items = [
        ("premium_week", "💎 Премиум на неделю", "Премиум статус на 7 дней", 100.00, 0.00, "premium", "💎"),
        ("premium_month", "💎 Премиум на месяц", "Премиум статус на 30 дней", 350.00, 0.00, "premium", "💎"),
        ("theme_dark", "🌙 Темная тема", "Темная тема оформления", 50.00, 0.00, "design", "🎨"),
        ("theme_light", "🌞 Светлая тема", "Светлая тема оформления", 50.00, 0.00, "design", "🎨"),
        ("booster_2x", "⚡️ Бустер x2 на день", "Удвоение наград за тренировки на 24 часа", 75.00, 0.00, "boosters", "⚡️"),
        ("booster_3x", "⚡️ Бустер x3 на день", "Утроение наград за тренировки на 24 часа", 150.00, 0.00, "boosters", "⚡️"),
        ("gift_small", "🎁 Маленький подарок", "Подарок для друга (10 токенов)", 15.00, 0.00, "gifts", "🎁"),
        ("gift_medium", "🎁 Средний подарок", "Подарок для друга (25 токенов)", 30.00, 0.00, "gifts", "🎁"),
        ("gift_large", "🎁 Большой подарок", "Подарок для друга (50 токенов)", 50.00, 0.00, "gifts", "🎁"),
        ("tool_calculator", "🧮 Калькулятор калорий", "Инструмент для расчета калорий", 25.00, 0.00, "tools", "🛠️"),
        ("tool_planner", "📅 Планировщик тренировок", "Планировщик тренировок на неделю", 40.00, 0.00, "tools", "🛠️"),
        ("emotion_fire", "🔥 Огонь", "Стикер 'Огонь' для профиля", 10.00, 0.00, "emotions", "🎭"),
        ("emotion_medal", "🏅 Медаль", "Стикер 'Медаль' для профиля", 10.00, 0.00, "emotions", "🎭"),
        ("emotion_trophy", "🏆 Кубок", "Стикер 'Кубок' для профиля", 10.00, 0.00, "emotions", "🎭"),
        ("emotion_star", "⭐️ Звезда", "Стикер 'Звезда' для профиля", 10.00, 0.00, "emotions", "🎭")
    ]
    
    inserted_count = 0
    
    for item in sample_items:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO shop_items 
                (item_id, name, description, price_tokens, price_diamonds, category, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                item
            )
            inserted_count += 1
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления товара {item[0]}: {e}")
    
    conn.commit()
    
    if inserted_count > 0:
        logger.info(f"Добавлено {inserted_count} тестовых товаров")
    
    return inserted_count

def backup_database(db_path):
    """Создание резервной копии базы данных"""
    try:
        backup_path = db_path.with_suffix('.backup.db')
        
        import shutil
        if db_path.exists():
            shutil.copy2(db_path, backup_path)
            logger.info(f"Создана резервная копия: {backup_path}")
            return True
        else:
            logger.warning("База данных не существует, резервная копия не создана")
            return False
    except Exception as e:
        logger.error(f"Ошибка создания резервной копии: {e}")
        return False

def check_database_integrity(conn):
    """Проверка целостности базы данных"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result == "ok":
            logger.info("✅ Целостность базы данных: OK")
            return True
        else:
            logger.error(f"❌ Проблемы с целостностью базы данных: {result}")
            return False
    except sqlite3.Error as e:
        logger.error(f"❌ Ошибка проверки целостности: {e}")
        return False

def get_database_stats(conn):
    """Получение статистики базы данных"""
    cursor = conn.cursor()
    
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {}

def main():
    """Основная функция"""
    print("=" * 60)
    print("🔄 Обновление базы данных GromFitBot")
    print("=" * 60)
    
    # Получаем путь к базе данных
    db_path = get_database_path()
    
    print(f"\n📂 Путь к базе данных: {db_path}")
    
    # Создаем директорию если ее нет
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Создаем резервную копию если база существует
    if db_path.exists():
        print("\n📋 Создание резервной копии...")
        if backup_database(db_path):
            print("✅ Резервная копия создана")
        else:
            print("⚠️  Не удалось создать резервную копию")
            print("Продолжить без резервной копии? (y/n): ", end="")
            answer = input().strip().lower()
            if answer != 'y':
                print("❌ Отмена обновления")
                return
    else:
        print("\n📋 Новая база данных будет создана")
    
    # Подключаемся к базе данных
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        print("\n🔧 Создание таблиц...")
        tables_created = create_tables(conn)
        print(f"✅ Создано/проверено таблиц: {tables_created}")
        
        print("\n🔍 Создание индексов...")
        indexes_created = create_indexes(conn)
        print(f"✅ Создано/проверено индексов: {indexes_created}")
        
        print("\n🔍 Проверка целостности...")
        if check_database_integrity(conn):
            print("✅ Целостность базы данных проверена")
        else:
            print("⚠️  Обнаружены проблемы с целостностью")
        
        print("\n📊 Добавление тестовых данных...")
        sample_data_added = add_sample_data(conn)
        if sample_data_added > 0:
            print(f"✅ Добавлено тестовых товаров: {sample_data_added}")
        else:
            print("✅ Тестовые данные уже существуют или не добавлены")
        
        print("\n📈 Получение статистики...")
        stats = get_database_stats(conn)
        if stats:
            print(f"📊 Размер базы данных: {stats.get('database_size', 0):,} байт")
            print(f"👥 Пользователей: {stats.get('users_count', 0)}")
            print(f"🛒 Товаров в магазине: {stats.get('shop_items_count', 0)}")
            print(f"📋 Транзакций: {stats.get('transactions_count', 0)}")
            
            if stats.get('last_user_registration'):
                print(f"📅 Последняя регистрация: {stats['last_user_registration']}")
        else:
            print("⚠️  Не удалось получить статистику")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Обновление базы данных завершено успешно!")
        print("=" * 60)
        
        print("\n📝 Следующие шаги:")
        print("1. Убедитесь, что файл .env настроен с токеном бота")
        print("2. Запустите бота: python run.py")
        print("3. Или запустите напрямую: python src/main.py")
        
    except sqlite3.Error as e:
        print(f"\n❌ Ошибка базы данных: {e}")
        logger.error(f"Ошибка базы данных: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        logger.error(f"Неожиданная ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Обновление отменено пользователем")
        sys.exit(1)