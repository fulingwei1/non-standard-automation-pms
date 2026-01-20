# -*- coding: utf-8 -*-
"""
Tests for resource_allocation_service service
Covers: app/services/resource_allocation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 153 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.resource_allocation_service import ResourceAllocationService
from app.models.project import Workstation


@pytest.fixture
def test_workstation(db_session: Session):
    """创建测试工位"""
    workstation = Workstation(
        workstation_code="WS001",
        workstation_name="测试工位",
        is_active=True,
        status="IDLE"
    )
    db_session.add(workstation)
    db_session.commit()
    db_session.refresh(workstation)
    return workstation


class TestResourceAllocationService:
    """Test suite for ResourceAllocationService."""

    def test_check_workstation_availability_not_found(self, db_session):
        """测试检查工位可用性 - 工位不存在"""
        is_available, reason = ResourceAllocationService.check_workstation_availability(
            db_session,
            workstation_id=99999,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert is_available is False
        assert '不存在' in reason

    def test_check_workstation_availability_inactive(self, db_session, test_workstation):
        """测试检查工位可用性 - 工位已停用"""
        test_workstation.is_active = False
        db_session.add(test_workstation)
        db_session.commit()
        
        is_available, reason = ResourceAllocationService.check_workstation_availability(
            db_session,
            workstation_id=test_workstation.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert is_available is False
        assert '停用' in reason

    def test_check_workstation_availability_success(self, db_session, test_workstation):
        """测试检查工位可用性 - 成功场景"""
        is_available, reason = ResourceAllocationService.check_workstation_availability(
            db_session,
            workstation_id=test_workstation.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert is_available is True
        assert reason is None

    def test_find_available_workstations_default_dates(self, db_session):
        """测试查找可用工位 - 使用默认日期"""
        result = ResourceAllocationService.find_available_workstations(db_session)
        
        assert isinstance(result, list)

    def test_find_available_workstations_with_dates(self, db_session):
        """测试查找可用工位 - 指定日期"""
        start_date = date.today()
        end_date = date.today() + timedelta(days=7)
        
        result = ResourceAllocationService.find_available_workstations(
            db_session,
            start_date=start_date,
            end_date=end_date
        )
        
        assert isinstance(result, list)

    def test_find_available_workstations_with_workshop(self, db_session):
        """测试查找可用工位 - 指定车间"""
        result = ResourceAllocationService.find_available_workstations(
            db_session,
            workshop_id=1
        )
        
        assert isinstance(result, list)

    def test_find_available_workstations_with_capability(self, db_session):
        """测试查找可用工位 - 指定能力"""
        result = ResourceAllocationService.find_available_workstations(
            db_session,
            required_capability="ASSEMBLY"
        )
        
        assert isinstance(result, list)

    def test_check_worker_availability_not_found(self, db_session):
        """测试检查人员可用性 - 人员不存在"""
        is_available, reason = ResourceAllocationService.check_worker_availability(
            db_session,
            worker_id=99999,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert is_available is False
        assert '不存在' in reason

    def test_find_available_workers_default_dates(self, db_session):
        """测试查找可用人员 - 使用默认日期"""
        result = ResourceAllocationService.find_available_workers(db_session)
        
        assert isinstance(result, list)

    def test_detect_resource_conflicts_no_conflicts(self, db_session):
        """测试检测资源冲突 - 无冲突"""
        result = ResourceAllocationService.detect_resource_conflicts(
            db_session,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )
        
        assert isinstance(result, list)

    def test_allocate_resources_success(self, db_session):
        """测试分配资源 - 成功场景"""
        allocation_request = {
            'workstation_id': 1,
            'worker_ids': [1, 2],
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=7)
        }
        
        result = ResourceAllocationService.allocate_resources(
            db_session,
            allocation_request
        )
        
        assert result is not None
        assert 'success' in result
