from unittest.mock import MagicMock

import pytest

from app.api.v1.endpoints.data_import_export import validators


class FakePd:
    @staticmethod
    def isna(value):
        return value is None


def make_db(*first_results):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = list(first_results) or [None]
    return db


@pytest.mark.unit
def test_row_level_validators_cover_valid_and_invalid_inputs():
    errors = []
    assert validators._validate_project_row({"项目编码*": "P-1", "项目名称*": "项目A"}, 2, errors) is True
    assert validators._validate_user_row({"名字": "张三"}, 3, errors) is True
    assert validators._validate_timesheet_row(
        {"工作日期*": "2026-01-01", "人员姓名*": "李四", "工时(小时)*": 8},
        4,
        errors,
        FakePd,
    ) is True
    assert validators._validate_task_row({"任务名称*": "调试", "项目编码*": "P-1"}, 5, errors) is True
    assert validators._validate_material_row({"物料编码*": "M-1", "物料名称*": "电机"}, 6, errors) is True
    assert validators._validate_bom_row(
        {"BOM编码*": "B-1", "项目编码*": "P-1", "物料编码*": "M-1", "用量*": 2},
        7,
        errors,
        FakePd,
    ) is True
    assert errors == []

    invalid_errors = []
    assert validators._validate_project_row({}, 1, invalid_errors) is False
    assert validators._validate_user_row({}, 2, invalid_errors) is False
    assert validators._validate_timesheet_row({}, 3, invalid_errors, FakePd) is False
    assert validators._validate_task_row({}, 4, invalid_errors) is False
    assert validators._validate_material_row({}, 5, invalid_errors) is False
    assert validators._validate_bom_row({}, 6, invalid_errors, FakePd) is False
    assert len(invalid_errors) == 14


@pytest.mark.unit
def test_validate_import_row_dispatches_known_templates_and_defaults_to_true():
    row = {"项目编码*": "P-1", "项目名称*": "项目A"}
    errors = []

    assert validators._validate_import_row(row, 1, "PROJECT", errors, FakePd) is True
    assert validators._validate_import_row({"姓名": "王五"}, 2, "USER", errors, FakePd) is True
    assert validators._validate_import_row({"工作日期": "2026-01-01", "人员姓名": "赵六", "工时": 1}, 3, "TIMESHEET", errors, FakePd) is True
    assert validators._validate_import_row({"任务名称": "设计", "项目编码": "P-1"}, 4, "TASK", errors, FakePd) is True
    assert validators._validate_import_row({"物料编码": "M-1", "物料名称": "阀门"}, 5, "MATERIAL", errors, FakePd) is True
    assert validators._validate_import_row({"BOM编码": "B-1", "项目编码": "P-1", "物料编码": "M-1", "用量": 1}, 6, "BOM", errors, FakePd) is True
    assert validators._validate_import_row({}, 7, "UNKNOWN", errors, FakePd) is True
    assert errors == []


@pytest.mark.unit
def test_validate_date_and_amount_fields_collect_expected_errors():
    row_errors = []
    validators._validate_date_fields(
        {
            "planned_start_date": "2026-02-02",
            "planned_end_date": "2026-01-01",
        },
        row_errors,
    )
    validators._validate_date_fields({"planned_start_date": "bad-date"}, row_errors)
    validators._validate_date_fields(
        {"planned_start_date": "bad-date", "planned_end_date": "2026-01-01"}, row_errors
    )
    validators._validate_amount_fields(
        {"contract_amount": "oops", "budget_amount": object()},
        row_errors,
    )

    assert {error["field"] for error in row_errors} == {
        "planned_end_date",
        "planned_start_date",
        "contract_amount",
        "budget_amount",
    }


@pytest.mark.unit
def test_validate_project_data_checks_required_duplicate_dates_and_amounts():
    row_errors = []
    db = make_db(object())

    validators._validate_project_data(
        {
            "project_code": "P-100",
            "project_name": "",
            "planned_start_date": "2026-01-05",
            "planned_end_date": "2026-01-01",
            "contract_amount": "bad",
        },
        1,
        db,
        row_errors,
    )

    messages = {error["field"]: error["message"] for error in row_errors}
    assert messages["project_name"] == "项目名称不能为空"
    assert messages["project_code"] == "项目编码 P-100 已存在"
    assert messages["planned_end_date"] == "计划结束日期不能早于计划开始日期"
    assert messages["contract_amount"] == "contract_amount 必须是数字"


@pytest.mark.unit
def test_validate_user_and_timesheet_data_cover_all_branches():
    user_errors = []
    validators._validate_user_data({"name": ""}, user_errors)
    assert user_errors == [{"field": "name", "message": "姓名不能为空"}]

    row_errors = []
    validators._validate_timesheet_data({}, row_errors)
    validators._validate_timesheet_data(
        {"work_date": "bad", "user_name": "", "hours": "oops"}, row_errors
    )
    validators._validate_timesheet_data(
        {"work_date": "2026-01-01", "user_name": "张三", "hours": 0}, row_errors
    )
    validators._validate_timesheet_data(
        {"work_date": "2026-01-01", "user_name": "张三", "hours": 25}, row_errors
    )
    validators._validate_timesheet_data(
        {"work_date": "2026-01-01", "user_name": "张三", "hours": 8}, row_errors
    )

    assert {error["message"] for error in row_errors} >= {
        "工作日期不能为空",
        "人员姓名不能为空",
        "工时不能为空",
        "日期格式错误，应为YYYY-MM-DD",
        "工时格式错误",
        "工时必须在0-24之间",
    }


@pytest.mark.unit
def test_validate_task_material_and_bom_data_cover_lookup_and_numeric_branches():
    task_errors = []
    validators._validate_task_data({"task_name": "", "project_code": ""}, make_db(), task_errors)
    validators._validate_task_data(
        {"task_name": "装配", "project_code": "P-404"},
        make_db(None),
        task_errors,
    )
    validators._validate_task_data(
        {"task_name": "装配", "project_code": "P-1"},
        make_db(object()),
        [],
    )
    assert {error["message"] for error in task_errors} >= {
        "任务名称不能为空",
        "项目编码不能为空",
        "项目 P-404 不存在",
    }

    material_errors = []
    validators._validate_material_data(
        {"material_code": "", "material_name": ""},
        make_db(),
        material_errors,
    )
    validators._validate_material_data(
        {"material_code": "M-1", "material_name": "电机"},
        make_db(object()),
        material_errors,
    )
    assert {error["message"] for error in material_errors} >= {
        "物料编码不能为空",
        "物料名称不能为空",
        "物料编码 M-1 已存在",
    }

    bom_errors = []
    validators._validate_bom_data(
        {"bom_code": "", "project_code": "", "material_code": "", "quantity": None},
        make_db(),
        bom_errors,
    )
    validators._validate_bom_data(
        {"bom_code": "B-1", "project_code": "P-1", "material_code": "M-1", "quantity": 0},
        make_db(None, None),
        bom_errors,
    )
    validators._validate_bom_data(
        {"bom_code": "B-2", "project_code": "P-1", "material_code": "M-1", "quantity": "oops"},
        make_db(None, None),
        bom_errors,
    )
    validators._validate_bom_data(
        {"bom_code": "B-3", "project_code": "P-1", "material_code": "M-1", "quantity": 1},
        make_db(object(), object()),
        [],
    )

    assert {error["message"] for error in bom_errors} >= {
        "BOM编码不能为空",
        "项目编码不能为空",
        "物料编码不能为空",
        "用量不能为空",
        "用量必须大于0",
        "用量格式错误",
        "项目 P-1 不存在",
        "物料 M-1 不存在",
    }


@pytest.mark.unit
def test_validate_row_data_dispatches_each_template_type():
    project_errors = validators._validate_row_data(
        {"project_code": "", "project_name": ""},
        1,
        make_db(),
        "PROJECT",
    )
    user_errors = validators._validate_row_data({"name": ""}, 1, make_db(), "USER")
    timesheet_errors = validators._validate_row_data(
        {"work_date": "bad", "user_name": "", "hours": "oops"},
        1,
        make_db(),
        "TIMESHEET",
    )
    task_errors = validators._validate_row_data(
        {"task_name": "设计", "project_code": "P-404"},
        1,
        make_db(None),
        "TASK",
    )
    material_errors = validators._validate_row_data(
        {"material_code": "M-1", "material_name": "电机"},
        1,
        make_db(object()),
        "MATERIAL",
    )
    bom_errors = validators._validate_row_data(
        {"bom_code": "B-1", "project_code": "P-404", "material_code": "M-404", "quantity": 1},
        1,
        make_db(None, None),
        "BOM",
    )
    unknown_errors = validators._validate_row_data({}, 1, make_db(), "UNKNOWN")

    assert len(project_errors) == 2
    assert user_errors == [{"field": "name", "message": "姓名不能为空"}]
    assert {error["field"] for error in timesheet_errors} == {"work_date", "user_name", "hours"}
    assert task_errors == [{"field": "project_code", "message": "项目 P-404 不存在"}]
    assert material_errors == [{"field": "material_code", "message": "物料编码 M-1 已存在"}]
    assert {error["message"] for error in bom_errors} == {"项目 P-404 不存在", "物料 M-404 不存在"}
    assert unknown_errors == []
