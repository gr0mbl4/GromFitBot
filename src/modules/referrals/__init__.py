"""
Модуль реферальной системы
"""

from .handlers import router
from .system import referral_system

__all__ = ["router", "referral_system"]