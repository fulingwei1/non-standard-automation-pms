# -*- coding: utf-8 -*-
"""
推荐引擎基础类型

定义所有推荐引擎共享的数据结构和基类。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session


class RecommendationType(str, Enum):
    """推荐类型"""

    FOLLOW_UP = "follow_up"  # 跟进策略
    PRICING = "pricing"  # 报价优化
    RELATIONSHIP = "relationship"  # 客户关系
    CROSS_SELL = "cross_sell"  # 交叉销售
    UPSELL = "upsell"  # 升级销售
    PRIORITY = "priority"  # 优先级排序
    RISK = "risk"  # 风险预警


class RecommendationPriority(str, Enum):
    """推荐优先级"""

    CRITICAL = "critical"  # 紧急
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


@dataclass
class Recommendation:
    """推荐项"""

    type: RecommendationType  # 推荐类型
    priority: RecommendationPriority  # 优先级
    title: str  # 标题
    description: str  # 详细描述
    action: str  # 建议行动
    entity_type: Optional[str] = None  # 关联实体类型
    entity_id: Optional[int] = None  # 关联实体ID
    confidence: float = 0.0  # 置信度 (0-1)
    expected_impact: Optional[str] = None  # 预期影响
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据


@dataclass
class RecommendationResult:
    """推荐结果"""

    user_id: int  # 用户ID
    generated_at: datetime  # 生成时间
    recommendations: List[Recommendation]  # 推荐列表
    summary: Dict[str, Any] = field(default_factory=dict)  # 摘要统计


class BaseRecommendationEngine:
    """推荐引擎基类"""

    def __init__(self, db: Session):
        self.db = db

    def get_recommendations(self, user_id: int) -> List[Recommendation]:
        """
        获取推荐列表。

        子类必须实现此方法。

        Args:
            user_id: 用户 ID

        Returns:
            推荐列表
        """
        raise NotImplementedError("子类必须实现 get_recommendations 方法")
