# -*- coding: utf-8 -*-
"""
Presale AI Service - 兼容模块

此模块用于向后兼容，将 app.services.presale.presale_ai_service 重新导出。
"""

from app.services.presale.presale_ai_service import PresaleAIService

__all__ = [
    "PresaleAIService",
]