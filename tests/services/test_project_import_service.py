# -*- coding: utf-8 -*-
"""项目导入服务单元测试 (ProjectImportService)"""
import io
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi import HTTPException

from app.services import project_import_service as pis


def _make_db():
    """创建数据库 mock"""
    return MagicMock()


def _make_customer(**kw):
    """创建客户 mock"""
    c = MagicMock()
    defaults = dict(
        id=1,
        customer_name="比亚迪",
        contact_person="张三",
        contact_phone="13800138000",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(c, k, v)
    return c


def _make_user(**kw):
    """创建用户 mock"""
    u = MagicMock()
    defaults = dict(
        id=1,
        username="zhangsan",
        real_name="张三",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(u, k, v)
    return u


def _make_project(**kw):
    """创建项目 mock"""
    p = MagicMock()
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
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


class TestValidateExcelFile:
    """测试 Excel 文件验证"""

    def test_valid_xlsx_file(self):
        """测试有效的 .xlsx 文件"""
        pis.validate_excel_file("projects.xlsx")  # 不应抛出异常

    def test_valid_xls_file(self):
        """测试有效的 .xls 文件"""
        pis.validate_excel_file("projects.xls")  # 不应抛出异常

    def test_invalid_file_extension(self):
        """测试无效的文件扩展名"""
        with pytest.raises(HTTPException) as exc:
            pis.validate_excel_file("projects.csv")
        assert exc.value.status_code == 400
        assert "只支持Excel文件" in exc.value.detail

    def test_no_extension(self):
        """测试没有扩展名的文件"""
        with pytest.raises(HTTPException) as exc:
            pis.validate_excel_file("projects")
        assert exc.value.status_code == 400


class TestParseExcelData:
    """测试 Excel 数据解析"""

    @patch("app.services.project_import_service.ImportExportEngine.parse_excel")
    def test_successful_parse(self, mock_parse):
        """测试成功解析 Excel 文件"""
        df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["测试项目"]})
        mock_parse.return_value = df

        result = pis.parse_excel_data(b"fake_excel_content")
        assert len(result) == 1
        assert result.iloc[0]["项目编码*"] == "P001"

    @patch("app.services.project_import_service.ImportExportEngine.parse_excel")
    def test_empty_file(self, mock_parse):
        """测试空文件"""
        mock_parse.return_value = pd.DataFrame()

        with pytest.raises(HTTPException) as exc:
            pis.parse_excel_data(b"fake_excel_content")
        assert exc.value.status_code == 400
        assert "没有数据" in exc.value.detail

    @patch("app.services.project_import_service.ImportExportEngine.parse_excel")
    def test_parse_exception(self, mock_parse):
        """测试解析异常"""
        mock_parse.side_effect = Exception("文件损坏")

        with pytest.raises(HTTPException) as exc:
            pis.parse_excel_data(b"fake_excel_content")
        assert exc.value.status_code == 400
        assert "解析失败" in exc.value.detail


class TestValidateProjectColumns:
    """测试项目列验证"""

    def test_all_required_columns_present_with_asterisk(self):
        """测试所有必需列都存在（带*）"""
        df = pd.DataFrame({"项目编码*": [], "项目名称*": []})
        pis.validate_project_columns(df)  # 不应抛出异常

    def test_all_required_columns_present_without_asterisk(self):
        """测试所有必需列都存在（不带*）"""
        df = pd.DataFrame({"项目编码": [], "项目名称": []})
        pis.validate_project_columns(df)  # 不应抛出异常

    def test_missing_project_code(self):
        """测试缺少项目编码列"""
        df = pd.DataFrame({"项目名称*": []})
        with pytest.raises(HTTPException) as exc:
            pis.validate_project_columns(df)
        assert exc.value.status_code == 400
        assert "项目编码" in exc.value.detail

    def test_missing_project_name(self):
        """测试缺少项目名称列"""
        df = pd.DataFrame({"项目编码*": []})
        with pytest.raises(HTTPException) as exc:
            pis.validate_project_columns(df)
        assert "项目名称" in exc.value.detail

    def test_missing_both_columns(self):
        """测试缺少所有必需列"""
        df = pd.DataFrame({"其他列": []})
        with pytest.raises(HTTPException) as exc:
            pis.validate_project_columns(df)
        assert "项目编码" in exc.value.detail
        assert "项目名称" in exc.value.detail


class TestGetColumnValue:
    """测试列值获取"""

    def test_get_value_from_primary_column(self):
        """测试从主列获取值"""
        row = pd.Series({"项目编码*": "P001", "项目编码": "P002"})
        value = pis.get_column_value(row, "项目编码*")
        assert value == "P001"

    def test_get_value_from_alt_column(self):
        """测试从备用列获取值"""
        row = pd.Series({"项目编码": "P002"})
        value = pis.get_column_value(row, "项目编码*")
        assert value == "P002"

    def test_get_value_strips_whitespace(self):
        """测试去除空白字符"""
        row = pd.Series({"项目编码*": "  P001  "})
        value = pis.get_column_value(row, "项目编码*")
        assert value == "P001"

    def test_get_value_returns_none_for_nan(self):
        """测试 NaN 返回 None"""
        row = pd.Series({"项目编码*": pd.NA})
        value = pis.get_column_value(row, "项目编码*")
        assert value is None

    def test_get_value_returns_none_for_empty_string(self):
        """测试空字符串返回 None"""
        row = pd.Series({"项目编码*": ""})
        value = pis.get_column_value(row, "项目编码*")
        assert value is None

    def test_get_value_with_custom_alt_column(self):
        """测试自定义备用列名"""
        row = pd.Series({"col_a": "value_a", "col_b": "value_b"})
        value = pis.get_column_value(row, "col_a", "col_b")
        assert value == "value_a"


class TestParseProjectRow:
    """测试项目行数据解析"""

    def test_parse_valid_row(self):
        """测试解析有效的行"""
        row = pd.Series({"项目编码*": "P001", "项目名称*": "测试项目"})
        code, name, errors = pis.parse_project_row(row, 0)
        assert code == "P001"
        assert name == "测试项目"
        assert errors == []

    def test_parse_row_without_asterisk(self):
        """测试解析不带*的列名"""
        row = pd.Series({"项目编码": "P001", "项目名称": "测试项目"})
        code, name, errors = pis.parse_project_row(row, 0)
        assert code == "P001"
        assert name == "测试项目"

    def test_parse_row_missing_code(self):
        """测试缺少项目编码"""
        row = pd.Series({"项目名称*": "测试项目"})
        code, name, errors = pis.parse_project_row(row, 0)
        assert code is None
        assert name is None
        assert len(errors) > 0
        assert "不能为空" in errors[0]

    def test_parse_row_missing_name(self):
        """测试缺少项目名称"""
        row = pd.Series({"项目编码*": "P001"})
        code, name, errors = pis.parse_project_row(row, 0)
        assert code is None
        assert name is None
        assert len(errors) > 0

    def test_parse_row_with_nan_values(self):
        """测试包含 NaN 值的行"""
        row = pd.Series({"项目编码*": pd.NA, "项目名称*": pd.NA})
        code, name, errors = pis.parse_project_row(row, 0)
        assert len(errors) > 0


class TestFindOrCreateCustomer:
    """测试客户查找/创建"""

    def test_find_existing_customer(self):
        """测试查找现有客户"""
        db = _make_db()
        customer = _make_customer(customer_name="比亚迪")
        db.query.return_value.filter.return_value.first.return_value = customer

        result = pis.find_or_create_customer(db, "比亚迪")
        assert result is customer

    def test_customer_not_found_returns_none(self):
        """测试客户不存在返回 None"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = pis.find_or_create_customer(db, "不存在的客户")
        assert result is None

    def test_empty_customer_name_returns_none(self):
        """测试空客户名返回 None"""
        db = _make_db()
        result = pis.find_or_create_customer(db, "")
        assert result is None


class TestFindProjectManager:
    """测试项目经理查找"""

    def test_find_by_real_name(self):
        """测试按真实姓名查找"""
        db = _make_db()
        pm = _make_user(real_name="张三")
        db.query.return_value.filter.return_value.first.return_value = pm

        result = pis.find_project_manager(db, "张三")
        assert result is pm

    def test_find_by_username_when_real_name_not_found(self):
        """测试真实姓名未找到时按用户名查找"""
        db = _make_db()
        pm = _make_user(username="zhangsan")

        # 第一次查询（按真实姓名）返回 None，第二次查询（按用户名）返回用户
        query_mock = db.query.return_value
        query_mock.filter.return_value.first.side_effect = [None, pm]

        result = pis.find_project_manager(db, "zhangsan")
        assert result is pm

    def test_pm_not_found_returns_none(self):
        """测试项目经理不存在返回 None"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        result = pis.find_project_manager(db, "不存在的用户")
        assert result is None

    def test_empty_pm_name_returns_none(self):
        """测试空项目经理名返回 None"""
        db = _make_db()
        result = pis.find_project_manager(db, "")
        assert result is None


class TestParseDateValue:
    """测试日期解析"""

    def test_parse_valid_date_string(self):
        """测试解析有效的日期字符串"""
        result = pis.parse_date_value("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_datetime_object(self):
        """测试解析 datetime 对象"""
        dt = pd.Timestamp("2024-01-15")
        result = pis.parse_date_value(dt)
        assert result == date(2024, 1, 15)

    def test_parse_nan_returns_none(self):
        """测试解析 NaN 返回 None"""
        result = pis.parse_date_value(pd.NA)
        assert result is None

    def test_parse_invalid_date_returns_none(self):
        """测试解析无效日期返回 None"""
        result = pis.parse_date_value("invalid-date")
        assert result is None

    def test_parse_none_returns_none(self):
        """测试解析 None 返回 None"""
        result = pis.parse_date_value(None)
        assert result is None


class TestParseDecimalValue:
    """测试金额解析"""

    def test_parse_valid_decimal_string(self):
        """测试解析有效的金额字符串"""
        result = pis.parse_decimal_value("123456.78")
        assert result == Decimal("123456.78")

    def test_parse_integer(self):
        """测试解析整数"""
        result = pis.parse_decimal_value(100000)
        assert result == Decimal("100000")

    def test_parse_float(self):
        """测试解析浮点数"""
        result = pis.parse_decimal_value(123.45)
        assert isinstance(result, Decimal)

    def test_parse_nan_returns_none(self):
        """测试解析 NaN 返回 None"""
        result = pis.parse_decimal_value(pd.NA)
        assert result is None

    def test_parse_invalid_value_returns_none(self):
        """测试解析无效值返回 None"""
        result = pis.parse_decimal_value("abc")
        assert result is None

    def test_parse_none_returns_none(self):
        """测试解析 None 返回 None"""
        result = pis.parse_decimal_value(None)
        assert result is None


class TestPopulateProjectFromRow:
    """测试项目数据填充"""

    def test_populate_customer_info(self):
        """测试填充客户信息"""
        db = _make_db()
        project = _make_project()
        customer = _make_customer(
            id=10,
            customer_name="比亚迪",
            contact_person="李四",
            contact_phone="13900139000",
        )
        db.query.return_value.filter.return_value.first.return_value = customer

        row = pd.Series({"客户名称": "比亚迪"})
        pis.populate_project_from_row(db, project, row)

        assert project.customer_id == 10
        assert project.customer_name == "比亚迪"
        assert project.customer_contact == "李四"
        assert project.customer_phone == "13900139000"

    def test_populate_contract_info(self):
        """测试填充合同信息"""
        db = _make_db()
        project = _make_project()

        row = pd.Series({
            "合同编号": "HT-2024-001",
            "项目类型": "研发项目",
            "合同日期": "2024-01-15",
            "合同金额": 500000,
            "预算金额": 450000,
        })
        pis.populate_project_from_row(db, project, row)

        assert project.contract_no == "HT-2024-001"
        assert project.project_type == "研发项目"
        assert project.contract_date == date(2024, 1, 15)
        assert project.contract_amount == Decimal("500000")
        assert project.budget_amount == Decimal("450000")

    def test_populate_dates(self):
        """测试填充日期"""
        db = _make_db()
        project = _make_project()

        row = pd.Series({
            "计划开始日期": "2024-01-01",
            "计划结束日期": "2024-12-31",
        })
        pis.populate_project_from_row(db, project, row)

        assert project.planned_start_date == date(2024, 1, 1)
        assert project.planned_end_date == date(2024, 12, 31)

    def test_populate_project_manager(self):
        """测试填充项目经理"""
        db = _make_db()
        project = _make_project()
        pm = _make_user(id=5, real_name="王五", username="wangwu")

        # 模拟第一次查询（按真实姓名）返回用户
        db.query.return_value.filter.return_value.first.return_value = pm

        row = pd.Series({"项目经理": "王五"})
        pis.populate_project_from_row(db, project, row)

        assert project.pm_id == 5
        assert project.pm_name == "王五"

    def test_populate_description(self):
        """测试填充项目描述"""
        db = _make_db()
        project = _make_project()

        row = pd.Series({"项目描述": "这是一个测试项目"})
        pis.populate_project_from_row(db, project, row)

        assert project.description == "这是一个测试项目"

    def test_populate_with_nan_values(self):
        """测试填充包含 NaN 值的数据"""
        db = _make_db()
        project = _make_project()

        row = pd.Series({
            "客户名称": pd.NA,
            "合同编号": pd.NA,
            "合同金额": pd.NA,
        })
        pis.populate_project_from_row(db, project, row)
        # 不应抛出异常


class TestImportProjectsFromDataframe:
    """测试从 DataFrame 导入项目"""

    @patch("app.services.project_import_service.init_project_stages")
    def test_import_new_project_successfully(self, mock_init_stages):
        """测试成功导入新项目"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None  # 项目不存在

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["测试项目"],
        })

        imported, updated, failed = pis.import_projects_from_dataframe(
            db, df, update_existing=False
        )

        assert imported == 1
        assert updated == 0
        assert len(failed) == 0
        db.add.assert_called_once()
        mock_init_stages.assert_called_once()

    def test_import_duplicate_project_without_update(self):
        """测试导入重复项目（不更新）"""
        db = _make_db()
        existing_project = _make_project(project_code="P001")
        db.query.return_value.filter.return_value.first.return_value = existing_project

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["测试项目"],
        })

        imported, updated, failed = pis.import_projects_from_dataframe(
            db, df, update_existing=False
        )

        assert imported == 0
        assert updated == 0
        assert len(failed) == 1
        assert "已存在" in failed[0]["error"]

    @patch("app.services.project_import_service.init_project_stages")
    def test_update_existing_project(self, mock_init_stages):
        """测试更新现有项目"""
        db = _make_db()
        existing_project = _make_project(project_code="P001")
        db.query.return_value.filter.return_value.first.return_value = existing_project

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["更新后的项目"],
            "项目描述": ["新描述"],
        })

        imported, updated, failed = pis.import_projects_from_dataframe(
            db, df, update_existing=True
        )

        assert imported == 0
        assert updated == 1
        assert len(failed) == 0
        db.add.assert_not_called()  # 更新时不调用 add
        mock_init_stages.assert_not_called()  # 更新时不初始化阶段

    def test_import_row_with_missing_required_fields(self):
        """测试导入缺少必需字段的行"""
        db = _make_db()

        df = pd.DataFrame({
            "项目编码*": ["P001", pd.NA],
            "项目名称*": ["测试项目", "无编码项目"],
        })

        imported, updated, failed = pis.import_projects_from_dataframe(
            db, df, update_existing=False
        )

        assert imported == 1  # 只有第一行成功
        assert len(failed) == 1  # 第二行失败
        assert failed[0]["row_index"] == 3  # Excel 第3行（0-based index 1 + 2）

    def test_import_multiple_projects(self):
        """测试批量导入多个项目"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        df = pd.DataFrame({
            "项目编码*": ["P001", "P002", "P003"],
            "项目名称*": ["项目1", "项目2", "项目3"],
        })

        with patch("app.services.project_import_service.init_project_stages"):
            imported, updated, failed = pis.import_projects_from_dataframe(
                db, df, update_existing=False
            )

        assert imported == 3
        assert updated == 0
        assert len(failed) == 0

    def test_import_with_exception_handling(self):
        """测试异常处理"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.side_effect = Exception("数据库错误")

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["测试项目"],
        })

        imported, updated, failed = pis.import_projects_from_dataframe(
            db, df, update_existing=False
        )

        assert imported == 0
        assert updated == 0
        assert len(failed) == 1
        assert "数据库错误" in failed[0]["error"]

    def test_import_mixed_success_and_failure(self):
        """测试混合成功和失败的导入"""
        db = _make_db()

        # 第一个项目成功，第二个项目失败（缺少名称）
        df = pd.DataFrame({
            "项目编码*": ["P001", "P002"],
            "项目名称*": ["项目1", pd.NA],
        })

        # 模拟查询：第一个项目不存在
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.project_import_service.init_project_stages"):
            imported, updated, failed = pis.import_projects_from_dataframe(
                db, df, update_existing=False
            )

        assert imported == 1
        assert updated == 0
        assert len(failed) == 1
        assert failed[0]["row_index"] == 3

    def test_import_with_full_data(self):
        """测试导入完整数据的项目"""
        db = _make_db()
        customer = _make_customer(customer_name="比亚迪")
        pm = _make_user(real_name="张三")

        # 模拟查询
        query_mock = db.query.return_value.filter.return_value
        query_mock.first.side_effect = [
            None,  # 项目不存在
            customer,  # 客户查询
            pm,  # 项目经理查询（按真实姓名）
        ]

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["完整项目"],
            "客户名称": ["比亚迪"],
            "项目经理": ["张三"],
            "合同编号": ["HT-001"],
            "合同金额": [500000],
            "计划开始日期": ["2024-01-01"],
            "计划结束日期": ["2024-12-31"],
        })

        with patch("app.services.project_import_service.init_project_stages"):
            imported, updated, failed = pis.import_projects_from_dataframe(
                db, df, update_existing=False
            )

        assert imported == 1
        assert updated == 0
        assert len(failed) == 0
