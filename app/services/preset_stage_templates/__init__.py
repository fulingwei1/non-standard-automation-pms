# -*- coding: utf-8 -*-
"""
预置阶段模板数据

包含三个初始模板：
1. TPL_STANDARD - 标准全流程（新产品完整流程）
2. TPL_QUICK - 简易快速开发（简单新产品）
3. TPL_REPEAT - 重复生产（老产品复制）
"""

from typing import Any, Dict, List, Optional

from .templates.quick import QUICK_TEMPLATE
from .templates.repeat import REPEAT_TEMPLATE
from .templates.standard import STANDARD_TEMPLATE

# 所有预置模板列表
PRESET_TEMPLATES: List[Dict[str, Any]] = [
    STANDARD_TEMPLATE,
    QUICK_TEMPLATE,
    REPEAT_TEMPLATE,
]


def get_preset_template(template_code: str) -> Optional[Dict[str, Any]]:
    """根据模板编码获取预置模板数据"""
    for template in PRESET_TEMPLATES:
        if template["template_code"] == template_code:
            return template
    return None


def init_preset_templates(template_service) -> List:
    """
    初始化预置模板到数据库

    Args:
        template_service: StageTemplateService 实例

    Returns:
        List[StageTemplate]: 创建的模板列表
    """
    from app.models.stage_template import StageTemplate

    created_templates = []

    for template_data in PRESET_TEMPLATES:
        try:
            # 检查是否已存在
            existing = template_service.db.query(StageTemplate).filter(
                StageTemplate.template_code == template_data["template_code"]
            ).first()

            if not existing:
                template = template_service.import_template(template_data)
                # 设置为默认（第一个同类型模板）
                template_service.set_default_template(template.id)
                created_templates.append(template)
        except Exception as e:
            print(f"初始化模板 {template_data['template_code']} 失败: {e}")

    return created_templates


__all__ = [
    "STANDARD_TEMPLATE",
    "QUICK_TEMPLATE",
    "REPEAT_TEMPLATE",
    "PRESET_TEMPLATES",
    "get_preset_template",
    "init_preset_templates",
]
