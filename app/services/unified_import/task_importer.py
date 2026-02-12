# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 任务数据导入
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.progress import Task
from app.models.project import Project
from app.models.user import User

from .base import ImportBase


class TaskImporter(ImportBase):
    """任务数据导入器"""

    @classmethod
    def import_task_data(
        cls,
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入任务数据
        """
        required_columns = ['任务名称*', '项目编码*']
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                task_name = str(row.get('任务名称*', '') or row.get('任务名称', '')).strip()
                project_code = str(row.get('项目编码*', '') or row.get('项目编码', '')).strip()

                if not task_name or not project_code:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "任务名称和项目编码为必填项"
                    })
                    continue

                # 查找项目
                project = db.query(Project).filter(Project.project_code == project_code).first()
                if not project:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到项目: {project_code}"
                    })
                    continue

                # 解析可选字段
                stage = str(row.get('阶段', 'S1') or 'S1').strip().upper()
                owner_name = str(row.get('负责人*', '') or row.get('负责人', '') or '').strip()

                owner_id = None
                if owner_name:
                    owner = db.query(User).filter(
                        (User.real_name == owner_name) | (User.username == owner_name)
                    ).first()
                    if owner:
                        owner_id = owner.id

                # 解析日期
                plan_start = None
                plan_end = None
                if pd.notna(row.get('计划开始日期')):
                    try:
                        plan_start = pd.to_datetime(row.get('计划开始日期')).date()
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass
                if pd.notna(row.get('计划结束日期')):
                    try:
                        plan_end = pd.to_datetime(row.get('计划结束日期')).date()
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass

                # 解析权重
                weight = Decimal('1.00')
                if pd.notna(row.get('权重(%)')):
                    try:
                        weight = Decimal(str(row.get('权重(%)'))) / Decimal('100')
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                str(row.get('任务描述', '') or '').strip()

                # 检查是否已存在
                existing = db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.task_name == task_name
                ).first()

                if existing:
                    if update_existing:
                        existing.stage = stage
                        if owner_id:
                            existing.owner_id = owner_id
                        if plan_start:
                            existing.plan_start = plan_start
                        if plan_end:
                            existing.plan_end = plan_end
                        existing.weight = weight
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "该任务已存在"
                        })
                        continue
                else:
                    # 创建任务
                    task = Task(
                        project_id=project.id,
                        task_name=task_name,
                        stage=stage,
                        status='TODO',
                        owner_id=owner_id,
                        plan_start=plan_start,
                        plan_end=plan_end,
                        weight=weight,
                        progress_percent=0
                    )
                    db.add(task)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows
