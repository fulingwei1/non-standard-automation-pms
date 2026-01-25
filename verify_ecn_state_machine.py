#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 ECN 状态机实现
"""

import sys

sys.path.insert(0, "/Users/flw/non-standard-automation-pm")

# Mock dependencies
from unittest.mock import MagicMock

sys.modules["redis"] = MagicMock()
sys.modules["redis.exceptions"] = MagicMock()

print("=" * 60)
print("ECN 状态机实现验证")
print("=" * 60)

# Test 1: Import EcnStateMachine
try:
    from app.core.state_machine import EcnStateMachine

    print("✓ Test 1: EcnStateMachine 导入成功")
    import_success = True
except Exception as e:
    print(f"✗ Test 1: 导入失败 - {e}")
    import_success = False

# Test 2: Create instance
try:

    class MockEcnModel:
        def __init__(self):
            self.status = "DRAFT"
            self.change_reason = "测试变更"
            self.change_description = "测试描述"
            self.ecn_type = "DC"
            self.approval_note = None
            self.approved_at = None
            self.execution_start = None

    model = MockEcnModel()
    db = MagicMock()
    sm = EcnStateMachine(model, db)
    print("✓ Test 2: EcnStateMachine 实例创建成功")
    print(f"   当前状态: {sm.current_state}")
    instance_success = True
except Exception as e:
    print(f"✗ Test 2: 实例创建失败 - {e}")
    instance_success = False

# Test 3: Check allowed transitions from DRAFT
try:
    allowed = sm.get_allowed_transitions()
    print("✓ Test 3: 获取允许的转换成功")
    print(f"   DRAFT 状态允许的转换: {allowed}")
    transitions_success = True
except Exception as e:
    print(f"✗ Test 3: 获取允许转换失败 - {e}")
    transitions_success = False

# Test 4: Test DRAFT → PENDING_REVIEW
try:
    result = sm.transition_to("PENDING_REVIEW")
    if result:
        print("✓ Test 4: DRAFT → PENDING_REVIEW 转换成功")
        print(f"   当前状态: {sm.current_state}")
        submit_success = True
    else:
        print("✗ Test 4: DRAFT → PENDING_REVIEW 转换失败")
        submit_success = False
except Exception as e:
    print(f"✗ Test 4: DRAFT → PENDING_REVIEW 转换失败 - {e}")
    submit_success = False

# Test 5: Test PENDING_REVIEW → APPROVED
try:
    model.approval_note = "审批通过"
    from datetime import datetime

    model.approved_at = datetime.now()

    result = sm.transition_to("APPROVED")
    if result:
        print("✓ Test 5: PENDING_REVIEW → APPROVED 转换成功")
        print(f"   当前状态: {sm.current_state}")
        approve_success = True
    else:
        print("✗ Test 5: PENDING_REVIEW → APPROVED 转换失败")
        approve_success = False
except Exception as e:
    print(f"✗ Test 5: PENDING_REVIEW → APPROVED 转换失败 - {e}")
    approve_success = False

# Test 6: Test APPROVED → IMPLEMENTED
try:
    result = sm.transition_to("IMPLEMENTED")
    if result:
        print("✓ Test 6: APPROVED → IMPLEMENTED 转换成功")
        print(f"   当前状态: {sm.current_state}")
        implement_success = True
    else:
        print("✗ Test 6: APPROVED → IMPLEMENTED 转换失败")
        implement_success = False
except Exception as e:
    print(f"✗ Test 6: APPROVED → IMPLEMENTED 转换失败 - {e}")
    implement_success = False

# Test 7: Check helper methods
try:
    editable = sm.is_editable()
    cancellable = sm.is_cancellable()
    status_label = sm.get_status_label()
    print("✓ Test 7: 辅助方法测试成功")
    print(f"   可编辑: {editable}")
    print(f"   可取消: {cancellable}")
    print(f"   状态标签: {status_label}")
    helper_success = True
except Exception as e:
    print(f"✗ Test 7: 辅助方法测试失败 - {e}")
    helper_success = False

# Test 8: Check transition history
try:
    history = sm.get_transition_history()
    print("✓ Test 8: 转换历史测试成功")
    print(f"   转换次数: {len(history)}")
    for i, transition in enumerate(history, 1):
        print(f"   转换 {i}: {transition['from_state']} → {transition['to_state']}")
    history_success = True
except Exception as e:
    print(f"✗ Test 8: 转换历史测试失败 - {e}")
    history_success = False

# Summary
print("\n" + "=" * 60)
print("验证总结")
print("=" * 60)

tests_passed = sum(
    [
        import_success,
        instance_success,
        transitions_success,
        submit_success,
        approve_success,
        implement_success,
        helper_success,
        history_success,
    ]
)

tests_total = 8

print(f"总计: {tests_total} 个测试")
print(f"通过: {tests_passed} 个")
print(f"失败: {tests_total - tests_passed} 个")

if tests_passed == tests_total:
    print("\n🎉 ECN 状态机实现验证全部通过！")
    print("=" * 60)
    sys.exit(0)
else:
    print(f"\n⚠️  有 {tests_total - tests_passed} 个测试失败，请检查实现。")
    print("=" * 60)
    sys.exit(1)
