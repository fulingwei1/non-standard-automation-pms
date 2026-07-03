# -*- coding: utf-8 -*-
"""
P0-1: 采购/外协/验收/立项 4 条审批链 template_code 与 DB 错位。

引擎按 template_code 查 approval_templates，查不到就抛 ValueError("审批模板不存在")。
4 个业务服务引用的 code 不在 DB 中（DB 用 TPL_* 命名，代码用 *_APPROVAL / PROJECT_TEMPLATE）。

正确行为：每一条业务审批链引用的 template_code 都必须在 approval_templates 里有对应模板。
当前必然失败 —— 失败即证明 4 条链从未真正跑通。
"""
import pytest

pytestmark = pytest.mark.audit_p0

# 业务服务里写死的 template_code -> 源码位置（report 第二节 A#1）
SERVICE_TEMPLATE_CODES = {
    "PURCHASE_ORDER_APPROVAL": "app/services/purchase_workflow/service.py:18",
    "OUTSOURCING_ORDER_APPROVAL": "app/services/outsourcing_workflow/outsourcing_workflow_service.py:21",
    "ACCEPTANCE_ORDER_APPROVAL": "app/services/acceptance_approval/service.py:70",
    "PROJECT_TEMPLATE": "app/api/v1/endpoints/projects/approvals/submit_new.py:94",
}


def _template_codes(conn):
    return {r[0] for r in conn.execute("SELECT template_code FROM approval_templates")}


@pytest.mark.parametrize("code", sorted(SERVICE_TEMPLATE_CODES))
def test_business_template_code_resolves_to_a_template(code, sandbox_conn):
    """正确行为：业务链引用的模板 code 应能在 DB 命中一个模板。当前 4 个都命中不了。

    DB 里存在同义的 TPL_* 模板，证明是命名错位（非缺库）。修好错位/加注册表后转绿。
    """
    codes = _template_codes(sandbox_conn)
    assert {"TPL_PURCHASE", "TPL_OUTSOURCING", "TPL_ACCEPTANCE", "TPL_PROJECT"} <= codes, (
        f"前置检查：TPL_* 基线模板应存在，实有 {sorted(codes)}"
    )
    assert code in codes, (
        f"审批链引用的模板 {code}（{SERVICE_TEMPLATE_CODES[code]}）在 approval_templates "
        f"中不存在；DB 实有: {sorted(codes)} -> 提交必抛『审批模板不存在』"
    )
