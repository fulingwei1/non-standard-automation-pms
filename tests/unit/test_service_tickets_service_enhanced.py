# -*- coding: utf-8 -*-
"""
服务工单管理服务增强测试
覆盖率目标：70%+
测试用例数：30-40个
"""
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, PropertyMock

from fastapi import HTTPException

from app.services.service.service_tickets_service import ServiceTicketsService
from app.models.service import ServiceTicket, CustomerSatisfaction
from app.models.user import User
from app.schemas.service import PaginatedResponse


class TestServiceTicketsService(unittest.TestCase):
    """服务工单管理服务测试"""

    def setUp(self):
        """每个测试前的准备工作"""
        self.db = MagicMock()
        self.service = ServiceTicketsService(db=self.db)

    def tearDown(self):
        """每个测试后的清理工作"""
        self.db.reset_mock()

    # ==================== 1. 仪表板统计测试 ====================

    def test_get_dashboard_statistics_basic(self):
        """测试基础仪表板统计"""
        # Mock 查询返回值
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.return_value = 5

        # Mock 私有方法
        with patch.object(self.service, '_calculate_avg_response_time', return_value=120.5), \
             patch.object(self.service, '_calculate_satisfaction_rate', return_value=4.5):
            
            result = self.service.get_dashboard_statistics()
            
            self.assertEqual(result.active_cases, 5)
            self.assertEqual(result.avg_response_time, 120.5)
            self.assertEqual(result.customer_satisfaction, 4.5)

    def test_get_dashboard_statistics_zero_values(self):
        """测试仪表板统计零值情况"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.return_value = 0

        with patch.object(self.service, '_calculate_avg_response_time', return_value=0.0), \
             patch.object(self.service, '_calculate_satisfaction_rate', return_value=0.0):
            
            result = self.service.get_dashboard_statistics()
            
            self.assertEqual(result.active_cases, 0)
            self.assertEqual(result.pending_cases, 0)
            self.assertEqual(result.resolved_today, 0)

    def test_calculate_avg_response_time_no_data(self):
        """测试无数据时的平均响应时间计算"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.with_entities.return_value.all.return_value = []
        
        result = self.service._calculate_avg_response_time()
        
        self.assertEqual(result, 0)

    def test_calculate_avg_response_time_with_data(self):
        """测试有数据时的平均响应时间计算"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.with_entities.return_value.all.return_value = [
            (3600,),  # 1小时 = 3600秒
            (7200,),  # 2小时 = 7200秒
        ]
        
        result = self.service._calculate_avg_response_time()
        
        # 平均 (3600 + 7200) / 2 = 5400秒 = 90分钟
        self.assertEqual(result, 90.0)

    def test_calculate_satisfaction_rate_no_data(self):
        """测试无数据时的满意度计算"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.with_entities.return_value.all.return_value = []
        
        result = self.service._calculate_satisfaction_rate()
        
        self.assertEqual(result, 0)

    def test_calculate_satisfaction_rate_with_data(self):
        """测试有数据时的满意度计算"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.with_entities.return_value.all.return_value = [
            (5.0,),
            (4.5,),
            (4.0,),
        ]
        
        result = self.service._calculate_satisfaction_rate()
        
        # 平均 (5.0 + 4.5 + 4.0) / 3 = 4.5
        self.assertEqual(result, 4.5)

    # ==================== 2. 项目成员测试 ====================

    def test_get_project_members_success(self):
        """测试获取项目成员成功"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "张三"
        mock_user.department = "技术部"
        mock_user.position = "工程师"
        mock_user.phone = "13800138000"
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_user]
        
        result = self.service.get_project_members()
        
        self.assertIn("members", result)
        self.assertEqual(len(result["members"]), 1)
        self.assertEqual(result["members"][0]["id"], 1)
        self.assertEqual(result["members"][0]["name"], "张三")

    def test_get_project_members_empty(self):
        """测试获取项目成员为空"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_project_members()
        
        self.assertIn("members", result)
        self.assertEqual(len(result["members"]), 0)

    def test_get_project_members_with_real_name_fallback(self):
        """测试成员姓名回退到 real_name"""
        mock_user = MagicMock()
        mock_user.id = 2
        mock_user.name = None
        mock_user.real_name = "李四"
        mock_user.department = "客服部"
        mock_user.position = "客服专员"
        mock_user.phone = "13900139000"
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_user]
        
        result = self.service.get_project_members()
        
        self.assertEqual(result["members"][0]["name"], "李四")

    # ==================== 3. 工单项目关联测试 ====================

    def test_get_ticket_projects_success(self):
        """测试获取工单项目成功"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "测试项目"
        mock_project.status = "IN_PROGRESS"
        
        mock_ticket = MagicMock()
        mock_ticket.projects = [mock_project]
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.first.return_value = mock_ticket
        
        result = self.service.get_ticket_projects(1)
        
        self.assertIn("projects", result)
        self.assertEqual(len(result["projects"]), 1)
        self.assertEqual(result["projects"][0]["name"], "测试项目")

    def test_get_ticket_projects_not_found(self):
        """测试工单不存在时的异常"""
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        with self.assertRaises(HTTPException) as context:
            self.service.get_ticket_projects(999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "工单不存在")

    # ==================== 4. 工单统计测试 ====================

    def test_get_ticket_statistics_basic(self):
        """测试基础工单统计"""
        mock_query = self.db.query.return_value
        mock_query.count.return_value = 10
        
        # Status 分布 - 修复：返回正确的对象格式
        status_stat1 = MagicMock()
        status_stat1.status = "PENDING"
        status_stat1.count = 5
        
        status_stat2 = MagicMock()
        status_stat2.status = "COMPLETED"
        status_stat2.count = 5
        
        priority_stat1 = MagicMock()
        priority_stat1.priority = "HIGH"
        priority_stat1.count = 3
        
        priority_stat2 = MagicMock()
        priority_stat2.priority = "NORMAL"
        priority_stat2.count = 7
        
        mock_query.with_entities.return_value.group_by.return_value.all.side_effect = [
            [status_stat1, status_stat2],
            [priority_stat1, priority_stat2]
        ]
        
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_ticket_statistics()
        
        self.assertEqual(result["total_tickets"], 10)
        self.assertIn("status_distribution", result)
        self.assertIn("priority_distribution", result)

    def test_get_ticket_statistics_with_filters(self):
        """测试带过滤条件的工单统计"""
        mock_query = self.db.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.count.return_value = 5
        mock_filtered.with_entities.return_value.group_by.return_value.all.return_value = []
        mock_filtered.filter.return_value.all.return_value = []
        
        result = self.service.get_ticket_statistics(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            status="COMPLETED",
            priority="HIGH",
            assigned_to=1
        )
        
        # 验证统计结果
        self.assertIn("total_tickets", result)

    def test_get_ticket_statistics_processing_time(self):
        """测试处理时长统计"""
        mock_ticket1 = MagicMock()
        mock_ticket1.created_at = datetime(2024, 1, 1, 10, 0)
        mock_ticket1.resolved_time = datetime(2024, 1, 1, 12, 0)
        
        mock_ticket2 = MagicMock()
        mock_ticket2.created_at = datetime(2024, 1, 2, 10, 0)
        mock_ticket2.resolved_at = datetime(2024, 1, 2, 14, 0)
        
        mock_query = self.db.query.return_value
        mock_query.count.return_value = 2
        mock_query.filter.return_value.all.return_value = [mock_ticket1, mock_ticket2]
        
        # Mock status/priority distribution
        status_stat = MagicMock()
        status_stat.status = "COMPLETED"
        status_stat.count = 2
        
        mock_query.with_entities.return_value.group_by.return_value.all.side_effect = [
            [status_stat],
            []
        ]
        
        result = self.service.get_ticket_statistics()
        
        # (2小时 + 4小时) / 2 = 3小时
        self.assertEqual(result["average_processing_time_hours"], 3.0)

    def test_get_ticket_statistics_completion_rate(self):
        """测试完成率计算"""
        mock_query = self.db.query.return_value
        mock_query.count.return_value = 10
        
        status_stat1 = MagicMock()
        status_stat1.status = "COMPLETED"
        status_stat1.count = 7
        
        status_stat2 = MagicMock()
        status_stat2.status = "PENDING"
        status_stat2.count = 3
        
        mock_query.with_entities.return_value.group_by.return_value.all.side_effect = [
            [status_stat1, status_stat2],
            []
        ]
        
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_ticket_statistics()
        
        self.assertEqual(result["completed_tickets"], 7)
        self.assertEqual(result["completion_rate"], 70.0)

    def test_get_ticket_statistics_zero_tickets(self):
        """测试零工单时的统计"""
        mock_query = self.db.query.return_value
        mock_query.count.return_value = 0
        mock_query.with_entities.return_value.group_by.return_value.all.side_effect = [[], []]
        mock_query.filter.return_value.all.return_value = []
        
        result = self.service.get_ticket_statistics()
        
        self.assertEqual(result["total_tickets"], 0)
        self.assertEqual(result["completion_rate"], 0)

    # ==================== 5. 工单列表测试 ====================

    def test_get_service_tickets_basic(self):
        """测试基础工单列表"""
        # 创建完整的 mock 工单对象
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.ticket_no = "REPAIR20240101001"
        mock_ticket.project_name = "测试项目"
        mock_ticket.customer_name = "测试客户"
        mock_ticket.problem_type = "repair"
        mock_ticket.problem_desc = "设备故障"
        mock_ticket.urgency = "HIGH"
        mock_ticket.reported_by = "1"
        mock_ticket.assigned_to_name = "张三"
        mock_ticket.status = "PENDING"
        mock_ticket.solution = None
        mock_ticket.root_cause = None
        mock_ticket.preventive_action = None
        mock_ticket.feedback = None
        mock_ticket.created_at = datetime.now()
        mock_ticket.updated_at = datetime.now()
        
        mock_query = self.db.query.return_value
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [mock_ticket]
        
        with patch('app.services.service.service_tickets_service.apply_keyword_filter', return_value=mock_query), \
             patch('app.services.service.service_tickets_service.apply_pagination', return_value=mock_query), \
             patch('app.services.service.service_tickets_service.get_pagination_params') as mock_pagination:
            
            mock_pagination.return_value = MagicMock(page=1, page_size=20, offset=0, limit=20, pages_for_total=lambda x: 1)
            
            result = self.service.get_service_tickets(page=1, page_size=20)
            
            self.assertIsInstance(result, PaginatedResponse)
            self.assertEqual(result.total, 1)
            self.assertEqual(result.page, 1)

    def test_get_service_tickets_with_filters(self):
        """测试带筛选条件的工单列表"""
        mock_query = self.db.query.return_value
        mock_query.options.return_value = mock_query
        mock_filtered = mock_query.filter.return_value
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.order_by.return_value = mock_filtered
        mock_filtered.count.return_value = 0
        mock_filtered.all.return_value = []
        
        with patch('app.services.service.service_tickets_service.apply_keyword_filter', return_value=mock_query), \
             patch('app.services.service.service_tickets_service.apply_pagination', return_value=mock_filtered), \
             patch('app.services.service.service_tickets_service.get_pagination_params') as mock_pagination:
            
            mock_pagination.return_value = MagicMock(page=1, page_size=20, offset=0, limit=20, pages_for_total=lambda x: 0)
            
            result = self.service.get_service_tickets(
                keyword="测试",
                status="PENDING",
                priority="HIGH",
                ticket_type="repair",
                assigned_to=1,
                customer_id=10,
                project_id=5,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
            
            # 验证返回结果是分页响应
            self.assertIsInstance(result, PaginatedResponse)
            self.assertEqual(result.total, 0)

    def test_get_service_tickets_pagination(self):
        """测试分页功能"""
        mock_query = self.db.query.return_value
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.all.return_value = []
        
        with patch('app.services.service.service_tickets_service.apply_keyword_filter', return_value=mock_query), \
             patch('app.services.service.service_tickets_service.apply_pagination', return_value=mock_query), \
             patch('app.services.service.service_tickets_service.get_pagination_params') as mock_pagination:
            
            mock_pagination.return_value = MagicMock(page=2, page_size=10, offset=10, limit=10, pages_for_total=lambda x: 5)
            
            result = self.service.get_service_tickets(page=2, page_size=10)
            
            self.assertEqual(result.page, 2)
            self.assertEqual(result.page_size, 10)
            self.assertEqual(result.pages, 5)

    # ==================== 6. 单个工单测试 ====================

    def test_get_service_ticket_success(self):
        """测试获取单个工单成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        
        mock_query = self.db.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = mock_ticket
        
        result = self.service.get_service_ticket(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    def test_get_service_ticket_not_found(self):
        """测试获取不存在的工单"""
        mock_query = self.db.query.return_value
        mock_query.options.return_value.filter.return_value.first.return_value = None
        
        result = self.service.get_service_ticket(999)
        
        self.assertIsNone(result)

    # ==================== 7. 创建工单测试 ====================

    def test_create_service_ticket_basic(self):
        """测试基础创建工单"""
        mock_ticket_data = MagicMock()
        mock_ticket_data.ticket_type = "repair"
        mock_ticket_data.problem_desc = "设备故障"
        mock_ticket_data.urgency = "HIGH"
        mock_ticket_data.customer_id = 1
        mock_ticket_data.project_id = 1
        
        mock_user = MagicMock()
        mock_user.id = 1
        
        with patch.object(self.service, '_generate_ticket_number', return_value="REPAIR20240101001"), \
             patch.object(self.service, '_auto_assign_ticket'), \
             patch.object(self.service, '_send_ticket_notification'), \
             patch('app.services.service.service_tickets_service.save_obj') as mock_save:
            
            result = self.service.create_service_ticket(mock_ticket_data, mock_user)
            
            mock_save.assert_called_once()
            self.assertIsInstance(result, ServiceTicket)
            self.assertEqual(result.status, "PENDING")

    def test_create_service_ticket_with_description_fallback(self):
        """测试创建工单时描述字段回退"""
        mock_ticket_data = MagicMock()
        mock_ticket_data.ticket_type = "maintenance"
        mock_ticket_data.description = "定期维护"
        mock_ticket_data.problem_desc = None
        mock_ticket_data.urgency = "NORMAL"
        
        with patch.object(self.service, '_generate_ticket_number', return_value="MAINT20240101001"), \
             patch.object(self.service, '_auto_assign_ticket'), \
             patch.object(self.service, '_send_ticket_notification'), \
             patch('app.services.service.service_tickets_service.save_obj'):
            
            result = self.service.create_service_ticket(mock_ticket_data)
            
            self.assertEqual(result.problem_desc, "定期维护")

    def test_generate_ticket_number_installation(self):
        """测试生成安装工单编号"""
        today = date.today()
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.return_value = 5
        
        result = self.service._generate_ticket_number("installation")
        
        expected = f"INST{today.strftime('%Y%m%d')}0006"
        self.assertEqual(result, expected)

    def test_generate_ticket_number_other(self):
        """测试生成其他类型工单编号"""
        today = date.today()
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.return_value = 0
        
        result = self.service._generate_ticket_number("unknown_type")
        
        expected = f"SRV{today.strftime('%Y%m%d')}0001"
        self.assertEqual(result, expected)

    # ==================== 8. 分配工单测试 ====================

    def test_assign_ticket_success(self):
        """测试分配工单成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        
        mock_assign_data = MagicMock()
        mock_assign_data.assigned_to = 2
        mock_assign_data.assignee_id = 2
        
        with patch.object(self.service, 'get_service_ticket', return_value=mock_ticket), \
             patch.object(self.service, '_send_ticket_notification'):
            
            result = self.service.assign_ticket(1, mock_assign_data)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.status, "assigned")
            self.db.commit.assert_called_once()

    def test_assign_ticket_not_found(self):
        """测试分配不存在的工单"""
        with patch.object(self.service, 'get_service_ticket', return_value=None):
            
            result = self.service.assign_ticket(999, MagicMock())
            
            self.assertIsNone(result)

    # ==================== 9. 更新状态测试 ====================

    def test_update_ticket_status_to_completed(self):
        """测试更新工单状态为已完成"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "IN_PROGRESS"
        
        with patch.object(self.service, 'get_service_ticket', return_value=mock_ticket), \
             patch.object(self.service, '_send_ticket_notification'):
            
            result = self.service.update_ticket_status(1, "COMPLETED")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.status, "COMPLETED")
            self.assertIsNotNone(result.resolved_at)

    def test_update_ticket_status_to_in_progress(self):
        """测试更新工单状态为进行中"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.status = "PENDING"
        
        with patch.object(self.service, 'get_service_ticket', return_value=mock_ticket), \
             patch.object(self.service, '_send_ticket_notification'):
            
            result = self.service.update_ticket_status(1, "IN_PROGRESS")
            
            self.assertIsNotNone(result.started_at)

    def test_update_ticket_status_not_found(self):
        """测试更新不存在工单的状态"""
        with patch.object(self.service, 'get_service_ticket', return_value=None):
            
            result = self.service.update_ticket_status(999, "COMPLETED")
            
            self.assertIsNone(result)

    # ==================== 10. 关闭工单测试 ====================

    def test_close_ticket_success(self):
        """测试关闭工单成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        
        mock_close_data = MagicMock()
        mock_close_data.resolution_summary = "问题已解决"
        mock_close_data.customer_satisfaction = 5
        
        with patch.object(self.service, 'get_service_ticket', return_value=mock_ticket), \
             patch.object(self.service, '_send_ticket_notification'), \
             patch.object(self.service, '_create_satisfaction_survey'):
            
            result = self.service.close_ticket(1, mock_close_data)
            
            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(result.resolved_at)

    def test_close_ticket_with_feedback(self):
        """测试带客户反馈关闭工单"""
        mock_ticket = MagicMock()
        mock_close_data = MagicMock()
        mock_close_data.customer_feedback = "服务很好"
        mock_close_data.satisfaction = 5
        
        with patch.object(self.service, 'get_service_ticket', return_value=mock_ticket), \
             patch.object(self.service, '_send_ticket_notification'), \
             patch.object(self.service, '_create_satisfaction_survey'):
            
            result = self.service.close_ticket(1, mock_close_data)
            
            self.assertEqual(result.customer_feedback, "服务很好")

    def test_close_ticket_not_found(self):
        """测试关闭不存在的工单"""
        with patch.object(self.service, 'get_service_ticket', return_value=None):
            
            result = self.service.close_ticket(999, MagicMock())
            
            self.assertIsNone(result)

    # ==================== 11. 自动分配测试 ====================

    def test_auto_assign_ticket_success(self):
        """测试自动分配工单成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.ticket_type = "repair"
        
        mock_engineer = MagicMock()
        mock_engineer.id = 10
        mock_engineer.department = "维修部"
        
        mock_user_query = self.db.query.return_value
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [mock_engineer]
        
        # Mock 工程师负载查询
        mock_ticket_query = self.db.query.return_value
        mock_ticket_query.filter.return_value.count.return_value = 2
        
        self.service._auto_assign_ticket(mock_ticket)
        
        self.assertEqual(mock_ticket.assigned_to_id, 10)
        self.assertEqual(mock_ticket.status, "assigned")

    def test_auto_assign_ticket_no_engineers(self):
        """测试无可用工程师时的自动分配"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.ticket_type = "repair"
        
        mock_user_query = self.db.query.return_value
        mock_user_query.filter.return_value.filter.return_value.all.return_value = []
        
        # 不应该抛出异常，只记录日志
        self.service._auto_assign_ticket(mock_ticket)
        
        # 工单状态不应被修改
        self.assertNotEqual(getattr(mock_ticket, 'status', None), "assigned")

    def test_auto_assign_ticket_load_balancing(self):
        """测试负载均衡分配"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.ticket_type = "maintenance"
        
        # 两个工程师，不同负载
        mock_eng1 = MagicMock()
        mock_eng1.id = 10
        
        mock_eng2 = MagicMock()
        mock_eng2.id = 11
        
        mock_user_query = self.db.query.return_value
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [mock_eng1, mock_eng2]
        
        # Mock 负载查询：eng1有5个工单，eng2有2个工单
        mock_load_query = self.db.query.return_value
        mock_load_query.filter.return_value.count.side_effect = [5, 2]
        
        self.service._auto_assign_ticket(mock_ticket)
        
        # 应分配给负载较低的 eng2
        self.assertEqual(mock_ticket.assigned_to_id, 11)

    # ==================== 12. 通知测试 ====================

    def test_send_ticket_notification_success(self):
        """测试发送工单通知成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.ticket_no = "REPAIR20240101001"
        mock_ticket.problem_type = "repair"
        mock_ticket.status = "PENDING"
        mock_ticket.problem_desc = "设备故障"
        mock_ticket.assigned_to_id = 10
        mock_ticket.reported_by = "5"
        mock_ticket.urgency = "HIGH"
        
        # 修复：使用正确的导入路径
        with patch('app.services.unified_notification_service.get_notification_service') as mock_get_service:
            mock_notification_service = MagicMock()
            mock_get_service.return_value = mock_notification_service
            
            self.service._send_ticket_notification(mock_ticket, "created")
            
            # 应发送2条通知（分配人+报告人）
            self.assertEqual(mock_notification_service.send_notification.call_count, 2)

    def test_send_ticket_notification_exception(self):
        """测试发送通知异常时不影响主流程"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        
        # 修复：使用正确的导入路径
        with patch('app.services.unified_notification_service.get_notification_service', side_effect=Exception("通知服务异常")):
            
            # 不应抛出异常
            self.service._send_ticket_notification(mock_ticket, "created")

    # ==================== 13. 满意度调查测试 ====================

    def test_create_satisfaction_survey_success(self):
        """测试创建满意度调查成功"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.assigned_to_id = 10
        
        mock_customer = MagicMock()
        mock_customer.name = "测试客户"
        mock_customer.contact = "13800138000"
        mock_customer.email = "test@example.com"
        mock_ticket.customer = mock_customer
        
        mock_query = self.db.query.return_value
        mock_query.filter.return_value.count.return_value = 5
        
        self.service._create_satisfaction_survey(mock_ticket)
        
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_create_satisfaction_survey_exception(self):
        """测试创建满意度调查异常"""
        mock_ticket = MagicMock()
        mock_ticket.id = 1
        
        self.db.query.side_effect = Exception("数据库异常")
        
        # 不应抛出异常
        self.service._create_satisfaction_survey(mock_ticket)


if __name__ == '__main__':
    unittest.main()
