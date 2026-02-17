# -*- coding: utf-8 -*-
"""
I2组 - 项目导出服务 单元测试
覆盖: app/services/project_export_service.py
"""
from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch, call
import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_project():
    p = MagicMock()
    p.id = 1
    p.project_code = "PJ-001"
    p.project_name = "测试项目"
    p.customer_name = "测试客户"
    p.contract_no = "CT-001"
    p.contract_amount = Decimal("100000.00")
    p.pm_name = "张经理"
    p.project_type = "标准型"
    p.stage = "S2"
    p.status = "ST01"
    p.health = "H1"
    p.progress_pct = Decimal("50.00")
    p.planned_start_date = date(2024, 1, 1)
    p.planned_end_date = date(2024, 12, 31)
    p.actual_start_date = date(2024, 1, 15)
    p.actual_end_date = None
    return p


def _make_mock_db(tasks=None, costs=None):
    db = MagicMock()
    tasks = tasks or []
    costs = costs or []

    def query_side_effect(model):
        from app.models.progress import Task
        try:
            from app.models.project import ProjectCost
            if model is ProjectCost:
                q = MagicMock()
                q.filter.return_value.order_by.return_value.all.return_value = costs
                return q
        except Exception:
            pass
        q = MagicMock()
        q.filter.return_value.order_by.return_value.all.return_value = tasks
        return q

    db.query.side_effect = query_side_effect
    return db


# ─── get_excel_styles ─────────────────────────────────────────────────────────

class TestGetExcelStyles:
    def test_returns_dict_when_available(self):
        from app.services.project_export_service import get_excel_styles, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        styles = get_excel_styles()
        assert "header_fill" in styles
        assert "header_font" in styles
        assert "title_font" in styles
        assert "border" in styles

    def test_returns_empty_when_unavailable(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import get_excel_styles
            result = get_excel_styles()
        assert result == {}


# ─── build_project_info_data ─────────────────────────────────────────────────

class TestBuildProjectInfoData:
    def test_returns_list_of_tuples(self):
        from app.services.project_export_service import build_project_info_data
        project = _make_project()
        result = build_project_info_data(project)

        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_contains_required_fields(self):
        from app.services.project_export_service import build_project_info_data
        project = _make_project()
        result = build_project_info_data(project)

        labels = [label for label, _ in result]
        assert "项目编码" in labels
        assert "项目名称" in labels
        assert "客户名称" in labels
        assert "项目经理" in labels

    def test_handles_none_amounts(self):
        from app.services.project_export_service import build_project_info_data
        project = _make_project()
        project.contract_amount = None
        project.progress_pct = None
        project.planned_start_date = None
        project.planned_end_date = None
        project.actual_start_date = None
        project.actual_end_date = None

        result = build_project_info_data(project)
        assert isinstance(result, list)
        # 不应抛出异常

    def test_date_formatting(self):
        from app.services.project_export_service import build_project_info_data
        project = _make_project()
        result = build_project_info_data(project)

        date_dict = dict(result)
        assert date_dict["计划开始日期"] == "2024-01-01"
        assert date_dict["计划结束日期"] == "2024-12-31"

    def test_amount_formatting(self):
        from app.services.project_export_service import build_project_info_data
        project = _make_project()
        result = build_project_info_data(project)
        data = dict(result)
        assert "100,000.00" in data["合同金额"]


# ─── add_project_info_sheet ───────────────────────────────────────────────────

class TestAddProjectInfoSheet:
    def test_noop_when_unavailable(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import add_project_info_sheet
            ws = MagicMock()
            add_project_info_sheet(ws, _make_project(), {})
        ws.merge_cells.assert_not_called()

    def test_writes_cells(self):
        from app.services.project_export_service import add_project_info_sheet, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        ws = MagicMock()
        mock_cell = MagicMock()
        ws.__getitem__ = MagicMock(return_value=mock_cell)
        ws.__setitem__ = MagicMock()
        ws.column_dimensions = {"A": MagicMock(), "B": MagicMock()}

        styles = {
            "title_font": MagicMock(),
            "border": MagicMock(),
        }
        add_project_info_sheet(ws, _make_project(), styles)

        ws.merge_cells.assert_called_once_with('A1:B1')


# ─── add_tasks_sheet ──────────────────────────────────────────────────────────

class TestAddTasksSheet:
    def test_noop_when_unavailable(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import add_tasks_sheet
            wb = MagicMock()
            add_tasks_sheet(wb, MagicMock(), 1, {})
        wb.create_sheet.assert_not_called()

    def test_creates_sheet_with_tasks(self):
        from app.services.project_export_service import add_tasks_sheet, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        mock_task = MagicMock()
        mock_task.task_code = "T-001"
        mock_task.task_name = "任务一"
        mock_task.task_type = "DEVELOP"
        mock_task.priority = "HIGH"
        mock_task.status = "IN_PROGRESS"
        mock_task.progress_pct = Decimal("60")
        mock_task.planned_start_date = date(2024, 1, 1)
        mock_task.planned_end_date = date(2024, 3, 31)
        mock_task.actual_start_date = date(2024, 1, 5)
        mock_task.actual_end_date = None
        mock_task.assignee_name = "开发者"
        mock_task.created_at = MagicMock()
        mock_task.created_at.strftime.return_value = "2024-01-01 00:00:00"

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

        wb = MagicMock()
        ws = MagicMock()
        ws.cell = MagicMock(return_value=MagicMock())
        ws.column_dimensions = {chr(64 + i): MagicMock() for i in range(1, 14)}
        wb.create_sheet.return_value = ws

        styles = {
            "header_fill": MagicMock(),
            "header_font": MagicMock(),
            "border": MagicMock(),
        }
        add_tasks_sheet(wb, db, 1, styles)
        wb.create_sheet.assert_called_once_with("任务列表")

    def test_empty_tasks(self):
        from app.services.project_export_service import add_tasks_sheet, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        wb = MagicMock()
        ws = MagicMock()
        ws.cell = MagicMock(return_value=MagicMock())
        ws.column_dimensions = {chr(64 + i): MagicMock() for i in range(1, 14)}
        wb.create_sheet.return_value = ws

        styles = {"header_fill": MagicMock(), "header_font": MagicMock(), "border": MagicMock()}
        add_tasks_sheet(wb, db, 1, styles)
        wb.create_sheet.assert_called_once()


# ─── add_costs_sheet ──────────────────────────────────────────────────────────

class TestAddCostsSheet:
    def test_noop_when_unavailable(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import add_costs_sheet
            wb = MagicMock()
            add_costs_sheet(wb, MagicMock(), 1, {})
        wb.create_sheet.assert_not_called()

    def test_creates_costs_sheet(self):
        from app.services.project_export_service import add_costs_sheet, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        mock_cost = MagicMock()
        mock_cost.cost_date = date(2024, 1, 10)
        mock_cost.cost_type = "人工"
        mock_cost.cost_category = "直接成本"
        mock_cost.amount = Decimal("5000.00")
        mock_cost.currency = "CNY"
        mock_cost.description = "1月人工费用"
        mock_cost.created_at = MagicMock()
        mock_cost.created_at.strftime.return_value = "2024-01-10 00:00:00"

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_cost]

        wb = MagicMock()
        ws = MagicMock()
        ws.cell = MagicMock(return_value=MagicMock())
        ws.column_dimensions = {chr(64 + i): MagicMock() for i in range(1, 9)}
        wb.create_sheet.return_value = ws

        styles = {"header_fill": MagicMock(), "header_font": MagicMock(), "border": MagicMock()}
        add_costs_sheet(wb, db, 1, styles)
        wb.create_sheet.assert_called_once_with("成本列表")


# ─── create_project_detail_excel ─────────────────────────────────────────────

class TestCreateProjectDetailExcel:
    def test_raises_when_unavailable(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import create_project_detail_excel
            with pytest.raises(ImportError):
                create_project_detail_excel(MagicMock(), _make_project(), True, True)

    def test_returns_bytes_io(self):
        from app.services.project_export_service import create_project_detail_excel, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch("app.services.project_export_service.add_tasks_sheet"), \
             patch("app.services.project_export_service.add_costs_sheet"), \
             patch("app.services.project_export_service.add_project_info_sheet"):
            result = create_project_detail_excel(db, _make_project(), True, True)

        assert isinstance(result, BytesIO)

    def test_no_tasks_no_costs(self):
        from app.services.project_export_service import create_project_detail_excel, OPENPYXL_AVAILABLE
        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl 未安装")

        db = MagicMock()

        with patch("app.services.project_export_service.add_tasks_sheet") as mock_tasks, \
             patch("app.services.project_export_service.add_costs_sheet") as mock_costs, \
             patch("app.services.project_export_service.add_project_info_sheet"):
            result = create_project_detail_excel(db, _make_project(), False, False)
            mock_tasks.assert_not_called()
            mock_costs.assert_not_called()

        assert isinstance(result, BytesIO)
