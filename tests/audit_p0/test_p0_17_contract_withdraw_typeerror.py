# -*- coding: utf-8 -*-
"""
P0-17: 合同/验收/报价/ECN 撤回必 500（引擎参数名 user_id vs initiator_id）。

引擎签名 withdraw(instance_id, initiator_id, comment=None)，但 4 处业务服务传
`user_id=` -> 必然 TypeError；端点只 catch ValueError -> 撤回 500，单据永卡审批中。

正确行为：4 个业务服务应使用引擎接受的参数名（initiator_id），不得传 user_id。
静态复现（源码调用点检查），修好 4 行后转绿。
"""
import re

import pytest

pytestmark = pytest.mark.audit_p0

WITHDRAW_CALL_SITES = [
    "app/services/contract_approval/service.py",
    "app/services/acceptance_approval/service.py",
    "app/services/quote_approval/quote_approval_service.py",
    "app/services/ecn/approval/service.py",
]


def test_engine_withdraw_signature_has_no_user_id():
    """诊断根因：引擎 withdraw 不接受 user_id（稳定守卫，说明为何 user_id= 会崩）。"""
    import inspect

    from app.services.approval_engine.engine.actions import ApprovalActionsMixin

    params = inspect.signature(ApprovalActionsMixin.withdraw).parameters
    assert "initiator_id" in params
    assert "user_id" not in params

    # 复刻业务服务的错误调用形态 -> 必抛 TypeError
    with pytest.raises(TypeError):
        ApprovalActionsMixin.withdraw(object(), instance_id=1, user_id=1)


@pytest.mark.parametrize("rel", WITHDRAW_CALL_SITES)
def test_withdraw_call_uses_engine_param_name(rel, repo_root):
    src = (repo_root / rel).read_text(encoding="utf-8")
    # 找到对 withdraw( 的调用，检查是否误传 user_id=
    bad = re.findall(r"withdraw\([^)]*user_id\s*=", src)
    assert not bad, (
        f"{rel} 以 user_id= 调用 engine.withdraw（引擎只接受 initiator_id）"
        f" -> 撤回必 TypeError->500，单据永卡 PENDING_APPROVAL"
    )
