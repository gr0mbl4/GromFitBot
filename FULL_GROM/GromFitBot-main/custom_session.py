import aiohttp
from aiogram.client.session.aiohttp import AiohttpSession
import ssl

class CustomAiohttpSession(AiohttpSession):
    def __init__(self, proxy_url=None):
        super().__init__()
        self.proxy_url = proxy_url
        
    def _create_session(self) -> aiohttp.ClientSession:
        if self.proxy_url:
            # Создаем SSL контекст без проверки
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Создаем connector с прокси и кастомным SSL
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            return aiohttp.ClientSession(
                connector=connector,
                trust_env=True  # Используем системные настройки прокси
            )
        return super()._create_session()