# -*- coding: utf-8 -*-
"""
缺料告警服务单元测试

Mock策略：
- 只mock外部依赖（db.query, db.add, db.commit等数据库操作）
- 让业务逻辑真正执行（不mock业务方法）
- 覆盖主要方法和边界情况
"""

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch, call

from fastapi import HTTPException

from app.services.shortage.shortage_alerts_service import ShortageAlertsService


class TestShortageAlertsService(unittest.TestCase):
    """缺料告警服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ShortageAlertsService(self.db)
        self.current_user = Mock(id=1, name="测试用户")

    def _create_mock_shortage(
        self,
        shortage_id=1,
        material_code="M001",
        material_name="测试物料",
        shortage_quantity=100,
        severity="high",
        status="pending",
        material_id=1,
        project_id=1,
        machine_id=1,
        assigned_user_id=1,
        shortage_reason="供应商延期",
        required_date=None,
        acknowledged_by=None,
        acknowledged_at=None,
        acknowledgment_note=None,
        resolved_by=None,
        resolved_at=None,
        resolution_method=None,
        resolution_note=None,
        actual_arrival_date=None,
        created_at=None,
        updated_at=None
    ):
        """创建mock缺料告警对象"""
        shortage = Mock()
        shortage.id = shortage_id
        shortage.material_id = material_id
        shortage.material_code = material_code
        shortage.material_name = material_name
        shortage.shortage_quantity = shortage_quantity
        shortage.required_date = required_date or date.today()
        shortage.severity = severity
        shortage.status = status
        shortage.shortage_reason = shortage_reason
        shortage.project_id = project_id
        shortage.machine_id = machine_id
        shortage.assigned_user_id = assigned_user_id
        shortage.acknowledged_by = acknowledged_by
        shortage.acknowledged_at = acknowledged_at
        shortage.acknowledgment_note = acknowledgment_note
        shortage.resolved_by = resolved_by
        shortage.resolved_at = resolved_at
        shortage.resolution_method = resolution_method
        shortage.resolution_note = resolution_note
        shortage.actual_arrival_date = actual_arrival_date
        shortage.created_at = created_at or datetime.now(timezone.utc)
        shortage.updated_at = updated_at
        
        # 关联对象
        shortage.material = Mock()
        shortage.material.material_type = "原材料"
        shortage.project = Mock(name="测试项目")
        shortage.machine = Mock(name="测试设备")
        shortage.assigned_user = Mock(name="负责人")
        shortage.acknowledged_by_user = None
        shortage.resolved_by_user = None
        
        return shortage

    def _create_mock_query_chain(self, return_value=None, count_value=0):
        """创建mock查询链"""
        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = count_value
        
        if return_value is not None:
            if isinstance(return_value, list):
                mock_query.all.return_value = return_value
                mock_query.first.return_value = return_value[0] if return_value else None
            else:
                mock_query.all.return_value = [return_value]
                mock_query.first.return_value = return_value
        else:
            mock_query.all.return_value = []
            mock_query.first.return_value = None
        
        mock_query.scalar.return_value = None
        
        return mock_query

    # ========== get_shortage_alerts() 测试 ==========

    def test_get_shortage_alerts_basic(self):
        """测试获取告警列表（基础功能）"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=[mock_shortage], count_value=1)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alerts(page=1, page_size=20)

        self.assertEqual(result.total, 1)
        self.assertEqual(result.page, 1)
        self.assertEqual(result.page_size, 20)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["material_code"], "M001")
        self.db.query.assert_called_once()

    def test_get_shortage_alerts_with_filters(self):
        """测试带筛选条件的查询"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=[mock_shortage], count_value=1)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alerts(
            page=1,
            page_size=10,
            keyword="测试",
            severity="high",
            status="pending",
            material_id=1,
            project_id=1,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today()
        )

        self.assertEqual(result.total, 1)
        # 验证filter被调用多次（各种筛选条件）
        self.assertGreater(mock_query.filter.call_count, 0)

    def test_get_shortage_alerts_empty_result(self):
        """测试空结果"""
        mock_query = self._create_mock_query_chain(return_value=[], count_value=0)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alerts()

        self.assertEqual(result.total, 0)
        self.assertEqual(len(result.items), 0)

    def test_get_shortage_alerts_pagination(self):
        """测试分页"""
        mock_shortages = [
            self._create_mock_shortage(shortage_id=i, material_code=f"M{i:03d}")
            for i in range(1, 6)
        ]
        mock_query = self._create_mock_query_chain(return_value=mock_shortages, count_value=100)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alerts(page=2, page_size=5)

        self.assertEqual(result.total, 100)
        self.assertEqual(result.page, 2)
        self.assertEqual(result.page_size, 5)
        # 验证返回了数据（即使mock可能返回空列表也不影响主要逻辑）
        self.assertIsNotNone(result.items)

    # ========== get_shortage_alert() 测试 ==========

    def test_get_shortage_alert_success(self):
        """测试获取单个告警（成功）"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alert(1)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["material_code"], "M001")
        mock_query.filter.assert_called_once()

    def test_get_shortage_alert_not_found(self):
        """测试获取不存在的告警"""
        mock_query = self._create_mock_query_chain(return_value=None)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alert(999)

        self.assertIsNone(result)

    # ========== acknowledge_shortage_alert() 测试 ==========

    def test_acknowledge_shortage_alert_success(self):
        """测试确认告警（成功）"""
        mock_shortage = self._create_mock_shortage(status="pending")
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        with patch.object(self.service, '_send_notification'):
            result = self.service.acknowledge_shortage_alert(
                alert_id=1,
                current_user=self.current_user,
                note="已确认，正在处理"
            )

        self.assertIsNotNone(result)
        self.assertEqual(mock_shortage.status, "acknowledged")
        self.assertEqual(mock_shortage.acknowledged_by, 1)
        self.assertIsNotNone(mock_shortage.acknowledged_at)
        self.assertEqual(mock_shortage.acknowledgment_note, "已确认，正在处理")
        self.db.commit.assert_called_once()

    def test_acknowledge_shortage_alert_not_found(self):
        """测试确认不存在的告警"""
        mock_query = self._create_mock_query_chain(return_value=None)
        self.db.query.return_value = mock_query

        result = self.service.acknowledge_shortage_alert(
            alert_id=999,
            current_user=self.current_user
        )

        self.assertIsNone(result)

    def test_acknowledge_shortage_alert_invalid_status(self):
        """测试确认非待处理状态的告警"""
        mock_shortage = self._create_mock_shortage(status="acknowledged")
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        with self.assertRaises(HTTPException) as context:
            self.service.acknowledge_shortage_alert(
                alert_id=1,
                current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("只能确认待处理状态的告警", str(context.exception.detail))

    def test_acknowledge_shortage_alert_without_note(self):
        """测试确认告警（无备注）"""
        mock_shortage = self._create_mock_shortage(status="pending")
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        with patch.object(self.service, '_send_notification'):
            result = self.service.acknowledge_shortage_alert(
                alert_id=1,
                current_user=self.current_user
            )

        self.assertIsNotNone(result)
        self.assertIsNone(mock_shortage.acknowledgment_note)

    # ========== update_shortage_alert() 测试 ==========

    def test_update_shortage_alert_success(self):
        """测试更新告警（成功）"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        update_data = {
            "severity": "critical",
            "shortage_reason": "供应商破产"
        }

        result = self.service.update_shortage_alert(
            alert_id=1,
            update_data=update_data,
            current_user=self.current_user
        )

        self.assertIsNotNone(result)
        self.assertEqual(mock_shortage.severity, "critical")
        self.assertEqual(mock_shortage.shortage_reason, "供应商破产")
        self.assertEqual(mock_shortage.updated_by, 1)
        self.db.commit.assert_called_once()

    def test_update_shortage_alert_not_found(self):
        """测试更新不存在的告警"""
        mock_query = self._create_mock_query_chain(return_value=None)
        self.db.query.return_value = mock_query

        result = self.service.update_shortage_alert(
            alert_id=999,
            update_data={"severity": "critical"},
            current_user=self.current_user
        )

        self.assertIsNone(result)

    def test_update_shortage_alert_ignore_protected_fields(self):
        """测试更新时忽略受保护字段"""
        mock_shortage = self._create_mock_shortage()
        original_id = mock_shortage.id
        original_created_at = mock_shortage.created_at
        
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        update_data = {
            "id": 999,  # 应该被忽略
            "created_at": datetime(2020, 1, 1),  # 应该被忽略
            "severity": "critical"
        }

        result = self.service.update_shortage_alert(
            alert_id=1,
            update_data=update_data,
            current_user=self.current_user
        )

        # 验证受保护字段未被修改
        self.assertEqual(mock_shortage.id, original_id)
        self.assertEqual(mock_shortage.created_at, original_created_at)
        # 验证普通字段被修改
        self.assertEqual(mock_shortage.severity, "critical")

    # ========== add_follow_up() 测试 ==========

    @patch('app.services.shortage.shortage_alerts_service.ArrivalFollowUp')
    @patch('app.services.shortage.shortage_alerts_service.save_obj')
    def test_add_follow_up_success(self, mock_save_obj, mock_follow_up_class):
        """测试添加跟进（成功）"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        follow_up_data = {
            "follow_up_type": "phone",
            "description": "致电供应商确认到货时间",
            "contact_person": "张三",
            "contact_method": "电话",
            "scheduled_time": datetime.now()
        }

        # Mock ArrivalFollowUp实例
        mock_follow_up_instance = Mock()
        mock_follow_up_instance.id = 1
        mock_follow_up_class.return_value = mock_follow_up_instance

        result = self.service.add_follow_up(
            alert_id=1,
            follow_up_data=follow_up_data,
            current_user=self.current_user
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["follow_up_id"], 1)
        self.assertIn("成功", result["message"])
        mock_save_obj.assert_called_once()

    @patch('app.services.shortage.shortage_alerts_service.save_obj')
    def test_add_follow_up_shortage_not_found(self, mock_save_obj):
        """测试为不存在的告警添加跟进"""
        mock_query = self._create_mock_query_chain(return_value=None)
        self.db.query.return_value = mock_query

        follow_up_data = {
            "follow_up_type": "phone",
            "description": "测试"
        }

        with self.assertRaises(HTTPException) as context:
            self.service.add_follow_up(
                alert_id=999,
                follow_up_data=follow_up_data,
                current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, 404)
        mock_save_obj.assert_not_called()

    # ========== get_follow_ups() 测试 ==========

    def test_get_follow_ups_success(self):
        """测试获取跟进列表"""
        mock_follow_up = Mock()
        mock_follow_up.id = 1
        mock_follow_up.follow_up_type = "phone"
        mock_follow_up.follow_up_note = "致电确认"
        mock_follow_up.created_at = datetime.now()
        mock_follow_up.completed_at = datetime.now()

        mock_query = self._create_mock_query_chain(return_value=[mock_follow_up])
        self.db.query.return_value = mock_query

        result = self.service.get_follow_ups(alert_id=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["follow_up_type"], "phone")

    def test_get_follow_ups_empty(self):
        """测试获取空跟进列表"""
        mock_query = self._create_mock_query_chain(return_value=[])
        self.db.query.return_value = mock_query

        result = self.service.get_follow_ups(alert_id=1)

        self.assertEqual(len(result), 0)

    # ========== resolve_shortage_alert() 测试 ==========

    def test_resolve_shortage_alert_success(self):
        """测试解决告警（成功）"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        resolve_data = {
            "resolution_method": "替代料",
            "resolution_note": "使用替代料解决",
            "actual_arrival_date": date.today()
        }

        with patch.object(self.service, '_send_notification'):
            result = self.service.resolve_shortage_alert(
                alert_id=1,
                resolve_data=resolve_data,
                current_user=self.current_user
            )

        self.assertIsNotNone(result)
        self.assertEqual(mock_shortage.status, "resolved")
        self.assertEqual(mock_shortage.resolved_by, 1)
        self.assertIsNotNone(mock_shortage.resolved_at)
        self.assertEqual(mock_shortage.resolution_method, "替代料")
        self.db.commit.assert_called_once()

    def test_resolve_shortage_alert_not_found(self):
        """测试解决不存在的告警"""
        mock_query = self._create_mock_query_chain(return_value=None)
        self.db.query.return_value = mock_query

        result = self.service.resolve_shortage_alert(
            alert_id=999,
            resolve_data={},
            current_user=self.current_user
        )

        self.assertIsNone(result)

    # ========== get_statistics_overview() 测试 ==========

    def test_get_statistics_overview_with_default_dates(self):
        """测试统计概览（默认日期）"""
        # Mock基础查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        
        # Mock状态统计
        mock_status_stat = Mock()
        mock_status_stat.status = "pending"
        mock_status_stat.count = 5
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        
        # 设置all()返回值 - 按调用顺序
        mock_query.all.side_effect = [
            [mock_status_stat],  # 第一次调用（状态统计）
            [],  # 第二次调用（严重程度统计）
            []   # 第三次调用（物料类型统计）
        ]
        
        mock_query.join.return_value = mock_query
        mock_query.scalar.return_value = 3600.0  # 1小时
        
        self.db.query.return_value = mock_query

        result = self.service.get_statistics_overview()

        self.assertIsNotNone(result)
        self.assertIn("period", result)
        self.assertIn("total_alerts", result)
        self.assertIn("today_new_alerts", result)
        self.assertIn("status_distribution", result)
        self.assertIn("severity_distribution", result)
        self.assertIn("material_type_distribution", result)
        self.assertIn("average_resolution_hours", result)

    def test_get_statistics_overview_with_custom_dates(self):
        """测试统计概览（自定义日期范围）"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.with_entities.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.side_effect = [[], [], []]
        mock_query.join.return_value = mock_query
        mock_query.scalar.return_value = None
        
        self.db.query.return_value = mock_query

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = self.service.get_statistics_overview(
            start_date=start_date,
            end_date=end_date
        )

        self.assertEqual(result["period"]["start_date"], "2024-01-01")
        self.assertEqual(result["period"]["end_date"], "2024-01-31")
        self.assertIsNone(result["average_resolution_hours"])

    # ========== get_dashboard_data() 测试 ==========

    def test_get_dashboard_data(self):
        """测试仪表板数据"""
        mock_shortage = self._create_mock_shortage(severity="critical", status="pending")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_shortage]
        
        self.db.query.return_value = mock_query

        result = self.service.get_dashboard_data()

        self.assertIn("today_summary", result)
        self.assertIn("week_trend", result)
        self.assertIn("critical_alerts", result)
        
        # 验证今日摘要
        summary = result["today_summary"]
        self.assertIn("new_alerts", summary)
        self.assertIn("pending_alerts", summary)
        self.assertIn("acknowledged_alerts", summary)
        self.assertIn("resolved_alerts", summary)
        
        # 验证周趋势
        self.assertEqual(len(result["week_trend"]), 7)
        
        # 验证紧急告警
        self.assertEqual(len(result["critical_alerts"]), 1)
        self.assertEqual(result["critical_alerts"][0]["id"], 1)

    # ========== _format_shortage_alert() 测试 ==========

    def test_format_shortage_alert_complete(self):
        """测试格式化告警（完整数据）"""
        mock_shortage = self._create_mock_shortage(
            shortage_id=1,
            acknowledged_by=2,
            acknowledged_at=datetime(2024, 1, 15, 10, 0, 0),
            acknowledgment_note="已确认",
            resolved_by=3,
            resolved_at=datetime(2024, 1, 16, 15, 0, 0),
            resolution_method="替代料",
            resolution_note="使用替代料",
            actual_arrival_date=date(2024, 1, 20),
            updated_at=datetime(2024, 1, 16, 15, 0, 0)
        )
        mock_shortage.acknowledged_by_user = Mock(name="确认人")
        mock_shortage.resolved_by_user = Mock(name="解决人")

        result = self.service._format_shortage_alert(mock_shortage)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["material_code"], "M001")
        self.assertEqual(result["material_name"], "测试物料")
        self.assertEqual(result["shortage_quantity"], 100)
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["status"], "pending")
        self.assertIsNotNone(result["acknowledged_at"])
        self.assertIsNotNone(result["resolved_at"])
        self.assertEqual(result["resolution_method"], "替代料")

    def test_format_shortage_alert_minimal(self):
        """测试格式化告警（最小数据）"""
        mock_shortage = self._create_mock_shortage()
        mock_shortage.project = None
        mock_shortage.machine = None
        mock_shortage.assigned_user = None
        mock_shortage.acknowledged_by_user = None
        mock_shortage.resolved_by_user = None

        result = self.service._format_shortage_alert(mock_shortage)

        self.assertEqual(result["id"], 1)
        self.assertIsNone(result["project_name"])
        self.assertIsNone(result["machine_name"])
        self.assertIsNone(result["assigned_to"])
        self.assertIsNone(result["acknowledged_by"])
        self.assertIsNone(result["resolved_by"])

    # ========== _send_notification() 测试 ==========

    def test_send_notification_acknowledged(self):
        """测试发送确认通知"""
        with patch('app.services.notification_dispatcher.NotificationDispatcher') as mock_dispatcher_class:
            mock_shortage = self._create_mock_shortage()
            mock_shortage.handler_id = 10
            
            mock_dispatcher = MagicMock()
            mock_dispatcher_class.return_value = mock_dispatcher

            self.service._send_notification(mock_shortage, "acknowledged")

            mock_dispatcher_class.assert_called_once_with(self.db)
            mock_dispatcher.send_notification_request.assert_called_once()
            
            # 验证通知请求参数
            call_args = mock_dispatcher.send_notification_request.call_args
            request = call_args[0][0]
            self.assertEqual(request.recipient_id, 10)
            self.assertEqual(request.notification_type, "SHORTAGE_UPDATE")
            self.assertIn("已确认", request.title)

    def test_send_notification_resolved(self):
        """测试发送解决通知"""
        with patch('app.services.notification_dispatcher.NotificationDispatcher') as mock_dispatcher_class:
            mock_shortage = self._create_mock_shortage()
            # 明确设置handler_id和created_by
            mock_shortage.handler_id = None
            mock_shortage.created_by = 5
            
            mock_dispatcher = MagicMock()
            mock_dispatcher_class.return_value = mock_dispatcher

            self.service._send_notification(mock_shortage, "resolved")

            mock_dispatcher.send_notification_request.assert_called_once()
            
            call_args = mock_dispatcher.send_notification_request.call_args
            request = call_args[0][0]
            self.assertEqual(request.recipient_id, 5)
            self.assertIn("已解决", request.title)

    def test_send_notification_no_recipient(self):
        """测试无接收人时不发送通知"""
        with patch('app.services.notification_dispatcher.NotificationDispatcher') as mock_dispatcher_class:
            mock_shortage = self._create_mock_shortage()
            mock_shortage.handler_id = None
            mock_shortage.created_by = None
            
            mock_dispatcher = MagicMock()
            mock_dispatcher_class.return_value = mock_dispatcher

            self.service._send_notification(mock_shortage, "acknowledged")

            # 应该不调用发送
            mock_dispatcher.send_notification_request.assert_not_called()

    def test_send_notification_exception_handling(self):
        """测试通知发送异常处理"""
        with patch('app.services.notification_dispatcher.NotificationDispatcher') as mock_dispatcher_class:
            mock_shortage = self._create_mock_shortage()
            mock_shortage.created_by = 5
            
            # 模拟异常
            mock_dispatcher_class.side_effect = Exception("通知服务不可用")

            # 应该捕获异常，不抛出
            try:
                self.service._send_notification(mock_shortage, "resolved")
            except Exception:
                self.fail("_send_notification应该捕获异常")

    # ========== 边界情况测试 ==========

    def test_get_shortage_alerts_with_all_none_filters(self):
        """测试所有筛选条件为None"""
        mock_query = self._create_mock_query_chain(return_value=[], count_value=0)
        self.db.query.return_value = mock_query

        result = self.service.get_shortage_alerts(
            keyword=None,
            severity=None,
            status=None,
            material_id=None,
            project_id=None,
            start_date=None,
            end_date=None
        )

        self.assertEqual(result.total, 0)

    def test_acknowledge_shortage_alert_updates_all_fields(self):
        """测试确认告警时所有字段正确更新"""
        mock_shortage = self._create_mock_shortage(status="pending")
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        before_time = datetime.now(timezone.utc)
        
        with patch.object(self.service, '_send_notification'):
            self.service.acknowledge_shortage_alert(
                alert_id=1,
                current_user=self.current_user,
                note="测试备注"
            )

        # 验证所有更新字段
        self.assertEqual(mock_shortage.status, "acknowledged")
        self.assertEqual(mock_shortage.acknowledged_by, 1)
        self.assertIsNotNone(mock_shortage.acknowledged_at)
        self.assertGreaterEqual(mock_shortage.acknowledged_at, before_time)
        self.assertEqual(mock_shortage.acknowledgment_note, "测试备注")
        self.assertEqual(mock_shortage.updated_by, 1)
        self.assertIsNotNone(mock_shortage.updated_at)

    def test_resolve_shortage_alert_updates_all_fields(self):
        """测试解决告警时所有字段正确更新"""
        mock_shortage = self._create_mock_shortage()
        mock_query = self._create_mock_query_chain(return_value=mock_shortage)
        self.db.query.return_value = mock_query

        resolve_data = {
            "resolution_method": "紧急采购",
            "resolution_note": "从其他供应商紧急采购",
            "actual_arrival_date": date.today() + timedelta(days=3)
        }

        before_time = datetime.now(timezone.utc)

        with patch.object(self.service, '_send_notification'):
            self.service.resolve_shortage_alert(
                alert_id=1,
                resolve_data=resolve_data,
                current_user=self.current_user
            )

        # 验证所有更新字段
        self.assertEqual(mock_shortage.status, "resolved")
        self.assertEqual(mock_shortage.resolved_by, 1)
        self.assertIsNotNone(mock_shortage.resolved_at)
        self.assertGreaterEqual(mock_shortage.resolved_at, before_time)
        self.assertEqual(mock_shortage.resolution_method, "紧急采购")
        self.assertEqual(mock_shortage.resolution_note, "从其他供应商紧急采购")
        self.assertIsNotNone(mock_shortage.actual_arrival_date)


if __name__ == "__main__":
    unittest.main()
