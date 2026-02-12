# -*- coding: utf-8 -*-
"""
工作日志自动生成服务
从工时系统自动生成工作日志摘要
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.work_log import WorkLog


class WorkLogAutoGenerator:
    """工作日志自动生成服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_work_log_from_timesheet(
        self,
        user_id: int,
        work_date: date,
        auto_submit: bool = False
    ) -> Optional[WorkLog]:
        """
        从工时记录自动生成工作日志

        Args:
            user_id: 用户ID
            work_date: 工作日期
            auto_submit: 是否自动提交（默认False，需要用户确认）

        Returns:
            生成的工作日志对象，如果已存在则返回None
        """
        # 检查是否已存在工作日志
        existing_log = self.db.query(WorkLog).filter(
            WorkLog.user_id == user_id,
            WorkLog.work_date == work_date,
            WorkLog.status == 'SUBMITTED'
        ).first()

        if existing_log:
            # 如果已存在已提交的日志，不覆盖
            return None

        # 获取该日期的所有已审批工时记录
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.work_date == work_date,
            Timesheet.status == 'APPROVED'
        ).order_by(Timesheet.project_id, Timesheet.task_id).all()

        if not timesheets:
            # 没有工时记录，不生成日志
            return None

        # 获取用户信息
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # 聚合工时记录，生成工作日志内容
        work_content_parts = []
        mentioned_projects = []
        total_hours = Decimal('0')

        # 按项目分组
        project_groups = {}
        for ts in timesheets:
            project_id = ts.project_id
            if project_id not in project_groups:
                project_groups[project_id] = []
            project_groups[project_id].append(ts)
            total_hours += ts.hours

            # 收集提及的项目
            if project_id and project_id not in mentioned_projects:
                mentioned_projects.append(project_id)

        # 生成工作内容
        for project_id, ts_list in project_groups.items():
            project = None
            if project_id:
                project = self.db.query(Project).filter(Project.id == project_id).first()

            project_name = project.project_name if project else "未关联项目"
            project_hours = sum(ts.hours for ts in ts_list)

            # 项目标题
            work_content_parts.append(f"【{project_name}】（{float(project_hours)}小时）")

            # 按任务分组
            task_groups = {}
            for ts in ts_list:
                task_id = ts.task_id
                if task_id not in task_groups:
                    task_groups[task_id] = []
                task_groups[task_id].append(ts)

            for task_id, task_ts_list in task_groups.items():
                task_name = task_ts_list[0].task_name or "未指定任务"
                task_hours = sum(ts.hours for ts in task_ts_list)

                work_content_parts.append(f"  - {task_name}（{float(task_hours)}小时）")

                # 添加工作内容和成果
                for ts in task_ts_list:
                    if ts.work_content:
                        work_content_parts.append(f"    工作内容：{ts.work_content}")
                    if ts.work_result:
                        work_content_parts.append(f"    工作成果：{ts.work_result}")
                    if ts.progress_before is not None and ts.progress_after is not None:
                        work_content_parts.append(
                            f"    进度更新：{ts.progress_before}% → {ts.progress_after}%"
                        )

        # 生成完整工作日志内容
        content = "\n".join(work_content_parts)

        # 如果内容超过300字，截断
        if len(content) > 300:
            content = content[:297] + "..."

        # 创建或更新工作日志
        work_log = self.db.query(WorkLog).filter(
            WorkLog.user_id == user_id,
            WorkLog.work_date == work_date,
            WorkLog.status == 'DRAFT'
        ).first()

        if work_log:
            # 更新现有草稿
            work_log.content = content
            work_log.updated_at = datetime.now()
        else:
            # 创建新日志
            work_log = WorkLog(
                user_id=user_id,
                user_name=user.real_name or user.username,
                work_date=work_date,
                content=content,
                status='SUBMITTED' if auto_submit else 'DRAFT'
            )
            self.db.add(work_log)

        self.db.flush()

        # 处理@提及（需要创建WorkLogMention记录）
        # 这里简化处理，实际应该创建WorkLogMention记录
        # 为了不增加复杂度，暂时跳过

        self.db.commit()
        self.db.refresh(work_log)

        return work_log

    def batch_generate_work_logs(
        self,
        start_date: date,
        end_date: date,
        user_ids: Optional[List[int]] = None,
        auto_submit: bool = False
    ) -> Dict[str, Any]:
        """
        批量生成工作日志

        Args:
            start_date: 开始日期
            end_date: 结束日期
            user_ids: 用户ID列表（None表示所有用户）
            auto_submit: 是否自动提交

        Returns:
            生成统计信息
        """
        stats = {
            'total_users': 0,
            'total_days': 0,
            'generated_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }

        # 获取需要处理的用户
        if user_ids:
            users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        else:
            # 获取所有有工时记录的用户
            user_ids_with_timesheet = self.db.query(Timesheet.user_id).filter(
                Timesheet.work_date.between(start_date, end_date),
                Timesheet.status == 'APPROVED'
            ).distinct().all()
            user_ids_list = [uid[0] for uid in user_ids_with_timesheet]
            users = self.db.query(User).filter(User.id.in_(user_ids_list)).all()

        stats['total_users'] = len(users)

        # 遍历每个用户和日期
        current_date = start_date
        while current_date <= end_date:
            stats['total_days'] += 1

            for user in users:
                try:
                    work_log = self.generate_work_log_from_timesheet(
                        user_id=user.id,
                        work_date=current_date,
                        auto_submit=auto_submit
                    )

                    if work_log:
                        stats['generated_count'] += 1
                    else:
                        stats['skipped_count'] += 1
                except Exception as e:
                    stats['error_count'] += 1
                    stats['errors'].append({
                        'user_id': user.id,
                        'user_name': user.real_name or user.username,
                        'date': current_date.isoformat(),
                        'error': str(e)
                    })

            current_date += timedelta(days=1)

        return stats

    def generate_yesterday_work_logs(
        self,
        user_ids: Optional[List[int]] = None,
        auto_submit: bool = False
    ) -> Dict[str, Any]:
        """
        生成昨日工作日志（定时任务使用）

        Args:
            user_ids: 用户ID列表（None表示所有用户）
            auto_submit: 是否自动提交

        Returns:
            生成统计信息
        """
        yesterday = date.today() - timedelta(days=1)
        return self.batch_generate_work_logs(
            start_date=yesterday,
            end_date=yesterday,
            user_ids=user_ids,
            auto_submit=auto_submit
        )
