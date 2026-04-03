# -*- coding: utf-8 -*-
"""
行业最佳实践 P0 级优化 - 业务逻辑层

功能：
1. ABC 物料自动分级
2. 供应商动态升降级
3. 缺料自动升级通知
4. 齐套率阶段目标配置
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import (
    BomItem,
    Material,
    MaterialShortage,
    MaterialSupplier,
)
from app.models.project.core import Project
from app.models.vendor import Vendor
from app.schemas.best_practice import (
    ABCClassificationConfig,
    ABCClassificationResponse,
    ABCMaterialResult,
    EscalationRecord,
    KittingTargetsRequest,
    KittingTargetsResponse,
    ShortageEscalationConfig,
    ShortageEscalationResponse,
    StageKittingStatus,
    SupplierReclassifyConfig,
    SupplierReclassifyResponse,
    SupplierReclassifyResult,
)

# ABC 管理策略映射
ABC_STRATEGIES = {
    "A": (
        "重点管控：定期盘点（每月）、安全库存设置、多源采购、"
        "签订长期合同、密切跟踪交期、建立战略合作关系"
    ),
    "B": (
        "常规管控：定期盘点（每季度）、按需采购、"
        "维护 2-3 家合格供应商、关注价格波动"
    ),
    "C": (
        "简化管控：定期盘点（每半年）、批量采购降本、"
        "可适当增大订购批量、简化审批流程"
    ),
}

# 供应商等级顺序
SUPPLIER_LEVELS = ["D", "C", "B", "A", "S"]

# 阶段中文名
STAGE_NAMES = {
    "S3": "采购备料",
    "S4": "加工制造",
    "S5": "装配调试",
    "S6": "出厂验收",
}


class BestPracticeService:
    """行业最佳实践服务"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 1. ABC 物料自动分级
    # ------------------------------------------------------------------

    def abc_classification(
        self,
        config: ABCClassificationConfig,
        material_ids: Optional[List[int]] = None,
    ) -> ABCClassificationResponse:
        """
        按年消耗金额 + 采购周期 + 供应商数量综合分级。
        """
        # 查询物料
        query = self.db.query(Material).filter(Material.is_active.is_(True))
        if material_ids:
            query = query.filter(Material.id.in_(material_ids))
        materials = query.all()

        # 预加载每个物料的供应商数量
        supplier_counts = dict(
            self.db.query(
                MaterialSupplier.material_id,
                func.count(MaterialSupplier.id),
            )
            .filter(MaterialSupplier.is_active.is_(True))
            .group_by(MaterialSupplier.material_id)
            .all()
        )

        # 计算每个物料的年消耗金额（基于 BOM 用量 * 单价）
        annual_consumptions = dict(
            self.db.query(
                BomItem.material_id,
                func.sum(BomItem.amount),
            )
            .filter(BomItem.material_id.isnot(None))
            .group_by(BomItem.material_id)
            .all()
        )

        results: List[ABCMaterialResult] = []
        summary = {"A": 0, "B": 0, "C": 0}

        for mat in materials:
            annual = Decimal(str(annual_consumptions.get(mat.id, 0) or 0))
            lead_time = mat.lead_time_days or 0
            sup_count = supplier_counts.get(mat.id, 0)

            grade, reasons = self._determine_abc_grade(
                annual, lead_time, sup_count, config
            )
            summary[grade] += 1

            results.append(
                ABCMaterialResult(
                    material_id=mat.id,
                    material_code=mat.material_code,
                    material_name=mat.material_name,
                    annual_consumption=annual,
                    lead_time_days=lead_time,
                    supplier_count=sup_count,
                    grade=grade,
                    reasons=reasons,
                    strategy=ABC_STRATEGIES[grade],
                )
            )

        # 按分级排序：A → B → C
        grade_order = {"A": 0, "B": 1, "C": 2}
        results.sort(key=lambda r: (grade_order[r.grade], -r.annual_consumption))

        return ABCClassificationResponse(
            total=len(results),
            summary=summary,
            items=results,
        )

    @staticmethod
    def _determine_abc_grade(
        annual: Decimal,
        lead_time: int,
        supplier_count: int,
        config: ABCClassificationConfig,
    ) -> tuple:
        """判定 ABC 等级，返回 (grade, reasons)。"""
        reasons: List[str] = []

        # 规则 1：单一来源自动 A 类
        if config.single_source_auto_a and supplier_count <= 1:
            reasons.append(f"单一来源供应商（供应商数量={supplier_count}）")
            return "A", reasons

        # 规则 2：长采购周期自动 A 类
        if lead_time >= config.long_lead_time_days:
            reasons.append(
                f"采购周期 {lead_time} 天 ≥ 阈值 {config.long_lead_time_days} 天"
            )
            return "A", reasons

        # 规则 3：按年消耗金额分级
        if annual >= config.a_threshold:
            reasons.append(
                f"年消耗金额 {annual:,.0f} ≥ A 类阈值 {config.a_threshold:,.0f}"
            )
            return "A", reasons
        elif annual >= config.b_threshold:
            reasons.append(
                f"年消耗金额 {annual:,.0f} ≥ B 类阈值 {config.b_threshold:,.0f}"
            )
            return "B", reasons
        else:
            reasons.append(
                f"年消耗金额 {annual:,.0f} < B 类阈值 {config.b_threshold:,.0f}"
            )
            return "C", reasons

    # ------------------------------------------------------------------
    # 2. 供应商动态升降级
    # ------------------------------------------------------------------

    def supplier_reclassify(
        self,
        config: SupplierReclassifyConfig,
        supplier_ids: Optional[List[int]] = None,
        quarter_scores: Optional[List[Dict]] = None,
    ) -> SupplierReclassifyResponse:
        """
        基于季度绩效自动升降级。

        如果未传入 quarter_scores，则使用供应商模型上的 overall_rating 作为
        最近两个季度的绩效分数（简化模式）。
        """
        query = (
            self.db.query(Vendor)
            .filter(Vendor.vendor_type == "MATERIAL")
            .filter(Vendor.status != "ELIMINATED")
        )
        if supplier_ids:
            query = query.filter(Vendor.id.in_(supplier_ids))
        suppliers = query.all()

        # 构建季度分数索引
        score_map: Dict[int, List[Dict]] = {}
        if quarter_scores:
            for entry in quarter_scores:
                sid = entry.get("supplier_id")
                if sid:
                    score_map[sid] = entry.get("quarters", [])

        results: List[SupplierReclassifyResult] = []
        counts = {"upgraded": 0, "downgraded": 0, "eliminated": 0, "unchanged": 0}

        for sup in suppliers:
            quarters = score_map.get(sup.id)
            if not quarters:
                # 简化模式：用 overall_rating 模拟最近 N 个季度
                rating = float(sup.overall_rating or 0)
                quarters = [
                    {"quarter": f"Q{i+1}", "score": rating}
                    for i in range(config.consecutive_quarters)
                ]

            result = self._evaluate_supplier(sup, quarters, config)
            counts[
                {
                    "UPGRADE": "upgraded",
                    "DOWNGRADE": "downgraded",
                    "ELIMINATE": "eliminated",
                    "NO_CHANGE": "unchanged",
                }[result.action]
            ] += 1
            results.append(result)

        return SupplierReclassifyResponse(
            total=len(results),
            upgraded=counts["upgraded"],
            downgraded=counts["downgraded"],
            eliminated=counts["eliminated"],
            unchanged=counts["unchanged"],
            items=results,
        )

    def _evaluate_supplier(
        self,
        supplier: Vendor,
        quarters: List[Dict],
        config: SupplierReclassifyConfig,
    ) -> SupplierReclassifyResult:
        """评估单个供应商升降级。"""
        current_level = supplier.supplier_level or "B"
        recent = quarters[-config.consecutive_quarters :]
        scores = [Decimal(str(q.get("score", 0))) for q in recent]

        action = "NO_CHANGE"
        new_level = current_level
        reason = "绩效稳定，维持当前等级"
        recommendation = "继续保持合作关系"

        # 检查是否有重大质量问题（score=0 表示严重质量事故）
        if config.critical_quality_auto_eliminate and any(s == 0 for s in scores):
            action = "ELIMINATE"
            new_level = "D"
            reason = "存在重大质量问题（绩效为 0），直接淘汰"
            recommendation = "立即停止合作，启动替代供应商寻源"
        elif len(scores) >= config.consecutive_quarters and all(
            s >= config.upgrade_threshold for s in scores
        ):
            # 连续达标 → 升级
            idx = SUPPLIER_LEVELS.index(current_level) if current_level in SUPPLIER_LEVELS else 2
            if idx < len(SUPPLIER_LEVELS) - 1:
                new_level = SUPPLIER_LEVELS[idx + 1]
                action = "UPGRADE"
                avg = sum(scores) / len(scores)
                reason = (
                    f"连续 {config.consecutive_quarters} 季度绩效 ≥ "
                    f"{config.upgrade_threshold} 分（均分 {avg:.1f}）"
                )
                recommendation = (
                    f"升级为 {new_level} 级供应商，可增加订单份额、"
                    "优先考虑战略合作"
                )
        elif len(scores) >= config.consecutive_quarters and all(
            s < config.downgrade_threshold for s in scores
        ):
            # 连续不达标 → 降级
            idx = SUPPLIER_LEVELS.index(current_level) if current_level in SUPPLIER_LEVELS else 2
            if idx > 0:
                new_level = SUPPLIER_LEVELS[idx - 1]
                action = "DOWNGRADE"
                avg = sum(scores) / len(scores)
                reason = (
                    f"连续 {config.consecutive_quarters} 季度绩效 < "
                    f"{config.downgrade_threshold} 分（均分 {avg:.1f}）"
                )
                recommendation = (
                    f"降级为 {new_level} 级供应商，减少订单份额、"
                    "启动供应商辅导或替代寻源"
                )

        return SupplierReclassifyResult(
            supplier_id=supplier.id,
            supplier_code=supplier.supplier_code,
            supplier_name=supplier.supplier_name,
            current_level=current_level,
            new_level=new_level,
            action=action,
            reason=reason,
            recent_scores=[{"quarter": q.get("quarter", ""), "score": float(q.get("score", 0))} for q in quarters],
            recommendation=recommendation,
        )

    # ------------------------------------------------------------------
    # 3. 缺料自动升级通知
    # ------------------------------------------------------------------

    def shortage_escalation(
        self,
        config: ShortageEscalationConfig,
        project_id: Optional[int] = None,
    ) -> ShortageEscalationResponse:
        """
        检查所有 OPEN 状态的缺料记录，按延期天数分级通知。
        """
        query = self.db.query(MaterialShortage).filter(
            MaterialShortage.status == "OPEN"
        )
        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)
        shortages = query.all()

        today = date.today()
        items: List[EscalationRecord] = []
        summary = {"level_1": 0, "level_2": 0, "level_3": 0}

        # 预加载项目信息
        project_ids = {s.project_id for s in shortages}
        projects = {
            p.id: p
            for p in self.db.query(Project)
            .filter(Project.id.in_(project_ids))
            .all()
        } if project_ids else {}

        for shortage in shortages:
            if not shortage.required_date:
                continue

            overdue_days = (today - shortage.required_date).days
            if overdue_days < config.level1_days:
                continue

            level, roles, message = self._determine_escalation(
                shortage, overdue_days, config
            )
            level_key = f"level_{level}"
            summary[level_key] = summary.get(level_key, 0) + 1

            proj = projects.get(shortage.project_id)
            items.append(
                EscalationRecord(
                    shortage_id=shortage.id,
                    material_code=shortage.material_code,
                    material_name=shortage.material_name,
                    project_id=shortage.project_id,
                    project_code=proj.project_code if proj else None,
                    required_date=str(shortage.required_date),
                    overdue_days=overdue_days,
                    escalation_level=level,
                    notify_roles=roles,
                    message=message,
                    escalated_at=datetime.now().isoformat(),
                )
            )

        # 按延期天数降序排列（最紧急的在前）
        items.sort(key=lambda r: -r.overdue_days)

        return ShortageEscalationResponse(
            total_shortages_checked=len(shortages),
            escalated_count=len(items),
            escalation_summary=summary,
            items=items,
        )

    @staticmethod
    def _determine_escalation(
        shortage: MaterialShortage,
        overdue_days: int,
        config: ShortageEscalationConfig,
    ) -> tuple:
        """判定升级级别，返回 (level, roles, message)。"""
        mat_info = f"物料 {shortage.material_code}（{shortage.material_name}）"

        if overdue_days >= config.level3_days:
            return (
                3,
                ["总经理", "项目经理"],
                f"【紧急-三级升级】{mat_info} 延期 {overdue_days} 天（>={config.level3_days} 天），"
                f"请总经理及项目经理立即介入协调",
            )
        elif overdue_days >= config.level2_days:
            return (
                2,
                ["采购经理"],
                f"【警告-二级升级】{mat_info} 延期 {overdue_days} 天（{config.level2_days}-{config.level2_max_days} 天），"
                f"请采购经理跟进处理",
            )
        else:
            return (
                1,
                ["采购员"],
                f"【提醒-一级通知】{mat_info} 延期 {overdue_days} 天（{config.level1_days}-{config.level1_max_days} 天），"
                f"请采购员及时跟催",
            )

    # ------------------------------------------------------------------
    # 4. 齐套率阶段目标配置
    # ------------------------------------------------------------------

    def set_kitting_targets(
        self,
        project_id: int,
        request: KittingTargetsRequest,
    ) -> KittingTargetsResponse:
        """
        配置各阶段齐套率目标，并与实际齐套率对比。
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目 ID={project_id} 不存在")

        # 构建目标映射
        target_map: Dict[str, Decimal] = {}
        for t in request.targets:
            target_map[t.stage] = t.target_rate

        # 计算各阶段实际齐套率
        actual_rates = self._calc_kitting_rates(project_id)

        stages: List[StageKittingStatus] = []
        current_stage_met = True

        for stage_code in ["S3", "S4", "S5", "S6"]:
            target = target_map.get(stage_code)
            actual = actual_rates.get(stage_code)
            gap = None
            is_met = True
            alert = None

            if target is not None and actual is not None:
                gap = actual - target
                is_met = actual >= target
                if not is_met:
                    alert = (
                        f"{STAGE_NAMES.get(stage_code, stage_code)} 齐套率 "
                        f"{actual:.1f}% 未达目标 {target:.1f}%，差距 {abs(gap):.1f}%"
                    )
                    if stage_code == project.stage:
                        current_stage_met = False
            elif target is not None and actual is None:
                is_met = False
                alert = f"{STAGE_NAMES.get(stage_code, stage_code)} 暂无齐套率数据"
                if stage_code == project.stage:
                    current_stage_met = False

            stages.append(
                StageKittingStatus(
                    stage=stage_code,
                    stage_name=STAGE_NAMES.get(stage_code, stage_code),
                    target_rate=target,
                    actual_rate=actual,
                    gap=gap,
                    is_met=is_met,
                    alert=alert,
                )
            )

        return KittingTargetsResponse(
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            current_stage=project.stage or "S1",
            stages=stages,
            overall_met=current_stage_met,
        )

    def _calc_kitting_rates(self, project_id: int) -> Dict[str, Decimal]:
        """
        计算项目各阶段齐套率。

        齐套率 = 已到货行数 / 总需求行数 × 100

        简化逻辑：基于 BOM 明细的 received_qty vs quantity 计算。
        """
        from app.models.material import BomHeader

        bom_headers = (
            self.db.query(BomHeader)
            .filter(BomHeader.project_id == project_id)
            .all()
        )
        if not bom_headers:
            return {}

        bom_ids = [h.id for h in bom_headers]
        items = (
            self.db.query(BomItem)
            .filter(BomItem.bom_id.in_(bom_ids))
            .filter(BomItem.source_type == "PURCHASE")
            .all()
        )
        if not items:
            return {}

        total_count = len(items)
        kitted_count = sum(
            1
            for item in items
            if (item.received_qty or 0) >= (item.quantity or 0)
        )
        rate = Decimal(str(kitted_count * 100 / total_count)) if total_count > 0 else Decimal("0")

        # 简化：所有阶段使用相同的整体齐套率
        project = self.db.query(Project).filter(Project.id == project_id).first()
        current_stage = project.stage if project else "S3"

        result: Dict[str, Decimal] = {}
        for stage in ["S3", "S4", "S5", "S6"]:
            # 当前及之前的阶段有数据，之后的阶段暂无
            stage_order = {"S3": 3, "S4": 4, "S5": 5, "S6": 6}
            current_order = stage_order.get(current_stage, 3)
            if stage_order.get(stage, 3) <= current_order:
                result[stage] = rate

        return result
