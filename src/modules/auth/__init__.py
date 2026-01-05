"""
Модуль авторизации и регистрации
"""

from .registration import router
from .keyboards import AuthKeyboards, MainKeyboards

__all__ = ["router", "AuthKeyboards", "MainKeyboards"]