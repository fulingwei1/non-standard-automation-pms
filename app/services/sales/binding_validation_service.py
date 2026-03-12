# -*- coding: utf-8 -*-
"""
绑定验证服务

确保 方案-成本-报价 三位一体绑定的一致性。
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.sales.presale_ai_cost import PresaleAICostEstimation
from app.models.sales.quotes import QuoteVersion
from app.models.sales.solution_version import SolutionVersion


class BindingIssueLevel(str, Enum):
    """绑定问题级别"""

    ERROR = "error"  # 严重错误，阻止操作
    WARNING = "warning"  # 警告，允许操作但需注意
    INFO = "info"  # 信息提示


class BindingIssueCode(str, Enum):
    """绑定问题代码"""

    # 方案相关
    SOLUTION_NOT_BOUND = "SOLUTION_NOT_BOUND"
    SOLUTION_NOT_APPROVED = "SOLUTION_NOT_APPROVED"
    SOLUTION_VERSION_OUTDATED = "SOLUTION_VERSION_OUTDATED"

    # 成本相关
    COST_NOT_BOUND = "COST_NOT_BOUND"
    COST_NOT_APPROVED = "COST_NOT_APPROVED"
    COST_SOLUTION_MISMATCH = "COST_SOLUTION_MISMATCH"
    COST_AMOUNT_MISMATCH = "COST_AMOUNT_MISMATCH"

    # 报价相关
    QUOTE_BINDING_INCOMPLETE = "QUOTE_BINDING_INCOMPLETE"


@dataclass
class BindingIssue:
    """绑定问题"""

    level: BindingIssueLevel
    code: BindingIssueCode
    message: str
    details: Optional[dict] = None


@dataclass
class BindingValidationResult:
    """绑定验证结果"""

    quote_version_id: int
    status: str  # valid / outdated / invalid
    issues: List[BindingIssue]
    validated_at: datetime

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"

    @property
    def has_errors(self) -> bool:
        return any(i.level == BindingIssueLevel.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.level == BindingIssueLevel.WARNING for i in self.issues)


class BindingValidationService:
    """绑定验证服务

    职责：
    1. 验证报价版本的绑定状态
    2. 同步成本到报价
    3. 检查绑定一致性
    """

    def __init__(self, db: Session):
        self.db = db

    async def validate_quote_binding(
        self,
        quote_version_id: int,
    ) -> BindingValidationResult:
        """验证报价版本的绑定状态

        检查项：
        1. 方案版本是否已绑定
        2. 方案版本是否已审批
        3. 成本估算是否已绑定
        4. 成本估算是否已审批
        5. 成本估算是否绑定正确的方案版本
        6. 报价金额是否与成本一致

        Args:
            quote_version_id: 报价版本ID

        Returns:
            绑定验证结果
        """
        qv = self.db.query(QuoteVersion).get(quote_version_id)
        if not qv:
            raise ValueError(f"报价版本不存在: {quote_version_id}")

        issues: List[BindingIssue] = []

        # === 1. 检查方案版本绑定 ===
        if not qv.solution_version_id:
            issues.append(
                BindingIssue(
                    level=BindingIssueLevel.ERROR,
                    code=BindingIssueCode.SOLUTION_NOT_BOUND,
                    message="报价未绑定方案版本",
                )
            )
        else:
            sv = qv.solution_version
            if sv.status != "approved":
                issues.append(
                    BindingIssue(
                        level=BindingIssueLevel.WARNING,
                        code=BindingIssueCode.SOLUTION_NOT_APPROVED,
                        message=f"方案版本 {sv.version_no} 未审批（状态：{sv.status}）",
                        details={"solution_version_id": sv.id, "status": sv.status},
                    )
                )

            # 检查是否为最新版本
            latest_version = self._get_latest_approved_solution_version(sv.solution_id)
            if latest_version and latest_version.id != sv.id:
                issues.append(
                    BindingIssue(
                        level=BindingIssueLevel.WARNING,
                        code=BindingIssueCode.SOLUTION_VERSION_OUTDATED,
                        message=f"绑定的方案版本 {sv.version_no} 不是最新审批版本（最新：{latest_version.version_no}）",
                        details={
                            "current_version_id": sv.id,
                            "latest_version_id": latest_version.id,
                        },
                    )
                )

        # === 2. 检查成本估算绑定 ===
        if not qv.cost_estimation_id:
            issues.append(
                BindingIssue(
                    level=BindingIssueLevel.ERROR,
                    code=BindingIssueCode.COST_NOT_BOUND,
                    message="报价未绑定成本估算",
                )
            )
        else:
            ce = qv.cost_estimation
            if ce.status != "approved":
                issues.append(
                    BindingIssue(
                        level=BindingIssueLevel.WARNING,
                        code=BindingIssueCode.COST_NOT_APPROVED,
                        message=f"成本估算未审批（状态：{ce.status}）",
                        details={"cost_estimation_id": ce.id, "status": ce.status},
                    )
                )

            # 检查成本估算是否绑定正确的方案版本
            if qv.solution_version_id and ce.solution_version_id != qv.solution_version_id:
                issues.append(
                    BindingIssue(
                        level=BindingIssueLevel.ERROR,
                        code=BindingIssueCode.COST_SOLUTION_MISMATCH,
                        message="成本估算绑定的方案版本与报价不一致",
                        details={
                            "quote_solution_version_id": qv.solution_version_id,
                            "cost_solution_version_id": ce.solution_version_id,
                        },
                    )
                )

            # 检查金额一致性
            if qv.cost_total and ce.total_cost:
                if qv.cost_total != ce.total_cost:
                    issues.append(
                        BindingIssue(
                            level=BindingIssueLevel.ERROR,
                            code=BindingIssueCode.COST_AMOUNT_MISMATCH,
                            message=f"报价成本 {qv.cost_total} 与估算成本 {ce.total_cost} 不一致",
                            details={
                                "quote_cost_total": float(qv.cost_total),
                                "estimation_total_cost": float(ce.total_cost),
                                "difference": float(qv.cost_total - ce.total_cost),
                            },
                        )
                    )

        # === 3. 确定绑定状态 ===
        if any(i.level == BindingIssueLevel.ERROR for i in issues):
            binding_status = "invalid"
        elif issues:
            binding_status = "outdated"
        else:
            binding_status = "valid"

        # === 4. 更新报价版本的绑定状态 ===
        qv.binding_status = binding_status
        qv.binding_validated_at = datetime.now()
        qv.binding_warning = "\n".join(i.message for i in issues) if issues else None

        self.db.commit()

        return BindingValidationResult(
            quote_version_id=quote_version_id,
            status=binding_status,
            issues=issues,
            validated_at=qv.binding_validated_at,
        )

    async def sync_cost_to_quote(
        self,
        quote_version_id: int,
    ) -> QuoteVersion:
        """同步成本到报价

        从绑定的 CostEstimation 同步 cost_total 到 QuoteVersion，
        并重新计算毛利率。

        Args:
            quote_version_id: 报价版本ID

        Returns:
            更新后的报价版本

        Raises:
            ValueError: 报价未绑定成本估算
        """
        qv = self.db.query(QuoteVersion).get(quote_version_id)
        if not qv:
            raise ValueError(f"报价版本不存在: {quote_version_id}")

        ce = qv.cost_estimation
        if not ce:
            raise ValueError("报价未绑定成本估算，无法同步")

        # 同步成本
        qv.cost_total = ce.total_cost

        # 重新计算毛利率
        if qv.total_price and qv.cost_total and qv.total_price > 0:
            margin = (qv.total_price - qv.cost_total) / qv.total_price * Decimal("100")
            qv.gross_margin = margin.quantize(Decimal("0.01"))

        # 更新绑定状态
        qv.binding_status = "valid"
        qv.binding_validated_at = datetime.now()
        qv.binding_warning = None

        # 更新成本估算的绑定标记
        ce.is_bound_to_quote = True
        ce.bound_quote_version_id = qv.id

        self.db.commit()

        return qv

    async def validate_binding_before_submit(
        self,
        quote_version_id: int,
    ) -> BindingValidationResult:
        """提交前验证绑定

        在报价提交审批前调用，确保：
        1. 绑定完整
        2. 无严重错误

        Args:
            quote_version_id: 报价版本ID

        Returns:
            验证结果

        Raises:
            ValueError: 存在阻止提交的问题
        """
        result = await self.validate_quote_binding(quote_version_id)

        if result.has_errors:
            error_messages = [i.message for i in result.issues if i.level == BindingIssueLevel.ERROR]
            raise ValueError(f"报价绑定验证失败：{'; '.join(error_messages)}")

        return result

    async def check_solution_update_impact(
        self,
        solution_version_id: int,
    ) -> List[dict]:
        """检查方案版本更新的影响

        当方案版本更新时，查找受影响的成本估算和报价。

        Args:
            solution_version_id: 方案版本ID

        Returns:
            受影响的实体列表
        """
        sv = self.db.query(SolutionVersion).get(solution_version_id)
        if not sv:
            return []

        # 查找绑定此方案版本的成本估算
        affected_estimations = (
            self.db.query(PresaleAICostEstimation)
            .filter(PresaleAICostEstimation.solution_version_id == solution_version_id)
            .all()
        )

        # 查找绑定此方案版本的报价
        affected_quotes = (
            self.db.query(QuoteVersion)
            .filter(QuoteVersion.solution_version_id == solution_version_id)
            .all()
        )

        results = []

        for ce in affected_estimations:
            results.append(
                {
                    "type": "cost_estimation",
                    "id": ce.id,
                    "version_no": ce.version_no,
                    "status": ce.status,
                    "impact": "需要重新评估成本",
                }
            )

        for qv in affected_quotes:
            results.append(
                {
                    "type": "quote_version",
                    "id": qv.id,
                    "quote_id": qv.quote_id,
                    "version_no": qv.version_no,
                    "impact": "需要更新绑定或重新报价",
                }
            )

        return results

    def _get_latest_approved_solution_version(
        self,
        solution_id: int,
    ) -> Optional[SolutionVersion]:
        """获取最新审批的方案版本"""
        return (
            self.db.query(SolutionVersion)
            .filter(
                SolutionVersion.solution_id == solution_id,
                SolutionVersion.status == "approved",
            )
            .order_by(SolutionVersion.approved_at.desc())
            .first()
        )
