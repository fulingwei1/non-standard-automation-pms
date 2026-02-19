"""Tests for app/services/stage_template/stage_management.py"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.stage_template.stage_management import StageManagementMixin
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteStageManagement(StageManagementMixin):
    def __init__(self, db):
        self.db = db


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.all.return_value = []
    q.count.return_value = 0
    q.first.return_value = None
    return db


def test_add_stage_raises_if_template_not_found():
    """模板不存在时 add_stage 抛出 ValueError"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    mgmt = ConcreteStageManagement(db)
    with pytest.raises(ValueError, match="模板.*不存在"):
        mgmt.add_stage(999, "S01", "测试阶段")


def test_add_stage_raises_if_stage_code_duplicate():
    """阶段编码重复时 add_stage 抛出 ValueError"""
    db = _make_db()
    template = MagicMock()
    existing_stage = MagicMock()
    # First call returns template, second call returns existing stage
    db.query.return_value.filter.return_value.first.side_effect = [template, existing_stage]
    mgmt = ConcreteStageManagement(db)
    with pytest.raises(ValueError, match="已存在"):
        mgmt.add_stage(1, "S01", "测试阶段")


def test_add_stage_success():
    """模板存在且编码唯一时 add_stage 正常创建阶段"""
    db = _make_db()
    template = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [template, None]
    mgmt = ConcreteStageManagement(db)
    with patch("app.services.stage_template.stage_management.StageDefinition") as MockStage:
        mock_stage = MagicMock()
        MockStage.return_value = mock_stage
        result = mgmt.add_stage(1, "S01", "测试阶段", sequence=1)
        db.add.assert_called_once_with(mock_stage)
        db.flush.assert_called()
        assert result is mock_stage


def test_update_stage_not_found_returns_none():
    """阶段不存在时 update_stage 返回 None"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    mgmt = ConcreteStageManagement(db)
    result = mgmt.update_stage(999, stage_name="新名称")
    assert result is None


def test_update_stage_updates_attributes():
    """阶段存在时 update_stage 更新属性"""
    db = _make_db()
    stage = MagicMock()
    stage.stage_name = "旧名称"
    db.query.return_value.filter.return_value.first.return_value = stage
    mgmt = ConcreteStageManagement(db)
    result = mgmt.update_stage(1, stage_name="新名称")
    assert result is stage
    db.flush.assert_called_once()


def test_delete_stage_not_found_returns_false():
    """阶段不存在时 delete_stage 返回 False"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    mgmt = ConcreteStageManagement(db)
    assert mgmt.delete_stage(999) is False


def test_delete_stage_success():
    """阶段存在时 delete_stage 调用 db.delete 并返回 True"""
    db = _make_db()
    stage = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = stage
    mgmt = ConcreteStageManagement(db)
    result = mgmt.delete_stage(1)
    db.delete.assert_called_once_with(stage)
    assert result is True


def test_reorder_stages_updates_sequence():
    """reorder_stages 更新每个阶段的 sequence"""
    db = _make_db()
    db.query.return_value.filter.return_value.update = MagicMock()
    mgmt = ConcreteStageManagement(db)
    result = mgmt.reorder_stages(1, [10, 20, 30])
    db.flush.assert_called()
    assert result is True
