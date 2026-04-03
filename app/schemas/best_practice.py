# -*- coding: utf-8 -*-
"""
行业最佳实践 P0 级优化功能 Schema

包含：
- ABC 物料自动分级
- 供应商动态升降级
- 缺料自动升级通知
- 齐套率阶段目标配置
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== ABC 物料自动分级 ====================


class ABCClassificationConfig(BaseModel):
    """ABC 分级配置（可自定义阈值）"""

    a_threshold: Decimal = Field(
        default=Decimal("1000000"),
        description="A 类年消耗金额阈值（默认 100 万）",
    )
    b_threshold: Decimal = Field(
        default=Decimal("100000"),
        description="B 类年消耗金额阈值（默认 10 万）",
    )
    long_lead_time_days: int = Field(
        default=60,
        description="长采购周期阈值（天），超过自动归 A 类",
    )
    single_source_auto_a: bool = Field(
        default=True,
        description="单一来源供应商自动归 A 类",
    )


class ABCClassificationRequest(BaseModel):
    """ABC 分级请求"""

    config: ABCClassificationConfig = Field(
        default_factory=ABCClassificationConfig,
        description="分级配置（可选，不传则使用默认阈值）",
    )
    material_ids: Optional[List[int]] = Field(
        default=None,
        description="指定物料 ID 列表（不传则对全部活跃物料分级）",
    )


class ABCMaterialResult(BaseModel):
    """单条物料 ABC 分级结果"""

    material_id: int
    material_code: str
    material_name: str
    annual_consumption: Decimal = Field(description="年消耗金额")
    lead_time_days: int = Field(description="采购周期（天）")
    supplier_count: int = Field(description="供应商数量")
    grade: str = Field(description="分级结果：A / B / C")
    reasons: List[str] = Field(description="分级原因")
    strategy: str = Field(description="建议管理策略")


class ABCClassificationResponse(BaseModel):
    """ABC 分级响应"""

    total: int
    summary: Dict[str, int] = Field(description="各级数量 {'A': n, 'B': n, 'C': n}")
    items: List[ABCMaterialResult]


# ==================== 供应商动态升降级 ====================


class SupplierReclassifyConfig(BaseModel):
    """供应商升降级配置"""

    upgrade_threshold: Decimal = Field(
        default=Decimal("90"),
        description="升级分数阈值（连续 2 季度 ≥ 此分数）",
    )
    downgrade_threshold: Decimal = Field(
        default=Decimal("60"),
        description="降级分数阈值（连续 2 季度 < 此分数）",
    )
    consecutive_quarters: int = Field(
        default=2,
        description="连续季度数",
    )
    critical_quality_auto_eliminate: bool = Field(
        default=True,
        description="重大质量问题直接淘汰",
    )


class SupplierReclassifyRequest(BaseModel):
    """供应商升降级请求"""

    config: SupplierReclassifyConfig = Field(
        default_factory=SupplierReclassifyConfig,
    )
    supplier_ids: Optional[List[int]] = Field(
        default=None,
        description="指定供应商 ID 列表（不传则对全部活跃物料供应商评估）",
    )
    quarter_scores: Optional[List[Dict]] = Field(
        default=None,
        description="外部传入的季度绩效数据 [{'supplier_id': 1, 'quarters': [{'quarter': 'Q1', 'score': 92}]}]",
    )


class SupplierReclassifyResult(BaseModel):
    """单条供应商升降级结果"""

    supplier_id: int
    supplier_code: str
    supplier_name: str
    current_level: str
    new_level: str
    action: str = Field(description="UPGRADE / DOWNGRADE / ELIMINATE / NO_CHANGE")
    reason: str
    recent_scores: List[Dict] = Field(description="近期季度绩效")
    recommendation: str = Field(description="建议措施")


class SupplierReclassifyResponse(BaseModel):
    """供应商升降级响应"""

    total: int
    upgraded: int
    downgraded: int
    eliminated: int
    unchanged: int
    items: List[SupplierReclassifyResult]


# ==================== 缺料自动升级通知 ====================


class ShortageEscalationConfig(BaseModel):
    """缺料升级通知配置"""

    level1_days: int = Field(default=1, description="一级通知起始天数")
    level1_max_days: int = Field(default=3, description="一级通知最大天数")
    level2_days: int = Field(default=4, description="二级通知起始天数")
    level2_max_days: int = Field(default=7, description="二级通知最大天数")
    level3_days: int = Field(default=8, description="三级通知起始天数")


class ShortageEscalationRequest(BaseModel):
    """缺料升级通知请求"""

    config: ShortageEscalationConfig = Field(
        default_factory=ShortageEscalationConfig,
    )
    project_id: Optional[int] = Field(
        default=None,
        description="指定项目 ID（不传则检查所有项目）",
    )


class EscalationRecord(BaseModel):
    """单条升级通知记录"""

    shortage_id: int
    material_code: str
    material_name: str
    project_id: int
    project_code: Optional[str] = None
    required_date: Optional[str] = None
    overdue_days: int
    escalation_level: int = Field(description="升级级别：1/2/3")
    notify_roles: List[str] = Field(description="通知角色列表")
    message: str = Field(description="通知内容")
    escalated_at: str = Field(description="升级时间")


class ShortageEscalationResponse(BaseModel):
    """缺料升级通知响应"""

    total_shortages_checked: int
    escalated_count: int
    escalation_summary: Dict[str, int] = Field(
        description="各级别通知数量 {'level_1': n, 'level_2': n, 'level_3': n}"
    )
    items: List[EscalationRecord]


# ==================== 齐套率阶段目标配置 ====================


class StageKittingTarget(BaseModel):
    """单阶段齐套率目标"""

    stage: str = Field(description="阶段代码：S3/S4/S5/S6")
    target_rate: Decimal = Field(
        ge=0, le=100, description="目标齐套率（百分比）"
    )


class KittingTargetsRequest(BaseModel):
    """齐套率目标配置请求"""

    targets: List[StageKittingTarget] = Field(
        description="各阶段齐套率目标列表",
    )


class StageKittingStatus(BaseModel):
    """单阶段齐套率状态"""

    stage: str
    stage_name: str
    target_rate: Optional[Decimal] = Field(description="目标齐套率")
    actual_rate: Optional[Decimal] = Field(description="实际齐套率")
    gap: Optional[Decimal] = Field(description="差距（actual - target）")
    is_met: bool = Field(description="是否达标")
    alert: Optional[str] = Field(default=None, description="预警信息")


class KittingTargetsResponse(BaseModel):
    """齐套率目标配置响应"""

    project_id: int
    project_code: str
    project_name: str
    current_stage: str
    stages: List[StageKittingStatus]
    overall_met: bool = Field(description="当前阶段是否达标")
