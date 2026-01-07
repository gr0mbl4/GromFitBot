from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

from core.database import db

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "🏋️‍♂️ Добавить тренировку")
@router.message(Command("add_workout"))
async def add_workout(message: Message):
    """Добавить тренировку"""
    
    workout_text = """
🏋️‍♂️ **ДОБАВЛЕНИЕ ТРЕНИРОВКИ**

📝 **Формат:**
упражнение вес подходы повторения

💡 **Примеры:**
`жим лежа 80 3 10`
`приседания 100 4 8`
`подтягивания 0 3 15`
`бег 0 1 30` (30 минут)

📊 **Или используй подробный формат:**
`упражнение:жим лежа,вес:80,подходы:3,повторения:10,заметки:хорошая тренировка`

👇 **Отправь свою тренировку в чат:**
    """
    
    await message.answer(workout_text)

@router.message(F.text.regexp(r'^[а-яА-Яa-zA-Z\s]+\s+\d+\s+\d+\s+\d+$'))
async def handle_simple_workout(message: Message):
    """Обработка простого формата тренировки"""
    try:
        parts = message.text.split()
        exercise = ' '.join(parts[:-3])
        weight = float(parts[-3])
        sets = int(parts[-2])
        reps = int(parts[-1])
        
        # Получаем ID пользователя
        user = db.fetch_one(
            "SELECT id FROM users WHERE telegram_id = ?",
            (message.from_user.id,)
        )
        
        if user:
            db.execute('''
                INSERT INTO workouts (user_id, exercise, weight, sets, reps)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['id'], exercise, weight, sets, reps))
            
            volume = weight * sets * reps
            
            await message.answer(
                f"✅ **Тренировка сохранена!**\n\n"
                f"🏋️‍♂️ **Упражнение:** {exercise}\n"
                f"⚖️ **Вес:** {weight} кг\n"
                f"🔄 **Подходы/повторения:** {sets}x{reps}\n"
                f"📦 **Объем:** {volume:,.0f} кг\n\n"
                f"💪 Так держать!",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Сначала зарегистрируйтесь через /start")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка формата: {e}")

@router.message(F.text == "📊 Статистика")
@router.message(Command("stats"))
async def show_stats(message: Message):
    """Показать статистику тренировок"""
    
    user = db.fetch_one(
        "SELECT id FROM users WHERE telegram_id = ?",
        (message.from_user.id,)
    )
    
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start")
        return
    
    db_user_id = user['id']
    
    # Получаем общую статистику
    total_stats = db.fetch_one('''
        SELECT 
            COUNT(*) as total_workouts,
            SUM(weight * sets * reps) as total_volume,
            SUM(duration) as total_duration,
            COUNT(DISTINCT exercise) as exercises_count
        FROM workouts 
        WHERE user_id = ?
    ''', (db_user_id,))
    
    # Получаем топ упражнений
    top_exercises = db.fetch_all('''
        SELECT 
            exercise,
            COUNT(*) as workouts_count,
            SUM(weight * sets * reps) as total_volume,
            MAX(weight) as max_weight
        FROM workouts 
        WHERE user_id = ?
        GROUP BY exercise
        ORDER BY total_volume DESC
        LIMIT 5
    ''', (db_user_id,))
    
    if not total_stats['total_workouts']:
        await message.answer("📭 У вас пока нет тренировок. Добавьте первую!")
        return
    
    # Формируем текст статистики
    stats_text = f"""
📊 **ВАША СТАТИСТИКА**

📈 **ОБЩАЯ:**
🏋️‍♂️ **Тренировок:** {total_stats['total_workouts'] or 0}
📦 **Общий объем:** {total_stats['total_volume'] or 0:,.0f} кг
⏱️ **Время тренировок:** {total_stats['total_duration'] or 0 // 60} мин
💪 **Упражнений:** {total_stats['exercises_count'] or 0}

🏆 **ТОП-5 УПРАЖНЕНИЙ:**
"""
    
    for i, ex in enumerate(top_exercises, 1):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
        stats_text += f"\n{medal} **{ex['exercise']}**\n"
        stats_text += f"   🏋️‍♂️ {ex['workouts_count']} тренировок\n"
        stats_text += f"   📦 {ex['total_volume'] or 0:,.0f} кг объем\n"
        if ex['max_weight']:
            stats_text += f"   ⚖️ Макс. вес: {ex['max_weight']} кг\n"
    
    stats_text += "\n💪 **Продолжай в том же духе!**"
    
    await message.answer(stats_text, parse_mode="Markdown")

@router.message(F.text == "📈 График")
@router.message(Command("graph"))
async def show_graph(message: Message):
    """Показать график прогресса"""
    
    user = db.fetch_one(
        "SELECT id FROM users WHERE telegram_id = ?",
        (message.from_user.id,)
    )
    
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start")
        return
    
    db_user_id = user['id']
    
    # Получаем данные для графика
    workouts_data = db.fetch_all('''
        SELECT 
            DATE(workout_date) as date,
            SUM(weight * sets * reps) as daily_volume
        FROM workouts 
        WHERE user_id = ? 
        AND workout_date >= DATE('now', '-30 days')
        GROUP BY DATE(workout_date)
        ORDER BY date
    ''', (db_user_id,))
    
    if not workouts_data or len(workouts_data) < 2:
        await message.answer(
            "📭 Недостаточно данных для построения графика.\n"
            "Добавьте несколько тренировок за последние 30 дней."
        )
        return
    
    # Подготавливаем данные
    dates = [datetime.strptime(w['date'], '%Y-%m-%d') for w in workouts_data]
    volumes = [w['daily_volume'] or 0 for w in workouts_data]
    
    # Создаем график
    plt.figure(figsize=(10, 6))
    plt.plot(dates, volumes, 'o-', linewidth=2, markersize=8, color='#4CAF50')
    plt.fill_between(dates, volumes, alpha=0.3, color='#4CAF50')
    
    plt.title('📈 ПРОГРЕСС ТРЕНИРОВОК (30 ДНЕЙ)', fontsize=16, fontweight='bold')
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Объем (кг)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Отправляем график
    from aiogram.types import InputFile
    
    caption = f"""
📈 **ВАШ ПРОГРЕСС**

📅 **Период:** последние 30 дней
📊 **Тренировок:** {len(workouts_data)}
📦 **Средний объем:** {sum(volumes)/len(volumes):,.0f} кг/день
📈 **Максимальный объем:** {max(volumes):,.0f} кг

💪 **Так держать! Продолжай прогрессировать!**
"""
    
    await message.answer_photo(
        InputFile(buf, filename="progress_graph.png"),
        caption=caption
    )

@router.message(Command("leaderboard"))
async def show_leaderboard(message: Message):
    """Таблица лидеров"""
    
    leaders = db.fetch_all('''
        SELECT 
            u.full_name,
            u.username,
            COUNT(w.id) as workouts_count,
            SUM(w.weight * w.sets * w.reps) as total_volume,
            ROUND(AVG(w.weight), 1) as avg_weight
        FROM users u
        LEFT JOIN workouts w ON u.id = w.user_id
        WHERE u.is_active = 1
        GROUP BY u.id
        HAVING workouts_count > 0
        ORDER BY total_volume DESC
        LIMIT 10
    ''')
    
    if not leaders:
        await message.answer("🏆 Таблица лидеров пуста. Будьте первым!")
        return
    
    leaderboard_text = "🏆 **ТАБЛИЦА ЛИДЕРОВ**\n\n"
    
    for i, leader in enumerate(leaders, 1):
        name = leader['username'] or leader['full_name']
        workouts = leader['workouts_count'] or 0
        volume = leader['total_volume'] or 0
        avg_weight = leader['avg_weight'] or 0
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        medal = medals[i-1] if i <= len(medals) else f"{i}."
        
        leaderboard_text += f"{medal} **{name}**\n"
        leaderboard_text += f"   🏋️‍♂️ {workouts} тренировок\n"
        leaderboard_text += f"   📦 {volume:,.0f} кг объем\n"
        leaderboard_text += f"   ⚖️ Ср. вес: {avg_weight} кг\n\n"
    
    leaderboard_text += "💪 **Присоединяйся к лидерам!**"
    
    await message.answer(leaderboard_text, parse_mode="Markdown")

# Экспортируем роутер
__all__ = ['router']