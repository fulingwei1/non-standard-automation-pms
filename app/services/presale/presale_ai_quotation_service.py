"""
AI报价单自动生成服务
Team 5: AI Quotation Generator Service
"""

import json
import re
import time
from datetime import date, datetime, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.models.presale_ai_quotation import (
    PresaleAIQuotation,
    QuotationStatus,
    QuotationType,
    QuotationVersion,
)
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteItem, QuoteVersion as SalesQuoteVersion
from app.models.presale import PresaleSupportTicket
from app.schemas.presale_ai_quotation import (
    QuotationGenerateRequest,
    QuotationItem,
    QuotationUpdateRequest,
    ThreeTierQuotationRequest,
)
from app.services.ai_client_service import AIClientService
from app.services.ai_structured_output import extract_json_payload
from app.utils.db_helpers import save_obj


class AIQuotationGeneratorService:
    """AI报价单生成服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
        # 报价项为结构化JSON且需连出3档，优先用更快的 coder 模型，避免重推理模型串行超时
        self.ai_model = (
            "qwen3-coder-plus" if getattr(self.ai_client, "qwen_api_key", "") else "gpt-4"
        )

    def generate_quotation_number(self) -> str:
        """生成报价单编号"""
        today = datetime.now().strftime("%Y%m%d")
        # 查询今天已有的报价单数量
        count = (
            self.db.query(PresaleAIQuotation)
            .filter(PresaleAIQuotation.quotation_number.like(f"QT-{today}-%"))
            .count()
        )
        return f"QT-{today}-{count + 1:04d}"

    def generate_quotation(
        self, request: QuotationGenerateRequest, user_id: int
    ) -> PresaleAIQuotation:
        """
        生成报价单
        Args:
            request: 报价单生成请求
            user_id: 创建用户ID
        Returns:
            生成的报价单对象
        """
        start_time = time.time()

        # 计算价格
        subtotal = sum(item.total_price for item in request.items)
        tax = subtotal * request.tax_rate
        discount = subtotal * request.discount_rate
        total = subtotal + tax - discount

        # 生成报价单编号
        quotation_number = self.generate_quotation_number()

        # 如果没有提供付款条款，使用AI生成
        payment_terms = request.payment_terms
        if not payment_terms:
            payment_terms = self._generate_payment_terms(
                total=total, quotation_type=request.quotation_type
            )

        # 序列化报价项（JSON 列不支持 Decimal，需转为 float）
        items_data = [
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in item.dict().items()}
            for item in request.items
        ]

        # 创建报价单
        quotation = PresaleAIQuotation(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            quotation_number=quotation_number,
            quotation_type=request.quotation_type,
            items=items_data,
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total=total,
            payment_terms=payment_terms,
            validity_days=request.validity_days,
            status=QuotationStatus.DRAFT,
            created_by=user_id,
            ai_model=self.ai_model,
            generation_time=Decimal(str(round(time.time() - start_time, 2))),
            notes=request.notes,
        )

        save_obj(self.db, quotation)

        # 创建版本快照
        self._create_version_snapshot(quotation, user_id, "初始创建")

        return quotation

    def resolve_base_requirements(self, request: ThreeTierQuotationRequest) -> str:
        """需求来源解析：手填 base_requirements 优先；为空时从需求分析记录组装；两者皆空拒绝。"""
        base = (request.base_requirements or "").strip()
        if base:
            return base
        if request.requirement_analysis_id:
            from app.services.presale import requirement_analysis_bridge as bridge

            analysis = bridge.get_analysis(self.db, request.requirement_analysis_id)
            if not analysis:
                raise ValueError(f"需求分析记录 {request.requirement_analysis_id} 不存在")
            composed = bridge.compose_requirements_text(analysis)
            if composed:
                return composed
        raise ValueError("需求为空：请提供 base_requirements 或有效的 requirement_analysis_id")

    def generate_three_tier_quotations(
        self, request: ThreeTierQuotationRequest, user_id: int
    ) -> Tuple[PresaleAIQuotation, PresaleAIQuotation, PresaleAIQuotation]:
        """
        生成三档报价方案（基础版、标准版、高级版）
        Args:
            request: 三档报价请求
            user_id: 创建用户ID
        Returns:
            (基础版, 标准版, 高级版) 报价单元组
        """
        # 需求来源解析：base_requirements 为空时自动从 requirement_analysis_id 带出
        base_requirements = self.resolve_base_requirements(request)

        # 基于需求生成三档方案
        basic_items = self._generate_basic_items(base_requirements)
        standard_items = self._generate_standard_items(base_requirements, basic_items)
        premium_items = self._generate_premium_items(base_requirements, standard_items)

        # 生成基础版报价单
        basic_request = QuotationGenerateRequest(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            quotation_type=QuotationType.BASIC,
            items=basic_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0"),
            validity_days=30,
        )
        basic_quotation = self.generate_quotation(basic_request, user_id)

        # 生成标准版报价单
        standard_request = QuotationGenerateRequest(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            quotation_type=QuotationType.STANDARD,
            items=standard_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.05"),
            validity_days=30,
        )
        standard_quotation = self.generate_quotation(standard_request, user_id)

        # 生成高级版报价单
        premium_request = QuotationGenerateRequest(
            presale_ticket_id=request.presale_ticket_id,
            customer_id=request.customer_id,
            quotation_type=QuotationType.PREMIUM,
            items=premium_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.10"),
            validity_days=30,
        )
        premium_quotation = self.generate_quotation(premium_request, user_id)

        return basic_quotation, standard_quotation, premium_quotation

    def update_quotation(
        self, quotation_id: int, request: QuotationUpdateRequest, user_id: int
    ) -> PresaleAIQuotation:
        """
        更新报价单
        Args:
            quotation_id: 报价单ID
            request: 更新请求
            user_id: 更新用户ID
        Returns:
            更新后的报价单
        """
        quotation = (
            self.db.query(PresaleAIQuotation).filter(PresaleAIQuotation.id == quotation_id).first()
        )

        if not quotation:
            raise ValueError(f"Quotation {quotation_id} not found")

        # 创建版本快照
        change_summary = []
        previous_subtotal = self._to_decimal(quotation.subtotal)
        existing_tax_rate = self._safe_rate(quotation.tax, previous_subtotal)
        existing_discount_rate = self._safe_rate(quotation.discount, previous_subtotal)

        # 更新报价项
        if request.items is not None:
            quotation.items = self._serialize_items(request.items)
            # 重新计算价格
            subtotal = sum(item.total_price for item in request.items)
            quotation.subtotal = subtotal
            change_summary.append("更新报价项")

        # 更新税率
        if request.items is not None or request.tax_rate is not None:
            tax_rate = request.tax_rate if request.tax_rate is not None else existing_tax_rate
            quotation.tax = quotation.subtotal * tax_rate
        if request.tax_rate is not None:
            change_summary.append(f"税率调整为{request.tax_rate}")

        # 更新折扣
        if request.items is not None or request.discount_rate is not None:
            discount_rate = (
                request.discount_rate
                if request.discount_rate is not None
                else existing_discount_rate
            )
            quotation.discount = quotation.subtotal * discount_rate
        if request.discount_rate is not None:
            change_summary.append(f"折扣率调整为{request.discount_rate}")

        # 重新计算总价
        quotation.total = quotation.subtotal + quotation.tax - quotation.discount

        # 更新其他字段
        if request.validity_days is not None:
            quotation.validity_days = request.validity_days
            change_summary.append(f"有效期调整为{request.validity_days}天")

        if request.payment_terms is not None:
            quotation.payment_terms = request.payment_terms
            change_summary.append("更新付款条款")

        if request.status is not None:
            quotation.status = request.status
            change_summary.append(f"状态变更为{request.status}")

        if request.notes is not None:
            quotation.notes = request.notes

        # 增加版本号
        quotation.version += 1
        quotation.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(quotation)

        # 创建版本快照
        self._create_version_snapshot(quotation, user_id, "; ".join(change_summary))

        return quotation

    def get_quotation(self, quotation_id: int) -> Optional[PresaleAIQuotation]:
        """获取报价单"""
        return (
            self.db.query(PresaleAIQuotation).filter(PresaleAIQuotation.id == quotation_id).first()
        )

    def get_quotation_response(self, quotation_id: int) -> Optional[Dict[str, Any]]:
        """获取报价单响应数据，兼容历史非法枚举值。"""
        try:
            quotation = self.get_quotation(quotation_id)
            if quotation:
                return quotation
            return None
        except LookupError:
            row = (
                self.db.execute(
                    text(
                        """
                        SELECT
                            id,
                            presale_ticket_id,
                            customer_id,
                            quotation_number,
                            quotation_type,
                            items,
                            subtotal,
                            tax,
                            discount,
                            total,
                            payment_terms,
                            validity_days,
                            status,
                            pdf_url,
                            version,
                            created_by,
                            created_at,
                            updated_at,
                            ai_model,
                            generation_time,
                            notes
                        FROM presale_ai_quotation
                        WHERE id = :quotation_id
                        """
                    ),
                    {"quotation_id": quotation_id},
                )
                .mappings()
                .first()
            )
            if not row:
                return None
            return self._quotation_row_to_response(row)

    def get_quotation_history(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取报价单历史（按版本号降序），兼容历史非法枚举值。"""
        rows = (
            self.db.execute(
                text(
                    """
                    SELECT
                        id,
                        presale_ticket_id,
                        customer_id,
                        quotation_number,
                        quotation_type,
                        items,
                        subtotal,
                        tax,
                        discount,
                        total,
                        payment_terms,
                        validity_days,
                        status,
                        pdf_url,
                        version,
                        created_by,
                        created_at,
                        updated_at,
                        ai_model,
                        generation_time,
                        notes
                    FROM presale_ai_quotation
                    WHERE presale_ticket_id = :ticket_id
                    ORDER BY version DESC, id DESC
                    """
                ),
                {"ticket_id": ticket_id},
            )
            .mappings()
            .all()
        )
        return [self._quotation_row_to_response(row) for row in rows]

    def get_quotation_versions(self, quotation_id: int) -> List[QuotationVersion]:
        """获取报价单所有版本"""
        return (
            self.db.query(QuotationVersion)
            .filter(QuotationVersion.quotation_id == quotation_id)
            .order_by(desc(QuotationVersion.version))
            .all()
        )

    @staticmethod
    def _json_or_default(value: Any, default: Any) -> Any:
        if value in (None, ""):
            return default
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return value

    def _quotation_row_to_response(self, row: Any) -> Dict[str, Any]:
        payload = dict(row)
        payload["quotation_type"] = self._normalize_quotation_type(payload.get("quotation_type"))
        payload["status"] = self._normalize_quotation_status(payload.get("status"))
        payload["items"] = self._json_or_default(payload.get("items"), [])
        payload["validity_days"] = payload.get("validity_days") or 30
        payload["version"] = payload.get("version") or 1
        return payload

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _safe_rate(self, amount: Any, subtotal: Any) -> Decimal:
        subtotal_decimal = self._to_decimal(subtotal)
        if subtotal_decimal == 0:
            return Decimal("0")
        return self._to_decimal(amount) / subtotal_decimal

    @staticmethod
    def _serialize_items(items: List[QuotationItem]) -> List[Dict[str, Any]]:
        return [
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in item.dict().items()}
            for item in items
        ]

    @staticmethod
    def _normalize_quotation_type(value: Any) -> str:
        if hasattr(value, "value"):
            value = value.value
        value = str(value or "").lower()
        if value in {"basic", "standard", "premium"}:
            return value
        return "standard"

    @staticmethod
    def _normalize_quotation_status(value: Any) -> str:
        if hasattr(value, "value"):
            value = value.value
        value = str(value or "").lower()
        if value in {"draft", "pending_approval", "approved", "sent", "accepted", "rejected"}:
            return value
        return "draft"

    def approve_quotation(
        self, quotation_id: int, approver_id: int, status: str, comments: Optional[str] = None
    ) -> dict:
        """
        审批报价单
        Args:
            quotation_id: 报价单ID
            approver_id: 审批人ID
            status: 审批状态 (approved/rejected)
            comments: 审批意见
        Returns:
            审批结果
        """
        quotation = self.get_quotation(quotation_id)
        if not quotation:
            raise ValueError(f"Quotation {quotation_id} not found")

        # 更新报价单状态
        if status == "approved":
            quotation.status = QuotationStatus.APPROVED
        elif status == "rejected":
            quotation.status = QuotationStatus.REJECTED

        approved_at = datetime.now()
        self.db.commit()
        return {
            "id": quotation_id,
            "quotation_id": quotation_id,
            "approver_id": approver_id,
            "status": status,
            "comments": comments,
            "created_at": approved_at,
            "approved_at": approved_at,
        }

    def promote_to_sales_quote(
        self,
        quotation_id: int,
        user_id: int,
        opportunity_id: Optional[int] = None,
    ) -> Quote:
        """Promote an AI quotation draft into the formal sales quote chain."""
        quotation = self.get_quotation(quotation_id)
        if not quotation:
            raise ValueError(f"Quotation {quotation_id} not found")

        existing_quote_id = self._promoted_quote_id_from_notes(quotation.notes)
        if existing_quote_id:
            existing_quote = self.db.query(Quote).filter(Quote.id == existing_quote_id).first()
            if existing_quote:
                return existing_quote

        ticket = (
            self.db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.id == quotation.presale_ticket_id)
            .first()
        )
        resolved_opportunity = self._resolve_sales_opportunity(
            quotation,
            ticket,
            opportunity_id=opportunity_id,
        )
        if not resolved_opportunity:
            raise ValueError("AI报价转正式报价需要关联商机")

        customer_id = quotation.customer_id or resolved_opportunity.customer_id
        if not customer_id:
            raise ValueError("AI报价转正式报价需要关联客户")

        quote = Quote(
            quote_code=self._generate_sales_quote_code(quotation),
            opportunity_id=resolved_opportunity.id,
            customer_id=customer_id,
            status="DRAFT",
            valid_until=date.today() + timedelta(days=quotation.validity_days or 30),
            owner_id=user_id,
            tenant_id=quotation.tenant_id,
        )
        self.db.add(quote)
        self.db.flush()

        amount_without_tax = self._round_money(
            self._to_decimal(quotation.subtotal) - self._to_decimal(quotation.discount)
        )
        tax_amount = self._round_money(self._to_decimal(quotation.tax))
        total_price = self._round_money(self._to_decimal(quotation.total))
        tax_rate = Decimal("0")
        if self._to_decimal(quotation.subtotal):
            tax_rate = self._round_money(
                tax_amount / self._to_decimal(quotation.subtotal) * Decimal("100")
            )

        version = SalesQuoteVersion(
            quote_id=quote.id,
            version_no=f"AI-{quotation.version or 1}",
            quote_code=quotation.quotation_number,
            status="DRAFT",
            total_price=total_price,
            amount_without_tax=amount_without_tax,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            amount_with_tax=total_price,
            cost_total=Decimal("0"),
            gross_margin=Decimal("100.00") if total_price > 0 else Decimal("0"),
            risk_terms=self._build_sales_quote_risk_terms(quotation),
            presale_ticket_id=quotation.presale_ticket_id,
            created_by=user_id,
            tenant_id=quotation.tenant_id,
        )
        self.db.add(version)
        self.db.flush()

        for item in self._normalised_sales_quote_items(quotation.items):
            self.db.add(
                QuoteItem(
                    quote_version_id=version.id,
                    item_type="AI_QUOTATION",
                    item_name=item["name"],
                    qty=item["quantity"],
                    unit=item["unit"],
                    unit_price=item["unit_price"],
                    cost=Decimal("0"),
                    cost_category=item["category"],
                    specification=item["description"],
                    remark=f"来源AI报价: {quotation.quotation_number}",
                    tenant_id=quotation.tenant_id,
                )
            )

        quote.current_version_id = version.id
        quotation.status = QuotationStatus.ACCEPTED
        quotation.notes = self._append_promotion_note(
            quotation.notes,
            quote_id=quote.id,
            version_id=version.id,
        )
        self.db.commit()
        self.db.refresh(quote)
        return quote

    # ========== 私有方法 ==========

    def _resolve_sales_opportunity(
        self,
        quotation: PresaleAIQuotation,
        ticket: Optional[PresaleSupportTicket],
        *,
        opportunity_id: Optional[int] = None,
    ) -> Optional[Opportunity]:
        if opportunity_id:
            return self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if ticket and ticket.opportunity_id:
            return (
                self.db.query(Opportunity)
                .filter(Opportunity.id == ticket.opportunity_id)
                .first()
            )
        if quotation.customer_id:
            return (
                self.db.query(Opportunity)
                .filter(Opportunity.customer_id == quotation.customer_id)
                .order_by(Opportunity.created_at.desc(), Opportunity.id.desc())
                .first()
            )
        return None

    def _generate_sales_quote_code(self, quotation: PresaleAIQuotation) -> str:
        base = f"AIQ-{quotation.id}-{datetime.now().strftime('%m%d')}"[:20]
        candidate = base
        counter = 1
        while self.db.query(Quote).filter(Quote.quote_code == candidate).first():
            suffix = f"-{counter}"
            candidate = f"{base[: 20 - len(suffix)]}{suffix}"
            counter += 1
        return candidate

    def _normalised_sales_quote_items(self, raw_items: Any) -> List[Dict[str, Any]]:
        items = self._json_or_default(raw_items, [])
        if not isinstance(items, list):
            return []
        normalised: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("item_name") or item.get("product_name")
            if not name:
                continue
            quantity = self._to_decimal(item.get("quantity") or item.get("qty") or 1)
            unit_price = self._to_decimal(item.get("unit_price"))
            total_price = self._to_decimal(item.get("total_price"))
            if not unit_price and quantity:
                unit_price = total_price / quantity
            normalised.append(
                {
                    "name": str(name),
                    "description": item.get("description") or item.get("specification"),
                    "quantity": quantity,
                    "unit": item.get("unit") or "项",
                    "unit_price": unit_price,
                    "category": item.get("category") or item.get("cost_category"),
                }
            )
        return normalised

    def _build_sales_quote_risk_terms(self, quotation: PresaleAIQuotation) -> str:
        parts = [
            f"来源AI报价: {quotation.quotation_number}",
            f"报价档位: {self._normalize_quotation_type(quotation.quotation_type)}",
        ]
        if quotation.payment_terms:
            parts.append(f"付款条款: {quotation.payment_terms}")
        return "\n".join(parts)

    @staticmethod
    def _promoted_quote_id_from_notes(notes: Optional[str]) -> Optional[int]:
        if not notes:
            return None
        match = re.search(r"promoted_quote_id=(\d+)", notes)
        return int(match.group(1)) if match else None

    @staticmethod
    def _append_promotion_note(notes: Optional[str], *, quote_id: int, version_id: int) -> str:
        promotion_note = f"promoted_quote_id={quote_id}; promoted_quote_version_id={version_id}"
        if not notes:
            return promotion_note
        if "promoted_quote_id=" in notes:
            return notes
        return f"{notes}\n{promotion_note}"

    def _generate_payment_terms(self, total: Decimal, quotation_type: QuotationType) -> str:
        """
        AI生成付款条款
        Args:
            total: 总金额
            quotation_type: 报价单类型
        Returns:
            付款条款文本
        """
        payment_terms = self._generate_payment_terms_with_ai(total, quotation_type)
        if payment_terms:
            return payment_terms
        return self._default_payment_terms(total, quotation_type)

    def _generate_basic_items(self, requirements: str) -> List[QuotationItem]:
        """生成基础版报价项"""
        ai_items = self._generate_items_with_ai(requirements, QuotationType.BASIC)
        if ai_items:
            return ai_items
        return self._fallback_basic_items()

    def _generate_standard_items(
        self, requirements: str, basic_items: List[QuotationItem]
    ) -> List[QuotationItem]:
        """生成标准版报价项（基于基础版扩展）"""
        ai_items = self._generate_items_with_ai(
            requirements,
            QuotationType.STANDARD,
            reference_items=basic_items,
        )
        if ai_items:
            items = ai_items
        else:
            items = self._fallback_standard_items()

        return self._ensure_minimum_subtotal(
            items,
            reference_items=basic_items,
            multiplier=Decimal("1.18"),
        )

    def _generate_premium_items(
        self, requirements: str, standard_items: List[QuotationItem]
    ) -> List[QuotationItem]:
        """生成高级版报价项（基于标准版扩展）"""
        ai_items = self._generate_items_with_ai(
            requirements,
            QuotationType.PREMIUM,
            reference_items=standard_items,
        )
        if ai_items:
            items = ai_items
        else:
            items = self._fallback_premium_items()

        return self._ensure_minimum_subtotal(
            items,
            reference_items=standard_items,
            multiplier=Decimal("1.22"),
        )

    def _fallback_basic_items(self) -> List[QuotationItem]:
        """基础版静态回退报价项。"""
        return [
            QuotationItem(
                name="基础检测工装与控制单元",
                description="包含基础测试工装、控制单元、I/O模块和必要安全互锁，满足单工位检测需求",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("80000"),
                total_price=Decimal("80000"),
                category="设备",
            ),
            QuotationItem(
                name="通用夹治具与安全防护",
                description="包含产品定位夹具、压紧机构、探针/接插件和基础防护罩",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("28000"),
                total_price=Decimal("28000"),
                category="夹治具",
            ),
            QuotationItem(
                name="现场安装调试与操作培训",
                description="完成现场安装、基础参数调试、操作培训和试运行支持",
                quantity=Decimal("1"),
                unit="次",
                unit_price=Decimal("12000"),
                total_price=Decimal("12000"),
                category="服务",
            ),
        ]

    def _fallback_standard_items(self) -> List[QuotationItem]:
        """标准版静态回退报价项。"""
        return [
            QuotationItem(
                name="标准自动化检测工作站",
                description="包含标准机架、PLC控制、气动执行、测试仪表集成和安全防护",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("120000"),
                total_price=Decimal("120000"),
                category="自动化集成",
            ),
            QuotationItem(
                name="视觉与传感检测模块",
                description="配置工业相机、光源、传感器和检测算法，用于关键尺寸/状态识别",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("45000"),
                total_price=Decimal("45000"),
                category="视觉检测",
            ),
            QuotationItem(
                name="数据采集与追溯模块",
                description="采集检测数据、条码信息和工艺参数，支持本地报表与追溯查询",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("30000"),
                total_price=Decimal("30000"),
                category="数据系统",
            ),
            QuotationItem(
                name="现场安装调试与验收培训",
                description="完成现场联调、节拍验证、验收资料和班组培训",
                quantity=Decimal("1"),
                unit="次",
                unit_price=Decimal("25000"),
                total_price=Decimal("25000"),
                category="服务",
            ),
        ]

    def _fallback_premium_items(self) -> List[QuotationItem]:
        """高级版静态回退报价项。"""
        return [
            QuotationItem(
                name="高节拍自动化检测产线",
                description="包含多工位检测平台、节拍平衡、自动流转机构和完整安全防护",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("180000"),
                total_price=Decimal("180000"),
                category="自动化集成",
            ),
            QuotationItem(
                name="机器人或自动上下料模块",
                description="配置机器人/机械手、料仓、输送定位和防呆检测，实现自动上下料",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("85000"),
                total_price=Decimal("85000"),
                category="自动上下料",
            ),
            QuotationItem(
                name="高级视觉与数据追溯系统",
                description="包含多相机检测、缺陷判定、检测数据归档、看板和接口对接",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("65000"),
                total_price=Decimal("65000"),
                category="视觉检测",
            ),
            QuotationItem(
                name="定制夹治具与安全防护系统",
                description="针对多型号产品配置快换夹治具、互锁防护、光栅和安全门",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("42000"),
                total_price=Decimal("42000"),
                category="夹治具",
            ),
            QuotationItem(
                name="一年质保与驻场支持",
                description="提供验收后一年的质保、远程诊断和关键阶段驻场支持",
                quantity=Decimal("1"),
                unit="年",
                unit_price=Decimal("28000"),
                total_price=Decimal("28000"),
                category="服务",
            ),
        ]

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _ceil_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_CEILING)

    def _items_subtotal(self, items: List[QuotationItem]) -> Decimal:
        return self._round_money(sum((self._to_decimal(item.total_price) for item in items), Decimal("0")))

    def _ensure_minimum_subtotal(
        self,
        items: List[QuotationItem],
        reference_items: List[QuotationItem],
        multiplier: Decimal,
    ) -> List[QuotationItem]:
        """按参考档放大报价小计，避免三档总价被税折扣放大后倒挂。"""
        current_subtotal = self._items_subtotal(items)
        reference_subtotal = self._items_subtotal(reference_items)
        if current_subtotal <= 0 or reference_subtotal <= 0:
            return items

        minimum_subtotal = self._round_money(reference_subtotal * multiplier)
        if current_subtotal >= minimum_subtotal:
            return items

        scale = minimum_subtotal / current_subtotal
        adjusted = [
            self._copy_item_with_price(item, self._to_decimal(item.unit_price) * scale)
            for item in items
        ]

        adjusted_subtotal = self._items_subtotal(adjusted)
        if adjusted and adjusted_subtotal < minimum_subtotal:
            shortfall = minimum_subtotal - adjusted_subtotal
            last = adjusted[-1]
            unit_increment = self._ceil_money(shortfall / self._to_decimal(last.quantity))
            adjusted[-1] = self._copy_item_with_price(
                last,
                self._to_decimal(last.unit_price) + unit_increment,
            )

        return adjusted

    def _copy_item_with_price(self, item: QuotationItem, unit_price: Decimal) -> QuotationItem:
        unit_price = self._round_money(unit_price)
        quantity = self._to_decimal(item.quantity)
        return QuotationItem(
            item_id=item.item_id,
            name=item.name,
            description=item.description,
            quantity=quantity,
            unit=item.unit,
            unit_price=unit_price,
            total_price=self._round_money(quantity * unit_price),
            category=item.category,
        )

    def _create_version_snapshot(
        self, quotation: PresaleAIQuotation, user_id: int, change_summary: str
    ):
        """创建版本快照"""
        snapshot_data = {
            "quotation_number": quotation.quotation_number,
            "quotation_type": quotation.quotation_type.value,
            "items": quotation.items,
            "subtotal": float(quotation.subtotal),
            "tax": float(quotation.tax),
            "discount": float(quotation.discount),
            "total": float(quotation.total),
            "payment_terms": quotation.payment_terms,
            "validity_days": quotation.validity_days,
            "status": quotation.status.value,
        }

        version = QuotationVersion(
            quotation_id=quotation.id,
            version=quotation.version,
            snapshot_data=snapshot_data,
            changed_by=user_id,
            change_summary=change_summary,
        )

        self.db.add(version)
        self.db.commit()

    def _has_live_ai(self) -> bool:
        """检查是否具备真实AI能力。"""
        openai_ready = bool(
            self.ai_client.openai_client
            and str(self.ai_client.openai_api_key).startswith(("sk-", "sk-proj-"))
        )
        return bool(
            openai_ready
            or self.ai_client.zhipu_client
            or self.ai_client.kimi_api_key
            or getattr(self.ai_client, "qwen_api_key", "")  # 阿里百炼 Coding Plan
        )

    def _generate_ai_content(
        self, prompt: str, temperature: float = 0.25, max_tokens: int = 1800
    ) -> Optional[str]:
        """统一AI调用，Mock或失败时返回None。"""
        if not self._has_live_ai():
            return None

        models = [self.ai_model]
        if self.ai_client.default_model not in models:
            models.append(self.ai_client.default_model)

        for model in models:
            try:
                response = self.ai_client.generate_solution(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception:
                continue

            content = (response or {}).get("content")
            model_name = str((response or {}).get("model", ""))
            if content and not model_name.endswith("-mock"):
                return str(content).strip()

        return None

    def _generate_payment_terms_with_ai(
        self, total: Decimal, quotation_type: QuotationType
    ) -> Optional[str]:
        """使用AI按报价档位生成付款条款。"""
        prompt = f"""你是一名非标自动化行业的商务报价专家，请为以下报价生成付款条款。

报价档位：{quotation_type.value}
报价总额：¥{total:,.2f}

请直接输出中文付款条款文本，要求：
1. 明确首付款、中期款、尾款比例和付款节点。
2. 条款简洁正式，适用于设备/自动化项目报价单。
3. 输出中必须包含总金额。"""

        return self._generate_ai_content(prompt, temperature=0.2, max_tokens=600)

    def _default_payment_terms(self, total: Decimal, quotation_type: QuotationType) -> str:
        """静态付款条款回退。"""
        if quotation_type == QuotationType.BASIC:
            return f"总金额：¥{total:,.2f}\n付款方式：签订合同后一次性支付全款"
        if quotation_type == QuotationType.STANDARD:
            return (
                f"总金额：¥{total:,.2f}\n付款方式：\n"
                "- 首付款：30%（签订合同后7个工作日内）\n"
                "- 中期款：40%（完成中期验收后7个工作日内）\n"
                "- 尾款：30%（完成终期验收后7个工作日内）"
            )
        return (
            f"总金额：¥{total:,.2f}\n付款方式：\n"
            "- 首付款：20%（签订合同后7个工作日内）\n"
            "- 中期款1：30%（完成需求确认后7个工作日内）\n"
            "- 中期款2：30%（完成中期验收后7个工作日内）\n"
            "- 尾款：20%（完成终期验收后7个工作日内）"
        )

    def _generate_items_with_ai(
        self,
        requirements: str,
        quotation_type: QuotationType,
        reference_items: Optional[List[QuotationItem]] = None,
    ) -> Optional[List[QuotationItem]]:
        """使用AI生成结构化报价项。"""
        reference_payload = (
            [item.model_dump() for item in reference_items]
            if reference_items
            else []
        )
        prompt = f"""你是一名非标自动化行业报价工程师，请根据需求生成 {quotation_type.value} 档报价项。

客户需求：
{requirements}

参考报价项（如有）：
{json.dumps(reference_payload, ensure_ascii=False, indent=2, default=str)}

请仅输出 JSON，格式如下：
{{
  "items": [
    {{
      "name": "报价项名称",
      "description": "用途和范围",
      "quantity": 1,
      "unit": "套",
      "unit_price": 100000,
      "category": "设备/软件/服务"
    }}
  ]
}}

要求：
1. 至少输出2个报价项。
2. total_price 由系统自动计算，不需要输出。
3. {quotation_type.value} 档要体现对应层级能力，避免与其他档位完全重复。
4. 只返回合法 JSON。"""

        content = self._generate_ai_content(prompt, temperature=0.35, max_tokens=1600)
        payload = extract_json_payload(content or "")
        if isinstance(payload, dict):
            payload = payload.get("items")
        if not isinstance(payload, list):
            return None

        items = []
        for item in payload:
            normalized = self._normalize_item(item)
            if normalized is not None:
                items.append(normalized)

        return items if items else None

    def _normalize_item(self, item: Any) -> Optional[QuotationItem]:
        """归一化AI返回的报价项。"""
        if not isinstance(item, dict):
            return None

        name = str(item.get("name") or "").strip()
        unit = str(item.get("unit") or "项").strip()
        if not name:
            return None

        try:
            quantity = Decimal(str(item.get("quantity", "1")))
            unit_price = Decimal(str(item.get("unit_price", "0")))
        except Exception:
            return None

        if quantity <= 0 or unit_price <= 0:
            return None

        return QuotationItem(
            name=name,
            description=str(item.get("description") or "").strip() or None,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            category=str(item.get("category") or "").strip() or None,
        )
