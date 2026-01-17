# -*- coding: utf-8 -*-
"""
绩效融合服务
将任职资格体系与绩效评价系统融合
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.performance import (
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
    PerformancePeriod,
    PerformanceResult,
)
from app.models.qualification import EmployeeQualification
from app.models.user import User
from app.services.qualification_service import QualificationService


class PerformanceIntegrationService:
    """绩效融合服务"""

    # 默认权重配置
    DEFAULT_BASE_PERFORMANCE_WEIGHT = 0.70  # 基础绩效权重 70%
    DEFAULT_QUALIFICATION_WEIGHT = 0.30     # 任职资格权重 30%

    @staticmethod
    def calculate_integrated_score(
        db: Session,
        user_id: int,
        period: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算融合后的绩效得分

        Args:
            db: 数据库会话
            user_id: 用户ID
            period: 考核周期 (格式: YYYY-MM)

        Returns:
            {
                'base_score': float,           # 基础绩效得分
                'qualification_score': float,   # 任职资格得分
                'integrated_score': float,      # 融合后综合得分
                'base_weight': float,           # 基础绩效权重
                'qualification_weight': float,  # 任职资格权重
                'qualification_level': str,     # 任职资格等级
                'details': {...}                # 详细信息
            }
        """
        # 1. 获取基础绩效得分
        base_score = PerformanceIntegrationService._get_base_performance_score(
            db, user_id, period
        )

        if base_score is None:
            return None

        # 2. 获取任职资格得分
        qualification_data = PerformanceIntegrationService._get_qualification_score(
            db, user_id
        )

        # 3. 获取权重配置
        weight_config = PerformanceIntegrationService.get_qualification_weight_config()

        # 4. 计算融合得分
        if qualification_data:
            qualification_score = qualification_data.get('score', 0.0)
            integrated_score = (
                base_score * weight_config['base_weight'] +
                qualification_score * weight_config['qualification_weight']
            )
        else:
            # 如果没有任职资格，只使用基础绩效
            qualification_score = 0.0
            integrated_score = base_score

        return {
            'base_score': float(base_score),
            'qualification_score': float(qualification_score),
            'integrated_score': float(integrated_score),
            'base_weight': weight_config['base_weight'],
            'qualification_weight': weight_config['qualification_weight'],
            'qualification_level': qualification_data.get('level_code') if qualification_data else None,
            'details': {
                'base_performance': base_score,
                'qualification': qualification_data,
                'calculation': {
                    'formula': f"{base_score} × {weight_config['base_weight']} + {qualification_score} × {weight_config['qualification_weight']}",
                    'result': integrated_score
                }
            }
        }

    @staticmethod
    def _get_base_performance_score(
        db: Session,
        user_id: int,
        period: str
    ) -> Optional[Decimal]:
        """获取基础绩效得分"""
        # 获取工作总结
        summary = db.query(MonthlyWorkSummary).filter(
            MonthlyWorkSummary.employee_id == user_id,
            MonthlyWorkSummary.period == period
        ).first()

        if not summary:
            return None

        # 获取评价记录
        evaluations = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == summary.id,
            PerformanceEvaluationRecord.status == 'COMPLETED'
        ).all()

        if not evaluations:
            return None

        # 计算加权平均分（使用评价权重配置）
        from app.services.performance_service import PerformanceService
        final_score_data = PerformanceService.calculate_final_score(db, summary.id, period)

        if final_score_data:
            return Decimal(str(final_score_data.get('final_score', 0)))

        # 如果没有配置权重，使用简单平均
        total_score = sum(e.score for e in evaluations)
        return Decimal(str(total_score / len(evaluations)))

    @staticmethod
    def _get_qualification_score(
        db: Session,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取任职资格得分"""
        # 获取员工ID（从User获取Employee）
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.employee_id:
            return None

        # 获取员工任职资格
        qualification = QualificationService.get_employee_qualification(db, user.employee_id)
        if not qualification:
            return None

        # 获取最近的评估记录
        assessments = QualificationService.get_assessment_history(
            db, user.employee_id, qualification.id
        )

        if not assessments:
            # 如果没有评估记录，使用认证时的评估详情
            if qualification.assessment_details:
                scores = qualification.assessment_details
                total_score = sum(
                    float(v.get('score', 0)) if isinstance(v, dict) else float(v) if isinstance(v, (int, float)) else 0
                    for v in scores.values()
                ) / len(scores) if scores else 0.0
            else:
                return None
        else:
            # 使用最近的评估得分
            latest_assessment = assessments[0]
            if latest_assessment.total_score:
                total_score = float(latest_assessment.total_score)
            else:
                return None

        # 获取等级信息
        level = qualification.level
        level_code = level.level_code if level else None
        level_name = level.level_name if level else None

        return {
            'score': total_score,
            'level_id': qualification.current_level_id,
            'level_code': level_code,
            'level_name': level_name,
            'position_type': qualification.position_type,
            'certified_date': qualification.certified_date.isoformat() if qualification.certified_date else None
        }

    @staticmethod
    def get_qualification_weight_config() -> Dict[str, float]:
        """获取任职资格权重配置"""
        # 可以从配置表或环境变量读取
        # 这里使用默认值
        return {
            'base_weight': PerformanceIntegrationService.DEFAULT_BASE_PERFORMANCE_WEIGHT,
            'qualification_weight': PerformanceIntegrationService.DEFAULT_QUALIFICATION_WEIGHT
        }

    @staticmethod
    def update_qualification_in_evaluation(
        db: Session,
        evaluation_id: int,
        qualification_data: Dict[str, Any]
    ) -> PerformanceEvaluationRecord:
        """在评价中更新任职资格信息"""
        evaluation = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.id == evaluation_id
        ).first()

        if not evaluation:
            raise ValueError(f"评价记录 {evaluation_id} 不存在")

        # 更新任职资格相关字段
        evaluation.qualification_level_id = qualification_data.get('level_id')
        evaluation.qualification_score = qualification_data.get('scores')

        db.commit()
        db.refresh(evaluation)

        return evaluation

    @staticmethod
    def get_integrated_performance_for_period(
        db: Session,
        user_id: int,
        period_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取指定周期的融合绩效"""
        if period_id:
            period = db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()
            if not period:
                return None
            period_str = period.start_date.strftime('%Y-%m')
        else:
            # 获取最新周期
            period = db.query(PerformancePeriod).filter(
                PerformancePeriod.status == 'FINALIZED'
            ).order_by(PerformancePeriod.end_date.desc()).first()
            if not period:
                return None
            period_str = period.start_date.strftime('%Y-%m')

        return PerformanceIntegrationService.calculate_integrated_score(
            db, user_id, period_str
        )






