# -*- coding: utf-8 -*-
"""
状态机装饰器单元测试
"""

from app.core.state_machine import StateMachine
from app.core.state_machine.decorators import (
    transition,
    before_transition,
    after_transition,
)


class MockModel:
    """模拟模型"""

    def __init__(self):
        self.status = "DRAFT"


class TestDecorators:
    """装饰器测试"""

    def setup_method(self):
        """每个测试前设置"""
        self.model = MockModel()
        self.db = type("MockDB", (), {})()

    def test_transition_decorator_registers_transition(self):
        """测试 @transition 装饰器注册转换"""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(from_state="DRAFT", to_state="SUBMITTED")
            def submit(self, from_state, to_state, **kwargs):
                pass

        sm = TestSM(self.model, self.db)

        # 检查转换是否被注册
        assert hasattr(TestSM.submit, "_is_transition")
        assert TestSM.submit._is_transition is True
        assert TestSM.submit._from_state == "DRAFT"
        assert TestSM.submit._to_state == "SUBMITTED"

    def test_before_transition_decorator_registers_hook(self):
        """测试 @before_transition 装饰器注册钩子"""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(from_state="DRAFT", to_state="SUBMITTED")
            def submit(self, from_state, to_state, **kwargs):
                pass

            @before_transition
            def before_hook(self, from_state, to_state, **kwargs):
                pass

        sm = TestSM(self.model, self.db)

        # 检查 before 钩子是否被注册
        assert hasattr(TestSM.before_hook, "_before_hook")
        assert TestSM.before_hook._before_hook is not None

    def test_after_transition_decorator_registers_hook(self):
        """测试 @after_transition 装饰器注册钩子"""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(from_state="DRAFT", to_state="SUBMITTED")
            def submit(self, from_state, to_state, **kwargs):
                pass

            @after_transition
            def after_hook(self, from_state, to_state, **kwargs):
                pass

        sm = TestSM(self.model, self.db)

        # 检查 after 钩子是否被注册
        assert hasattr(TestSM.after_hook, "_after_hook")
        assert TestSM.after_hook._after_hook is not None

    def test_multiple_transitions_registration(self):
        """测试多个转换注册"""

        class TestSM(StateMachine):
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

        sm = TestSM(self.model, self.db)

        # 检查所有转换是否被正确注册
        transitions = sm._transitions
        assert ("DRAFT", "SUBMITTED") in transitions
        assert ("SUBMITTED", "APPROVED") in transitions
        assert ("SUBMITTED", "REJECTED") in transitions

    def test_transition_with_validator(self):
        """测试带验证器的转换"""

        def validate_test(sm, from_state, to_state):
            return True, ""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(
                from_state="DRAFT", to_state="SUBMITTED", validator=validate_test
            )
            def submit(self, from_state, to_state, **kwargs):
                pass

        sm = TestSM(self.model, self.db)

        # 检查验证器是否被注册
        transition_func = sm._transitions[("DRAFT", "SUBMITTED")]
        assert hasattr(transition_func, "_validator")
        assert transition_func._validator is not None

    def test_decorator_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(from_state="DRAFT", to_state="SUBMITTED")
            def submit(self, from_state, to_state, **kwargs):
                """提交函数"""
                pass

        # 检查函数名称和文档是否被保留
        assert TestSM.submit.__name__ == "submit"
        assert TestSM.submit.__doc__ == """提交函数"""

    def test_transition_decorator_with_none_validator(self):
        """测试没有验证器的转换"""

        class TestSM(StateMachine):
            def __init__(self, model, db):
                super().__init__(model, db, state_field="status")

            @transition(from_state="DRAFT", to_state="SUBMITTED", validator=None)
            def submit(self, from_state, to_state, **kwargs):
                pass

        sm = TestSM(self.model, self.db)

        # 检查验证器为 None
        transition_func = sm._transitions[("DRAFT", "SUBMITTED")]
        assert hasattr(transition_func, "_validator")
        assert transition_func._validator is None
