# -*- coding: utf-8 -*-
"""
OTD 阈值配置服务

- get_active_config(db)：取运行时生效配置（is_default=True 且 is_active=True），
  DB 无则返回内存默认实例（保证首次运行无需手动建配置）
- update_default_config(db, payload, user_id)：更新或创建默认配置
- build_default_config()：构造内存默认实例（fallback 用）

scan service 在 __init__ 时调 get_active_config 一次性加载，各检测器读 config.xxx。
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.otd_threshold_config import (
    DEFAULT_SCAN_LIMIT,
    DEFAULT_STAGES_IN_DELIVERY,
    DEFAULT_STATUS_SETS,
    OtdThresholdConfig,
)
from app.schemas.otd_threshold import OtdThresholdConfigUpdate

logger = logging.getLogger(__name__)

# 默认配置行的固定 code（is_default=True 的唯一标识）
DEFAULT_CONFIG_CODE = "OTD_DEFAULT"


def build_default_config() -> OtdThresholdConfig:
    """构造内存默认配置实例（DB 无配置时 fallback）。

    值与原硬编码阈值完全一致，保证行为零回归。
    """
    return OtdThresholdConfig(
        name="OTD 默认阈值配置",
        code=DEFAULT_CONFIG_CODE,
        description="OTD 11 维风险检测默认阈值（首次运行自动生成，管理员可修改）",
        is_active=True,
        is_default=True,
        priority=0,
        # 扫描范围
        scan_limit=DEFAULT_SCAN_LIMIT,
        stages_in_delivery=list(DEFAULT_STAGES_IN_DELIVERY),
        # 维度1 采购延期
        procurement_overdue_medium_days=7,
        procurement_overdue_high_days=15,
        procurement_overdue_critical_days=30,
        # 维度2 图纸未冻结
        design_freeze_check_from_stage="S3",
        design_freeze_high_stage="S4",
        design_freeze_critical_stage="S5",
        design_review_pass_conclusions=["pass", "pass_with_condition"],
        # 维度3 客户变更
        change_window_short_days=30,
        change_window_long_days=90,
        change_critical_count=5,
        change_high_count=3,
        # 维度5 调试反复
        debug_window_days=30,
        debug_high_count=5,
        debug_medium_count=3,
        debug_categories=["ACCEPTANCE", "QUALITY", "TECHNICAL"],
        # 维度6 验收资料
        acceptance_near_window_days=60,
        acceptance_high_window_days=30,
        acceptance_check_from_stage="S6",
        acceptance_doc_keywords=["交付物", "文档", "验收", "客户签署", "报告"],
        # 维度7 回款
        payment_upcoming_days=7,
        # 维度8 关键节点
        key_milestone_critical_days=30,
        key_milestone_critical_count=2,
        # 维度9 进度滞后
        progress_medium_threshold=-15,
        progress_high_threshold=-25,
        # 维度10 毛利偏差
        margin_medium_threshold=-3,
        margin_high_threshold=-5,
        margin_critical_threshold=-10,
        # 维度11 未关闭事项
        open_items_high_count=10,
        open_items_medium_count=5,
        # 状态集合
        status_sets=dict(DEFAULT_STATUS_SETS),
    )


def get_active_config(db: Session) -> OtdThresholdConfig:
    """取运行时生效的阈值配置。

    优先取 DB 中 is_default=True 且 is_active=True 的行；
    DB 无配置则返回内存默认实例（不写库，只读用）。
    """
    try:
        config = (
            db.query(OtdThresholdConfig)
            .filter(
                OtdThresholdConfig.is_default.is_(True),
                OtdThresholdConfig.is_active.is_(True),
            )
            .order_by(OtdThresholdConfig.priority.desc())
            .first()
        )
        if config:
            # 填充可能为 None 的字段为默认值（防止历史数据缺字段）
            _fill_defaults(config)
            return config
    except Exception as e:
        logger.warning("读取 OTD 阈值配置失败，使用代码默认值: %s", e)

    # fallback：内存默认实例（不持久化）
    return build_default_config()


def update_default_config(
    db: Session,
    payload: OtdThresholdConfigUpdate,
    user_id: Optional[int] = None,
) -> OtdThresholdConfig:
    """更新或创建默认配置行。

    不存在则建（首次配置时）；存在则更新（部分字段）。
    返回持久化后的配置对象。
    """
    config = (
        db.query(OtdThresholdConfig)
        .filter(OtdThresholdConfig.code == DEFAULT_CONFIG_CODE)
        .first()
    )

    if config is None:
        # 从内存默认值起步，再覆盖 payload 传入的字段
        config = build_default_config()
        config.created_by = user_id
        db.add(config)

    # 应用 payload 中非 None 的字段（部分更新）
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(config, field) and value is not None:
            setattr(config, field, value)

    db.commit()
    db.refresh(config)
    _fill_defaults(config)
    logger.info(
        "OTD 阈值配置已更新 code=%s 字段数=%d by=%s",
        config.code,
        len(update_data),
        user_id,
    )
    return config


def _fill_defaults(config: OtdThresholdConfig) -> None:
    """把可能为 None 的关键字段填上默认值（防历史数据/部分更新缺失）。"""
    if config.scan_limit is None:
        config.scan_limit = DEFAULT_SCAN_LIMIT
    if not config.stages_in_delivery:
        config.stages_in_delivery = list(DEFAULT_STAGES_IN_DELIVERY)
    if not config.status_sets:
        config.status_sets = dict(DEFAULT_STATUS_SETS)
    if not config.design_review_pass_conclusions:
        config.design_review_pass_conclusions = ["pass", "pass_with_condition"]
    if not config.debug_categories:
        config.debug_categories = ["ACCEPTANCE", "QUALITY", "TECHNICAL"]
    if not config.acceptance_doc_keywords:
        config.acceptance_doc_keywords = ["交付物", "文档", "验收", "客户签署", "报告"]


def config_to_dict(config: OtdThresholdConfig) -> Dict[str, Any]:
    """转成 dict，便于日志/调试。"""
    return {
        c.name: getattr(config, c.name, None)
        for c in config.__table__.columns
        if c.name not in ("created_at", "updated_at")
    }
