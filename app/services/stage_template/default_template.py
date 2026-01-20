# -*- coding: utf-8 -*-
"""
默认模板管理模块
提供默认模板的查询和设置功能
"""

from typing import Optional

from sqlalchemy import and_

from app.models.enums import TemplateProjectTypeEnum
from app.models.stage_template import StageTemplate


class DefaultTemplateMixin:
    """默认模板管理功能混入类"""

    def get_default_template(
        self,
        project_type: str = TemplateProjectTypeEnum.CUSTOM.value
    ) -> Optional[StageTemplate]:
        """获取指定项目类型的默认模板"""
        return self.db.query(StageTemplate).filter(
            and_(
                StageTemplate.project_type == project_type,
                StageTemplate.is_default == True,
                StageTemplate.is_active == True
            )
        ).first()

    def set_default_template(self, template_id: int) -> StageTemplate:
        """设置模板为默认"""
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 取消同类型的其他默认模板
        self._clear_default_template(template.project_type)

        template.is_default = True
        self.db.flush()
        return template
