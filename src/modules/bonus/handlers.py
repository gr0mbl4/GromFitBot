"""
Модуль для ежедневных бонусов
"""

import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from src.core.database import db
from src.modules.keyboards.main_keyboards import MainKeyboards

router = Router()
logger = logging.getLogger(__name__)

class DailyBonusSystem:
    """Система ежедневных бонусов"""
    
    BONUS_AMOUNT = 10  # Количество токенов за ежедневный бонус
    
    @staticmethod
    def can_claim_bonus(last_claim_time: str) -> bool:
        """Проверяет, может ли пользователь получить бонус"""
        if not last_claim_time:
            return True
            
        try:
            # Преобразуем строку в datetime
            last_claim = datetime.strptime(last_claim_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            # Проверяем, прошло ли более 24 часов или наступило время сброса (3:00 по МСК)
            if now.hour >= 3:  # 03:00 по МСК
                # Если сейчас после 3:00, проверяем, было ли последнее получение до 3:00 сегодня
                today_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)
                if now >= today_3am:
                    return last_claim < today_3am
            else:
                # Если сейчас до 3:00, проверяем, было ли последнее получение до 3:00 вчера
                yesterday_3am = (now - timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
                return last_claim < yesterday_3am
                
        except Exception as e:
            logger.error(f"Ошибка проверки бонуса: {e}")
            return True
        
        return True
    
    @staticmethod
    def get_next_bonus_time(last_claim_time: str) -> str:
        """Получаем время следующего доступного бонуса"""
        now = datetime.now()
        
        if now.hour >= 3:
            # Следующий бонус будет доступен в 3:00 следующего дня
            next_bonus = (now + timedelta(days=1)).replace(
                hour=3, 
                minute=0, 
                second=0, 
                microsecond=0
            )
        else:
            # Следующий бонус будет доступен в 3:00 сегодня
            next_bonus = now.replace(
                hour=3, 
                minute=0, 
                second=0, 
                microsecond=0
            )
        
        return next_bonus.strftime("%H:%M")
    
    @staticmethod
    def get_time_until_next_bonus(last_claim_time: str) -> str:
        """Получаем время до следующего бонуса в читаемом формате"""
        now = datetime.now()
        
        if now.hour >= 3:
            next_bonus = (now + timedelta(days=1)).replace(
                hour=3, minute=0, second=0, microsecond=0
            )
        else:
            next_bonus = now.replace(hour=3, minute=0, second=0, microsecond=0)
        
        time_left = next_bonus - now
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        
        return f"{hours}ч {minutes}м"

@router.message(Command("bonus"))
async def cmd_daily_bonus(message: Message):
    """Обработчик команды /bonus"""
    telegram_id = message.from_user.id
    
    user = db.get_user(telegram_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь с помощью /start")
        return
    
    last_claim_time = user.get('last_bonus_claim')
    
    if DailyBonusSystem.can_claim_bonus(last_claim_time):
        try:
            # Получаем текущий баланс
            current_balance = db.get_balance(telegram_id)
            
            # Начисляем бонус
            db.add_tokens(
                telegram_id=telegram_id,
                amount=DailyBonusSystem.BONUS_AMOUNT,
                transaction_type="daily_bonus",
                description="Ежедневный бонус"
            )
            
            # Обновляем время последнего получения бонуса
            db.execute(
                "UPDATE users SET last_bonus_claim = datetime('now') WHERE telegram_id = ?",
                (telegram_id,)
            )
            db.commit()
            
            # Получаем обновленный баланс
            new_balance = current_balance + DailyBonusSystem.BONUS_AMOUNT
            
            await message.answer(
                f"🎉 <b>Ежедневный бонус получен!</b>\n\n"
                f"💰 +{DailyBonusSystem.BONUS_AMOUNT} токенов\n"
                f"💳 Ваш баланс: {new_balance:.0f} токенов\n\n"
                f"⏰ Следующий бонус будет доступен в 03:00 по МСК",
                reply_markup=MainKeyboards.get_bottom_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при начислении бонуса: {e}")
            await message.answer(
                "❌ Ошибка при начислении бонуса. Попробуйте позже.",
                reply_markup=MainKeyboards.get_bottom_keyboard()
            )
    else:
        time_until = DailyBonusSystem.get_time_until_next_bonus(last_claim_time)
        await message.answer(
            f"⏳ <b>Бонус уже получен сегодня</b>\n\n"
            f"Следующий ежедневный бонус будет доступен через {time_until} (в 03:00 по МСК)",
            reply_markup=MainKeyboards.get_bottom_keyboard()
        )

@router.message(F.text == "🎁 ЕЖЕДНЕВНЫЙ БОНУС")
async def handle_daily_bonus_button(message: Message):
    """Обработчик кнопки ежедневного бонуса в главном меню"""
    await cmd_daily_bonus(message)