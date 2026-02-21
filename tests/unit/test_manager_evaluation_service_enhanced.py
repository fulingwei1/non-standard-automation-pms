# -*- coding: utf-8 -*-
"""
部门经理评价服务增强单元测试

测试覆盖：
- 权限检查（多场景）
- 绩效调整（综合得分、排名、等级计算）
- 调整历史记录（详细信息、分页）
- 评价任务获取（部门过滤、周期过滤）
- 评价提交（创建、更新、验证）
- 边界条件和异常处理
"""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, call

from app.services.manager_evaluation_service import ManagerEvaluationService


class TestManagerEvaluationService(unittest.TestCase):
    """部门经理评价服务测试基类"""

    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.service = ManagerEvaluationService(self.db)

    def tearDown(self):
        """测试后置清理"""
        self.db.reset_mock()


class TestInitialization(TestManagerEvaluationService):
    """测试初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        self.assertIs(self.service.db, self.db)

    def test_init_with_custom_session(self):
        """测试自定义Session初始化"""
        custom_db = MagicMock()
        service = ManagerEvaluationService(custom_db)
        self.assertIs(service.db, custom_db)


class TestCheckManagerPermission(TestManagerEvaluationService):
    """测试权限检查"""

    def test_check_permission_success(self):
        """测试权限检查成功"""
        # Mock数据
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        department = Mock()
        department.id = 10
        department.manager_id = 100
        department.is_active = True

        engineer = Mock()
        engineer.id = 2
        engineer.employee_id = 200

        employee = Mock()
        employee.id = 200
        employee.department_id = 10

        # 配置查询链
        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,  # 第一次查询manager
            department,  # 第二次查询department
            engineer,  # 第三次查询engineer
            employee  # 第四次查询employee
        ]

        result = self.service.check_manager_permission(1, 2)
        self.assertTrue(result)

    def test_check_permission_manager_not_found(self):
        """测试经理不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.check_manager_permission(999, 2)
        self.assertFalse(result)

    def test_check_permission_not_department_manager(self):
        """测试不是部门经理"""
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,  # 查询manager成功
            None  # 查询department失败
        ]

        result = self.service.check_manager_permission(1, 2)
        self.assertFalse(result)

    def test_check_permission_engineer_not_found(self):
        """测试工程师不存在"""
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        department = Mock()
        department.id = 10
        department.manager_id = 100
        department.is_active = True

        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,
            department,
            None  # engineer不存在
        ]

        result = self.service.check_manager_permission(1, 999)
        self.assertFalse(result)

    def test_check_permission_engineer_no_employee_id(self):
        """测试工程师没有employee_id"""
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        department = Mock()
        department.id = 10
        department.manager_id = 100
        department.is_active = True

        engineer = Mock()
        engineer.id = 2
        engineer.employee_id = None

        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,
            department,
            engineer
        ]

        result = self.service.check_manager_permission(1, 2)
        self.assertFalse(result)

    def test_check_permission_different_department(self):
        """测试工程师在不同部门"""
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        department = Mock()
        department.id = 10
        department.manager_id = 100
        department.is_active = True

        engineer = Mock()
        engineer.id = 2
        engineer.employee_id = 200

        employee = Mock()
        employee.id = 200
        employee.department_id = 99  # 不同部门

        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,
            department,
            engineer,
            employee
        ]

        result = self.service.check_manager_permission(1, 2)
        self.assertFalse(result)


class TestCalculateLevel(TestManagerEvaluationService):
    """测试等级计算"""

    def test_calculate_level_s(self):
        """测试S级（>=85分）"""
        self.assertEqual(self.service._calculate_level(Decimal('85')), 'S')
        self.assertEqual(self.service._calculate_level(Decimal('90')), 'S')
        self.assertEqual(self.service._calculate_level(Decimal('100')), 'S')

    def test_calculate_level_a(self):
        """测试A级（70-84分）"""
        self.assertEqual(self.service._calculate_level(Decimal('70')), 'A')
        self.assertEqual(self.service._calculate_level(Decimal('75')), 'A')
        self.assertEqual(self.service._calculate_level(Decimal('84')), 'A')

    def test_calculate_level_b(self):
        """测试B级（60-69分）"""
        self.assertEqual(self.service._calculate_level(Decimal('60')), 'B')
        self.assertEqual(self.service._calculate_level(Decimal('65')), 'B')
        self.assertEqual(self.service._calculate_level(Decimal('69')), 'B')

    def test_calculate_level_c(self):
        """测试C级（40-59分）"""
        self.assertEqual(self.service._calculate_level(Decimal('40')), 'C')
        self.assertEqual(self.service._calculate_level(Decimal('50')), 'C')
        self.assertEqual(self.service._calculate_level(Decimal('59')), 'C')

    def test_calculate_level_d(self):
        """测试D级（<40分）"""
        self.assertEqual(self.service._calculate_level(Decimal('0')), 'D')
        self.assertEqual(self.service._calculate_level(Decimal('30')), 'D')
        self.assertEqual(self.service._calculate_level(Decimal('39')), 'D')

    def test_calculate_level_boundary(self):
        """测试边界值"""
        self.assertEqual(self.service._calculate_level(Decimal('84.9')), 'A')
        self.assertEqual(self.service._calculate_level(Decimal('85.0')), 'S')
        self.assertEqual(self.service._calculate_level(Decimal('69.9')), 'B')
        self.assertEqual(self.service._calculate_level(Decimal('70.0')), 'A')


class TestAdjustPerformance(TestManagerEvaluationService):
    """测试绩效调整"""

    def setUp(self):
        """测试前置设置"""
        super().setUp()
        # Mock check_manager_permission
        self.patcher = patch.object(
            self.service, 'check_manager_permission', return_value=True
        )
        self.mock_permission = self.patcher.start()

    def tearDown(self):
        """测试后置清理"""
        self.patcher.stop()
        super().tearDown()

    def test_adjust_performance_empty_reason(self):
        """测试调整理由为空"""
        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(1, 1, adjustment_reason="")
        self.assertIn("调整理由不能为空", str(context.exception))

    def test_adjust_performance_short_reason(self):
        """测试调整理由过短（<10字符）"""
        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(1, 1, adjustment_reason="太短了")
        self.assertIn("至少需要10个字符", str(context.exception))

    def test_adjust_performance_whitespace_reason(self):
        """测试调整理由只有空白字符"""
        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(1, 1, adjustment_reason="   ")
        self.assertIn("调整理由不能为空", str(context.exception))

    def test_adjust_performance_result_not_found(self):
        """测试绩效结果不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(
                999, 1, adjustment_reason="有效的调整理由大于十个字符"
            )
        self.assertIn("绩效结果不存在", str(context.exception))

    def test_adjust_performance_no_permission(self):
        """测试无权限调整"""
        self.mock_permission.return_value = False

        result = Mock()
        result.id = 1
        result.user_id = 2
        self.db.query.return_value.filter.return_value.first.return_value = result

        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(
                1, 1, adjustment_reason="有效的调整理由大于十个字符"
            )
        self.assertIn("无权限调整该工程师的绩效", str(context.exception))

    def test_adjust_performance_manager_not_found(self):
        """测试部门经理不存在"""
        result = Mock()
        result.id = 1
        result.user_id = 2

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,  # 绩效结果查询成功
            None  # 经理查询失败
        ]

        with self.assertRaises(ValueError) as context:
            self.service.adjust_performance(
                1, 999, adjustment_reason="有效的调整理由大于十个字符"
            )
        self.assertIn("部门经理不存在", str(context.exception))

    @patch('app.services.manager_evaluation_service.save_obj')
    def test_adjust_performance_first_time_success(self, mock_save):
        """测试首次调整成功"""
        result = Mock()
        result.id = 1
        result.user_id = 2
        result.is_adjusted = False
        result.total_score = Decimal('75')
        result.dept_rank = 5
        result.company_rank = 20
        result.level = 'A'

        manager = Mock()
        manager.id = 1
        manager.name = "经理张三"
        manager.username = "zhang3"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            manager
        ]

        new_result = self.service.adjust_performance(
            result_id=1,
            manager_id=1,
            new_total_score=Decimal('88'),
            new_dept_rank=3,
            new_company_rank=10,
            adjustment_reason="表现优异，工作态度积极，调整得分"
        )

        # 验证原始值保存
        self.assertEqual(new_result.original_total_score, Decimal('75'))
        self.assertEqual(new_result.original_dept_rank, 5)
        self.assertEqual(new_result.original_company_rank, 20)

        # 验证调整后的值
        self.assertEqual(new_result.adjusted_total_score, Decimal('88'))
        self.assertEqual(new_result.total_score, Decimal('88'))
        self.assertEqual(new_result.adjusted_dept_rank, 3)
        self.assertEqual(new_result.dept_rank, 3)
        self.assertEqual(new_result.adjusted_company_rank, 10)
        self.assertEqual(new_result.company_rank, 10)
        self.assertEqual(new_result.level, 'S')  # 88分应该是S级
        self.assertTrue(new_result.is_adjusted)

    @patch('app.services.manager_evaluation_service.save_obj')
    def test_adjust_performance_already_adjusted(self, mock_save):
        """测试已调整过的绩效再次调整"""
        result = Mock()
        result.id = 1
        result.user_id = 2
        result.is_adjusted = True
        result.original_total_score = Decimal('75')
        result.total_score = Decimal('80')
        result.dept_rank = 4
        result.company_rank = 15

        manager = Mock()
        manager.id = 1
        manager.name = "经理李四"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            manager
        ]

        new_result = self.service.adjust_performance(
            result_id=1,
            manager_id=1,
            new_total_score=Decimal('85'),
            adjustment_reason="二次调整，进一步认可工作表现"
        )

        # 原始值不应该被覆盖
        self.assertEqual(new_result.original_total_score, Decimal('75'))
        self.assertEqual(new_result.total_score, Decimal('85'))

    @patch('app.services.manager_evaluation_service.save_obj')
    def test_adjust_performance_only_score(self, mock_save):
        """测试只调整得分"""
        result = Mock()
        result.id = 1
        result.user_id = 2
        result.is_adjusted = False
        result.total_score = Decimal('60')
        result.dept_rank = 10
        result.company_rank = 50

        manager = Mock()
        manager.id = 1
        manager.name = "经理王五"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            manager
        ]

        new_result = self.service.adjust_performance(
            result_id=1,
            manager_id=1,
            new_total_score=Decimal('72'),
            adjustment_reason="项目贡献度评估后上调分数"
        )

        self.assertEqual(new_result.total_score, Decimal('72'))
        self.assertEqual(new_result.dept_rank, 10)  # 排名不变
        self.assertEqual(new_result.company_rank, 50)  # 排名不变
        self.assertEqual(new_result.level, 'A')

    @patch('app.services.manager_evaluation_service.save_obj')
    def test_adjust_performance_only_rank(self, mock_save):
        """测试只调整排名"""
        result = Mock()
        result.id = 1
        result.user_id = 2
        result.is_adjusted = False
        result.total_score = Decimal('78')
        result.dept_rank = 8
        result.company_rank = 40
        result.level = 'A'

        manager = Mock()
        manager.id = 1
        manager.name = "经理赵六"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            manager
        ]

        new_result = self.service.adjust_performance(
            result_id=1,
            manager_id=1,
            new_dept_rank=5,
            new_company_rank=25,
            adjustment_reason="综合考虑团队贡献调整排名"
        )

        self.assertEqual(new_result.total_score, Decimal('78'))  # 得分不变
        self.assertEqual(new_result.dept_rank, 5)
        self.assertEqual(new_result.company_rank, 25)


class TestGetAdjustmentHistory(TestManagerEvaluationService):
    """测试获取调整历史"""

    def test_get_adjustment_history_empty(self):
        """测试空历史记录"""
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        history = self.service.get_adjustment_history(1)
        self.assertEqual(history, [])

    def test_get_adjustment_history_single_record(self):
        """测试单条历史记录"""
        mock_history = Mock()
        mock_history.id = 1
        mock_history.result_id = 1
        mock_history.original_total_score = Decimal('75')
        mock_history.original_dept_rank = 5
        mock_history.original_company_rank = 20
        mock_history.original_level = 'A'
        mock_history.adjusted_total_score = Decimal('88')
        mock_history.adjusted_dept_rank = 3
        mock_history.adjusted_company_rank = 10
        mock_history.adjusted_level = 'S'
        mock_history.adjustment_reason = "表现优异调整"
        mock_history.adjusted_by = 1
        mock_history.adjusted_by_name = "经理张三"
        mock_history.adjusted_at = datetime(2024, 1, 15, 10, 30, 0)

        mock_adjuster = Mock()
        mock_adjuster.name = "经理张三"

        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_history]
        self.db.query.return_value.filter.return_value.first.return_value = mock_adjuster

        history = self.service.get_adjustment_history(1)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['id'], 1)
        self.assertEqual(history[0]['original_total_score'], 75.0)
        self.assertEqual(history[0]['adjusted_total_score'], 88.0)
        self.assertEqual(history[0]['score_change'], 13.0)
        self.assertEqual(history[0]['rank_change']['dept'], -2)
        self.assertEqual(history[0]['rank_change']['company'], -10)

    def test_get_adjustment_history_multiple_records(self):
        """测试多条历史记录（按时间倒序）"""
        mock_history1 = Mock()
        mock_history1.id = 2
        mock_history1.result_id = 1
        mock_history1.original_total_score = Decimal('80')
        mock_history1.adjusted_total_score = Decimal('85')
        mock_history1.original_dept_rank = 4
        mock_history1.adjusted_dept_rank = 3
        mock_history1.original_company_rank = 15
        mock_history1.adjusted_company_rank = 12
        mock_history1.original_level = 'A'
        mock_history1.adjusted_level = 'S'
        mock_history1.adjustment_reason = "二次调整"
        mock_history1.adjusted_by = 1
        mock_history1.adjusted_by_name = "经理李四"
        mock_history1.adjusted_at = datetime(2024, 1, 20, 14, 0, 0)

        mock_history2 = Mock()
        mock_history2.id = 1
        mock_history2.result_id = 1
        mock_history2.original_total_score = Decimal('75')
        mock_history2.adjusted_total_score = Decimal('80')
        mock_history2.original_dept_rank = 5
        mock_history2.adjusted_dept_rank = 4
        mock_history2.original_company_rank = 20
        mock_history2.adjusted_company_rank = 15
        mock_history2.original_level = 'A'
        mock_history2.adjusted_level = 'A'
        mock_history2.adjustment_reason = "首次调整"
        mock_history2.adjusted_by = 1
        mock_history2.adjusted_by_name = "经理张三"
        mock_history2.adjusted_at = datetime(2024, 1, 15, 10, 30, 0)

        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_history1, mock_history2
        ]

        # Mock adjuster查询
        self.db.query.return_value.filter.return_value.first.side_effect = [
            Mock(name="经理李四"),
            Mock(name="经理张三")
        ]

        history = self.service.get_adjustment_history(1)

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['id'], 2)  # 最新的在前
        self.assertEqual(history[1]['id'], 1)

    def test_get_adjustment_history_with_none_values(self):
        """测试包含None值的历史记录"""
        mock_history = Mock()
        mock_history.id = 1
        mock_history.result_id = 1
        mock_history.original_total_score = None
        mock_history.adjusted_total_score = None
        mock_history.original_dept_rank = None
        mock_history.adjusted_dept_rank = 3
        mock_history.original_company_rank = None
        mock_history.adjusted_company_rank = None
        mock_history.original_level = 'A'
        mock_history.adjusted_level = 'A'
        mock_history.adjustment_reason = "仅调整部门排名"
        mock_history.adjusted_by = 1
        mock_history.adjusted_by_name = None
        mock_history.adjusted_at = None

        adjuster = Mock()
        adjuster.name = "经理王五"

        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_history]
        self.db.query.return_value.filter.return_value.first.return_value = adjuster

        history = self.service.get_adjustment_history(1)

        self.assertEqual(len(history), 1)
        self.assertIsNone(history[0]['original_total_score'])
        self.assertIsNone(history[0]['adjusted_total_score'])
        self.assertEqual(history[0]['score_change'], 0.0)
        self.assertEqual(history[0]['adjusted_by_name'], "经理王五")


class TestGetManagerEvaluationTasks(TestManagerEvaluationService):
    """测试获取评价任务列表"""

    def test_get_evaluation_tasks_manager_not_found(self):
        """测试经理不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        tasks = self.service.get_manager_evaluation_tasks(999)
        self.assertEqual(tasks, [])

    def test_get_evaluation_tasks_no_department(self):
        """测试经理没有管理部门"""
        manager = Mock()
        manager.id = 1
        manager.employee_id = 100

        self.db.query.return_value.filter.return_value.first.side_effect = [
            manager,  # 经理查询成功
            None  # 部门查询失败
        ]

        tasks = self.service.get_manager_evaluation_tasks(1)
        self.assertEqual(tasks, [])



class TestGetEngineersForEvaluation(TestManagerEvaluationService):
    """测试获取可评价工程师列表"""

    @patch.object(ManagerEvaluationService, 'get_manager_evaluation_tasks')
    def test_get_engineers_empty(self, mock_tasks):
        """测试无工程师列表"""
        mock_tasks.return_value = []
        engineers = self.service.get_engineers_for_evaluation(1)
        self.assertEqual(engineers, [])

    @patch.object(ManagerEvaluationService, 'get_manager_evaluation_tasks')
    def test_get_engineers_success(self, mock_tasks):
        """测试成功获取工程师列表"""
        result1 = Mock()
        result1.id = 1
        result1.user_id = 10
        result1.total_score = Decimal('85')
        result1.dept_rank = 2
        result1.company_rank = 10
        result1.level = 'S'
        result1.is_adjusted = False
        result1.adjustment_reason = None

        result2 = Mock()
        result2.id = 2
        result2.user_id = 20
        result2.total_score = Decimal('75')
        result2.dept_rank = 5
        result2.company_rank = 25
        result2.level = 'A'
        result2.is_adjusted = True
        result2.adjustment_reason = "调整过"

        mock_tasks.return_value = [result1, result2]

        user1 = Mock()
        user1.id = 10
        user1.username = "engineer1"
        user1.real_name = "工程师张三"
        user1.name = None

        user2 = Mock()
        user2.id = 20
        user2.username = "engineer2"
        user2.real_name = None
        user2.name = "工程师李四"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            user1, user2
        ]

        engineers = self.service.get_engineers_for_evaluation(1)

        self.assertEqual(len(engineers), 2)
        self.assertEqual(engineers[0]['user_id'], 10)
        self.assertEqual(engineers[0]['name'], "工程师张三")
        self.assertEqual(engineers[1]['user_id'], 20)
        self.assertEqual(engineers[1]['name'], "工程师李四")

    @patch.object(ManagerEvaluationService, 'get_manager_evaluation_tasks')
    def test_get_engineers_user_not_found(self, mock_tasks):
        """测试用户不存在时跳过"""
        result = Mock()
        result.id = 1
        result.user_id = 999

        mock_tasks.return_value = [result]
        self.db.query.return_value.filter.return_value.first.return_value = None

        engineers = self.service.get_engineers_for_evaluation(1)
        self.assertEqual(engineers, [])


class TestSubmitEvaluation(TestManagerEvaluationService):
    """测试提交评价"""

    def setUp(self):
        """测试前置设置"""
        super().setUp()
        self.patcher = patch.object(
            self.service, 'check_manager_permission', return_value=True
        )
        self.mock_permission = self.patcher.start()

    def tearDown(self):
        """测试后置清理"""
        self.patcher.stop()
        super().tearDown()

    def test_submit_evaluation_result_not_found(self):
        """测试绩效结果不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(999, 1)
        self.assertIn("绩效结果不存在", str(context.exception))

    def test_submit_evaluation_no_permission(self):
        """测试无权限评价"""
        self.mock_permission.return_value = False

        result = Mock()
        result.id = 1
        result.user_id = 2
        self.db.query.return_value.filter.return_value.first.return_value = result

        with self.assertRaises(ValueError) as context:
            self.service.submit_evaluation(1, 1)
        self.assertIn("无权限评价该工程师", str(context.exception))

    def test_submit_evaluation_create_new(self):
        """测试创建新评价"""
        result = Mock()
        result.id = 1
        result.user_id = 2

        manager = Mock()
        manager.id = 1
        manager.name = "经理张三"
        manager.username = "zhang3"

        # 第一次查询result，第二次查询evaluation（不存在），第三次查询manager
        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            None,  # 评价不存在
            manager
        ]

        mock_evaluation = Mock()
        mock_evaluation.id = 100

        self.db.refresh = Mock(side_effect=lambda obj: setattr(obj, 'id', 100))

        response = self.service.submit_evaluation(
            result_id=1,
            manager_id=1,
            overall_comment="整体表现良好",
            strength_comment="技术能力强",
            improvement_comment="需要提升沟通能力"
        )

        self.assertEqual(response['result_id'], 1)
        self.assertIn('evaluation_id', response)
        self.assertEqual(response['message'], '评价提交成功')

    def test_submit_evaluation_update_existing(self):
        """测试更新现有评价"""
        result = Mock()
        result.id = 1
        result.user_id = 2

        existing_evaluation = Mock()
        existing_evaluation.id = 100
        existing_evaluation.result_id = 1
        existing_evaluation.evaluator_id = 1

        manager = Mock()
        manager.id = 1
        manager.name = "经理李四"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            existing_evaluation,
            manager
        ]

        response = self.service.submit_evaluation(
            result_id=1,
            manager_id=1,
            overall_comment="更新后的评价",
            strength_comment="更新后的优点",
            improvement_comment="更新后的建议"
        )

        self.assertEqual(existing_evaluation.overall_comment, "更新后的评价")
        self.assertEqual(existing_evaluation.strength_comment, "更新后的优点")
        self.assertEqual(existing_evaluation.improvement_comment, "更新后的建议")
        self.assertEqual(response['evaluation_id'], 100)

    def test_submit_evaluation_minimal_comments(self):
        """测试最小评价（不填写评价内容）"""
        result = Mock()
        result.id = 1
        result.user_id = 2

        manager = Mock()
        manager.id = 1
        manager.name = None
        manager.username = "wang5"

        self.db.query.return_value.filter.return_value.first.side_effect = [
            result,
            None,
            manager
        ]

        response = self.service.submit_evaluation(
            result_id=1,
            manager_id=1
        )

        self.assertEqual(response['message'], '评价提交成功')


if __name__ == '__main__':
    unittest.main()
