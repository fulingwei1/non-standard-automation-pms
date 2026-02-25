# -*- coding: utf-8 -*-
"""
资源调度服务层
提取自 app/api/v1/endpoints/resource_scheduling.py
负责资源冲突检测、调度方案推荐、需求预测、利用率分析等业务逻辑
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.resource_scheduling import (
    ResourceConflictDetection,
    ResourceDemandForecast,
    ResourceSchedulingLog,
    ResourceSchedulingSuggestion,
    ResourceUtilizationAnalysis,
)
from app.models.user import User
from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService


class ResourceSchedulingService:
    """资源调度服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = ResourceSchedulingAIService(db)

    # ============================================================================
    # 1. 资源冲突检测
    # ============================================================================

    def detect_conflicts(
        self,
        resource_id: Optional[int],
        resource_type: str,
        project_id: Optional[int],
        start_date: Optional[str],
        end_date: Optional[str],
        auto_generate_suggestions: bool,
        operator_id: int,
        operator_name: str,
    ) -> Dict[str, Any]:
        """
        检测资源冲突
        
        Returns:
            dict: {
                'conflicts': List[ResourceConflictDetection],
                'total_conflicts': int,
                'critical_conflicts': int,
                'suggestions_generated': int,
                'detection_time_ms': int,
            }
        """
        start_time = time.time()

        # 检测冲突
        conflicts = self.ai_service.detect_resource_conflicts(
            resource_id=resource_id,
            resource_type=resource_type,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 统计
        total_conflicts = len(conflicts)
        critical_conflicts = sum(1 for c in conflicts if c.severity == "CRITICAL")

        # 自动生成方案
        suggestions_generated = 0
        if auto_generate_suggestions and conflicts:
            for conflict in conflicts[:5]:  # 限制前5个
                try:
                    self.ai_service.generate_scheduling_suggestions(
                        conflict_id=conflict.id,
                        max_suggestions=2,
                    )
                    suggestions_generated += 1
                except Exception:
                    pass

        # 记录日志
        self._log_action(
            action_type="DETECT",
            action_desc=f"检测到{total_conflicts}个资源冲突",
            operator_id=operator_id,
            operator_name=operator_name,
            result="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

        return {
            "conflicts": conflicts,
            "total_conflicts": total_conflicts,
            "critical_conflicts": critical_conflicts,
            "suggestions_generated": suggestions_generated,
            "detection_time_ms": int((time.time() - start_time) * 1000),
        }

    def list_conflicts(
        self,
        skip: int,
        limit: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        resource_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
    ) -> List[ResourceConflictDetection]:
        """查询资源冲突列表"""
        query = self.db.query(ResourceConflictDetection)

        if status:
            query = query.filter(ResourceConflictDetection.status == status)
        if severity:
            query = query.filter(ResourceConflictDetection.severity == severity)
        if resource_id:
            query = query.filter(ResourceConflictDetection.resource_id == resource_id)
        if is_resolved is not None:
            query = query.filter(ResourceConflictDetection.is_resolved == is_resolved)

        return query.order_by(desc(ResourceConflictDetection.priority_score)).offset(skip).limit(limit).all()

    def get_conflict(self, conflict_id: int) -> Optional[ResourceConflictDetection]:
        """获取冲突详情"""
        return self.db.query(ResourceConflictDetection).filter(
            ResourceConflictDetection.id == conflict_id
        ).first()

    def update_conflict(
        self,
        conflict_id: int,
        update_data: Dict[str, Any],
        operator_id: int,
        operator_name: str,
    ) -> Optional[ResourceConflictDetection]:
        """更新冲突状态"""
        conflict = self.get_conflict(conflict_id)
        if not conflict:
            return None

        # 更新字段
        for field, value in update_data.items():
            if hasattr(conflict, field):
                setattr(conflict, field, value)

        # 如果标记为已解决
        if update_data.get("is_resolved"):
            conflict.resolved_by = operator_id
            conflict.resolved_at = datetime.now()
            conflict.status = "RESOLVED"

        conflict.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(conflict)

        # 记录日志
        self._log_action(
            conflict_id=conflict_id,
            action_type="RESOLVE" if update_data.get("is_resolved") else "UPDATE",
            action_desc="更新冲突状态",
            operator_id=operator_id,
            operator_name=operator_name,
            result="SUCCESS",
        )

        return conflict

    def delete_conflict(self, conflict_id: int) -> bool:
        """删除冲突记录"""
        conflict = self.get_conflict(conflict_id)
        if not conflict:
            return False

        self.db.delete(conflict)
        self.db.commit()
        return True

    # ============================================================================
    # 2. AI调度方案推荐
    # ============================================================================

    def generate_suggestions(
        self,
        conflict_id: int,
        max_suggestions: int,
        prefer_minimal_impact: bool,
        operator_id: int,
        operator_name: str,
    ) -> Dict[str, Any]:
        """
        AI生成调度方案
        
        Returns:
            dict: {
                'suggestions': List[ResourceSchedulingSuggestion],
                'recommended_id': Optional[int],
                'total_tokens': int,
                'generation_time_ms': int,
            }
        """
        start_time = time.time()

        suggestions = self.ai_service.generate_scheduling_suggestions(
            conflict_id=conflict_id,
            max_suggestions=max_suggestions,
            prefer_minimal_impact=prefer_minimal_impact,
        )

        # 找到推荐方案
        recommended_id = next((s.id for s in suggestions if s.is_recommended), None)

        # 统计Token消耗
        total_tokens = sum(s.ai_tokens_used or 0 for s in suggestions)

        # 记录日志
        self._log_action(
            conflict_id=conflict_id,
            action_type="SUGGEST",
            action_desc=f"AI生成{len(suggestions)}个调度方案",
            operator_id=operator_id,
            operator_name=operator_name,
            result="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
            ai_tokens_used=total_tokens,
        )

        return {
            "suggestions": suggestions,
            "recommended_id": recommended_id,
            "total_tokens": total_tokens,
            "generation_time_ms": int((time.time() - start_time) * 1000),
        }

    def list_suggestions(
        self,
        skip: int,
        limit: int,
        conflict_id: Optional[int] = None,
        status: Optional[str] = None,
        solution_type: Optional[str] = None,
        is_recommended: Optional[bool] = None,
    ) -> List[ResourceSchedulingSuggestion]:
        """查询调度方案列表"""
        query = self.db.query(ResourceSchedulingSuggestion)

        if conflict_id:
            query = query.filter(ResourceSchedulingSuggestion.conflict_id == conflict_id)
        if status:
            query = query.filter(ResourceSchedulingSuggestion.status == status)
        if solution_type:
            query = query.filter(ResourceSchedulingSuggestion.solution_type == solution_type)
        if is_recommended is not None:
            query = query.filter(ResourceSchedulingSuggestion.is_recommended == is_recommended)

        return query.order_by(ResourceSchedulingSuggestion.rank_order).offset(skip).limit(limit).all()

    def get_suggestion(self, suggestion_id: int) -> Optional[ResourceSchedulingSuggestion]:
        """获取方案详情"""
        return self.db.query(ResourceSchedulingSuggestion).filter(
            ResourceSchedulingSuggestion.id == suggestion_id
        ).first()

    def review_suggestion(
        self,
        suggestion_id: int,
        action: str,
        review_comment: Optional[str],
        operator_id: int,
        operator_name: str,
    ) -> Tuple[bool, Optional[ResourceSchedulingSuggestion], Optional[str]]:
        """
        审核调度方案
        
        Returns:
            (success, suggestion, error_msg)
        """
        suggestion = self.get_suggestion(suggestion_id)
        if not suggestion:
            return False, None, f"Suggestion {suggestion_id} not found"

        if action == "ACCEPT":
            suggestion.status = "ACCEPTED"
        elif action == "REJECT":
            suggestion.status = "REJECTED"
        else:
            return False, None, "Invalid action. Use ACCEPT or REJECT."

        suggestion.reviewed_by = operator_id
        suggestion.reviewed_at = datetime.now()
        suggestion.review_comment = review_comment
        suggestion.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(suggestion)

        # 记录日志
        self._log_action(
            suggestion_id=suggestion_id,
            action_type="REVIEW",
            action_desc=f"审核方案: {action}",
            operator_id=operator_id,
            operator_name=operator_name,
            result="SUCCESS",
        )

        return True, suggestion, None

    def implement_suggestion(
        self,
        suggestion_id: int,
        implementation_result: str,
        operator_id: int,
        operator_name: str,
    ) -> Tuple[bool, Optional[ResourceSchedulingSuggestion], Optional[str]]:
        """
        执行调度方案
        
        Returns:
            (success, suggestion, error_msg)
        """
        suggestion = self.get_suggestion(suggestion_id)
        if not suggestion:
            return False, None, f"Suggestion {suggestion_id} not found"

        if suggestion.status != "ACCEPTED":
            return False, None, "Only ACCEPTED suggestions can be implemented"

        suggestion.status = "IMPLEMENTED"
        suggestion.implemented_by = operator_id
        suggestion.implemented_at = datetime.now()
        suggestion.implementation_result = implementation_result
        suggestion.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(suggestion)

        # 同时解决关联的冲突
        conflict = self.db.query(ResourceConflictDetection).filter(
            ResourceConflictDetection.id == suggestion.conflict_id
        ).first()

        if conflict:
            conflict.is_resolved = True
            conflict.resolved_by = operator_id
            conflict.resolved_at = datetime.now()
            conflict.resolution_method = f"AI方案{suggestion.solution_type}"
            conflict.status = "RESOLVED"
            self.db.commit()

        # 记录日志
        self._log_action(
            suggestion_id=suggestion_id,
            conflict_id=suggestion.conflict_id,
            action_type="IMPLEMENT",
            action_desc="执行调度方案",
            operator_id=operator_id,
            operator_name=operator_name,
            result="SUCCESS",
        )

        return True, suggestion, None

    # ============================================================================
    # 3. 资源需求预测
    # ============================================================================

    def generate_forecast(
        self,
        forecast_period: str,
        resource_type: Optional[str],
        skill_category: Optional[str],
    ) -> Dict[str, Any]:
        """
        生成资源需求预测
        
        Returns:
            dict: {
                'forecasts': List[ResourceDemandForecast],
                'critical_gaps': int,
                'total_hiring': int,
                'generation_time_ms': int,
            }
        """
        start_time = time.time()

        forecasts = self.ai_service.forecast_resource_demand(
            forecast_period=forecast_period,
            resource_type=resource_type,
            skill_category=skill_category,
        )

        # 统计关键缺口
        critical_gaps = sum(1 for f in forecasts if f.gap_severity in ["SHORTAGE", "CRITICAL"])
        total_hiring = sum(f.demand_gap for f in forecasts if f.demand_gap and f.demand_gap > 0)

        return {
            "forecasts": forecasts,
            "critical_gaps": critical_gaps,
            "total_hiring": total_hiring or 0,
            "generation_time_ms": int((time.time() - start_time) * 1000),
        }

    def list_forecasts(
        self,
        skip: int,
        limit: int,
        forecast_period: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ResourceDemandForecast]:
        """查询资源需求预测列表"""
        query = self.db.query(ResourceDemandForecast)

        if forecast_period:
            query = query.filter(ResourceDemandForecast.forecast_period == forecast_period)
        if status:
            query = query.filter(ResourceDemandForecast.status == status)

        return query.order_by(desc(ResourceDemandForecast.created_at)).offset(skip).limit(limit).all()

    def get_forecast(self, forecast_id: int) -> Optional[ResourceDemandForecast]:
        """获取预测详情"""
        return self.db.query(ResourceDemandForecast).filter(
            ResourceDemandForecast.id == forecast_id
        ).first()

    # ============================================================================
    # 4. 资源利用率分析
    # ============================================================================

    def analyze_utilization(
        self,
        resource_id: Optional[int],
        start_date: Optional[str],
        end_date: Optional[str],
        analysis_period: str,
    ) -> Dict[str, Any]:
        """
        分析资源利用率
        
        Returns:
            dict: {
                'analyses': List[ResourceUtilizationAnalysis],
                'idle_count': int,
                'overloaded_count': int,
                'avg_utilization': float,
                'analysis_time_ms': int,
            }
        """
        start_time = time.time()

        analyses = []

        # 如果指定resource_id，分析单个资源
        if resource_id:
            analysis = self.ai_service.analyze_resource_utilization(
                resource_id=resource_id,
                start_date=start_date,
                end_date=end_date,
                analysis_period=analysis_period,
            )
            analyses.append(analysis)
        else:
            # 否则分析所有资源（限制数量）
            users = self.db.query(User).filter(User.is_active == True).limit(50).all()

            for user in users:
                try:
                    analysis = self.ai_service.analyze_resource_utilization(
                        resource_id=user.id,
                        start_date=start_date,
                        end_date=end_date,
                        analysis_period=analysis_period,
                    )
                    analyses.append(analysis)
                except Exception:
                    pass

        # 统计
        idle_count = sum(1 for a in analyses if a.is_idle_resource)
        overloaded_count = sum(1 for a in analyses if a.is_overloaded)

        # 计算平均利用率
        avg_utilization = sum(a.utilization_rate or 0 for a in analyses) / len(analyses) if analyses else 0

        return {
            "analyses": analyses,
            "idle_count": idle_count,
            "overloaded_count": overloaded_count,
            "avg_utilization": avg_utilization,
            "optimization_opportunities": idle_count + overloaded_count,
            "analysis_time_ms": int((time.time() - start_time) * 1000),
        }

    def list_utilization_analyses(
        self,
        skip: int,
        limit: int,
        resource_id: Optional[int] = None,
        is_idle: Optional[bool] = None,
        is_overloaded: Optional[bool] = None,
    ) -> List[ResourceUtilizationAnalysis]:
        """查询资源利用率分析列表"""
        query = self.db.query(ResourceUtilizationAnalysis)

        if resource_id:
            query = query.filter(ResourceUtilizationAnalysis.resource_id == resource_id)
        if is_idle is not None:
            query = query.filter(ResourceUtilizationAnalysis.is_idle_resource == is_idle)
        if is_overloaded is not None:
            query = query.filter(ResourceUtilizationAnalysis.is_overloaded == is_overloaded)

        return query.order_by(desc(ResourceUtilizationAnalysis.created_at)).offset(skip).limit(limit).all()

    def get_utilization_analysis(self, analysis_id: int) -> Optional[ResourceUtilizationAnalysis]:
        """获取利用率分析详情"""
        return self.db.query(ResourceUtilizationAnalysis).filter(
            ResourceUtilizationAnalysis.id == analysis_id
        ).first()

    # ============================================================================
    # 5. 仪表板和统计
    # ============================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        资源调度仪表板摘要
        
        Returns:
            dict: 包含所有关键指标的摘要
        """
        # 冲突统计
        total_conflicts = self.db.query(func.count(ResourceConflictDetection.id)).scalar() or 0
        critical_conflicts = self.db.query(func.count(ResourceConflictDetection.id)).filter(
            ResourceConflictDetection.severity == "CRITICAL"
        ).scalar() or 0
        unresolved_conflicts = self.db.query(func.count(ResourceConflictDetection.id)).filter(
            ResourceConflictDetection.is_resolved == False
        ).scalar() or 0

        # 方案统计
        total_suggestions = self.db.query(func.count(ResourceSchedulingSuggestion.id)).scalar() or 0
        pending_suggestions = self.db.query(func.count(ResourceSchedulingSuggestion.id)).filter(
            ResourceSchedulingSuggestion.status == "PENDING"
        ).scalar() or 0
        implemented_suggestions = self.db.query(func.count(ResourceSchedulingSuggestion.id)).filter(
            ResourceSchedulingSuggestion.status == "IMPLEMENTED"
        ).scalar() or 0

        # 利用率统计
        idle_resources = self.db.query(func.count(ResourceUtilizationAnalysis.id)).filter(
            ResourceUtilizationAnalysis.is_idle_resource == True
        ).scalar() or 0
        overloaded_resources = self.db.query(func.count(ResourceUtilizationAnalysis.id)).filter(
            ResourceUtilizationAnalysis.is_overloaded == True
        ).scalar() or 0

        # 平均利用率
        avg_util = self.db.query(func.avg(ResourceUtilizationAnalysis.utilization_rate)).scalar()
        avg_utilization = float(avg_util) if avg_util else 0.0

        # 预测统计
        forecasts_count = self.db.query(func.count(ResourceDemandForecast.id)).filter(
            ResourceDemandForecast.status == "ACTIVE"
        ).scalar() or 0

        critical_gaps = self.db.query(func.count(ResourceDemandForecast.id)).filter(
            ResourceDemandForecast.gap_severity.in_(["SHORTAGE", "CRITICAL"])
        ).scalar() or 0

        # 招聘需求
        hiring_query = self.db.query(func.sum(ResourceDemandForecast.demand_gap)).filter(
            ResourceDemandForecast.demand_gap > 0
        ).scalar()
        hiring_needed = int(hiring_query) if hiring_query else 0

        # 最近检测/分析时间
        last_conflict = self.db.query(ResourceConflictDetection).order_by(
            desc(ResourceConflictDetection.created_at)
        ).first()

        last_analysis = self.db.query(ResourceUtilizationAnalysis).order_by(
            desc(ResourceUtilizationAnalysis.created_at)
        ).first()

        return {
            "total_conflicts": total_conflicts,
            "critical_conflicts": critical_conflicts,
            "unresolved_conflicts": unresolved_conflicts,
            "total_suggestions": total_suggestions,
            "pending_suggestions": pending_suggestions,
            "implemented_suggestions": implemented_suggestions,
            "idle_resources": idle_resources,
            "overloaded_resources": overloaded_resources,
            "avg_utilization": avg_utilization,
            "forecasts_count": forecasts_count,
            "critical_gaps": critical_gaps,
            "hiring_needed": hiring_needed,
            "last_detection_time": last_conflict.created_at if last_conflict else None,
            "last_analysis_time": last_analysis.created_at if last_analysis else None,
        }

    def list_logs(
        self,
        skip: int,
        limit: int,
        action_type: Optional[str] = None,
        conflict_id: Optional[int] = None,
    ) -> List[ResourceSchedulingLog]:
        """查询资源调度操作日志"""
        query = self.db.query(ResourceSchedulingLog)

        if action_type:
            query = query.filter(ResourceSchedulingLog.action_type == action_type)
        if conflict_id:
            query = query.filter(ResourceSchedulingLog.conflict_id == conflict_id)

        return query.order_by(desc(ResourceSchedulingLog.created_at)).offset(skip).limit(limit).all()

    # ============================================================================
    # 私有辅助方法
    # ============================================================================

    def _log_action(
        self,
        action_type: str,
        action_desc: str,
        operator_id: int,
        operator_name: str,
        result: str = "SUCCESS",
        conflict_id: Optional[int] = None,
        suggestion_id: Optional[int] = None,
        execution_time_ms: Optional[int] = None,
        ai_tokens_used: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """记录操作日志"""
        log = ResourceSchedulingLog(
            conflict_id=conflict_id,
            suggestion_id=suggestion_id,
            action_type=action_type,
            action_desc=action_desc,
            operator_id=operator_id,
            operator_name=operator_name,
            result=result,
            execution_time_ms=execution_time_ms,
            ai_tokens_used=ai_tokens_used,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()
