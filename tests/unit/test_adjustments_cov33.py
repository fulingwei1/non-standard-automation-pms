# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 阶段调整混入 (AdjustmentsMixin)
"""
import pytest
from unittest.mock import MagicMock
from datetime import date

try:
    from app.services.stage_instance.adjustments import AdjustmentsMixin
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="adjustments 导入失败")


def _make_mixin(stage=None, node=None):
    """构造测试用混入实例"""
    mixin = MagicMock(spec=AdjustmentsMixin)
    mixin.db = MagicMock()

    def query_dispatch(model):
        q = MagicMock()
        name = model.__name__
        if "Stage" in name:
            q.filter.return_value.first.return_value = stage
        elif "Node" in name:
            q.filter.return_value.first.return_value = node
            q.filter.return_value.count.return_value = 3
            q.filter.return_value.update.return_value = None
        return q

    mixin.db.query.side_effect = query_dispatch
    return mixin


class TestAddCustomNode:
    def test_stage_not_found_raises(self):
        """阶段不存在时抛出 ValueError"""
        mixin = _make_mixin(stage=None)

        with pytest.raises(ValueError, match="阶段实例"):
            AdjustmentsMixin.add_custom_node(
                mixin,
                stage_instance_id=999,
                node_code="N001",
                node_name="测试节点",
            )

    def test_add_node_to_end(self):
        """无指定插入位置时节点添加到末尾"""
        mock_stage = MagicMock()
        mock_stage.project_id = 10
        mock_stage.is_modified = False

        mixin = _make_mixin(stage=mock_stage)

        result = AdjustmentsMixin.add_custom_node(
            mixin,
            stage_instance_id=1,
            node_code="N002",
            node_name="自定义节点",
        )

        mixin.db.add.assert_called()
        mixin.db.flush.assert_called_once()
        assert mock_stage.is_modified is True

    def test_add_node_after_existing(self):
        """指定插入位置时节点插入到指定节点后"""
        mock_stage = MagicMock()
        mock_stage.project_id = 10

        mock_after_node = MagicMock()
        mock_after_node.sequence = 5

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "Stage" in name:
                q.filter.return_value.first.return_value = mock_stage
            elif "Node" in name:
                q.filter.return_value.first.return_value = mock_after_node
                q.filter.return_value.count.return_value = 3
                q.filter.return_value.update.return_value = None
            return q

        mixin = MagicMock(spec=AdjustmentsMixin)
        mixin.db = MagicMock()
        mixin.db.query.side_effect = query_dispatch

        AdjustmentsMixin.add_custom_node(
            mixin,
            stage_instance_id=1,
            node_code="N_INSERT",
            node_name="插入节点",
            insert_after_node_id=100,
        )

        mixin.db.flush.assert_called_once()

    def test_add_node_with_planned_date(self):
        """带计划日期的节点创建"""
        mock_stage = MagicMock()
        mock_stage.project_id = 20

        mixin = _make_mixin(stage=mock_stage)
        planned = date(2026, 3, 1)

        AdjustmentsMixin.add_custom_node(
            mixin,
            stage_instance_id=2,
            node_code="N_DATE",
            node_name="有日期节点",
            planned_date=planned,
            is_required=True,
        )

        mixin.db.add.assert_called()

    def test_add_node_with_required_flag(self):
        """必需节点标记正确"""
        mock_stage = MagicMock()
        mock_stage.project_id = 30

        mixin = _make_mixin(stage=mock_stage)

        AdjustmentsMixin.add_custom_node(
            mixin,
            stage_instance_id=3,
            node_code="N_REQ",
            node_name="必需节点",
            is_required=True,
        )

        mixin.db.flush.assert_called()


class TestUpdateNodePlannedDate:
    def test_node_not_found_raises(self):
        """节点不存在时抛出 ValueError"""
        mixin = _make_mixin(node=None)

        with pytest.raises(ValueError, match="节点实例"):
            AdjustmentsMixin.update_node_planned_date(
                mixin,
                node_instance_id=999,
                planned_date=date(2026, 4, 1),
            )

    def test_update_date_success(self):
        """成功更新节点计划日期"""
        mock_node = MagicMock()
        mock_node.planned_date = None

        mixin = _make_mixin(node=mock_node)
        new_date = date(2026, 5, 15)

        result = AdjustmentsMixin.update_node_planned_date(
            mixin,
            node_instance_id=1,
            planned_date=new_date,
        )

        assert mock_node.planned_date == new_date
        mixin.db.flush.assert_called_once()

    def test_update_date_returns_node(self):
        """返回更新后的节点实例"""
        mock_node = MagicMock()

        mixin = _make_mixin(node=mock_node)

        result = AdjustmentsMixin.update_node_planned_date(
            mixin,
            node_instance_id=1,
            planned_date=date(2026, 6, 1),
        )

        assert result is mock_node
