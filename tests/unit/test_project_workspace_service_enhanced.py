# -*- coding: utf-8 -*-
"""
项目工作空间服务增强单元测试
覆盖所有核心方法，使用真实数据对象，只mock外部依赖
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

from app.services.project_workspace_service import (
    build_project_basic_info,
    build_team_info,
    build_task_info,
    build_bonus_info,
    build_meeting_info,
    build_issue_info,
    build_solution_info,
    build_document_info,
)


# ═══════════════════════════════════════════════════════════════════════════
# 测试数据工厂函数
# ═══════════════════════════════════════════════════════════════════════════

def create_mock_project(**kwargs):
    """创建模拟项目对象"""
    defaults = {
        'id': 1,
        'project_code': 'PRJ001',
        'project_name': '测试项目',
        'stage': 'S2',
        'status': 'ST01',
        'health': 'H1',
        'progress_pct': Decimal('45.5'),
        'contract_amount': Decimal('200000.00'),
        'pm_name': '张三',
    }
    defaults.update(kwargs)
    
    project = MagicMock()
    for key, value in defaults.items():
        setattr(project, key, value)
    return project


def create_mock_user(**kwargs):
    """创建模拟用户对象"""
    defaults = {
        'id': 1,
        'username': 'zhangsan',
        'real_name': '张三',
    }
    defaults.update(kwargs)
    
    user = MagicMock()
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


def create_mock_member(**kwargs):
    """创建模拟团队成员对象"""
    defaults = {
        'user_id': 1,
        'role_code': 'PM',
        'allocation_pct': Decimal('100.0'),
        'start_date': date(2025, 1, 1),
        'end_date': None,
        'is_active': True,
    }
    defaults.update(kwargs)
    
    member = MagicMock()
    for key, value in defaults.items():
        setattr(member, key, value)
    
    # 默认关联用户
    if 'user' not in kwargs:
        member.user = create_mock_user()
    
    return member


def create_mock_task(**kwargs):
    """创建模拟任务对象"""
    defaults = {
        'id': 1,
        'title': '任务1',
        'status': 'IN_PROGRESS',
        'assignee_name': '张三',
        'plan_end_date': date(2025, 6, 30),
        'progress': Decimal('60.0'),
    }
    defaults.update(kwargs)
    
    task = MagicMock()
    for key, value in defaults.items():
        setattr(task, key, value)
    return task


def create_mock_issue(**kwargs):
    """创建模拟问题对象"""
    defaults = {
        'id': 1,
        'issue_no': 'ISS001',
        'title': '测试问题',
        'status': 'OPEN',
        'severity': 'HIGH',
        'priority': 'P1',
        'solution': '',
        'assignee_name': '张三',
        'report_date': date(2025, 4, 1),
    }
    defaults.update(kwargs)
    
    issue = MagicMock()
    for key, value in defaults.items():
        setattr(issue, key, value)
    return issue


def create_mock_document(**kwargs):
    """创建模拟文档对象"""
    defaults = {
        'id': 1,
        'doc_name': '需求文档',
        'doc_type': 'REQUIREMENT',
        'version': 'v1.0',
        'status': 'APPROVED',
        'created_at': datetime(2025, 1, 1, 10, 0, 0),
    }
    defaults.update(kwargs)
    
    doc = MagicMock()
    for key, value in defaults.items():
        setattr(doc, key, value)
    return doc


# ═══════════════════════════════════════════════════════════════════════════
# build_project_basic_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildProjectBasicInfo:
    """测试项目基本信息构建"""

    def test_returns_all_required_fields(self):
        """测试返回所有必需字段"""
        project = create_mock_project()
        result = build_project_basic_info(project)
        
        expected_keys = {
            'id', 'project_code', 'project_name', 'stage', 'status',
            'health', 'progress_pct', 'contract_amount', 'pm_name'
        }
        assert set(result.keys()) == expected_keys

    def test_handles_decimal_progress_pct(self):
        """测试处理 Decimal 类型的进度百分比"""
        project = create_mock_project(progress_pct=Decimal('75.25'))
        result = build_project_basic_info(project)
        
        assert isinstance(result['progress_pct'], float)
        assert result['progress_pct'] == 75.25

    def test_handles_decimal_contract_amount(self):
        """测试处理 Decimal 类型的合同金额"""
        project = create_mock_project(contract_amount=Decimal('500000.50'))
        result = build_project_basic_info(project)
        
        assert isinstance(result['contract_amount'], float)
        assert result['contract_amount'] == 500000.50

    def test_handles_none_progress_pct(self):
        """测试处理 None 进度百分比"""
        project = create_mock_project(progress_pct=None)
        result = build_project_basic_info(project)
        
        assert result['progress_pct'] == 0.0

    def test_handles_none_contract_amount(self):
        """测试处理 None 合同金额"""
        project = create_mock_project(contract_amount=None)
        result = build_project_basic_info(project)
        
        assert result['contract_amount'] == 0.0

    def test_handles_zero_values(self):
        """测试处理零值"""
        project = create_mock_project(progress_pct=0, contract_amount=0)
        result = build_project_basic_info(project)
        
        assert result['progress_pct'] == 0.0
        assert result['contract_amount'] == 0.0

    def test_preserves_project_metadata(self):
        """测试保留项目元数据"""
        project = create_mock_project(
            project_code='PRJ-2025-001',
            project_name='重要项目',
            stage='S3',
            status='ST02',
            health='H2',
            pm_name='李四'
        )
        result = build_project_basic_info(project)
        
        assert result['project_code'] == 'PRJ-2025-001'
        assert result['project_name'] == '重要项目'
        assert result['stage'] == 'S3'
        assert result['status'] == 'ST02'
        assert result['health'] == 'H2'
        assert result['pm_name'] == '李四'


# ═══════════════════════════════════════════════════════════════════════════
# build_team_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildTeamInfo:
    """测试团队信息构建"""

    def test_returns_empty_list_when_no_members(self):
        """测试无成员时返回空列表"""
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        
        result = build_team_info(db, project_id=1)
        assert result == []

    def test_returns_single_member(self):
        """测试返回单个成员"""
        db = MagicMock()
        member = create_mock_member()
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert len(result) == 1
        assert result[0]['user_id'] == 1
        assert result[0]['user_name'] == '张三'
        assert result[0]['role_code'] == 'PM'

    def test_returns_multiple_members(self):
        """测试返回多个成员"""
        db = MagicMock()
        members = [
            create_mock_member(user_id=1, role_code='PM', user=create_mock_user(id=1, real_name='张三')),
            create_mock_member(user_id=2, role_code='DEV', user=create_mock_user(id=2, real_name='李四')),
            create_mock_member(user_id=3, role_code='QA', user=create_mock_user(id=3, real_name='王五')),
        ]
        db.query.return_value.options.return_value.filter.return_value.all.return_value = members
        
        result = build_team_info(db, project_id=1)
        
        assert len(result) == 3
        assert result[0]['role_code'] == 'PM'
        assert result[1]['role_code'] == 'DEV'
        assert result[2]['role_code'] == 'QA'

    def test_handles_decimal_allocation_pct(self):
        """测试处理 Decimal 类型的分配百分比"""
        db = MagicMock()
        member = create_mock_member(allocation_pct=Decimal('80.5'))
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert isinstance(result[0]['allocation_pct'], float)
        assert result[0]['allocation_pct'] == 80.5

    def test_handles_none_allocation_pct(self):
        """测试处理 None 分配百分比（默认100）"""
        db = MagicMock()
        member = create_mock_member(allocation_pct=None)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['allocation_pct'] == 100.0

    def test_formats_start_date(self):
        """测试格式化开始日期"""
        db = MagicMock()
        member = create_mock_member(start_date=date(2025, 3, 15))
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['start_date'] == '2025-03-15'

    def test_formats_end_date(self):
        """测试格式化结束日期"""
        db = MagicMock()
        member = create_mock_member(end_date=date(2025, 12, 31))
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['end_date'] == '2025-12-31'

    def test_handles_none_dates(self):
        """测试处理 None 日期"""
        db = MagicMock()
        member = create_mock_member(start_date=None, end_date=None)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['start_date'] is None
        assert result[0]['end_date'] is None

    def test_uses_real_name_when_available(self):
        """测试优先使用真实姓名"""
        db = MagicMock()
        user = create_mock_user(username='zhangsan', real_name='张三')
        member = create_mock_member(user=user)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['user_name'] == '张三'

    def test_falls_back_to_username_when_no_real_name(self):
        """测试无真实姓名时回退到用户名"""
        db = MagicMock()
        user = create_mock_user(username='zhangsan', real_name=None)
        member = create_mock_member(user=user)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['user_name'] == 'zhangsan'

    def test_handles_missing_user(self):
        """测试处理缺失的用户对象"""
        db = MagicMock()
        member = create_mock_member(user_id=999, user=None)
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        
        result = build_team_info(db, project_id=1)
        
        assert result[0]['user_name'] == 'user_999'


# ═══════════════════════════════════════════════════════════════════════════
# build_task_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildTaskInfo:
    """测试任务信息构建"""

    def test_returns_empty_list_when_no_tasks(self):
        """测试无任务时返回空列表"""
        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        result = build_task_info(db, project_id=1)
        assert result == []

    def test_returns_task_list(self):
        """测试返回任务列表"""
        db = MagicMock()
        tasks = [
            create_mock_task(id=1, title='任务1'),
            create_mock_task(id=2, title='任务2'),
        ]
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = tasks
        
        result = build_task_info(db, project_id=1)
        
        assert len(result) == 2
        assert result[0]['title'] == '任务1'
        assert result[1]['title'] == '任务2'

    def test_respects_limit_parameter(self):
        """测试遵守limit参数"""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        build_task_info(db, project_id=1, limit=100)
        
        db.query.return_value.filter.return_value.limit.assert_called_once_with(100)

    def test_default_limit_is_50(self):
        """测试默认limit为50"""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        build_task_info(db, project_id=1)
        
        db.query.return_value.filter.return_value.limit.assert_called_once_with(50)

    def test_handles_decimal_progress(self):
        """测试处理 Decimal 类型的进度"""
        db = MagicMock()
        task = create_mock_task(progress=Decimal('85.5'))
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        
        result = build_task_info(db, project_id=1)
        
        assert isinstance(result[0]['progress'], float)
        assert result[0]['progress'] == 85.5

    def test_handles_none_progress(self):
        """测试处理 None 进度"""
        db = MagicMock()
        task = create_mock_task(progress=None)
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        
        result = build_task_info(db, project_id=1)
        
        assert result[0]['progress'] == 0.0

    def test_formats_plan_end_date(self):
        """测试格式化计划结束日期"""
        db = MagicMock()
        task = create_mock_task(plan_end_date=date(2025, 6, 30))
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        
        result = build_task_info(db, project_id=1)
        
        assert result[0]['plan_end_date'] == '2025-06-30'

    def test_handles_none_plan_end_date(self):
        """测试处理 None 计划结束日期"""
        db = MagicMock()
        task = create_mock_task(plan_end_date=None)
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        
        result = build_task_info(db, project_id=1)
        
        assert result[0]['plan_end_date'] is None


# ═══════════════════════════════════════════════════════════════════════════
# build_bonus_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildBonusInfo:
    """测试奖金信息构建"""

    def test_returns_all_required_keys(self):
        """测试返回所有必需的键"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectBonusService') as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_project_bonus_rules.return_value = []
            mock_svc.get_project_bonus_calculations.return_value = []
            mock_svc.get_project_bonus_distributions.return_value = []
            mock_svc.get_project_bonus_statistics.return_value = {}
            mock_svc.get_project_member_bonus_summary.return_value = []
            
            result = build_bonus_info(db, project_id=1)
        
        expected_keys = {'rules', 'calculations', 'distributions', 'statistics', 'member_summary'}
        assert set(result.keys()) == expected_keys

    def test_handles_bonus_rules(self):
        """测试处理奖金规则"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectBonusService') as MockService:
            mock_rule = MagicMock()
            mock_rule.id = 1
            mock_rule.rule_name = '项目奖金规则'
            mock_rule.bonus_type = 'PROJECT_COMPLETE'
            mock_rule.coefficient = Decimal('1.5')
            
            mock_svc = MockService.return_value
            mock_svc.get_project_bonus_rules.return_value = [mock_rule]
            mock_svc.get_project_bonus_calculations.return_value = []
            mock_svc.get_project_bonus_distributions.return_value = []
            mock_svc.get_project_bonus_statistics.return_value = {}
            mock_svc.get_project_member_bonus_summary.return_value = []
            
            result = build_bonus_info(db, project_id=1)
        
        assert len(result['rules']) == 1
        assert result['rules'][0]['rule_name'] == '项目奖金规则'
        assert result['rules'][0]['coefficient'] == 1.5

    def test_limits_calculations_to_20(self):
        """测试限制计算记录最多返回20条"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectBonusService') as MockService:
            mock_calculations = []
            for i in range(30):
                calc = MagicMock()
                calc.id = i
                calc.calculation_code = f'CALC{i:03d}'
                calc.user = create_mock_user(id=i, real_name=f'用户{i}')
                calc.calculated_amount = Decimal('1000.00')
                calc.status = 'CALCULATED'
                calc.calculated_at = datetime(2025, 1, 1)
                mock_calculations.append(calc)
            
            mock_svc = MockService.return_value
            mock_svc.get_project_bonus_rules.return_value = []
            mock_svc.get_project_bonus_calculations.return_value = mock_calculations
            mock_svc.get_project_bonus_distributions.return_value = []
            mock_svc.get_project_bonus_statistics.return_value = {}
            mock_svc.get_project_member_bonus_summary.return_value = []
            
            result = build_bonus_info(db, project_id=1)
        
        assert len(result['calculations']) == 20

    def test_limits_distributions_to_20(self):
        """测试限制分配记录最多返回20条"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectBonusService') as MockService:
            mock_distributions = []
            for i in range(25):
                dist = MagicMock()
                dist.id = i
                dist.user = create_mock_user(id=i, real_name=f'用户{i}')
                dist.distributed_amount = Decimal('500.00')
                dist.status = 'DISTRIBUTED'
                dist.distributed_at = datetime(2025, 1, 1)
                mock_distributions.append(dist)
            
            mock_svc = MockService.return_value
            mock_svc.get_project_bonus_rules.return_value = []
            mock_svc.get_project_bonus_calculations.return_value = []
            mock_svc.get_project_bonus_distributions.return_value = mock_distributions
            mock_svc.get_project_bonus_statistics.return_value = {}
            mock_svc.get_project_member_bonus_summary.return_value = []
            
            result = build_bonus_info(db, project_id=1)
        
        assert len(result['distributions']) == 20

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectBonusService') as MockService:
            MockService.side_effect = Exception('数据库连接失败')
            
            result = build_bonus_info(db, project_id=1)
        
        assert result == {
            'rules': [],
            'calculations': [],
            'distributions': [],
            'statistics': {},
            'member_summary': [],
        }


# ═══════════════════════════════════════════════════════════════════════════
# build_meeting_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildMeetingInfo:
    """测试会议信息构建"""

    def test_returns_required_keys(self):
        """测试返回必需的键"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectMeetingService') as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_project_meetings.return_value = []
            mock_svc.get_project_meeting_statistics.return_value = {}
            
            result = build_meeting_info(db, project_id=1)
        
        assert 'meetings' in result
        assert 'statistics' in result

    def test_handles_meetings_with_minutes(self):
        """测试处理有会议纪要的会议"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectMeetingService') as MockService:
            mock_meeting = MagicMock()
            mock_meeting.id = 1
            mock_meeting.meeting_name = '项目启动会'
            mock_meeting.meeting_date = date(2025, 1, 15)
            mock_meeting.rhythm_level = 'WEEKLY'
            mock_meeting.status = 'COMPLETED'
            mock_meeting.organizer_name = '张三'
            mock_meeting.minutes = '会议讨论了项目范围和时间表'
            
            mock_svc = MockService.return_value
            mock_svc.get_project_meetings.return_value = [mock_meeting]
            mock_svc.get_project_meeting_statistics.return_value = {}
            
            result = build_meeting_info(db, project_id=1)
        
        assert len(result['meetings']) == 1
        assert result['meetings'][0]['has_minutes'] is True

    def test_handles_meetings_without_minutes(self):
        """测试处理无会议纪要的会议"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectMeetingService') as MockService:
            mock_meeting = MagicMock()
            mock_meeting.id = 2
            mock_meeting.meeting_name = '周会'
            mock_meeting.meeting_date = date(2025, 1, 22)
            mock_meeting.rhythm_level = 'WEEKLY'
            mock_meeting.status = 'SCHEDULED'
            mock_meeting.organizer_name = '李四'
            mock_meeting.minutes = ''
            
            mock_svc = MockService.return_value
            mock_svc.get_project_meetings.return_value = [mock_meeting]
            mock_svc.get_project_meeting_statistics.return_value = {}
            
            result = build_meeting_info(db, project_id=1)
        
        assert result['meetings'][0]['has_minutes'] is False

    def test_limits_meetings_to_20(self):
        """测试限制会议记录最多返回20条"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectMeetingService') as MockService:
            mock_meetings = []
            for i in range(30):
                meeting = MagicMock()
                meeting.id = i
                meeting.meeting_name = f'会议{i}'
                meeting.meeting_date = date(2025, 1, 1)
                meeting.rhythm_level = 'WEEKLY'
                meeting.status = 'COMPLETED'
                meeting.organizer_name = '张三'
                meeting.minutes = ''
                mock_meetings.append(meeting)
            
            mock_svc = MockService.return_value
            mock_svc.get_project_meetings.return_value = mock_meetings
            mock_svc.get_project_meeting_statistics.return_value = {}
            
            result = build_meeting_info(db, project_id=1)
        
        assert len(result['meetings']) == 20

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectMeetingService') as MockService:
            MockService.side_effect = Exception('服务不可用')
            
            result = build_meeting_info(db, project_id=1)
        
        assert result == {'meetings': [], 'statistics': {}}


# ═══════════════════════════════════════════════════════════════════════════
# build_issue_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildIssueInfo:
    """测试问题信息构建"""

    def test_returns_issues_key(self):
        """测试返回issues键"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = build_issue_info(db, project_id=1)
        assert 'issues' in result

    def test_issue_with_solution(self):
        """测试有解决方案的问题"""
        db = MagicMock()
        issue = create_mock_issue(solution='使用备用方案解决')
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        
        result = build_issue_info(db, project_id=1)
        
        assert result['issues'][0]['has_solution'] is True

    def test_issue_without_solution(self):
        """测试无解决方案的问题"""
        db = MagicMock()
        issue = create_mock_issue(solution='')
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        
        result = build_issue_info(db, project_id=1)
        
        assert result['issues'][0]['has_solution'] is False

    def test_formats_report_date(self):
        """测试格式化上报日期"""
        db = MagicMock()
        issue = create_mock_issue(report_date=date(2025, 4, 15))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        
        result = build_issue_info(db, project_id=1)
        
        assert result['issues'][0]['report_date'] == '2025-04-15'

    def test_handles_none_report_date(self):
        """测试处理 None 上报日期"""
        db = MagicMock()
        issue = create_mock_issue(report_date=None)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        
        result = build_issue_info(db, project_id=1)
        
        assert result['issues'][0]['report_date'] is None

    def test_respects_limit_parameter(self):
        """测试遵守limit参数"""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        build_issue_info(db, project_id=1, limit=100)
        
        db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(100)


# ═══════════════════════════════════════════════════════════════════════════
# build_solution_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildSolutionInfo:
    """测试解决方案信息构建"""

    def test_returns_required_keys(self):
        """测试返回必需的键"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectSolutionService') as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_project_solutions.return_value = []
            mock_svc.get_project_solution_statistics.return_value = {}
            
            result = build_solution_info(db, project_id=1)
        
        assert 'solutions' in result
        assert 'statistics' in result

    def test_limits_solutions_to_20(self):
        """测试限制解决方案最多返回20条"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectSolutionService') as MockService:
            mock_solutions = list(range(30))  # 模拟30个解决方案
            
            mock_svc = MockService.return_value
            mock_svc.get_project_solutions.return_value = mock_solutions
            mock_svc.get_project_solution_statistics.return_value = {}
            
            result = build_solution_info(db, project_id=1)
        
        assert len(result['solutions']) == 20

    def test_handles_non_list_solutions(self):
        """测试处理非列表类型的解决方案"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectSolutionService') as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_project_solutions.return_value = "not a list"  # 错误的类型
            mock_svc.get_project_solution_statistics.return_value = {}
            
            result = build_solution_info(db, project_id=1)
        
        assert result['solutions'] == []

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        db = MagicMock()
        with patch('app.services.project_workspace_service.ProjectSolutionService') as MockService:
            MockService.side_effect = Exception('服务异常')
            
            result = build_solution_info(db, project_id=1)
        
        assert result == {'solutions': [], 'statistics': {}}


# ═══════════════════════════════════════════════════════════════════════════
# build_document_info 测试
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildDocumentInfo:
    """测试文档信息构建"""

    def test_returns_empty_list_when_no_documents(self):
        """测试无文档时返回空列表"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = build_document_info(db, project_id=1)
        assert result == []

    def test_returns_document_list(self):
        """测试返回文档列表"""
        db = MagicMock()
        docs = [
            create_mock_document(id=1, doc_name='需求文档'),
            create_mock_document(id=2, doc_name='设计文档'),
        ]
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = docs
        
        result = build_document_info(db, project_id=1)
        
        assert len(result) == 2
        assert result[0]['doc_name'] == '需求文档'
        assert result[1]['doc_name'] == '设计文档'

    def test_formats_created_at(self):
        """测试格式化创建时间"""
        db = MagicMock()
        doc = create_mock_document(created_at=datetime(2025, 1, 1, 10, 30, 0))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [doc]
        
        result = build_document_info(db, project_id=1)
        
        assert result[0]['created_at'] == '2025-01-01T10:30:00'

    def test_handles_none_created_at(self):
        """测试处理 None 创建时间"""
        db = MagicMock()
        doc = create_mock_document(created_at=None)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [doc]
        
        result = build_document_info(db, project_id=1)
        
        assert result[0]['created_at'] is None

    def test_respects_limit_parameter(self):
        """测试遵守limit参数"""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        build_document_info(db, project_id=1, limit=50)
        
        db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(50)

    def test_default_limit_is_20(self):
        """测试默认limit为20"""
        db = MagicMock()
        query_mock = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value = query_mock
        query_mock.all.return_value = []
        
        build_document_info(db, project_id=1)
        
        db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_once_with(20)
