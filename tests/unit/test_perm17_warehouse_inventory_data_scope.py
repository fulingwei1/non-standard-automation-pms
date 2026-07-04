# -*- coding: utf-8 -*-
"""
PERM-17: 仓储/库存域数据权限过滤挂载 回归测试

覆盖:
- app/api/v1/endpoints/warehouse/crud.py::list_inbound (InboundOrder)
- app/api/v1/endpoints/warehouse/count.py::list_count_orders (StockCountOrder)
- app/services/stock_count_service.py::StockCountService.get_count_tasks (StockCountTask)

验证:
1. ALL 范围（超级管理员）能看到全部记录，不受创建人限制。
2. OWN 范围（默认无角色用户）只能看到自己创建/参与的记录。
"""
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.inventory_tracking import StockCountTask
from app.models.user import User
from app.models.warehouse import InboundOrder, StockCountOrder


def _make_user(db: Session, *, is_superuser: bool) -> User:
    suffix = uuid4().hex[:10]
    user = User(
        username=f"perm17-{suffix}",
        password_hash="x",
        real_name=f"perm17-{suffix}",
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestInboundOrderDataScope:
    """warehouse/crud.py::list_inbound 数据权限过滤"""

    def test_all_scope_sees_every_order(self, db_session: Session):
        from app.api.v1.endpoints.warehouse.crud import list_inbound

        owner = _make_user(db_session, is_superuser=False)
        other = _make_user(db_session, is_superuser=False)
        admin = _make_user(db_session, is_superuser=True)

        suffix = uuid4().hex[:8]
        db_session.add(
            InboundOrder(
                order_no=f"IN-{suffix}-A",
                order_type="PURCHASE",
                status="DRAFT",
                created_by=owner.id,
            )
        )
        db_session.add(
            InboundOrder(
                order_no=f"IN-{suffix}-B",
                order_type="PURCHASE",
                status="DRAFT",
                created_by=other.id,
            )
        )
        db_session.commit()

        result = list_inbound(
            status=None,
            order_type=None,
            keyword=f"IN-{suffix}",
            page=1,
            page_size=50,
            db=db_session,
            current_user=admin,
        )

        assert result["total"] == 2

    def test_own_scope_only_sees_own_orders(self, db_session: Session):
        from app.api.v1.endpoints.warehouse.crud import list_inbound

        owner = _make_user(db_session, is_superuser=False)
        other = _make_user(db_session, is_superuser=False)

        suffix = uuid4().hex[:8]
        db_session.add(
            InboundOrder(
                order_no=f"IN-{suffix}-A",
                order_type="PURCHASE",
                status="DRAFT",
                created_by=owner.id,
            )
        )
        db_session.add(
            InboundOrder(
                order_no=f"IN-{suffix}-B",
                order_type="PURCHASE",
                status="DRAFT",
                created_by=other.id,
            )
        )
        db_session.commit()

        # owner has no roles assigned -> UserScopeService defaults to OWN scope
        result = list_inbound(
            status=None,
            order_type=None,
            keyword=f"IN-{suffix}",
            page=1,
            page_size=50,
            db=db_session,
            current_user=owner,
        )

        assert result["total"] == 1
        assert result["items"][0]["order_no"] == f"IN-{suffix}-A"


class TestStockCountOrderDataScope:
    """warehouse/count.py::list_count_orders 数据权限过滤"""

    def test_own_scope_only_sees_own_count_orders(self, db_session: Session):
        from app.api.v1.endpoints.warehouse.count import list_count_orders

        owner = _make_user(db_session, is_superuser=False)
        other = _make_user(db_session, is_superuser=False)
        admin = _make_user(db_session, is_superuser=True)

        suffix = uuid4().hex[:8]
        db_session.add(
            StockCountOrder(
                count_no=f"SC-{suffix}-A",
                count_type="FULL",
                status="DRAFT",
                created_by=owner.id,
            )
        )
        db_session.add(
            StockCountOrder(
                count_no=f"SC-{suffix}-B",
                count_type="FULL",
                status="DRAFT",
                created_by=other.id,
            )
        )
        db_session.commit()

        admin_result = list_count_orders(
            status=None, page=1, page_size=50, db=db_session, current_user=admin
        )
        owner_ids = {
            o.count_no
            for o in db_session.query(StockCountOrder).filter(
                StockCountOrder.count_no.like(f"SC-{suffix}-%")
            )
        }
        assert len(owner_ids) == 2

        owner_result = list_count_orders(
            status=None, page=1, page_size=50, db=db_session, current_user=owner
        )
        owner_items = [
            i for i in owner_result["items"] if i["count_no"].startswith(f"SC-{suffix}-")
        ]
        assert len(owner_items) == 1
        assert owner_items[0]["count_no"] == f"SC-{suffix}-A"

        admin_items = [
            i for i in admin_result["items"] if i["count_no"].startswith(f"SC-{suffix}-")
        ]
        assert len(admin_items) == 2


class TestStockCountTaskDataScope:
    """stock_count_service.py::StockCountService.get_count_tasks 数据权限过滤"""

    def test_all_scope_and_own_scope(self, db_session: Session):
        import datetime

        from app.services.stock_count_service import StockCountService

        owner = _make_user(db_session, is_superuser=False)
        other = _make_user(db_session, is_superuser=False)
        admin = _make_user(db_session, is_superuser=True)

        tenant_id = 999999
        suffix = uuid4().hex[:10]

        task_owner = StockCountTask(
            tenant_id=tenant_id,
            task_no=f"CNT-{suffix}-A",
            count_type="FULL",
            count_date=datetime.date.today(),
            status="PENDING",
            created_by=owner.id,
        )
        task_other = StockCountTask(
            tenant_id=tenant_id,
            task_no=f"CNT-{suffix}-B",
            count_type="FULL",
            count_date=datetime.date.today(),
            status="PENDING",
            created_by=other.id,
        )
        db_session.add(task_owner)
        db_session.add(task_other)
        db_session.commit()
        db_session.refresh(task_owner)
        db_session.refresh(task_other)

        service = StockCountService(db_session, tenant_id=tenant_id)

        # Without current_user: legacy behaviour, no filtering
        legacy = service.get_count_tasks()
        legacy_ids = {t.id for t in legacy}
        assert {task_owner.id, task_other.id} <= legacy_ids

        # ALL scope (superuser) sees both
        all_scope = service.get_count_tasks(current_user=admin)
        all_ids = {t.id for t in all_scope}
        assert {task_owner.id, task_other.id} <= all_ids

        # OWN scope (no roles) only sees own task
        own_scope = service.get_count_tasks(current_user=owner)
        own_ids = {t.id for t in own_scope}
        assert task_owner.id in own_ids
        assert task_other.id not in own_ids
