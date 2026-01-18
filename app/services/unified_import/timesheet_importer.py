# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 工时数据导入
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User

from .base import ImportBase


class TimesheetImporter(ImportBase):
    """工时数据导入器"""

    @staticmethod
    def create_timesheet_record(
        user: User, index: int, work_date: date, hours: float,
        project_id: Optional[int], project_code: str, project_name: Optional[str],
        task_name: str, overtime_type: str, work_content: str, work_result: str,
        progress_before: Optional[int], progress_after: Optional[int],
        current_user_id: int
    ) -> Timesheet:
        """创建工时记录对象"""
        return Timesheet(
            timesheet_no=f"TS{datetime.now().strftime('%Y%m%d%H%M%S')}{index:03d}",
            user_id=user.id,
            user_name=user.real_name or user.username,
            department_id=user.department_id,
            department_name=user.department if hasattr(user, 'department') else '',
            project_id=project_id,
            project_code=project_code,
            project_name=project_name,
            task_name=task_name,
            work_date=work_date,
            hours=Decimal(str(hours)),
            overtime_type=overtime_type,
            work_content=work_content,
            work_result=work_result,
            progress_before=progress_before,
            progress_after=progress_after,
            status='DRAFT',
            created_by=current_user_id
        )

    @staticmethod
    def parse_progress(row: pd.Series, field_name: str) -> Optional[int]:
        """解析进度字段"""
        val = row.get(field_name)
        if pd.notna(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
        return None

    @classmethod
    def import_timesheet_data(
        cls,
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入工时数据
        """
        required_columns = ['工作日期*', '人员姓名*', '工时(小时)*']
        missing = cls.check_required_columns(df, required_columns)
        if missing:
            raise HTTPException(status_code=400, detail=f"Excel文件缺少必需的列：{', '.join(missing)}")

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            row_idx = index + 2
            try:
                # 解析必需字段
                work_date_val = row.get('工作日期*') or row.get('工作日期')
                user_name = str(row.get('人员姓名*', '') or row.get('人员姓名', '')).strip()
                hours_val = row.get('工时(小时)*') or row.get('工时(小时)') or row.get('工时')

                if not work_date_val or not user_name or pd.isna(hours_val):
                    failed_rows.append({"row_index": row_idx, "error": "工作日期、人员姓名、工时为必填项"})
                    continue

                # 解析日期和工时
                try:
                    work_date = cls.parse_work_date(work_date_val)
                except (ValueError, TypeError, pd.errors.ParserError):
                    failed_rows.append({"row_index": row_idx, "error": "工作日期格式错误"})
                    continue

                try:
                    hours = cls.parse_hours(hours_val)
                    if hours is None:
                        failed_rows.append({"row_index": row_idx, "error": "工时必须在0-24之间"})
                        continue
                except (ValueError, TypeError):
                    failed_rows.append({"row_index": row_idx, "error": "工时格式错误"})
                    continue

                # 查找用户
                user = db.query(User).filter(
                    (User.real_name == user_name) | (User.username == user_name)
                ).first()
                if not user:
                    failed_rows.append({"row_index": row_idx, "error": f"未找到用户: {user_name}"})
                    continue

                # 解析可选字段
                project_code = str(row.get('项目编码', '') or '').strip()
                project_id, project_name = None, None
                if project_code:
                    project = db.query(Project).filter(Project.project_code == project_code).first()
                    if project:
                        project_id, project_name = project.id, project.project_name

                task_name = str(row.get('任务名称', '') or '').strip()
                work_content = str(row.get('工作内容', '') or '').strip()
                work_result = str(row.get('工作成果', '') or '').strip()
                overtime_type = str(row.get('加班类型', 'NORMAL') or 'NORMAL').strip().upper()
                progress_before = cls.parse_progress(row, '更新前进度(%)')
                progress_after = cls.parse_progress(row, '更新后进度(%)')

                # 检查是否已存在相同记录
                existing = db.query(Timesheet).filter(
                    Timesheet.user_id == user.id,
                    Timesheet.work_date == work_date,
                    Timesheet.project_id == project_id,
                    Timesheet.task_name == task_name
                ).first()

                if existing:
                    if update_existing:
                        existing.hours = hours
                        existing.overtime_type = overtime_type
                        existing.work_content = work_content
                        existing.work_result = work_result
                        existing.progress_before = progress_before
                        existing.progress_after = progress_after
                        updated_count += 1
                    else:
                        failed_rows.append({"row_index": row_idx, "error": "该工时记录已存在"})
                        continue
                else:
                    timesheet = cls.create_timesheet_record(
                        user, index, work_date, hours, project_id, project_code, project_name,
                        task_name, overtime_type, work_content, work_result,
                        progress_before, progress_after, current_user_id
                    )
                    db.add(timesheet)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({"row_index": row_idx, "error": str(e)})

        return imported_count, updated_count, failed_rows
