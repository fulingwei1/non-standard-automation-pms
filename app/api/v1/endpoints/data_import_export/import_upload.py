# -*- coding: utf-8 -*-
"""
数据导入上传 routes
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.report_center import DataImportTask
from app.models.user import User
from app.schemas.data_import_export import ImportUploadResponse
from app.services.import_export_engine import ImportExportEngine

router = APIRouter()


@router.post(
    "/upload", response_model=ImportUploadResponse, status_code=status.HTTP_201_CREATED
)
def upload_and_import_data(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    template_type: str = Query(..., description="模板类型"),
    update_existing: bool = Query(False, description="是否更新已存在的数据"),
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    上传并导入数据（执行导入）

    支持多种数据类型导入：
    - PROJECT: 项目导入
    - USER: 用户导入
    - TIMESHEET: 工时导入
    - TASK: 任务导入
    - MATERIAL: 物料导入
    - BOM: BOM导入
    """
    try:
        file_content = file.file.read()

        result = ImportExportEngine.import_data(
            db=db,
            file_content=file_content,
            filename=file.filename,
            template_type=template_type,
            current_user_id=current_user.id,
            update_existing=update_existing,
        )

        db.commit()

        task_code = f"IMP-{datetime.now().strftime('%y%m%d%H%M%S')}"
        import_task = DataImportTask(
            task_code=task_code,
            template_type=template_type,
            file_url=file.filename,
            status="COMPLETED" if result.get("failed_count", 0) == 0 else "PARTIAL",
            requested_by=current_user.id,
            import_options={"update_existing": update_existing},
        )
        db.add(import_task)
        db.commit()

        imported = result.get("imported_count", 0)
        updated = result.get("updated_count", 0)
        failed = result.get("failed_count", 0)

        message = f"导入完成：成功导入 {imported} 条"
        if updated > 0:
            message += f"，更新 {updated} 条"
        if failed > 0:
            message += f"，失败 {failed} 条"

        return ImportUploadResponse(
            task_id=import_task.id,
            task_code=import_task.task_code,
            status="COMPLETED" if failed == 0 else "PARTIAL",
            message=message,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")
