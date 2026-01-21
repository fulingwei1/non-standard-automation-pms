# -*- coding: utf-8 -*-
"""
销售线索优先级评分服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .constants import ScoringConstants
from .core import LeadPriorityScoringCore
from .descriptions import DescriptionsMixin
from .lead_scoring import LeadScoringMixin
from .level_determination import LevelDeterminationMixin
from .opportunity_scoring import OpportunityScoringMixin
from .ranking import RankingMixin
from .scoring_helpers import ScoringHelpersMixin


class LeadPriorityScoringService(
    LeadPriorityScoringCore,
    ScoringConstants,
    LeadScoringMixin,
    OpportunityScoringMixin,
    RankingMixin,
    ScoringHelpersMixin,
    LevelDeterminationMixin,
    DescriptionsMixin,
):
    """销售线索优先级评分服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        LeadPriorityScoringCore.__init__(self, db)


__all__ = ["LeadPriorityScoringService"]
