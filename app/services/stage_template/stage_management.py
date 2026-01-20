# -*- coding: utf-8 -*-
"""
阶段管理模块
提供阶段定义的CRUD和排序功能
"""

from typing import List, Optional

from sqlalchemy import and_

from app.models.stage_template import StageDefinition, StageTemplate


class StageManagementMixin:
    """阶段管理功能混入类"""

    def add_stage(
        self,
        template_id: int,
        stage_code: str,
        stage_name: str,
        sequence: int = 0,
        estimated_days: Optional[int] = None,
        description: Optional[str] = None,
        is_required: bool = True,
    ) -> StageDefinition:
        """
        添加阶段定义

        Args:
            template_id: 模板ID
            stage_code: 阶段编码
            stage_name: 阶段名称
            sequence: 排序序号
            estimated_days: 预计工期（天）
            description: 阶段描述
            is_required: 是否必需阶段

        Returns:
            StageDefinition: 创建的阶段定义
        """
        # 检查模板存在
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 检查编码在模板内唯一
        existing = self.db.query(StageDefinition).filter(
            and_(
                StageDefinition.template_id == template_id,
                StageDefinition.stage_code == stage_code
            )
        ).first()
        if existing:
            raise ValueError(f"阶段编码 {stage_code} 在该模板中已存在")

        stage = StageDefinition(
            template_id=template_id,
            stage_code=stage_code,
            stage_name=stage_name,
            sequence=sequence,
            estimated_days=estimated_days,
            description=description,
            is_required=is_required,
        )
        self.db.add(stage)
        self.db.flush()
        return stage

    def update_stage(
        self,
        stage_id: int,
        **kwargs
    ) -> Optional[StageDefinition]:
        """更新阶段定义"""
        stage = self.db.query(StageDefinition).filter(
            StageDefinition.id == stage_id
        ).first()

        if not stage:
            return None

        for key, value in kwargs.items():
            if hasattr(stage, key) and key not in ["id", "template_id", "created_at"]:
                setattr(stage, key, value)

        self.db.flush()
        return stage

    def delete_stage(self, stage_id: int) -> bool:
        """删除阶段定义（级联删除节点）"""
        stage = self.db.query(StageDefinition).filter(
            StageDefinition.id == stage_id
        ).first()

        if not stage:
            return False

        self.db.delete(stage)
        return True

    def reorder_stages(self, template_id: int, stage_ids: List[int]) -> bool:
        """重新排序阶段"""
        for index, stage_id in enumerate(stage_ids):
            self.db.query(StageDefinition).filter(
                and_(
                    StageDefinition.id == stage_id,
                    StageDefinition.template_id == template_id
                )
            ).update({"sequence": index})
        self.db.flush()
        return True
