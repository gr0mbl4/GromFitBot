import sqlite3
import json
import random
import string
from datetime import datetime, timedelta

class GromFitWithReferrals:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.setup_database()
        self.current_user_id = None
        print("🏋️ GromFit с Реферальной Системой")
        print("✅ Система готова к работе\n")
    
    def setup_database(self):
        """Создаем базу данных"""
        cursor = self.conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE users (
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
                registration_step TEXT DEFAULT 'start',
                da_payment_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица реферальных кодов (для проверки существующих)
        cursor.execute('''
            CREATE TABLE referral_codes (
                id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_count INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица реферальных начислений
        cursor.execute('''
            CREATE TABLE referral_bonuses (
                id INTEGER PRIMARY KEY,
                referrer_id INTEGER,
                referred_user_id INTEGER,
                bonus_type TEXT,
                bonus_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def generate_referral_code(self, length=16):
        """Генерирует уникальный реферальный код длиной 16 символов"""
        while True:
            # Используем буквы и цифры
            characters = string.ascii_uppercase + string.digits
            code = ''.join(random.choice(characters) for _ in range(length))
            
            # Проверяем уникальность
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM referral_codes WHERE code = ?', (code,))
            if not cursor.fetchone():
                return code
    
    def register_referral_code(self, user_id, code):
        """Регистрирует реферальный код для пользователя"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO referral_codes (code, user_id) VALUES (?, ?)',
                (code, user_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def check_referral_code(self, code):
        """Проверяет существование реферального кода"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.id, u.name 
            FROM referral_codes rc 
            JOIN users u ON rc.user_id = u.id 
            WHERE rc.code = ?
        ''', (code,))
        result = cursor.fetchone()
        return result if result else None
    
    def apply_referral_bonus(self, referrer_id, referred_user_id):
        """Начисляет бонусы за реферала"""
        cursor = self.conn.cursor()
        
        # Бонус для пригласившего: 3 дня премиума
        cursor.execute('''
            INSERT INTO referral_bonuses (referrer_id, referred_user_id, bonus_type, bonus_days)
            VALUES (?, ?, 'premium', 3)
        ''', (referrer_id, referred_user_id))
        
        # Бонус для приглашенного: 7 дней премиума за 10 руб (пробный период)
        cursor.execute('''
            INSERT INTO referral_bonuses (referrer_id, referred_user_id, bonus_type, bonus_days)
            VALUES (?, ?, 'trial_premium', 7)
        ''', (referrer_id, referred_user_id))
        
        # Обновляем счетчик использования кода
        cursor.execute('''
            UPDATE referral_codes SET used_count = used_count + 1 
            WHERE user_id = ?
        ''', (referrer_id,))
        
        self.conn.commit()
        
        print(f"🎁 Начислены бонусы:")
        print(f"   👤 Пригласившему: 3 дня премиума")
        print(f"   👥 Приглашенному: 7 дней премиума (пробный период)")
    
    def simulate_telegram_start(self, user_id, username, first_name, last_name):
        """Имитируем команду /start в Telegram"""
        print(f"👤 Пользователь: {first_name} {last_name} (@{username})")
        print(f"🆔 ID: {user_id}")
        print("➡️ Отправляет: /start\n")
        
        cursor = self.conn.cursor()
        
        # Проверяем есть ли пользователь
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            # Новый пользователь
            da_link = f"https://www.donationalerts.com/r/gromfit_{user_id}"
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name, registration_step, da_payment_link)
                VALUES (?, ?, ?, ?, 'name', ?)
            ''', (user_id, username, first_name, last_name, da_link))
            self.conn.commit()
            
            print("🤖 Бот: Добро пожаловать в GromFit!")
            print("🤖 Бот: Давай познакомимся! Как мне к тебе обращаться?")
            self.current_user_id = user_id
            return "waiting_for_name"
        
        else:
            # Пользователь уже есть
            registration_step = user[11]  # registration_step
            if registration_step != 'completed':
                if registration_step == 'name':
                    print("🤖 Бот: Как мне к тебе обращаться?")
                    return "waiting_for_name"
                elif registration_step == 'region':
                    print("🤖 Бот: Выбери свой регион:")
                    self.show_regions()
                    return "waiting_for_region"
                elif registration_step == 'referral':
                    print("🤖 Бот: Есть реферальный код? (если нет - напиши 'нет')")
                    return "waiting_for_referral"
            else:
                user_name = user[5]  # name
                print(f"🤖 Бот: С возвращением, {user_name}! 👋")
                print("🤖 Бот: Готов к новой тренировке?")
                self.show_main_menu()
                return "main_menu"
    
    def process_name(self, name):
        """Обрабатываем ввод имени"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET name = ?, registration_step = ? WHERE telegram_id = ?',
            (name, 'region', self.current_user_id)
        )
        self.conn.commit()
        
        print(f"🤖 Бот: Приятно познакомиться, {name}! 👋")
        print("🤖 Бот: Теперь выбери свой регион:")
        self.show_regions()
        return "waiting_for_region"
    
    def show_regions(self):
        """Показываем список регионов"""
        regions = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Другой регион"]
        for i, region in enumerate(regions, 1):
            print(f"   {i}. {region}")
    
    def process_region(self, region_input):
        """Обрабатываем выбор региона"""
        regions = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Другой регион"]
        
        try:
            if region_input.isdigit():
                region_index = int(region_input) - 1
                if 0 <= region_index < len(regions):
                    region = regions[region_index]
                else:
                    return "invalid_region"
            else:
                region = region_input
        except:
            region = region_input
        
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE users SET region = ?, registration_step = ? WHERE telegram_id = ?',
            (region, 'referral', self.current_user_id)
        )
        self.conn.commit()
        
        print(f"🤖 Бот: Отлично! 🎯 Регион: {region}")
        print("🤖 Бот: Есть реферальный код? Его тебе мог дать друг.")
        print("🤖 Бот: Если кода нет - просто напиши 'нет'")
        return "waiting_for_referral"
    
    def process_referral(self, referral_input):
        """Обрабатываем реферальный код"""
        cursor = self.conn.cursor()
        
        referrer_id = None
        referral_code = None
        
        if referral_input.lower() != 'нет':
            # Проверяем существование кода
            referrer_info = self.check_referral_code(referral_input.upper())
            if referrer_info:
                referrer_id = referrer_info[0]
                referrer_name = referrer_info[1]
                referral_code = referral_input.upper()
                print(f"✅ Найден реферальный код! Пригласил: {referrer_name}")
            else:
                print("❌ Реферальный код не найден. Регистрация продолжится без бонусов.")
        
        # Генерируем уникальный реферальный код для нового пользователя
        user_referral_code = self.generate_referral_code(16)
        
        # Завершаем регистрацию
        cursor.execute(
            'UPDATE users SET referral_code = ?, referrer_id = ?, registration_step = ? WHERE telegram_id = ?',
            (user_referral_code, referrer_id, 'completed', self.current_user_id)
        )
        
        # Регистрируем реферальный код пользователя в базе
        self.register_referral_code(self.current_user_id, user_referral_code)
        
        self.conn.commit()
        
        # Если был реферальный код - начисляем бонусы
        if referrer_id:
            self.apply_referral_bonus(referrer_id, self.current_user_id)
        
        # Получаем данные пользователя
        cursor.execute('SELECT name, region, da_payment_link FROM users WHERE telegram_id = ?', (self.current_user_id,))
        user = cursor.fetchone()
        
        print(f"\n🎉 Регистрация завершена, {user[0]}!")
        print(f"📍 Регион: {user[1]}")
        print(f"🎯 Твой реферальный код: {user_referral_code}")
        print(f"💳 Ссылка для платежей: {user[2]}")
        print("\n🤖 Бот: Теперь ты можешь:")
        print("   • Загружать тренировки")
        print("   • Отслеживать прогресс") 
        print("   • Получать достижения")
        print("   • Приглашать друзей")
        print("\n🏋️ Начни с загрузки первой тренировки!")
        
        self.show_main_menu()
        return "main_menu"
    
    def show_referral_stats(self):
        """Показывает статистику рефералов"""
        cursor = self.conn.cursor()
        
        # Считаем рефералов
        cursor.execute('''
            SELECT COUNT(*) FROM users WHERE referrer_id = ?
        ''', (self.current_user_id,))
        total_referrals = cursor.fetchone()[0]
        
        # Считаем бонусы
        cursor.execute('''
            SELECT SUM(bonus_days) FROM referral_bonuses 
            WHERE referrer_id = ? AND bonus_type = 'premium'
        ''', (self.current_user_id,))
        total_bonus_days = cursor.fetchone()[0] or 0
        
        print(f"\n👥 РЕФЕРАЛЬНАЯ СИСТЕМА:")
        print(f"   Приглашено рефералов: {total_referrals}")
        print(f"   Заработано дней премиума: {total_bonus_days}")
        
        # Получаем реферальный код пользователя
        cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (self.current_user_id,))
        user_code = cursor.fetchone()[0]
        
        print(f"   Твой реферальный код: {user_code}")
        print(f"   Твоя реферальная ссылка: https://t.me/GromFitBot?start={user_code}")
        print("\n💎 За каждого приведенного друга:")
        print("   • Ты получаешь 3 дня премиума")
        print("   • Друг получает 7 дней премиума за 10 руб")
    
    def show_main_menu(self):
        """Показываем главное меню"""
        print("\n📱 ГЛАВНОЕ МЕНЮ:")
        print("1. 🏋️ Загрузить тренировку")
        print("2. 📊 Мои упражнения")
        print("3. 🏆 Достижения") 
        print("4. 👤 Профиль")
        print("5. 📈 Аналитика")
        print("6. 👥 Реферальная система")
        print("7. 🚪 Выход")
    
    def show_profile(self):
        """Показываем профиль пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT name, region, referral_code, premium, created_at, referrer_id 
            FROM users WHERE telegram_id = ?
        ''', (self.current_user_id,))
        user = cursor.fetchone()
        
        print(f"\n👤 ПРОФИЛЬ:")
        print(f"   Имя: {user[0]}")
        print(f"   Регион: {user[1]}")
        print(f"   Реф. код: {user[2]}")
        print(f"   Премиум: {'✅' if user[3] else '❌'}")
        print(f"   Регистрация: {user[4]}")
        
        if user[5]:  # referrer_id
            cursor.execute('SELECT name FROM users WHERE id = ?', (user[5],))
            referrer = cursor.fetchone()
            if referrer:
                print(f"   Пригласил: {referrer[0]}")
    
    def run_demo(self):
        """Запускаем демо-режим"""
        print("=" * 50)
        print("🎮 ДЕМО РЕФЕРАЛЬНОЙ СИСТЕМЫ GromFit")
        print("=" * 50)
        
        # Сначала создадим тестового пользователя с реферальным кодом
        print("\n🔧 Создаем тестового пользователя с реферальным кодом...")
        test_user_id = 111111111
        test_code = self.generate_referral_code(16)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, name, region, referral_code, registration_step)
            VALUES (?, 'test_referrer', 'Алексей', 'Алексей', 'Москва', ?, 'completed')
        ''', (test_user_id, test_code))
        self.register_referral_code(test_user_id, test_code)
        self.conn.commit()
        
        print(f"👤 Создан пользователь: Алексей")
        print(f"🎯 Его реферальный код: {test_code}")
        
        # Имитируем нового пользователя
        state = self.simulate_telegram_start(
            user_id=123456789,
            username="new_user",
            first_name="Олег",
            last_name="Иванов"
        )
        
        while True:
            if state == "waiting_for_name":
                name = input("\nВведите ваше имя: ").strip()
                if name:
                    state = self.process_name(name)
                else:
                    print("❌ Имя не может быть пустым")
                    
            elif state == "waiting_for_region":
                region = input("\nВыберите регион (1-6 или введите название): ").strip()
                state = self.process_region(region)
                if state == "invalid_region":
                    print("❌ Неверный выбор региона")
                    state = "waiting_for_region"
                    
            elif state == "waiting_for_referral":
                print(f"\n💡 Подсказка: тестовый код - {test_code}")
                referral = input("Введите реферальный код или 'нет': ").strip()
                state = self.process_referral(referral)
                
            elif state == "main_menu":
                choice = input("\nВыберите действие (1-7): ").strip()
                
                if choice == '1':
                    print("\n🤖 Бот: Загрузите тренировку в формате:")
                    print("   1. Жим лежа 3x10 50кг")
                    print("   2. Приседания 4x12 60кг")
                elif choice == '2':
                    print("\n🤖 Бот: Здесь будут ваши упражнения")
                elif choice == '3':
                    print("\n🤖 Бот: Система достижений - 50 достижений")
                elif choice == '4':
                    self.show_profile()
                elif choice == '5':
                    print("\n🤖 Бот: Аналитика тренировок")
                elif choice == '6':
                    self.show_referral_stats()
                elif choice == '7':
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неверный выбор")

if __name__ == "__main__":
    demo = GromFitWithReferrals()
    demo.run_demo()