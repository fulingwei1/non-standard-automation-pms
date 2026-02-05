# -*- coding: utf-8 -*-
"""
应用启动时的数据初始化模块

包含预置模板、API权限等基础数据的自动初始化逻辑
"""

import logging
import os
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import text

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


def init_api_permissions(db: Session) -> int:
    """
    初始化 API 权限种子数据

    从 SQL 迁移文件加载权限定义和角色-权限映射。
    此函数是幂等的（使用 INSERT OR IGNORE）。

    Args:
        db: 数据库会话

    Returns:
        int: 新创建的权限数量
    """
    # 检查是否已有权限数据
    from app.models.user import ApiPermission
    existing_count = db.query(ApiPermission).count()
    if existing_count > 0:
        logger.debug(f"API权限表已有 {existing_count} 条记录，跳过初始化")
        return 0

    # 读取并执行种子数据 SQL
    seed_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "migrations",
        "20260205_api_permissions_seed_sqlite.sql",
    )

    if not os.path.exists(seed_file):
        logger.warning(f"权限种子文件不存在: {seed_file}")
        return 0

    try:
        with open(seed_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # 按语句分割执行（跳过注释和空行）
        statements = []
        current_stmt = []
        for line in sql_content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            current_stmt.append(line)
            if stripped.endswith(";"):
                statements.append("\n".join(current_stmt))
                current_stmt = []

        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    db.execute(text(stmt))
                except Exception as e:
                    logger.warning(f"执行权限SQL语句失败（可能已存在）: {e}")

        db.flush()
        new_count = db.query(ApiPermission).count()
        logger.info(f"API权限初始化完成，共 {new_count} 条权限记录")
        return new_count
    except Exception as e:
        logger.error(f"API权限种子数据加载失败: {e}")
        return 0


def init_all_data():
    """
    初始化所有基础数据

    在应用启动时调用，包含：
    - 预置阶段模板
    - API权限种子数据
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

        # 初始化 API 权限种子数据
        perm_count = init_api_permissions(db)
        if perm_count > 0:
            db.commit()
            logger.info(f"API权限初始化完成，新建 {perm_count} 条权限")
        else:
            logger.info("API权限已存在或无需初始化")

    except Exception as e:
        db.rollback()
        logger.error(f"基础数据初始化失败: {e}")
    finally:
        db.close()

    logger.info("基础数据初始化完成")
