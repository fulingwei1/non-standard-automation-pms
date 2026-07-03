# -*- coding: utf-8 -*-
"""
P0-1: 采购/外协/验收/立项 4 条审批链 template_code 与 DB 错位。

引擎按 template_code 查 approval_templates，查不到就抛 ValueError("审批模板不存在")。
4 个业务服务引用的 code 不在 DB 中（DB 用 TPL_* 命名，代码用 *_APPROVAL / PROJECT_TEMPLATE）。

正确行为：每一条业务审批链必须引用当前库里的 TPL_* 模板，而不是靠库里保留错名别名。
当前必然失败 —— 失败即证明 4 条链从未真正跑通。
"""
import pytest

pytestmark = pytest.mark.audit_p0

EXPECTED_BUSINESS_TEMPLATE_CODES = {
    "PURCHASE_ORDER": (
        "TPL_PURCHASE",
        "app/services/purchase_workflow/service.py",
    ),
    "OUTSOURCING_ORDER": (
        "TPL_OUTSOURCING",
        "app/services/outsourcing_workflow/outsourcing_workflow_service.py",
    ),
    "ACCEPTANCE_ORDER": (
        "TPL_ACCEPTANCE",
        "app/services/acceptance_approval/service.py",
    ),
    "PROJECT": (
        "TPL_PROJECT",
        "app/api/v1/endpoints/projects/approvals/submit_new.py",
    ),
}


def _template_codes(conn):
    return {r[0] for r in conn.execute("SELECT template_code FROM approval_templates")}


def _business_template_codes():
    from app.api.v1.endpoints.projects.approvals import submit_new
    from app.services.acceptance_approval import service as acceptance_service
    from app.services.outsourcing_workflow.outsourcing_workflow_service import (
        OutsourcingWorkflowService,
    )
    from app.services.purchase_workflow.service import PurchaseWorkflowService

    return {
        "PURCHASE_ORDER": PurchaseWorkflowService.template_code,
        "OUTSOURCING_ORDER": OutsourcingWorkflowService.template_code,
        "ACCEPTANCE_ORDER": getattr(acceptance_service, "ACCEPTANCE_APPROVAL_TEMPLATE_CODE", None),
        "PROJECT": getattr(submit_new, "PROJECT_APPROVAL_TEMPLATE_CODE", None),
    }


@pytest.mark.parametrize("entity_type", sorted(EXPECTED_BUSINESS_TEMPLATE_CODES))
def test_business_template_code_resolves_to_a_template(entity_type, sandbox_conn):
    """正确行为：业务链实际引用的模板 code 应等于现有 TPL_* 模板并能在 DB 命中。

    如果业务代码仍引用旧错名，即使库里有 TPL_* 基线模板，提交也会抛『审批模板不存在』。
    """
    codes = _template_codes(sandbox_conn)
    assert {"TPL_PURCHASE", "TPL_OUTSOURCING", "TPL_ACCEPTANCE", "TPL_PROJECT"} <= codes, (
        f"前置检查：TPL_* 基线模板应存在，实有 {sorted(codes)}"
    )
    actual_code = _business_template_codes()[entity_type]
    expected_code, source = EXPECTED_BUSINESS_TEMPLATE_CODES[entity_type]
    assert actual_code == expected_code, (
        f"{entity_type} 审批链应引用 {expected_code}，但 {source} 当前引用 {actual_code!r}"
    )
    assert actual_code in codes, (
        f"审批链引用的模板 {actual_code}（{source}）在 approval_templates "
        f"中不存在；DB 实有: {sorted(codes)}"
    )
