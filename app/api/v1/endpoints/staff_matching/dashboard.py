# -*- coding: utf-8 -*-
"""
仪表板 API端点
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.models.staff_matching import HrAIMatchingLog, MesProjectStaffingNeed
from app.models.user import User


class StaffMatchingDashboardEndpoint(BaseDashboardEndpoint):
    """人员匹配Dashboard端点"""
    
    module_name = "staff_matching"
    permission_required = "staff_matching:read"
    
    def __init__(self):
        """初始化路由，覆盖主路由路径为/"""
        # 先创建router，不调用super().__init__()
        self.router = APIRouter()
        self._register_custom_routes()
    
    def _register_custom_routes(self):
        """注册自定义路由"""
        user_dependency = self._get_user_dependency()
        
        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_dashboard_handler(db, current_user)
        
        # 主dashboard端点（路径为/，保持向后兼容）
        self.router.add_api_route(
            "/",
            dashboard_endpoint,
            methods=["GET"],
            summary="获取人员匹配仪表板"
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """获取人员匹配仪表板"""
        # 需求统计
        open_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
            MesProjectStaffingNeed.status == 'OPEN'
        ).scalar() or 0

        matching_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
            MesProjectStaffingNeed.status == 'MATCHING'
        ).scalar() or 0

        filled_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
            MesProjectStaffingNeed.status == 'FILLED'
        ).scalar() or 0

        # 按优先级统计
        priority_counts = db.query(
            MesProjectStaffingNeed.priority,
            func.count(MesProjectStaffingNeed.id)
        ).filter(
            MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING'])
        ).group_by(MesProjectStaffingNeed.priority).all()

        needs_by_priority = {p: c for p, c in priority_counts}

        # 匹配统计
        total_requests = db.query(func.count(func.distinct(HrAIMatchingLog.request_id))).scalar() or 0
        total_matched = db.query(func.count(HrAIMatchingLog.id)).scalar() or 0
        accepted = db.query(func.count(HrAIMatchingLog.id)).filter(
            HrAIMatchingLog.is_accepted
        ).scalar() or 0
        rejected = db.query(func.count(HrAIMatchingLog.id)).filter(
            not HrAIMatchingLog.is_accepted
        ).scalar() or 0
        pending = total_matched - accepted - rejected

        avg_score = db.query(func.avg(HrAIMatchingLog.total_score)).filter(
            HrAIMatchingLog.is_accepted
        ).scalar()

        success_rate = (accepted / total_matched * 100) if total_matched > 0 else 0

        # 最近匹配
        recent_logs = db.query(HrAIMatchingLog).order_by(
            HrAIMatchingLog.matching_time.desc()
        ).limit(10).all()

        recent_matches = []
        for log in recent_logs:
            recent_matches.append(
                self.create_list_item(
                    id=log.id,
                    title=f"{log.project.name if log.project else '未知项目'} - {log.candidate.name if log.candidate else '未知员工'}",
                    subtitle=f"匹配分数: {log.total_score}",
                    status="accepted" if log.is_accepted else ("rejected" if log.is_accepted is False else "pending"),
                    extra={
                        'request_id': log.request_id,
                        'project_id': log.project_id,
                        'staffing_need_id': log.staffing_need_id,
                        'candidate_employee_id': log.candidate_employee_id,
                        'total_score': log.total_score,
                        'dimension_scores': log.dimension_scores,
                        'rank': log.rank,
                        'recommendation_type': log.recommendation_type,
                        'matching_time': str(log.matching_time) if log.matching_time else None,
                    }
                )
            )

        # 统计总人数需求
        total_headcount_needed = db.query(func.sum(MesProjectStaffingNeed.headcount)).filter(
            MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING', 'FILLED'])
        ).scalar() or 0

        # 统计已填充人数
        total_headcount_filled = db.query(func.sum(MesProjectStaffingNeed.headcount)).filter(
            MesProjectStaffingNeed.status == 'FILLED'
        ).scalar() or 0

        # 使用基类方法创建统计卡片
        stats = [
            self.create_stat_card(
                key="open_needs",
                label="待匹配需求",
                value=open_needs,
                unit="个",
                icon="open",
                color="warning"
            ),
            self.create_stat_card(
                key="matching_needs",
                label="匹配中需求",
                value=matching_needs,
                unit="个",
                icon="matching"
            ),
            self.create_stat_card(
                key="filled_needs",
                label="已填充需求",
                value=filled_needs,
                unit="个",
                icon="filled",
                color="success"
            ),
            self.create_stat_card(
                key="total_headcount_needed",
                label="总需求人数",
                value=int(total_headcount_needed),
                unit="人",
                icon="headcount"
            ),
            self.create_stat_card(
                key="total_headcount_filled",
                label="已填充人数",
                value=int(total_headcount_filled),
                unit="人",
                icon="filled_headcount"
            ),
            self.create_stat_card(
                key="success_rate",
                label="匹配成功率",
                value=round(success_rate, 1),
                unit="%",
                icon="success"
            ),
        ]

        return {
            'stats': stats,
            'open_needs': open_needs,
            'matching_needs': matching_needs,
            'filled_needs': filled_needs,
            'total_headcount_needed': int(total_headcount_needed),
            'total_headcount_filled': int(total_headcount_filled),
            'needs_by_priority': needs_by_priority,
            'matching_stats': {
                'total_requests': total_requests,
                'total_candidates_matched': total_matched,
                'accepted_count': accepted,
                'rejected_count': rejected,
                'pending_count': pending,
                'avg_score': round(float(avg_score), 2) if avg_score else None,
                'success_rate': round(success_rate, 2)
            },
            'recent_matches': recent_matches
        }


# 创建端点实例并获取路由
dashboard_endpoint = StaffMatchingDashboardEndpoint()
router = dashboard_endpoint.router
