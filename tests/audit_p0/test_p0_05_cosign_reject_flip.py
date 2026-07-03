# -*- coding: utf-8 -*-
"""
P0-5: 会签驳回语义破坏——REJECTED 实例可被翻转回 APPROVED。

复现需要：一个走 AND_SIGN 会签节点的实例（如 ECN_STANDARD flow4 节点1），
给两个审批人设已知密码，一人 reject 使实例 REJECTED，另一会签人再 approve
观察实例是否翻成 APPROVED。

现状：端到端造两个会签审批人 + 触发 ECN 会签流的成本高，30 分钟内跑不通稳定的
数据前置（沙箱库审批人/委托/节点解析依赖 ROLE 全库首个用户等）。按任务要求标记为
skip（受限），静态结论见报告 A#3：engine/approve.py:105-140 reject 不看会签汇总即
置 REJECTED、engine/core.py:246-263 approve 只看任务不看实例状态。

修复后应改写为：reject 后剩余会签人 approve，实例必须保持 REJECTED（不得翻转）。
"""
import pytest

pytestmark = pytest.mark.audit_p0


@pytest.mark.skip(reason="受限：会签双人 ECN 流端到端前置无法在时限内稳定构造；静态已确认，见报告 A#3")
def test_rejected_cosign_instance_cannot_flip_to_approved():
    # 目标断言（修复后启用）：
    #   1) 会签节点一人 reject -> 实例 REJECTED
    #   2) 另一会签人 approve -> 实例仍为 REJECTED（当前会翻成 APPROVED）
    ...
