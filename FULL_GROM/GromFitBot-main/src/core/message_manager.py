"""
Менеджер сообщений для управления отображением и заменой сообщений в GromFitBot
Полная версия с обработкой всех типов сообщений и клавиатур
"""

from typing import Optional, Union
from aiogram import Bot
from aiogram.types import (
    Message, 
    CallbackQuery,
    ReplyKeyboardMarkup, 
    InlineKeyboardMarkup,
    ForceReply,
    ReplyKeyboardRemove
)
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
import logging
import asyncio

logger = logging.getLogger(__name__)

class MessageManager:
    """Полный менеджер сообщений с обработкой всех сценариев"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def replace_message(
        self,
        message: Message,
        text: str,
        keyboard: Optional[Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, ForceReply, ReplyKeyboardRemove]] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        protect_content: bool = False
    ) -> Optional[Message]:
        """
        Полная замена текущего сообщения новым с меню
        
        Args:
            message: Исходное сообщение для замены
            text: Текст нового сообщения
            keyboard: Клавиатура (Reply или Inline)
            parse_mode: Режим парсинга (HTML/Markdown)
            disable_web_page_preview: Отключить превью ссылок
            protect_content: Защитить контент от пересылки
            
        Returns:
            Новое сообщение или None при ошибке
        """
        try:
            # Пытаемся удалить старое сообщение
            try:
                await message.delete()
            except TelegramBadRequest as e:
                if "message can't be deleted" not in str(e):
                    logger.warning(f"Не удалось удалить сообщение {message.message_id}: {e}")
            except Exception as e:
                logger.debug(f"Ошибка удаления сообщения: {e}")
            
            # Небольшая задержка для предотвращения конфликтов
            await asyncio.sleep(0.1)
            
            # Отправляем новое сообщение
            if keyboard:
                new_message = await message.answer(
                    text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    protect_content=protect_content
                )
            else:
                new_message = await message.answer(
                    text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    protect_content=protect_content
                )
            
            logger.debug(f"Сообщение заменено: {message.message_id} -> {new_message.message_id}")
            return new_message
            
        except TelegramAPIError as e:
            logger.error(f"Telegram API error при замене сообщения: {e}")
            return None
        except Exception as e:
            logger.error(f"Критическая ошибка при замене сообщения: {e}")
            return None
    
    async def edit_message_with_menu(
        self,
        callback_query: CallbackQuery,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Редактирование существующего сообщения с инлайн-клавиатурой
        
        Args:
            callback_query: Объект callback_query с сообщением
            text: Новый текст сообщения
            keyboard: Новая инлайн-клавиатура
            parse_mode: Режим парсинга текста
            disable_web_page_preview: Отключить превью ссылок
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            message = callback_query.message
            
            if keyboard:
                await message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview
                )
            else:
                await message.edit_text(
                    text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview
                )
            
            logger.debug(f"Сообщение отредактировано: {message.message_id}")
            return True
            
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                logger.debug(f"Сообщение не изменилось: {message.message_id}")
                return True
            else:
                logger.error(f"Ошибка редактирования сообщения {message.message_id}: {e}")
                # Пытаемся отправить новое сообщение как запасной вариант
                try:
                    await callback_query.message.answer(
                        text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=disable_web_page_preview
                    )
                    return True
                except Exception as fallback_error:
                    logger.error(f"Ошибка запасного варианта: {fallback_error}")
                    return False
        except Exception as e:
            logger.error(f"Критическая ошибка при редактировании сообщения: {e}")
            return False
    
    async def delete_message_safe(
        self,
        chat_id: int,
        message_id: int
    ) -> bool:
        """
        Безопасное удаление сообщения
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения
            
        Returns:
            True если удалено, False если ошибка
        """
        try:
            await self.bot.delete_message(chat_id, message_id)
            logger.debug(f"Сообщение удалено: {message_id}")
            return True
        except TelegramBadRequest as e:
            if "message to delete not found" in str(e) or "message can't be deleted" in str(e):
                logger.debug(f"Не удалось удалить сообщение {message_id}: {e}")
            else:
                logger.warning(f"Ошибка удаления сообщения {message_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Критическая ошибка при удалении сообщения: {e}")
            return False
    
    async def send_with_bottom_keyboard(
        self,
        message: Message,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> Optional[Message]:
        """
        Отправка сообщения с нижней клавиатурой (всегда видимой)
        
        Args:
            message: Сообщение для ответа
            text: Текст сообщения
            parse_mode: Режим парсинга текста
            disable_web_page_preview: Отключить превью ссылок
            
        Returns:
            Отправленное сообщение или None при ошибке
        """
        try:
            from modules.keyboards.main_keyboards import MainKeyboards
            
            bottom_keyboard = MainKeyboards.get_bottom_keyboard()
            
            new_message = await message.answer(
                text,
                reply_markup=bottom_keyboard,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            
            logger.debug(f"Сообщение с нижней клавиатурой отправлено: {new_message.message_id}")
            return new_message
            
        except Exception as e:
            logger.error(f"Ошибка отправки с нижней клавиатурой: {e}")
            return None
    
    async def send_temporary_message(
        self,
        message: Message,
        text: str,
        delete_after: int = 5,
        parse_mode: str = "HTML"
    ) -> Optional[Message]:
        """
        Отправка временного сообщения (удаляется через указанное время)
        
        Args:
            message: Сообщение для ответа
            text: Текст временного сообщения
            delete_after: Через сколько секунд удалить
            parse_mode: Режим парсинга текста
            
        Returns:
            Временное сообщение
        """
        try:
            temp_message = await message.answer(text, parse_mode=parse_mode)
            
            # Запланировать удаление
            if delete_after > 0:
                asyncio.create_task(self._delete_after(temp_message, delete_after))
            
            return temp_message
            
        except Exception as e:
            logger.error(f"Ошибка отправки временного сообщения: {e}")
            return None
    
    async def _delete_after(
        self,
        message: Message,
        seconds: int
    ) -> None:
        """Удаление сообщения через указанное время"""
        await asyncio.sleep(seconds)
        await self.delete_message_safe(message.chat.id, message.message_id)
    
    async def answer_callback_with_notification(
        self,
        callback_query: CallbackQuery,
        text: str = "",
        show_alert: bool = False
    ) -> None:
        """
        Ответ на callback_query с обработкой ошибок
        
        Args:
            callback_query: Объект callback_query
            text: Текст уведомления
            show_alert: Показывать как alert (модальное окно)
        """
        try:
            await callback_query.answer(text, show_alert=show_alert)
        except TelegramBadRequest as e:
            if "query is too old" in str(e) or "query_id_invalid" in str(e):
                logger.debug(f"Callback query устарел: {callback_query.id}")
            else:
                logger.warning(f"Ошибка ответа на callback query: {e}")
        except Exception as e:
            logger.error(f"Критическая ошибка при ответе на callback: {e}")
    
    async def safe_edit_or_resend(
        self,
        callback_query: CallbackQuery,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Безопасное редактирование или повторная отправка сообщения
        
        Args:
            callback_query: Объект callback_query
            text: Текст сообщения
            keyboard: Клавиатура
            parse_mode: Режим парсинга
            
        Returns:
            True если успешно
        """
        # Сначала пробуем отредактировать
        success = await self.edit_message_with_menu(callback_query, text, keyboard, parse_mode)
        
        if not success:
            # Если не удалось отредактировать, удаляем старое и отправляем новое
            try:
                await callback_query.message.delete()
                if keyboard:
                    await callback_query.message.answer(text, reply_markup=keyboard, parse_mode=parse_mode)
                else:
                    await callback_query.message.answer(text, parse_mode=parse_mode)
                return True
            except Exception as e:
                logger.error(f"Ошибка при повторной отправке сообщения: {e}")
                return False
        
        return success
    
    async def create_menu_flow(
        self,
        message: Message,
        menus: list,
        current_index: int = 0
    ) -> None:
        """
        Создание потока меню с навигацией
        
        Args:
            message: Начальное сообщение
            menus: Список меню [{"text": "", "keyboard": keyboard}, ...]
            current_index: Текущий индекс меню
        """
        if not menus or current_index >= len(menus):
            return
        
        menu = menus[current_index]
        await self.replace_message(message, menu["text"], menu.get("keyboard"))