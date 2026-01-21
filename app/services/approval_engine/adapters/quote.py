# -*- coding: utf-8 -*-
"""
报价审批适配器

将报价模块接入统一审批系统
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.sales.quotes import Quote, QuoteVersion

from .base import ApprovalAdapter


class QuoteApprovalAdapter(ApprovalAdapter):
    """
    报价审批适配器

    支持的条件字段:
    - entity.gross_margin: 毛利率 (0-100)
    - entity.total_price: 总价
    - entity.cost_total: 总成本
    - entity.lead_time_days: 交期天数
    - entity.customer_name: 客户名称
    """

    entity_type = "QUOTE"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Quote]:
        """获取报价实体"""
        return self.db.query(Quote).filter(Quote.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取报价数据用于条件路由

        Returns:
            包含报价关键数据的字典，用于审批流程路由决策
        """
        quote = self.get_entity(entity_id)
        if not quote:
            return {}

        # 获取当前版本
        version = quote.current_version
        if not version:
            # 如果没有当前版本，尝试获取最新版本
            version = (
                self.db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote.id)
                .order_by(QuoteVersion.id.desc())
                .first()
            )

        data = {
            "quote_code": quote.quote_code,
            "status": quote.status,
            "customer_id": quote.customer_id,
            "customer_name": quote.customer.name if quote.customer else None,
            "owner_id": quote.owner_id,
            "owner_name": quote.owner.name if quote.owner else None,
        }

        if version:
            # 毛利率转换为百分比（0-100）
            gross_margin = version.gross_margin
            if gross_margin is not None:
                # 如果已经是百分比形式（>1），保持不变；否则乘以100
                if gross_margin <= Decimal("1"):
                    gross_margin = gross_margin * 100

            data.update({
                "version_no": version.version_no,
                "total_price": float(version.total_price) if version.total_price else 0,
                "cost_total": float(version.cost_total) if version.cost_total else 0,
                "gross_margin": float(gross_margin) if gross_margin is not None else None,
                "lead_time_days": version.lead_time_days,
                "delivery_date": version.delivery_date.isoformat() if version.delivery_date else None,
            })

        return data

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        提交审批时的回调

        更新报价状态为"审批中"
        """
        quote = self.get_entity(entity_id)
        if quote:
            quote.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批通过时的回调

        更新报价状态为"已审批"
        """
        quote = self.get_entity(entity_id)
        if quote:
            quote.status = "APPROVED"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批驳回时的回调

        更新报价状态为"已驳回"
        """
        quote = self.get_entity(entity_id)
        if quote:
            quote.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        撤回审批时的回调

        恢复报价状态为"草稿"
        """
        quote = self.get_entity(entity_id)
        if quote:
            quote.status = "DRAFT"
            self.db.flush()

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        quote = self.get_entity(entity_id)
        if quote:
            customer_name = quote.customer.name if quote.customer else "未知客户"
            return f"报价审批 - {quote.quote_code} ({customer_name})"
        return f"报价审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("customer_name"):
            parts.append(f"客户: {data['customer_name']}")
        if data.get("total_price"):
            parts.append(f"总价: ¥{data['total_price']:,.2f}")
        if data.get("gross_margin") is not None:
            parts.append(f"毛利率: {data['gross_margin']:.1f}%")
        if data.get("lead_time_days"):
            parts.append(f"交期: {data['lead_time_days']}天")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """
        验证是否可以提交审批

        Returns:
            (是否可提交, 错误信息)
        """
        quote = self.get_entity(entity_id)
        if not quote:
            return False, "报价不存在"

        if quote.status not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({quote.status})不允许提交审批"

        # 检查是否有版本
        if not quote.current_version:
            versions = (
                self.db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote.id)
                .count()
            )
            if versions == 0:
                return False, "报价未添加任何版本，无法提交审批"

        return True, ""
