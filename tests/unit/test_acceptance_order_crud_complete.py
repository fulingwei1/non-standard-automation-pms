# -*- coding: utf-8 -*-
"""
验收单 CRUD 单元测试

覆盖 app/api/v1/endpoints/acceptance/order_crud.py 的关键端点
"""

import pytest
pytestmark = pytest.mark.skip(reason="Missing factory classes - needs implementation")
from fastapi import HTTPException
from sqlalchemy.orm import Session

from tests.factories import (
    AcceptanceOrderFactory,
    MachineFactory,
    ProjectFactory,
    UserFactory,
)
from app.models.acceptance import AcceptanceOrder


class TestReadAcceptanceOrder:
    """读取验收单测试"""

    def test_read_order_success(self, db_session: Session, test_acceptance_order):
        """成功读取验收单"""
        from app.api.v1.endpoints.acceptance import order_crud

        response = order_crud.read_acceptance_order(
        order_id=test_acceptance_order.id, db_session=db_session
        )
        assert response.id == test_acceptance_order.id

    def test_read_order_not_found(self, db_session: Session):
        """验收单不存在时应抛出 404 错误"""
        from app.api.v1.endpoints.acceptance import order_crud

        with pytest.raises(HTTPException) as exc_info:
            order_crud.read_acceptance_order(order_id=99999, db_session=db_session)
            assert exc_info.value.status_code == 404


class TestReadAcceptanceOrders:
    """读取验收单列表测试"""

    def test_read_orders_by_project(self, db_session: Session, test_project):
        """按项目读取验收单列表"""
        AcceptanceOrderFactory.create(
        project=test_project, acceptance_type="FAT", order_no="FAT-001"
        )
        AcceptanceOrderFactory.create(
        project=test_project, acceptance_type="SAT", order_no="SAT-001"
        )
        db_session.commit()

        from app.api.v1.endpoints.acceptance import order_crud

        response = order_crud.read_acceptance_orders(
        project_id=test_project.id, db_session=db_session, skip=0, limit=10
        )
        assert len(response.items) == 2

    def test_read_orders_with_filter_by_status(self, db_session: Session, test_project):
        """按状态过滤验收单列表"""
        AcceptanceOrderFactory.create(
        project=test_project, status="COMPLETED", order_no="FAT-001"
        )
        AcceptanceOrderFactory.create(
        project=test_project, status="IN_PROGRESS", order_no="SAT-001"
        )
        db_session.commit()

        from app.api.v1.endpoints.acceptance import order_crud

        response = order_crud.read_acceptance_orders(
        project_id=test_project.id,
        status="COMPLETED",
        db_session=db_session,
        skip=0,
        limit=10,
        )
        assert len(response.items) == 1
        assert response.items[0].status == "COMPLETED"


class TestCreateAcceptanceOrder:
    """创建验收单测试"""

    def test_create_fat_order_success(
        self, db_session: Session, test_project, test_machine, test_user
    ):
        """成功创建 FAT 验收单"""
        from app.api.v1.endpoints.acceptance import order_crud
        from app.schemas.acceptance import AcceptanceOrderCreateRequest

        order_data = AcceptanceOrderCreateRequest(
        acceptance_type="FAT",
        scheduled_date="2025-02-01",
        engineer_id=test_user.id,
        )

        response = order_crud.create_acceptance_order(
        project_id=test_project.id,
        machine_id=test_machine.id,
        order_data=order_data,
        current_user=test_user,
        db_session=db_session,
        )
        assert response.acceptance_type == "FAT"
        assert response.project_id == test_project.id
        assert response.machine_id == test_machine.id

    def test_create_sat_order_success(
        self, db_session: Session, test_project, test_machine, test_user
    ):
        """成功创建 SAT 验收单"""
        from app.api.v1.endpoints.acceptance import order_crud
        from app.schemas.acceptance import AcceptanceOrderCreateRequest

        order_data = AcceptanceOrderCreateRequest(
        acceptance_type="SAT",
        scheduled_date="2025-02-15",
        engineer_id=test_user.id,
        )

        response = order_crud.create_acceptance_order(
        project_id=test_project.id,
        machine_id=test_machine.id,
        order_data=order_data,
        current_user=test_user,
        db_session=db_session,
        )
        assert response.acceptance_type == "SAT"

    def test_create_final_order_success(
        self, db_session: Session, test_project, test_user
    ):
        """成功创建终验收单"""
        from app.api.v1.endpoints.acceptance import order_crud
        from app.schemas.acceptance import AcceptanceOrderCreateRequest

        order_data = AcceptanceOrderCreateRequest(
        acceptance_type="FINAL",
        scheduled_date="2025-03-01",
        engineer_id=test_user.id,
        )

        response = order_crud.create_acceptance_order(
        project_id=test_project.id,
        machine_id=None,
        order_data=order_data,
        current_user=test_user,
        db_session=db_session,
        )
        assert response.acceptance_type == "FINAL"
        assert response.machine_id is None


class TestUpdateAcceptanceOrder:
    """更新验收单测试"""

    def test_update_order_success(
        self, db_session: Session, test_acceptance_order, test_user
    ):
        """成功更新验收单"""
        from app.api.v1.endpoints.acceptance import order_crud
        from app.schemas.acceptance import AcceptanceOrderUpdateRequest

        update_data = AcceptanceOrderUpdateRequest(
        scheduled_date="2025-02-10", engineer_id=test_user.id
        )

        response = order_crud.update_acceptance_order(
        order_id=test_acceptance_order.id,
        order_data=update_data,
        current_user=test_user,
        db_session=db_session,
        )
        assert response.scheduled_date == "2025-02-10"

    def test_update_nonexistent_order(self, db_session: Session, test_user):
        """更新不存在的验收单应抛出 404 错误"""
        from app.api.v1.endpoints.acceptance import order_crud
        from app.schemas.acceptance import AcceptanceOrderUpdateRequest

        update_data = AcceptanceOrderUpdateRequest(scheduled_date="2025-02-10")

        with pytest.raises(HTTPException) as exc_info:
            order_crud.update_acceptance_order(
            99999, update_data, test_user, db_session
            )
            assert exc_info.value.status_code == 404


class TestDeleteAcceptanceOrder:
    """删除验收单测试"""

    def test_delete_order_success(self, db_session: Session, test_acceptance_order):
        """成功删除验收单"""
        from app.api.v1.endpoints.acceptance import order_crud

        order_id = test_acceptance_order.id
        db_session.flush()

        order_crud.delete_acceptance_order(order_id=order_id, db_session=db_session)

        # 验证已被标记为已删除
        deleted_order = (
        db_session.query(AcceptanceOrder)
        .filter(AcceptanceOrder.id == order_id)
        .first()
        )
        assert deleted_order.is_active == False

    def test_delete_nonexistent_order(self, db_session: Session):
        """删除不存在的验收单应抛出 404 错误"""
        from app.api.v1.endpoints.acceptance import order_crud

        with pytest.raises(HTTPException) as exc_info:
            order_crud.delete_acceptance_order(order_id=99999, db_session=db_session)
            assert exc_info.value.status_code == 404


            # Fixtures
@pytest.fixture
def test_project(db_session: Session):
    """创建测试项目"""
    project = ProjectFactory.create(project_code="P2025001", stage="S5")
    db_session.commit()
    return project


@pytest.fixture
def test_machine(db_session: Session, test_project):
    """创建测试设备"""
    machine = MachineFactory.create(
        project=test_project, machine_code="PN001", machine_name="测试机台", stage="S5"
    )
    db_session.commit()
    return machine


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = UserFactory.create(username="testuser", real_name="测试用户")
    db_session.commit()
    return user


@pytest.fixture
def test_acceptance_order(db_session: Session, test_project, test_machine, test_user):
    """创建测试验收单"""
    order = AcceptanceOrderFactory.create(
        project=test_project,
        machine=test_machine,
        acceptance_type="FAT",
        order_no="FAT-P2025001-M01-001",
        status="IN_PROGRESS",
        engineer_id=test_user.id,
    )
    db_session.commit()
    return order
