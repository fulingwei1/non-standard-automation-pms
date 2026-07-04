# -*- coding: utf-8 -*-
"""
OTD（Order-to-Delivery）项目交付智能体

定位：编排层，不是新器官。把现有的分散能力（交付风险/ECN影响/回款风险/质量风险/
关闭就绪/超预算）串成每日一份的 OTD 全景扫描 + 7 核心指标。

- otd_scan_service.py：10 维风险检测 + 批量扫描 + 可选 AI 归因 + 预警产出推送
- otd_metrics_service.py：7 核心指标聚合（准时交付率/延期天数/返工/变更/毛利/验收周期/投诉率）

设计原则：
1. 零新增表、零 migration、零前端改动
2. 复用 ProjectRiskService / BudgetAlertService / ClosureReadinessService / ProfitAnalysisService
3. 复用 AlertRecord + NotificationDispatcher 走站内 + 邮件推送
4. AI 归因可选，失败不影响主流程
"""

from .otd_metrics_service import OTDMetricsService
from .otd_scan_service import OTDScanService
from . import threshold_service, trend_service

__all__ = [
    "OTDScanService",
    "OTDMetricsService",
    "threshold_service",
    "trend_service",
]
