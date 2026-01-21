# -*- coding: utf-8 -*-
"""
Tests for resource_allocation_service service
Covers: app/services/resource_allocation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 153 lines
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.resource_allocation_service import ResourceAllocationService
from app.models.project import Project
from tests.factories import ProjectFactory


class TestResourceAllocationService:
    """Test suite for ResourceAllocationService."""

    def test_check_workstation_availability_not_found(self, db_session):
        """测试检查工位可用性 - 工位不存在"""
        is_available, reason = ResourceAllocationService.check_workstation_availability(
            db_session,
            workstation_id=99999,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert is_available is False
        assert "不存在" in reason

    def test_find_available_workstations_default_dates(self, db_session):
        """测试查找可用工位 - 使用默认日期"""
        result = ResourceAllocationService.find_available_workstations(db_session)

        assert isinstance(result, list)

    def test_find_available_workstations_with_dates(self, db_session):
        """测试查找可用工位 - 指定日期"""
        start_date = date.today()
        end_date = date.today() + timedelta(days=7)

        result = ResourceAllocationService.find_available_workstations(
            db_session, start_date=start_date, end_date=end_date
        )

        assert isinstance(result, list)

    def test_find_available_workstations_with_workshop(self, db_session):
        """测试查找可用工位 - 指定车间"""
        result = ResourceAllocationService.find_available_workstations(
            db_session, workshop_id=1
        )

        assert isinstance(result, list)

    def test_check_worker_availability_not_found(self, db_session):
        """测试检查人员可用性 - 人员不存在"""
        is_available, reason, available_hours = ResourceAllocationService.check_worker_availability(
            db_session,
            worker_id=99999,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert is_available is False
        assert "不存在" in reason
        assert available_hours == 0.0

    def test_find_available_workers_default_dates(self, db_session):
        """测试查找可用人员 - 使用默认日期"""
        result = ResourceAllocationService.find_available_workers(db_session)

        assert isinstance(result, list)

    def test_detect_resource_conflicts_no_conflicts(self, db_session):
        """测试检测资源冲突 - 无冲突"""
        from app.models.project import Project
        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            stage="S1",
            status="ST01",
            health="H1"
        )
        db_session.add(project)
        db_session.flush()

        result = ResourceAllocationService.detect_resource_conflicts(
            db_session,
            project_id=project.id,
            machine_id=None,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        assert isinstance(result, list)

    def test_allocate_resources_success(self, db_session):
        """测试分配资源 - 成功场景"""
        from app.models.project import Project
        project = Project(
            project_code="PJ-TEST2",
            project_name="测试项目2",
            stage="S1",
            status="ST01",
            health="H1"
        )
        db_session.add(project)
        db_session.flush()

        result = ResourceAllocationService.allocate_resources(
            db_session,
            project_id=project.id,
            machine_id=None,
            suggested_start_date=date.today(),
            suggested_end_date=date.today() + timedelta(days=7),
        )

        assert result is not None
        assert "can_allocate" in result
        assert "workstations" in result
        assert "workers" in result
        assert "conflicts" in result

    def test_calculate_workdays(self, db_session):
        """测试计算工作日"""
        start_date = date(2024, 1, 1)  # 周一
        end_date = date(2024, 1, 7)    # 周日

        workdays = ResourceAllocationService._calculate_workdays(start_date, end_date)
        assert workdays >= 1

    def test_calculate_overlap_days(self, db_session):
        """测试计算重叠天数"""
        # 完全重叠
        days = ResourceAllocationService._calculate_overlap_days(
            date(2024, 1, 1), date(2024, 1, 5),
            date(2024, 1, 2), date(2024, 1, 4)
        )
        assert days == 3

        # 无重叠
        days = ResourceAllocationService._calculate_overlap_days(
            date(2024, 1, 1), date(2024, 1, 5),
            date(2024, 1, 6), date(2024, 1, 10)
        )
        assert days == 0
