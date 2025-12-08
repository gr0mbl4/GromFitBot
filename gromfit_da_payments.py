import sqlite3
import json
import random
import string
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

class GromFitDAPayments:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.setup_database()
        self.current_user_id = None
        
        # Твои настройки DonationAlerts
        self.da_config = {
            'client_id': '16677',  # ID приложения
            'client_secret': 'OuwpXPkCFcIAfkqwo8O2H02mnSH8waqafj0wzfmB',  # Ключ API
            'redirect_uri': 'https://dalink.to/gromfitbot',  # Твой redirect URI
            'api_base_url': 'https://www.donationalerts.com/api/v1',
            'auth_url': 'https://www.donationalerts.com/oauth/authorize',
            'token_url': 'https://www.donationalerts.com/oauth/token'
        }
        
        # Все варианты покупок для GromFit
        self.payment_options = {
            # Голосовые сообщения (пакеты)
            'voices_10': {
                'amount': 49,
                'description': '🎤 10 голосовых сообщений (15 сек)',
                'type': 'voices'
            },
            'voices_30': {
                'amount': 119, 
                'description': '🎤 30 голосовых сообщений (15 сек) 🔥 Выгода 28₽',
                'type': 'voices'
            },
            'voices_100': {
                'amount': 299,
                'description': '🎤 100 голосовых сообщений (15 сек) 💎 Выгода 191₽',
                'type': 'voices'
            },
            
            # Голосовые сообщения (подписки)
            'voices_10_daily': {
                'amount': 199,
                'description': '🔄 10 ГС в день (30 дней)',
                'type': 'voices_subscription'
            },
            'voices_25_daily': {
                'amount': 399,
                'description': '🔄 25 ГС в день (30 дней) 🔥 Популярный',
                'type': 'voices_subscription'
            },
            'voices_999_daily': {
                'amount': 799,
                'description': '🔄 999 ГС в день (30 дней) 💎 Безлимит',
                'type': 'voices_subscription'
            },
            
            # Премиум подписка
            'premium_1_month': {
                'amount': 590,
                'description': '💎 Премиум на 1 месяц',
                'type': 'premium'
            },
            'premium_2_months': {
                'amount': 999,
                'description': '💎 Премиум на 2 месяца 🔥 Выгода 181₽',
                'type': 'premium'
            },
            'premium_3_months': {
                'amount': 1299,
                'description': '💎 Премиум на 3 месяца 💎 Выгода 471₽',
                'type': 'premium'
            },
            
            # Подарочные коды премиума
            'gift_premium_1_month': {
                'amount': 590,
                'description': '🎁 Подарочный код: Премиум 1 месяц',
                'type': 'gift_code'
            },
            'gift_premium_2_months': {
                'amount': 999,
                'description': '🎁 Подарочный код: Премиум 2 месяца',
                'type': 'gift_code'
            },
            'gift_premium_3_months': {
                'amount': 1299,
                'description': '🎁 Подарочный код: Премиум 3 месяца',
                'type': 'gift_code'
            },
            
            # AI анализы
            'analysis_10': {
                'amount': 79,
                'description': '📊 10 AI анализов',
                'type': 'analysis'
            },
            'analysis_30': {
                'amount': 199,
                'description': '📊 30 AI анализов 🔥 Выгода 38₽',
                'type': 'analysis'
            },
            'analysis_100': {
                'amount': 699,
                'description': '📊 100 AI анализов 💎 Выгода 91₽',
                'type': 'analysis'
            }
        }
        
        print("🏋️ GromFit - DonationAlerts Payments")
        print("✅ Платежная система готова\n")
    
    def setup_database(self):
        """Создаем базу данных"""
        cursor = self.conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                da_access_token TEXT,
                da_refresh_token TEXT,
                da_token_expires TIMESTAMP,
                premium BOOLEAN DEFAULT 0,
                premium_until TIMESTAMP,
                voices_remaining INTEGER DEFAULT 0,
                voices_daily INTEGER DEFAULT 3,
                analysis_remaining INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ожидающие платежи
        cursor.execute('''
            CREATE TABLE pending_payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                payment_type TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Завершенные платежи
        cursor.execute('''
            CREATE TABLE completed_payments (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                payment_type TEXT,
                amount INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Подарочные коды
        cursor.execute('''
            CREATE TABLE gift_codes (
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
        
        # Тестовый пользователь
        cursor.execute('''
            INSERT INTO users (telegram_id, username)
            VALUES (?, ?)
        ''', (123456789, 'test_user'))
        
        self.conn.commit()
        self.current_user_id = 123456789
    
    def get_da_auth_url(self, user_id):
        """Генерирует URL для авторизации в DonationAlerts"""
        params = {
            'client_id': self.da_config['client_id'],
            'redirect_uri': self.da_config['redirect_uri'],
            'response_type': 'code',
            'scope': 'oauth-donation-index oauth-user-show',
            'state': f"gromfit_{user_id}"  # Идентификатор пользователя
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
            print(f"🔄 Отправка запроса для обмена кода на токен...")
            response = requests.post(self.da_config['token_url'], data=data)
            print(f"📡 Ответ от DA: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Токен успешно получен")
                return token_data
            else:
                print(f"❌ Ошибка получения токена: {response.status_code}")
                print(f"📝 Ответ: {response.text}")
                return None
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
        print(f"✅ Токены сохранены для пользователя {user_id}")
        return True
    
    def get_valid_access_token(self, user_id):
        """Получает валидный access token"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT da_access_token, da_token_expires FROM users WHERE telegram_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return None
        
        access_token, expires_at = result
        
        # Если токен истек - нужно обновить (в реальном боте добавить логику обновления)
        if datetime.now() > datetime.fromisoformat(expires_at):
            print("⚠️ Токен истек, требуется обновление")
            return None
        
        return access_token
    
    def get_user_donations(self, user_id):
        """Получает список донатов пользователя"""
        access_token = self.get_valid_access_token(user_id)
        if not access_token:
            print("❌ Нет валидного токена доступа")
            return None
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Получаем последние донаты
            url = f"{self.da_config['api_base_url']}/alerts/donations"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                donations_data = response.json()
                donations = donations_data.get('data', [])
                print(f"✅ Получено {len(donations)} донатов")
                return donations
            else:
                print(f"❌ Ошибка получения донатов: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None
    
    def check_pending_payments(self, user_id):
        """Проверяет и обрабатывает ожидающие платежи"""
        donations = self.get_user_donations(user_id)
        if not donations:
            return []
        
        cursor = self.conn.cursor()
        completed_payments = []
        
        # Получаем ожидающие платежи пользователя
        cursor.execute('SELECT id, payment_type, amount FROM pending_payments WHERE user_id = ? AND status = "pending"', (user_id,))
        pending_payments = cursor.fetchall()
        
        for payment_id, payment_type, expected_amount in pending_payments:
            # Ищем донат с подходящей суммой
            for donation in donations:
                if donation['amount'] == expected_amount:
                    # Нашли подходящий донат!
                    print(f"✅ Найден донат для платежа {payment_type} на сумму {expected_amount}₽")
                    
                    # Помечаем платеж как завершенный
                    cursor.execute('UPDATE pending_payments SET status = ? WHERE id = ?', ('completed', payment_id))
                    cursor.execute('''
                        INSERT INTO completed_payments (user_id, payment_type, amount)
                        VALUES (?, ?, ?)
                    ''', (user_id, payment_type, expected_amount))
                    
                    # Активируем услугу
                    self.activate_service(user_id, payment_type)
                    
                    completed_payments.append({
                        'type': payment_type,
                        'amount': expected_amount,
                        'description': self.payment_options[payment_type]['description']
                    })
                    
                    break
        
        self.conn.commit()
        return completed_payments
    
    def activate_service(self, user_id, payment_type):
        """Активирует услугу после оплаты"""
        cursor = self.conn.cursor()
        
        if payment_type.startswith('premium') and not payment_type.startswith('gift'):
            # Активация премиум подписки
            if payment_type == 'premium_1_month':
                days = 30
            elif payment_type == 'premium_2_months':
                days = 60
            elif payment_type == 'premium_3_months':
                days = 90
            else:
                days = 30
            
            premium_until = datetime.now() + timedelta(days=days)
            cursor.execute('UPDATE users SET premium = 1, premium_until = ? WHERE telegram_id = ?', 
                         (premium_until, user_id))
            print(f"✅ Активирован премиум на {days} дней для пользователя {user_id}")
            
        elif payment_type.startswith('gift_premium'):
            # Создание подарочного кода
            if payment_type == 'gift_premium_1_month':
                days = 30
            elif payment_type == 'gift_premium_2_months':
                days = 60
            elif payment_type == 'gift_premium_3_months':
                days = 90
            else:
                days = 30
            
            gift_code = self.generate_gift_code('premium', days, user_id)
            print(f"🎁 Создан подарочный код: {gift_code} (премиум на {days} дней)")
            
        elif payment_type.startswith('voices'):
            # Добавление голосовых сообщений
            if payment_type == 'voices_10':
                voices_to_add = 10
            elif payment_type == 'voices_30':
                voices_to_add = 30
            elif payment_type == 'voices_100':
                voices_to_add = 100
            elif payment_type == 'voices_10_daily':
                voices_to_add = 300  # 10 в день × 30 дней
            elif payment_type == 'voices_25_daily':
                voices_to_add = 750  # 25 в день × 30 дней
            elif payment_type == 'voices_999_daily':
                voices_to_add = 29970  # 999 в день × 30 дней
            else:
                voices_to_add = 0
            
            cursor.execute('UPDATE users SET voices_remaining = voices_remaining + ? WHERE telegram_id = ?', 
                         (voices_to_add, user_id))
            print(f"✅ Добавлено {voices_to_add} голосовых сообщений пользователю {user_id}")
            
        elif payment_type.startswith('analysis'):
            # Добавление AI анализов
            if payment_type == 'analysis_10':
                analysis_to_add = 10
            elif payment_type == 'analysis_30':
                analysis_to_add = 30
            elif payment_type == 'analysis_100':
                analysis_to_add = 100
            else:
                analysis_to_add = 0
            
            cursor.execute('UPDATE users SET analysis_remaining = analysis_remaining + ? WHERE telegram_id = ?', 
                         (analysis_to_add, user_id))
            print(f"✅ Добавлено {analysis_to_add} AI анализов пользователю {user_id}")
        
        self.conn.commit()
    
    def generate_gift_code(self, gift_type, duration_days, created_by):
        """Генерирует подарочный код"""
        while True:
            code = 'GF' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
            
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM gift_codes WHERE code = ?', (code,))
            if not cursor.fetchone():
                break
        
        cursor.execute('''
            INSERT INTO gift_codes (code, gift_type, duration_days, created_by)
            VALUES (?, ?, ?, ?)
        ''', (code, gift_type, duration_days, created_by))
        
        self.conn.commit()
        return code
    
    def create_pending_payment(self, user_id, payment_type):
        """Создает запись об ожидающем платеже"""
        if payment_type not in self.payment_options:
            return None
        
        amount = self.payment_options[payment_type]['amount']
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO pending_payments (user_id, payment_type, amount)
            VALUES (?, ?, ?)
        ''', (user_id, payment_type, amount))
        
        self.conn.commit()
        print(f"💰 Создан ожидающий платеж: {payment_type} на {amount}₽")
        return amount
    
    def show_payment_instructions(self, payment_type, amount):
        """Показывает инструкцию по оплате"""
        description = self.payment_options[payment_type]['description']
        
        instructions = f"""
💰 {description}
💳 Сумма: {amount} RUB

📋 ИНСТРУКЦИЯ ПО ОПЛАТЕ:

1. 🔗 Перейдите в ваш DonationAlerts:
   https://www.donationalerts.com/dashboard

2. 💰 Создайте донат на сумму: {amount} RUB

3. 📝 В сообщении укажите:
   "GromFit {payment_type}"

4. ✅ Совершите оплату удобным способом

5. ⏱️ Ожидайте активации (до 5 минут)

💡 После оплаты услуга активируется автоматически!
📞 При проблемах - обратитесь в поддержку
        """
        
        return instructions
    
    def setup_da_connection(self):
        """Показывает инструкцию по подключению DonationAlerts"""
        auth_url = self.get_da_auth_url(self.current_user_id)
        
        instructions = f"""
🔗 ПОДКЛЮЧЕНИЕ DONATIONALERTS

Для приема платежей необходимо подключить ваш аккаунт DonationAlerts:

1. 📱 Перейдите по ссылке:
   {auth_url}

2. ✅ Разрешите доступ приложению "GromFitBot"

3. 🔄 Вы будете перенаправлены и получите код авторизации

4. 📝 Отправьте код боту командой:
   /da_code ВАШ_КОД

После этого можно будет принимать платежи!
💳 Все платежи будут автоматически обрабатываться
        """
        
        return instructions
    
    def process_da_code(self, authorization_code):
        """Обрабатывает код авторизации"""
        print(f"🔄 Обработка кода авторизации: {authorization_code}")
        token_data = self.exchange_code_for_token(authorization_code)
        
        if token_data:
            success = self.save_user_tokens(self.current_user_id, token_data)
            if success:
                return True, "✅ DonationAlerts успешно подключен! Теперь вы можете принимать платежи."
            else:
                return False, "❌ Ошибка сохранения токенов."
        else:
            return False, "❌ Неверный код авторизации или ошибка подключения. Попробуйте еще раз."
    
    # Красивые меню (остаются как в предыдущей версии)
    def show_main_shop_menu(self):
        """Главное меню магазина"""
        while True:
            print("\n" + "🛍️" + "="*40 + "🛍️")
            print("           МАГАЗИН GROMFIT")
            print("🛍️" + "="*40 + "🛍️")
            
            # Проверяем статус подключения DA
            cursor = self.conn.cursor()
            cursor.execute('SELECT da_access_token FROM users WHERE telegram_id = ?', (self.current_user_id,))
            result = cursor.fetchone()
            
            if not result or not result[0]:
                print("❌ DonationAlerts не подключен")
                print("1. 🔗 Подключить DonationAlerts")
                print("2. 🔙 Назад")
                
                choice = input("\n🎯 Выберите действие: ").strip()
                
                if choice == '1':
                    instructions = self.setup_da_connection()
                    print(instructions)
                    # В демо просто показываем ссылку
                    auth_url = self.get_da_auth_url(self.current_user_id)
                    print(f"\n🔗 Ссылка для авторизации: {auth_url}")
                    input("📌 Нажмите Enter чтобы продолжить...")
                elif choice == '2':
                    break
                else:
                    print("❌ Неверный выбор")
                continue
            
            print("✅ DonationAlerts подключен")
            print("\n1. 🎤 Голосовые сообщения")
            print("2. 💎 Премиум подписка") 
            print("3. 🎁 Подарить премиум")
            print("4. 📊 AI анализы")
            print("5. 🔄 Проверить платежи")
            print("6. 🔙 Назад")
            
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
                self.check_user_payments()
            elif choice == '6':
                break
            else:
                print("❌ Неверный выбор")
    
    def show_voices_menu(self):
        """Меню голосовых сообщений"""
        while True:
            print("\n" + "🎤" + "="*35 + "🎤")
            print("      ГОЛОСОВЫЕ СООБЩЕНИЯ")
            print("🎤" + "="*35 + "🎤")
            
            print("\n📦 ПАКЕТЫ:")
            print("1. 🎤 10 сообщений - 49₽")
            print("2. 🎤 30 сообщений - 119₽ 🔥 Выгода 28₽")
            print("3. 🎤 100 сообщений - 299₽ 💎 Выгода 191₽")
            
            print("\n🔄 ПОДПИСКИ (в день):")
            print("4. 🔄 10 ГС/день - 199₽/мес")
            print("5. 🔄 25 ГС/день - 399₽/мес 🔥 Популярный")
            print("6. 🔄 999 ГС/день - 799₽/мес 💎 Безлимит")
            print("7. 🔙 Назад")
            
            choice = input("\n🎯 Выберите вариант: ").strip()
            
            options = {
                '1': 'voices_10',
                '2': 'voices_30', 
                '3': 'voices_100',
                '4': 'voices_10_daily',
                '5': 'voices_25_daily',
                '6': 'voices_999_daily'
            }
            
            if choice in options:
                payment_type = options[choice]
                amount = self.create_pending_payment(self.current_user_id, payment_type)
                
                if amount:
                    instructions = self.show_payment_instructions(payment_type, amount)
                    print(instructions)
                    input("📌 Нажмите Enter чтобы продолжить...")
            elif choice == '7':
                break
            else:
                print("❌ Неверный выбор")
    
    def show_premium_menu(self):
        """Меню премиум подписки"""
        while True:
            print("\n" + "💎" + "="*35 + "💎")
            print("       ПРЕМИУМ ПОДПИСКА")
            print("💎" + "="*35 + "💎")
            
            print("\n✨ Премиум включает:")
            print("   ✅ AI анализы без ограничений")
            print("   ✅ Безлимитные голосовые сообщения") 
            print("   ✅ Расширенная статистика")
            print("   ✅ Приоритет в очереди ИИ")
            
            print("\n💰 ВАРИАНТЫ ПОДПИСКИ:")
            print("1. 💎 1 месяц - 590₽")
            print("2. 💎 2 месяца - 999₽ 🔥 Выгода 181₽")
            print("3. 💎 3 месяца - 1299₽ 💎 Выгода 471₽")
            print("4. 🔙 Назад")
            
            choice = input("\n🎯 Выберите вариант: ").strip()
            
            options = {
                '1': 'premium_1_month',
                '2': 'premium_2_months',
                '3': 'premium_3_months'
            }
            
            if choice in options:
                payment_type = options[choice]
                amount = self.create_pending_payment(self.current_user_id, payment_type)
                
                if amount:
                    instructions = self.show_payment_instructions(payment_type, amount)
                    print(instructions)
                    input("📌 Нажмите Enter чтобы продолжить...")
            elif choice == '4':
                break
            else:
                print("❌ Неверный выбор")
    
    def show_gift_menu(self):
        """Меню подарков"""
        while True:
            print("\n" + "🎁" + "="*35 + "🎁")
            print("        ПОДАРИТЬ ПРЕМИУМ")
            print("🎁" + "="*35 + "🎁")
            
            print("\n💝 Подарочные коды:")
            print("1. 🎁 Премиум 1 месяц - 590₽")
            print("2. 🎁 Премиум 2 месяца - 999₽")
            print("3. 🎁 Премиум 3 месяца - 1299₽")
            print("4. 🎫 Активировать подарочный код")
            print("5. 🔙 Назад")
            
            choice = input("\n🎯 Выберите вариант: ").strip()
            
            options = {
                '1': 'gift_premium_1_month',
                '2': 'gift_premium_2_months', 
                '3': 'gift_premium_3_months'
            }
            
            if choice in options:
                payment_type = options[choice]
                amount = self.create_pending_payment(self.current_user_id, payment_type)
                
                if amount:
                    instructions = self.show_payment_instructions(payment_type, amount)
                    print(instructions)
                    input("📌 Нажмите Enter чтобы продолжить...")
            elif choice == '4':
                code = input("Введите подарочный код: ").strip()
                # Здесь будет активация кода
                print(f"🎁 Активация кода: {code}")
            elif choice == '5':
                break
            else:
                print("❌ Неверный выбор")
    
    def show_analysis_menu(self):
        """Меню AI анализов"""
        while True:
            print("\n" + "📊" + "="*35 + "📊")
            print("          AI АНАЛИЗЫ")
            print("📊" + "="*35 + "📊")
            
            print("\n🤖 AI анализ включает:")
            print("   📈 Детальная статистика прогресса")
            print("   💡 Персональные рекомендации")
            print("   🎯 Анализ техники выполнения")
            
            print("\n📦 ПАКЕТЫ АНАЛИЗОВ:")
            print("1. 📊 10 анализов - 79₽")
            print("2. 📊 30 анализов - 199₽ 🔥 Выгода 38₽")
            print("3. 📊 100 анализов - 699₽ 💎 Выгода 91₽")
            print("4. 🔙 Назад")
            
            choice = input("\n🎯 Выберите вариант: ").strip()
            
            options = {
                '1': 'analysis_10',
                '2': 'analysis_30',
                '3': 'analysis_100'
            }
            
            if choice in options:
                payment_type = options[choice]
                amount = self.create_pending_payment(self.current_user_id, payment_type)
                
                if amount:
                    instructions = self.show_payment_instructions(payment_type, amount)
                    print(instructions)
                    input("📌 Нажмите Enter чтобы продолжить...")
            elif choice == '4':
                break
            else:
                print("❌ Неверный выбор")
    
    def check_user_payments(self):
        """Проверяет платежи пользователя"""
        print("\n🔄 Проверяем платежи...")
        
        completed_payments = self.check_pending_payments(self.current_user_id)
        
        if completed_payments:
            print("✅ НОВЫЕ ОПЛАТЫ:")
            for payment in completed_payments:
                print(f"   💰 {payment['description']} - {payment['amount']}₽")
        else:
            print("📭 Новых оплат не найдено")
        
        input("\n📌 Нажмите Enter чтобы продолжить...")
    
    def run_demo(self):
        """Запускает демо"""
        print("=" * 50)
        print("🏋️ ДЕМО - GROMFIT DONATIONALERTS PAYMENTS")
        print("=" * 50)
        
        print(f"\n👋 Привет, пользователь {self.current_user_id}!")
        
        # Демонстрация обработки кода авторизации
        print("\n🔧 Демонстрация обработки кода авторизации...")
        test_code = "test_authorization_code"
        success, message = self.process_da_code(test_code)
        print(f"Результат: {message}")
        
        while True:
            print("\n🏠 ГЛАВНОЕ МЕНЮ")
            print("1. 🏋️ Тренировки")
            print("2. 💳 Магазин")
            print("3. 🚪 Выход")
            
            choice = input("\n🎯 Выберите действие: ").strip()
            
            if choice == '1':
                print("\n🤖 Раздел тренировок...")
            elif choice == '2':
                self.show_main_shop_menu()
            elif choice == '3':
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор")

if __name__ == "__main__":
    payment_system = GromFitDAPayments()
    payment_system.run_demo()