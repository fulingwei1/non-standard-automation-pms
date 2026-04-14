# -*- coding: utf-8 -*-
"""
成本预测服务 - 重新导出模块

此模块重新导出 cost 子目录中的成本预测服务，
用于向后兼容，并同步常见模块级 patch 目标。
"""

from app.services.cost import cost_prediction_service as _impl

EVMCalculator = _impl.EVMCalculator
GLM5CostPredictor = _impl.GLM5CostPredictor
requests = _impl.requests
save_obj = _impl.save_obj


class CostPredictionService(_impl.CostPredictionService):
    """兼容包装，确保兼容模块级 patch 会同步到真实实现模块。"""

    def __init__(self, *args, **kwargs):
        original_predictor = _impl.GLM5CostPredictor
        _impl.GLM5CostPredictor = GLM5CostPredictor
        try:
            super().__init__(*args, **kwargs)
        finally:
            _impl.GLM5CostPredictor = original_predictor


__all__ = [
    "CostPredictionService",
    "EVMCalculator",
    "GLM5CostPredictor",
    "requests",
    "save_obj",
]
