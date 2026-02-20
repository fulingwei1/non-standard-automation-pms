# -*- coding: utf-8 -*-
"""
车间管理服务测试

测试 app/services/production/workshop_service.py
目标覆盖率: 60%+
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException
from decimal import Decimal

from app.services.production.workshop_service import WorkshopService
from app.models.production import Workshop, WorkOrder, ProductionDailyReport
from app.models.user import User
from app.schemas.production import WorkshopResponse


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def workshop_service(mock_db):
    """创建车间服务实例"""
    return WorkshopService(mock_db)


@pytest.fixture
def sample_workshop():
    """示例车间数据"""
    workshop = MagicMock(spec=Workshop)
    workshop.id = 1
    workshop.workshop_code = "WS001"
    workshop.workshop_name = "装配车间"
    workshop.workshop_type = "ASSEMBLY"
    workshop.manager_id = 10
    workshop.location = "一楼东区"
    workshop.capacity_hours = Decimal("160.00")
    workshop.description = "主要装配车间"
    workshop.is_active = True
    workshop.worker_count = 20
    workshop.created_at = datetime(2024, 1, 1, 8, 0)
    workshop.updated_at = datetime(2024, 1, 15, 10, 30)
    return workshop


@pytest.fixture
def sample_user():
    """示例用户数据"""
    user = MagicMock(spec=User)
    user.id = 10
    user.real_name = "张主管"
    return user


class TestBuildWorkshopResponse:
    """测试 _build_workshop_response 方法"""

    def test_build_response_with_manager(self, workshop_service, mock_db, sample_workshop, sample_user):
        """测试构建响应时包含主管信息"""
        # 配置 mock
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_user

        # 执行
        result = workshop_service._build_workshop_response(sample_workshop)

        # 验证
        assert isinstance(result, WorkshopResponse)
        assert result.id == 1
        assert result.workshop_code == "WS001"
        assert result.workshop_name == "装配车间"
        assert result.manager_id == 10
        assert result.manager_name == "张主管"
        assert result.capacity_hours == 160.00
        mock_db.query.assert_called_once_with(User)

    def test_build_response_without_manager(self, workshop_service, sample_workshop):
        """测试构建响应时没有主管"""
        sample_workshop.manager_id = None

        result = workshop_service._build_workshop_response(sample_workshop)

        assert result.manager_id is None
        assert result.manager_name is None

    def test_build_response_manager_not_found(self, workshop_service, mock_db, sample_workshop):
        """测试主管不存在的情况"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = workshop_service._build_workshop_response(sample_workshop)

        assert result.manager_id == 10
        assert result.manager_name is None

    def test_build_response_with_null_capacity(self, workshop_service, mock_db, sample_workshop):
        """测试产能为空的情况"""
        sample_workshop.capacity_hours = None
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        result = workshop_service._build_workshop_response(sample_workshop)

        assert result.capacity_hours is None


class TestListWorkshops:
    """测试 list_workshops 方法"""

    def test_list_all_workshops(self, workshop_service, mock_db, sample_workshop):
        """测试查询所有车间"""
        # 配置分页
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 10
        pagination.to_response = lambda items, total: {"items": items, "total": total}

        # 配置 mock
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value.all.return_value = [sample_workshop]

        # Mock user query
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None

        def query_side_effect(model):
            if model == Workshop:
                return mock_query
            return mock_user_query

        mock_db.query.side_effect = query_side_effect

        # 执行
        result = workshop_service.list_workshops(pagination)

        # 验证
        assert result["total"] == 1
        assert len(result["items"]) == 1

    def test_list_workshops_filter_by_type(self, workshop_service, mock_db):
        """测试按类型过滤车间"""
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 10
        pagination.to_response = lambda items, total: {"items": items, "total": total}

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.all.return_value = []

        result = workshop_service.list_workshops(pagination, workshop_type="ASSEMBLY")

        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_workshops_filter_by_active(self, workshop_service, mock_db):
        """测试按活跃状态过滤车间"""
        pagination = MagicMock()
        pagination.offset = 0
        pagination.limit = 10
        pagination.to_response = lambda items, total: {"items": items, "total": total}

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.all.return_value = []

        result = workshop_service.list_workshops(pagination, is_active=True)

        assert result["total"] == 0


class TestCreateWorkshop:
    """测试 create_workshop 方法"""

    def test_create_workshop_success(self, workshop_service, mock_db):
        """测试成功创建车间"""
        workshop_in = MagicMock()
        workshop_in.workshop_code = "WS002"
        workshop_in.manager_id = 10
        workshop_in.model_dump.return_value = {
            "workshop_code": "WS002",
            "workshop_name": "新车间",
            "manager_id": 10,
        }

        # 配置 mock - 车间不存在
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        # Mock get_or_404
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_user = MagicMock(spec=User)
            mock_get.return_value = mock_user

            # Mock save_obj
            with patch("app.services.production.workshop_service.save_obj"):
                result = workshop_service.create_workshop(workshop_in)

                assert isinstance(result, WorkshopResponse)

    def test_create_workshop_duplicate_code(self, workshop_service, mock_db, sample_workshop):
        """测试创建重复编码的车间"""
        workshop_in = MagicMock()
        workshop_in.workshop_code = "WS001"

        # 配置 mock - 车间已存在
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = sample_workshop

        # 执行并验证异常
        with pytest.raises(HTTPException) as exc_info:
            workshop_service.create_workshop(workshop_in)

        assert exc_info.value.status_code == 400
        assert "车间编码已存在" in str(exc_info.value.detail)

    def test_create_workshop_invalid_manager(self, workshop_service, mock_db):
        """测试创建车间时主管不存在"""
        workshop_in = MagicMock()
        workshop_in.workshop_code = "WS002"
        workshop_in.manager_id = 999

        # 配置 mock - 车间不存在
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        # Mock get_or_404 抛出异常
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="车间主管不存在")

            with pytest.raises(HTTPException) as exc_info:
                workshop_service.create_workshop(workshop_in)

            assert exc_info.value.status_code == 404


class TestGetWorkshop:
    """测试 get_workshop 方法"""

    def test_get_workshop_success(self, workshop_service):
        """测试成功获取车间"""
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_workshop = MagicMock(spec=Workshop)
            mock_workshop.id = 1
            mock_workshop.manager_id = None
            mock_get.return_value = mock_workshop

            result = workshop_service.get_workshop(1)

            assert isinstance(result, WorkshopResponse)
            mock_get.assert_called_once()

    def test_get_workshop_not_found(self, workshop_service):
        """测试获取不存在的车间"""
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="车间不存在")

            with pytest.raises(HTTPException) as exc_info:
                workshop_service.get_workshop(999)

            assert exc_info.value.status_code == 404


class TestUpdateWorkshop:
    """测试 update_workshop 方法"""

    def test_update_workshop_success(self, workshop_service, sample_workshop):
        """测试成功更新车间"""
        workshop_in = MagicMock()
        workshop_in.manager_id = 20
        workshop_in.model_dump.return_value = {"workshop_name": "更新后的车间", "manager_id": 20}

        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.return_value = sample_workshop

            with patch("app.services.production.workshop_service.save_obj"):
                result = workshop_service.update_workshop(1, workshop_in)

                assert isinstance(result, WorkshopResponse)

    def test_update_workshop_invalid_manager(self, workshop_service, sample_workshop):
        """测试更新时主管不存在"""
        workshop_in = MagicMock()
        workshop_in.manager_id = 999
        workshop_in.model_dump.return_value = {"manager_id": 999}

        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            # 第一次调用返回车间，第二次调用抛出异常
            mock_get.side_effect = [
                sample_workshop,
                HTTPException(status_code=404, detail="车间主管不存在")
            ]

            with pytest.raises(HTTPException) as exc_info:
                workshop_service.update_workshop(1, workshop_in)

            assert exc_info.value.status_code == 404


class TestGetCapacity:
    """测试 get_capacity 方法"""

    def test_get_capacity_with_date_range(self, workshop_service, mock_db, sample_workshop):
        """测试获取车间产能（指定日期范围）"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        # Mock get_or_404
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.return_value = sample_workshop

            # Mock work orders query
            mock_wo_query = MagicMock()
            mock_work_order = MagicMock(spec=WorkOrder)
            mock_work_order.standard_hours = Decimal("10.0")
            mock_work_order.actual_hours = Decimal("8.0")
            mock_work_order.status = "COMPLETED"

            mock_wo_query.filter.return_value.all.return_value = [mock_work_order]

            # Mock daily reports query
            mock_dr_query = MagicMock()
            mock_daily_report = MagicMock(spec=ProductionDailyReport)
            mock_daily_report.actual_hours = Decimal("8.0")

            mock_dr_query.filter.return_value.all.return_value = [mock_daily_report]

            # Setup query side effect
            def query_side_effect(model):
                if model == WorkOrder:
                    return mock_wo_query
                elif model == ProductionDailyReport:
                    return mock_dr_query
                return MagicMock()

            mock_db.query.side_effect = query_side_effect

            # 执行
            result = workshop_service.get_capacity(1, start, end)

            # 验证
            assert result["workshop_id"] == 1
            assert result["workshop_name"] == "装配车间"
            assert result["work_days"] == 31
            assert result["worker_count"] == 20
            assert result["capacity_hours"] == 160.0
            assert result["work_order_count"] == 1
            assert result["completed_count"] == 1

    def test_get_capacity_without_date_range(self, workshop_service, mock_db, sample_workshop):
        """测试获取车间产能（无日期范围，使用当月）"""
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.return_value = sample_workshop

            # Mock queries
            mock_wo_query = MagicMock()
            mock_wo_query.filter.return_value.all.return_value = []

            mock_dr_query = MagicMock()
            mock_dr_query.filter.return_value.all.return_value = []

            def query_side_effect(model):
                if model == WorkOrder:
                    return mock_wo_query
                elif model == ProductionDailyReport:
                    return mock_dr_query
                return MagicMock()

            mock_db.query.side_effect = query_side_effect

            # 执行
            result = workshop_service.get_capacity(1)

            # 验证
            assert "start_date" in result
            assert "end_date" in result
            assert result["work_order_count"] == 0

    def test_get_capacity_zero_capacity(self, workshop_service, mock_db, sample_workshop):
        """测试产能为零的情况"""
        sample_workshop.capacity_hours = None
        sample_workshop.worker_count = 10

        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.return_value = sample_workshop

            mock_wo_query = MagicMock()
            mock_wo_query.filter.return_value.all.return_value = []

            mock_dr_query = MagicMock()
            mock_dr_query.filter.return_value.all.return_value = []

            def query_side_effect(model):
                if model == WorkOrder:
                    return mock_wo_query
                elif model == ProductionDailyReport:
                    return mock_dr_query
                return MagicMock()

            mock_db.query.side_effect = query_side_effect

            result = workshop_service.get_capacity(1, date(2024, 1, 1), date(2024, 1, 10))

            # 验证使用默认计算: 10天 * 8小时 * 10人 = 800
            assert result["capacity_hours"] == 0.0
            assert result["worker_count"] == 10

    def test_get_capacity_various_work_order_status(self, workshop_service, mock_db, sample_workshop):
        """测试不同工单状态的统计"""
        with patch("app.services.production.workshop_service.get_or_404") as mock_get:
            mock_get.return_value = sample_workshop

            # 创建不同状态的工单
            wo_pending = MagicMock(spec=WorkOrder)
            wo_pending.status = "PENDING"
            wo_pending.standard_hours = Decimal("5.0")
            wo_pending.actual_hours = Decimal("0.0")

            wo_started = MagicMock(spec=WorkOrder)
            wo_started.status = "STARTED"
            wo_started.standard_hours = Decimal("10.0")
            wo_started.actual_hours = Decimal("5.0")

            wo_completed = MagicMock(spec=WorkOrder)
            wo_completed.status = "COMPLETED"
            wo_completed.standard_hours = Decimal("8.0")
            wo_completed.actual_hours = Decimal("7.0")

            mock_wo_query = MagicMock()
            mock_wo_query.filter.return_value.all.return_value = [wo_pending, wo_started, wo_completed]

            mock_dr_query = MagicMock()
            mock_dr_query.filter.return_value.all.return_value = []

            def query_side_effect(model):
                if model == WorkOrder:
                    return mock_wo_query
                elif model == ProductionDailyReport:
                    return mock_dr_query
                return MagicMock()

            mock_db.query.side_effect = query_side_effect

            result = workshop_service.get_capacity(1, date(2024, 1, 1), date(2024, 1, 10))

            assert result["pending_count"] == 1
            assert result["in_progress_count"] == 1
            assert result["completed_count"] == 1
            assert result["work_order_count"] == 3
