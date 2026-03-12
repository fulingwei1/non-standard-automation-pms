# -*- coding: utf-8 -*-
"""
销售模块 SQLAlchemy 事件监听器

自动维护销售模块各实体间的数据一致性：
1. 合同金额变更 → 更新商机预估金额
2. 报价状态变更 → 更新商机阶段
3. 发票收款状态变更 → 更新合同收款统计
4. 合同状态变更 → 更新商机阶段
"""

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import event
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _get_session(target) -> Optional[Session]:
    """从目标对象获取Session"""
    from sqlalchemy.orm import object_session

    return object_session(target)


# ==================== 合同金额变更 → 商机预估金额同步 ====================


def sync_opportunity_amount_from_contract(mapper, connection, target):
    """
    合同金额变更时，自动更新关联商机的预估金额

    触发条件：Contract 表 INSERT 或 UPDATE
    """
    from app.models.sales import Opportunity

    if not target.opportunity_id:
        return

    session = _get_session(target)
    if not session:
        return

    try:
        opportunity = session.query(Opportunity).filter(
            Opportunity.id == target.opportunity_id
        ).first()

        if opportunity and target.total_amount:
            old_amount = opportunity.est_amount
            opportunity.est_amount = target.total_amount
            logger.info(
                f"商机金额同步: Opportunity {opportunity.id} "
                f"金额从 {old_amount} 更新为 {target.total_amount}"
            )
    except Exception as e:
        logger.error(f"同步商机金额失败: {e}")


# ==================== 报价状态变更 → 商机阶段更新 ====================


def update_opportunity_stage_on_quote_status(mapper, connection, target):
    """
    报价状态变更时，自动更新商机阶段

    业务规则（仅前进，不回退）：
    - SUBMITTED → PROPOSAL（方案介绍阶段）
    - APPROVED → NEGOTIATION（价格谈判阶段）
    - ACCEPTED → CLOSING（成交促成阶段）
    - REJECTED → 保持当前阶段（不回退）
    """
    from app.models.enums import OpportunityStageEnum, QuoteStatusEnum
    from app.models.sales import Opportunity

    if not target.opportunity_id:
        return

    session = _get_session(target)
    if not session:
        return

    # 统一转换为字符串值进行比较（兼容枚举和字符串）
    status_value = target.status.value if hasattr(target.status, "value") else target.status

    stage_mapping = {
        QuoteStatusEnum.SUBMITTED.value: OpportunityStageEnum.PROPOSAL.value,
        QuoteStatusEnum.APPROVED.value: OpportunityStageEnum.NEGOTIATION.value,
        QuoteStatusEnum.ACCEPTED.value: OpportunityStageEnum.CLOSING.value,
    }

    new_stage = stage_mapping.get(status_value)
    if not new_stage:
        return

    try:
        opportunity = session.query(Opportunity).filter(
            Opportunity.id == target.opportunity_id
        ).first()

        if opportunity:
            old_stage = opportunity.stage.value if hasattr(opportunity.stage, "value") else opportunity.stage

            # 定义阶段顺序（用字符串值）
            stage_order = [
                OpportunityStageEnum.DISCOVERY.value,
                OpportunityStageEnum.QUALIFICATION.value,
                OpportunityStageEnum.PROPOSAL.value,
                OpportunityStageEnum.NEGOTIATION.value,
                OpportunityStageEnum.CLOSING.value,
                OpportunityStageEnum.WON.value,
                OpportunityStageEnum.LOST.value,
            ]

            # 仅在阶段前进时更新（不允许回退）
            old_index = stage_order.index(old_stage) if old_stage in stage_order else -1
            new_index = stage_order.index(new_stage) if new_stage in stage_order else -1

            if old_index >= 0 and new_index > old_index:
                opportunity.stage = new_stage
                logger.info(
                    f"商机阶段同步: Opportunity {opportunity.id} "
                    f"阶段从 {old_stage} 推进为 {new_stage}"
                )
    except Exception as e:
        logger.error(f"同步商机阶段失败: {e}")


# ==================== 发票收款 → 合同收款统计更新 ====================


def update_contract_payment_stats_on_invoice(mapper, connection, target):
    """
    发票收款金额变更时，更新合同收款统计

    自动计算合同的已收款金额、未收款金额、收款进度
    """
    from app.models.sales import Contract, Invoice

    if not target.contract_id:
        return

    session = _get_session(target)
    if not session:
        return

    try:
        # 汇总该合同下所有发票的已收款金额
        total_paid = session.query(Invoice).filter(
            Invoice.contract_id == target.contract_id
        ).with_entities(
            Invoice.paid_amount
        ).all()

        paid_sum = sum((p.paid_amount or Decimal("0")) for p in total_paid)

        contract = session.query(Contract).filter(
            Contract.id == target.contract_id
        ).first()

        if contract:
            contract.received_amount = paid_sum
            # 计算收款进度（仅用于日志，Contract 模型无 payment_progress 字段）
            progress = Decimal("0")
            if contract.total_amount and contract.total_amount > 0:
                progress = min((paid_sum / contract.total_amount) * 100, Decimal("100"))
            logger.info(
                f"合同收款同步: Contract {contract.id} "
                f"已收款 {paid_sum}, 进度 {progress:.1f}%"
            )
    except Exception as e:
        logger.error(f"同步合同收款统计失败: {e}")


# ==================== 合同状态变更 → 商机阶段更新 ====================


def update_opportunity_stage_on_contract_status(mapper, connection, target):
    """
    合同状态变更时，更新商机阶段

    业务规则：
    - SIGNED → WON（赢单），同时记录成交日期
    - CANCELLED → CLOSING（回退到成交促成阶段，而非直接输单）
    - ACTIVE → 保持 WON（合同进入执行阶段）
    - COMPLETED → 保持 WON（合同完成）
    """
    from datetime import date

    from app.models.enums import ContractStatusEnum, OpportunityStageEnum
    from app.models.sales import Opportunity

    if not target.opportunity_id:
        return

    session = _get_session(target)
    if not session:
        return

    try:
        opportunity = session.query(Opportunity).filter(
            Opportunity.id == target.opportunity_id
        ).first()

        if not opportunity:
            return

        old_stage = opportunity.stage

        if target.status == ContractStatusEnum.SIGNED:
            if opportunity.stage != OpportunityStageEnum.WON:
                opportunity.stage = OpportunityStageEnum.WON
                # 记录实际成交日期（复用 expected_close_date 字段）
                if not opportunity.expected_close_date:
                    opportunity.expected_close_date = date.today()
                logger.info(
                    f"商机状态同步: Opportunity {opportunity.id} "
                    f"从 {old_stage} 标记为赢单 (WON)"
                )

        elif target.status == ContractStatusEnum.CANCELLED:
            # 合同取消时，商机回退到 CLOSING（而非直接输单，给销售补救机会）
            if opportunity.stage == OpportunityStageEnum.WON:
                opportunity.stage = OpportunityStageEnum.CLOSING
                logger.info(
                    f"商机状态同步: Opportunity {opportunity.id} "
                    f"合同取消，从 WON 回退到 CLOSING"
                )
            # 如果商机本就不是 WON，保持原状态

    except Exception as e:
        logger.error(f"同步商机状态失败: {e}")


# ==================== 商机状态变更 → 报价/合同反向联动 ====================


def sync_related_entities_on_opportunity_lost(mapper, connection, target):
    """
    商机标记为输单时，自动处理关联的报价和合同

    业务规则：
    - 草稿/提交中的报价自动标记为过期（EXPIRED）
    - 草稿合同自动取消
    - 已签订的合同保持不变（需人工处理）
    """
    from app.models.enums import ContractStatusEnum, OpportunityStageEnum, QuoteStatusEnum
    from app.models.sales import Contract, Quote

    # 仅处理变为 LOST 的情况
    stage_value = target.stage.value if hasattr(target.stage, "value") else target.stage
    if stage_value != OpportunityStageEnum.LOST.value:
        return

    session = _get_session(target)
    if not session:
        return

    try:
        # 将未完成的报价标记为过期
        pending_quotes = session.query(Quote).filter(
            Quote.opportunity_id == target.id,
            Quote.status.in_([
                QuoteStatusEnum.DRAFT.value,
                QuoteStatusEnum.SUBMITTED.value,
            ])
        ).all()

        for quote in pending_quotes:
            quote.status = QuoteStatusEnum.EXPIRED.value
            logger.info(f"商机输单联动: Quote {quote.id} 标记为过期")

        # 将草稿合同取消
        draft_contracts = session.query(Contract).filter(
            Contract.opportunity_id == target.id,
            Contract.status.in_([
                ContractStatusEnum.DRAFT.value,
                ContractStatusEnum.REVIEW.value,
            ])
        ).all()

        for contract in draft_contracts:
            contract.status = ContractStatusEnum.CANCELLED.value
            logger.info(f"商机输单联动: Contract {contract.id} 标记为取消")

    except Exception as e:
        logger.error(f"处理商机输单联动失败: {e}")


# ==================== 注册事件监听器 ====================


def register_sales_event_listeners():
    """
    注册所有销售模块事件监听器

    在应用启动时调用此函数
    """
    from app.models.sales import Contract, Invoice, Opportunity, Quote

    # 合同金额同步（合同创建/更新 → 商机金额同步）
    event.listen(Contract, "after_insert", sync_opportunity_amount_from_contract)
    event.listen(Contract, "after_update", sync_opportunity_amount_from_contract)

    # 报价状态同步（报价状态变更 → 商机阶段推进）
    event.listen(Quote, "after_update", update_opportunity_stage_on_quote_status)

    # 发票收款同步（发票收款 → 合同收款统计更新）
    event.listen(Invoice, "after_update", update_contract_payment_stats_on_invoice)

    # 合同状态同步（合同签订/取消 → 商机状态更新）
    event.listen(Contract, "after_update", update_opportunity_stage_on_contract_status)

    # 商机输单反向联动（商机输单 → 报价过期、草稿合同取消）
    event.listen(Opportunity, "after_update", sync_related_entities_on_opportunity_lost)

    logger.info("销售模块事件监听器已注册（共6个监听器）")


def unregister_sales_event_listeners():
    """
    注销所有销售模块事件监听器

    用于测试场景
    """
    from app.models.sales import Contract, Invoice, Opportunity, Quote

    event.remove(Contract, "after_insert", sync_opportunity_amount_from_contract)
    event.remove(Contract, "after_update", sync_opportunity_amount_from_contract)
    event.remove(Quote, "after_update", update_opportunity_stage_on_quote_status)
    event.remove(Invoice, "after_update", update_contract_payment_stats_on_invoice)
    event.remove(Contract, "after_update", update_opportunity_stage_on_contract_status)
    event.remove(Opportunity, "after_update", sync_related_entities_on_opportunity_lost)

    logger.info("销售模块事件监听器已注销")
