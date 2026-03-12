# -*- coding: utf-8 -*-
"""
毛利率预警服务

提供毛利率预警的触发、审批和管理功能
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.sales import (
    MarginAlertConfig,
    MarginAlertLevelEnum,
    MarginAlertRecord,
    MarginAlertStatusEnum,
    Quote,
    QuoteVersion,
)
from app.utils.decimal_helpers import parse_decimal
from app.utils.status_helpers import assert_status_allows

logger = logging.getLogger(__name__)


class MarginAlertService:
    """毛利率预警服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 配置管理 ====================

    def get_applicable_config(
        self,
        customer_level: Optional[str] = None,
        project_type: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> Optional[MarginAlertConfig]:
        """
        获取适用的毛利率配置

        按优先级匹配：精确匹配 > 部分匹配 > 默认配置
        """
        # 尝试精确匹配
        if customer_level and project_type and industry:
            config = (
                self.db.query(MarginAlertConfig)
                .filter(
                    and_(
                        MarginAlertConfig.is_active == True,
                        MarginAlertConfig.customer_level == customer_level,
                        MarginAlertConfig.project_type == project_type,
                        MarginAlertConfig.industry == industry,
                    )
                )
                .order_by(desc(MarginAlertConfig.priority))
                .first()
            )
            if config:
                return config

        # 尝试客户等级匹配
        if customer_level:
            config = (
                self.db.query(MarginAlertConfig)
                .filter(
                    and_(
                        MarginAlertConfig.is_active == True,
                        MarginAlertConfig.customer_level == customer_level,
                        or_(
                            MarginAlertConfig.project_type.is_(None),
                            MarginAlertConfig.industry.is_(None),
                        ),
                    )
                )
                .order_by(desc(MarginAlertConfig.priority))
                .first()
            )
            if config:
                return config

        # 返回默认配置
        return (
            self.db.query(MarginAlertConfig)
            .filter(
                and_(
                    MarginAlertConfig.is_active == True,
                    MarginAlertConfig.is_default == True,
                )
            )
            .first()
        )

    def create_config(
        self,
        name: str,
        code: str,
        created_by: int,
        customer_level: Optional[str] = None,
        project_type: Optional[str] = None,
        industry: Optional[str] = None,
        standard_margin: float = 25.0,
        warning_margin: float = 20.0,
        alert_margin: float = 15.0,
        minimum_margin: float = 10.0,
        approval_rules: Optional[Dict] = None,
        is_default: bool = False,
    ) -> MarginAlertConfig:
        """创建毛利率预警配置"""
        config = MarginAlertConfig(
            name=name,
            code=code,
            customer_level=customer_level,
            project_type=project_type,
            industry=industry,
            standard_margin=parse_decimal(standard_margin),
            warning_margin=parse_decimal(warning_margin),
            alert_margin=parse_decimal(alert_margin),
            minimum_margin=parse_decimal(minimum_margin),
            approval_rules=approval_rules or {},
            is_active=True,
            is_default=is_default,
            created_by=created_by,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        logger.info(f"创建毛利率预警配置: {code}")
        return config

    def list_configs(
        self, is_active: Optional[bool] = True
    ) -> List[MarginAlertConfig]:
        """列出所有配置"""
        query = self.db.query(MarginAlertConfig)
        if is_active is not None:
            query = query.filter(MarginAlertConfig.is_active == is_active)
        return query.order_by(desc(MarginAlertConfig.priority)).all()

    # ==================== 预警检查 ====================

    def check_margin_alert(
        self,
        quote_id: int,
        quote_version_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        检查报价的毛利率是否触发预警

        Args:
            quote_id: 报价ID
            quote_version_id: 报价版本ID（可选，默认使用当前版本）

        Returns:
            预警检查结果
        """
        # 获取报价和版本
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValueError(f"报价不存在: {quote_id}")

        if quote_version_id:
            version = self.db.query(QuoteVersion).filter(
                QuoteVersion.id == quote_version_id
            ).first()
        else:
            version = quote.current_version

        if not version:
            raise ValueError("报价版本不存在")

        # 计算毛利率
        total_price = float(version.total_price or 0)
        total_cost = float(version.cost_total or 0)

        if total_price <= 0:
            return {
                "quote_id": quote_id,
                "alert_required": False,
                "message": "报价金额无效",
            }

        gross_margin = ((total_price - total_cost) / total_price) * 100

        # 获取适用配置
        config = self.get_applicable_config(
            customer_level=getattr(quote.customer, "level", None) if quote.customer else None,
        )

        if not config:
            return {
                "quote_id": quote_id,
                "alert_required": False,
                "message": "无适用的预警配置",
            }

        # 判断预警级别
        standard = float(config.standard_margin)
        warning = float(config.warning_margin)
        alert = float(config.alert_margin)
        minimum = float(config.minimum_margin)

        if gross_margin >= standard:
            level = MarginAlertLevelEnum.GREEN
            alert_required = False
        elif gross_margin >= warning:
            level = MarginAlertLevelEnum.YELLOW
            alert_required = True
        else:
            level = MarginAlertLevelEnum.RED
            alert_required = True

        # 如果低于最低毛利率，标记为需要特殊审批
        below_minimum = gross_margin < minimum

        return {
            "quote_id": quote_id,
            "quote_version_id": version.id,
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": round(gross_margin, 2),
            "alert_level": level.value,
            "alert_required": alert_required,
            "below_minimum": below_minimum,
            "config_id": config.id,
            "thresholds": {
                "standard": standard,
                "warning": warning,
                "alert": alert,
                "minimum": minimum,
            },
        }

    # ==================== 预警记录管理 ====================

    def create_alert_record(
        self,
        quote_id: int,
        requested_by: int,
        justification: str,
        quote_version_id: Optional[int] = None,
    ) -> MarginAlertRecord:
        """
        创建毛利率预警记录

        Args:
            quote_id: 报价ID
            requested_by: 申请人ID
            justification: 申请理由
            quote_version_id: 报价版本ID

        Returns:
            预警记录
        """
        # 检查毛利率
        check_result = self.check_margin_alert(quote_id, quote_version_id)

        if not check_result.get("alert_required"):
            raise ValueError("毛利率正常，无需创建预警记录")

        # 获取报价
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()

        # 创建记录
        record = MarginAlertRecord(
            quote_id=quote_id,
            quote_version_id=check_result.get("quote_version_id"),
            opportunity_id=quote.opportunity_id,
            customer_id=quote.customer_id,
            config_id=check_result.get("config_id"),
            alert_level=check_result["alert_level"],
            alert_reason=f"毛利率 {check_result['gross_margin']}% 低于阈值",
            total_price=parse_decimal(check_result["total_price"]),
            total_cost=parse_decimal(check_result["total_cost"]),
            gross_margin=parse_decimal(check_result["gross_margin"]),
            threshold_margin=parse_decimal(check_result["thresholds"]["warning"]),
            margin_gap=parse_decimal(
                check_result["thresholds"]["standard"] - check_result["gross_margin"]
            ),
            requested_by=requested_by,
            justification=justification,
            status=MarginAlertStatusEnum.PENDING.value,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(
            f"创建毛利率预警记录: 报价 {quote_id}, "
            f"毛利率 {check_result['gross_margin']}%, "
            f"级别 {check_result['alert_level']}"
        )

        return record

    def approve_alert(
        self,
        record_id: int,
        approved_by: int,
        comment: str,
        valid_days: int = 30,
    ) -> MarginAlertRecord:
        """
        审批通过预警记录

        Args:
            record_id: 记录ID
            approved_by: 审批人ID
            comment: 审批意见
            valid_days: 批准有效天数

        Returns:
            更新后的记录
        """
        record = self.db.query(MarginAlertRecord).filter(
            MarginAlertRecord.id == record_id
        ).first()

        if not record:
            raise ValueError(f"预警记录不存在: {record_id}")

        assert_status_allows(
            record, MarginAlertStatusEnum.PENDING.value,
            f"记录状态不允许审批: {record.status}"
        )

        # 更新记录
        record.status = MarginAlertStatusEnum.APPROVED.value
        record.approved_by = approved_by
        record.approved_at = datetime.now()
        record.approval_comment = comment
        record.valid_until = datetime.now().date() + timedelta(days=valid_days)

        # 添加审批历史
        history = record.approval_history or []
        history.append({
            "approver_id": approved_by,
            "action": "APPROVE",
            "comment": comment,
            "at": datetime.now().isoformat(),
        })
        record.approval_history = history

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"审批通过毛利率预警: 记录 {record_id}")

        return record

    def reject_alert(
        self,
        record_id: int,
        rejected_by: int,
        comment: str,
    ) -> MarginAlertRecord:
        """驳回预警记录"""
        record = self.db.query(MarginAlertRecord).filter(
            MarginAlertRecord.id == record_id
        ).first()

        if not record:
            raise ValueError(f"预警记录不存在: {record_id}")

        assert_status_allows(
            record, MarginAlertStatusEnum.PENDING.value,
            f"记录状态不允许驳回: {record.status}"
        )

        record.status = MarginAlertStatusEnum.REJECTED.value
        record.approved_by = rejected_by
        record.approved_at = datetime.now()
        record.approval_comment = comment

        # 添加审批历史
        history = record.approval_history or []
        history.append({
            "approver_id": rejected_by,
            "action": "REJECT",
            "comment": comment,
            "at": datetime.now().isoformat(),
        })
        record.approval_history = history

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"驳回毛利率预警: 记录 {record_id}")

        return record

    def list_pending_alerts(
        self,
        approver_id: Optional[int] = None,
    ) -> List[MarginAlertRecord]:
        """列出待审批的预警记录"""
        query = self.db.query(MarginAlertRecord).filter(
            MarginAlertRecord.status == MarginAlertStatusEnum.PENDING.value
        )

        if approver_id:
            query = query.filter(
                MarginAlertRecord.current_approver_id == approver_id
            )

        return query.order_by(desc(MarginAlertRecord.requested_at)).all()

    def get_quote_alert_history(
        self, quote_id: int
    ) -> List[MarginAlertRecord]:
        """获取报价的预警历史"""
        return (
            self.db.query(MarginAlertRecord)
            .filter(MarginAlertRecord.quote_id == quote_id)
            .order_by(desc(MarginAlertRecord.requested_at))
            .all()
        )
