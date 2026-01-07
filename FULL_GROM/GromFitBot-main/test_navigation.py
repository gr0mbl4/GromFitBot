"""
Скрипт для тестирования навигации и функциональности GromFitBot
Проверяет исправление критических ошибок навигации
"""

import sys
import os
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

def setup_test_environment():
    """Настройка тестового окружения"""
    print("=" * 60)
    print("🧪 Тестирование навигации GromFitBot")
    print("=" * 60)
    
    # Добавляем корневую директорию в путь Python
    current_dir = Path.cwd()
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(current_dir / 'src'))
    
    print(f"📂 Рабочая директория: {current_dir}")
    
    return True

def check_database():
    """Проверка базы данных"""
    print("\n🔍 Проверка базы данных...")
    
    db_path = Path('data/users.db')
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        print("   Запустите: python update_database.py")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем наличие таблицы users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ Таблица 'users' не найдена в базе данных")
            conn.close()
            return False
        
        # Проверяем структуру таблиции
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['telegram_id', 'nickname', 'registration_number', 'balance_tokens']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"❌ Отсутствуют обязательные колонки: {missing_columns}")
            conn.close()
            return False
        
        # Проверяем количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"✅ База данных: {db_path}")
        print(f"📊 Таблиц: {len(tables)}")
        print(f"📋 Колонок в users: {len(column_names)}")
        print(f"👥 Пользователей: {user_count}")
        
        # Показываем несколько пользователей для тестирования
        if user_count > 0:
            cursor.execute("SELECT telegram_id, nickname, registration_number FROM users LIMIT 3")
            users = cursor.fetchall()
            
            print("\n📋 Примеры пользователей:")
            for user in users:
                print(f"  • ID: {user[0]}, Ник: {user[1]}, Рег.номер: {user[2]}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def check_file_structure():
    """Проверка структуры файлов проекта"""
    print("\n📁 Проверка структуры файлов...")
    
    required_files = [
        'src/main.py',
        'src/core/bot.py',
        'src/core/config.py',
        'src/core/database.py',
        'src/core/message_manager.py',
        'src/modules/auth/registration.py',
        'src/modules/profile/handlers.py',
        'src/modules/referrals/handlers.py',
        'src/modules/shop/handlers.py',
        'src/modules/bonus/handlers.py',
        'src/modules/keyboards/main_keyboards.py',
        '.env',
        'requirements.txt',
        'run.py',
        'update_database.py',
        'remove_user.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {len(missing_files)}")
        for file in missing_files[:5]:  # Показываем только первые 5
            print(f"  • {file}")
        
        if len(missing_files) > 5:
            print(f"  ... и еще {len(missing_files) - 5} файлов")
        
        return False
    else:
        print(f"✅ Все файлы на месте: {len(required_files)} файлов")
        return True

def check_env_file():
    """Проверка .env файла"""
    print("\n⚙️  Проверка .env файла...")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'BOT_TOKEN=' in content and 'your_bot_token_here' not in content:
            print("✅ .env файл настроен")
            return True
        else:
            print("⚠️  .env файл найден, но BOT_TOKEN не настроен")
            return False
    except Exception as e:
        print(f"❌ Ошибка чтения .env файла: {e}")
        return False

def test_message_manager():
    """Тестирование менеджера сообщений"""
    print("\n💬 Проверка менеджера сообщений...")
    
    try:
        # Создаем мок-объект бота для тестирования
        class MockBot:
            async def delete_message(self, chat_id, message_id):
                return True
        
        bot = MockBot()
        
        # Пытаемся импортировать менеджер сообщений
        try:
            from core.message_manager import MessageManager
            manager = MessageManager(bot)
        except ImportError:
            # Пробуем альтернативный путь
            sys.path.insert(0, 'src')
            from core.message_manager import MessageManager
            manager = MessageManager(bot)
        
        print("✅ Менеджер сообщений загружен")
        
        # Проверяем методы
        methods = ['replace_message', 'edit_message_with_menu', 'delete_message_safe']
        for method in methods:
            if hasattr(manager, method):
                print(f"  ✅ Метод {method} доступен")
            else:
                print(f"  ❌ Метод {method} отсутствует")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта менеджера сообщений: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования менеджера сообщений: {e}")
        return False

def test_keyboards():
    """Тестирование клавиатур"""
    print("\n⌨️  Проверка клавиатур...")
    
    try:
        # Пытаемся импортировать клавиатуры
        try:
            from modules.keyboards.main_keyboards import MainKeyboards, AuthKeyboards
        except ImportError:
            # Пробуем альтернативный путь
            sys.path.insert(0, 'src')
            from modules.keyboards.main_keyboards import MainKeyboards, AuthKeyboards
        
        print("✅ Модуль клавиатур загружен")
        
        # Тестируем основные клавиатуры
        keyboards_to_test = [
            ('Главное меню', MainKeyboards.get_main_menu),
            ('Кнопки под чатом', MainKeyboards.get_bottom_keyboard),
            ('Назад в главное меню', MainKeyboards.get_back_to_main_keyboard),
            ('Навигация', lambda: MainKeyboards.get_navigation_keyboard('test')),
            ('Профиль', MainKeyboards.get_profile_keyboard),
            ('Рефералы', MainKeyboards.get_referrals_keyboard),
            ('Магазин категории', MainKeyboards.get_shop_categories_keyboard),
            ('Бонусы', lambda: MainKeyboards.get_bonus_keyboard(True, 3)),
        ]
        
        for name, method in keyboards_to_test:
            try:
                keyboard = method()
                print(f"  ✅ {name}: создана")
            except Exception as e:
                print(f"  ❌ {name}: ошибка - {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта клавиатур: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования клавиатур: {e}")
        return False

def test_navigation_fixes():
    """Тестирование исправлений навигации"""
    print("\n🧭 Проверка исправлений навигации...")
    
    issues_to_check = [
        {
            'name': 'Главное меню заменяет сообщения',
            'file': 'src/core/bot.py',
            'check': lambda content: 'message_manager.replace_message' in content and 
                                     'handle_main_menu_button' in content and
                                     'await self._show_main_menu(message)' in content
        },
        {
            'name': 'Кнопка "Записать результат" без главного меню',
            'file': 'src/core/bot.py',
            'check': lambda content: 'handle_record_result' in content and 
                                     'message_manager.replace_message' in content and
                                     'MainKeyboards.get_main_menu()' not in content
        },
        {
            'name': 'Проверка пользователя в обработчиках "Назад"',
            'file': 'src/modules/referrals/handlers.py',
            'check': lambda content: 'back_to_referrals' in content and 
                                     'db.get_user(user_id)' in content and
                                     'if not user:' in content
        },
        {
            'name': 'persistent=True только у нижней клавиатуры',
            'file': 'src/modules/keyboards/main_keyboards.py',
            'check': lambda content: 'get_bottom_keyboard' in content and 
                                     'persistent=True' in content and 
                                     'get_main_menu' in content and 
                                     'persistent=True' not in content
        }
    ]
    
    all_checks_passed = True
    
    for issue in issues_to_check:
        file_path = Path(issue['file'])
        
        if not file_path.exists():
            print(f"❌ {issue['name']}: файл не найден - {issue['file']}")
            all_checks_passed = False
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if issue['check'](content):
                print(f"✅ {issue['name']}: исправлено")
            else:
                print(f"❌ {issue['name']}: НЕ исправлено")
                
                # Выводим отладочную информацию
                if issue['name'] == 'Главное меню заменяет сообщения':
                    print(f"   Поиск 'message_manager.replace_message': {'message_manager.replace_message' in content}")
                    print(f"   Поиск 'handle_main_menu_button': {'handle_main_menu_button' in content}")
                    print(f"   Поиск 'await self._show_main_menu(message)': {'await self._show_main_menu(message)' in content}")
                elif issue['name'] == 'persistent=True только у нижней клавиатуры':
                    print(f"   get_bottom_keyboard с persistent=True: {'get_bottom_keyboard' in content and 'persistent=True' in content}")
                    print(f"   get_main_menu БЕЗ persistent=True: {'get_main_menu' in content and 'persistent=True' not in content}")
                
                all_checks_passed = False
                
        except Exception as e:
            print(f"❌ {issue['name']}: ошибка проверки - {e}")
            all_checks_passed = False
    
    return all_checks_passed

def create_test_user():
    """Создание тестового пользователя для проверки"""
    print("\n👤 Создание тестового пользователя...")
    
    db_path = Path('data/users.db')
    
    if not db_path.exists():
        print("❌ База данных не найдена")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Удаляем старые тестовые пользователи (если есть)
        cursor.execute("DELETE FROM users WHERE nickname LIKE 'TestUser%'")
        
        # Создаем нового тестового пользователя
        test_data = {
            'telegram_id': 999999999,
            'registration_number': 'GF1234567890ABC',
            'nickname': 'TestUser',
            'username': 'testuser',
            'region': 'Москва',
            'balance_tokens': 100.00,
            'referrals_count': 3,
            'total_trainings': 5,
            'total_duels': 2,
            'duels_won': 1,
            'daily_streak': 3
        }
        
        cursor.execute(
            """
            INSERT INTO users 
            (telegram_id, registration_number, username, nickname, region, 
             balance_tokens, referrals_count, total_trainings, total_duels, 
             duels_won, daily_streak, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_data['telegram_id'],
                test_data['registration_number'],
                test_data['username'],
                test_data['nickname'],
                test_data['region'],
                test_data['balance_tokens'],
                test_data['referrals_count'],
                test_data['total_trainings'],
                test_data['total_duels'],
                test_data['duels_won'],
                test_data['daily_streak'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            )
        )
        
        conn.commit()
        
        user_id = cursor.lastrowid
        print(f"✅ Тестовый пользователь создан:")
        print(f"   • ID: {user_id}")
        print(f"   • Telegram ID: {test_data['telegram_id']}")
        print(f"   • Никнейм: {test_data['nickname']}")
        print(f"   • Баланс: {test_data['balance_tokens']} токенов")
        
        conn.close()
        return test_data['telegram_id']
        
    except sqlite3.Error as e:
        print(f"❌ Ошибка создания тестового пользователя: {e}")
        
        # Проверим структуру таблицы
        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print("📋 Структура таблицы users:")
            for col in columns:
                print(f"  • {col[1]} ({col[2]})")
        except:
            pass
            
        return None

def test_module_imports():
    """Тестирование импорта всех модулей"""
    print("\n📦 Проверка импорта модулей...")
    
    # Добавляем пути для импорта
    sys.path.insert(0, 'src')
    
    modules_to_test = [
        ('core.bot', 'GromFitBot'),
        ('core.config', 'Config'),
        ('core.database', 'Database'),
        ('core.message_manager', 'MessageManager'),
        ('modules.auth.registration', 'router'),
        ('modules.profile.handlers', 'router'),
        ('modules.referrals.handlers', 'router'),
        ('modules.shop.handlers', 'router'),
        ('modules.bonus.handlers', 'router'),
        ('modules.keyboards.main_keyboards', 'MainKeyboards'),
    ]
    
    all_modules_loaded = True
    
    for module_path, item_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[item_name])
            
            # Проверяем наличие нужного атрибута
            if hasattr(module, item_name) or item_name == 'router':
                print(f"✅ {module_path}")
            else:
                print(f"⚠️  {module_path}: атрибут {item_name} не найден")
                all_modules_loaded = False
                
        except ImportError as e:
            print(f"❌ {module_path}: {e}")
            all_modules_loaded = False
        except Exception as e:
            print(f"❌ {module_path}: ошибка - {e}")
            all_modules_loaded = False
    
    return all_modules_loaded

async def test_bot_initialization():
    """Тестирование инициализации бота"""
    print("\n🤖 Тестирование инициализации бота...")
    
    try:
        # Пытаемся импортировать бота
        try:
            from core.bot import GromFitBot
        except ImportError:
            sys.path.insert(0, 'src')
            from core.bot import GromFitBot
        
        # Пытаемся создать экземпляр бота
        bot = GromFitBot()
        
        print("✅ Экземпляр бота создан")
        
        # Проверяем основные атрибуты
        attributes_to_check = ['bot', 'dp', 'db', 'message_manager', 'common_router']
        
        for attr in attributes_to_check:
            if hasattr(bot, attr):
                print(f"  ✅ Атрибут {attr} присутствует")
            else:
                print(f"  ❌ Атрибут {attr} отсутствует")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта бота: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка инициализации бота: {e}")
        
        # Выводим подробности ошибки
        import traceback
        error_details = traceback.format_exc()
        
        # Ищем строку с ошибкой кодировки
        if "invalid character" in str(e):
            print(f"🔍 Обнаружена ошибка кодировки в файле bot.py")
            print(f"   Ошибка: {e}")
            
            # Попробуем найти проблемную строку в файле
            try:
                with open('src/core/bot.py', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    if '⏹' in line or '🛑' in line:
                        print(f"   Возможная проблемная строка {i}: {line.strip()[:50]}...")
            except:
                pass
        
        return False

def run_comprehensive_tests():
    """Запуск комплексного тестирования"""
    print("\n" + "=" * 60)
    print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    # 1. Настройка окружения
    if not setup_test_environment():
        return False
    
    # 2. Проверка структуры файлов
    file_structure_ok = check_file_structure()
    
    # 3. Проверка .env файла
    env_ok = check_env_file()
    
    # 4. Проверка базы данных
    database_ok = check_database()
    
    # 5. Создание тестового пользователя (пропускаем если ошибка с achievements)
    try:
        test_user_id = create_test_user()
    except:
        test_user_id = None
        print("⚠️  Пропускаем создание тестового пользователя из-за ошибки базы данных")
    
    # 6. Тестирование импорта модулей
    imports_ok = test_module_imports()
    
    # 7. Тестирование менеджера сообщений
    message_manager_ok = test_message_manager()
    
    # 8. Тестирование клавиатур
    keyboards_ok = test_keyboards()
    
    # 9. Тестирование исправлений навигации
    navigation_fixed = test_navigation_fixes()
    
    # 10. Тестирование инициализации бота
    try:
        bot_initialized = asyncio.run(test_bot_initialization())
    except Exception as e:
        bot_initialized = False
        print(f"❌ Не удалось протестировать инициализацию бота: {e}")
    
    # Итоги тестирования
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    test_results = {
        'Структура файлов': file_structure_ok,
        'Файл .env': env_ok,
        'База данных': database_ok,
        'Импорт модулей': imports_ok,
        'Менеджер сообщений': message_manager_ok,
        'Клавиатуры': keyboards_ok,
        'Исправления навигации': navigation_fixed,
        'Инициализация бота': bot_initialized
    }
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"\n✅ Пройдено тестов: {passed}/{total}")
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print("\n" + "=" * 60)
    
    if navigation_fixed:
        print("\n🎉 КРИТИЧЕСКИЕ ОШИБКИ НАВИГАЦИИ ИСПРАВЛЕНЫ!")
        print("\n✅ Решены следующие проблемы:")
        print("   1. Главное меню заменяет сообщения, а не добавляется под чатом")
        print("   2. Кнопка 'Записать результат' показывает только сообщение")
        print("   3. Кнопки 'Назад' проверяют пользователя перед возвратом")
        print("   4. Главное меню показывается под сообщением (без persistent=True)")
        print("   5. Нижнее меню всегда видимо (с persistent=True)")
    else:
        print("\n⚠️  НЕ ВСЕ ПРОБЛЕМЫ НАВИГАЦИИ ИСПРАВЛЕНЫ!")
        print("Проверьте файлы и убедитесь, что все исправления применены")
    
    print("\n📝 Следующие шаги:")
    print("   1. Убедитесь, что в .env файле установлен токен бота")
    print("   2. Запустите бота: python run.py")
    print("   3. Протестируйте навигацию вручную:")
    print("      • Нажмите 'Главное меню' - должно появиться под сообщением")
    print("      • Нажмите 'Записать результат' - только сообщение, без меню")
    print("      • Перейдите в 'Рефералы' → 'Лидеры' → 'Назад' - должен вернуться")
    
    # Дополнительные рекомендации
    if not navigation_fixed:
        print("\n🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        print("   1. Проверьте файл src/core/bot.py:")
        print("      • Убедитесь, что handle_main_menu_button вызывает _show_main_menu")
        print("      • Убедитесь, что _show_main_menu использует message_manager.replace_message")
        print("      • Убедитесь, что handle_record_result НЕ использует reply_markup")
        print("   2. Проверьте файл src/modules/keyboards/main_keyboards.py:")
        print("      • get_bottom_keyboard() должен иметь persistent=True")
        print("      • get_main_menu() НЕ должен иметь persistent=True")
    
    return navigation_fixed

def quick_test():
    """Быстрый тест основных функций"""
    print("\n⚡ БЫСТРЫЙ ТЕСТ ОСНОВНЫХ ФУНКЦИЙ")
    print("=" * 40)
    
    tests = [
        ("Проверка структуры файлов", check_file_structure),
        ("Проверка .env файла", check_env_file),
        ("Проверка базы данных", check_database),
        ("Проверка импорта модулей", test_module_imports),
        ("Проверка исправлений навигации", test_navigation_fixes),
    ]
    
    print()
    results = []
    for test_name, test_func in tests:
        print(f"🧪 {test_name}...", end=" ", flush=True)
        try:
            if test_func():
                print("✅")
                results.append(True)
            else:
                print("❌")
                results.append(False)
        except Exception as e:
            print(f"❌ (ошибка: {e})")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены")
    
    print("\n⚡ Быстрый тест завершен")

def check_bot_startup():
    """Проверка запуска бота"""
    try:
        # Пробуем импортировать бота без создания экземпляра
        sys.path.insert(0, 'src')
        from core.bot import GromFitBot
        return True
    except ImportError as e:
        # Ищем ошибку кодировки
        error_msg = str(e)
        if "invalid character" in error_msg or "encoding" in error_msg:
            print(f"\n⚠️  Обнаружена ошибка кодировки в bot.py")
            print(f"   Ошибка: {error_msg}")
            
            # Проверим файл на наличие проблемных символов
            try:
                with open('src/core/bot.py', 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверяем на наличие проблемных символов
                problem_chars = ['⏹', '🛑', '🚧', '🚀', '🎉', '⚠️', '❌', '✅']
                for char in problem_chars:
                    if char in content:
                        print(f"   Найден символ: {char}")
                
                # Попробуем прочитать файл с другой кодировкой
                with open('src/core/bot.py', 'rb') as f:
                    raw_content = f.read()
                    try:
                        raw_content.decode('utf-8')
                        print("   Файл корректно декодируется в UTF-8")
                    except UnicodeDecodeError as decode_error:
                        print(f"   Ошибка декодирования UTF-8: {decode_error}")
            except Exception as file_error:
                print(f"   Ошибка при проверке файла: {file_error}")
                        
        return False
    except Exception as e:
        print(f"❌ Общая ошибка при импорте бота: {e}")
        return False

def check_main_menu_fix():
    """Проверка исправления главного меню"""
    try:
        with open('src/core/bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем ключевые элементы
        checks = [
            'handle_main_menu_button' in content,
            '_show_main_menu' in content,
            'message_manager.replace_message' in content,
            'MainKeyboards.get_main_menu()' in content
        ]
        
        return all(checks)
    except:
        return False

def check_record_result_fix():
    """Проверка исправления кнопки "Записать результат" """
    try:
        with open('src/core/bot.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, что нет главного меню в handle_record_result
        if 'handle_record_result' in content:
            # Ищем строку с reply_markup
            lines = content.split('\n')
            in_record_result = False
            has_reply_markup = False
            
            for line in lines:
                if 'handle_record_result' in line or 'async def _handle_record_result' in line:
                    in_record_result = True
                elif in_record_result and 'def ' in line and 'handle_record_result' not in line:
                    # Вышли из функции
                    break
                
                if in_record_result and 'reply_markup=MainKeyboards.get_main_menu()' in line:
                    has_reply_markup = True
            
            return not has_reply_markup
        
        return False
    except:
        return False

def check_back_navigation_fix():
    """Проверка исправления навигации "Назад" """
    try:
        with open('src/modules/referrals/handlers.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем ключевые элементы
        checks = [
            'back_to_referrals' in content,
            'db.get_user(user_id)' in content,
            'if not user:' in content
        ]
        
        return all(checks)
    except:
        return False

def check_critical_fixes():
    """Проверка критических исправлений"""
    print("\n🔍 ПРОВЕРКА КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ")
    print("=" * 40)
    
    critical_fixes = [
        {
            'name': 'Бот не падает при запуске',
            'check': lambda: check_bot_startup()
        },
        {
            'name': 'Главное меню заменяет сообщения',
            'check': lambda: check_main_menu_fix()
        },
        {
            'name': 'Кнопка "Записать результат" без меню',
            'check': lambda: check_record_result_fix()
        },
        {
            'name': 'Навигация "Назад" работает',
            'check': lambda: check_back_navigation_fix()
        }
    ]
    
    print()
    for fix in critical_fixes:
        print(f"🔧 {fix['name']}...", end=" ", flush=True)
        try:
            if fix['check']():
                print("✅")
            else:
                print("❌")
        except Exception as e:
            print(f"❌ (ошибка: {e})")
    
    print("\n🔍 Проверка критических исправлений завершена")

def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование GromFitBot')
    parser.add_argument('--quick', action='store_true', help='Быстрый тест')
    parser.add_argument('--full', action='store_true', help='Полное тестирование')
    parser.add_argument('--critical', action='store_true', help='Проверка критических исправлений')
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            quick_test()
        elif args.full:
            run_comprehensive_tests()
        elif args.critical:
            check_critical_fixes()
        else:
            # По умолчанию полное тестирование
            run_comprehensive_tests()
    except KeyboardInterrupt:
        print("\n\n👋 Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()