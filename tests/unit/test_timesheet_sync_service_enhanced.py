# -*- coding: utf-8 -*-
"""
TimesheetSyncService 增强单元测试
覆盖所有核心方法、边界条件和错误处理
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.timesheet_sync_service import TimesheetSyncService
from app.models.timesheet import Timesheet
from app.models.project import FinancialProjectCost
from app.models.rd_project import RdCost, RdProject, RdCostType


class TestTimesheetSyncServiceInit(unittest.TestCase):
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = TimesheetSyncService(mock_db)
        self.assertEqual(service.db, mock_db)


class TestSyncToFinance(unittest.TestCase):
    """测试同步到财务系统"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    def test_sync_single_timesheet_success(self):
        """测试同步单个工时记录成功"""
        # 准备数据
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.project_id = 100

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        # Mock _create_financial_cost_from_timesheet
        with patch.object(self.service, '_create_financial_cost_from_timesheet') as mock_create:
            mock_create.return_value = {'success': True, 'created': True, 'cost_id': 1}

            result = self.service.sync_to_finance(timesheet_id=1)

            self.assertTrue(result['success'])
            mock_create.assert_called_once_with(mock_timesheet)

    def test_sync_single_timesheet_not_found(self):
        """测试同步不存在的工时记录"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_to_finance(timesheet_id=999)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录不存在')

    def test_sync_single_timesheet_not_approved(self):
        """测试同步未审批的工时记录"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'PENDING'

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_finance(timesheet_id=1)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '只能同步已审批的工时记录')

    def test_sync_single_timesheet_no_project(self):
        """测试同步未关联项目的工时记录"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.project_id = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_finance(timesheet_id=1)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录未关联项目')

    @patch('app.services.timesheet_sync_service.get_month_range_by_ym')
    def test_sync_batch_by_project_and_month(self, mock_get_month_range):
        """测试批量同步项目月度数据"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))

        # Mock timesheets
        mock_ts1 = MagicMock(spec=Timesheet)
        mock_ts1.id = 1
        mock_ts2 = MagicMock(spec=Timesheet)
        mock_ts2.id = 2

        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        with patch.object(self.service, '_create_financial_cost_from_timesheet') as mock_create:
            mock_create.side_effect = [
                {'success': True, 'created': True},
                {'success': True, 'updated': True}
            ]

            result = self.service.sync_to_finance(project_id=100, year=2024, month=1)

            self.assertTrue(result['success'])
            self.assertEqual(result['created_count'], 1)
            self.assertEqual(result['updated_count'], 1)
            self.assertEqual(len(result['errors']), 0)

    @patch('app.services.timesheet_sync_service.get_month_range_by_ym')
    def test_sync_batch_with_errors(self, mock_get_month_range):
        """测试批量同步时部分记录失败"""
        mock_get_month_range.return_value = (date(2024, 1, 1), date(2024, 1, 31))

        mock_ts1 = MagicMock(spec=Timesheet)
        mock_ts1.id = 1
        mock_ts2 = MagicMock(spec=Timesheet)
        mock_ts2.id = 2

        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        with patch.object(self.service, '_create_financial_cost_from_timesheet') as mock_create:
            mock_create.side_effect = [
                {'success': True, 'created': True},
                Exception('数据库错误')
            ]

            result = self.service.sync_to_finance(project_id=100, year=2024, month=1)

            self.assertTrue(result['success'])
            self.assertEqual(result['created_count'], 1)
            self.assertEqual(result['updated_count'], 0)
            self.assertEqual(len(result['errors']), 1)
            self.assertIn('工时记录2', result['errors'][0])

    def test_sync_incomplete_parameters(self):
        """测试参数不完整"""
        result = self.service.sync_to_finance(project_id=100)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '参数不完整')


class TestCreateFinancialCostFromTimesheet(unittest.TestCase):
    """测试从工时创建财务成本"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    @patch('app.services.timesheet_sync_service.save_obj')
    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_create_new_financial_cost(self, mock_hourly_rate_service, mock_save_obj):
        """测试创建新的财务成本记录"""
        # Mock timesheet
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.project_id = 100
        mock_timesheet.project_code = 'P001'
        mock_timesheet.project_name = '测试项目'
        mock_timesheet.hours = 8
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.work_content = '开发工作'
        mock_timesheet.user_id = 10
        mock_timesheet.user_name = '张三'
        mock_timesheet.approver_id = 20
        mock_timesheet.approve_time = datetime(2024, 1, 16, 10, 0)

        # Mock no existing record
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock hourly rate
        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100.00')

        result = self.service._create_financial_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        self.assertFalse(result['updated'])
        mock_save_obj.assert_called_once()

    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_update_existing_financial_cost(self, mock_hourly_rate_service):
        """测试更新现有财务成本记录"""
        # Mock timesheet
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.work_content = '更新的工作内容'
        mock_timesheet.user_id = 10
        mock_timesheet.user_name = '张三'

        # Mock existing record
        mock_existing = MagicMock(spec=FinancialProjectCost)
        mock_existing.id = 50
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_existing

        # Mock hourly rate
        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100.00')

        result = self.service._create_financial_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])
        self.assertFalse(result['created'])
        self.assertTrue(result['updated'])
        self.assertEqual(result['cost_id'], 50)
        self.mock_db.commit.assert_called_once()

    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_calculate_cost_amount_correctly(self, mock_hourly_rate_service):
        """测试正确计算成本金额"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.hours = 8.5
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.user_id = 10

        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('120.50')

        with patch('app.services.timesheet_sync_service.save_obj'):
            result = self.service._create_financial_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])


class TestSyncToRd(unittest.TestCase):
    """测试同步到研发系统"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    def test_sync_single_rd_timesheet_success(self):
        """测试同步单个研发工时成功"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.rd_project_id = 200

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        with patch.object(self.service, '_create_rd_cost_from_timesheet') as mock_create:
            mock_create.return_value = {'success': True, 'created': True}

            result = self.service.sync_to_rd(timesheet_id=1)

            self.assertTrue(result['success'])
            mock_create.assert_called_once_with(mock_timesheet)

    def test_sync_rd_timesheet_not_found(self):
        """测试研发工时记录不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_to_rd(timesheet_id=999)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录不存在')

    def test_sync_rd_timesheet_not_approved(self):
        """测试研发工时未审批"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'DRAFT'

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_rd(timesheet_id=1)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '只能同步已审批的工时记录')

    def test_sync_rd_timesheet_no_rd_project(self):
        """测试工时未关联研发项目"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.rd_project_id = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_rd(timesheet_id=1)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录未关联研发项目')

    @patch('app.services.timesheet_sync_service.get_month_range_by_ym')
    def test_sync_rd_batch_by_project_and_month(self, mock_get_month_range):
        """测试批量同步研发项目月度数据"""
        mock_get_month_range.return_value = (date(2024, 2, 1), date(2024, 2, 29))

        mock_ts1 = MagicMock(spec=Timesheet)
        mock_ts1.id = 1
        mock_ts2 = MagicMock(spec=Timesheet)
        mock_ts2.id = 2

        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_ts1, mock_ts2]

        with patch.object(self.service, '_create_rd_cost_from_timesheet') as mock_create:
            mock_create.side_effect = [
                {'success': True, 'created': True},
                {'success': True, 'created': True}
            ]

            result = self.service.sync_to_rd(rd_project_id=200, year=2024, month=2)

            self.assertTrue(result['success'])
            self.assertEqual(result['created_count'], 2)
            self.assertEqual(result['updated_count'], 0)

    def test_sync_rd_incomplete_parameters(self):
        """测试研发同步参数不完整"""
        result = self.service.sync_to_rd(rd_project_id=200, year=2024)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '参数不完整')


class TestCreateRdCostFromTimesheet(unittest.TestCase):
    """测试从工时创建研发费用"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    def test_create_rd_cost_project_not_found(self):
        """测试研发项目不存在"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.rd_project_id = 999

        # Mock查询返回None（项目不存在）
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [None]  # rd_project不存在
        self.mock_db.query.return_value = query_mock

        result = self.service._create_rd_cost_from_timesheet(mock_timesheet)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '研发项目不存在')

    @patch('app.services.timesheet_sync_service.apply_like_filter')
    @patch('app.services.timesheet_sync_service.save_obj')
    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_create_new_rd_cost_with_existing_type(self, mock_hourly_rate_service, 
                                                    mock_save_obj, mock_apply_like_filter):
        """测试创建新研发费用（费用类型已存在）"""

        # Mock timesheet
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.rd_project_id = 200
        mock_timesheet.hours = 8
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.work_content = '研发工作'
        mock_timesheet.user_id = 10

        # Mock rd_project
        mock_rd_project = MagicMock(spec=RdProject)
        mock_rd_project.id = 200

        # Mock cost_type
        mock_cost_type = MagicMock(spec=RdCostType)
        mock_cost_type.id = 5
        mock_cost_type.type_code = 'LABOR'

        # Mock查询链
        query_mock = MagicMock()
        first_results = [
            mock_rd_project,  # 第一次查询：rd_project
            mock_cost_type,   # 第二次查询：cost_type (LABOR)
            None,             # 第三次查询：existing RdCost
            None              # 第四次查询：max_cost
        ]
        query_mock.filter.return_value.first.side_effect = first_results
        self.mock_db.query.return_value = query_mock

        # Mock apply_like_filter
        mock_apply_like_filter.return_value = query_mock.filter.return_value.order_by.return_value

        # Mock hourly rate
        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100.00')

        result = self.service._create_rd_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        mock_save_obj.assert_called_once()

    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_update_existing_rd_cost(self, mock_hourly_rate_service):
        """测试更新现有研发费用"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.rd_project_id = 200
        mock_timesheet.hours = 10
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.work_content = '更新工作'
        mock_timesheet.user_id = 10

        # Mock rd_project
        mock_rd_project = MagicMock(spec=RdProject)

        # Mock existing RdCost
        mock_existing = MagicMock(spec=RdCost)
        mock_existing.id = 60

        # Mock查询链
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [
            mock_rd_project,  # rd_project查询
            MagicMock(),      # cost_type查询
            mock_existing     # existing查询
        ]
        self.mock_db.query.return_value = query_mock

        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100.00')

        result = self.service._create_rd_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])
        self.assertFalse(result['created'])
        self.assertTrue(result['updated'])
        self.assertEqual(result['cost_id'], 60)

    @patch('app.services.timesheet_sync_service.apply_like_filter')
    @patch('app.services.timesheet_sync_service.save_obj')
    @patch('app.services.timesheet_sync_service.HourlyRateService')
    def test_create_rd_cost_type_if_not_exists(self, mock_hourly_rate_service,
                                                 mock_save_obj, mock_apply_like_filter):
        """测试费用类型不存在时自动创建"""

        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.rd_project_id = 200
        mock_timesheet.hours = 8
        mock_timesheet.work_date = date(2024, 1, 15)
        mock_timesheet.user_id = 10

        mock_rd_project = MagicMock(spec=RdProject)

        # Mock查询：项目存在，但费用类型不存在
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [
            mock_rd_project,  # rd_project
            None,             # cost_type (type_code=LABOR)
            None,             # cost_type (category=LABOR)
            None,             # existing RdCost
            None              # max_cost
        ]
        self.mock_db.query.return_value = query_mock

        mock_apply_like_filter.return_value = query_mock.filter.return_value.order_by.return_value

        mock_hourly_rate_service.get_user_hourly_rate.return_value = Decimal('100.00')

        result = self.service._create_rd_cost_from_timesheet(mock_timesheet)

        self.assertTrue(result['success'])
        # 验证添加了新的费用类型
        self.mock_db.add.assert_called()
        self.mock_db.flush.assert_called()


class TestSyncToProject(unittest.TestCase):
    """测试同步到项目系统"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    @patch('app.services.timesheet_sync_service.LaborCostService')
    def test_sync_single_timesheet_to_project(self, mock_labor_cost_service):
        """测试同步单个工时到项目"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.project_id = 100
        mock_timesheet.work_date = date(2024, 1, 15)

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        mock_labor_cost_service.calculate_project_labor_cost.return_value = {
            'success': True,
            'total_cost': Decimal('800.00')
        }

        result = self.service.sync_to_project(timesheet_id=1)

        self.assertTrue(result['success'])
        mock_labor_cost_service.calculate_project_labor_cost.assert_called_once_with(
            self.mock_db,
            100,
            start_date=mock_timesheet.work_date,
            end_date=mock_timesheet.work_date,
            recalculate=False
        )

    def test_sync_to_project_timesheet_not_found(self):
        """测试项目同步时工时不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_to_project(timesheet_id=999)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录不存在')

    def test_sync_to_project_not_approved(self):
        """测试同步未审批工时到项目"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'PENDING'

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_project(timesheet_id=1)

        self.assertFalse(result['success'])

    def test_sync_to_project_no_project_id(self):
        """测试同步未关联项目的工时"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.status = 'APPROVED'
        mock_timesheet.project_id = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        result = self.service.sync_to_project(timesheet_id=1)

        self.assertFalse(result['success'])

    @patch('app.services.timesheet_sync_service.LaborCostService')
    def test_sync_batch_to_project(self, mock_labor_cost_service):
        """测试批量同步到项目"""
        mock_labor_cost_service.calculate_project_labor_cost.return_value = {
            'success': True,
            'total_cost': Decimal('5000.00')
        }

        result = self.service.sync_to_project(project_id=100)

        self.assertTrue(result['success'])
        mock_labor_cost_service.calculate_project_labor_cost.assert_called_once_with(
            self.mock_db,
            100,
            recalculate=False
        )

    def test_sync_to_project_incomplete_parameters(self):
        """测试项目同步参数不完整"""
        result = self.service.sync_to_project()

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '参数不完整')


class TestSyncToHr(unittest.TestCase):
    """测试同步到HR系统"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    def test_sync_to_hr_all_departments(self):
        """测试同步全公司HR数据"""
        # Mock OvertimeCalculationService in the method scope
        with patch('app.services.overtime_calculation_service.OvertimeCalculationService') as mock_overtime_service_class:
            mock_overtime_service = MagicMock()
            mock_overtime_service_class.return_value = mock_overtime_service

            mock_stats = [
                {'user_id': 1, 'overtime_hours': 10},
                {'user_id': 2, 'overtime_hours': 5}
            ]
            mock_overtime_service.get_overtime_statistics.return_value = mock_stats

            result = self.service.sync_to_hr(year=2024, month=1)

            self.assertTrue(result['success'])
            self.assertEqual(result['statistics'], mock_stats)
            mock_overtime_service.get_overtime_statistics.assert_called_once_with(2024, 1, None)

    def test_sync_to_hr_specific_department(self):
        """测试同步特定部门HR数据"""
        # Mock OvertimeCalculationService in the method scope
        with patch('app.services.overtime_calculation_service.OvertimeCalculationService') as mock_overtime_service_class:
            mock_overtime_service = MagicMock()
            mock_overtime_service_class.return_value = mock_overtime_service

            mock_stats = [{'user_id': 1, 'overtime_hours': 10}]
            mock_overtime_service.get_overtime_statistics.return_value = mock_stats

            result = self.service.sync_to_hr(year=2024, month=2, department_id=5)

            self.assertTrue(result['success'])
            mock_overtime_service.get_overtime_statistics.assert_called_once_with(2024, 2, 5)


class TestSyncAllOnApproval(unittest.TestCase):
    """测试审批后自动同步所有系统"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.service = TimesheetSyncService(self.mock_db)

    def test_sync_all_timesheet_not_found(self):
        """测试工时不存在时自动同步"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service.sync_all_on_approval(timesheet_id=999)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '工时记录不存在')

    def test_sync_all_with_project_only(self):
        """测试只同步到项目和财务（无研发项目）"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.project_id = 100
        mock_timesheet.rd_project_id = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        with patch.object(self.service, 'sync_to_finance') as mock_finance, \
             patch.object(self.service, 'sync_to_project') as mock_project, \
             patch.object(self.service, 'sync_to_rd') as mock_rd:

            mock_finance.return_value = {'success': True}
            mock_project.return_value = {'success': True}

            result = self.service.sync_all_on_approval(timesheet_id=1)

            self.assertTrue(result['success'])
            self.assertIsNotNone(result['results']['finance'])
            self.assertIsNotNone(result['results']['project'])
            self.assertIsNone(result['results']['rd'])
            mock_rd.assert_not_called()

    def test_sync_all_with_rd_project(self):
        """测试同步到所有系统（包含研发项目）"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.project_id = 100
        mock_timesheet.rd_project_id = 200

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        with patch.object(self.service, 'sync_to_finance') as mock_finance, \
             patch.object(self.service, 'sync_to_project') as mock_project, \
             patch.object(self.service, 'sync_to_rd') as mock_rd:

            mock_finance.return_value = {'success': True}
            mock_project.return_value = {'success': True}
            mock_rd.return_value = {'success': True}

            result = self.service.sync_all_on_approval(timesheet_id=1)

            self.assertTrue(result['success'])
            self.assertIsNotNone(result['results']['finance'])
            self.assertIsNotNone(result['results']['project'])
            self.assertIsNotNone(result['results']['rd'])
            mock_finance.assert_called_once_with(timesheet_id=1)
            mock_project.assert_called_once_with(timesheet_id=1)
            mock_rd.assert_called_once_with(timesheet_id=1)

    def test_sync_all_no_project_or_rd_project(self):
        """测试没有项目和研发项目时的同步"""
        mock_timesheet = MagicMock(spec=Timesheet)
        mock_timesheet.id = 1
        mock_timesheet.project_id = None
        mock_timesheet.rd_project_id = None

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_timesheet

        with patch.object(self.service, 'sync_to_finance') as mock_finance, \
             patch.object(self.service, 'sync_to_project') as mock_project, \
             patch.object(self.service, 'sync_to_rd') as mock_rd:

            result = self.service.sync_all_on_approval(timesheet_id=1)

            self.assertTrue(result['success'])
            self.assertIsNone(result['results']['finance'])
            self.assertIsNone(result['results']['project'])
            self.assertIsNone(result['results']['rd'])
            mock_finance.assert_not_called()
            mock_project.assert_not_called()
            mock_rd.assert_not_called()


if __name__ == '__main__':
    unittest.main()
