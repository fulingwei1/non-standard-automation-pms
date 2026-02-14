# -*- coding: utf-8 -*-
"""
用户批量导入API端点
"""

import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import success_response
from app.models.user import User
from app.services.user_import_service import UserImportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_users(
    file: UploadFile = File(..., description="Excel或CSV文件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:create")),
) -> Any:
    """
    批量导入用户
    
    - 支持Excel (.xlsx, .xls) 和CSV格式
    - 单次最多导入500条数据
    - 支持字段：用户名、密码、真实姓名、邮箱、手机号、工号、部门、职位、角色、是否启用
    - 必填字段：用户名、真实姓名、邮箱
    - 密码为空时使用默认密码 123456
    - 角色名称用逗号分隔，如：普通用户,销售经理
    - 采用事务处理：全部成功或全部回滚
    """
    try:
        # 验证文件格式
        if not UserImportService.validate_file_format(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 .xlsx、.xls 或 .csv 文件"
            )

        # 读取文件内容
        file_content = await file.read()
        
        # 读取为DataFrame
        df = UserImportService.read_file(file.filename, file_content)

        # 执行导入
        result = UserImportService.import_users(
            db=db,
            df=df,
            operator_id=current_user.id,
            tenant_id=current_user.tenant_id,
        )

        # 构建响应消息
        message = f"导入完成：成功 {result['success_count']} 条，失败 {result['failed_count']} 条"
        
        return success_response(
            data={
                "total": result["total"],
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
                "errors": result["errors"][:20],  # 最多返回前20条错误
                "success_users": result["success_users"],
            },
            message=message
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"批量导入用户失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.get("/import/template", status_code=status.HTTP_200_OK)
def download_import_template(
    format: str = "xlsx",
    current_user: User = Depends(security.require_permission("user:read")),
) -> Any:
    """
    下载用户导入模板
    
    - 支持格式: xlsx (默认), csv
    - 包含示例数据和字段说明
    """
    try:
        # 生成模板
        df = UserImportService.generate_template()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp:
            if format.lower() == "csv":
                df.to_csv(tmp.name, index=False, encoding="utf-8-sig")
                media_type = "text/csv"
                filename = "user_import_template.csv"
            else:
                df.to_excel(tmp.name, index=False, engine="openpyxl")
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename = "user_import_template.xlsx"

            # 读取文件内容
            with open(tmp.name, "rb") as f:
                content = f.read()

            # 删除临时文件
            Path(tmp.name).unlink()

        # 返回文件流
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"生成导入模板失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成模板失败: {str(e)}"
        )


@router.post("/import/preview", status_code=status.HTTP_200_OK)
async def preview_import_data(
    file: UploadFile = File(..., description="Excel或CSV文件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Any:
    """
    预览导入数据（不实际导入）
    
    - 验证文件格式和数据有效性
    - 返回前20条数据预览
    - 返回所有验证错误
    """
    try:
        # 验证文件格式
        if not UserImportService.validate_file_format(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 .xlsx、.xls 或 .csv 文件"
            )

        # 读取文件内容
        file_content = await file.read()
        
        # 读取为DataFrame
        df = UserImportService.read_file(file.filename, file_content)

        # 标准化列名
        df = UserImportService.normalize_columns(df)

        # 验证DataFrame结构
        structure_errors = UserImportService.validate_dataframe(df)
        if structure_errors:
            return success_response(
                data={
                    "total": len(df),
                    "preview": [],
                    "errors": structure_errors,
                    "is_valid": False,
                },
                message="数据验证失败"
            )

        # 验证每一行
        existing_usernames = set()
        existing_emails = set()
        validation_errors = []

        for idx, row in df.iterrows():
            row_index = idx + 2
            error = UserImportService.validate_row(
                row, row_index, db, existing_usernames, existing_emails
            )
            if error:
                validation_errors.append({"row": row_index, "error": error})

        # 预览数据（前20条）
        preview_data = []
        for idx, row in df.head(20).iterrows():
            preview_data.append({
                "row": idx + 2,
                "username": row.get("username"),
                "real_name": row.get("real_name"),
                "email": row.get("email"),
                "department": row.get("department"),
                "position": row.get("position"),
                "roles": row.get("roles"),
            })

        return success_response(
            data={
                "total": len(df),
                "preview": preview_data,
                "errors": validation_errors[:50],  # 最多返回前50条错误
                "is_valid": len(validation_errors) == 0,
            },
            message=f"数据预览：共 {len(df)} 条，{'验证通过' if not validation_errors else f'发现 {len(validation_errors)} 个错误'}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"预览导入数据失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}"
        )
