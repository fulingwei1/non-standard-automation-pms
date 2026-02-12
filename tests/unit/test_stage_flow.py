# -*- coding: utf-8 -*-
"""阶段状态流转 单元测试"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import StageStatusEnum
from app.services.stage_instance.stage_flow import StageFlowMixin


def _make_mixin():
    m = StageFlowMixin()
    m.db = MagicMock()
    return m


def _make_stage(status="PENDING", sequence=1, project_id=1):
    s = MagicMock()
    s.id = 1
    s.status = status
    s.sequence = sequence
    s.project_id = project_id
    return s


class TestStartStage:
    def test_success(self):
        m = _make_mixin()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        m.db.query.return_value.filter.return_value.first.return_value = stage
        result = m.start_stage(1)
        assert result.status == StageStatusEnum.IN_PROGRESS.value

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.start_stage(999)

    def test_wrong_status(self):
        m = _make_mixin()
        stage = _make_stage(status=StageStatusEnum.COMPLETED.value)
        m.db.query.return_value.filter.return_value.first.return_value = stage
        with pytest.raises(ValueError, match="无法开始"):
            m.start_stage(1)


class TestCompleteStage:
    def test_incomplete_required_nodes(self):
        m = _make_mixin()
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value)
        # first call returns stage, second call for count returns 2
        m.db.query.return_value.filter.return_value.first.return_value = stage
        m.db.query.return_value.filter.return_value.count.return_value = 2
        with pytest.raises(ValueError, match="必需节点未完成"):
            m.complete_stage(1)

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.complete_stage(999)


class TestSkipStage:
    def test_success(self):
        m = _make_mixin()
        stage = _make_stage(status=StageStatusEnum.PENDING.value)
        m.db.query.return_value.filter.return_value.first.return_value = stage
        m.db.query.return_value.filter.return_value.update.return_value = None
        result = m.skip_stage(1, reason="不需要")
        assert result.status == StageStatusEnum.SKIPPED.value

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.skip_stage(999)
