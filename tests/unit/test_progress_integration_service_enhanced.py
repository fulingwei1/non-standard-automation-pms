# -*- coding: utf-8 -*-
"""
进度跟踪联动服务增强测试
测试覆盖：缺料联动、ECN联动、验收联动
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.alert import AlertRecord
from app.models.ecn import Ecn
from app.models.enums import IssueStatusEnum, IssueTypeEnum, SeverityEnum
from app.models.issue import Issue
from app.models.progress import Task
from app.models.project import ProjectMilestone
from app.services.progress_integration_service import ProgressIntegrationService


class TestProgressIntegrationService(TestCase):
    """进度跟踪联动服务测试类"""

    def setUp(self):
        """测试前置准备"""
        self.db = MagicMock(spec=Session)
        self.service = ProgressIntegrationService(self.db)

    def tearDown(self):
        """测试后清理"""
        self.db.reset_mock()

    # ==================== 缺料联动测试 ====================

    def test_handle_shortage_alert_created_no_project_id(self):
        """测试创建缺料预警 - 无项目ID"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = None

        result = self.service.handle_shortage_alert_created(alert)

        self.assertEqual(result, [])
        self.db.query.assert_not_called()

    def test_handle_shortage_alert_created_low_level_no_block(self):
        """测试创建缺料预警 - 低级别预警不阻塞任务"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'level1'
        alert.alert_data = json.dumps({
            'impact_type': 'none',
            'estimated_delay_days': 0
        })
        alert.alert_no = 'ALERT-001'
        alert.target_name = 'Test Material'

        # Mock查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.handle_shortage_alert_created(alert)

        self.assertEqual(result, [])

    def test_handle_shortage_alert_created_critical_level_blocks_tasks(self):
        """测试创建缺料预警 - 严重级别预警阻塞任务"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'CRITICAL'
        alert.alert_data = json.dumps({
            'impact_type': 'stop',
            'estimated_delay_days': 5
        })
        alert.alert_no = 'ALERT-002'
        alert.target_name = 'Critical Material'

        # 创建模拟任务
        task1 = Mock(spec=Task)
        task1.id = 1
        task1.status = 'IN_PROGRESS'
        task1.plan_end = datetime.now() + timedelta(days=10)
        task1.stage = 'S5'

        task2 = Mock(spec=Task)
        task2.id = 2
        task2.status = 'TODO'
        task2.plan_end = datetime.now() + timedelta(days=15)
        task2.stage = 'S6'

        # Mock查询链
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [task1, task2]

        result = self.service.handle_shortage_alert_created(alert)

        # 验证任务被阻塞
        self.assertEqual(len(result), 2)
        self.assertEqual(task1.status, 'BLOCKED')
        self.assertEqual(task2.status, 'BLOCKED')
        self.assertIsNotNone(task1.block_reason)
        self.assertIsNotNone(task2.block_reason)
        self.db.commit.assert_called_once()

    def test_handle_shortage_alert_created_with_delay_adjustment(self):
        """测试创建缺料预警 - 带延迟天数调整"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'level2'
        alert.alert_data = json.dumps({
            'impact_type': 'delay',
            'estimated_delay_days': 7
        })
        alert.alert_no = 'ALERT-003'
        alert.target_name = 'Delayed Material'

        original_date = datetime.now() + timedelta(days=10)
        task = Mock(spec=Task)
        task.id = 1
        task.status = 'TODO'
        task.plan_end = original_date
        task.stage = 'S5'

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [task]

        self.service.handle_shortage_alert_created(alert)

        # 验证计划结束日期被延迟
        expected_date = original_date + timedelta(days=7)
        self.assertEqual(task.plan_end, expected_date)

    def test_handle_shortage_alert_created_json_decode_error(self):
        """测试创建缺料预警 - JSON解析错误"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'level1'
        alert.alert_data = "invalid json {"
        alert.alert_no = 'ALERT-004'
        alert.target_name = 'Material'

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        # 应该不抛出异常
        result = self.service.handle_shortage_alert_created(alert)
        self.assertEqual(result, [])

    def test_handle_shortage_alert_created_delivery_impact(self):
        """测试创建缺料预警 - 交付影响类型阻塞任务"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'level2'
        alert.alert_data = json.dumps({
            'impact_type': 'delivery',
            'estimated_delay_days': 3
        })
        alert.alert_no = 'ALERT-005'
        alert.target_name = 'Delivery Material'

        task = Mock(spec=Task)
        task.id = 1
        task.status = 'IN_PROGRESS'
        task.plan_end = datetime.now() + timedelta(days=10)
        task.stage = 'S5'

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [task]

        result = self.service.handle_shortage_alert_created(alert)

        # delivery影响类型应阻塞任务
        self.assertEqual(len(result), 1)
        self.assertEqual(task.status, 'BLOCKED')

    def test_handle_shortage_alert_resolved_no_project_id(self):
        """测试解决缺料预警 - 无项目ID"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = None

        result = self.service.handle_shortage_alert_resolved(alert)

        self.assertEqual(result, [])
        self.db.query.assert_not_called()

    @patch('app.services.progress_integration_service.apply_keyword_filter')
    def test_handle_shortage_alert_resolved_unblocks_tasks(self, mock_filter):
        """测试解决缺料预警 - 解除任务阻塞"""
        alert = Mock(spec=AlertRecord)
        alert.id = 1
        alert.project_id = 1
        alert.alert_no = 'ALERT-006'
        alert.target_no = 'MAT-001'

        task = Mock(spec=Task)
        task.id = 1
        task.status = 'BLOCKED'
        task.block_reason = 'ALERT-006'

        # Mock apply_keyword_filter返回task id查询
        mock_id_query = MagicMock()
        mock_filter.return_value = mock_id_query

        # Mock查询链 - 第一次查询任务，第二次查询其他预警
        mock_query1 = MagicMock()
        mock_query2 = MagicMock()
        mock_query1.filter.return_value = mock_query1
        mock_query1.all.return_value = [task]
        mock_query2.filter.return_value = mock_query2
        mock_query2.count.return_value = 0  # 无其他预警
        
        self.db.query.side_effect = [mock_query1, mock_id_query, mock_id_query, mock_query2]

        result = self.service.handle_shortage_alert_resolved(alert)

        # 验证任务解除阻塞
        self.assertEqual(len(result), 1)
        self.assertEqual(task.status, 'IN_PROGRESS')
        self.assertIsNone(task.block_reason)
        self.db.commit.assert_called_once()

    @patch('app.services.progress_integration_service.apply_keyword_filter')
    def test_handle_shortage_alert_resolved_keeps_blocked_if_other_alerts(self, mock_filter):
        """测试解决缺料预警 - 有其他预警时保持阻塞"""
        alert = Mock(spec=AlertRecord)
        alert.id = 1
        alert.project_id = 1
        alert.alert_no = 'ALERT-007'
        alert.target_no = 'MAT-002'

        task = Mock(spec=Task)
        task.id = 1
        task.status = 'BLOCKED'
        task.block_reason = 'ALERT-007'

        # Mock apply_keyword_filter返回task id查询
        mock_id_query = MagicMock()
        mock_filter.return_value = mock_id_query

        # Mock查询链 - 第一次查询任务，第二次查询其他预警
        mock_query1 = MagicMock()
        mock_query2 = MagicMock()
        mock_query1.filter.return_value = mock_query1
        mock_query1.all.return_value = [task]
        mock_query2.filter.return_value = mock_query2
        mock_query2.count.return_value = 1  # 有其他严重预警
        
        self.db.query.side_effect = [mock_query1, mock_id_query, mock_id_query, mock_query2]

        result = self.service.handle_shortage_alert_resolved(alert)

        # 验证任务保持阻塞状态
        self.assertEqual(len(result), 0)
        self.assertEqual(task.status, 'BLOCKED')

    # ==================== ECN联动测试 ====================

    def test_handle_ecn_approved_no_project_id(self):
        """测试ECN审批 - 无项目ID"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = None

        result = self.service.handle_ecn_approved(ecn)

        self.assertEqual(result['adjusted_tasks'], [])
        self.assertEqual(result['created_tasks'], [])
        self.assertEqual(result['affected_milestones'], [])

    def test_handle_ecn_approved_below_threshold(self):
        """测试ECN审批 - 影响天数低于阈值"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 2
        ecn.machine_id = None
        ecn.tasks = []

        result = self.service.handle_ecn_approved(ecn, threshold_days=3)

        # 影响小于阈值，不调整任务
        self.assertEqual(result['adjusted_tasks'], [])
        self.db.commit.assert_called_once()

    def test_handle_ecn_approved_adjusts_tasks(self):
        """测试ECN审批 - 调整任务计划"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 5
        ecn.machine_id = 10
        ecn.tasks = []

        original_date = datetime.now() + timedelta(days=10)
        task = Mock(spec=Task)
        task.id = 1
        task.task_name = 'Assembly Task'
        task.plan_end = original_date
        task.actual_start = None
        task.plan_start = datetime.now()

        # Mock查询
        mock_task_query = MagicMock()
        mock_milestone_query = MagicMock()
        
        def query_side_effect(model):
            if model == Task:
                return mock_task_query
            elif model == ProjectMilestone:
                return mock_milestone_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        mock_task_query.filter.return_value = mock_task_query
        mock_task_query.all.return_value = [task]
        mock_milestone_query.filter.return_value = mock_milestone_query
        mock_milestone_query.all.return_value = []

        result = self.service.handle_ecn_approved(ecn)

        # 验证任务计划被调整
        expected_date = original_date + timedelta(days=5)
        self.assertEqual(task.plan_end, expected_date)
        self.assertEqual(len(result['adjusted_tasks']), 1)
        self.assertEqual(result['adjusted_tasks'][0]['task_id'], 1)

    def test_handle_ecn_approved_adjusts_milestones(self):
        """测试ECN审批 - 调整里程碑计划"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 7
        ecn.machine_id = None
        ecn.tasks = []

        original_date = datetime.now() + timedelta(days=30)
        milestone = Mock(spec=ProjectMilestone)
        milestone.id = 1
        milestone.milestone_name = 'FAT Milestone'
        milestone.planned_date = original_date

        # Mock查询链
        mock_task_query = MagicMock()
        mock_milestone_query = MagicMock()
        
        def query_side_effect(model):
            if model == Task:
                return mock_task_query
            elif model == ProjectMilestone:
                return mock_milestone_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        mock_task_query.filter.return_value = mock_task_query
        mock_task_query.all.return_value = []
        mock_milestone_query.filter.return_value = mock_milestone_query
        mock_milestone_query.all.return_value = [milestone]

        result = self.service.handle_ecn_approved(ecn)

        # 验证里程碑计划被调整
        expected_date = original_date + timedelta(days=7)
        self.assertEqual(milestone.planned_date, expected_date)
        self.assertEqual(len(result['affected_milestones']), 1)

    def test_handle_ecn_approved_without_ecn_tasks(self):
        """测试ECN审批 - 无ECN执行任务"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 2
        ecn.machine_id = 20
        ecn.tasks = []  # 无ECN任务

        # Mock查询
        mock_query1 = MagicMock()
        mock_query2 = MagicMock()
        mock_query1.filter.return_value = mock_query1
        mock_query1.all.return_value = []
        mock_query2.filter.return_value = mock_query2
        mock_query2.all.return_value = []
        
        self.db.query.side_effect = [mock_query1, mock_query2]

        result = self.service.handle_ecn_approved(ecn)

        # 无ECN任务，不创建或更新任务
        self.assertEqual(len(result['created_tasks']), 0)
        self.db.commit.assert_called_once()

    def test_handle_ecn_approved_with_ecn_tasks_basic(self):
        """测试ECN审批 - 带ECN任务（基础验证）"""
        ecn_task = Mock()
        ecn_task.task_name = 'ECN Implementation'
        ecn_task.planned_start = datetime.now()
        ecn_task.planned_end = datetime.now() + timedelta(days=5)
        ecn_task.assignee_id = 100
        ecn_task.status = 'TODO'

        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 1
        ecn.machine_id = 20
        ecn.tasks = [ecn_task]

        # Mock查询 - 简化处理
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        
        self.db.query.return_value = mock_query

        result = self.service.handle_ecn_approved(ecn)

        # 验证方法可以正常调用
        self.assertIsInstance(result, dict)
        self.assertIn('created_tasks', result)
        self.assertIn('adjusted_tasks', result)
        self.db.commit.assert_called()

    # ==================== 验收联动测试 ====================

    def test_check_milestone_completion_requirements_delivery_no_deliverables(self):
        """测试里程碑完成检查 - 交付类型但无交付物"""
        milestone = Mock(spec=ProjectMilestone)
        milestone.milestone_type = 'DELIVERY'
        milestone.deliverables = None

        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        self.assertTrue(can_complete)
        self.assertEqual(missing, [])

    def test_check_milestone_completion_requirements_deliverables_not_approved(self):
        """测试里程碑完成检查 - 交付物未全部审批"""
        milestone = Mock(spec=ProjectMilestone)
        milestone.milestone_type = 'DELIVERY'
        milestone.deliverables = json.dumps([
            {'name': 'Doc1', 'status': 'APPROVED'},
            {'name': 'Doc2', 'status': 'PENDING'}
        ])

        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        self.assertFalse(can_complete)
        self.assertIn('交付物未全部审批', missing)

    def test_check_milestone_completion_requirements_deliverables_all_approved(self):
        """测试里程碑完成检查 - 交付物全部审批"""
        milestone = Mock(spec=ProjectMilestone)
        milestone.milestone_type = 'DELIVERY'
        milestone.deliverables = json.dumps([
            {'name': 'Doc1', 'status': 'APPROVED'},
            {'name': 'Doc2', 'status': 'APPROVED'}
        ])
        milestone.acceptance_required = False

        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        self.assertTrue(can_complete)
        self.assertEqual(missing, [])

    def test_check_milestone_completion_requirements_no_acceptance_required(self):
        """测试里程碑完成检查 - 无需验收"""
        milestone = Mock()
        milestone.id = 1
        milestone.project_id = 1
        milestone.milestone_type = 'OTHER'
        milestone.deliverables = None
        # 明确设置不需要验收
        type(milestone).acceptance_required = PropertyMock(return_value=False)

        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        # 无需验收，可以完成
        self.assertTrue(can_complete)
        self.assertEqual(missing, [])

    def test_check_milestone_completion_requirements_simple_milestone(self):
        """测试里程碑完成检查 - 简单里程碑无额外要求"""
        milestone = Mock()
        milestone.milestone_type = 'MILESTONE'
        milestone.deliverables = None
        # 明确设置不需要验收 - 避免hasattr检查问题
        type(milestone).acceptance_required = PropertyMock(return_value=False)
        
        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)
        
        # 无额外要求，可以完成
        self.assertTrue(can_complete)
        self.assertEqual(missing, [])

    def test_check_milestone_completion_requirements_invalid_json(self):
        """测试里程碑完成检查 - 无效JSON交付物"""
        milestone = Mock(spec=ProjectMilestone)
        milestone.milestone_type = 'DELIVERY'
        milestone.deliverables = "invalid json {"
        milestone.acceptance_required = False

        # 不应抛出异常
        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        self.assertTrue(can_complete)

    def test_handle_acceptance_failed_not_failed_status(self):
        """测试处理验收失败 - 非失败状态"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.overall_result = 'PASSED'

        result = self.service.handle_acceptance_failed(acceptance)

        self.assertEqual(result, [])
        self.db.query.assert_not_called()

    def test_handle_acceptance_failed_fat_blocks_s6_milestone(self):
        """测试处理验收失败 - FAT验收失败阻塞S6里程碑"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 1
        acceptance.overall_result = 'FAILED'
        acceptance.acceptance_type = 'FAT'
        acceptance.project_id = 1
        acceptance.order_no = 'FAT-001'
        acceptance.created_by = 100

        milestone = Mock(spec=ProjectMilestone)
        milestone.id = 1
        milestone.milestone_name = 'Factory Acceptance'
        milestone.stage_code = 'S6'
        milestone.status = 'IN_PROGRESS'

        # Mock查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [milestone]

        result = self.service.handle_acceptance_failed(acceptance)

        # 验证里程碑被阻塞
        self.assertEqual(len(result), 1)
        self.assertEqual(milestone.status, 'BLOCKED')
        self.db.add.assert_called()
        self.db.commit.assert_called_once()

    def test_handle_acceptance_failed_sat_blocks_s8_s9_milestone(self):
        """测试处理验收失败 - SAT验收失败阻塞S8/S9里程碑"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 2
        acceptance.overall_result = 'FAILED'
        acceptance.acceptance_type = 'SAT'
        acceptance.project_id = 1
        acceptance.order_no = 'SAT-001'
        acceptance.created_by = 101

        milestone1 = Mock(spec=ProjectMilestone)
        milestone1.id = 2
        milestone1.milestone_name = 'Site Acceptance'
        milestone1.stage_code = 'S8'
        milestone1.status = 'PENDING'

        milestone2 = Mock(spec=ProjectMilestone)
        milestone2.id = 3
        milestone2.milestone_name = 'Final Delivery'
        milestone2.stage_code = 'S9'
        milestone2.status = 'PENDING'

        # Mock查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [milestone1, milestone2]

        result = self.service.handle_acceptance_failed(acceptance)

        # 验证两个里程碑都被阻塞
        self.assertEqual(len(result), 2)
        self.assertEqual(milestone1.status, 'BLOCKED')
        self.assertEqual(milestone2.status, 'BLOCKED')

    def test_handle_acceptance_failed_creates_issue(self):
        """测试处理验收失败 - 生成问题清单"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 3
        acceptance.overall_result = 'FAILED'
        acceptance.acceptance_type = 'FINAL'
        acceptance.project_id = 1
        acceptance.order_no = 'FINAL-001'
        acceptance.created_by = 102

        milestone = Mock(spec=ProjectMilestone)
        milestone.id = 4
        milestone.milestone_name = 'Final Acceptance'
        milestone.stage_code = 'S9'
        milestone.status = 'IN_PROGRESS'

        # Mock查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [milestone]

        # 记录add调用
        added_objects = []
        self.db.add.side_effect = lambda obj: added_objects.append(obj)

        result = self.service.handle_acceptance_failed(acceptance)

        # 验证生成了问题
        issues = [obj for obj in added_objects if isinstance(obj, (Issue, Mock))]
        self.assertGreater(len(issues), 0)

    def test_handle_acceptance_passed_not_passed_status(self):
        """测试处理验收通过 - 非通过状态"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.overall_result = 'FAILED'

        result = self.service.handle_acceptance_passed(acceptance)

        self.assertEqual(result, [])
        self.db.query.assert_not_called()

    def test_handle_acceptance_passed_unblocks_milestone(self):
        """测试处理验收通过 - 解除里程碑阻塞"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 4
        acceptance.overall_result = 'PASSED'
        acceptance.acceptance_type = 'FAT'
        acceptance.project_id = 1

        milestone = Mock(spec=ProjectMilestone)
        milestone.id = 5
        milestone.status = 'BLOCKED'
        milestone.stage_code = 'S6'

        # Mock查询链
        mock_milestone_query = MagicMock()
        mock_issue_query = MagicMock()
        
        def query_side_effect(model):
            if model == ProjectMilestone:
                return mock_milestone_query
            elif model == Issue:
                return mock_issue_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        mock_milestone_query.filter.return_value = mock_milestone_query
        mock_milestone_query.all.return_value = [milestone]
        mock_issue_query.filter.return_value = mock_issue_query
        mock_issue_query.count.return_value = 0  # 无其他阻塞问题

        result = self.service.handle_acceptance_passed(acceptance)

        # 验证里程碑解除阻塞
        self.assertEqual(len(result), 1)
        self.assertEqual(milestone.status, 'IN_PROGRESS')
        self.db.commit.assert_called_once()

    def test_handle_acceptance_passed_keeps_blocked_if_other_issues(self):
        """测试处理验收通过 - 有其他阻塞问题时保持阻塞"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 5
        acceptance.overall_result = 'PASSED'
        acceptance.acceptance_type = 'SAT'
        acceptance.project_id = 1

        milestone = Mock(spec=ProjectMilestone)
        milestone.id = 6
        milestone.status = 'BLOCKED'
        milestone.stage_code = 'S8'

        # Mock查询链
        mock_milestone_query = MagicMock()
        mock_issue_query = MagicMock()
        
        def query_side_effect(model):
            if model == ProjectMilestone:
                return mock_milestone_query
            elif model == Issue:
                return mock_issue_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        mock_milestone_query.filter.return_value = mock_milestone_query
        mock_milestone_query.all.return_value = [milestone]
        mock_issue_query.filter.return_value = mock_issue_query
        mock_issue_query.count.return_value = 1  # 有其他阻塞问题

        result = self.service.handle_acceptance_passed(acceptance)

        # 验证里程碑保持阻塞
        self.assertEqual(len(result), 0)
        self.assertEqual(milestone.status, 'BLOCKED')

    def test_handle_acceptance_passed_multiple_milestones(self):
        """测试处理验收通过 - 多个里程碑解除阻塞"""
        acceptance = Mock(spec=AcceptanceOrder)
        acceptance.id = 6
        acceptance.overall_result = 'PASSED'
        acceptance.acceptance_type = 'FINAL'
        acceptance.project_id = 1

        milestone1 = Mock(spec=ProjectMilestone)
        milestone1.id = 7
        milestone1.status = 'BLOCKED'
        milestone1.stage_code = 'S8'

        milestone2 = Mock(spec=ProjectMilestone)
        milestone2.id = 8
        milestone2.status = 'BLOCKED'
        milestone2.stage_code = 'S9'

        # Mock查询链
        mock_milestone_query = MagicMock()
        mock_issue_query = MagicMock()
        
        def query_side_effect(model):
            if model == ProjectMilestone:
                return mock_milestone_query
            elif model == Issue:
                return mock_issue_query
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        mock_milestone_query.filter.return_value = mock_milestone_query
        mock_milestone_query.all.return_value = [milestone1, milestone2]
        mock_issue_query.filter.return_value = mock_issue_query
        mock_issue_query.count.return_value = 0

        result = self.service.handle_acceptance_passed(acceptance)

        # 验证两个里程碑都解除阻塞
        self.assertEqual(len(result), 2)
        self.assertEqual(milestone1.status, 'IN_PROGRESS')
        self.assertEqual(milestone2.status, 'IN_PROGRESS')

    # ==================== 边界条件和异常测试 ====================

    def test_handle_shortage_alert_created_empty_tasks(self):
        """测试创建缺料预警 - 无匹配任务"""
        alert = Mock(spec=AlertRecord)
        alert.project_id = 1
        alert.alert_level = 'CRITICAL'
        alert.alert_data = '{}'
        alert.alert_no = 'ALERT-100'
        alert.target_name = 'Material'

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = self.service.handle_shortage_alert_created(alert)

        self.assertEqual(result, [])
        self.db.commit.assert_called_once()

    def test_handle_ecn_approved_zero_impact_days(self):
        """测试ECN审批 - 零影响天数"""
        ecn = Mock(spec=Ecn)
        ecn.project_id = 1
        ecn.schedule_impact_days = 0
        ecn.machine_id = None
        ecn.tasks = []

        result = self.service.handle_ecn_approved(ecn)

        self.assertEqual(result['adjusted_tasks'], [])
        self.assertEqual(result['affected_milestones'], [])

    def test_check_milestone_completion_deliverables_empty_list(self):
        """测试里程碑完成检查 - 空交付物列表"""
        milestone = Mock(spec=ProjectMilestone)
        milestone.milestone_type = 'DELIVERY'
        milestone.deliverables = json.dumps([])
        milestone.acceptance_required = False

        can_complete, missing = self.service.check_milestone_completion_requirements(milestone)

        self.assertTrue(can_complete)
        self.assertEqual(missing, [])

    def test_service_initialization(self):
        """测试服务初始化"""
        db = MagicMock(spec=Session)
        service = ProgressIntegrationService(db)

        self.assertIsNotNone(service)
        self.assertEqual(service.db, db)
