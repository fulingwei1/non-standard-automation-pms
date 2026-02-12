# -*- coding: utf-8 -*-
"""
发票自动服务 - 验证功能
"""
from app.models.acceptance import AcceptanceOrder, AcceptanceIssue
from app.models.project import ProjectPaymentPlan


def check_deliverables_complete(service: "InvoiceAutoService", plan: ProjectPaymentPlan) -> bool:
    """
    检查交付物是否齐全

    简化实现：检查合同交付物是否都已交付
    """
    if not plan.contract_id:
        return True  # 如果没有合同，默认交付物齐全

    from app.models.sales import Contract
    contract = service.db.query(Contract).filter(
        Contract.id == plan.contract_id
    ).first()

    if not contract:
        return True

    # 检查合同交付物（这里简化处理，实际应该检查所有必需交付物）
    # 如果有交付物表，可以检查交付状态
    # 这里默认返回 True，表示交付物齐全
    return True


def check_acceptance_issues_resolved(service: "InvoiceAutoService", order: AcceptanceOrder) -> bool:
    """
    检查验收问题是否已全部解决

    规则：存在未闭环的阻塞问题时，不能开票

    Args:
        service: InvoiceAutoService实例
        order: 验收单对象

    Returns:
        bool: True表示所有阻塞问题已解决，可以开票；False表示存在未解决的阻塞问题
    """
    # 查找所有阻塞问题
    blocking_issues = service.db.query(AcceptanceIssue).filter(
        AcceptanceIssue.order_id == order.id,
        AcceptanceIssue.is_blocking,
        AcceptanceIssue.status.in_(["OPEN", "PROCESSING", "RESOLVED", "DEFERRED"])
    ).all()

    if not blocking_issues:
        return True  # 没有阻塞问题，可以开票

    # 检查是否有未闭环的阻塞问题
    for issue in blocking_issues:
        if issue.status == "RESOLVED":
            # 已解决的问题需要验证通过才能算闭环
            if issue.verified_result != "VERIFIED":
                return False  # 存在已解决但未验证的问题
        else:
            # OPEN, PROCESSING, DEFERRED 状态的问题都算未闭环
            return False

    return True  # 所有阻塞问题都已解决并验证通过
