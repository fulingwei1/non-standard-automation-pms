# -*- coding: utf-8 -*-
"""
规格匹配检查服务
用于在采购订单创建和BOM审批时自动检查规格匹配
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
from app.models.technical_spec import SpecMatchRecord, TechnicalSpecRequirement
from app.utils.spec_matcher import SpecMatcher


class SpecMatchService:
    """规格匹配检查服务"""

    def __init__(self):
        self.matcher = SpecMatcher()

    def check_po_item_spec_match(
        self,
        db: Session,
        project_id: int,
        po_item_id: int,
        material_code: str,
        specification: str,
        brand: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[SpecMatchRecord]:
        """
        检查采购订单行的规格匹配

        Args:
            db: 数据库会话
            project_id: 项目ID
            po_item_id: 采购订单行ID
            material_code: 物料编码
            specification: 规格型号
            brand: 品牌
            model: 型号

        Returns:
            匹配记录（如果不匹配则返回记录，匹配则返回None）
        """
        # 查找相关的规格要求
        requirements = db.query(TechnicalSpecRequirement).filter(
            TechnicalSpecRequirement.project_id == project_id
        ).filter(
            (TechnicalSpecRequirement.material_code == material_code) |
            (TechnicalSpecRequirement.material_code.is_(None))
        ).all()

        if not requirements:
            return None

        # 对每个规格要求进行匹配
        for req in requirements:
            # 如果规格要求有物料编码，必须匹配
            if req.material_code and req.material_code != material_code:
                continue

            match_result = self.matcher.match_specification(
                requirement=req,
                actual_spec=specification or '',
                actual_brand=brand,
                actual_model=model
            )

            # 创建匹配记录
            match_record = SpecMatchRecord(
                project_id=project_id,
                spec_requirement_id=req.id,
                match_type='PURCHASE_ORDER',
                match_target_id=po_item_id,
                match_status=match_result.match_status,
                match_score=match_result.match_score,
                differences=match_result.differences
            )
            db.add(match_record)
            db.flush()

            # 如果不匹配，生成预警
            if match_result.match_status == 'MISMATCHED':
                self._create_alert(
                    db=db,
                    project_id=project_id,
                    match_record_id=match_record.id,
                    requirement=req,
                    match_result=match_result
                )

            return match_record

        return None

    def check_bom_item_spec_match(
        self,
        db: Session,
        project_id: int,
        bom_item_id: int,
        material_code: str,
        specification: str,
        brand: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[SpecMatchRecord]:
        """
        检查BOM行的规格匹配

        Args:
            db: 数据库会话
            project_id: 项目ID
            bom_item_id: BOM行ID
            material_code: 物料编码
            specification: 规格型号
            brand: 品牌
            model: 型号

        Returns:
            匹配记录（如果不匹配则返回记录，匹配则返回None）
        """
        # 查找相关的规格要求
        requirements = db.query(TechnicalSpecRequirement).filter(
            TechnicalSpecRequirement.project_id == project_id
        ).filter(
            (TechnicalSpecRequirement.material_code == material_code) |
            (TechnicalSpecRequirement.material_code.is_(None))
        ).all()

        if not requirements:
            return None

        # 对每个规格要求进行匹配
        for req in requirements:
            # 如果规格要求有物料编码，必须匹配
            if req.material_code and req.material_code != material_code:
                continue

            match_result = self.matcher.match_specification(
                requirement=req,
                actual_spec=specification or '',
                actual_brand=brand,
                actual_model=model
            )

            # 创建匹配记录
            match_record = SpecMatchRecord(
                project_id=project_id,
                spec_requirement_id=req.id,
                match_type='BOM',
                match_target_id=bom_item_id,
                match_status=match_result.match_status,
                match_score=match_result.match_score,
                differences=match_result.differences
            )
            db.add(match_record)
            db.flush()

            # 如果不匹配，生成预警
            if match_result.match_status == 'MISMATCHED':
                self._create_alert(
                    db=db,
                    project_id=project_id,
                    match_record_id=match_record.id,
                    requirement=req,
                    match_result=match_result
                )

            return match_record

        return None

    def _create_alert(
        self,
        db: Session,
        project_id: int,
        match_record_id: int,
        requirement: TechnicalSpecRequirement,
        match_result
    ):
        """
        创建规格不匹配预警

        Args:
            db: 数据库会话
            project_id: 项目ID
            match_record_id: 匹配记录ID
            requirement: 规格要求
            match_result: 匹配结果
        """
        # 查找或创建预警规则
        rule = db.query(AlertRule).filter(
            AlertRule.rule_type == AlertRuleTypeEnum.SPECIFICATION_MISMATCH.value,
            AlertRule.is_enabled
        ).first()

        if not rule:
            # 创建默认预警规则
            rule = AlertRule(
                rule_code=f'SPEC_MISMATCH_{project_id}',
                rule_name='规格不匹配预警',
                rule_type=AlertRuleTypeEnum.SPECIFICATION_MISMATCH.value,
                target_type='SPEC_MATCH',
                condition_type='THRESHOLD',
                condition_operator='LT',
                threshold_value='80',
                alert_level=AlertLevelEnum.WARNING.value,
                is_enabled=True,
                is_system=True,
                description='当采购订单或BOM中的物料规格与技术规格书要求不匹配时触发预警'
            )
            db.add(rule)
            db.flush()

        # 生成预警编号
        today = datetime.now().strftime('%Y%m%d')
        count_query = db.query(AlertRecord)
        count_query = apply_like_filter(
            count_query,
            AlertRecord,
            f'AL{today}%',
            "alert_no",
            use_ilike=False,
        )
        count = count_query.count()
        alert_no = f'AL{today}{str(count + 1).zfill(4)}'

        # 创建预警记录
        alert = AlertRecord(
            alert_no=alert_no,
            rule_id=rule.id,
            target_type='SPEC_MATCH',
            target_id=match_record_id,
            target_no=f'MATCH-{match_record_id}',
            target_name=f'{requirement.material_name} 规格不匹配',
            project_id=project_id,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_title=f'物料 {requirement.material_name} 规格不匹配',
            alert_content=f'物料 {requirement.material_name} 的规格与技术规格书要求不一致。匹配度：{match_result.match_score}%。差异：{match_result.differences}',
            alert_data={
                'spec_requirement_id': requirement.id,
                'material_name': requirement.material_name,
                'required_spec': requirement.specification,
                'match_score': float(match_result.match_score) if match_result.match_score else 0,
                'differences': match_result.differences
            },
            status=AlertStatusEnum.PENDING.value,
            triggered_at=datetime.now()
        )
        db.add(alert)
        db.flush()

        # 更新匹配记录的预警ID
        match_record = db.query(SpecMatchRecord).filter(
            SpecMatchRecord.id == match_record_id
        ).first()
        if match_record:
            match_record.alert_id = alert.id



