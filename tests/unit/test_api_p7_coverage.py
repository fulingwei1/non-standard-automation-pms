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
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException
from decimal import Decimal
from datetime import date, datetime


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
    return p


# ============================================================
# 1. users/crud_refactored.py
# ============================================================

class TestUsersCrudRefactored:
    """用户 CRUD 端点（重构版）测试"""

    def _setup_db_empty_query(self, db):
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.order_by.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        return db

    def test_read_users_returns_result(self):
        from app.api.v1.endpoints.users.crud_refactored import read_users
        db = _mock_db()
        self._setup_db_empty_query(db)
        # Mock apply_keyword_filter and apply_pagination to return same query
        with patch("app.api.v1.endpoints.users.crud_refactored.apply_keyword_filter", return_value=db.query.return_value.filter.return_value), \
             patch("app.api.v1.endpoints.users.crud_refactored.apply_pagination", return_value=db.query.return_value):
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
        with patch("app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj), \
             patch("app.api.v1.endpoints.users.crud_refactored.build_user_response") as mock_build:
            mock_build.return_value = {"id": 1}
            result = read_user_by_id(user_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_delete_user_not_self(self):
        from app.api.v1.endpoints.users.crud_refactored import delete_user
        db = _mock_db()
        mock_user_obj = MagicMock()
        mock_user_obj.id = 99
        with patch("app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj), \
             patch("app.api.v1.endpoints.users.crud_refactored.delete_obj"):
            result = delete_user(user_id=99, db=db, current_user=_mock_user(is_superuser=True))
        assert result is not None

    def test_delete_user_self_raises_400(self):
        from app.api.v1.endpoints.users.crud_refactored import delete_user
        db = _mock_db()
        current = _mock_user()
        current.id = 1
        mock_user_obj = MagicMock()
        mock_user_obj.id = 1
        with patch("app.api.v1.endpoints.users.crud_refactored.get_or_404", return_value=mock_user_obj):
            with pytest.raises(HTTPException) as exc:
                delete_user(user_id=1, db=db, current_user=current)
            assert exc.value.status_code == 400


# ============================================================
# 2. purchase/workflow.py
# ============================================================

class TestPurchaseWorkflow:
    """采购订单审批工作流测试"""

    def test_submit_orders_for_approval_success(self):
        from app.api.v1.endpoints.purchase.workflow import submit_orders_for_approval, PurchaseOrderSubmitRequest
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_no = "PO001"
        mock_order.status = "DRAFT"
        db.query.return_value.filter.return_value.all.return_value = [mock_order]

        mock_service = MagicMock()
        mock_service.submit_for_approval.return_value = {"task_id": 1, "status": "PENDING"}
        with patch("app.api.v1.endpoints.purchase.workflow.ApprovalEngineService", return_value=mock_service):
            req = PurchaseOrderSubmitRequest(order_ids=[1], urgency="NORMAL")
            result = submit_orders_for_approval(request=req, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_pending_approval_tasks(self):
        from app.api.v1.endpoints.purchase.workflow import get_pending_approval_tasks
        db = _mock_db()
        mock_service = MagicMock()
        mock_service.get_pending_tasks.return_value = {"items": [], "total": 0}
        with patch("app.api.v1.endpoints.purchase.workflow.ApprovalEngineService", return_value=mock_service):
            result = get_pending_approval_tasks(
                db=db,
                pagination=_mock_pagination(),
                current_user=_mock_user()
            )
        assert result is not None

    def test_perform_approval_action(self):
        from app.api.v1.endpoints.purchase.workflow import perform_approval_action, ApprovalActionRequest
        db = _mock_db()
        mock_service = MagicMock()
        mock_service.perform_action.return_value = {"success": True}
        with patch("app.api.v1.endpoints.purchase.workflow.ApprovalEngineService", return_value=mock_service):
            req = ApprovalActionRequest(task_id=1, action="approve", comment="OK")
            result = perform_approval_action(request=req, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_approval_status(self):
        from app.api.v1.endpoints.purchase.workflow import get_approval_status
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.status = "PENDING"
        with patch("app.api.v1.endpoints.purchase.workflow.get_or_404", return_value=mock_order):
            mock_service = MagicMock()
            mock_service.get_approval_status.return_value = {"status": "PENDING"}
            with patch("app.api.v1.endpoints.purchase.workflow.ApprovalEngineService", return_value=mock_service):
                result = get_approval_status(order_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_approval_history(self):
        from app.api.v1.endpoints.purchase.workflow import get_approval_history
        db = _mock_db()
        mock_service = MagicMock()
        mock_service.get_history.return_value = {"items": [], "total": 0}
        with patch("app.api.v1.endpoints.purchase.workflow.ApprovalEngineService", return_value=mock_service):
            result = get_approval_history(
                order_id=1, db=db, current_user=_mock_user()
            )
        assert result is not None


# ============================================================
# 3. shortage/detection/alerts.py
# ============================================================

class TestShortageAlerts:
    """缺料预警管理测试"""

    def test_list_alerts_empty(self):
        from app.api.v1.endpoints.shortage.detection.alerts import list_alerts
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.shortage.detection.alerts.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = list_alerts(
                db=db,
                pagination=_mock_pagination(),
                status=None,
                alert_level=None,
                project_id=None,
                current_user=_mock_user(),
            )
        assert result is not None

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
        with patch("app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert), \
             patch("app.api.v1.endpoints.shortage.detection.alerts._build_alert_detail_response", return_value={"id": 1}):
            result = get_alert(alert_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_acknowledge_alert(self):
        from app.api.v1.endpoints.shortage.detection.alerts import acknowledge_alert
        db = _mock_db()
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "OPEN"
        with patch("app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert), \
             patch("app.api.v1.endpoints.shortage.detection.alerts._build_alert_response", return_value={"id": 1}):
            result = acknowledge_alert(alert_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_resolve_alert(self):
        from app.api.v1.endpoints.shortage.detection.alerts import resolve_alert
        db = _mock_db()
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.status = "ACKNOWLEDGED"
        with patch("app.api.v1.endpoints.shortage.detection.alerts.get_or_404", return_value=mock_alert), \
             patch("app.api.v1.endpoints.shortage.detection.alerts._build_alert_response", return_value={"id": 1}), \
             patch("app.api.v1.endpoints.shortage.detection.alerts._handle_shortage_integration"):
            result = resolve_alert(alert_id=1, solution="替代料", db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 4. purchase/orders_refactored.py
# ============================================================

class TestPurchaseOrdersRefactored:
    """采购订单 CRUD（重构版）测试"""

    def test_list_purchase_orders_empty(self):
        from app.api.v1.endpoints.purchase.orders_refactored import list_purchase_orders
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.purchase.orders_refactored.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = list_purchase_orders(
                db=db,
                pagination=_mock_pagination(),
                status=None,
                supplier_id=None,
                current_user=_mock_user(),
            )
        assert result is not None

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
        with patch("app.api.v1.endpoints.purchase.orders_refactored.get_or_404", return_value=mock_order):
            result = get_purchase_order_detail(order_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_create_purchase_order(self):
        from app.api.v1.endpoints.purchase.orders_refactored import create_purchase_order
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.items = []
        mock_schema.supplier_id = 1
        mock_schema.project_id = None
        with patch("app.api.v1.endpoints.purchase.orders_refactored.save_obj") as mock_save, \
             patch("app.api.v1.endpoints.purchase.orders_refactored.generate_order_no", return_value="PO-001"):
            result = create_purchase_order(order_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_purchase_order_items_empty(self):
        from app.api.v1.endpoints.purchase.orders_refactored import get_purchase_order_items
        db = _mock_db()
        mock_order = MagicMock()
        mock_order.id = 1
        with patch("app.api.v1.endpoints.purchase.orders_refactored.get_or_404", return_value=mock_order):
            db.query.return_value.filter.return_value.all.return_value = []
            result = get_purchase_order_items(order_id=1, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 5. organization/departments_refactored.py
# ============================================================

class TestDepartmentsRefactored:
    """部门管理（重构版）测试"""

    def test_read_departments_empty(self):
        from app.api.v1.endpoints.organization.departments_refactored import read_departments
        db = _mock_db()
        db.query.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        with patch("app.api.v1.endpoints.organization.departments_refactored.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = read_departments(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                is_active=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_department_tree(self):
        from app.api.v1.endpoints.organization.departments_refactored import get_department_tree
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        result = get_department_tree(db=db, current_user=_mock_user())
        assert result is not None

    def test_read_department_not_found(self):
        from app.api.v1.endpoints.organization.departments_refactored import read_department
        db = _mock_db()
        with patch("app.api.v1.endpoints.organization.departments_refactored.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="部门不存在")
            with pytest.raises(HTTPException) as exc:
                read_department(dept_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_department(self):
        from app.api.v1.endpoints.organization.departments_refactored import create_department
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.dept_code = "D001"
        mock_schema.parent_id = None
        db.query.return_value.filter.return_value.first.return_value = None
        with patch("app.api.v1.endpoints.organization.departments_refactored.save_obj") as mock_save:
            mock_save.return_value = MagicMock(id=1)
            result = create_department(dept_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_department_statistics(self):
        from app.api.v1.endpoints.organization.departments_refactored import get_department_statistics
        db = _mock_db()
        db.query.return_value.count.return_value = 5
        db.query.return_value.filter.return_value.count.return_value = 3
        result = get_department_statistics(db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 6. projects/risks.py
# ============================================================

class TestProjectRisks:
    """项目风险管理测试"""

    def test_get_risks_empty(self):
        from app.api.v1.endpoints.projects.risks import get_risks
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.projects.risks.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = get_risks(
                project_id=1,
                db=db,
                pagination=_mock_pagination(),
                risk_type=None,
                status=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_risk_not_found(self):
        from app.api.v1.endpoints.projects.risks import get_risk
        db = _mock_db()
        with patch("app.api.v1.endpoints.projects.risks.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="风险不存在")
            with pytest.raises(HTTPException) as exc:
                get_risk(project_id=1, risk_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_risk(self):
        from app.api.v1.endpoints.projects.risks import create_risk
        db = _mock_db()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_schema = MagicMock()
        with patch("app.api.v1.endpoints.projects.risks.get_or_404", return_value=mock_project), \
             patch("app.api.v1.endpoints.projects.risks.save_obj") as mock_save:
            mock_save.return_value = MagicMock(id=1)
            result = create_risk(project_id=1, risk_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_delete_risk(self):
        from app.api.v1.endpoints.projects.risks import delete_risk
        db = _mock_db()
        mock_risk = MagicMock()
        mock_risk.id = 1
        mock_risk.project_id = 1
        with patch("app.api.v1.endpoints.projects.risks.get_or_404", return_value=mock_risk), \
             patch("app.api.v1.endpoints.projects.risks.delete_obj"):
            result = delete_risk(project_id=1, risk_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_risk_matrix(self):
        from app.api.v1.endpoints.projects.risks import get_risk_matrix
        db = _mock_db()
        mock_project = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        with patch("app.api.v1.endpoints.projects.risks.get_or_404", return_value=mock_project):
            result = get_risk_matrix(project_id=1, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 7. production/plans.py
# ============================================================

class TestProductionPlans:
    """生产计划管理测试"""

    def test_read_production_plans_empty(self):
        from app.api.v1.endpoints.production.plans import read_production_plans
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.production.plans.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = read_production_plans(
                db=db,
                pagination=_mock_pagination(),
                plan_type=None,
                project_id=None,
                workshop_id=None,
                status=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_read_production_plan_not_found(self):
        from app.api.v1.endpoints.production.plans import read_production_plan
        db = _mock_db()
        with patch("app.api.v1.endpoints.production.plans.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="计划不存在")
            with pytest.raises(HTTPException) as exc:
                read_production_plan(plan_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_production_plan(self):
        from app.api.v1.endpoints.production.plans import create_production_plan
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.plan_type = "MASTER"
        mock_schema.project_id = None
        with patch("app.api.v1.endpoints.production.plans.save_obj") as mock_save, \
             patch("app.api.v1.endpoints.production.plans.generate_plan_no", return_value="PP-001"):
            mock_save.return_value = MagicMock(id=1)
            result = create_production_plan(plan_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_submit_production_plan_not_found(self):
        from app.api.v1.endpoints.production.plans import submit_production_plan
        db = _mock_db()
        with patch("app.api.v1.endpoints.production.plans.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="计划不存在")
            with pytest.raises(HTTPException) as exc:
                submit_production_plan(plan_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_submit_production_plan_success(self):
        from app.api.v1.endpoints.production.plans import submit_production_plan
        db = _mock_db()
        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.status = "DRAFT"
        with patch("app.api.v1.endpoints.production.plans.get_or_404", return_value=mock_plan), \
             patch("app.api.v1.endpoints.production.plans.save_obj", return_value=mock_plan):
            result = submit_production_plan(plan_id=1, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 8. presale/statistics.py
# ============================================================

class TestPresaleStatistics:
    """售前统计测试"""

    def test_get_workload_stats(self):
        from app.api.v1.endpoints.presale.statistics import get_workload_stats
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_workload_stats(
            start_date=None,
            end_date=None,
            user_id=None,
            db=db,
            current_user=_mock_user(),
        )
        assert result is not None

    def test_get_response_time_stats(self):
        from app.api.v1.endpoints.presale.statistics import get_response_time_stats
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_response_time_stats(
            start_date=None,
            end_date=None,
            db=db,
            current_user=_mock_user(),
        )
        assert result is not None

    def test_get_conversion_stats(self):
        from app.api.v1.endpoints.presale.statistics import get_conversion_stats
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.count.return_value = 0
        result = get_conversion_stats(
            start_date=None,
            end_date=None,
            db=db,
            current_user=_mock_user(),
        )
        assert result is not None

    def test_get_performance_stats(self):
        from app.api.v1.endpoints.presale.statistics import get_performance_stats
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        result = get_performance_stats(
            start_date=None,
            end_date=None,
            db=db,
            current_user=_mock_user(),
        )
        assert result is not None


# ============================================================
# 9. sales/quote_cost_calculations.py
# ============================================================

class TestQuoteCostCalculations:
    """报价成本计算测试"""

    def test_calculate_margin_positive(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import calculate_margin
        result = calculate_margin(Decimal("100"), Decimal("60"))
        assert result == Decimal("40.00")

    def test_calculate_margin_zero_price(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import calculate_margin
        result = calculate_margin(Decimal("0"), Decimal("60"))
        assert result == Decimal("0")

    def test_calculate_markup_positive(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import calculate_markup
        result = calculate_markup(Decimal("100"), Decimal("80"))
        assert result == Decimal("25.00")

    def test_calculate_markup_zero_cost(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import calculate_markup
        result = calculate_markup(Decimal("100"), Decimal("0"))
        assert result == Decimal("0")

    def test_get_cost_calculations_not_found(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import get_cost_calculations
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.quote_cost_calculations.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="报价不存在")
            with pytest.raises(HTTPException) as exc:
                get_cost_calculations(quote_id=999, version_id=None, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_simulate_cost(self):
        from app.api.v1.endpoints.sales.quote_cost_calculations import simulate_cost
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.items = []
        mock_schema.discount_rate = Decimal("0.9")
        result = simulate_cost(simulate_request=mock_schema, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 10. shortage/handling/substitutions.py
# ============================================================

class TestShortageSubstitutions:
    """物料替代测试"""

    def test_list_substitutions_empty(self):
        from app.api.v1.endpoints.shortage.handling.substitutions import list_substitutions
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.shortage.handling.substitutions.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = list_substitutions(
                db=db,
                pagination=_mock_pagination(),
                project_id=None,
                status=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_substitution_not_found(self):
        from app.api.v1.endpoints.shortage.handling.substitutions import get_substitution
        db = _mock_db()
        with patch("app.api.v1.endpoints.shortage.handling.substitutions.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="替代申请不存在")
            with pytest.raises(HTTPException) as exc:
                get_substitution(substitution_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_substitution(self):
        from app.api.v1.endpoints.shortage.handling.substitutions import create_substitution
        db = _mock_db()
        mock_schema = MagicMock()
        with patch("app.api.v1.endpoints.shortage.handling.substitutions._generate_substitution_no", return_value="SUB-001"), \
             patch("app.api.v1.endpoints.shortage.handling.substitutions.save_obj") as mock_save, \
             patch("app.api.v1.endpoints.shortage.handling.substitutions._build_substitution_response", return_value={"id": 1}):
            result = create_substitution(substitution_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_tech_approve_substitution(self):
        from app.api.v1.endpoints.shortage.handling.substitutions import tech_approve_substitution
        db = _mock_db()
        mock_sub = MagicMock()
        mock_sub.id = 1
        mock_sub.status = "PENDING"
        with patch("app.api.v1.endpoints.shortage.handling.substitutions.get_or_404", return_value=mock_sub), \
             patch("app.api.v1.endpoints.shortage.handling.substitutions._build_substitution_response", return_value={"id": 1}):
            result = tech_approve_substitution(substitution_id=1, comment="OK", db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 11. business_support_orders/customer_registrations.py  (async)
# ============================================================

class TestCustomerRegistrations:
    """客户入驻管理测试（async）"""

    def test_get_customer_registrations_empty(self):
        from app.api.v1.endpoints.business_support_orders.customer_registrations import get_customer_registrations
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.business_support_orders.customer_registrations.apply_keyword_filter", return_value=db.query.return_value):
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = asyncio.run(get_customer_registrations(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                registration_type=None,
                status=None,
                current_user=_mock_user(),
            ))
        assert result is not None

    def test_get_customer_registration_not_found(self):
        from app.api.v1.endpoints.business_support_orders.customer_registrations import get_customer_registration
        db = _mock_db()
        with patch("app.api.v1.endpoints.business_support_orders.customer_registrations.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="入驻申请不存在")
            with pytest.raises(HTTPException) as exc:
                asyncio.run(get_customer_registration(registration_id=999, db=db, current_user=_mock_user()))
            assert exc.value.status_code == 404

    def test_create_customer_registration(self):
        from app.api.v1.endpoints.business_support_orders.customer_registrations import create_customer_registration
        db = _mock_db()
        mock_schema = MagicMock()
        with patch("app.api.v1.endpoints.business_support_orders.customer_registrations.generate_registration_no", return_value="REG-001"), \
             patch("app.api.v1.endpoints.business_support_orders.customer_registrations._to_registration_response", return_value={"id": 1}):
            result = asyncio.run(create_customer_registration(
                registration_in=mock_schema, db=db, current_user=_mock_user()
            ))
        assert result is not None

    def test_approve_customer_registration(self):
        from app.api.v1.endpoints.business_support_orders.customer_registrations import approve_customer_registration
        db = _mock_db()
        mock_reg = MagicMock()
        mock_reg.id = 1
        mock_reg.status = "PENDING"
        mock_review = MagicMock()
        with patch("app.api.v1.endpoints.business_support_orders.customer_registrations.get_or_404", return_value=mock_reg), \
             patch("app.api.v1.endpoints.business_support_orders.customer_registrations._to_registration_response", return_value={"id": 1}):
            result = asyncio.run(approve_customer_registration(
                registration_id=1, review_data=mock_review, db=db, current_user=_mock_user()
            ))
        assert result is not None


# ============================================================
# 12. sales/customers.py
# ============================================================

class TestSalesCustomers:
    """客户档案管理测试"""

    def test_read_customers_empty(self):
        from app.api.v1.endpoints.sales.customers import read_customers
        db = _mock_db()
        # customers.py does NOT import apply_pagination; it uses inline pagination
        with patch("app.api.v1.endpoints.sales.customers.apply_keyword_filter", return_value=db.query.return_value), \
             patch("app.api.v1.endpoints.sales.customers.security.filter_sales_data_by_scope", return_value=db.query.return_value):
            db.query.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = read_customers(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                customer_level=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_read_customer_not_found(self):
        from app.api.v1.endpoints.sales.customers import read_customer
        db = _mock_db()
        # read_customer uses inline db.query(...).filter(...).first()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            read_customer(customer_id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_create_customer(self):
        from app.api.v1.endpoints.sales.customers import create_customer
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.customer_name = "Test Corp"
        # Ensure customer_code is falsy so auto-generation is triggered
        mock_schema.customer_code = None
        mock_schema.model_dump.return_value = {"customer_name": "Test Corp", "customer_code": None}
        mock_customer = MagicMock()
        mock_customer.__table__ = MagicMock()
        mock_customer.__table__.columns = []
        mock_customer.sales_owner = None
        with patch("app.api.v1.endpoints.sales.customers.generate_customer_code", return_value="CUS20240101001"), \
             patch("app.api.v1.endpoints.sales.customers.save_obj") as mock_save, \
             patch("app.api.v1.endpoints.sales.customers.Customer", return_value=mock_customer):
            result = create_customer(customer_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_delete_customer_not_found(self):
        from app.api.v1.endpoints.sales.customers import delete_customer
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.customers.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="客户不存在")
            with pytest.raises(HTTPException) as exc:
                delete_customer(customer_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_get_customer_stats(self):
        from app.api.v1.endpoints.sales.customers import get_customer_stats
        db = _mock_db()
        db.query.return_value.count.return_value = 10
        db.query.return_value.filter.return_value.count.return_value = 5
        # scalar() for Decimal values
        db.query.return_value.scalar.return_value = Decimal("0")
        db.query.return_value.filter.return_value.scalar.return_value = Decimal("0")
        with patch("app.api.v1.endpoints.sales.customers.func") as mock_func:
            mock_func.sum.return_value = MagicMock()
            result = get_customer_stats(db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 13. projects/workload/crud.py
# ============================================================

class TestProjectWorkloadCrud:
    """项目工作量 CRUD 测试"""

    def test_calculate_workdays_normal(self):
        from app.api.v1.endpoints.projects.workload.crud import _calculate_workdays
        start = date(2025, 1, 6)   # Monday
        end = date(2025, 1, 10)    # Friday
        result = _calculate_workdays(start, end)
        assert result == 5

    def test_calculate_workdays_zero(self):
        from app.api.v1.endpoints.projects.workload.crud import _calculate_workdays
        start = date(2025, 1, 10)
        end = date(2025, 1, 6)
        result = _calculate_workdays(start, end)
        assert result == 0

    def test_get_project_team_workload_not_found(self):
        from app.api.v1.endpoints.projects.workload.crud import get_project_team_workload
        db = _mock_db()
        with patch("app.api.v1.endpoints.projects.workload.crud.check_project_access_or_raise") as mock_check, \
             patch("app.api.v1.endpoints.projects.workload.crud.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="项目不存在")
            with pytest.raises(HTTPException) as exc:
                get_project_team_workload(project_id=999, start_date=None, end_date=None, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_get_project_workload_gantt(self):
        from app.api.v1.endpoints.projects.workload.crud import get_project_workload_gantt
        db = _mock_db()
        mock_project = MagicMock()
        mock_project.id = 1
        with patch("app.api.v1.endpoints.projects.workload.crud.check_project_access_or_raise"), \
             patch("app.api.v1.endpoints.projects.workload.crud.get_or_404", return_value=mock_project):
            db.query.return_value.filter.return_value.all.return_value = []
            result = get_project_workload_gantt(
                project_id=1, start_date=None, end_date=None, db=db, current_user=_mock_user()
            )
        assert result is not None


# ============================================================
# 14. rd_project/expenses.py
# ============================================================

class TestRdProjectExpenses:
    """研发费用归集测试"""

    def test_get_rd_costs_empty(self):
        from app.api.v1.endpoints.rd_project.expenses import get_rd_costs
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.rd_project.expenses.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = get_rd_costs(
                db=db,
                pagination=_mock_pagination(),
                rd_project_id=None,
                cost_type_id=None,
                start_date=None,
                end_date=None,
                cost_status=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_create_rd_cost(self):
        from app.api.v1.endpoints.rd_project.expenses import create_rd_cost
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.rd_project_id = 1
        mock_schema.cost_type_id = 1
        mock_project = MagicMock()
        mock_cost_type = MagicMock()
        mock_cost = MagicMock()
        with patch("app.api.v1.endpoints.rd_project.expenses.get_or_404", side_effect=[mock_project, mock_cost_type]), \
             patch("app.api.v1.endpoints.rd_project.expenses.generate_cost_no", return_value="COST-001"), \
             patch("app.api.v1.endpoints.rd_project.expenses.save_obj"), \
             patch("app.api.v1.endpoints.rd_project.expenses.RdCost", return_value=mock_cost), \
             patch("app.api.v1.endpoints.rd_project.expenses.RdCostResponse") as mock_resp:
            mock_resp.model_validate.return_value = MagicMock()
            result = create_rd_cost(cost_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_update_rd_cost_not_found(self):
        from app.api.v1.endpoints.rd_project.expenses import update_rd_cost
        db = _mock_db()
        with patch("app.api.v1.endpoints.rd_project.expenses.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="费用不存在")
            with pytest.raises(HTTPException) as exc:
                # Correct param name is cost_in
                update_rd_cost(cost_id=999, cost_in=MagicMock(), db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_calculate_labor_cost(self):
        from app.api.v1.endpoints.rd_project.expenses import calculate_labor_cost
        db = _mock_db()
        mock_calc_req = MagicMock()
        mock_calc_req.rd_project_id = 1
        mock_calc_req.user_id = 1
        mock_calc_req.start_date = date(2025, 1, 1)
        mock_calc_req.end_date = date(2025, 1, 31)
        mock_calc_req.hourly_rate = Decimal("100")
        mock_project = MagicMock()
        mock_user = MagicMock()
        with patch("app.api.v1.endpoints.rd_project.expenses.get_or_404", side_effect=[mock_project, mock_user]):
            db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
            result = calculate_labor_cost(calc_request=mock_calc_req, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 15. shortage/handling/arrivals.py
# ============================================================

class TestShortageArrivals:
    """到货跟踪测试"""

    def test_list_arrivals_empty(self):
        from app.api.v1.endpoints.shortage.handling.arrivals import list_arrivals
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.shortage.handling.arrivals.apply_pagination") as mock_pag, \
             patch("app.api.v1.endpoints.shortage.handling.arrivals.apply_keyword_filter", return_value=db.query.return_value):
            mock_pag.return_value.all.return_value = []
            result = list_arrivals(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                arrival_status=None,
                supplier_id=None,
                is_delayed=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_arrival_not_found(self):
        from app.api.v1.endpoints.shortage.handling.arrivals import get_arrival
        db = _mock_db()
        with patch("app.api.v1.endpoints.shortage.handling.arrivals.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="到货记录不存在")
            with pytest.raises(HTTPException) as exc:
                get_arrival(arrival_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_arrival(self):
        from app.api.v1.endpoints.shortage.handling.arrivals import create_arrival
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.material_id = 1
        mock_schema.shortage_report_id = None
        mock_schema.purchase_order_id = None
        mock_schema.supplier_id = None
        mock_material = MagicMock()
        with patch("app.api.v1.endpoints.shortage.handling.arrivals.get_or_404", return_value=mock_material), \
             patch("app.api.v1.endpoints.shortage.handling.arrivals._generate_arrival_no", return_value="ARR-001"), \
             patch("app.api.v1.endpoints.shortage.handling.arrivals.save_obj"), \
             patch("app.api.v1.endpoints.shortage.handling.arrivals._build_arrival_response", return_value={"id": 1}), \
             patch("app.api.v1.endpoints.shortage.handling.arrivals.MaterialArrival") as mock_cls:
            mock_cls.return_value = MagicMock()
            result = create_arrival(arrival_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_delayed_arrivals_empty(self):
        from app.api.v1.endpoints.shortage.handling.arrivals import get_delayed_arrivals
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.shortage.handling.arrivals.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = get_delayed_arrivals(db=db, pagination=_mock_pagination(), current_user=_mock_user())
        assert result is not None


# ============================================================
# 16. sales/payments/payment_exports.py
# ============================================================

class TestPaymentExports:
    """回款导出测试"""

    def test_export_payment_invoices_empty(self):
        from app.api.v1.endpoints.sales.payments.payment_exports import export_payment_invoices
        from io import BytesIO
        db = _mock_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.join.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        # Mock Workbook to avoid Excel encoding issues
        with patch("app.api.v1.endpoints.sales.payments.payment_exports.Workbook") as mock_wb:
            mock_ws = MagicMock()
            mock_wb.return_value.active = mock_ws
            mock_buf = BytesIO()
            mock_wb.return_value.save = lambda buf: buf.write(b"mock_excel")
            result = export_payment_invoices(
                db=db,
                contract_id=None,
                project_id=None,
                customer_id=None,
                payment_status=None,
                start_date=None,
                end_date=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_export_payments_empty(self):
        from app.api.v1.endpoints.sales.payments.payment_exports import export_payments
        from io import BytesIO
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        with patch("app.api.v1.endpoints.sales.payments.payment_exports.Workbook") as mock_wb:
            mock_ws = MagicMock()
            mock_wb.return_value.active = mock_ws
            mock_wb.return_value.save = lambda buf: buf.write(b"mock_excel")
            result = export_payments(
                db=db,
                keyword=None,
                status=None,
                customer_id=None,
                include_aging=False,
                current_user=_mock_user(),
            )
        assert result is not None


# ============================================================
# 17. sales/contracts/basic.py
# ============================================================

class TestSalesContractsBasic:
    """合同基础操作测试"""

    def test_read_contracts_empty(self):
        from app.api.v1.endpoints.sales.contracts.basic import read_contracts
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.sales.contracts.basic.apply_keyword_filter", return_value=db.query.return_value), \
             patch("app.api.v1.endpoints.sales.contracts.basic.apply_pagination") as mock_pag, \
             patch("app.api.v1.endpoints.sales.contracts.basic.security.filter_sales_data_by_scope", return_value=db.query.return_value):
            mock_pag.return_value.all.return_value = []
            result = read_contracts(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                status=None,
                customer_id=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_read_contract_not_found(self):
        from app.api.v1.endpoints.sales.contracts.basic import read_contract
        db = _mock_db()
        # read_contract uses inline db.query().options().filter().first()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            read_contract(contract_id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_create_contract_no_quote(self):
        from app.api.v1.endpoints.sales.contracts.basic import create_contract
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.deliverables = []
        mock_schema.model_dump.return_value = {
            "contract_code": None,
            "opportunity_id": 1,
            "customer_id": 1,
            "owner_id": None,
            "quote_version_id": None,
        }
        mock_opportunity = MagicMock()
        mock_opportunity.opp_code = "OPP-001"
        mock_customer = MagicMock()
        mock_customer.customer_name = "Test"
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.project = None
        mock_contract.sales_owner = None
        mock_contract.__table__ = MagicMock()
        mock_contract.__table__.columns = []
        with patch("app.api.v1.endpoints.sales.contracts.basic.generate_contract_code", return_value="CON-001"), \
             patch("app.api.v1.endpoints.sales.contracts.basic.security.filter_sales_data_by_scope", return_value=db.query.return_value):
            # opportunity query
            db.query.return_value.filter.return_value.first.side_effect = [mock_opportunity, mock_customer, []]
            result = create_contract(contract_in=mock_schema, db=db, skip_g3_validation=True, current_user=_mock_user())
        assert result is not None

    def test_update_contract_not_found(self):
        from app.api.v1.endpoints.sales.contracts.basic import update_contract
        db = _mock_db()
        # update_contract uses inline query
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            update_contract(contract_id=999, contract_in=MagicMock(), db=db, current_user=_mock_user())
        assert exc.value.status_code == 404


# ============================================================
# 18. business_support_orders/reconciliations.py  (async)
# ============================================================

class TestReconciliations:
    """对账单管理测试（async）"""

    def test_get_reconciliations_empty(self):
        from app.api.v1.endpoints.business_support_orders.reconciliations import get_reconciliations
        db = _mock_db()
        # get_reconciliations uses inline pagination, not apply_pagination
        with patch("app.api.v1.endpoints.business_support_orders.reconciliations.apply_keyword_filter", return_value=db.query.return_value):
            db.query.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = asyncio.run(get_reconciliations(
                db=db,
                pagination=_mock_pagination(),
                customer_id=None,
                reconciliation_status=None,
                search=None,
                current_user=_mock_user(),
            ))
        assert result is not None

    def test_get_reconciliation_not_found(self):
        from app.api.v1.endpoints.business_support_orders.reconciliations import get_reconciliation
        db = _mock_db()
        with patch("app.api.v1.endpoints.business_support_orders.reconciliations.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="对账单不存在")
            with pytest.raises(HTTPException) as exc:
                asyncio.run(get_reconciliation(reconciliation_id=999, db=db, current_user=_mock_user()))
            assert exc.value.status_code == 404

    def test_update_reconciliation_not_found(self):
        from app.api.v1.endpoints.business_support_orders.reconciliations import update_reconciliation
        db = _mock_db()
        with patch("app.api.v1.endpoints.business_support_orders.reconciliations.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="对账单不存在")
            with pytest.raises(HTTPException) as exc:
                # correct param name is reconciliation_data
                asyncio.run(update_reconciliation(reconciliation_id=999, reconciliation_data=MagicMock(), db=db, current_user=_mock_user()))
            assert exc.value.status_code == 404


# ============================================================
# 19. sales/utils/common.py
# ============================================================

class TestSalesUtilsCommon:
    """销售通用工具测试"""

    def test_calculate_growth_with_previous(self):
        from app.api.v1.endpoints.sales.utils.common import calculate_growth
        result = calculate_growth(120.0, 100.0)
        assert result == 20.0

    def test_calculate_growth_no_previous(self):
        from app.api.v1.endpoints.sales.utils.common import calculate_growth
        # When previous is None and current > 0, returns 100.0
        result = calculate_growth(120.0, None)
        assert result == 100.0

    def test_calculate_growth_previous_zero(self):
        from app.api.v1.endpoints.sales.utils.common import calculate_growth
        # When previous is 0 and current > 0, returns 100.0
        result = calculate_growth(120.0, 0.0)
        assert result == 100.0

    def test_shift_month_forward(self):
        from app.api.v1.endpoints.sales.utils.common import shift_month
        year, month = shift_month(2025, 12, 1)
        assert year == 2026
        assert month == 1

    def test_shift_month_backward(self):
        from app.api.v1.endpoints.sales.utils.common import shift_month
        year, month = shift_month(2025, 1, -1)
        assert year == 2024
        assert month == 12

    def test_get_user_role_code_no_role(self):
        from app.api.v1.endpoints.sales.utils.common import get_user_role_code
        db = _mock_db()
        db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        result = get_user_role_code(db, _mock_user())
        assert result is not None

    def test_normalize_date_range(self):
        from app.api.v1.endpoints.sales.utils.common import normalize_date_range
        start, end = normalize_date_range("2025-01-01", "2025-12-31")
        assert start is not None
        assert end is not None

    def test_get_previous_range(self):
        from app.api.v1.endpoints.sales.utils.common import get_previous_range
        start = date(2025, 1, 1)
        end = date(2025, 3, 31)
        prev_start, prev_end = get_previous_range(start, end)
        assert prev_start < start


# ============================================================
# 20. sales/targets.py
# ============================================================

class TestSalesTargets:
    """销售目标管理测试"""

    def test_get_sales_targets_empty(self):
        from app.api.v1.endpoints.sales.targets import get_sales_targets
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        mock_service_instance = MagicMock()
        mock_service_instance.calculate_target_performance.return_value = (Decimal("0"), Decimal("0"))
        with patch("app.api.v1.endpoints.sales.targets.apply_pagination") as mock_pag, \
             patch("app.api.v1.endpoints.sales.targets.get_user_role_code", return_value="SALES"), \
             patch("app.api.v1.endpoints.sales.targets.SalesTeamService", return_value=mock_service_instance):
            mock_pag.return_value.all.return_value = []
            result = get_sales_targets(
                db=db,
                pagination=_mock_pagination(),
                target_scope=None,
                target_type=None,
                target_period=None,
                period_value=None,
                user_id=None,
                department_id=None,
                status=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_create_sales_target(self):
        from app.api.v1.endpoints.sales.targets import create_sales_target
        db = _mock_db()
        mock_schema = MagicMock()
        mock_target = MagicMock()
        mock_target.__table__ = MagicMock()
        mock_target.__table__.columns = []
        with patch("app.api.v1.endpoints.sales.targets.save_obj") as mock_save, \
             patch("app.api.v1.endpoints.sales.targets.SalesTarget", return_value=mock_target):
            mock_save.return_value = mock_target
            result = create_sales_target(target_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_update_sales_target_not_found(self):
        from app.api.v1.endpoints.sales.targets import update_sales_target
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.targets.get_or_404") as mock_get, \
             patch("app.api.v1.endpoints.sales.targets.SalesTeamService") as mock_svc:
            mock_get.side_effect = HTTPException(status_code=404, detail="目标不存在")
            with pytest.raises(HTTPException) as exc:
                update_sales_target(target_id=999, target_in=MagicMock(), db=db, current_user=_mock_user())
            assert exc.value.status_code == 404


# ============================================================
# 21. sales/opportunity_crud.py
# ============================================================

class TestOpportunityCrud:
    """商机管理测试"""

    def test_read_opportunities_empty(self):
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunities
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.sales.opportunity_crud.apply_keyword_filter", return_value=db.query.return_value), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.security.filter_sales_data_by_scope", return_value=db.query.return_value):
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = read_opportunities(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                stage=None,
                customer_id=None,
                owner_id=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_read_opportunity_not_found(self):
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunity
        db = _mock_db()
        # read_opportunity uses inline db.query().options().filter().first()
        db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            read_opportunity(opp_id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_create_opportunity(self):
        from app.api.v1.endpoints.sales.opportunity_crud import create_opportunity
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.customer_id = 1
        mock_schema.requirement = None
        # model_dump must not contain opp_code (or be falsy) to trigger auto-gen
        mock_schema.model_dump.return_value = {
            "opp_code": None,  # falsy: auto-generate
            "customer_id": 1,
            "owner_id": None,
        }
        mock_customer = MagicMock()
        mock_customer.customer_name = "Test Corp"
        mock_opp = MagicMock()
        mock_opp.id = 1
        mock_opp.owner = None
        mock_opp.updater = None
        mock_opp.requirements = []
        mock_opp.__table__ = MagicMock()
        mock_opp.__table__.columns = []
        with patch("app.api.v1.endpoints.sales.opportunity_crud.generate_opportunity_code", return_value="OPP-001"), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.Opportunity", return_value=mock_opp):
            # customer lookup returns mock_customer
            db.query.return_value.filter.return_value.first.return_value = mock_customer
            db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
            result = create_opportunity(opp_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_update_opportunity_not_found(self):
        from app.api.v1.endpoints.sales.opportunity_crud import update_opportunity
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.opportunity_crud.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="商机不存在")
            with pytest.raises(HTTPException) as exc:
                update_opportunity(opp_id=999, opp_in=MagicMock(), db=db, current_user=_mock_user())
            assert exc.value.status_code == 404


# ============================================================
# 22. organization/units.py
# ============================================================

class TestOrganizationUnits:
    """组织单元管理测试"""

    def test_list_org_units_empty(self):
        from app.api.v1.endpoints.organization.units import list_org_units
        db = _mock_db()
        with patch("app.api.v1.endpoints.organization.units.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = list_org_units(
                db=db,
                pagination=_mock_pagination(),
                unit_type=None,
                is_active=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_org_unit_not_found(self):
        from app.api.v1.endpoints.organization.units import get_org_unit
        db = _mock_db()
        # get_org_unit uses inline db.query(...).filter(...).first()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_org_unit(id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_create_org_unit(self):
        from app.api.v1.endpoints.organization.units import create_org_unit
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.unit_code = "ORG001"
        mock_schema.parent_id = None
        mock_schema.model_dump.return_value = {"unit_code": "ORG001", "parent_id": None, "unit_name": "Test"}
        # First query: check existing code -> None means not found (ok)
        db.query.return_value.filter.return_value.first.return_value = None
        mock_unit = MagicMock()
        with patch("app.api.v1.endpoints.organization.units.OrganizationUnit", return_value=mock_unit), \
             patch("app.api.v1.endpoints.organization.units.OrganizationUnitResponse") as mock_resp, \
             patch("app.api.v1.endpoints.organization.units.success_response", return_value={"code": 200}):
            result = create_org_unit(unit_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_delete_org_unit_not_found(self):
        from app.api.v1.endpoints.organization.units import delete_org_unit
        db = _mock_db()
        # delete_org_unit uses inline db.query
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            delete_org_unit(id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_get_org_tree(self):
        from app.api.v1.endpoints.organization.units import get_org_tree
        db = _mock_db()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        result = get_org_tree(db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 23. projects/archive.py
# ============================================================

class TestProjectsArchive:
    """项目归档管理测试"""

    def test_archive_project_already_archived(self):
        from app.api.v1.endpoints.projects.archive import archive_project
        db = _mock_db()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.is_archived = True
        # check_project_access_or_raise is imported inline, patch it at source
        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=mock_project):
            result = archive_project(project_id=1, reason=None, db=db, current_user=_mock_user())
        assert result is not None

    def test_unarchive_project_not_archived(self):
        from app.api.v1.endpoints.projects.archive import unarchive_project
        db = _mock_db()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.is_archived = False
        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=mock_project):
            result = unarchive_project(project_id=1, db=db, current_user=_mock_user())
        assert result is not None

    def test_get_archived_projects_empty(self):
        from app.api.v1.endpoints.projects.archive import get_archived_projects
        db = _mock_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.projects.archive.apply_pagination") as mock_pag, \
             patch("app.api.v1.endpoints.projects.archive.apply_keyword_filter", return_value=db.query.return_value):
            mock_pag.return_value.all.return_value = []
            result = get_archived_projects(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_batch_archive_projects_empty_list(self):
        from app.api.v1.endpoints.projects.archive import batch_archive_projects
        db = _mock_db()
        with patch("app.services.data_scope.DataScopeService.filter_projects_by_scope", return_value=db.query.return_value):
            db.query.return_value.filter.return_value.all.return_value = []
            result = batch_archive_projects(project_ids=[], archive_reason=None, db=db, current_user=_mock_user())
        assert result is not None


# ============================================================
# 24. sales/team/pk.py
# ============================================================

class TestSalesTeamPK:
    """团队PK管理测试"""

    def test_list_team_pks_empty(self):
        from app.api.v1.endpoints.sales.team.pk import list_team_pks
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.sales.team.pk.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []
            result = list_team_pks(
                db=db,
                status_filter=None,
                pagination=_mock_pagination(),
                current_user=_mock_user(),
            )
        assert result is not None

    def test_get_team_pk_not_found(self):
        from app.api.v1.endpoints.sales.team.pk import get_team_pk
        db = _mock_db()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_team_pk(pk_id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404

    def test_create_team_pk(self):
        from app.api.v1.endpoints.sales.team.pk import create_team_pk
        db = _mock_db()
        mock_request = MagicMock()
        mock_request.team_ids = [1, 2]
        mock_request.pk_name = "PK大战"
        mock_request.pk_type = "REVENUE"
        mock_request.start_date = datetime(2025, 1, 1)
        mock_request.end_date = datetime(2025, 12, 31)
        mock_request.target_value = Decimal("100000")
        mock_request.reward_description = "奖励说明"
        # teams query returns same count as requested
        mock_team1, mock_team2 = MagicMock(), MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [mock_team1, mock_team2]
        mock_pk = MagicMock()
        mock_pk.id = 1
        mock_pk.pk_name = "PK大战"
        mock_pk.status = "ONGOING"
        with patch("app.api.v1.endpoints.sales.team.pk.save_obj"), \
             patch("app.api.v1.endpoints.sales.team.pk.TeamPKRecord", return_value=mock_pk):
            result = create_team_pk(request=mock_request, db=db, current_user=_mock_user())
        assert result is not None

    def test_complete_team_pk_not_found(self):
        from app.api.v1.endpoints.sales.team.pk import complete_team_pk
        db = _mock_db()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            complete_team_pk(pk_id=999, db=db, current_user=_mock_user())
        assert exc.value.status_code == 404


# ============================================================
# 25. sales/leads/crud.py
# ============================================================

class TestSalesLeadsCrud:
    """销售线索 CRUD 测试"""

    def test_read_leads_empty(self):
        from app.api.v1.endpoints.sales.leads.crud import read_leads
        db = _mock_db()
        db.query.return_value.count.return_value = 0
        with patch("app.api.v1.endpoints.sales.leads.crud.apply_keyword_filter", return_value=db.query.return_value), \
             patch("app.api.v1.endpoints.sales.leads.crud.security.filter_sales_data_by_scope", return_value=db.query.return_value):
            db.query.return_value.filter.return_value.count.return_value = 0
            db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            result = read_leads(
                db=db,
                pagination=_mock_pagination(),
                keyword=None,
                status=None,
                owner_id=None,
                current_user=_mock_user(),
            )
        assert result is not None

    def test_read_lead_not_found(self):
        from app.api.v1.endpoints.sales.leads.crud import read_lead
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.leads.crud.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="线索不存在")
            with pytest.raises(HTTPException) as exc:
                read_lead(lead_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_create_lead(self):
        from app.api.v1.endpoints.sales.leads.crud import create_lead
        db = _mock_db()
        mock_schema = MagicMock()
        mock_schema.lead_name = "潜在客户A"
        # model_dump must NOT contain lead_code (or set it falsy) to bypass existing check
        mock_schema.model_dump.return_value = {
            "lead_name": "潜在客户A",
            "lead_code": None,  # falsy: auto-generate
            "owner_id": None,
            "selected_advantage_products": None,
        }
        mock_lead = MagicMock()
        mock_lead.owner = None
        mock_lead.__table__ = MagicMock()
        mock_lead.__table__.columns = []
        with patch("app.api.v1.endpoints.sales.leads.crud.generate_lead_code", return_value="LEAD-001"), \
             patch("app.api.v1.endpoints.sales.leads.crud.save_obj"), \
             patch("app.api.v1.endpoints.sales.leads.crud.Lead", return_value=mock_lead):
            result = create_lead(lead_in=mock_schema, db=db, current_user=_mock_user())
        assert result is not None

    def test_delete_lead_not_found(self):
        from app.api.v1.endpoints.sales.leads.crud import delete_lead
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.leads.crud.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="线索不存在")
            with pytest.raises(HTTPException) as exc:
                delete_lead(lead_id=999, db=db, current_user=_mock_user())
            assert exc.value.status_code == 404

    def test_update_lead_not_found(self):
        from app.api.v1.endpoints.sales.leads.crud import update_lead
        db = _mock_db()
        with patch("app.api.v1.endpoints.sales.leads.crud.get_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="线索不存在")
            with pytest.raises(HTTPException) as exc:
                update_lead(lead_id=999, lead_in=MagicMock(), db=db, current_user=_mock_user())
            assert exc.value.status_code == 404
