# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 统一导入入口
"""

from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .base import ImportBase
from .bom_importer import BomImporter
from .material_importer import MaterialImporter
from .task_importer import TaskImporter
from .timesheet_importer import TimesheetImporter
from .user_importer import UserImporter


class UnifiedImporter(ImportBase):
    """统一导入器 - 根据类型分发到具体导入器"""

    @classmethod
    def import_data(
        cls,
        db: Session,
        file_content: bytes,
        filename: str,
        template_type: str,
        current_user_id: int,
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        统一导入入口

        Returns:
            Dict[str, Any]: 导入结果
        """
        # 验证文件
        cls.validate_file(filename)

        # 解析文件
        df = cls.parse_file(file_content)

        # 根据类型导入
        template_type = template_type.upper()
        imported_count = 0
        updated_count = 0
        failed_rows = []

        if template_type == "PROJECT":
            # 调用项目导入服务
            from app.services.project_import_service import import_projects_from_dataframe
            imported_count, updated_count, failed_rows = import_projects_from_dataframe(
                db, df, update_existing
            )
        elif template_type == "USER":
            imported_count, updated_count, failed_rows = UserImporter.import_user_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "TIMESHEET":
            imported_count, updated_count, failed_rows = TimesheetImporter.import_timesheet_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "TASK":
            imported_count, updated_count, failed_rows = TaskImporter.import_task_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "MATERIAL":
            imported_count, updated_count, failed_rows = MaterialImporter.import_material_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "BOM":
            imported_count, updated_count, failed_rows = BomImporter.import_bom_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "EMPLOYEE":
            from app.services.employee_import_service import import_employees_from_dataframe
            result = import_employees_from_dataframe(db, df, current_user_id)
            imported_count = result.get("imported", 0)
            updated_count = result.get("updated", 0)
            failed_rows = [{"row_index": 0, "error": e} for e in result.get("errors", [])]
        elif template_type == "HR_PROFILE":
            from app.services.hr_profile_import_service import import_hr_profiles_from_dataframe
            result = import_hr_profiles_from_dataframe(db, df)
            imported_count = result.get("imported", 0)
            updated_count = result.get("updated", 0)
            failed_rows = [{"row_index": 0, "error": e} for e in result.get("errors", [])]
        else:
            raise HTTPException(status_code=400, detail=f"不支持的模板类型: {template_type}")

        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "failed_count": len(failed_rows),
            "failed_rows": failed_rows[:20]  # 最多返回20个错误
        }
