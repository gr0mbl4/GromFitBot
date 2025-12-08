import asyncio
import sqlite3
import json
import random
import string
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

class GromFitCompleteBot:
    def __init__(self):
        self.conn = sqlite3.connect('gromfit.db', check_same_thread=False)
        self.setup_database()
        self.current_user_id = None
        
        # DonationAlerts настройки
        self.da_config = {
            'client_id': '16677',
            'client_secret': 'OuwpXPkCFcIAfkqwo8O2H02mnSH8waqafj0wzfmB',
            'redirect_uri': 'https://dalink.to/gromfitbot',
            'api_base_url': 'https://www.donationalerts.com/api/v1',
            'auth_url': 'https://www.donationalerts.com/oauth/authorize',
            'token_url': 'https://www.donationalerts.com/oauth/token'
        }
        
        # Все варианты покупок
        self.payment_options = {
            'voices_10': {'amount': 49, 'description': '🎤 10 голосовых сообщений (15 сек)'},
            'voices_30': {'amount': 119, 'description': '🎤 30 голосовых сообщений (15 сек) 🔥 Выгода 28₽'},
            'voices_100': {'amount': 299, 'description': '🎤 100 голосовых сообщений (15 сек) 💎 Выгода 191₽'},
            'voices_10_daily': {'amount': 199, 'description': '🔄 10 ГС в день (30 дней)'},
            'voices_25_daily': {'amount': 399, 'description': '🔄 25 ГС в день (30 дней) 🔥 Популярный'},
            'voices_999_daily': {'amount': 799, 'description': '🔄 999 ГС в день (30 дней) 💎 Безлимит'},
            'premium_1_month': {'amount': 590, 'description': '💎 Премиум на 1 месяц'},
            'premium_2_months': {'amount': 999, 'description': '💎 Премиум на 2 месяца 🔥 Выгода 181₽'},
            'premium_3_months': {'amount': 1299, 'description': '💎 Премиум на 3 месяца 💎 Выгода 471₽'},
            'gift_premium_1_month': {'amount': 590, 'description': '🎁 Подарочный код: Премиум 1 месяц'},
            'gift_premium_2_months': {'amount': 999, 'description': '🎁 Подарочный код: Премиум 2 месяца'},
            'gift_premium_3_months': {'amount': 1299, 'description': '🎁 Подарочный код: Премиум 3 месяца'},
            'analysis_10': {'amount': 79, 'description': '📊 10 AI анализов'},
            'analysis_30': {'amount': 199, 'description': '📊 30 AI анализов 🔥 Выгода 38₽'},
            'analysis_100': {'amount': 699, 'description': '📊 100 AI анализов 💎 Выгода 91₽'}
        }
        
        # Система достижений
        self.achievements = [
            {"id": 1, "name": "Новичок", "desc": "Выполнить первую тренировку"},
            {"id": 2, "name": "Силач", "desc": "Пожать в сумме 1000 кг"},
            {"id": 3, "name": "Мастер приседа", "desc": "Присесть 5000 кг в сумме"},
            {"id": 4, "name": "Стальной пресс", "desc": "1000 повторений на пресс"},
            {"id": 5, "name": "Терпеливый", "desc": "10 тренировок подряд"},
            {"id": 6, "name": "Железный человек", "desc": "Пожать в сумме 10000 кг"},
            {"id": 7, "name": "Король приседа", "desc": "Присесть 10000 кг в сумме"},
            {"id": 8, "name": "Марафонец", "desc": "30 тренировок за месяц"},
        ]
        
        print("🏋️ GromFit Complete Bot")
        print("✅ Все системы готовы\n")
    
    def setup_database(self):
        """Создаем базу данных"""
        cursor = self.conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                name TEXT,
                region TEXT,
                referral_code TEXT UNIQUE,
                referrer_id INTEGER,
                premium BOOLEAN DEFAULT 0,
                premium_until TIMESTAMP,
                da_access_token TEXT,
                da_refresh_token TEXT,
                da_token_expires TIMESTAMP,
                voices_remaining INTEGER DEFAULT 0,
                voices_daily INTEGER DEFAULT 3,
                voices_used_today INTEGER DEFAULT 0,
                last_voice_date TEXT,
                analysis_remaining INTEGER DEFAULT 0,
                registration_step TEXT DEFAULT 'start',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Тренировки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exercises TEXT,
                total_weight INTEGER,
                duration_minutes INTEGER
            )
        ''')
        
        # Достижения
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                achievement_id INTEGER,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Платежи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                payment_type TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Подарочные коды
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gift_codes (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                gift_type TEXT,
                duration_days INTEGER,
                created_by INTEGER,
                used_by INTEGER,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Промо-коды
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                description TEXT,
                bonus_type TEXT,
                bonus_value INTEGER,
                usage_limit INTEGER,
                used_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Добавляем тестовые промо-коды
        cursor.execute('''
            INSERT OR IGNORE INTO promo_codes (code, description, bonus_type, bonus_value, usage_limit)
            VALUES 
            ('NEWYEAR2024', 'Новогодний бонус', 'premium_days', 7, 1000),
            ('SUMMERFIT', 'Летняя акция', 'voices', 10, 500)
        ''')
        
        self.conn.commit()
    
    # ========== РЕГИСТРАЦИЯ ==========
    
    def start_registration(self, user_id, username, first_name, last_name):
        """Начинает регистрацию пользователя"""
        cursor = self.conn.cursor()
        
        # Проверяем есть ли пользователь
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            # Новый пользователь
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name, registration_step)
                VALUES (?, ?, ?, ?, 'name')
            ''', (user_id, username, first_name, last_name))
            self.conn.commit()
            self.current_user_id = user_id
            return "waiting_for_name"
        else:
            # Пользователь уже есть
            registration_step = user[20]  # registration_step
            self.current_user_id = user_id
            
            if registration_step != 'completed':
                return registration_step
            else:
                return "main_menu"
    
    def process_name(self, name):
        """Обрабатывает ввод имени"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET name = ?, registration_step = ? WHERE telegram_id = ?',
            (name, 'region', self.current_user_id)
        )
        self.conn.commit()
        return "waiting_for_region"
    
    def process_region(self, region):
        """Обрабатывает ввод региона"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET region = ?, registration_step = ? WHERE telegram_id = ?',
            (region, 'referral', self.current_user_id)
        )
        self.conn.commit()
        return "waiting_for_referral"
    
    def process_referral(self, referral_input):
        """Обрабатывает реферальный код"""
        cursor = self.conn.cursor()
        
        referrer_id = None
        if referral_input.lower() != 'пропустить':
            # Проверяем реферальный код
            cursor.execute('SELECT telegram_id FROM users WHERE referral_code = ?', (referral_input.upper(),))
            result = cursor.fetchone()
            if result:
                referrer_id = result[0]
                print(f"✅ Найден реферальный код! Пригласил пользователь {referrer_id}")
        
        # Генерируем реферальный код для пользователя
        referral_code = self.generate_referral_code()
        
        # Завершаем регистрацию
        cursor.execute('''
            UPDATE users SET referral_code = ?, referrer_id = ?, registration_step = ?
            WHERE telegram_id = ?
        ''', (referral_code, referrer_id, 'completed', self.current_user_id))
        
        self.conn.commit()
        
        # Получаем данные пользователя
        cursor.execute('SELECT name, region FROM users WHERE telegram_id = ?', (self.current_user_id,))
        user = cursor.fetchone()
        
        print(f"\n🎉 Регистрация завершена, {user[0]}!")
        print(f"📍 Регион: {user[1]}")
        print(f"🎯 Реферальный код: {referral_code}")
        
        return "main_menu"
    
    def generate_referral_code(self):
        """Генерирует реферальный код"""
        while True:
            code = 'GF' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (code,))
            if not cursor.fetchone():
                return code
    
    # ========== DONATIONALERTS ПЛАТЕЖИ ==========
    
    def get_da_auth_url(self, user_id):
        """Генерирует URL для авторизации в DonationAlerts"""
        params = {
            'client_id': self.da_config['client_id'],
            'redirect_uri': self.da_config['redirect_uri'],
            'response_type': 'code',
            'scope': 'oauth-donation-index oauth-user-show',
            'state': f"gromfit_{user_id}"
        }
        return f"{self.da_config['auth_url']}?{urlencode(params)}"
    
    def exchange_code_for_token(self, authorization_code):
        """Обменивает код авторизации на access token"""
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.da_config['client_id'],
            'client_secret': self.da_config['client_secret'],
            'redirect_uri': self.da_config['redirect_uri'],
            'code': authorization_code
        }
        
        try:
            response = requests.post(self.da_config['token_url'], data=data)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
        return None
    
    def save_user_tokens(self, user_id, token_data):
        """Сохраняет токены пользователя"""
        cursor = self.conn.cursor()
        expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        
        cursor.execute('''
            UPDATE users SET 
            da_access_token = ?, 
            da_refresh_token = ?, 
            da_token_expires = ?
            WHERE telegram_id = ?
        ''', (token_data['access_token'], token_data['refresh_token'], expires_at, user_id))
        
        self.conn.commit()
        return True
    
    def process_da_code(self, authorization_code):
        """Обрабатывает код авторизации"""
        token_data = self.exchange_code_for_token(authorization_code)
        if token_data:
            success = self.save_user_tokens(self.current_user_id, token_data)
            if success:
                return True, "✅ DonationAlerts успешно подключен!"
        return False, "❌ Ошибка подключения. Попробуйте еще раз."
    
    def create_pending_payment(self, payment_type):
        """Создает ожидающий платеж"""
        if payment_type not in self.payment_options:
            return None
        
        amount = self.payment_options[payment_type]['amount']
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO pending_payments (user_id, payment_type, amount)
            VALUES (?, ?, ?)
        ''', (self.current_user_id, payment_type, amount))
        
        self.conn.commit()
        return amount
    
    # ========== ПАРСЕР ТРЕНИРОВОК ==========
    
    def parse_exercises(self, text):
        """Парсит упражнения из текста"""
        import re
        exercises = []
        lines = text.strip().split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            # Паттерн: "1. Жим лежа 3x10 50кг"
            match = re.match(r'(\d+)\.?\s*(.+?)\s+(\d+)x(\d+)\s*(\d+)?\s*кг?', line, re.IGNORECASE)
            if match:
                exercise = {
                    'order': int(match.group(1)),
                    'name': match.group(2).strip(),
                    'sets': int(match.group(3)),
                    'reps': int(match.group(4)),
                    'weight': int(match.group(5)) if match.group(5) else 0
                }
                exercises.append(exercise)
        
        return exercises
    
    def save_workout(self, exercises):
        """Сохраняет тренировку"""
        total_weight = sum(ex['weight'] * ex['sets'] * ex['reps'] for ex in exercises)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO workouts (user_id, exercises, total_weight)
            VALUES (?, ?, ?)
        ''', (self.current_user_id, json.dumps(exercises), total_weight))
        
        # Проверяем достижения
        self.check_achievements(total_weight)
        
        self.conn.commit()
        return total_weight
    
    # ========== СИСТЕМА ДОСТИЖЕНИЙ ==========
    
    def check_achievements(self, total_weight):
        """Проверяет и выдает достижения"""
        cursor = self.conn.cursor()
        
        # Считаем количество тренировок
        cursor.execute('SELECT COUNT(*) FROM workouts WHERE user_id = ?', (self.current_user_id,))
        workout_count = cursor.fetchone()[0]
        
        new_achievements = []
        
        # Новичок - первая тренировка
        if workout_count == 1:
            new_achievements.append(1)
        
        # Силач - 1000 кг в сумме
        if total_weight >= 1000:
            new_achievements.append(2)
        
        # Железный человек - 10000 кг в сумме
        if total_weight >= 10000:
            new_achievements.append(6)
        
        # Добавляем достижения
        for ach_id in new_achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
                VALUES (?, ?)
            ''', (self.current_user_id, ach_id))
        
        self.conn.commit()
        return new_achievements
    
    # ========== ИНТЕРФЕЙС ==========
    
    def show_main_menu(self):
        """Главное меню"""
        print("\n" + "🏠" + "="*40 + "🏠")
        print("           ГЛАВНОЕ МЕНЮ GROMFIT")
        print("🏠" + "="*40 + "🏠")
        print("1. 🏋️ Загрузить тренировку")
        print("2. 📊 Мои упражнения")
        print("3. 🏆 Достижения")
        print("4. 👤 Профиль")
        print("5. 💳 Магазин")
        print("6. 🎫 Ввести промо-код")
        print("7. 🚪 Выход")
    
    def show_shop_menu(self):
        """Меню магазина"""
        while True:
            print("\n" + "🛍️" + "="*40 + "🛍️")
            print("           МАГАЗИН GROMFIT")
            print("🛍️" + "="*40 + "🛍️")
            
            # Проверяем подключение DA
            cursor = self.conn.cursor()
            cursor.execute('SELECT da_access_token FROM users WHERE telegram_id = ?', (self.current_user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                print("❌ DonationAlerts не подключен")
                print("1. 🔗 Подключить DonationAlerts")
                print("2. 🔙 Назад")
                
                choice = input("\n🎯 Выберите действие: ").strip()
                
                if choice == '1':
                    auth_url = self.get_da_auth_url(self.current_user_id)
                    print(f"\n🔗 Ссылка для авторизации:\n{auth_url}")
                    print("\nПосле авторизации отправьте код командой /da_code")
                    input("📌 Нажмите Enter чтобы продолжить...")
                elif choice == '2':
                    break
                continue
            
            print("✅ DonationAlerts подключен")
            print("\n1. 🎤 Голосовые сообщения")
            print("2. 💎 Премиум подписка")
            print("3. 🎁 Подарить премиум")
            print("4. 📊 AI анализы")
            print("5. 🔙 Назад")
            
            choice = input("\n🎯 Выберите категорию: ").strip()
            
            if choice == '1':
                self.show_voices_menu()
            elif choice == '2':
                self.show_premium_menu()
            elif choice == '3':
                self.show_gift_menu()
            elif choice == '4':
                self.show_analysis_menu()
            elif choice == '5':
                break
            else:
                print("❌ Неверный выбор")
    
    def show_voices_menu(self):
        """Меню голосовых сообщений"""
        print("\n🎤 ГОЛОСОВЫЕ СООБЩЕНИЯ:")
        print("1. 10 сообщений - 49₽")
        print("2. 30 сообщений - 119₽")
        print("3. 100 сообщений - 299₽")
        print("4. 🔙 Назад")
        
        choice = input("\n🎯 Выберите вариант: ").strip()
        options = {'1': 'voices_10', '2': 'voices_30', '3': 'voices_100'}
        
        if choice in options:
            self.process_payment(options[choice])
        elif choice == '4':
            return
    
    def show_premium_menu(self):
        """Меню премиум подписки"""
        print("\n💎 ПРЕМИУМ ПОДПИСКА:")
        print("1. 1 месяц - 590₽")
        print("2. 2 месяца - 999₽")
        print("3. 3 месяца - 1299₽")
        print("4. 🔙 Назад")
        
        choice = input("\n🎯 Выберите вариант: ").strip()
        options = {'1': 'premium_1_month', '2': 'premium_2_months', '3': 'premium_3_months'}
        
        if choice in options:
            self.process_payment(options[choice])
        elif choice == '4':
            return
    
    def show_gift_menu(self):
        """Меню подарков"""
        print("\n🎁 ПОДАРИТЬ ПРЕМИУМ:")
        print("1. Премиум 1 месяц - 590₽")
        print("2. Премиум 2 месяца - 999₽")
        print("3. Премиум 3 месяца - 1299₽")
        print("4. 🔙 Назад")
        
        choice = input("\n🎯 Выберите вариант: ").strip()
        options = {'1': 'gift_premium_1_month', '2': 'gift_premium_2_months', '3': 'gift_premium_3_months'}
        
        if choice in options:
            self.process_payment(options[choice])
        elif choice == '4':
            return
    
    def show_analysis_menu(self):
        """Меню анализов"""
        print("\n📊 AI АНАЛИЗЫ:")
        print("1. 10 анализов - 79₽")
        print("2. 30 анализов - 199₽")
        print("3. 100 анализов - 699₽")
        print("4. 🔙 Назад")
        
        choice = input("\n🎯 Выберите вариант: ").strip()
        options = {'1': 'analysis_10', '2': 'analysis_30', '3': 'analysis_100'}
        
        if choice in options:
            self.process_payment(options[choice])
        elif choice == '4':
            return
    
    def process_payment(self, payment_type):
        """Обрабатывает платеж"""
        amount = self.create_pending_payment(payment_type)
        if amount:
            description = self.payment_options[payment_type]['description']
            
            print(f"\n💰 {description}")
            print(f"💳 Сумма: {amount} RUB")
            print(f"\n📋 ИНСТРУКЦИЯ:")
            print("1. Перейдите в DonationAlerts")
            print("2. Создайте донат на указанную сумму")
            print("3. В сообщении укажите: GromFit")
            print("4. Совершите оплату")
            print("5. Ожидайте активации (до 5 минут)")
            input("\n📌 Нажмите Enter чтобы продолжить...")
    
    def show_profile(self):
        """Показывает профиль"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name, region, referral_code, premium, voices_remaining, analysis_remaining
            FROM users WHERE telegram_id = ?
        ''', (self.current_user_id,))
        user = cursor.fetchone()
        
        if user:
            print(f"\n👤 ПРОФИЛЬ:")
            print(f"   Имя: {user[0]}")
            print(f"   Регион: {user[1]}")
            print(f"   Реф. код: {user[2]}")
            print(f"   Премиум: {'✅' if user[3] else '❌'}")
            print(f"   Голосовые: {user[4]} шт")
            print(f"   Анализы: {user[5]} шт")
    
    def show_achievements(self):
        """Показывает достижения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ua.achievement_id, a.name, a.desc 
            FROM user_achievements ua
            JOIN (SELECT * FROM (VALUES 
                (1, 'Новичок', 'Первая тренировка'),
                (2, 'Силач', '1000 кг в сумме'),
                (3, 'Мастер приседа', '5000 кг в приседе'),
                (4, 'Стальной пресс', '1000 повторений на пресс'),
                (5, 'Терпеливый', '10 тренировок подряд'),
                (6, 'Железный человек', '10000 кг в сумме'),
                (7, 'Король приседа', '10000 кг в приседе'),
                (8, 'Марафонец', '30 тренировок за месяц')
            )) AS a(id, name, desc) ON ua.achievement_id = a.id
            WHERE ua.user_id = ?
        ''', (self.current_user_id,))
        
        achievements = cursor.fetchall()
        
        print(f"\n🏆 ДОСТИЖЕНИЯ ({len(achievements)}/8):")
        for ach_id, name, desc in achievements:
            print(f"   ✅ {name} - {desc}")
        
        if len(achievements) < 8:
            print(f"\n🎯 Доступно еще {8 - len(achievements)} достижений!")
    
    def process_promo_code(self, code):
        """Обрабатывает промо-код"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM promo_codes WHERE code = ? AND is_active = 1', (code.upper(),))
        promo = cursor.fetchone()
        
        if not promo:
            return "❌ Промо-код не найден"
        
        promo_id, _, description, bonus_type, bonus_value, usage_limit, used_count, _ = promo
        
        if used_count >= usage_limit:
            return "❌ Лимит использования промо-кода исчерпан"
        
        # Проверяем не использовал ли уже
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (self.current_user_id,))
        user = cursor.fetchone()
        if not user:
            return "❌ Пользователь не найден"
        
        # Активируем промо-код
        cursor.execute('UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?', (promo_id,))
        
        # Начисляем бонус
        if bonus_type == 'premium_days':
            premium_until = datetime.now() + timedelta(days=bonus_value)
            cursor.execute('UPDATE users SET premium = 1, premium_until = ? WHERE telegram_id = ?', 
                         (premium_until, self.current_user_id))
            bonus_text = f"{bonus_value} дней премиума"
        elif bonus_type == 'voices':
            cursor.execute('UPDATE users SET voices_remaining = voices_remaining + ? WHERE telegram_id = ?', 
                         (bonus_value, self.current_user_id))
            bonus_text = f"{bonus_value} голосовых сообщений"
        
        self.conn.commit()
        return f"✅ Промо-код активирован! Получено: {bonus_text}"
    
    # ========== ЗАПУСК БОТА ==========
    
    def run_bot(self):
        """Запускает бота"""
        print("=" * 50)
        print("🏋️ GROMFIT BOT - ЗАПУСК")
        print("=" * 50)
        
        # Регистрация/авторизация
        print("\n🔐 РЕГИСТРАЦИЯ")
        user_id = int(input("Введите ваш ID Telegram: ") or "123456789")
        username = input("Введите username: ") or "test_user"
        first_name = input("Введите имя: ") or "Тест"
        last_name = input("Введите фамилию: ") or "Пользователь"
        
        state = self.start_registration(user_id, username, first_name, last_name)
        
        # Процесс регистрации
        while state != "main_menu":
            if state == "waiting_for_name":
                name = input("\n🤖 Как мне к тебе обращаться? ")
                state = self.process_name(name)
            elif state == "waiting_for_region":
                print("\n🤖 Выбери регион: Москва, СПб, Новосибирск, Другой")
                region = input("Твой регион: ")
                state = self.process_region(region)
            elif state == "waiting_for_referral":
                print("\n🤖 Есть реферальный код? (если нет - напиши 'пропустить')")
                referral = input("Реферальный код: ")
                state = self.process_referral(referral)
        
        # Главный цикл бота
        while True:
            self.show_main_menu()
            choice = input("\n🎯 Выберите действие: ").strip()
            
            if choice == '1':
                self.process_workout()
            elif choice == '2':
                self.show_workouts()
            elif choice == '3':
                self.show_achievements()
            elif choice == '4':
                self.show_profile()
            elif choice == '5':
                self.show_shop_menu()
            elif choice == '6':
                code = input("Введите промо-код: ").strip()
                result = self.process_promo_code(code)
                print(result)
            elif choice == '7':
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор")
    
    def process_workout(self):
        """Обрабатывает загрузку тренировки"""
        print("\n💪 ЗАГРУЗКА ТРЕНИРОВКИ")
        print("Пример формата:")
        print("1. Жим лежа 3x10 50кг")
        print("2. Приседания 4x12 60кг")
        print("3. Тяга блока 3x15 40кг")
        
        workout_text = input("\nВведите упражнения: ")
        
        if workout_text:
            exercises = self.parse_exercises(workout_text)
            if exercises:
                total_weight = self.save_workout(exercises)
                
                print(f"\n✅ ТРЕНИРОВКА СОХРАНЕНА!")
                print("📊 Ваши упражнения:")
                for ex in exercises:
                    print(f"   {ex['order']}. {ex['name']} - {ex['sets']}x{ex['reps']} ({ex['weight']} кг)")
                
                print(f"💪 Общий вес: {total_weight} кг")
                
                # Проверяем достижения
                new_achievements = self.check_achievements(total_weight)
                if new_achievements:
                    print("\n🎉 НОВЫЕ ДОСТИЖЕНИЯ!")
                    for ach_id in new_achievements:
                        achievement = next(a for a in self.achievements if a['id'] == ach_id)
                        print(f"   ✅ {achievement['name']} - {achievement['desc']}")
            else:
                print("❌ Не удалось распознать упражнения")
    
    def show_workouts(self):
        """Показывает историю тренировок"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM workouts WHERE user_id = ?', (self.current_user_id,))
        count = cursor.fetchone()[0]
        
        print(f"\n📊 ВАШИ ТРЕНИРОВКИ: {count} всего")
        
        if count > 0:
            cursor.execute('''
                SELECT date, total_weight FROM workouts 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT 5
            ''', (self.current_user_id,))
            
            workouts = cursor.fetchall()
            print("\n📅 Последние тренировки:")
            for date, weight in workouts:
                print(f"   📅 {date} - {weight} кг")
        else:
            print("💡 Загрузите первую тренировку!")

if __name__ == "__main__":
    bot = GromFitCompleteBot()
    bot.run_bot()