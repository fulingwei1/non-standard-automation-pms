# -*- coding: utf-8 -*-
"""
部门经理评价服务
实现部门经理对工程师绩效的调整功能
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import PerformanceAdjustmentHistory, PerformanceResult
from app.models.user import User
from app.utils.db_helpers import save_obj


class ManagerEvaluationService:
    """部门经理评价服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_manager_permission(
        self,
        manager_id: int,
        engineer_id: int
    ) -> bool:
        """
        检查部门经理是否有权限评价该工程师

        Args:
            manager_id: 部门经理ID
            engineer_id: 工程师ID

        Returns:
            bool: 是否有权限
        """
        # 获取部门经理管理的部门
        manager = self.db.query(User).filter(User.id == manager_id).first()
        if not manager:
            return False

        # 检查是否是部门经理
        dept = self.db.query(Department).filter(
            Department.manager_id == manager.employee_id,
            Department.is_active
        ).first()

        if not dept:
            return False

        # 检查工程师是否在该部门
        engineer = self.db.query(User).filter(User.id == engineer_id).first()
        if not engineer or not engineer.employee_id:
            return False

        from app.models.organization import Employee
        employee = self.db.query(Employee).filter(
            Employee.id == engineer.employee_id
        ).first()

        if not employee or employee.department_id != dept.id:
            return False

        return True

    def adjust_performance(
        self,
        result_id: int,
        manager_id: int,
        new_total_score: Optional[Decimal] = None,
        new_dept_rank: Optional[int] = None,
        new_company_rank: Optional[int] = None,
        adjustment_reason: str = ""
    ) -> PerformanceResult:
        """
        部门经理调整绩效得分和排名

        Args:
            result_id: 绩效结果ID
            manager_id: 部门经理ID
            new_total_score: 新的综合得分（可选）
            new_dept_rank: 新的部门排名（可选）
            new_company_rank: 新的公司排名（可选）
            adjustment_reason: 调整理由（必填）

        Returns:
            更新后的绩效结果
        """
        # 调整理由必填验证（至少10个字符）
        if not adjustment_reason or not adjustment_reason.strip():
            raise ValueError("调整理由不能为空，请详细说明调整原因")

        if len(adjustment_reason.strip()) < 10:
            raise ValueError("调整理由至少需要10个字符，请详细说明调整原因")

        result = self.db.query(PerformanceResult).filter(
            PerformanceResult.id == result_id
        ).first()

        if not result:
            raise ValueError(f"绩效结果不存在: {result_id}")

        # 检查权限
        if not self.check_manager_permission(manager_id, result.user_id):
            raise ValueError("无权限调整该工程师的绩效")

        # 获取部门经理信息
        manager = self.db.query(User).filter(User.id == manager_id).first()
        if not manager:
            raise ValueError("部门经理不存在")

        # 保存原始值（如果是第一次调整）
        if not result.is_adjusted:
            result.original_total_score = result.total_score
            result.original_dept_rank = result.dept_rank
            result.original_company_rank = result.company_rank

        # 创建调整历史记录
        history = PerformanceAdjustmentHistory(
            result_id=result_id,
            original_total_score=result.total_score,
            original_dept_rank=result.dept_rank,
            original_company_rank=result.company_rank,
            original_level=result.level,
            adjusted_total_score=new_total_score if new_total_score else result.total_score,
            adjusted_dept_rank=new_dept_rank if new_dept_rank else result.dept_rank,
            adjusted_company_rank=new_company_rank if new_company_rank else result.company_rank,
            adjustment_reason=adjustment_reason,
            adjusted_by=manager_id,
            adjusted_by_name=manager.name or manager.username,
            adjusted_at=datetime.now()
        )

        # 更新绩效结果
        if new_total_score is not None:
            result.adjusted_total_score = new_total_score
            result.total_score = new_total_score
            # 重新计算等级
            result.level = self._calculate_level(new_total_score)

        if new_dept_rank is not None:
            result.adjusted_dept_rank = new_dept_rank
            result.dept_rank = new_dept_rank

        if new_company_rank is not None:
            result.adjusted_company_rank = new_company_rank
            result.company_rank = new_company_rank

        result.adjustment_reason = adjustment_reason
        result.adjusted_by = manager_id
        result.adjusted_at = datetime.now()
        result.is_adjusted = True

        # 更新历史记录中的调整后等级
        history.adjusted_level = result.level

        self.db.add(history)
        save_obj(self.db, result)

        return result

    def _calculate_level(self, score: Decimal) -> str:
        """根据得分计算等级"""
        score_int = int(score)
        if score_int >= 85:
            return 'S'
        elif score_int >= 70:
            return 'A'
        elif score_int >= 60:
            return 'B'
        elif score_int >= 40:
            return 'C'
        else:
            return 'D'

    def get_adjustment_history(
        self,
        result_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取调整历史记录（增强版：包含详细信息）

        Args:
            result_id: 绩效结果ID

        Returns:
            调整历史记录列表（包含详细信息）
        """
        histories = self.db.query(PerformanceAdjustmentHistory).filter(
            PerformanceAdjustmentHistory.result_id == result_id
        ).order_by(desc(PerformanceAdjustmentHistory.adjusted_at)).all()

        result = []
        for history in histories:
            # 获取调整人信息
            adjuster = self.db.query(User).filter(User.id == history.adjusted_by).first()

            result.append({
                'id': history.id,
                'result_id': history.result_id,
                'original_total_score': float(history.original_total_score) if history.original_total_score else None,
                'original_dept_rank': history.original_dept_rank,
                'original_company_rank': history.original_company_rank,
                'original_level': history.original_level,
                'adjusted_total_score': float(history.adjusted_total_score) if history.adjusted_total_score else None,
                'adjusted_dept_rank': history.adjusted_dept_rank,
                'adjusted_company_rank': history.adjusted_company_rank,
                'adjusted_level': history.adjusted_level,
                'adjustment_reason': history.adjustment_reason,
                'adjusted_by': history.adjusted_by,
                'adjusted_by_name': history.adjusted_by_name or (adjuster.name if adjuster else None),
                'adjusted_at': history.adjusted_at.isoformat() if history.adjusted_at else None,
                'score_change': float(history.adjusted_total_score - history.original_total_score) if history.adjusted_total_score and history.original_total_score else 0.0,
                'rank_change': {
                    'dept': (history.adjusted_dept_rank - history.original_dept_rank) if history.adjusted_dept_rank and history.original_dept_rank else 0,
                    'company': (history.adjusted_company_rank - history.original_company_rank) if history.adjusted_company_rank and history.original_company_rank else 0
                }
            })

        return result

    def get_engineers_for_evaluation(
        self,
        manager_id: int,
        period_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取部门经理可评价的工程师列表

        Args:
            manager_id: 部门经理ID
            period_id: 考核周期ID（可选）

        Returns:
            可评价的工程师列表
        """
        results = self.get_manager_evaluation_tasks(manager_id, period_id)

        engineers = []
        for result in results:
            engineer = self.db.query(User).filter(User.id == result.user_id).first()
            if engineer:
                engineers.append({
                    'user_id': engineer.id,
                    'username': engineer.username,
                    'name': engineer.real_name or engineer.name or engineer.username,
                    'result_id': result.id,
                    'total_score': float(result.total_score) if result.total_score else None,
                    'dept_rank': result.dept_rank,
                    'company_rank': result.company_rank,
                    'level': result.level,
                    'is_adjusted': result.is_adjusted,
                    'adjustment_reason': result.adjustment_reason
                })

        return engineers

    def get_manager_evaluation_tasks(
        self,
        manager_id: int,
        period_id: Optional[int] = None
    ) -> List[PerformanceResult]:
        """
        获取部门经理需要评价的任务列表

        Args:
            manager_id: 部门经理ID
            period_id: 考核周期ID（可选）

        Returns:
            需要评价的绩效结果列表
        """
        # 获取部门经理管理的部门
        manager = self.db.query(User).filter(User.id == manager_id).first()
        if not manager:
            return []

        dept = self.db.query(Department).filter(
            Department.manager_id == manager.employee_id,
            Department.is_active
        ).first()

        if not dept:
            return []

        # 获取该部门的所有工程师
        from app.models.organization import Employee
        employees = self.db.query(Employee).filter(
            Employee.department_id == dept.id,
            Employee.is_active
        ).all()

        employee_ids = [e.id for e in employees]
        user_ids = [
            u.id for u in self.db.query(User).filter(
                User.employee_id.in_(employee_ids)
            ).all()
        ]

        if not user_ids:
            return []

        # 查询绩效结果
        query = self.db.query(PerformanceResult).filter(
            PerformanceResult.user_id.in_(user_ids)
        )

        if period_id:
            query = query.filter(PerformanceResult.period_id == period_id)

        return query.order_by(desc(PerformanceResult.total_score)).all()

    def submit_evaluation(
        self,
        result_id: int,
        manager_id: int,
        overall_comment: Optional[str] = None,
        strength_comment: Optional[str] = None,
        improvement_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交评价（不调整得分和排名）

        Args:
            result_id: 绩效结果ID
            manager_id: 部门经理ID
            overall_comment: 总体评价
            strength_comment: 优点评价
            improvement_comment: 改进建议

        Returns:
            评价结果
        """
        result = self.db.query(PerformanceResult).filter(
            PerformanceResult.id == result_id
        ).first()

        if not result:
            raise ValueError(f"绩效结果不存在: {result_id}")

        # 检查权限
        if not self.check_manager_permission(manager_id, result.user_id):
            raise ValueError("无权限评价该工程师")

        # 创建或更新评价记录
        from app.models.performance import PerformanceEvaluation
        evaluation = self.db.query(PerformanceEvaluation).filter(
            PerformanceEvaluation.result_id == result_id,
            PerformanceEvaluation.evaluator_id == manager_id
        ).first()

        manager = self.db.query(User).filter(User.id == manager_id).first()

        if evaluation:
            # 更新现有评价
            evaluation.overall_comment = overall_comment
            evaluation.strength_comment = strength_comment
            evaluation.improvement_comment = improvement_comment
            evaluation.evaluated_at = datetime.now()
        else:
            # 创建新评价
            evaluation = PerformanceEvaluation(
                result_id=result_id,
                evaluator_id=manager_id,
                evaluator_name=manager.name or manager.username if manager else None,
                evaluator_role='dept_manager',
                overall_comment=overall_comment,
                strength_comment=strength_comment,
                improvement_comment=improvement_comment,
                evaluated_at=datetime.now()
            )
            self.db.add(evaluation)

        self.db.commit()
        self.db.refresh(evaluation)

        return {
            'evaluation_id': evaluation.id,
            'result_id': result_id,
            'message': '评价提交成功'
        }
