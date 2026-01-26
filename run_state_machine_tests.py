#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接运行状态机测试，验证框架正确性
"""

import sys

sys.path.insert(0, "/Users/flw/non-standard-automation-pm")

# Mock dependencies to avoid import errors
from unittest.mock import MagicMock

sys.modules["redis"] = MagicMock()
sys.modules["redis.exceptions"] = MagicMock()

# Direct imports
from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import (
    transition,
    before_transition,
    after_transition,
)
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    StateMachineValidationError,
)

print("=" * 60)
print("状态机框架单元测试")
print("=" * 60)


# Mock model and db for tests
class MockModel:
    def __init__(self):
        self.status = "DRAFT"


class SimpleStateMachine(StateMachine):
    def __init__(self, model, db):
        super().__init__(model, db, state_field="status")

    @transition(from_state="DRAFT", to_state="SUBMITTED")
    def submit(self, from_state, to_state, **kwargs):
        pass

    @transition(from_state="SUBMITTED", to_state="APPROVED")
    def approve(self, from_state, to_state, **kwargs):
        pass

    @transition(from_state="SUBMITTED", to_state="REJECTED")
    def reject(self, from_state, to_state, **kwargs):
        pass

    @transition(from_state="APPROVED", to_state="COMPLETED")
    def complete(self, from_state, to_state, **kwargs):
        pass

    @before_transition
    def before_hook(self, from_state, to_state, **kwargs):
        self.before_called = True

    @after_transition
    def after_hook(self, from_state, to_state, **kwargs):
        self.after_called = True


tests_passed = 0
tests_failed = 0

# Test 1: Test initialization
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    assert sm.current_state == "DRAFT"
    print("✓ Test 1: Initialization - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 1: Initialization - FAILED: {e}")
    tests_failed += 1

# Test 2: Test valid transition
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    result = sm.transition_to("SUBMITTED")
    assert result is True
    assert sm.current_state == "SUBMITTED"
    print("✓ Test 2: Valid transition - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 2: Valid transition - FAILED: {e}")
    tests_failed += 1

# Test 3: Test invalid transition
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    try:
        sm.transition_to("COMPLETED")
        print("✗ Test 3: Invalid transition - FAILED: Should have raised exception")
        tests_failed += 1
    except InvalidStateTransitionError:
        print("✓ Test 3: Invalid transition - PASSED (exception raised as expected)")
        tests_passed += 1
except Exception as e:
    print(f"✗ Test 3: Invalid transition - FAILED: {e}")
    tests_failed += 1

# Test 4: Test transition to same state
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    can, reason = sm.can_transition_to("DRAFT")
    assert not can
    assert "already" in reason
    print("✓ Test 4: Same state transition - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 4: Same state transition - FAILED: {e}")
    tests_failed += 1

# Test 5: Test transition history
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED")
    sm.transition_to("APPROVED")
    history = sm.get_transition_history()
    assert len(history) == 2
    print("✓ Test 5: Transition history - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 5: Transition history - FAILED: {e}")
    tests_failed += 1

# Test 6: Test allowed transitions
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    allowed = sm.get_allowed_transitions()
    assert "SUBMITTED" in allowed
    assert "APPROVED" not in allowed
    print("✓ Test 6: Allowed transitions - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 6: Allowed transitions - FAILED: {e}")
    tests_failed += 1

# Test 7: Test transition with kwargs
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED", user_id=123, note="test")
    history = sm.get_transition_history()
    assert history[-1]["user_id"] == 123
    assert history[-1]["note"] == "test"
    print("✓ Test 7: Transition with kwargs - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 7: Transition with kwargs - FAILED: {e}")
    tests_failed += 1

# Test 8: Test multiple transitions
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED")
    sm.transition_to("APPROVED")
    sm.transition_to("COMPLETED")
    assert sm.current_state == "COMPLETED"
    print("✓ Test 8: Multiple transitions - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 8: Multiple transitions - FAILED: {e}")
    tests_failed += 1

# Test 9: Test hooks
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED")
    assert sm.before_called is True
    assert sm.after_called is True
    print("✓ Test 9: Hooks - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 9: Hooks - FAILED: {e}")
    tests_failed += 1

# Test 10: Test transition with validator
try:

    class ValidatedStateMachine(StateMachine):
        def __init__(self, model, db):
            super().__init__(model, db, state_field="status")

        def validate(self, from_state, to_state):
            return True, ""

        @transition(from_state="DRAFT", to_state="SUBMITTED", validator=validate)
        def submit(self, from_state, to_state, **kwargs):
            pass

    model = MockModel()
    db = MagicMock()
    sm = ValidatedStateMachine(model, db)
    result = sm.transition_to("SUBMITTED")
    assert result is True
    print("✓ Test 10: Transition with validator - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 10: Transition with validator - FAILED: {e}")
    tests_failed += 1

# Test 11: Test validation failure
try:

    class ValidatedStateMachine2(StateMachine):
        def __init__(self, model, db):
            super().__init__(model, db, state_field="status")

        def validate(self, from_state, to_state):
            return False, "Validation failed"

        @transition(from_state="DRAFT", to_state="SUBMITTED", validator=validate)
        def submit(self, from_state, to_state, **kwargs):
            pass

    model = MockModel()
    db = MagicMock()
    sm = ValidatedStateMachine2(model, db)
    try:
        sm.transition_to("SUBMITTED")
        print("✗ Test 11: Validation failure - FAILED: Should have raised exception")
        tests_failed += 1
    except StateMachineValidationError:
        print("✓ Test 11: Validation failure - PASSED (exception raised as expected)")
        tests_passed += 1
except Exception as e:
    print(f"✗ Test 11: Validation failure - FAILED: {e}")
    tests_failed += 1

# Test 12: Test transition order in history
try:
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED", order=1)
    sm.transition_to("APPROVED", order=2)
    history = sm.get_transition_history()
    assert history[0]["order"] == 1
    assert history[1]["order"] == 2
    print("✓ Test 12: Transition order in history - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 12: Transition order in history - FAILED: {e}")
    tests_failed += 1

# Test 13: Test timestamp in history
try:
    from datetime import datetime

    before = datetime.now()
    model = MockModel()
    db = MagicMock()
    sm = SimpleStateMachine(model, db)
    sm.transition_to("SUBMITTED")
    history = sm.get_transition_history()
    assert before <= history[0]["timestamp"] <= datetime.now()
    print("✓ Test 13: Timestamp in history - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 13: Timestamp in history - FAILED: {e}")
    tests_failed += 1

# Test 14: Test hook failure doesn't prevent transition
try:

    class FailingHookStateMachine(StateMachine):
        def __init__(self, model, db):
            super().__init__(model, db, state_field="status")

        @transition(from_state="DRAFT", to_state="SUBMITTED")
        def submit(self, from_state, to_state, **kwargs):
            pass

        @before_transition
        def failing_hook(self, from_state, to_state, **kwargs):
            raise Exception("Hook failed")

    model = MockModel()
    db = MagicMock()
    sm = FailingHookStateMachine(model, db)
    # Transition should succeed even if hook fails
    result = sm.transition_to("SUBMITTED")
    assert result is True
    print("✓ Test 14: Hook failure doesn't prevent transition - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 14: Hook failure doesn't prevent transition - FAILED: {e}")
    tests_failed += 1

# Test 15: Test factory method
try:
    model = MockModel()
    db = MagicMock()
    sm = StateMachine.create(model, db, state_field="status")
    assert isinstance(sm, StateMachine)
    assert sm.model == model
    assert sm.db == db
    print("✓ Test 15: Factory method - PASSED")
    tests_passed += 1
except Exception as e:
    print(f"✗ Test 15: Factory method - FAILED: {e}")
    tests_failed += 1

# Summary
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)
print(f"总计: {tests_passed + tests_failed} 个测试")
print(f"通过: {tests_passed} 个")
print(f"失败: {tests_failed} 个")

if tests_failed == 0:
    print("\n🎉 状态机框架测试全部通过！框架正确性已验证。")
    print("=" * 60)
    sys.exit(0)
else:
    print(f"\n⚠️  有 {tests_failed} 个测试失败，请检查框架实现。")
    print("=" * 60)
    sys.exit(1)
