# -*- coding: utf-8 -*-
"""
DimensionConfigService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_config: 获取五维权重配置
- create_config: 创建配置
- list_configs: 获取配置列表
- get_department_configs: 获取部门配置
- approve_config: 审批配置
- get_pending_approvals: 获取待审批配置
"""

from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from decimal import Decimal

import pytest


class TestDimensionConfigServiceInit:
    """测试 DimensionConfigService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        service = DimensionConfigService(mock_db)

        assert service.db == mock_db


class TestGetConfig:
    """测试 get_config 方法"""

    def test_returns_department_config_first(self):
        """测试优先返回部门配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_dept_config = MagicMock()
        mock_dept_config.id = 1
        mock_dept_config.job_type = "mechanical"
        mock_dept_config.is_global = False

        service = DimensionConfigService(mock_db)
        service._get_department_config = MagicMock(return_value=mock_dept_config)
        service._get_global_config = MagicMock(return_value=None)

        result = service.get_config("mechanical", department_id=1)

        assert result == mock_dept_config
        service._get_department_config.assert_called_once()

    def test_falls_back_to_global_config(self):
        """测试回退到全局配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_global_config = MagicMock()
        mock_global_config.id = 2
        mock_global_config.is_global = True

        service = DimensionConfigService(mock_db)
        service._get_department_config = MagicMock(return_value=None)
        service._get_global_config = MagicMock(return_value=mock_global_config)

        result = service.get_config("mechanical", department_id=1)

        assert result == mock_global_config

    def test_uses_today_as_default_date(self):
        """测试默认使用今天日期"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        service = DimensionConfigService(mock_db)
        service._get_global_config = MagicMock(return_value=None)

        result = service.get_config("test")

        service._get_global_config.assert_called_once()
        call_args = service._get_global_config.call_args
        assert call_args[0][2] == date.today()

    def test_filters_by_job_level(self):
        """测试按岗位级别过滤"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.job_level = "senior"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.first.return_value = mock_config
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service._get_global_config("mechanical", "senior", date.today())

        assert result == mock_config


class TestGetDepartmentConfig:
    """测试 _get_department_config 方法"""

    def test_queries_department_config(self):
        """测试查询部门配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.department_id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.first.return_value = mock_config
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service._get_department_config("mechanical", "senior", date.today(), 1)

        mock_db.query.assert_called()

    def test_returns_none_when_not_found(self):
        """测试未找到时返回None"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service._get_department_config("mechanical", None, date.today(), 999)

        assert result is None


class TestCreateConfig:
    """测试 create_config 方法"""

    def test_creates_config_successfully(self):
        """测试成功创建配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = DimensionConfigService(mock_db)

        data = MagicMock()
        data.job_type = "mechanical"
        data.job_level = "senior"
        data.technical_weight = 30
        data.execution_weight = 25
        data.cost_quality_weight = 20
        data.knowledge_weight = 15
        data.collaboration_weight = 10
        data.effective_date = date.today()
        data.config_name = "测试配置"
        data.description = "测试描述"

        result = service.create_config(data, operator_id=1, require_approval=False)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_validates_weight_sum(self):
        """测试验证权重总和"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        service = DimensionConfigService(mock_db)

        data = MagicMock()
        data.technical_weight = 30
        data.execution_weight = 30
        data.cost_quality_weight = 30
        data.knowledge_weight = 30
        data.collaboration_weight = 30  # 总和150，不等于100

        with pytest.raises(ValueError) as exc_info:
            service.create_config(data, operator_id=1)

        assert "权重总和必须为100" in str(exc_info.value)

    def test_validates_department_manager_permission(self):
        """测试验证部门经理权限"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        service = DimensionConfigService(mock_db)
        service._validate_department_manager_permission = MagicMock(
            side_effect=ValueError("无权限")
        )

        data = MagicMock()
        data.technical_weight = 30
        data.execution_weight = 25
        data.cost_quality_weight = 20
        data.knowledge_weight = 15
        data.collaboration_weight = 10

        with pytest.raises(ValueError):
            service.create_config(data, operator_id=1, department_id=1)

    def test_sets_approval_status_for_department_config(self):
        """测试部门配置设置待审批状态"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = DimensionConfigService(mock_db)
        service._validate_department_manager_permission = MagicMock()

        data = MagicMock()
        data.job_type = "test"
        data.job_level = None
        data.technical_weight = 20
        data.execution_weight = 20
        data.cost_quality_weight = 20
        data.knowledge_weight = 20
        data.collaboration_weight = 20
        data.effective_date = date.today()
        data.config_name = "部门配置"
        data.description = None

        result = service.create_config(data, operator_id=1, department_id=1)

        mock_db.add.assert_called_once()


class TestValidateDepartmentManagerPermission:
    """测试 _validate_department_manager_permission 方法"""

    def test_raises_for_invalid_operator(self):
        """测试无效操作人时抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_department_manager_permission(1, 999)

        assert "操作人信息不完整" in str(exc_info.value)

    def test_raises_for_non_manager(self):
        """测试非部门经理时抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_operator = MagicMock()
        mock_operator.employee_id = 1

        # First query returns operator
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_operator,
            None  # Department not found
        ]

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_department_manager_permission(1, 1)

        assert "无权限" in str(exc_info.value)


class TestListConfigs:
    """测试 list_configs 方法"""

    def test_returns_all_configs(self):
        """测试返回所有配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config1 = MagicMock()
        mock_config1.id = 1
        mock_config2 = MagicMock()
        mock_config2.id = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_config1, mock_config2]
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.list_configs()

        assert len(result) == 2

    def test_filters_by_job_type(self):
        """测试按岗位类型过滤"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.list_configs(job_type="mechanical")

        mock_query.filter.assert_called()

    def test_filters_by_department(self):
        """测试按部门过滤"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.list_configs(department_id=1)

        mock_query.filter.assert_called()

    def test_excludes_expired_by_default(self):
        """测试默认排除过期配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.list_configs(include_expired=False)

        mock_query.filter.assert_called()


class TestGetDepartmentConfigs:
    """测试 get_department_configs 方法"""

    def test_returns_not_manager_for_invalid_user(self):
        """测试无效用户返回非经理状态"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DimensionConfigService(mock_db)

        result = service.get_department_configs(999)

        assert result['is_manager'] is False
        assert result['department_id'] is None

    def test_returns_not_manager_when_no_department(self):
        """测试无管理部门时返回非经理状态"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.employee_id = 1

        # First query returns user, second returns None (no department)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None
        ]

        service = DimensionConfigService(mock_db)

        result = service.get_department_configs(1)

        assert result['is_manager'] is False

    def test_returns_department_info_for_manager(self):
        """测试经理返回部门信息"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.employee_id = 1

        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_user, mock_dept]
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)
        service.list_configs = MagicMock(return_value=[])
        service._analyze_job_type_distribution = MagicMock(return_value={})
        service._build_config_list = MagicMock(return_value=[])

        result = service.get_department_configs(1)

        assert result['is_manager'] is True
        assert result['department_id'] == 1


class TestAnalyzeJobTypeDistribution:
    """测试 _analyze_job_type_distribution 方法"""

    def test_analyzes_distribution(self):
        """测试分析岗位类型分布"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_profile1 = MagicMock()
        mock_profile1.job_type = "mechanical"
        mock_profile1.job_level = "senior"

        mock_profile2 = MagicMock()
        mock_profile2.job_type = "mechanical"
        mock_profile2.job_level = "junior"

        mock_profile3 = MagicMock()
        mock_profile3.job_type = "test"
        mock_profile3.job_level = None

        service = DimensionConfigService(mock_db)

        result = service._analyze_job_type_distribution([mock_profile1, mock_profile2, mock_profile3])

        assert "mechanical" in result
        assert result["mechanical"]["count"] == 2
        assert "test" in result
        assert result["test"]["count"] == 1


class TestBuildConfigList:
    """测试 _build_config_list 方法"""

    def test_builds_config_list(self):
        """测试构建配置列表"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        job_type_distribution = {
            "mechanical": {"count": 5, "levels": {"senior": 2, "junior": 3}}
        }

        mock_dept_config = MagicMock()
        mock_dept_config.job_type = "mechanical"

        mock_global_config = MagicMock()
        mock_global_config.job_type = "mechanical"
        mock_global_config.is_global = True

        service = DimensionConfigService(mock_db)
        service._format_config = MagicMock(return_value={"id": 1})

        result = service._build_config_list(
            job_type_distribution,
            [mock_dept_config],
            [mock_global_config]
        )

        assert len(result) == 1
        assert result[0]["job_type"] == "mechanical"
        assert result[0]["engineer_count"] == 5


class TestFormatConfig:
    """测试 _format_config 方法"""

    def test_formats_config(self):
        """测试格式化配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.technical_weight = 30
        mock_config.execution_weight = 25
        mock_config.cost_quality_weight = 20
        mock_config.knowledge_weight = 15
        mock_config.collaboration_weight = 10
        mock_config.approval_status = "APPROVED"
        mock_config.effective_date = date(2024, 1, 1)

        service = DimensionConfigService(mock_db)

        result = service._format_config(mock_config)

        assert result["id"] == 1
        assert result["technical_weight"] == 30
        assert result["approval_status"] == "APPROVED"

    def test_returns_none_for_none_config(self):
        """测试空配置返回None"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        service = DimensionConfigService(mock_db)

        result = service._format_config(None)

        assert result is None


class TestApproveConfig:
    """测试 approve_config 方法"""

    def test_approves_config_successfully(self):
        """测试成功审批配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.is_global = False
        mock_config.approval_status = "PENDING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = DimensionConfigService(mock_db)
        service._validate_admin_permission = MagicMock()

        result = service.approve_config(1, approver_id=1, approved=True)

        assert mock_config.approval_status == "APPROVED"
        mock_db.commit.assert_called_once()

    def test_rejects_config(self):
        """测试拒绝配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.is_global = False
        mock_config.approval_status = "PENDING"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        service = DimensionConfigService(mock_db)
        service._validate_admin_permission = MagicMock()

        result = service.approve_config(1, approver_id=1, approved=False, approval_reason="不符合要求")

        assert mock_config.approval_status == "REJECTED"
        assert mock_config.approval_reason == "不符合要求"

    def test_raises_for_missing_config(self):
        """测试配置不存在时抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.approve_config(999, approver_id=1)

        assert "配置不存在" in str(exc_info.value)

    def test_raises_for_global_config(self):
        """测试全局配置抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.is_global = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.approve_config(1, approver_id=1)

        assert "全局配置无需审批" in str(exc_info.value)

    def test_raises_for_non_pending_status(self):
        """测试非待审批状态抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.is_global = False
        mock_config.approval_status = "APPROVED"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.approve_config(1, approver_id=1)

        assert "无法审批" in str(exc_info.value)


class TestValidateAdminPermission:
    """测试 _validate_admin_permission 方法"""

    def test_allows_superuser(self):
        """测试允许超级用户"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_approver = MagicMock()
        mock_approver.is_superuser = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_approver

        service = DimensionConfigService(mock_db)

        # Should not raise
        service._validate_admin_permission(1)

    def test_allows_admin_role(self):
        """测试允许管理员角色"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_approver = MagicMock()
        mock_approver.is_superuser = False

        mock_role = MagicMock()
        mock_role.role_code = "admin"

        mock_user_role = MagicMock()
        mock_user_role.role = mock_role

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_approver
        mock_query.all.return_value = [mock_user_role]
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        # Should not raise
        service._validate_admin_permission(1)

    def test_raises_for_non_admin(self):
        """测试非管理员抛出异常"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_approver = MagicMock()
        mock_approver.is_superuser = False

        mock_user_role = MagicMock()
        mock_user_role.role = MagicMock()
        mock_user_role.role.role_code = "user"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_approver
        mock_query.all.return_value = [mock_user_role]
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_admin_permission(1)

        assert "只有管理员可以审批" in str(exc_info.value)


class TestGetPendingApprovals:
    """测试 get_pending_approvals 方法"""

    def test_returns_pending_configs(self):
        """测试返回待审批配置"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_config1 = MagicMock()
        mock_config1.id = 1
        mock_config1.approval_status = "PENDING"

        mock_config2 = MagicMock()
        mock_config2.id = 2
        mock_config2.approval_status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_config1, mock_config2]
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.get_pending_approvals()

        assert len(result) == 2

    def test_returns_empty_list_when_no_pending(self):
        """测试无待审批时返回空列表"""
        from app.services.engineer_performance.dimension_config_service import DimensionConfigService

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = DimensionConfigService(mock_db)

        result = service.get_pending_approvals()

        assert result == []
