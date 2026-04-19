# -*- coding: utf-8 -*-
"""adjustments单元测试"""

from app.services.stage_instance.adjustments import AdjustmentsMixin


class TestAdjustmentsMixinInit:
    def test_methods_available(self):
        assert AdjustmentsMixin is not None
        assert hasattr(AdjustmentsMixin, "add_custom_node")
        assert hasattr(AdjustmentsMixin, "update_node_planned_date")
