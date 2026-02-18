# -*- coding: utf-8 -*-
"""第二十四批 - stage_instance/initialization 单元测试"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.stage_instance.initialization")

from app.services.stage_instance.initialization import InitializationMixin


def _make_mixin():
    mixin = InitializationMixin()
    db = MagicMock()
    mixin.db = db
    return mixin, db


class TestInitializeProjectStagesErrors:
    def test_project_not_found_raises(self):
        mixin, db = _make_mixin()
        # Project query returns None
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        db.query.return_value = mock_q

        with pytest.raises(ValueError, match="项目.*不存在"):
            mixin.initialize_project_stages(project_id=99, template_id=1)

    def test_template_not_found_raises(self):
        mixin, db = _make_mixin()
        project_mock = MagicMock()

        results = iter([
            # 1st query(Project).filter().first() -> project found
            project_mock,
            # 2nd query(ProjectStageInstance).filter().count() -> 0
            None,
            # 3rd query(StageTemplate).options().filter().first() -> None
            None,
        ])

        # We'll use side_effect on the filter chain
        def make_q(return_val=None, count_val=0, first_val=None):
            q = MagicMock()
            q.filter.return_value.first.return_value = first_val
            q.filter.return_value.count.return_value = count_val
            q.options.return_value.filter.return_value.first.return_value = return_val
            return q

        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return make_q(first_val=project_mock)
            elif call_count[0] == 2:
                return make_q(count_val=0)
            else:
                return make_q(return_val=None)

        db.query.side_effect = query_side_effect

        with pytest.raises(ValueError, match="模板.*不存在"):
            mixin.initialize_project_stages(project_id=1, template_id=99)

    def test_existing_stages_raises(self):
        mixin, db = _make_mixin()
        project_mock = MagicMock()

        call_count = [0]
        def query_side_effect(*args):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = project_mock
            else:
                q.filter.return_value.count.return_value = 5  # has existing stages
            return q

        db.query.side_effect = query_side_effect

        with pytest.raises(ValueError, match="已有阶段实例"):
            mixin.initialize_project_stages(project_id=1, template_id=1)


class TestClearProjectStages:
    def test_clear_returns_count(self):
        mixin, db = _make_mixin()
        mock_q = MagicMock()
        mock_q.filter.return_value.update.return_value = None
        mock_q.filter.return_value.delete.return_value = 3
        db.query.return_value = mock_q

        result = mixin.clear_project_stages(project_id=1)
        assert result == 3

    def test_clear_calls_queries(self):
        mixin, db = _make_mixin()
        mock_q = MagicMock()
        mock_q.filter.return_value.update.return_value = None
        mock_q.filter.return_value.delete.return_value = 0
        db.query.return_value = mock_q

        mixin.clear_project_stages(project_id=2)
        # Should query Project, ProjectNodeInstance, ProjectStageInstance
        assert db.query.call_count >= 3

    def test_clear_with_zero_stages(self):
        mixin, db = _make_mixin()
        mock_q = MagicMock()
        mock_q.filter.return_value.update.return_value = None
        mock_q.filter.return_value.delete.return_value = 0
        db.query.return_value = mock_q

        result = mixin.clear_project_stages(project_id=99)
        assert result == 0
