# -*- coding: utf-8 -*-
"""
问题导入导出端点

包含：导出Excel、从Excel导入
"""

import io
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.data_scope import DataScopeService

from .utils import generate_issue_no

router = APIRouter()

# 检查Excel库是否可用
try:
    import openpyxl
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


@router.get("/export", response_class=StreamingResponse)
def export_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    category: Optional[str] = Query(None, description="问题分类"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
) -> Any:
    """导出问题到Excel"""
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    query = db.query(Issue).filter(Issue.status != 'DELETED')
    query = DataScopeService.filter_issues_by_scope(db, query, current_user)

    if category:
        query = query.filter(Issue.category == category)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))

    issues = query.order_by(desc(Issue.created_at)).all()

    # 构建DataFrame
    data = []
    for issue in issues:
        data.append({
            '问题编号': issue.issue_no,
            '问题分类': issue.category,
            '问题类型': issue.issue_type,
            '严重程度': issue.severity,
            '优先级': issue.priority,
            '标题': issue.title,
            '描述': issue.description or '',
            '提出人': issue.reporter_name or '',
            '提出时间': issue.report_date.strftime('%Y-%m-%d %H:%M:%S') if issue.report_date else '',
            '处理人': issue.assignee_name or '',
            '要求完成日期': issue.due_date.strftime('%Y-%m-%d') if issue.due_date else '',
            '状态': issue.status,
            '解决方案': issue.solution or '',
            '解决时间': issue.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if issue.resolved_at else '',
            '是否阻塞': '是' if issue.is_blocking else '否',
            '跟进次数': issue.follow_up_count or 0,
            '创建时间': issue.created_at.strftime('%Y-%m-%d %H:%M:%S') if issue.created_at else '',
        })

    df = pd.DataFrame(data)

    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='问题列表', index=False)

        # 设置列宽
        worksheet = writer.sheets['问题列表']
        column_widths = {
            'A': 15,  # 问题编号
            'B': 12,  # 问题分类
            'C': 12,  # 问题类型
            'D': 10,  # 严重程度
            'E': 8,   # 优先级
            'F': 30,  # 标题
            'G': 50,  # 描述
            'H': 12,  # 提出人
            'I': 18,  # 提出时间
            'J': 12,  # 处理人
            'K': 12,  # 要求完成日期
            'L': 10,  # 状态
            'M': 50,  # 解决方案
            'N': 18,  # 解决时间
            'O': 8,   # 是否阻塞
            'P': 10,  # 跟进次数
            'Q': 18,  # 创建时间
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

    output.seek(0)

    filename = f"问题列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            # Use RFC 5987 encoding to support non-ASCII filenames.
            "Content-Disposition": (
                "attachment; "
                "filename=\"issues.xlsx\"; "
                f"filename*=UTF-8''{encoded_filename}"
            )
        },
    )


@router.post("/import", response_model=ResponseModel)
async def import_issues(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """从Excel导入问题"""
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    try:
        file_content = await file.read()
        df = pd.read_excel(io.BytesIO(file_content))

        # 验证必需的列
        required_columns = ['问题分类', '问题类型', '严重程度', '标题', '描述']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # 生成问题编号
                issue_no = generate_issue_no(db)

                # 创建问题
                issue = Issue(
                    issue_no=issue_no,
                    category=str(row.get('问题分类', 'OTHER')).strip(),
                    project_id=int(row['项目ID']) if pd.notna(row.get('项目ID')) else None,
                    issue_type=str(row.get('问题类型', 'OTHER')).strip(),
                    severity=str(row.get('严重程度', 'MINOR')).strip(),
                    priority=str(row.get('优先级', 'MEDIUM')).strip(),
                    title=str(row.get('标题', '')).strip(),
                    description=str(row.get('描述', '')).strip(),
                    reporter_id=current_user.id,
                    reporter_name=current_user.real_name or current_user.username,
                    report_date=datetime.now(),
                    assignee_id=int(row['处理人ID']) if pd.notna(row.get('处理人ID')) else None,
                    due_date=pd.to_datetime(row['要求完成日期']).date() if pd.notna(row.get('要求完成日期')) else None,
                    status=str(row.get('状态', 'OPEN')).strip(),
                    is_blocking=str(row.get('是否阻塞', '否')).strip().lower() in ['是', 'true', '1'],
                )

                db.add(issue)
                db.flush()
                imported_count += 1
            except Exception as e:
                failed_rows.append({"row_index": index + 2, "error": str(e)})

        db.commit()

        if failed_rows:
            return ResponseModel(
                code=200,
                message=f"部分成功导入。成功 {imported_count} 条，失败 {len(failed_rows)} 条。",
                data={"imported_count": imported_count, "failed_rows": failed_rows[:10]}
            )

        return ResponseModel(
            code=200,
            message=f"成功导入 {imported_count} 条问题",
            data={"imported_count": imported_count}
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"文件处理失败: {e}")
