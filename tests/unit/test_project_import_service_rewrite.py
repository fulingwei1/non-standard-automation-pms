# -*- coding: utf-8 -*-
"""兼容旧 project import rewrite 测试节点。"""

from unittest.mock import MagicMock

import pandas as pd

from app.services.project_import_service import get_column_value, populate_project_from_row


def _make_project(**kw):
    project = MagicMock()
    defaults = dict(
        id=1,
        project_code="BYD-2024-001",
        project_name="比亚迪ADAS ICT测试系统",
        stage="S1",
        status="ST01",
        health="H1",
        is_active=True,
    )
    defaults.update(kw)
    for key, value in defaults.items():
        setattr(project, key, value)
    return project


class TestGetColumnValue:
    def test_get_column_value_na(self):
        row = pd.Series({"项目编码*": pd.NA})
        assert get_column_value(row, "项目编码*") is None


class TestPopulateProjectFromRow:
    def test_populate_with_na_values(self):
        db = MagicMock()
        project = _make_project()
        row = pd.Series({"客户名称": pd.NA, "合同编号": pd.NA, "合同金额": pd.NA})

        populate_project_from_row(db, project, row)
