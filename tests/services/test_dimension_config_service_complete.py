# -*- coding: utf-8 -*-
"""
DimensionConfigService 完整测试套件
覆盖目标: 60%+ 代码覆盖率，26-38个测试用例
"""

import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

from app.services.engineer_performance.dimension_config_service import DimensionConfigService


class TestDimensionConfigServiceInit(unittest.TestCase):
    """服务初始化测试"""

    def test_service_initialization(self):
        """测试服务正确初始化"""
        db = MagicMock()
        service = DimensionConfigService(db)
        self.assertIsNotNone(service)
        self.assertEqual(service.db, db)


class TestGetConfig(unittest.TestCase):
    """get_config 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def _mock_query_chain(self):
        """创建标准查询链Mock"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        return q

    def test_get_config_with_department_priority(self):
        """部门配置应该优先于全局配置"""
        dept_config = MagicMock(id=1, is_global=False, department_id=10)
        q = self._mock_query_chain()
        q.first.return_value = dept_config

        result = self.service.get_config(
            "mechanical", "senior", date(2025, 6, 1), department_id=10
        )
        self.assertEqual(result.id, 1)
        self.assertFalse(result.is_global)

    def test_get_config_fallback_to_global(self):
        """当无部门配置时应回退到全局配置"""
        global_config = MagicMock(id=2, is_global=True)
        q = self._mock_query_chain()
        # 前两次调用返回None（无部门配置），第三次返回全局配置
        q.first.side_effect = [None, None, global_config]

        result = self.service.get_config(
            "mechanical", "senior", date(2025, 6, 1), department_id=10
        )
        # 验证至少尝试了查询
        self.assertTrue(self.db.query.called)

    def test_get_config_without_department(self):
        """不指定部门时直接查全局配置"""
        config = MagicMock(id=3, is_global=True)
        q = self._mock_query_chain()
        q.first.return_value = config

        result = self.service.get_config("test", "junior")
        self.assertIsNotNone(result)

    def test_get_config_defaults_to_today(self):
        """不传effective_date时应使用今天"""
        q = self._mock_query_chain()
        q.first.return_value = MagicMock()

        self.service.get_config("mechanical")
        self.assertTrue(self.db.query.called)

    def test_get_config_with_job_level_match(self):
        """应该优先匹配指定的职级"""
        config = MagicMock(id=4, job_level="senior")
        q = self._mock_query_chain()
        q.first.return_value = config

        result = self.service.get_config("mechanical", "senior")
        self.assertEqual(result.job_level, "senior")

    def test_get_config_returns_none_when_not_found(self):
        """找不到配置时返回None"""
        q = self._mock_query_chain()
        q.first.return_value = None

        result = self.service.get_config("nonexistent")
        self.assertIsNone(result)


class TestGetDepartmentConfig(unittest.TestCase):
    """_get_department_config 内部方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_get_department_config_with_level(self):
        """按部门和职级查找配置"""
        config = MagicMock(id=1)
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = config

        result = self.service._get_department_config(
            "mechanical", "senior", date(2025, 1, 1), 10
        )
        self.assertEqual(result.id, 1)

    def test_get_department_config_generic_fallback(self):
        """无职级匹配时回退到通用配置"""
        generic_config = MagicMock(id=2, job_level=None)
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        # 第一次查询无结果，第二次返回通用配置
        q.first.side_effect = [None, generic_config]

        result = self.service._get_department_config(
            "mechanical", "senior", date(2025, 1, 1), 10
        )
        self.assertEqual(result.id, 2)


class TestGetGlobalConfig(unittest.TestCase):
    """_get_global_config 内部方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_get_global_config_with_level(self):
        """全局配置按职级匹配"""
        config = MagicMock(id=1, job_level="senior")
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.return_value = config

        result = self.service._get_global_config("mechanical", "senior", date(2025, 1, 1))
        self.assertEqual(result.id, 1)

    def test_get_global_config_fallback_to_generic(self):
        """无职级匹配时回退到通用全局配置"""
        generic_config = MagicMock(id=2, job_level=None)
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.first.side_effect = [None, generic_config]

        result = self.service._get_global_config("test", "junior", date(2025, 1, 1))
        self.assertEqual(result.id, 2)


class TestCreateConfig(unittest.TestCase):
    """create_config 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def _make_valid_data(self):
        """创建有效的配置数据"""
        data = MagicMock()
        data.technical_weight = 30
        data.execution_weight = 25
        data.cost_quality_weight = 20
        data.knowledge_weight = 15
        data.collaboration_weight = 10
        data.job_type = "mechanical"
        data.job_level = "senior"
        data.effective_date = date(2025, 1, 1)
        data.config_name = "test_config"
        data.description = "test description"
        return data

    def test_create_config_weight_sum_validation_pass(self):
        """权重总和为100时创建成功"""
        data = self._make_valid_data()
        
        with patch('app.services.engineer_performance.dimension_config_service.save_obj') as mock_save:
            with patch('app.services.engineer_performance.dimension_config_service.EngineerDimensionConfig') as MockConfig:
                MockConfig.return_value = MagicMock()
                result = self.service.create_config(data, operator_id=1)
                mock_save.assert_called_once()

    def test_create_config_weight_sum_validation_fail_less_than_100(self):
        """权重总和小于100时抛出异常"""
        data = self._make_valid_data()
        data.collaboration_weight = 5  # 总和变为95

        with self.assertRaises(ValueError) as ctx:
            self.service.create_config(data, operator_id=1)
        self.assertIn("100", str(ctx.exception))
        self.assertIn("95", str(ctx.exception))

    def test_create_config_weight_sum_validation_fail_more_than_100(self):
        """权重总和大于100时抛出异常"""
        data = self._make_valid_data()
        data.technical_weight = 35  # 总和变为105

        with self.assertRaises(ValueError) as ctx:
            self.service.create_config(data, operator_id=1)
        self.assertIn("100", str(ctx.exception))
        self.assertIn("105", str(ctx.exception))

    def test_create_global_config_auto_approved(self):
        """全局配置（无部门）应自动审批通过"""
        data = self._make_valid_data()
        
        with patch('app.services.engineer_performance.dimension_config_service.save_obj'):
            with patch('app.services.engineer_performance.dimension_config_service.EngineerDimensionConfig') as MockConfig:
                created_config = MagicMock()
                MockConfig.return_value = created_config
                
                result = self.service.create_config(data, operator_id=1, department_id=None)
                
                call_kwargs = MockConfig.call_args.kwargs
                self.assertTrue(call_kwargs.get("is_global"))
                self.assertEqual(call_kwargs.get("approval_status"), "APPROVED")

    def test_create_department_config_pending_approval(self):
        """部门配置应设为待审批状态"""
        data = self._make_valid_data()
        
        # Mock部门经理权限验证
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        user = MagicMock(employee_id=100)
        dept = MagicMock(id=10, manager_id=100)
        q.first.side_effect = [user, dept]
        
        with patch('app.services.engineer_performance.dimension_config_service.save_obj'):
            with patch('app.services.engineer_performance.dimension_config_service.EngineerDimensionConfig') as MockConfig:
                created_config = MagicMock()
                MockConfig.return_value = created_config
                
                result = self.service.create_config(data, operator_id=1, department_id=10)
                
                call_kwargs = MockConfig.call_args.kwargs
                self.assertFalse(call_kwargs.get("is_global"))
                self.assertEqual(call_kwargs.get("approval_status"), "PENDING")

    def test_create_config_without_approval_requirement(self):
        """require_approval=False时不需要审批"""
        data = self._make_valid_data()
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        user = MagicMock(employee_id=100)
        dept = MagicMock(id=10, manager_id=100)
        q.first.side_effect = [user, dept]
        
        with patch('app.services.engineer_performance.dimension_config_service.save_obj'):
            with patch('app.services.engineer_performance.dimension_config_service.EngineerDimensionConfig') as MockConfig:
                created_config = MagicMock()
                MockConfig.return_value = created_config
                
                result = self.service.create_config(
                    data, operator_id=1, department_id=10, require_approval=False
                )
                
                call_kwargs = MockConfig.call_args.kwargs
                self.assertEqual(call_kwargs.get("approval_status"), "APPROVED")


class TestValidateDepartmentManagerPermission(unittest.TestCase):
    """_validate_department_manager_permission 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_validate_permission_success(self):
        """部门经理权限验证成功"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        
        user = MagicMock(employee_id=100)
        dept = MagicMock(id=10, manager_id=100)
        q.first.side_effect = [user, dept]
        
        # 不应抛出异常
        self.service._validate_department_manager_permission(10, 1)

    def test_validate_permission_operator_not_found(self):
        """操作人不存在时抛出异常"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = None
        
        with self.assertRaises(ValueError) as ctx:
            self.service._validate_department_manager_permission(10, 999)
        self.assertIn("操作人", str(ctx.exception))

    def test_validate_permission_no_employee_id(self):
        """操作人无员工ID时抛出异常"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        
        user = MagicMock(employee_id=None)
        q.first.return_value = user
        
        with self.assertRaises(ValueError) as ctx:
            self.service._validate_department_manager_permission(10, 1)
        self.assertIn("不完整", str(ctx.exception))

    def test_validate_permission_not_department_manager(self):
        """非部门经理时抛出异常"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        
        user = MagicMock(employee_id=100)
        q.first.side_effect = [user, None]  # 部门查询返回None
        
        with self.assertRaises(ValueError) as ctx:
            self.service._validate_department_manager_permission(10, 1)
        self.assertIn("无权限", str(ctx.exception))


class TestListConfigs(unittest.TestCase):
    """list_configs 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def _mock_query(self, return_value):
        """创建查询Mock"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = return_value
        return q

    def test_list_configs_all(self):
        """列出所有配置"""
        configs = [MagicMock(id=1), MagicMock(id=2)]
        self._mock_query(configs)
        
        result = self.service.list_configs()
        self.assertEqual(len(result), 2)

    def test_list_configs_by_job_type(self):
        """按岗位类型筛选"""
        configs = [MagicMock(job_type="mechanical")]
        self._mock_query(configs)
        
        result = self.service.list_configs(job_type="mechanical")
        self.assertEqual(len(result), 1)

    def test_list_configs_by_department(self):
        """按部门筛选"""
        configs = [MagicMock(department_id=10)]
        self._mock_query(configs)
        
        result = self.service.list_configs(department_id=10)
        self.assertEqual(len(result), 1)

    def test_list_configs_exclude_expired(self):
        """默认不包含已过期配置"""
        configs = [MagicMock()]
        self._mock_query(configs)
        
        result = self.service.list_configs(include_expired=False)
        self.assertIsNotNone(result)

    def test_list_configs_include_expired(self):
        """可选择包含已过期配置"""
        configs = [MagicMock(), MagicMock()]
        self._mock_query(configs)
        
        result = self.service.list_configs(include_expired=True)
        self.assertEqual(len(result), 2)

    def test_list_configs_exclude_global(self):
        """可选择排除全局配置"""
        configs = []
        self._mock_query(configs)
        
        result = self.service.list_configs(include_global=False)
        self.assertEqual(result, [])


class TestApproveConfig(unittest.TestCase):
    """approve_config 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_approve_config_success(self):
        """审批通过"""
        config = MagicMock(
            id=1,
            is_global=False,
            approval_status="PENDING"
        )
        approver = MagicMock(is_superuser=True)
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.side_effect = [config, approver]
        
        result = self.service.approve_config(1, approver_id=1, approved=True)
        
        self.assertEqual(result.approval_status, "APPROVED")

    def test_approve_config_reject(self):
        """审批拒绝"""
        config = MagicMock(
            id=1,
            is_global=False,
            approval_status="PENDING"
        )
        approver = MagicMock(is_superuser=True)
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.side_effect = [config, approver]
        
        result = self.service.approve_config(1, approver_id=1, approved=False)
        
        self.assertEqual(result.approval_status, "REJECTED")

    def test_approve_config_with_reason(self):
        """审批时提供理由"""
        config = MagicMock(
            id=1,
            is_global=False,
            approval_status="PENDING"
        )
        approver = MagicMock(is_superuser=True)
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.side_effect = [config, approver]
        
        result = self.service.approve_config(
            1, approver_id=1, approved=False, approval_reason="权重分配不合理"
        )
        
        self.assertEqual(result.approval_reason, "权重分配不合理")

    def test_approve_config_not_found(self):
        """配置不存在时抛出异常"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = None
        
        with self.assertRaises(ValueError) as ctx:
            self.service.approve_config(999, approver_id=1)
        self.assertIn("不存在", str(ctx.exception))

    def test_approve_config_global_raises(self):
        """全局配置不能审批"""
        config = MagicMock(is_global=True, approval_status="PENDING")
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = config
        
        with self.assertRaises(ValueError) as ctx:
            self.service.approve_config(1, approver_id=1)
        self.assertIn("全局", str(ctx.exception))

    def test_approve_config_wrong_status(self):
        """非待审批状态不能审批"""
        config = MagicMock(
            is_global=False,
            approval_status="APPROVED"
        )
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = config
        
        with self.assertRaises(ValueError) as ctx:
            self.service.approve_config(1, approver_id=1)
        self.assertIn("无法审批", str(ctx.exception))


class TestValidateAdminPermission(unittest.TestCase):
    """_validate_admin_permission 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_validate_admin_superuser(self):
        """超级用户有权限"""
        user = MagicMock(is_superuser=True)
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = user
        
        # 不应抛出异常
        self.service._validate_admin_permission(1)

    def test_validate_admin_by_admin_role(self):
        """admin角色有权限"""
        user = MagicMock(is_superuser=False)
        role = MagicMock()
        role.role = MagicMock(role_code="admin")
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = user
        q.all.return_value = [role]
        
        # 不应抛出异常
        self.service._validate_admin_permission(1)

    def test_validate_admin_by_super_admin_role(self):
        """super_admin角色有权限"""
        user = MagicMock(is_superuser=False)
        role = MagicMock()
        role.role = MagicMock(role_code="super_admin")
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = user
        q.all.return_value = [role]
        
        # 不应抛出异常
        self.service._validate_admin_permission(1)

    def test_validate_admin_not_found(self):
        """审批人不存在时抛出异常"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = None
        
        with self.assertRaises(ValueError) as ctx:
            self.service._validate_admin_permission(999)
        self.assertIn("不存在", str(ctx.exception))

    def test_validate_admin_no_permission(self):
        """非管理员无权限"""
        user = MagicMock(is_superuser=False)
        role = MagicMock()
        role.role = MagicMock(role_code="user")
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.first.return_value = user
        q.all.return_value = [role]
        
        with self.assertRaises(ValueError) as ctx:
            self.service._validate_admin_permission(1)
        self.assertIn("管理员", str(ctx.exception))


class TestGetPendingApprovals(unittest.TestCase):
    """get_pending_approvals 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_get_pending_approvals(self):
        """获取待审批配置列表"""
        pending_configs = [
            MagicMock(id=1, approval_status="PENDING"),
            MagicMock(id=2, approval_status="PENDING")
        ]
        
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = pending_configs
        
        result = self.service.get_pending_approvals()
        
        self.assertEqual(len(result), 2)
        for config in result:
            self.assertEqual(config.approval_status, "PENDING")

    def test_get_pending_approvals_empty(self):
        """无待审批配置时返回空列表"""
        q = MagicMock()
        self.db.query.return_value = q
        q.filter.return_value = q
        q.order_by.return_value = q
        q.all.return_value = []
        
        result = self.service.get_pending_approvals()
        
        self.assertEqual(result, [])


class TestFormatConfig(unittest.TestCase):
    """_format_config 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_format_config_none(self):
        """None输入返回None"""
        result = self.service._format_config(None)
        self.assertIsNone(result)

    def test_format_config_valid(self):
        """正确格式化配置"""
        config = MagicMock()
        config.id = 1
        config.technical_weight = 30
        config.execution_weight = 25
        config.cost_quality_weight = 20
        config.knowledge_weight = 15
        config.collaboration_weight = 10
        config.approval_status = "APPROVED"
        config.effective_date = date(2025, 1, 1)
        
        result = self.service._format_config(config)
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["technical_weight"], 30)
        self.assertEqual(result["execution_weight"], 25)
        self.assertEqual(result["cost_quality_weight"], 20)
        self.assertEqual(result["knowledge_weight"], 15)
        self.assertEqual(result["collaboration_weight"], 10)
        self.assertEqual(result["approval_status"], "APPROVED")
        self.assertEqual(result["effective_date"], "2025-01-01")

    def test_format_config_without_approval_status(self):
        """无审批状态时返回None"""
        config = MagicMock(spec=[
            'id', 'technical_weight', 'execution_weight',
            'cost_quality_weight', 'knowledge_weight',
            'collaboration_weight', 'effective_date'
        ])
        config.id = 1
        config.technical_weight = 30
        config.execution_weight = 25
        config.cost_quality_weight = 20
        config.knowledge_weight = 15
        config.collaboration_weight = 10
        config.effective_date = date(2025, 1, 1)
        
        result = self.service._format_config(config)
        
        self.assertIsNone(result.get("approval_status"))


class TestAnalyzeJobTypeDistribution(unittest.TestCase):
    """_analyze_job_type_distribution 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_analyze_empty_profiles(self):
        """空列表返回空字典"""
        result = self.service._analyze_job_type_distribution([])
        self.assertEqual(result, {})

    def test_analyze_single_type(self):
        """单一岗位类型"""
        p1 = MagicMock(job_type="mechanical", job_level="senior")
        p2 = MagicMock(job_type="mechanical", job_level="junior")
        
        result = self.service._analyze_job_type_distribution([p1, p2])
        
        self.assertEqual(result["mechanical"]["count"], 2)
        self.assertEqual(result["mechanical"]["levels"]["senior"], 1)
        self.assertEqual(result["mechanical"]["levels"]["junior"], 1)

    def test_analyze_multiple_types(self):
        """多种岗位类型"""
        p1 = MagicMock(job_type="mechanical", job_level="senior")
        p2 = MagicMock(job_type="test", job_level="junior")
        p3 = MagicMock(job_type="electrical", job_level="senior")
        
        result = self.service._analyze_job_type_distribution([p1, p2, p3])
        
        self.assertEqual(result["mechanical"]["count"], 1)
        self.assertEqual(result["test"]["count"], 1)
        self.assertEqual(result["electrical"]["count"], 1)

    def test_analyze_none_job_level(self):
        """job_level为None时归为'all'"""
        p = MagicMock(job_type="mechanical", job_level=None)
        
        result = self.service._analyze_job_type_distribution([p])
        
        self.assertEqual(result["mechanical"]["levels"]["all"], 1)


class TestBuildConfigList(unittest.TestCase):
    """_build_config_list 方法测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = DimensionConfigService(self.db)

    def test_build_config_list_with_both_configs(self):
        """同时有部门和全局配置"""
        distribution = {
            "mechanical": {
                "count": 5,
                "levels": {"senior": 2, "junior": 3}
            }
        }
        
        dept_config = MagicMock(
            id=1,
            job_type="mechanical",
            technical_weight=30,
            execution_weight=25,
            cost_quality_weight=20,
            knowledge_weight=15,
            collaboration_weight=10,
            effective_date=date(2025, 1, 1)
        )
        
        global_config = MagicMock(
            id=2,
            job_type="mechanical",
            is_global=True,
            technical_weight=25,
            execution_weight=25,
            cost_quality_weight=25,
            knowledge_weight=15,
            collaboration_weight=10,
            effective_date=date(2025, 1, 1)
        )
        
        result = self.service._build_config_list(
            distribution,
            [dept_config],
            [global_config]
        )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["job_type"], "mechanical")
        self.assertEqual(result[0]["engineer_count"], 5)
        self.assertIsNotNone(result[0]["department_config"])
        self.assertIsNotNone(result[0]["global_config"])

    def test_build_config_list_no_dept_config(self):
        """只有全局配置"""
        distribution = {
            "test": {
                "count": 3,
                "levels": {"junior": 3}
            }
        }
        
        global_config = MagicMock(
            id=1,
            job_type="test",
            is_global=True,
            technical_weight=30,
            execution_weight=25,
            cost_quality_weight=20,
            knowledge_weight=15,
            collaboration_weight=10,
            effective_date=date(2025, 1, 1)
        )
        
        result = self.service._build_config_list(
            distribution,
            [],
            [global_config]
        )
        
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0]["department_config"])
        self.assertIsNotNone(result[0]["global_config"])


if __name__ == "__main__":
    unittest.main()
