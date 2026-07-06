# -*- coding: utf-8 -*-
"""
项目等级毛利率底线服务

对应《项目经理毛利率提升操作手册》Sheet9 的红线规则：
  S级(全新平台) >= 40%
  A级(重大定制) >= 35%
  B级(改型升级) >= 30%
  C级(标准品)   >= 25%
  红线(任何项目) >= 20%（低于须总经理特批）

- get_target_margin(project_level)：按等级取目标毛利率（用于 ProfitAnalysisService）
- get_margin_floor(project_level)：取底线（最低 acceptable）
- ensure_default_levels()：首次运行时把手册的红线值初始化到 MarginAlertConfig
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sales.margin_alert import MarginAlertConfig

logger = logging.getLogger(__name__)

# 手册 Sheet9 的分级毛利率底线（首次初始化用，可被 DB 配置覆盖）
DEFAULT_LEVEL_MARGINS = {
    "S": {"standard": 40.0, "minimum": 30.0, "desc": "全新平台开发（首台套）"},
    "A": {"standard": 35.0, "minimum": 25.0, "desc": "重大定制化项目"},
    "B": {"standard": 30.0, "minimum": 22.0, "desc": "改型/升级项目"},
    "C": {"standard": 25.0, "minimum": 20.0, "desc": "标准品/小批量"},
}
# 通用底线（无等级或低于 C）
FLOOR_MARGIN = 20.0
DEFAULT_TARGET_MARGIN = 25.0


def get_target_margin(
    db: Session, project_level: Optional[str] = None
) -> float:
    """按项目等级取目标毛利率。

    优先读 MarginAlertConfig（project_level 匹配）；
    无配置则用手册默认值；无等级用 25%。
    """
    if not project_level:
        # 无等级：先查 is_default 配置，否则用默认
        cfg = (
            db.query(MarginAlertConfig)
            .filter(
                MarginAlertConfig.is_default.is_(True),
                MarginAlertConfig.is_active.is_(True),
                MarginAlertConfig.project_level.is_(None),
            )
            .first()
        )
        if cfg and cfg.standard_margin:
            return float(cfg.standard_margin)
        return DEFAULT_TARGET_MARGIN

    # 按等级查
    cfg = (
        db.query(MarginAlertConfig)
        .filter(
            MarginAlertConfig.project_level == project_level,
            MarginAlertConfig.is_active.is_(True),
        )
        .first()
    )
    if cfg and cfg.standard_margin:
        return float(cfg.standard_margin)

    # fallback 到手册默认值
    return DEFAULT_LEVEL_MARGINS.get(project_level, {}).get(
        "standard", DEFAULT_TARGET_MARGIN
    )


def get_margin_floor(
    db: Session, project_level: Optional[str] = None
) -> float:
    """按项目等级取毛利率底线（最低 acceptable，低于须特批）。"""
    if not project_level:
        return FLOOR_MARGIN

    cfg = (
        db.query(MarginAlertConfig)
        .filter(
            MarginAlertConfig.project_level == project_level,
            MarginAlertConfig.is_active.is_(True),
        )
        .first()
    )
    if cfg and cfg.minimum_margin:
        return float(cfg.minimum_margin)

    return DEFAULT_LEVEL_MARGINS.get(project_level, {}).get(
        "minimum", FLOOR_MARGIN
    )


def ensure_default_levels(db: Session) -> int:
    """首次运行时把手册的分级毛利率底线初始化到 DB。

    幂等：已存在的等级跳过。返回新建条数。
    """
    created = 0
    for level, conf in DEFAULT_LEVEL_MARGINS.items():
        existing = (
            db.query(MarginAlertConfig)
            .filter(MarginAlertConfig.project_level == level)
            .first()
        )
        if existing:
            continue
        cfg = MarginAlertConfig(
            name=f"{level}级项目毛利率底线",
            code=f"PROJECT_LEVEL_{level}",
            description=conf["desc"],
            project_level=level,
            standard_margin=conf["standard"],
            warning_margin=conf["standard"],
            alert_margin=conf["minimum"],
            minimum_margin=conf["minimum"],
            is_active=True,
            is_default=False,
            priority=10,
        )
        db.add(cfg)
        created += 1
    if created:
        db.commit()
        logger.info("已初始化 %d 个项目等级毛利率底线", created)
    return created


def get_level_summary(db: Session) -> list:
    """所有等级的底线汇总（给 Dashboard / 端点用）。"""
    ensure_default_levels(db)
    rows = (
        db.query(MarginAlertConfig)
        .filter(
            MarginAlertConfig.project_level.isnot(None),
            MarginAlertConfig.is_active.is_(True),
        )
        .order_by(MarginAlertConfig.project_level)
        .all()
    )
    result = []
    for cfg in rows:
        result.append(
            {
                "project_level": cfg.project_level,
                "name": cfg.name,
                "description": cfg.description,
                "standard_margin": float(cfg.standard_margin) if cfg.standard_margin else None,
                "minimum_margin": float(cfg.minimum_margin) if cfg.minimum_margin else None,
            }
        )
    return result
