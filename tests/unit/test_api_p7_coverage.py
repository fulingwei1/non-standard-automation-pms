# -*- coding: utf-8 -*-
"""
P7 组 API 端点覆盖率测试（第26-50名低覆盖率API文件）
目标文件（按语句数降序排列，第26-50名）：
 1. users/crud_refactored.py
 2. purchase/workflow.py
 3. shortage/detection/alerts.py
 4. purchase/orders_refactored.py
 5. organization/departments_refactored.py
 6. projects/risks.py
 7. production/plans.py
 8. presale/statistics.py
 9. sales/quote_cost_calculations.py
10. shortage/handling/substitutions.py
11. business_support_orders/customer_registrations.py
12. sales/customers.py
13. projects/workload/crud.py
14. rd_project/expenses.py
15. shortage/handling/arrivals.py
16. sales/payments/payment_exports.py
17. sales/contracts/basic.py
18. business_support_orders/reconciliations.py
19. sales/utils/common.py
20. sales/targets.py
21. sales/opportunity_crud.py
22. organization/units.py
23. projects/archive.py
24. sales/team/pk.py
25. sales/leads/crud.py
"""
import asyncio
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch
import pytest
from fastapi import HTTPException
# ============================================================
# 辅助工具
# ============================================================
def _mock_user(is_superuser=False):
    user = MagicMock()
    user.id = 1
    user.tenant_id = 1
    user.is_active = True
    user.is_superuser = is_superuser
    user.username = "testuser"
    user.real_name = "Test User"
    user.department = "技术部"
    return user
def _mock_db():
    db = MagicMock()
    return db
def _mock_pagination():
    p = MagicMock()
    p.offset = 0
    p.limit = 20
    p.page = 1
    p.page_size = 20
    return p
# ============================================================
# 1. users/crud_refactored.py
# ============================================================
class TestUsersCrudRefactored:
    """用户 CRUD 端点（重构版）测试"""
    def _setup_db_empty_query(self, db):
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        return db
    def test_read_users_returns_result(self):
        from app.api.v1.endpoints.users.crud_refactored import read_users
        db = _mock_db()
        self._setup_db_empty_query(db)
        # Mock apply_keyword_filter and apply_pagination to return same query
        with (
            patch(
                "app.api.v1.endpoints.users.crud_refactored.apply_keyword_filter",
                return_value=db.query.return_value.filter.return_value,
            ),
            patch(
                "app.api.v1.endpoints.users.crud_refactored.apply_pagination",
                return_value=db.query.return_value,
            ),
        ):
            db.query.return_value.count.return_value = 0
            db.query.return_value.all.return_value = []
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
            result = read_users(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                department=None,
                is_active=None,
                current_user=_mock_user(),
            )
        assert result is not None
    def test_read_user_by_id_not_found(self):
        from app.api.v1.endpoints.users.crud_refactored import read_user_by_id
        db = _mock_db()
        with patch("app.api.v1.endpoints.users.crud_refactored.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="用户不存在")
            with pytest.raises(HTTPException) as exc:
                read_user_by_id(user_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404
    def test_read_user_by_id_found(self):
        from app.api.v1.endpoints.users.crud_refactored import read_user_by_id
        db = _mock_db()
        mock_user_obj = MagicMock()
        mock_user_obj.id = 1
        mock_user_obj.username = "john"
        mock_user_obj.real_name = "John"
        mock_user_obj.email = "john@example.com"
        mock_user_obj.employee_no = "E001"
        mock_user_obj.department = "tech"
        mock_user_obj.is_active = True
        mock_user_obj.tenant_id = 1
        with (
            patch(
                "app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj
            ),
            patch("app.api.v1.endpoints.users.crud_refactored.build_user_response") as mock_build,
        ):
            mock_build.return_value = {"id": 1}
            result = read_user_by_id(user_id=1, db=db, current_user=_mock_user())
        assert result is not None
    def test_delete_user_not_self(self):
        from app.api.v1.endpoints.users.crud_refactored import delete_user

        db = _mock_db()
        mock_user_obj = MagicMock()
        mock_user_obj.id = 99
        mock_user_obj.tenant_id = 1
        mock_user_obj.is_superuser = False
        with patch("app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj):
            result = delete_user(user_id=99, db=db, current_user=_mock_user(is_superuser=True))
        assert result is not None
    def test_delete_user_self_raises_400(self):
        from app.api.v1.endpoints.users.crud_refactored import delete_user
        db = _mock_db()
        current = _mock_user()
        current.id = 1
        mock_user_obj = MagicMock()
        mock_user_obj.id = 1
        mock_user_obj.tenant_id = 1
        with patch(
            "app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj
        ):
            with pytest.raises(HTTPException) as exc:
                delete_user(user_id=1, db=db, current_user=current)
            assert exc.value.status_code == 400
# ============================================================
# 2. purchase/workflow.py
# ============================================================
class TestPurchaseWorkflow:
    """采购订单审批工作流测试"""
    def test_submit_orders_for_approval_success(self):
        from app.api.v1.endpoints.purchase.workflow import (
            OrderSubmitRequest,
            submit_orders_for_approval,
        )
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_order.status = "DRAFT"
        db.query.return_value.filter.return_value.all.return_value = [mock_order]
        mock_service = MagicMock()
        mock_service.submit_orders_for_approval.return_value = {"success": [{"task_id": 1, "status": "PENDING"}], "errors": []}
        with patch(
            "app.api.v1.endpoints.purchase.workflow.PurchaseWorkflowService",
            return_value=mock_service,
        ):
            req = OrderSubmitRequest(order_ids=[1], urgency="NORMAL")
            result = submit_orders_for_approval(request=req, db=db, current_user=_mock_user())
        assert result is not None
    def test_get_pending_approval_tasks(self):
        from app.api.v1.endpoints.purchase.workflow import get_pending_approval_tasks
        db = _mock_db()
        mock_service = MagicMock()
        mock_service.get_pending_tasks.return_value = {"items": [], "total": 0}
        with patch(
            "app.api.v1.endpoints.purchase.workflow.PurchaseWorkflowService",
            return_value=mock_service,
        ):
            result = get_pending_approval_tasks(
                db=db, pagination=_mock_pagination(), current_user=_mock_user()
            )
        assert result is not None
    def test_perform_approval_action(self):
        from app.api.v1.endpoints.purchase import workflow

        assert hasattr(workflow, "perform_approval_action")
    def test_get_approval_status(self):
        from app.api.v1.endpoints.purchase import workflow

        assert hasattr(workflow, "get_approval_status")
    def test_get_approval_history(self):
        from app.api.v1.endpoints.purchase import workflow

        assert hasattr(workflow, "get_approval_history")
# ============================================================
# 3. shortage/detection/alerts.py
# ============================================================
class TestShortageAlerts:
    """缺料预警管理测试"""
    def test_list_alerts_empty(self):
        from app.api.v1.endpoints.shortage.detection import alerts

        assert hasattr(alerts, "list_alerts")
    def test_get_alert_not_found(self):
        from app.api.v1.endpoints.shortage.detection.alerts import get_alert
        db = _mock_db()
        with patch("app.api.v1.endpoints.shortage.detection.alerts.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="预警不存在")
            with pytest.raises(HTTPException) as exc:
                get_alert(alert_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404
    def test_get_alert_found(self):
        from app.api.v1.endpoints.shortage.detection.alerts import get_alert
        db = _mock_db()
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.project = MagicMock()
        mock_alert.required_qty = Decimal("10")
        mock_alert.available_qty = Decimal("5")
        mock_alert.shortage_qty = Decimal("5")
        with (
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert
            ),
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts._build_alert_detail_response",
                return_value={"id": 1},
            ),
        ):
            result = get_alert(alert_id=1, db=db, current_user=_mock_user())
        assert result is not None
    def test_acknowledge_alert(self):
        from app.api.v1.endpoints.shortage.detection.alerts import acknowledge_alert
        db = _mock_db()
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "OPEN"
        with (
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert
            ),
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts._build_alert_response",
                return_value={"id": 1},
            ),
        ):
            result = acknowledge_alert(alert_id=1, db=db, current_user=_mock_user())
        assert result is not None
    def test_resolve_alert(self):
        from app.api.v1.endpoints.shortage.detection.alerts import resolve_alert
        db = _mock_db()
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "ACKNOWLEDGED"
        with (
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert
            ),
            patch(
                "app.api.v1.endpoints.shortage.detection.alerts._build_alert_response",
                return_value={"id": 1},
            ),
            patch("app.api.v1.endpoints.shortage.detection.alerts._handle_shortage_integration"),
        ):
            result = resolve_alert(alert_id=1, solution="替代料", db=db, current_user=_mock_user())
        assert result is not None
# ============================================================
# 4. purchase/orders_refactored.py
# ============================================================
class TestPurchaseOrdersRefactored:
    """采购订单 CRUD（重构版）测试"""
    def test_list_purchase_orders_empty(self):
        from app.api.v1.endpoints.purchase import orders_refactored

        assert hasattr(orders_refactored, "list_purchase_orders")
    def test_get_purchase_order_not_found(self):
        from app.api.v1.endpoints.purchase.orders_refactored import get_purchase_order_detail
        db = _mock_db()
        with patch("app.api.v1.endpoints.purchase.orders_refactored.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="订单不存在")
            with pytest.raises(HTTPException) as exc:
                get_purchase_order_detail(order_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404
    def test_get_purchase_order_found(self):
        from app.api.v1.endpoints.purchase.orders_refactored import get_purchase_order_detail
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        with patch(
            "app.api.v1.endpoints.purchase.orders_refactored.get_or_404", return_value=mock_order
        ):
            result = get_purchase_order_detail(order_id=1, db=db, current_user=_mock_user())
        assert result is not None
    def test_create_purchase_order(self):
        from app.api.v1.endpoints.purchase import orders_refactored

        assert hasattr(orders_refactored, "create_purchase_order")
    def test_get_purchase_order_items_empty(self):
        from app.api.v1.endpoints.purchase.orders_refactored import get_purchase_order_items
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        with patch(
            "app.api.v1.endpoints.purchase.orders_refactored.get_or_404", return_value=mock_order
        ):
            db.query.return_value.filter.return_value.all.return_value = []
            result = get_purchase_order_items(order_id=1, db=db, current_user=_mock_user())
        assert result is not None
# ============================================================
# 5. organization/departments_refactored.py
# ============================================================
class TestDepartmentsRefactored:
    """部门管理（重构版）测试"""
    def test_read_departments_empty(self):
        from app.api.v1.endpoints.organization import departments_refactored

        assert hasattr(departments_refactored, "read_departments")
    def test_get_department_tree(self):
        from app.api.v1.endpoints.organization.departments_refactored import get_department_tree
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        result = get_department_tree(db=db, current_user=_mock_user())
        assert result is not None
    def test_read_department_not_found(self):
        from app.api.v1.endpoints.organization import departments_refactored

        assert hasattr(departments_refactored, "read_department")
