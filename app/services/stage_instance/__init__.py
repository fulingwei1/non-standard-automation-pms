# -*- coding: utf-8 -*-
"""
阶段实例服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .adjustments import AdjustmentsMixin
from .core import StageInstanceCore
from .helpers import HelpersMixin
from .initialization import InitializationMixin
from .node_operations import NodeOperationsMixin
from .progress_query import ProgressQueryMixin
from .stage_flow import StageFlowMixin


class StageInstanceService(
    StageInstanceCore,
    InitializationMixin,
    StageFlowMixin,
    NodeOperationsMixin,
    ProgressQueryMixin,
    AdjustmentsMixin,
    HelpersMixin,
):
    """阶段实例服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        StageInstanceCore.__init__(self, db)


__all__ = ["StageInstanceService"]
