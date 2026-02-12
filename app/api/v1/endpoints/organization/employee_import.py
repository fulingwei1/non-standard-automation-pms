# -*- coding: utf-8 -*-
"""
员工批量导入端点
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.import_export_engine import ImportExportEngine
from app.models.user import User

router = APIRouter()


@router.post("/employees/import")
async def import_employees_from_excel(
    file: UploadFile = File(..., description="Excel文件（支持企业微信导出格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    从Excel文件批量导入员工数据

    支持的Excel格式：
    - 企业微信导出的通讯录
    - 人事系统导出的员工信息表

    必需列：姓名
    可选列：一级部门、二级部门、三级部门、部门、职务、联系方式、手机、在职离职状态

    系统会自动：
    - 跳过已存在的员工（按姓名+部门判断）
    - 更新已存在员工的信息
    - 为新员工生成工号
    - 创建员工档案
    """
    from app.services.employee_import_service import (
        import_employees_from_dataframe,
        validate_excel_file,
    )

    validate_excel_file(file.filename)

    try:
        contents = await file.read()
        df = ImportExportEngine.parse_excel(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")

    result = import_employees_from_dataframe(db, df, current_user.id)

    db.commit()

    return {
        "success": True,
        "message": f"导入完成：新增 {result['imported']} 人，更新 {result['updated']} 人，跳过 {result['skipped']} 条",
        "imported": result['imported'],
        "updated": result['updated'],
        "skipped": result['skipped'],
        "errors": result['errors']
    }


@router.get("/employees/import/template")
async def download_import_template(
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取员工导入模板说明

    返回导入模板的列说明，用户可以参考此格式准备数据
    """
    return {
        "template_columns": [
            {"name": "姓名", "required": True, "description": "员工姓名（必填）"},
            {"name": "一级部门", "required": False, "description": "一级部门名称"},
            {"name": "二级部门", "required": False, "description": "二级部门名称"},
            {"name": "三级部门", "required": False, "description": "三级部门名称"},
            {"name": "职务", "required": False, "description": "职务/岗位名称"},
            {"name": "联系方式", "required": False, "description": "手机号码"},
            {"name": "在职离职状态", "required": False, "description": "在职/离职/试用期等"},
        ],
        "supported_formats": [".xlsx", ".xls"],
        "notes": [
            "系统会根据 姓名+部门 判断员工是否已存在",
            "已存在的员工会更新其信息，不会重复创建",
            "支持直接导入企业微信导出的通讯录Excel",
            "部门会自动按 一级部门-二级部门-三级部门 格式组合"
        ]
    }
