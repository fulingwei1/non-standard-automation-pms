# -*- coding: utf-8 -*-
"""
中标率预测服务模块

聚合所有中标率预测相关的服务，保持向后兼容
"""
from .analysis import (
    get_win_rate_distribution,
    validate_model_accuracy,
)
from .base import WinRatePredictionService as OldWinRatePredictionService
from .service import WinRatePredictionService
from .ai_service import AIWinRatePredictionService
from .factors import (
    calculate_amount_factor,
    calculate_base_score,
    calculate_competitor_factor,
    calculate_customer_factor,
    calculate_product_factor,
    calculate_salesperson_factor,
)
from .history import (
    get_customer_cooperation_history,
    get_salesperson_historical_win_rate,
    get_similar_leads_statistics,
)
from .prediction import (
    batch_predict,
    predict,
)

__all__ = ["WinRatePredictionService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    WinRatePredictionService.get_salesperson_historical_win_rate = lambda self, salesperson_id, lookback_months=24: get_salesperson_historical_win_rate(self, salesperson_id, lookback_months)
    WinRatePredictionService.get_customer_cooperation_history = lambda self, customer_id=None, customer_name=None: get_customer_cooperation_history(self, customer_id, customer_name)
    WinRatePredictionService.get_similar_leads_statistics = lambda self, dimension_scores, score_tolerance=10: get_similar_leads_statistics(self, dimension_scores, score_tolerance)
    WinRatePredictionService.calculate_base_score = lambda self, dimension_scores: calculate_base_score(self, dimension_scores)
    WinRatePredictionService.calculate_salesperson_factor = lambda self, historical_win_rate: calculate_salesperson_factor(historical_win_rate)
    WinRatePredictionService.calculate_customer_factor = lambda self, cooperation_count, success_count, is_repeat_customer=False: calculate_customer_factor(cooperation_count, success_count, is_repeat_customer)
    WinRatePredictionService.calculate_competitor_factor = lambda self, competitor_count: calculate_competitor_factor(competitor_count)
    WinRatePredictionService.calculate_amount_factor = lambda self, estimated_amount: calculate_amount_factor(estimated_amount)
    WinRatePredictionService.calculate_product_factor = lambda self, product_match_type: calculate_product_factor(product_match_type)
    WinRatePredictionService.predict = lambda self, dimension_scores, salesperson_id, customer_id=None, customer_name=None, estimated_amount=None, competitor_count=3, is_repeat_customer=False, product_match_type=None: predict(self, dimension_scores, salesperson_id, customer_id, customer_name, estimated_amount, competitor_count, is_repeat_customer, product_match_type)
    WinRatePredictionService.batch_predict = lambda self, leads: batch_predict(self, leads)
    WinRatePredictionService.get_win_rate_distribution = lambda self, start_date=None, end_date=None: get_win_rate_distribution(self, start_date, end_date)
    WinRatePredictionService.validate_model_accuracy = lambda self, lookback_months=12: validate_model_accuracy(self, lookback_months)

_patch_methods()
