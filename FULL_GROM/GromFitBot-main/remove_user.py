"""
Скрипт удаления пользователей из базы данных GromFitBot
Для административных целей и тестирования
"""

import sys
import sqlite3
import argparse
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/user_management.log', encoding='utf-8'),
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

def connect_to_database():
    """Подключение к базе данных"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return None

def list_users(limit=20, search=None):
    """Вывод списка пользователей"""
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        if search:
            # Поиск пользователей
            cursor.execute(
                """
                SELECT * FROM users 
                WHERE nickname LIKE ? OR registration_number LIKE ? OR username LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (f"%{search}%", f"%{search}%", f"%{search}%", limit)
            )
        else:
            # Все пользователи
            cursor.execute(
                "SELECT * FROM users ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        
        users = cursor.fetchall()
        
        if not users:
            print("👥 Пользователи не найдены")
            return
        
        print(f"\n📋 Найдено пользователей: {len(users)}")
        print("=" * 80)
        print(f"{'ID':<4} {'Telegram ID':<12} {'Никнейм':<20} {'Рег. номер':<15} {'Дата регистрации':<20}")
        print("-" * 80)
        
        for user in users:
            user_id = user['id']
            telegram_id = user['telegram_id']
            nickname = user['nickname'][:18] + '..' if len(user['nickname']) > 18 else user['nickname']
            reg_number = user['registration_number']
            created_at = user['created_at'][:19] if user['created_at'] else 'Неизвестно'
            
            print(f"{user_id:<4} {telegram_id:<12} {nickname:<20} {reg_number:<15} {created_at:<20}")
        
        print("=" * 80)
        
        # Статистика
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        print(f"\n📊 Всего пользователей в базе: {total_users}")
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка получения списка пользователей: {e}")
    finally:
        conn.close()

def remove_user(user_identifier):
    """Удаление пользователя"""
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Определяем тип идентификатора
        if str(user_identifier).isdigit():
            # Это может быть ID пользователя или Telegram ID
            # Сначала проверяем по telegram_id
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (int(user_identifier),))
            user = cursor.fetchone()
            
            if not user:
                # Проверяем по ID
                cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_identifier),))
                user = cursor.fetchone()
        else:
            # Проверяем по регистрационному номеру
            cursor.execute("SELECT * FROM users WHERE registration_number = ?", (user_identifier,))
            user = cursor.fetchone()
        
        if not user:
            print(f"❌ Пользователь с идентификатором '{user_identifier}' не найден")
            conn.close()
            return
        
        # Показываем информацию о пользователе
        print("\n⚠️  Найден пользователь:")
        print(f"   ID: {user['id']}")
        print(f"   Telegram ID: {user['telegram_id']}")
        print(f"   Никнейм: {user['nickname']}")
        print(f"   Рег. номер: {user['registration_number']}")
        print(f"   Дата регистрации: {user['created_at']}")
        print(f"   Баланс: {user['balance_tokens']} токенов")
        print(f"   Рефералов: {user['referrals_count']}")
        
        # Подтверждение удаления
        print(f"\n❌ ВЫ УДАЛЯЕТЕ ПОЛЬЗОВАТЕЛЯ БЕЗ ВОЗМОЖНОСТИ ВОССТАНОВЛЕНИЯ!")
        print("Это действие удалит:")
        print("   • Все данные пользователя")
        print("   • Все его транзакции")
        print("   • Все его достижения")
        print("   • Все его покупки")
        print("   • Все связанные записи")
        
        confirmation = input("\nВведите 'DELETE' для подтверждения удаления: ").strip()
        
        if confirmation != 'DELETE':
            print("❌ Удаление отменено")
            conn.close()
            return
        
        # Получаем Telegram ID пользователя для удаления связанных данных
        telegram_id = user['telegram_id']
        
        # Начинаем транзакцию
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Удаляем связанные данные (в правильном порядке из-за foreign keys)
            
            # 1. Уведомления
            cursor.execute("DELETE FROM notifications WHERE user_id = ?", (telegram_id,))
            notifications_deleted = cursor.rowcount
            
            # 2. Достижения
            cursor.execute("DELETE FROM achievements WHERE user_id = ?", (telegram_id,))
            achievements_deleted = cursor.rowcount
            
            # 3. Покупки
            cursor.execute("DELETE FROM purchases WHERE user_id = ?", (telegram_id,))
            purchases_deleted = cursor.rowcount
            
            # 4. Тренировки
            cursor.execute("DELETE FROM trainings WHERE user_id = ?", (telegram_id,))
            trainings_deleted = cursor.rowcount
            
            # 5. Дуэли (где пользователь является участником)
            cursor.execute("DELETE FROM duels WHERE challenger_id = ? OR opponent_id = ?", 
                          (telegram_id, telegram_id))
            duels_deleted = cursor.rowcount
            
            # 6. Реферальные связи (где пользователь является реферером или рефералом)
            cursor.execute("DELETE FROM referral_connections WHERE referrer_id = ? OR referred_id = ?", 
                          (telegram_id, telegram_id))
            referrals_deleted = cursor.rowcount
            
            # 7. Транзакции
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (telegram_id,))
            transactions_deleted = cursor.rowcount
            
            # 8. Сам пользователь
            cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            user_deleted = cursor.rowcount
            
            # Фиксируем транзакцию
            conn.commit()
            
            print(f"\n✅ Пользователь успешно удален!")
            print(f"📊 Удалено записей:")
            print(f"   • Пользователь: {user_deleted}")
            print(f"   • Транзакции: {transactions_deleted}")
            print(f"   • Достижения: {achievements_deleted}")
            print(f"   • Покупки: {purchases_deleted}")
            print(f"   • Тренировки: {trainings_deleted}")
            print(f"   • Дуэли: {duels_deleted}")
            print(f"   • Реферальные связи: {referrals_deleted}")
            print(f"   • Уведомления: {notifications_deleted}")
            
            logger.info(f"Удален пользователь: {user['nickname']} (Telegram ID: {telegram_id})")
            
        except sqlite3.Error as e:
            conn.rollback()
            print(f"❌ Ошибка при удалении данных пользователя: {e}")
            logger.error(f"Ошибка удаления пользователя {telegram_id}: {e}")
            
    except sqlite3.Error as e:
        print(f"❌ Ошибка базы данных: {e}")
    finally:
        conn.close()

def backup_database():
    """Создание резервной копии базы данных"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.with_name(f"{db_path.stem}_backup_{timestamp}.db")
        
        shutil.copy2(db_path, backup_path)
        print(f"✅ Создана резервная копия: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания резервной копии: {e}")
        return False

def show_database_stats():
    """Показать статистику базы данных"""
    conn = connect_to_database()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        print("\n📊 Статистика базы данных")
        print("=" * 40)
        
        # Количество записей в таблицах
        tables = ['users', 'referral_connections', 'transactions', 'achievements', 
                 'shop_items', 'purchases', 'trainings', 'duels', 'notifications']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")
        
        print("-" * 40)
        
        # Размер базы данных
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_bytes = cursor.fetchone()[0]
        size_mb = size_bytes / (1024 * 1024)
        print(f"Размер базы данных: {size_mb:.2f} MB")
        
        # Последние регистрации
        cursor.execute("SELECT COUNT(*) as today_count FROM users WHERE date(created_at) = date('now')")
        today_registrations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as week_count FROM users WHERE date(created_at) >= date('now', '-7 days')")
        week_registrations = cursor.fetchone()[0]
        
        print(f"Регистраций сегодня: {today_registrations}")
        print(f"Регистраций за неделю: {week_registrations}")
        
        print("=" * 40)
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка получения статистики: {e}")
    finally:
        conn.close()

def interactive_mode():
    """Интерактивный режим работы"""
    print("\n" + "=" * 60)
    print("👥 Управление пользователями GromFitBot")
    print("=" * 60)
    
    while True:
        print("\n📋 Меню:")
        print("  1. Показать список пользователей")
        print("  2. Найти пользователя")
        print("  3. Удалить пользователя")
        print("  4. Создать резервную копию базы данных")
        print("  5. Показать статистику базы данных")
        print("  6. Выход")
        
        choice = input("\nВыберите действие (1-6): ").strip()
        
        if choice == '1':
            limit = input("Сколько пользователей показать? (по умолчанию 20): ").strip()
            if limit.isdigit():
                list_users(int(limit))
            else:
                list_users()
        
        elif choice == '2':
            search_term = input("Введите имя, ID или регистрационный номер для поиска: ").strip()
            if search_term:
                list_users(search=search_term)
            else:
                print("❌ Необходимо ввести поисковый запрос")
        
        elif choice == '3':
            user_id = input("Введите Telegram ID, ID пользователя или регистрационный номер: ").strip()
            if user_id:
                # Сначала создаем резервную копию
                print("\n📋 Создание резервной копии перед удалением...")
                if backup_database():
                    print("✅ Резервная копия создана")
                else:
                    print("⚠️  Не удалось создать резервную копию")
                    confirm = input("Продолжить без резервной копии? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("❌ Удаление отменено")
                        continue
                
                remove_user(user_id)
            else:
                print("❌ Необходимо ввести идентификатор пользователя")
        
        elif choice == '4':
            backup_database()
        
        elif choice == '5':
            show_database_stats()
        
        elif choice == '6':
            print("\n👋 Завершение работы")
            break
        
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Управление пользователями GromFitBot')
    parser.add_argument('action', nargs='?', choices=['list', 'remove', 'stats', 'backup', 'interactive'],
                       help='Действие: list - список пользователей, remove - удалить пользователя, '
                            'stats - статистика, backup - резервная копия, interactive - интерактивный режим')
    parser.add_argument('identifier', nargs='?', help='Идентификатор пользователя для удаления')
    parser.add_argument('--limit', type=int, default=20, help='Лимит пользователей для списка')
    parser.add_argument('--search', help='Поисковый запрос для поиска пользователей')
    
    args = parser.parse_args()
    
    # Если нет аргументов, запускаем интерактивный режим
    if not args.action:
        interactive_mode()
        return
    
    if args.action == 'list':
        list_users(args.limit, args.search)
    
    elif args.action == 'remove':
        if not args.identifier:
            print("❌ Необходимо указать идентификатор пользователя")
            print("Использование: python remove_user.py remove <telegram_id|id|reg_number>")
            return
        
        # Создаем резервную копию перед удалением
        if backup_database():
            print("✅ Резервная копия создана")
        else:
            print("⚠️  Не удалось создать резервную копию")
            confirm = input("Продолжить без резервной копии? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Удаление отменено")
                return
        
        remove_user(args.identifier)
    
    elif args.action == 'stats':
        show_database_stats()
    
    elif args.action == 'backup':
        backup_database()
    
    elif args.action == 'interactive':
        interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Завершение работы")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)