# -*- coding: utf-8 -*-
"""
技术评估模板服务

提供评估模板的 CRUD 操作、评估项管理和模板应用功能。
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.sales.assessment_template import (
    AssessmentDimensionEnum,
    AssessmentItem,
    AssessmentRisk,
    AssessmentTemplate,
    AssessmentVersion,
    RiskLevelEnum,
    RiskStatusEnum,
    TemplateCategoryEnum,
)
from app.models.sales.technical_assessment import TechnicalAssessment

logger = logging.getLogger(__name__)


class AssessmentTemplateService:
    """评估模板服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 模板 CRUD ====================

    def create_template(
        self,
        template_code: str,
        template_name: str,
        category: str = TemplateCategoryEnum.STANDARD,
        description: Optional[str] = None,
        dimension_weights: Optional[Dict] = None,
        veto_rules: Optional[List[Dict]] = None,
        score_thresholds: Optional[Dict] = None,
        created_by: Optional[int] = None,
    ) -> AssessmentTemplate:
        """创建评估模板"""
        # 使用默认权重（如果未提供）
        if dimension_weights is None:
            dimension_weights = AssessmentTemplate.get_default_weights()

        # 默认评分阈值
        if score_thresholds is None:
            score_thresholds = {
                "excellent": 90,  # ≥90 推荐立项
                "good": 75,  # ≥75 有条件立项
                "fair": 60,  # ≥60 暂缓
                "poor": 0,  # <60 不建议立项
            }

        template = AssessmentTemplate(
            template_code=template_code,
            template_name=template_name,
            category=category,
            description=description,
            dimension_weights=dimension_weights,
            veto_rules=veto_rules or [],
            score_thresholds=score_thresholds,
            created_by=created_by,
            is_active=True,
            is_default=False,
            version="V1.0",
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"创建评估模板: {template_code}")
        return template

    def get_template(
        self, template_id: int, include_items: bool = True
    ) -> Optional[AssessmentTemplate]:
        """获取评估模板"""
        query = self.db.query(AssessmentTemplate).filter(
            AssessmentTemplate.id == template_id
        )

        if include_items:
            query = query.options(joinedload(AssessmentTemplate.items))

        return query.first()

    def get_template_by_code(self, template_code: str) -> Optional[AssessmentTemplate]:
        """根据编码获取评估模板"""
        return (
            self.db.query(AssessmentTemplate)
            .filter(AssessmentTemplate.template_code == template_code)
            .options(joinedload(AssessmentTemplate.items))
            .first()
        )

    def list_templates(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[AssessmentTemplate], int]:
        """列出评估模板"""
        query = self.db.query(AssessmentTemplate)

        if category:
            query = query.filter(AssessmentTemplate.category == category)
        if is_active is not None:
            query = query.filter(AssessmentTemplate.is_active == is_active)

        total = query.count()
        templates = (
            query.order_by(AssessmentTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return templates, total

    def update_template(
        self,
        template_id: int,
        **kwargs,
    ) -> Optional[AssessmentTemplate]:
        """更新评估模板"""
        template = self.get_template(template_id, include_items=False)
        if not template:
            return None

        # 更新允许的字段
        allowed_fields = {
            "template_name",
            "category",
            "description",
            "dimension_weights",
            "veto_rules",
            "score_thresholds",
            "is_active",
            "is_default",
        }

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(template, key, value)

        template.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(template)

        logger.info(f"更新评估模板: {template.template_code}")
        return template

    def delete_template(self, template_id: int) -> bool:
        """删除评估模板（软删除）"""
        template = self.get_template(template_id, include_items=False)
        if not template:
            return False

        template.is_active = False
        template.updated_at = datetime.now()
        self.db.commit()

        logger.info(f"删除评估模板: {template.template_code}")
        return True

    def set_default_template(
        self, template_id: int, category: str
    ) -> Optional[AssessmentTemplate]:
        """设置默认模板"""
        # 取消当前类别的默认模板
        self.db.query(AssessmentTemplate).filter(
            and_(
                AssessmentTemplate.category == category,
                AssessmentTemplate.is_default == True,
            )
        ).update({"is_default": False})

        # 设置新的默认模板
        template = self.get_template(template_id, include_items=False)
        if template and template.category == category:
            template.is_default = True
            self.db.commit()
            self.db.refresh(template)
            return template

        return None

    def get_default_template(
        self, category: str = TemplateCategoryEnum.STANDARD
    ) -> Optional[AssessmentTemplate]:
        """获取默认模板"""
        return (
            self.db.query(AssessmentTemplate)
            .filter(
                and_(
                    AssessmentTemplate.category == category,
                    AssessmentTemplate.is_default == True,
                    AssessmentTemplate.is_active == True,
                )
            )
            .options(joinedload(AssessmentTemplate.items))
            .first()
        )

    # ==================== 评估项管理 ====================

    def add_assessment_item(
        self,
        template_id: int,
        item_code: str,
        item_name: str,
        dimension: str,
        max_score: int = 10,
        weight: float = 1.0,
        description: Optional[str] = None,
        scoring_criteria: Optional[List[Dict]] = None,
        is_veto_item: bool = False,
        veto_threshold: Optional[int] = None,
        is_required: bool = True,
        sort_order: int = 0,
    ) -> AssessmentItem:
        """添加评估项"""
        item = AssessmentItem(
            template_id=template_id,
            item_code=item_code,
            item_name=item_name,
            dimension=dimension,
            max_score=max_score,
            weight=weight,
            description=description,
            scoring_criteria=scoring_criteria,
            is_veto_item=is_veto_item,
            veto_threshold=veto_threshold,
            is_required=is_required,
            sort_order=sort_order,
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        logger.info(f"添加评估项: {item_code} to template {template_id}")
        return item

    def get_items_by_template(
        self, template_id: int, dimension: Optional[str] = None
    ) -> List[AssessmentItem]:
        """获取模板的评估项"""
        query = self.db.query(AssessmentItem).filter(
            AssessmentItem.template_id == template_id
        )

        if dimension:
            query = query.filter(AssessmentItem.dimension == dimension)

        return query.order_by(
            AssessmentItem.dimension, AssessmentItem.sort_order
        ).all()

    def update_assessment_item(
        self, item_id: int, **kwargs
    ) -> Optional[AssessmentItem]:
        """更新评估项"""
        item = self.db.query(AssessmentItem).filter(AssessmentItem.id == item_id).first()
        if not item:
            return None

        allowed_fields = {
            "item_name",
            "description",
            "max_score",
            "weight",
            "scoring_criteria",
            "is_veto_item",
            "veto_threshold",
            "is_required",
            "sort_order",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(item, key, value)

        item.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(item)

        return item

    def delete_assessment_item(self, item_id: int) -> bool:
        """删除评估项"""
        item = self.db.query(AssessmentItem).filter(AssessmentItem.id == item_id).first()
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()

        logger.info(f"删除评估项: {item_id}")
        return True

    def batch_add_items(
        self, template_id: int, items: List[Dict]
    ) -> List[AssessmentItem]:
        """批量添加评估项"""
        created_items = []

        for item_data in items:
            item = AssessmentItem(
                template_id=template_id,
                item_code=item_data["item_code"],
                item_name=item_data["item_name"],
                dimension=item_data["dimension"],
                max_score=item_data.get("max_score", 10),
                weight=item_data.get("weight", 1.0),
                description=item_data.get("description"),
                scoring_criteria=item_data.get("scoring_criteria"),
                is_veto_item=item_data.get("is_veto_item", False),
                veto_threshold=item_data.get("veto_threshold"),
                is_required=item_data.get("is_required", True),
                sort_order=item_data.get("sort_order", 0),
            )
            self.db.add(item)
            created_items.append(item)

        self.db.commit()

        # 刷新获取 ID
        for item in created_items:
            self.db.refresh(item)

        logger.info(f"批量添加 {len(created_items)} 个评估项到模板 {template_id}")
        return created_items


class AssessmentRiskService:
    """评估风险服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_risk(
        self,
        assessment_id: int,
        risk_title: str,
        risk_description: str,
        risk_category: Optional[str] = None,
        probability: str = "MEDIUM",
        impact: str = "MEDIUM",
        mitigation_plan: Optional[str] = None,
        contingency_plan: Optional[str] = None,
        owner_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
    ) -> AssessmentRisk:
        """创建风险记录"""
        # 生成风险编码
        risk_code = self._generate_risk_code()

        risk = AssessmentRisk(
            assessment_id=assessment_id,
            risk_code=risk_code,
            risk_title=risk_title,
            risk_description=risk_description,
            risk_category=risk_category,
            probability=probability,
            impact=impact,
            mitigation_plan=mitigation_plan,
            contingency_plan=contingency_plan,
            owner_id=owner_id,
            due_date=due_date,
            status=RiskStatusEnum.OPEN,
        )

        # 计算风险等级和分值
        risk.risk_score = risk.calculate_risk_score()
        risk.risk_level = self._determine_risk_level(risk.risk_score)

        self.db.add(risk)
        self.db.commit()
        self.db.refresh(risk)

        logger.info(f"创建风险记录: {risk_code}")
        return risk

    def _generate_risk_code(self) -> str:
        """生成风险编码"""
        today = datetime.now()
        prefix = f"RSK{today.strftime('%Y%m%d')}"

        # 查找今天的最后一个编码
        last_risk = (
            self.db.query(AssessmentRisk)
            .filter(AssessmentRisk.risk_code.like(f"{prefix}%"))
            .order_by(AssessmentRisk.risk_code.desc())
            .first()
        )

        if last_risk:
            seq = int(last_risk.risk_code[-4:]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    def _determine_risk_level(self, risk_score: int) -> str:
        """根据风险分值确定风险等级"""
        if risk_score >= 6:
            return RiskLevelEnum.CRITICAL
        elif risk_score >= 4:
            return RiskLevelEnum.HIGH
        elif risk_score >= 2:
            return RiskLevelEnum.MEDIUM
        else:
            return RiskLevelEnum.LOW

    def get_risks_by_assessment(
        self, assessment_id: int, status: Optional[str] = None
    ) -> List[AssessmentRisk]:
        """获取评估的风险列表"""
        query = self.db.query(AssessmentRisk).filter(
            AssessmentRisk.assessment_id == assessment_id
        )

        if status:
            query = query.filter(AssessmentRisk.status == status)

        return query.order_by(AssessmentRisk.risk_score.desc()).all()

    def update_risk_status(
        self,
        risk_id: int,
        status: str,
        resolution_notes: Optional[str] = None,
    ) -> Optional[AssessmentRisk]:
        """更新风险状态"""
        risk = self.db.query(AssessmentRisk).filter(AssessmentRisk.id == risk_id).first()
        if not risk:
            return None

        risk.status = status

        if status == RiskStatusEnum.RESOLVED:
            risk.resolved_at = datetime.now()
            risk.resolution_notes = resolution_notes

        risk.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(risk)

        logger.info(f"更新风险状态: {risk.risk_code} -> {status}")
        return risk

    def get_high_risks(self, limit: int = 10) -> List[AssessmentRisk]:
        """获取高风险列表"""
        return (
            self.db.query(AssessmentRisk)
            .filter(
                and_(
                    AssessmentRisk.risk_level.in_(
                        [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]
                    ),
                    AssessmentRisk.status.in_(
                        [RiskStatusEnum.OPEN, RiskStatusEnum.MITIGATING]
                    ),
                )
            )
            .order_by(AssessmentRisk.risk_score.desc())
            .limit(limit)
            .all()
        )


class AssessmentVersionService:
    """评估版本服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_version(
        self,
        assessment_id: int,
        version_note: Optional[str] = None,
        evaluator_id: Optional[int] = None,
    ) -> AssessmentVersion:
        """创建评估版本快照"""
        # 获取评估数据
        assessment = (
            self.db.query(TechnicalAssessment)
            .filter(TechnicalAssessment.id == assessment_id)
            .first()
        )
        if not assessment:
            raise ValueError(f"评估不存在: {assessment_id}")

        # 生成版本号
        version_no = self._generate_version_no(assessment_id)

        # 创建快照
        snapshot_data = {
            "source_type": assessment.source_type,
            "source_id": assessment.source_id,
            "status": assessment.status,
            "veto_triggered": assessment.veto_triggered,
            "veto_rules": json.loads(assessment.veto_rules)
            if assessment.veto_rules
            else None,
            "risks": json.loads(assessment.risks) if assessment.risks else None,
            "conditions": json.loads(assessment.conditions)
            if assessment.conditions
            else None,
            "ai_analysis": assessment.ai_analysis,
        }

        version = AssessmentVersion(
            assessment_id=assessment_id,
            version_no=version_no,
            version_note=version_note,
            snapshot_data=snapshot_data,
            dimension_scores=json.loads(assessment.dimension_scores)
            if assessment.dimension_scores
            else None,
            total_score=assessment.total_score,
            decision=assessment.decision,
            evaluator_id=evaluator_id or assessment.evaluator_id,
            evaluated_at=datetime.now(),
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        logger.info(f"创建评估版本: {assessment_id} - {version_no}")
        return version

    def _generate_version_no(self, assessment_id: int) -> str:
        """生成版本号"""
        # 查找最后一个版本
        last_version = (
            self.db.query(AssessmentVersion)
            .filter(AssessmentVersion.assessment_id == assessment_id)
            .order_by(AssessmentVersion.version_no.desc())
            .first()
        )

        if last_version:
            # 解析版本号并递增
            parts = last_version.version_no.split(".")
            major, minor = int(parts[0][1:]), int(parts[1])
            return f"V{major}.{minor + 1}"
        else:
            return "V1.0"

    def get_versions(self, assessment_id: int) -> List[AssessmentVersion]:
        """获取评估的所有版本"""
        return (
            self.db.query(AssessmentVersion)
            .filter(AssessmentVersion.assessment_id == assessment_id)
            .order_by(AssessmentVersion.version_no.desc())
            .all()
        )

    def get_version(
        self, assessment_id: int, version_no: str
    ) -> Optional[AssessmentVersion]:
        """获取特定版本"""
        return (
            self.db.query(AssessmentVersion)
            .filter(
                and_(
                    AssessmentVersion.assessment_id == assessment_id,
                    AssessmentVersion.version_no == version_no,
                )
            )
            .first()
        )

    def compare_versions(
        self, assessment_id: int, version_no_1: str, version_no_2: str
    ) -> Dict[str, Any]:
        """比较两个版本"""
        v1 = self.get_version(assessment_id, version_no_1)
        v2 = self.get_version(assessment_id, version_no_2)

        if not v1 or not v2:
            raise ValueError("版本不存在")

        return {
            "version_1": version_no_1,
            "version_2": version_no_2,
            "score_change": (v2.total_score or 0) - (v1.total_score or 0),
            "decision_change": {
                "from": v1.decision,
                "to": v2.decision,
            },
            "dimension_score_changes": self._compare_dimension_scores(
                v1.dimension_scores or {}, v2.dimension_scores or {}
            ),
        }

    def _compare_dimension_scores(
        self, scores_1: Dict, scores_2: Dict
    ) -> Dict[str, Dict]:
        """比较维度分数"""
        changes = {}
        all_dims = set(scores_1.keys()) | set(scores_2.keys())

        for dim in all_dims:
            s1 = scores_1.get(dim, 0)
            s2 = scores_2.get(dim, 0)
            if s1 != s2:
                changes[dim] = {
                    "from": s1,
                    "to": s2,
                    "change": s2 - s1,
                }

        return changes
