# -*- coding: utf-8 -*-
"""
数据导入验证器
"""

from datetime import datetime


from app.models.material import Material
from app.models.project import Project


def _validate_project_row(row, row_num, errors):
    """验证项目导入行"""
    is_valid = True
    project_code = str(row.get("项目编码*", row.get("项目编码", ""))).strip()
    project_name = str(row.get("项目名称*", row.get("项目名称", ""))).strip()

    if not project_code:
        errors.append(
            {"row": row_num, "field": "项目编码", "message": "项目编码不能为空"}
        )
        is_valid = False
    if not project_name:
        errors.append(
            {"row": row_num, "field": "项目名称", "message": "项目名称不能为空"}
        )
        is_valid = False
    return is_valid


def _validate_user_row(row, row_num, errors):
    """验证用户导入行"""
    name = str(row.get("姓名", row.get("名字", ""))).strip()
    if not name:
        errors.append({"row": row_num, "field": "姓名", "message": "姓名不能为空"})
        return False
    return True


def _validate_timesheet_row(row, row_num, errors, pd):
    """验证工时导入行"""
    is_valid = True
    work_date = row.get("工作日期*") or row.get("工作日期")
    user_name = str(row.get("人员姓名*", row.get("人员姓名", ""))).strip()
    hours = row.get("工时(小时)*") or row.get("工时(小时)") or row.get("工时")

    if pd.isna(work_date) or not work_date:
        errors.append(
            {"row": row_num, "field": "工作日期", "message": "工作日期不能为空"}
        )
        is_valid = False
    if not user_name:
        errors.append(
            {"row": row_num, "field": "人员姓名", "message": "人员姓名不能为空"}
        )
        is_valid = False
    if pd.isna(hours):
        errors.append({"row": row_num, "field": "工时", "message": "工时不能为空"})
        is_valid = False
    return is_valid


def _validate_task_row(row, row_num, errors):
    """验证任务导入行"""
    is_valid = True
    task_name = str(row.get("任务名称*", row.get("任务名称", ""))).strip()
    project_code = str(row.get("项目编码*", row.get("项目编码", ""))).strip()

    if not task_name:
        errors.append(
            {"row": row_num, "field": "任务名称", "message": "任务名称不能为空"}
        )
        is_valid = False
    if not project_code:
        errors.append(
            {"row": row_num, "field": "项目编码", "message": "项目编码不能为空"}
        )
        is_valid = False
    return is_valid


def _validate_material_row(row, row_num, errors):
    """验证物料导入行"""
    is_valid = True
    material_code = str(row.get("物料编码*", row.get("物料编码", ""))).strip()
    material_name = str(row.get("物料名称*", row.get("物料名称", ""))).strip()

    if not material_code:
        errors.append(
            {"row": row_num, "field": "物料编码", "message": "物料编码不能为空"}
        )
        is_valid = False
    if not material_name:
        errors.append(
            {"row": row_num, "field": "物料名称", "message": "物料名称不能为空"}
        )
        is_valid = False
    return is_valid


def _validate_bom_row(row, row_num, errors, pd):
    """验证BOM导入行"""
    is_valid = True
    bom_code = str(row.get("BOM编码*", row.get("BOM编码", ""))).strip()
    project_code = str(row.get("项目编码*", row.get("项目编码", ""))).strip()
    material_code = str(row.get("物料编码*", row.get("物料编码", ""))).strip()
    quantity = row.get("用量*") or row.get("用量")

    if not bom_code:
        errors.append(
            {"row": row_num, "field": "BOM编码", "message": "BOM编码不能为空"}
        )
        is_valid = False
    if not project_code:
        errors.append(
            {"row": row_num, "field": "项目编码", "message": "项目编码不能为空"}
        )
        is_valid = False
    if not material_code:
        errors.append(
            {"row": row_num, "field": "物料编码", "message": "物料编码不能为空"}
        )
        is_valid = False
    if pd.isna(quantity):
        errors.append({"row": row_num, "field": "用量", "message": "用量不能为空"})
        is_valid = False
    return is_valid


def _validate_import_row(row, row_num, template_type, errors, pd):
    """根据模板类型验证导入行"""
    validators = {
        "PROJECT": lambda: _validate_project_row(row, row_num, errors),
        "USER": lambda: _validate_user_row(row, row_num, errors),
        "TIMESHEET": lambda: _validate_timesheet_row(row, row_num, errors, pd),
        "TASK": lambda: _validate_task_row(row, row_num, errors),
        "MATERIAL": lambda: _validate_material_row(row, row_num, errors),
        "BOM": lambda: _validate_bom_row(row, row_num, errors, pd),
    }
    validator = validators.get(template_type)
    return validator() if validator else True


def _validate_date_fields(row_data, row_errors):
    """验证日期字段"""
    for date_field in ["planned_start_date", "planned_end_date"]:
        if row_data.get(date_field):
            try:
                datetime.strptime(str(row_data[date_field]), "%Y-%m-%d")
            except ValueError:
                row_errors.append(
                    {"field": date_field, "message": "日期格式错误，应为YYYY-MM-DD"}
                )

    if row_data.get("planned_start_date") and row_data.get("planned_end_date"):
        try:
            start_date = datetime.strptime(
                str(row_data["planned_start_date"]), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                str(row_data["planned_end_date"]), "%Y-%m-%d"
            ).date()
            if start_date > end_date:
                row_errors.append(
                    {
                        "field": "planned_end_date",
                        "message": "计划结束日期不能早于计划开始日期",
                    }
                )
        except ValueError:
            pass


def _validate_amount_fields(row_data, row_errors):
    """验证金额字段"""
    for amount_field in ["contract_amount", "budget_amount"]:
        if row_data.get(amount_field):
            try:
                float(row_data[amount_field])
            except (ValueError, TypeError):
                row_errors.append(
                    {"field": amount_field, "message": f"{amount_field} 必须是数字"}
                )


def _validate_project_data(row_data, idx, db, row_errors):
    """验证项目导入数据（含数据库校验）"""
    project_code = (row_data.get("project_code") or "").strip()
    project_name = (row_data.get("project_name") or "").strip()

    if not project_code:
        row_errors.append({"field": "project_code", "message": "项目编码不能为空"})
    if not project_name:
        row_errors.append({"field": "project_name", "message": "项目名称不能为空"})

    if project_code:
        existing = (
            db.query(Project).filter(Project.project_code == project_code).first()
        )
        if existing:
            row_errors.append(
                {"field": "project_code", "message": f"项目编码 {project_code} 已存在"}
            )

    _validate_date_fields(row_data, row_errors)
    _validate_amount_fields(row_data, row_errors)


def _validate_user_data(row_data, row_errors):
    """验证用户导入数据"""
    name = (row_data.get("name") or "").strip()
    if not name:
        row_errors.append({"field": "name", "message": "姓名不能为空"})


def _validate_timesheet_data(row_data, row_errors):
    """验证工时导入数据"""
    work_date = row_data.get("work_date")
    user_name = (row_data.get("user_name") or "").strip()
    hours = row_data.get("hours")

    if not work_date:
        row_errors.append({"field": "work_date", "message": "工作日期不能为空"})
    else:
        try:
            datetime.strptime(str(work_date), "%Y-%m-%d")
        except ValueError:
            row_errors.append(
                {"field": "work_date", "message": "日期格式错误，应为YYYY-MM-DD"}
            )

    if not user_name:
        row_errors.append({"field": "user_name", "message": "人员姓名不能为空"})

    if hours is None:
        row_errors.append({"field": "hours", "message": "工时不能为空"})
    else:
        try:
            h = float(hours)
            if h <= 0 or h > 24:
                row_errors.append({"field": "hours", "message": "工时必须在0-24之间"})
        except (ValueError, TypeError):
            row_errors.append({"field": "hours", "message": "工时格式错误"})


def _validate_task_data(row_data, db, row_errors):
    """验证任务导入数据"""
    task_name = (row_data.get("task_name") or "").strip()
    project_code = (row_data.get("project_code") or "").strip()

    if not task_name:
        row_errors.append({"field": "task_name", "message": "任务名称不能为空"})
    if not project_code:
        row_errors.append({"field": "project_code", "message": "项目编码不能为空"})
    elif project_code:
        project = db.query(Project).filter(Project.project_code == project_code).first()
        if not project:
            row_errors.append(
                {"field": "project_code", "message": f"项目 {project_code} 不存在"}
            )


def _validate_material_data(row_data, db, row_errors):
    """验证物料导入数据"""
    material_code = (row_data.get("material_code") or "").strip()
    material_name = (row_data.get("material_name") or "").strip()

    if not material_code:
        row_errors.append({"field": "material_code", "message": "物料编码不能为空"})
    if not material_name:
        row_errors.append({"field": "material_name", "message": "物料名称不能为空"})

    if material_code:
        existing = (
            db.query(Material).filter(Material.material_code == material_code).first()
        )
        if existing:
            row_errors.append(
                {
                    "field": "material_code",
                    "message": f"物料编码 {material_code} 已存在",
                }
            )


def _validate_bom_data(row_data, db, row_errors):
    """验证BOM导入数据"""
    bom_code = (row_data.get("bom_code") or "").strip()
    project_code = (row_data.get("project_code") or "").strip()
    material_code = (row_data.get("material_code") or "").strip()
    quantity = row_data.get("quantity")

    if not bom_code:
        row_errors.append({"field": "bom_code", "message": "BOM编码不能为空"})
    if not project_code:
        row_errors.append({"field": "project_code", "message": "项目编码不能为空"})
    if not material_code:
        row_errors.append({"field": "material_code", "message": "物料编码不能为空"})
    if quantity is None:
        row_errors.append({"field": "quantity", "message": "用量不能为空"})
    else:
        try:
            q = float(quantity)
            if q <= 0:
                row_errors.append({"field": "quantity", "message": "用量必须大于0"})
        except (ValueError, TypeError):
            row_errors.append({"field": "quantity", "message": "用量格式错误"})

    if project_code:
        project = db.query(Project).filter(Project.project_code == project_code).first()
        if not project:
            row_errors.append(
                {"field": "project_code", "message": f"项目 {project_code} 不存在"}
            )

    if material_code:
        material = (
            db.query(Material).filter(Material.material_code == material_code).first()
        )
        if not material:
            row_errors.append(
                {"field": "material_code", "message": f"物料 {material_code} 不存在"}
            )


def _validate_row_data(row_data, idx, db, template_type):
    """统一验证入口，根据模板类型调用对应验证器"""
    row_errors = []
    validators = {
        "PROJECT": lambda: _validate_project_data(row_data, idx, db, row_errors),
        "USER": lambda: _validate_user_data(row_data, row_errors),
        "TIMESHEET": lambda: _validate_timesheet_data(row_data, row_errors),
        "TASK": lambda: _validate_task_data(row_data, db, row_errors),
        "MATERIAL": lambda: _validate_material_data(row_data, db, row_errors),
        "BOM": lambda: _validate_bom_data(row_data, db, row_errors),
    }
    validator = validators.get(template_type)
    if validator:
        validator()
    return row_errors
