# -*- coding: utf-8 -*-
"""
Presale AI Service - 兼容模块

此模块用于向后兼容，将 app.services.presale.presale_ai_service 重新导出。
同时同步兼容测试中常见的模块级 patch 目标。
"""

from app.services.presale import presale_ai_service as _impl

AIClientService = _impl.AIClientService
PresaleAISolution = _impl.PresaleAISolution
PresaleSolutionTemplate = _impl.PresaleSolutionTemplate
save_obj = _impl.save_obj


class PresaleAIService(_impl.PresaleAIService):
    """兼容包装，确保兼容模块级 patch 会同步到真实实现模块。"""

    def __init__(self, *args, **kwargs):
        original_client_service = _impl.AIClientService
        _impl.AIClientService = AIClientService
        try:
            super().__init__(*args, **kwargs)
        finally:
            _impl.AIClientService = original_client_service

    def generate_solution(self, *args, **kwargs):
        original_save_obj = _impl.save_obj
        _impl.save_obj = save_obj
        try:
            return super().generate_solution(*args, **kwargs)
        finally:
            _impl.save_obj = original_save_obj


__all__ = [
    "AIClientService",
    "PresaleAIService",
    "PresaleAISolution",
    "PresaleSolutionTemplate",
    "save_obj",
]
