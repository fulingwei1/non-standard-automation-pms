# -*- coding: utf-8 -*-
"""
PERM-17: 采购/供应链域数据权限过滤挂载 回归测试

覆盖新挂载数据权限过滤的列表端点：
- app.api.v1.endpoints.purchase.requests_refactored.list_purchase_requests
- app.api.v1.endpoints.purchase.receipts.list_goods_receipts
- app.api.v1.endpoints.outsourcing.orders.read_outsourcing_orders

验证：
1. ALL 权限范围 / 超级用户可看到全部记录（不受过滤影响）
2. OWN 权限范围仅能看到自己拥有的记录（owner_field / additional_owner_fields 命中的行）
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.common.pagination import PaginationParams

# 使用大偏移量的 owner id，避免与其他测试/初始化种子数据的 id 冲突
OWNER_A = 900001
OWNER_B = 900002
OTHER_APPROVER = 900003


def _own_scope_patch():
    return patch(
        "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope",
        return_value="OWN",
    )


def _make_user(user_id: int, is_superuser: bool = False) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    return user


def _pagination() -> PaginationParams:
    return PaginationParams(page=1, page_size=50, offset=0, limit=50)


class TestPurchaseRequestsDataScope:
    """采购申请列表数据权限过滤"""

    def test_all_scope_sees_everything(self, db_session: Session):
        from app.api.v1.endpoints.purchase.requests_refactored import list_purchase_requests
        from app.models.purchase import PurchaseRequest

        owned = PurchaseRequest(
            request_no="PR-SCOPE-TEST-OWNED-1",
            created_by=OWNER_A,
            status="DRAFT",
            total_amount=0,
        )
        other = PurchaseRequest(
            request_no="PR-SCOPE-TEST-OTHER-1",
            created_by=OWNER_B,
            status="DRAFT",
            total_amount=0,
        )
        db_session.add_all([owned, other])
        db_session.commit()

        superuser = _make_user(1, is_superuser=True)
        result = list_purchase_requests(
            db=db_session, pagination=_pagination(), status=None, current_user=superuser
        )
        returned_ids = {item["id"] for item in result.items}

        assert owned.id in returned_ids
        assert other.id in returned_ids

    def test_own_scope_sees_only_own_rows(self, db_session: Session):
        from app.api.v1.endpoints.purchase.requests_refactored import list_purchase_requests
        from app.models.purchase import PurchaseRequest

        owned_by_created = PurchaseRequest(
            request_no="PR-SCOPE-TEST-OWNED-2",
            created_by=OWNER_A,
            status="DRAFT",
            total_amount=0,
        )
        owned_by_requested = PurchaseRequest(
            request_no="PR-SCOPE-TEST-OWNED-3",
            created_by=OWNER_B,
            requested_by=OWNER_A,
            status="DRAFT",
            total_amount=0,
        )
        other = PurchaseRequest(
            request_no="PR-SCOPE-TEST-OTHER-2",
            created_by=OWNER_B,
            status="DRAFT",
            total_amount=0,
        )
        db_session.add_all([owned_by_created, owned_by_requested, other])
        db_session.commit()

        user_a = _make_user(OWNER_A, is_superuser=False)
        with _own_scope_patch():
            result = list_purchase_requests(
                db=db_session, pagination=_pagination(), status=None, current_user=user_a
            )
        returned_ids = {item["id"] for item in result.items}

        assert owned_by_created.id in returned_ids
        assert owned_by_requested.id in returned_ids
        assert other.id not in returned_ids


class TestGoodsReceiptsDataScope:
    """收货单列表数据权限过滤"""

    def test_all_scope_sees_everything(self, db_session: Session):
        from app.api.v1.endpoints.purchase.receipts import list_goods_receipts
        from app.models.purchase import GoodsReceipt

        owned = GoodsReceipt(
            receipt_no="GR-SCOPE-TEST-OWNED-1",
            order_id=1,
            supplier_id=1,
            receipt_date=date.today(),
            created_by=OWNER_A,
        )
        other = GoodsReceipt(
            receipt_no="GR-SCOPE-TEST-OTHER-1",
            order_id=1,
            supplier_id=1,
            receipt_date=date.today(),
            created_by=OWNER_B,
        )
        db_session.add_all([owned, other])
        db_session.commit()

        superuser = _make_user(1, is_superuser=True)
        result = list_goods_receipts(
            order_id=None, status=None, db=db_session, pagination=_pagination(), current_user=superuser
        )
        returned_ids = {item["id"] for item in result["items"]}

        assert owned.id in returned_ids
        assert other.id in returned_ids

    def test_own_scope_sees_only_own_rows(self, db_session: Session):
        from app.api.v1.endpoints.purchase.receipts import list_goods_receipts
        from app.models.purchase import GoodsReceipt

        owned_by_created = GoodsReceipt(
            receipt_no="GR-SCOPE-TEST-OWNED-2",
            order_id=1,
            supplier_id=1,
            receipt_date=date.today(),
            created_by=OWNER_A,
        )
        owned_by_inspector = GoodsReceipt(
            receipt_no="GR-SCOPE-TEST-OWNED-3",
            order_id=1,
            supplier_id=1,
            receipt_date=date.today(),
            created_by=OWNER_B,
            inspected_by=OWNER_A,
        )
        other = GoodsReceipt(
            receipt_no="GR-SCOPE-TEST-OTHER-2",
            order_id=1,
            supplier_id=1,
            receipt_date=date.today(),
            created_by=OWNER_B,
        )
        db_session.add_all([owned_by_created, owned_by_inspector, other])
        db_session.commit()

        user_a = _make_user(OWNER_A, is_superuser=False)
        with _own_scope_patch():
            result = list_goods_receipts(
                order_id=None, status=None, db=db_session, pagination=_pagination(), current_user=user_a
            )
        returned_ids = {item["id"] for item in result["items"]}

        assert owned_by_created.id in returned_ids
        assert owned_by_inspector.id in returned_ids
        assert other.id not in returned_ids


class TestOutsourcingOrdersDataScope:
    """外协订单列表数据权限过滤"""

    def test_all_scope_sees_everything(self, db_session: Session):
        from app.api.v1.endpoints.outsourcing.orders import read_outsourcing_orders
        from app.models.outsourcing import OutsourcingOrder

        owned = OutsourcingOrder(
            order_no="OS-SCOPE-TEST-OWNED-1",
            vendor_id=1,
            project_id=1,
            order_type="NORMAL",
            order_title="scope-test-owned-1",
            created_by=OWNER_A,
        )
        other = OutsourcingOrder(
            order_no="OS-SCOPE-TEST-OTHER-1",
            vendor_id=1,
            project_id=1,
            order_type="NORMAL",
            order_title="scope-test-other-1",
            created_by=OWNER_B,
        )
        db_session.add_all([owned, other])
        db_session.commit()

        superuser = _make_user(1, is_superuser=True)
        result = read_outsourcing_orders(
            db=db_session,
            pagination=_pagination(),
            keyword=None,
            vendor_id=None,
            project_id=None,
            order_type=None,
            status=None,
            current_user=superuser,
        )
        returned_ids = {item.id for item in result["items"]}

        assert owned.id in returned_ids
        assert other.id in returned_ids

    def test_own_scope_sees_only_own_rows(self, db_session: Session):
        from app.api.v1.endpoints.outsourcing.orders import read_outsourcing_orders
        from app.models.outsourcing import OutsourcingOrder

        owned = OutsourcingOrder(
            order_no="OS-SCOPE-TEST-OWNED-2",
            vendor_id=1,
            project_id=1,
            order_type="NORMAL",
            order_title="scope-test-owned-2",
            created_by=OWNER_A,
        )
        other = OutsourcingOrder(
            order_no="OS-SCOPE-TEST-OTHER-2",
            vendor_id=1,
            project_id=1,
            order_type="NORMAL",
            order_title="scope-test-other-2",
            created_by=OWNER_B,
        )
        db_session.add_all([owned, other])
        db_session.commit()

        user_a = _make_user(OWNER_A, is_superuser=False)
        with _own_scope_patch():
            result = read_outsourcing_orders(
                db=db_session,
                pagination=_pagination(),
                keyword=None,
                vendor_id=None,
                project_id=None,
                order_type=None,
                status=None,
                current_user=user_a,
            )
        returned_ids = {item.id for item in result["items"]}

        assert owned.id in returned_ids
        assert other.id not in returned_ids
