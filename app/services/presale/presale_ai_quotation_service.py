"""
AI报价单自动生成服务
Team 5: AI Quotation Generator Service
"""

import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.presale_ai_quotation import (
    PresaleAIQuotation,
    QuotationApproval,
    QuotationStatus,
    QuotationType,
    QuotationVersion,
)
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
        self.ai_model = "gpt-4"  # 默认使用GPT-4，可配置为Kimi
        self.ai_client = AIClientService()

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

        # 序列化报价项
        items_data = [item.dict() for item in request.items]

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
        # 基于需求生成三档方案
        basic_items = self._generate_basic_items(request.base_requirements)
        standard_items = self._generate_standard_items(request.base_requirements, basic_items)
        premium_items = self._generate_premium_items(request.base_requirements, standard_items)

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

        # 更新报价项
        if request.items is not None:
            quotation.items = [item.dict() for item in request.items]
            # 重新计算价格
            subtotal = sum(item.total_price for item in request.items)
            quotation.subtotal = subtotal
            change_summary.append("更新报价项")

        # 更新税率
        if request.tax_rate is not None:
            quotation.tax = quotation.subtotal * request.tax_rate
            change_summary.append(f"税率调整为{request.tax_rate}")

        # 更新折扣
        if request.discount_rate is not None:
            quotation.discount = quotation.subtotal * request.discount_rate
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

    def get_quotation_history(self, ticket_id: int) -> List[PresaleAIQuotation]:
        """获取报价单历史（按版本号降序）"""
        return (
            self.db.query(PresaleAIQuotation)
            .filter(PresaleAIQuotation.presale_ticket_id == ticket_id)
            .order_by(desc(PresaleAIQuotation.version))
            .all()
        )

    def get_quotation_versions(self, quotation_id: int) -> List[QuotationVersion]:
        """获取报价单所有版本"""
        return (
            self.db.query(QuotationVersion)
            .filter(QuotationVersion.quotation_id == quotation_id)
            .order_by(desc(QuotationVersion.version))
            .all()
        )

    def approve_quotation(
        self, quotation_id: int, approver_id: int, status: str, comments: Optional[str] = None
    ) -> QuotationApproval:
        """
        审批报价单
        Args:
            quotation_id: 报价单ID
            approver_id: 审批人ID
            status: 审批状态 (approved/rejected)
            comments: 审批意见
        Returns:
            审批记录
        """
        quotation = self.get_quotation(quotation_id)
        if not quotation:
            raise ValueError(f"Quotation {quotation_id} not found")

        # 创建审批记录
        approval = QuotationApproval(
            quotation_id=quotation_id,
            approver_id=approver_id,
            status=status,
            comments=comments,
            approved_at=datetime.now(),
        )

        self.db.add(approval)

        # 更新报价单状态
        if status == "approved":
            quotation.status = QuotationStatus.APPROVED
        elif status == "rejected":
            quotation.status = QuotationStatus.REJECTED

        self.db.commit()
        self.db.refresh(approval)

        return approval

    # ========== 私有方法 ==========

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
            return ai_items

        items = basic_items.copy()
        items[0] = QuotationItem(
            name="标准ERP系统",
            description="包含进销存、财务管理、人力资源、报表分析功能",
            quantity=Decimal("1"),
            unit="套",
            unit_price=Decimal("150000"),
            total_price=Decimal("150000"),
            category="软件开发",
        )
        items.append(
            QuotationItem(
                name="移动端APP",
                description="iOS和Android移动应用",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("30000"),
                total_price=Decimal("30000"),
                category="软件开发",
            )
        )
        items.append(
            QuotationItem(
                name="系统部署与培训",
                description="标准部署和用户培训（5天）",
                quantity=Decimal("1"),
                unit="次",
                unit_price=Decimal("10000"),
                total_price=Decimal("10000"),
                category="服务",
            )
        )
        return items

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
            return ai_items

        items = standard_items.copy()
        items[0] = QuotationItem(
            name="高级ERP系统",
            description="包含进销存、财务管理、人力资源、项目管理、BI分析、AI智能推荐等全功能",
            quantity=Decimal("1"),
            unit="套",
            unit_price=Decimal("250000"),
            total_price=Decimal("250000"),
            category="软件开发",
        )
        items.append(
            QuotationItem(
                name="定制化开发",
                description="根据企业特定需求定制功能模块",
                quantity=Decimal("1"),
                unit="项",
                unit_price=Decimal("50000"),
                total_price=Decimal("50000"),
                category="软件开发",
            )
        )
        items.append(
            QuotationItem(
                name="系统集成",
                description="与现有系统（财务软件、OA等）集成",
                quantity=Decimal("1"),
                unit="项",
                unit_price=Decimal("30000"),
                total_price=Decimal("30000"),
                category="软件开发",
            )
        )
        items.append(
            QuotationItem(
                name="一年技术支持",
                description="7x24小时技术支持服务",
                quantity=Decimal("1"),
                unit="年",
                unit_price=Decimal("20000"),
                total_price=Decimal("20000"),
                category="服务",
            )
        )
        return items

    def _fallback_basic_items(self) -> List[QuotationItem]:
        """基础版静态回退报价项。"""
        return [
            QuotationItem(
                name="基础ERP系统",
                description="包含进销存、基础财务管理功能",
                quantity=Decimal("1"),
                unit="套",
                unit_price=Decimal("80000"),
                total_price=Decimal("80000"),
                category="软件开发",
            ),
            QuotationItem(
                name="系统部署与培训",
                description="基础部署和用户培训（2天）",
                quantity=Decimal("1"),
                unit="次",
                unit_price=Decimal("5000"),
                total_price=Decimal("5000"),
                category="服务",
            ),
        ]

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
        return bool(openai_ready or self.ai_client.zhipu_client or self.ai_client.kimi_api_key)

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
