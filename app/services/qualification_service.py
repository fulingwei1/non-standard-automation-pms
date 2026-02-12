# -*- coding: utf-8 -*-
"""
任职资格管理服务层
包含认证、评估、晋升检查等核心业务逻辑
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.qualification import (
    AssessmentResultEnum,
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationAssessment,
    QualificationLevel,
    QualificationStatusEnum,
)


class QualificationService:
    """任职资格管理服务"""

    @staticmethod
    def get_qualification_levels(
        db: Session,
        role_type: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> List[QualificationLevel]:
        """获取任职资格等级列表"""
        query = db.query(QualificationLevel)

        if role_type:
            query = query.filter(QualificationLevel.role_type == role_type)
        if is_active is not None:
            query = query.filter(QualificationLevel.is_active == is_active)

        return query.order_by(QualificationLevel.level_order).all()

    @staticmethod
    def get_competency_model(
        db: Session,
        position_type: str,
        level_id: int,
        position_subtype: Optional[str] = None
    ) -> Optional[PositionCompetencyModel]:
        """获取岗位能力模型"""
        query = db.query(PositionCompetencyModel).filter(
            PositionCompetencyModel.position_type == position_type,
            PositionCompetencyModel.level_id == level_id,
            PositionCompetencyModel.is_active
        )

        if position_subtype:
            query = query.filter(PositionCompetencyModel.position_subtype == position_subtype)

        return query.first()

    @staticmethod
    def get_employee_qualification(
        db: Session,
        employee_id: int,
        position_type: Optional[str] = None
    ) -> Optional[EmployeeQualification]:
        """获取员工任职资格"""
        query = db.query(EmployeeQualification).filter(
            EmployeeQualification.employee_id == employee_id
        )

        if position_type:
            query = query.filter(EmployeeQualification.position_type == position_type)

        return query.order_by(desc(EmployeeQualification.created_at)).first()

    @staticmethod
    def certify_employee(
        db: Session,
        employee_id: int,
        position_type: str,
        level_id: int,
        assessment_details: Dict[str, Any],
        certifier_id: int,
        certified_date: Optional[date] = None,
        valid_until: Optional[date] = None
    ) -> EmployeeQualification:
        """认证员工任职资格"""
        # 检查员工是否存在
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError(f"员工 {employee_id} 不存在")

        # 检查等级是否存在
        level = db.query(QualificationLevel).filter(QualificationLevel.id == level_id).first()
        if not level:
            raise ValueError(f"等级 {level_id} 不存在")

        # 创建或更新任职资格
        existing = db.query(EmployeeQualification).filter(
            EmployeeQualification.employee_id == employee_id,
            EmployeeQualification.position_type == position_type
        ).first()

        if existing:
            # 更新现有记录
            existing.current_level_id = level_id
            existing.assessment_details = assessment_details
            existing.certifier_id = certifier_id
            existing.certified_date = certified_date or date.today()
            existing.valid_until = valid_until
            existing.status = QualificationStatusEnum.APPROVED
            qualification = existing
        else:
            # 创建新记录
            qualification = EmployeeQualification(
                employee_id=employee_id,
                position_type=position_type,
                current_level_id=level_id,
                assessment_details=assessment_details,
                certifier_id=certifier_id,
                certified_date=certified_date or date.today(),
                valid_until=valid_until,
                status=QualificationStatusEnum.APPROVED
            )
            db.add(qualification)

        db.commit()
        db.refresh(qualification)
        return qualification

    @staticmethod
    def assess_employee(
        db: Session,
        employee_id: int,
        assessment_type: str,
        scores: Dict[str, Any],
        assessor_id: Optional[int] = None,
        qualification_id: Optional[int] = None,
        assessment_period: Optional[str] = None,
        comments: Optional[str] = None
    ) -> QualificationAssessment:
        """评估员工任职资格"""
        # 计算综合得分
        total_score = QualificationService._calculate_total_score(scores)

        # 判断评估结果
        result = QualificationService._determine_result(total_score)

        assessment = QualificationAssessment(
            employee_id=employee_id,
            qualification_id=qualification_id,
            assessment_period=assessment_period,
            assessment_type=assessment_type,
            scores=scores,
            total_score=total_score,
            result=result,
            assessor_id=assessor_id,
            comments=comments,
            assessed_at=datetime.now()
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        return assessment

    @staticmethod
    def check_promotion_eligibility(
        db: Session,
        employee_id: int,
        target_level_id: int
    ) -> Dict[str, Any]:
        """检查晋升资格"""
        # 获取当前任职资格
        qualification = QualificationService.get_employee_qualification(db, employee_id)
        if not qualification:
            return {
                'eligible': False,
                'reason': '员工尚未获得任职资格认证'
            }

        # 获取当前等级和目标等级
        current_level = db.query(QualificationLevel).filter(
            QualificationLevel.id == qualification.current_level_id
        ).first()
        target_level = db.query(QualificationLevel).filter(
            QualificationLevel.id == target_level_id
        ).first()

        if not current_level or not target_level:
            return {
                'eligible': False,
                'reason': '等级信息不存在'
            }

        # 检查是否满足晋升条件
        if target_level.level_order <= current_level.level_order:
            return {
                'eligible': False,
                'reason': '目标等级不能低于或等于当前等级'
            }

        # 检查是否有最近的评估记录
        recent_assessment = db.query(QualificationAssessment).filter(
            QualificationAssessment.employee_id == employee_id,
            QualificationAssessment.qualification_id == qualification.id
        ).order_by(desc(QualificationAssessment.assessed_at)).first()

        if not recent_assessment:
            return {
                'eligible': False,
                'reason': '需要先完成任职资格评估'
            }

        # 检查评估结果
        if recent_assessment.result != AssessmentResultEnum.PASS:
            return {
                'eligible': False,
                'reason': f'最近一次评估结果为 {recent_assessment.result}，需要达到 PASS 才能晋升'
            }

        # 检查综合得分是否达到目标等级要求（假设需要80分以上）
        if recent_assessment.total_score and recent_assessment.total_score < 80:
            return {
                'eligible': False,
                'reason': f'综合得分 {recent_assessment.total_score} 未达到晋升要求（需要80分以上）'
            }

        return {
            'eligible': True,
            'current_level': current_level.level_code,
            'target_level': target_level.level_code,
            'recent_score': float(recent_assessment.total_score) if recent_assessment.total_score else None
        }

    @staticmethod
    def _calculate_total_score(scores: Dict[str, Any]) -> Decimal:
        """计算综合得分"""
        # 获取能力模型（需要从评估详情中获取权重信息）
        # 这里简化处理，假设各维度权重相等
        if not scores:
            return Decimal('0.00')

        total = sum(float(v) if isinstance(v, (int, float)) else 0 for v in scores.values())
        count = len(scores)

        if count == 0:
            return Decimal('0.00')

        return Decimal(str(total / count)).quantize(Decimal('0.01'))

    @staticmethod
    def _determine_result(total_score: Decimal) -> str:
        """判断评估结果"""
        score = float(total_score)
        if score >= 80:
            return AssessmentResultEnum.PASS
        elif score >= 60:
            return AssessmentResultEnum.PARTIAL
        else:
            return AssessmentResultEnum.FAIL

    @staticmethod
    def get_assessment_history(
        db: Session,
        employee_id: int,
        qualification_id: Optional[int] = None
    ) -> List[QualificationAssessment]:
        """获取员工评估历史"""
        query = db.query(QualificationAssessment).filter(
            QualificationAssessment.employee_id == employee_id
        )

        if qualification_id:
            query = query.filter(QualificationAssessment.qualification_id == qualification_id)

        return query.order_by(desc(QualificationAssessment.assessed_at)).all()

    @staticmethod
    def get_competency_models_by_position(
        db: Session,
        position_type: str,
        position_subtype: Optional[str] = None
    ) -> List[PositionCompetencyModel]:
        """获取指定岗位的所有能力模型"""
        query = db.query(PositionCompetencyModel).filter(
            PositionCompetencyModel.position_type == position_type,
            PositionCompetencyModel.is_active
        )

        if position_subtype:
            query = query.filter(PositionCompetencyModel.position_subtype == position_subtype)

        return query.join(QualificationLevel).order_by(
            QualificationLevel.level_order
        ).all()






