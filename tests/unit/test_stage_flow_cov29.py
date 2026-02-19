# -*- coding: utf-8 -*-
"""第二十九批 - stage_instance/stage_flow.py 单元测试（StageFlowMixin）"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.stage_instance.stage_flow")

from app.services.stage_instance.stage_flow import StageFlowMixin
from app.models.enums import StageStatusEnum


# ─── 具体子类（用于测试 Mixin） ─────────────────────────────────────────────

class ConcreteStageFlow(StageFlowMixin):
    """用于测试的具体实现类"""

    def __init__(self, db):
        self.db = db


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_stage(
    stage_id=1,
    project_id=10,
    status=None,
    sequence=1,
):
    if status is None:
        status = StageStatusEnum.PENDING.value
    s = MagicMock()
    s.id = stage_id
    s.project_id = project_id
    s.status = status
    s.sequence = sequence
    s.actual_start_date = None
    s.actual_end_date = None
    s.remark = None
    s.is_modified = False
    return s


# ─── 测试：start_stage ────────────────────────────────────────────────────────

class TestStartStage:
    """测试 start_stage 方法"""

    def test_raises_when_stage_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="不存在"):
            flow.start_stage(stage_instance_id=999)

    def test_raises_when_stage_not_pending(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="无法开始"):
            flow.start_stage(stage_instance_id=1)

    def test_start_stage_success(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        db.query.return_value.filter.return_value.update.return_value = None
        flow = ConcreteStageFlow(db)
        result = flow.start_stage(stage_instance_id=1)
        assert result.status == StageStatusEnum.IN_PROGRESS.value

    def test_start_stage_uses_provided_date(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        db.query.return_value.filter.return_value.update.return_value = None
        flow = ConcreteStageFlow(db)
        custom_date = date(2025, 6, 1)
        result = flow.start_stage(stage_instance_id=1, actual_start_date=custom_date)
        assert result.actual_start_date == custom_date

    def test_start_stage_updates_project_current_stage(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.PENDING.value, stage_id=5, project_id=99)
        # 使用side_effect模拟两种query
        db.query.return_value.filter.return_value.first.return_value = stage
        update_mock = MagicMock()
        db.query.return_value.filter.return_value.update = update_mock
        flow = ConcreteStageFlow(db)
        flow.start_stage(stage_instance_id=5)
        # 验证update被调用来更新项目当前阶段
        update_mock.assert_called_once()


# ─── 测试：complete_stage ─────────────────────────────────────────────────────

class TestCompleteStage:
    """测试 complete_stage 方法"""

    def test_raises_when_stage_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="不存在"):
            flow.complete_stage(stage_instance_id=999)

    def test_raises_when_stage_not_in_progress(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="无法完成"):
            flow.complete_stage(stage_instance_id=1)

    def test_raises_when_incomplete_required_nodes(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value)

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = stage
            else:
                # count: 2 incomplete required nodes
                q.filter.return_value.filter.return_value.count.return_value = 2
                q.filter.return_value.count.return_value = 2
            return q

        db.query.side_effect = query_side_effect
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="必需节点未完成"):
            flow.complete_stage(stage_instance_id=1)

    def test_complete_stage_success_no_next(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value, sequence=2)
        incomplete_count = 0
        # first: stage query, second: incomplete nodes count, third: next_stage
        returns = iter([stage, None, None])
        db.query.return_value.filter.return_value.first.side_effect = lambda: next(returns, None)
        db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        flow = ConcreteStageFlow(db)
        current, next_stage = flow.complete_stage(stage_instance_id=1, auto_start_next=False)
        assert current.status == StageStatusEnum.COMPLETED.value
        assert next_stage is None


# ─── 测试：skip_stage ─────────────────────────────────────────────────────────

class TestSkipStage:
    """测试 skip_stage 方法"""

    def test_raises_when_stage_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="不存在"):
            flow.skip_stage(stage_instance_id=999)

    def test_raises_when_stage_completed(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.COMPLETED.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        flow = ConcreteStageFlow(db)
        with pytest.raises(ValueError, match="无法跳过"):
            flow.skip_stage(stage_instance_id=1)

    def test_skip_pending_stage(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        db.query.return_value.filter.return_value.filter.return_value.update.return_value = None
        db.query.return_value.filter.return_value.update.return_value = None
        flow = ConcreteStageFlow(db)
        result = flow.skip_stage(stage_instance_id=1, reason="测试跳过")
        assert result.status == StageStatusEnum.SKIPPED.value
        assert result.is_modified is True

    def test_skip_in_progress_stage(self):
        db = _make_db()
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value)
        db.query.return_value.filter.return_value.first.return_value = stage
        db.query.return_value.filter.return_value.filter.return_value.update.return_value = None
        flow = ConcreteStageFlow(db)
        result = flow.skip_stage(stage_instance_id=1)
        assert result.status == StageStatusEnum.SKIPPED.value
