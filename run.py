"""
Скрипт запуска бота с правильной настройкой путей
Полная версия с проверками и отладкой
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def print_header():
    """Вывод заголовка"""
    print("=" * 60)
    print("GromFitBot - Система спортивных дуэлей на токенах")
    print(f"Версия: 4.1 | Дата: 2026-01-07")
    print("=" * 60)
    print()

def check_environment():
    """Проверка окружения"""
    print("🔍 Проверка окружения...")
    
    # Проверка Python версии
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print(f"❌ Требуется Python 3.9 или выше. У вас: {python_version.major}.{python_version.minor}")
        return False
    
    print(f"✅ Python версия: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Определяем ОС
    os_name = platform.system()
    print(f"✅ Операционная система: {os_name}")
    
    return True

def check_directories():
    """Проверка необходимых директорий"""
    print("\n📁 Проверка структуры директорий...")
    
    current_dir = Path.cwd()
    print(f"📂 Текущая директория: {current_dir}")
    
    required_dirs = [
        'src',
        'src/core',
        'src/modules',
        'src/modules/auth',
        'src/modules/profile',
        'src/modules/referrals',
        'src/modules/shop',
        'src/modules/bonus',
        'src/modules/keyboards',
        'data',
        'logs',
        'temp'
    ]
    
    all_dirs_exist = True
    
    for dir_path in required_dirs:
        dir_full_path = current_dir / dir_path
        if dir_full_path.exists():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - не найдена")
            all_dirs_exist = False
    
    if not all_dirs_exist:
        print("\n⚠️  Некоторые директории отсутствуют.")
        print("   Создать недостающие директории? (y/n): ", end="")
        answer = input().strip().lower()
        
        if answer == 'y':
            create_missing_directories()
    
    return all_dirs_exist

def create_missing_directories():
    """Создание недостающих директорий"""
    current_dir = Path.cwd()
    required_dirs = [
        'src/core',
        'src/modules/auth',
        'src/modules/profile',
        'src/modules/referrals',
        'src/modules/shop',
        'src/modules/bonus',
        'src/modules/keyboards',
        'data',
        'logs',
        'temp'
    ]
    
    for dir_path in required_dirs:
        dir_full_path = current_dir / dir_path
        if not dir_full_path.exists():
            try:
                dir_full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Создана: {dir_path}/")
            except Exception as e:
                print(f"  ❌ Ошибка создания {dir_path}/: {e}")

def check_files():
    """Проверка необходимых файлов"""
    print("\n📄 Проверка необходимых файлов...")
    
    current_dir = Path.cwd()
    
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
        'update_database.py',
        'remove_user.py'
    ]
    
    all_files_exist = True
    
    for file_path in required_files:
        file_full_path = current_dir / file_path
        if file_full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - не найден")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n⚠️  Некоторые файлы отсутствуют.")
        print("   Убедитесь, что вы скопировали все файлы из репозитория.")
    
    return all_files_exist

def check_env_file():
    """Проверка .env файла"""
    print("\n⚙️  Проверка файла .env...")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("\nСоздать пример .env файла? (y/n): ", end="")
        answer = input().strip().lower()
        
        if answer == 'y':
            create_example_env()
            print("✅ Создан файл .env.example")
            print("⚠️  Отредактируйте .env.example и переименуйте в .env")
            return False
        else:
            return False
    
    # Проверяем содержимое .env файла
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'BOT_TOKEN=' in content and 'your_bot_token_here' not in content:
            print("✅ Файл .env настроен")
            return True
        else:
            print("⚠️  Файл .env найден, но BOT_TOKEN не настроен")
            print("   Убедитесь, что вы заменили 'your_bot_token_here' на реальный токен бота")
            return False
    except Exception as e:
        print(f"❌ Ошибка чтения .env файла: {e}")
        return False

def create_example_env():
    """Создание примера .env файла"""
    env_example_content = """# Токен бота Telegram (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# Настройки базы данных
DB_PATH=data/users.db

# Настройки Redis (опционально)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Веб-настройки (для будущего веб-интерфейса)
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_SECRET=your_secret_key_here

# Настройки S3 для бэкапов (опционально)
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=
S3_REGION=

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
ERROR_LOG_FILE=logs/errors.log

# ID администраторов (через запятую)
ADMIN_IDS=123456789,987654321

# Режимы работы
DEBUG_MODE=False
MAINTENANCE_MODE=False

# Настройки бота
BOT_USERNAME=
BOT_NAME=GromFitBot
BOT_DESCRIPTION=Спортивные дуэли на токенах

# Экономические настройки
START_TOKENS=50.0
REFERRAL_BONUS=10.0
DAILY_BONUS_BASE=5.0
DAILY_STREAK_MULTIPLIER=1.2

# Настройки регистрации
MIN_NICKNAME_LENGTH=3
MAX_NICKNAME_LENGTH=20
ALLOWED_REGIONS=Москва,Санкт-Петербург,Новосибирск,Екатеринбург,Казань

# Настройки магазина
SHOP_ENABLED=True
MAX_PURCHASE_PER_DAY=10
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example_content)

def check_virtual_environment():
    """Проверка виртуального окружения"""
    print("\n🐍 Проверка виртуального окружения...")
    
    # Проверяем, активировано ли виртуальное окружение
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Виртуальное окружение активировано")
        
        # Проверяем наличие venv директории
        venv_path = Path('venv')
        if venv_path.exists():
            print(f"✅ Директория venv найдена: {venv_path}")
        else:
            print("⚠️  Директория venv не найдена")
        
        return True
    else:
        print("⚠️  Виртуальное окружение не активировано")
        
        # Проверяем наличие venv директории
        venv_path = Path('venv')
        if venv_path.exists():
            print(f"✅ Директория venv найдена, но не активирована")
            
            # Определяем команду активации в зависимости от ОС
            os_name = platform.system()
            if os_name == 'Windows':
                activate_cmd = 'venv\\Scripts\\activate'
            else:
                activate_cmd = 'source venv/bin/activate'
            
            print(f"\n📝 Для активации выполните:")
            print(f"   {activate_cmd}")
            print("\nАктивировать виртуальное окружение сейчас? (y/n): ", end="")
            answer = input().strip().lower()
            
            if answer == 'y':
                activate_virtual_env(os_name)
        else:
            print("❌ Директория venv не найдена")
            print("\nСоздать виртуальное окружение? (y/n): ", end="")
            answer = input().strip().lower()
            
            if answer == 'y':
                create_virtual_environment()
        
        return False

def activate_virtual_env(os_name):
    """Активация виртуального окружения"""
    if os_name == 'Windows':
        activate_script = 'venv\\Scripts\\activate'
        print(f"\n🚀 Активация виртуального окружения...")
        print(f"Выполните: {activate_script}")
        print("Или запустите run.py заново из активированного окружения")
    else:
        print("\n🚀 Для активации выполните в терминале:")
        print("source venv/bin/activate")
    
    # Не можем программно активировать venv в текущем процессе
    print("\n⚠️  Перезапустите run.py после активации виртуального окружения")
    sys.exit(0)

def create_virtual_environment():
    """Создание виртуального окружения"""
    print("\n🚀 Создание виртуального окружения...")
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        print("✅ Виртуальное окружение создано")
        
        os_name = platform.system()
        if os_name == 'Windows':
            print("\n📝 Для активации выполните:")
            print("   venv\\Scripts\\activate")
        else:
            print("\n📝 Для активации выполните:")
            print("   source venv/bin/activate")
        
        print("\n⚠️  Активируйте виртуальное окружение и перезапустите run.py")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка создания виртуального окружения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return False

def check_dependencies():
    """Проверка зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    requirements_path = Path('requirements.txt')
    
    if not requirements_path.exists():
        print("❌ Файл requirements.txt не найден")
        return False
    
    try:
        # Пытаемся импортировать основные зависимости
        import_dependencies = [
            ('aiogram', 'aiogram'),
            ('python-dotenv', 'dotenv'),
            ('aiohttp', 'aiohttp'),
        ]
        
        all_deps_ok = True
        
        for package, import_name in import_dependencies:
            try:
                __import__(import_name)
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} - не установлен")
                all_deps_ok = False
        
        if not all_deps_ok:
            print("\n⚠️  Некоторые зависимости не установлены.")
            print("Установить зависимости? (y/n): ", end="")
            answer = input().strip().lower()
            
            if answer == 'y':
                install_dependencies()
        
        return all_deps_ok
    except Exception as e:
        print(f"❌ Ошибка проверки зависимостей: {e}")
        return False

def install_dependencies():
    """Установка зависимостей"""
    print("\n🚀 Установка зависимостей...")
    
    try:
        # Проверяем, активировано ли виртуальное окружение
        python_executable = sys.executable
        
        print(f"Используется Python: {python_executable}")
        
        result = subprocess.run(
            [python_executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Зависимости успешно установлены")
            return True
        else:
            print(f"❌ Ошибка установки зависимостей:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка при установке зависимостей: {e}")
        return False

def run_bot():
    """Запуск бота"""
    print("\n" + "=" * 60)
    print("🚀 Запуск GromFitBot...")
    print("=" * 60)
    
    try:
        # Добавляем корневую директорию в путь Python
        current_dir = Path.cwd()
        sys.path.insert(0, str(current_dir))
        
        # Импортируем и запускаем основной скрипт
        from src.main import main
        main()
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("\nВозможные причины:")
        print("1. Не установлены зависимости")
        print("2. Неправильная структура проекта")
        print("3. Отсутствуют необходимые файлы")
        
        print("\nПроверьте, что:")
        print("1. Все файлы скопированы из репозитория")
        print("2. Виртуальное окружение активировано")
        print("3. Зависимости установлены (pip install -r requirements.txt)")
        
        return False
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
        return True
    except Exception as e:
        print(f"\n❌ Ошибка запуска бота: {e}")
        
        # Выводим traceback для отладки
        import traceback
        traceback.print_exc()
        
        return False
    
    return True

def run_diagnostics():
    """Запуск диагностики системы"""
    print_header()
    
    # Проверка окружения
    if not check_environment():
        return False
    
    # Проверка директорий
    if not check_directories():
        print("\n⚠️  Проблемы со структурой директорий")
    
    # Проверка файлов
    if not check_files():
        print("\n⚠️  Отсутствуют некоторые файлы")
    
    # Проверка .env файла
    if not check_env_file():
        print("\n⚠️  Проблемы с .env файлом")
        return False
    
    # Проверка виртуального окружения
    check_virtual_environment()
    
    # Проверка зависимостей
    check_dependencies()
    
    return True

def main():
    """Основная функция запуска"""
    try:
        # Запускаем диагностику
        if not run_diagnostics():
            print("\n❌ Диагностика выявила проблемы")
            print("\n📋 Рекомендации:")
            print("1. Убедитесь, что все файлы скопированы из репозитория")
            print("2. Настройте .env файл с токеном бота")
            print("3. Активируйте виртуальное окружение")
            print("4. Установите зависимости: pip install -r requirements.txt")
            return
        
        # Предлагаем запустить бота
        print("\n" + "=" * 60)
        print("✅ Диагностика завершена успешно")
        print("=" * 60)
        
        print("\nЗапустить бота? (y/n): ", end="")
        answer = input().strip().lower()
        
        if answer == 'y':
            run_bot()
        else:
            print("\n👋 Завершение работы")
    
    except KeyboardInterrupt:
        print("\n\n👋 Завершение работы")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()