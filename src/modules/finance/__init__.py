"""
Модуль финансовой системы
"""

from .handlers import router
from .token_system import token_system
from .diamond_system import diamond_system

__all__ = ["router", "token_system", "diamond_system"]