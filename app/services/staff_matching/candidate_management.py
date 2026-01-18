# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 候选人管理
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.staff_matching import HrAIMatchingLog, MesProjectStaffingNeed


class CandidateManager:
    """候选人管理器"""

    @classmethod
    def accept_candidate(
        cls,
        db: Session,
        matching_log_id: int,
        acceptor_id: int
    ) -> bool:
        """采纳候选人"""
        log = db.query(HrAIMatchingLog).filter(HrAIMatchingLog.id == matching_log_id).first()
        if not log:
            return False

        log.is_accepted = True
        log.accept_time = datetime.now()
        log.acceptor_id = acceptor_id

        # 更新需求的已填充人数
        staffing_need = db.query(MesProjectStaffingNeed).filter(
            MesProjectStaffingNeed.id == log.staffing_need_id
        ).first()

        if staffing_need:
            staffing_need.filled_count = (staffing_need.filled_count or 0) + 1
            if staffing_need.filled_count >= staffing_need.headcount:
                staffing_need.status = 'FILLED'

        db.commit()
        return True

    @classmethod
    def reject_candidate(
        cls,
        db: Session,
        matching_log_id: int,
        reject_reason: str
    ) -> bool:
        """拒绝候选人"""
        log = db.query(HrAIMatchingLog).filter(HrAIMatchingLog.id == matching_log_id).first()
        if not log:
            return False

        log.is_accepted = False
        log.reject_reason = reject_reason
        db.commit()
        return True

    @classmethod
    def get_matching_history(
        cls,
        db: Session,
        project_id: Optional[int] = None,
        staffing_need_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        limit: int = 50
    ) -> List[HrAIMatchingLog]:
        """获取匹配历史"""
        query = db.query(HrAIMatchingLog)

        if project_id:
            query = query.filter(HrAIMatchingLog.project_id == project_id)
        if staffing_need_id:
            query = query.filter(HrAIMatchingLog.staffing_need_id == staffing_need_id)
        if employee_id:
            query = query.filter(HrAIMatchingLog.candidate_employee_id == employee_id)

        return query.order_by(HrAIMatchingLog.matching_time.desc()).limit(limit).all()
