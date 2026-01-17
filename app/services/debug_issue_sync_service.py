# -*- coding: utf-8 -*-
"""
调试问题自动同步服务
从问题管理系统自动同步调试问题记录
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.engineer_performance import MechanicalDebugIssue, TestBugRecord
from app.models.issue import Issue
from app.models.project import Project
from app.models.user import User


class DebugIssueSyncService:
    """调试问题自动同步服务"""

    def __init__(self, db: Session):
        self.db = db

    def sync_mechanical_debug_issue(
        self,
        issue_id: int,
        force_update: bool = False
    ) -> Optional[MechanicalDebugIssue]:
        """
        从问题管理系统同步机械调试问题

        Args:
            issue_id: 问题ID
            force_update: 是否强制更新

        Returns:
            同步的机械调试问题记录
        """
        # 获取问题
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()

        if not issue:
            return None

        # 只同步项目相关的缺陷问题
        if issue.category != 'PROJECT' or issue.issue_type != 'DEFECT':
            return None

        # 检查是否已同步（通过问题编号关联）
        existing_debug = self.db.query(MechanicalDebugIssue).filter(
            MechanicalDebugIssue.issue_code == issue.issue_no
        ).first()

        if existing_debug and not force_update:
            return existing_debug

        # 计算修复时长（小时）
        fix_duration_hours = None
        if issue.resolved_at and issue.report_date:
            duration = issue.resolved_at - issue.report_date
            fix_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        # 创建或更新机械调试问题记录
        if existing_debug:
            debug_issue = existing_debug
            debug_issue.issue_description = issue.description
            debug_issue.severity = issue.severity
            debug_issue.found_date = issue.report_date.date() if issue.report_date else None
            debug_issue.resolved_date = issue.resolved_at.date() if issue.resolved_at else None
            debug_issue.resolution = issue.solution
            debug_issue.status = issue.status.lower() if issue.status else 'open'
            debug_issue.time_impact_hours = fix_duration_hours
            debug_issue.updated_at = datetime.now()
        else:
            debug_issue = MechanicalDebugIssue(
                project_id=issue.project_id,
                responsible_id=issue.assignee_id or issue.reporter_id,
                reporter_id=issue.reporter_id,
                issue_code=issue.issue_no,
                issue_description=issue.description,
                severity=issue.severity,
                root_cause=issue.root_cause,
                found_date=issue.report_date.date() if issue.report_date else None,
                resolved_date=issue.resolved_at.date() if issue.resolved_at else None,
                resolution=issue.solution,
                status=issue.status.lower() if issue.status else 'open',
                time_impact_hours=fix_duration_hours
            )
            self.db.add(debug_issue)

        self.db.commit()
        self.db.refresh(debug_issue)

        return debug_issue

    def sync_test_bug_record(
        self,
        issue_id: int,
        force_update: bool = False
    ) -> Optional[TestBugRecord]:
        """
        从问题管理系统同步测试Bug记录

        Args:
            issue_id: 问题ID
            force_update: 是否强制更新

        Returns:
            同步的测试Bug记录
        """
        # 获取问题
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()

        if not issue:
            return None

        # 只同步项目相关的Bug问题
        if issue.category != 'PROJECT' or issue.issue_type != 'BUG':
            return None

        # 检查是否已同步（通过问题编号关联）
        existing_bug = self.db.query(TestBugRecord).filter(
            TestBugRecord.bug_code == issue.issue_no
        ).first()

        if existing_bug and not force_update:
            return existing_bug

        # 计算修复时长（小时）
        fix_duration_hours = None
        if issue.resolved_at and issue.report_date:
            duration = issue.resolved_at - issue.report_date
            fix_duration_hours = Decimal(str(duration.total_seconds() / 3600))

        # 确定发现阶段（从问题描述或标签推断）
        found_stage = 'internal_debug'  # 默认内部调试
        if issue.tags:
            tags_str = ','.join(issue.tags).lower()
            if 'site' in tags_str or '现场' in tags_str:
                found_stage = 'site_debug'
            elif 'acceptance' in tags_str or '验收' in tags_str:
                found_stage = 'acceptance'
            elif 'production' in tags_str or '生产' in tags_str:
                found_stage = 'production'

        # 创建或更新测试Bug记录
        if existing_bug:
            bug_record = existing_bug
            bug_record.title = issue.title
            bug_record.description = issue.description
            bug_record.severity = issue.severity
            bug_record.found_time = issue.report_date
            bug_record.resolved_time = issue.resolved_at
            bug_record.fix_duration_hours = fix_duration_hours
            bug_record.resolution = issue.solution
            bug_record.status = issue.status.lower() if issue.status else 'open'
            bug_record.updated_at = datetime.now()
        else:
            bug_record = TestBugRecord(
                project_id=issue.project_id,
                reporter_id=issue.reporter_id,
                assignee_id=issue.assignee_id or issue.reporter_id,
                bug_code=issue.issue_no,
                title=issue.title,
                description=issue.description,
                severity=issue.severity,
                bug_type='logic',  # 默认逻辑问题，可从标签推断
                found_stage=found_stage,
                status=issue.status.lower() if issue.status else 'open',
                found_time=issue.report_date,
                resolved_time=issue.resolved_at,
                fix_duration_hours=fix_duration_hours,
                resolution=issue.solution
            )
            self.db.add(bug_record)

        self.db.commit()
        self.db.refresh(bug_record)

        return bug_record

    def sync_issue(
        self,
        issue_id: int,
        force_update: bool = False
    ) -> Dict[str, Any]:
        """
        同步问题（自动判断类型）

        Args:
            issue_id: 问题ID
            force_update: 是否强制更新

        Returns:
            同步结果
        """
        result = {
            'issue_id': issue_id,
            'synced': False,
            'type': None,
            'record_id': None,
            'error': None
        }

        try:
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()

            if not issue:
                result['error'] = '问题不存在'
                return result

            # 根据问题类型同步
            if issue.category == 'PROJECT' and issue.issue_type == 'DEFECT':
                # 机械调试问题
                debug_issue = self.sync_mechanical_debug_issue(issue_id, force_update)
                if debug_issue:
                    result['synced'] = True
                    result['type'] = 'mechanical_debug'
                    result['record_id'] = debug_issue.id

            elif issue.category == 'PROJECT' and issue.issue_type == 'BUG':
                # 测试Bug记录
                bug_record = self.sync_test_bug_record(issue_id, force_update)
                if bug_record:
                    result['synced'] = True
                    result['type'] = 'test_bug'
                    result['record_id'] = bug_record.id

        except Exception as e:
            result['error'] = str(e)

        return result

    def sync_all_project_issues(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        同步所有项目相关的问题

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            同步统计信息
        """
        stats = {
            'total_issues': 0,
            'synced_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'mechanical_debug_count': 0,
            'test_bug_count': 0,
            'errors': []
        }

        # 查询项目相关的问题
        query = self.db.query(Issue).filter(
            Issue.category == 'PROJECT',
            Issue.issue_type.in_(['DEFECT', 'BUG'])
        )

        if start_date:
            query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))

        issues = query.all()
        stats['total_issues'] = len(issues)

        for issue in issues:
            try:
                sync_result = self.sync_issue(issue.id)
                if sync_result['synced']:
                    stats['synced_count'] += 1
                    if sync_result['type'] == 'mechanical_debug':
                        stats['mechanical_debug_count'] += 1
                    elif sync_result['type'] == 'test_bug':
                        stats['test_bug_count'] += 1
                else:
                    stats['skipped_count'] += 1
            except Exception as e:
                stats['error_count'] += 1
                stats['errors'].append({
                    'issue_id': issue.id,
                    'issue_no': issue.issue_no,
                    'error': str(e)
                })

        return stats
