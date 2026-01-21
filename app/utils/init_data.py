# -*- coding: utf-8 -*-
"""
应用启动时的数据初始化模块

包含预置模板等基础数据的自动初始化逻辑
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.models.base import SessionLocal
from app.models.stage_template import StageTemplate
from app.services.preset_stage_templates import PRESET_TEMPLATES
from app.services.stage_template import StageTemplateService

logger = logging.getLogger(__name__)


def init_preset_stage_templates(db: Session) -> List[StageTemplate]:
    """
    初始化预置阶段模板到数据库

    此函数是幂等的，已存在的模板不会重复创建

    Args:
        db: 数据库会话

    Returns:
        List[StageTemplate]: 新创建的模板列表
    """
    service = StageTemplateService(db)
    created_templates = []

    for template_data in PRESET_TEMPLATES:
        template_code = template_data["template_code"]

        # 检查是否已存在
        existing = db.query(StageTemplate).filter(
            StageTemplate.template_code == template_code
        ).first()

        if existing:
            logger.debug(f"预置模板 {template_code} 已存在，跳过")
            continue

        try:
            # 使用导入功能创建模板
            template = service.import_template(template_data)
            created_templates.append(template)
            logger.info(f"成功创建预置模板: {template_code} - {template_data['template_name']}")
        except Exception as e:
            logger.error(f"创建预置模板 {template_code} 失败: {e}")

    return created_templates


def init_all_data():
    """
    初始化所有基础数据

    在应用启动时调用，包含：
    - 预置阶段模板
    - （未来可扩展其他基础数据）
    """
    logger.info("开始初始化基础数据...")

    db = SessionLocal()
    try:
        # 初始化预置模板
        created = init_preset_stage_templates(db)
        if created:
            db.commit()
            logger.info(f"预置模板初始化完成，新建 {len(created)} 个模板")
        else:
            logger.info("所有预置模板已存在，无需初始化")

    except Exception as e:
        db.rollback()
        logger.error(f"基础数据初始化失败: {e}")
    finally:
        db.close()

    logger.info("基础数据初始化完成")
