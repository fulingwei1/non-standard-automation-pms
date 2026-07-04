# -*- coding: utf-8 -*-
"""TEN-03（全量铺开第一批+第三批）契约。

第一批：customers/contracts/invoices/sales_orders。
第三批：opportunities/quotes/quote_versions（contracts 在销售链路上的
直接上游）。

这几张表审计点名"全无 tenant_id"，与 projects 那种"DB 有列、模型没声明"的
幽灵列不同——是真的从零加列。风险点：如果新建的行没有自动带上 tenant_id，
会变成对创建者自己也不可见的"隐形数据"，不是隔离而是丢数据。本文件同时
验证：①跨租户查询隔离生效（复用 TEN-02 的全局过滤）；②新建行不显式传
tenant_id 时能通过 before_flush 钩子自动补全（TEN-02 铺开配套）。
"""
import uuid

import pytest

from app.core.middleware.tenant_middleware import (
    set_current_tenant_id,
    set_current_user_is_superuser,
)
from app.core.security import get_password_hash
from app.models.project.customer import Customer
from app.models.sales.contracts import Contract
from app.models.sales.invoices import Invoice
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.business_support.sales_order import SalesOrder
from app.models.tenant import Tenant, TenantPlan, TenantStatus
from app.models.user import User


@pytest.fixture(autouse=True)
def _reset_tenant_context():
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)
    yield
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)


def _make_tenant(db, suffix):
    tenant = Tenant(
        tenant_code=f"ten03_{suffix}",
        tenant_name=f"ten03 tenant {suffix}",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.FREE.value,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def two_tenants(db):
    suffix = uuid.uuid4().hex[:8]
    return _make_tenant(db, f"a{suffix}"), _make_tenant(db, f"b{suffix}")


class TestCustomerTenantScope:
    def test_cross_tenant_customer_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust_a = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_A_{suffix}", customer_name="客户A"
        )
        cust_b = Customer(
            tenant_id=tenant_b.id, customer_code=f"CUST_B_{suffix}", customer_name="客户B"
        )
        db.add_all([cust_a, cust_b])
        db.commit()

        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        visible = db.query(Customer).filter(Customer.id.in_([cust_a.id, cust_b.id])).all()
        assert [c.id for c in visible] == [cust_a.id]

    def test_new_customer_auto_gets_tenant_id(self, db, two_tenants):
        """创建时不传 tenant_id，应从当前请求上下文自动补全（否则对创建者自己也不可见）。"""
        tenant_a, _tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        cust = Customer(customer_code=f"CUST_AUTO_{suffix}", customer_name="自动归户客户")
        db.add(cust)
        db.commit()

        assert cust.tenant_id == tenant_a.id


class TestContractTenantScope:
    def test_cross_tenant_contract_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust_a = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_CA_{suffix}", customer_name="客户A"
        )
        cust_b = Customer(
            tenant_id=tenant_b.id, customer_code=f"CUST_CB_{suffix}", customer_name="客户B"
        )
        db.add_all([cust_a, cust_b])
        db.flush()

        contract_a = Contract(
            tenant_id=tenant_a.id,
            contract_code=f"CT_A_{suffix}",
            contract_name="合同A",
            contract_type="sales",
            customer_id=cust_a.id,
            total_amount=1000,
        )
        contract_b = Contract(
            tenant_id=tenant_b.id,
            contract_code=f"CT_B_{suffix}",
            contract_name="合同B",
            contract_type="sales",
            customer_id=cust_b.id,
            total_amount=2000,
        )
        db.add_all([contract_a, contract_b])
        db.commit()

        set_current_tenant_id(tenant_b.id)
        set_current_user_is_superuser(False)

        visible = (
            db.query(Contract).filter(Contract.id.in_([contract_a.id, contract_b.id])).all()
        )
        assert [c.id for c in visible] == [contract_b.id]

    def test_new_contract_auto_gets_tenant_id(self, db, two_tenants):
        tenant_a, _tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        cust = Customer(customer_code=f"CUST_CTX_{suffix}", customer_name="上下文客户")
        db.add(cust)
        db.flush()

        contract = Contract(
            contract_code=f"CT_AUTO_{suffix}",
            contract_name="自动归户合同",
            contract_type="sales",
            customer_id=cust.id,
            total_amount=500,
        )
        db.add(contract)
        db.commit()

        assert contract.tenant_id == tenant_a.id


class TestInvoiceTenantScope:
    def test_cross_tenant_invoice_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_IV_{suffix}", customer_name="客户"
        )
        db.add(cust)
        db.flush()
        contract = Contract(
            tenant_id=tenant_a.id,
            contract_code=f"CT_IV_{suffix}",
            contract_name="合同",
            contract_type="sales",
            customer_id=cust.id,
            total_amount=1000,
        )
        db.add(contract)
        db.flush()

        invoice_a = Invoice(
            tenant_id=tenant_a.id, invoice_code=f"INV_A_{suffix}", contract_id=contract.id
        )
        invoice_b = Invoice(
            tenant_id=tenant_b.id, invoice_code=f"INV_B_{suffix}", contract_id=contract.id
        )
        db.add_all([invoice_a, invoice_b])
        db.commit()

        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        visible = db.query(Invoice).filter(Invoice.id.in_([invoice_a.id, invoice_b.id])).all()
        assert [i.id for i in visible] == [invoice_a.id]


class TestSalesOrderTenantScope:
    def test_cross_tenant_sales_order_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust_a = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_SO_A_{suffix}", customer_name="客户A"
        )
        cust_b = Customer(
            tenant_id=tenant_b.id, customer_code=f"CUST_SO_B_{suffix}", customer_name="客户B"
        )
        db.add_all([cust_a, cust_b])
        db.flush()

        order_a = SalesOrder(
            tenant_id=tenant_a.id, order_no=f"SO_A_{suffix}", customer_id=cust_a.id
        )
        order_b = SalesOrder(
            tenant_id=tenant_b.id, order_no=f"SO_B_{suffix}", customer_id=cust_b.id
        )
        db.add_all([order_a, order_b])
        db.commit()

        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        visible = (
            db.query(SalesOrder).filter(SalesOrder.id.in_([order_a.id, order_b.id])).all()
        )
        assert [o.id for o in visible] == [order_a.id]


class TestOpportunityTenantScope:
    def test_cross_tenant_opportunity_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust_a = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_OP_A_{suffix}", customer_name="客户A"
        )
        cust_b = Customer(
            tenant_id=tenant_b.id, customer_code=f"CUST_OP_B_{suffix}", customer_name="客户B"
        )
        db.add_all([cust_a, cust_b])
        db.flush()

        opp_a = Opportunity(
            tenant_id=tenant_a.id,
            opp_code=f"OPP_A_{suffix}",
            customer_id=cust_a.id,
            opp_name="商机A",
        )
        opp_b = Opportunity(
            tenant_id=tenant_b.id,
            opp_code=f"OPP_B_{suffix}",
            customer_id=cust_b.id,
            opp_name="商机B",
        )
        db.add_all([opp_a, opp_b])
        db.commit()

        set_current_tenant_id(tenant_b.id)
        set_current_user_is_superuser(False)

        visible = db.query(Opportunity).filter(Opportunity.id.in_([opp_a.id, opp_b.id])).all()
        assert [o.id for o in visible] == [opp_b.id]

    def test_new_opportunity_auto_gets_tenant_id(self, db, two_tenants):
        tenant_a, _tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        cust = Customer(customer_code=f"CUST_OP_CTX_{suffix}", customer_name="上下文客户")
        db.add(cust)
        db.flush()

        opp = Opportunity(
            opp_code=f"OPP_AUTO_{suffix}", customer_id=cust.id, opp_name="自动归户商机"
        )
        db.add(opp)
        db.commit()

        assert opp.tenant_id == tenant_a.id


class TestQuoteTenantScope:
    def test_cross_tenant_quote_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_QT_{suffix}", customer_name="客户"
        )
        db.add(cust)
        db.flush()
        opp = Opportunity(
            tenant_id=tenant_a.id,
            opp_code=f"OPP_QT_{suffix}",
            customer_id=cust.id,
            opp_name="商机",
        )
        db.add(opp)
        db.flush()

        quote_a = Quote(
            tenant_id=tenant_a.id,
            quote_code=f"QT_A_{suffix}",
            opportunity_id=opp.id,
            customer_id=cust.id,
        )
        quote_b = Quote(
            tenant_id=tenant_b.id,
            quote_code=f"QT_B_{suffix}",
            opportunity_id=opp.id,
            customer_id=cust.id,
        )
        db.add_all([quote_a, quote_b])
        db.commit()

        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        visible = db.query(Quote).filter(Quote.id.in_([quote_a.id, quote_b.id])).all()
        assert [q.id for q in visible] == [quote_a.id]

    def test_cross_tenant_quote_version_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_QV_{suffix}", customer_name="客户"
        )
        db.add(cust)
        db.flush()
        opp = Opportunity(
            tenant_id=tenant_a.id,
            opp_code=f"OPP_QV_{suffix}",
            customer_id=cust.id,
            opp_name="商机",
        )
        db.add(opp)
        db.flush()
        quote = Quote(
            tenant_id=tenant_a.id,
            quote_code=f"QT_QV_{suffix}",
            opportunity_id=opp.id,
            customer_id=cust.id,
        )
        db.add(quote)
        db.flush()

        version_a = QuoteVersion(tenant_id=tenant_a.id, quote_id=quote.id, version_no="V1")
        version_b = QuoteVersion(tenant_id=tenant_b.id, quote_id=quote.id, version_no="V1")
        db.add_all([version_a, version_b])
        db.commit()

        set_current_tenant_id(tenant_b.id)
        set_current_user_is_superuser(False)

        visible = (
            db.query(QuoteVersion)
            .filter(QuoteVersion.id.in_([version_a.id, version_b.id]))
            .all()
        )
        assert [v.id for v in visible] == [version_b.id]


class TestSuperuserBypass:
    def test_superuser_sees_all_tenants_customers(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        cust_a = Customer(
            tenant_id=tenant_a.id, customer_code=f"CUST_SU_A_{suffix}", customer_name="客户A"
        )
        cust_b = Customer(
            tenant_id=tenant_b.id, customer_code=f"CUST_SU_B_{suffix}", customer_name="客户B"
        )
        db.add_all([cust_a, cust_b])
        db.commit()

        set_current_tenant_id(None)
        set_current_user_is_superuser(True)

        visible = {
            c.id for c in db.query(Customer).filter(Customer.id.in_([cust_a.id, cust_b.id])).all()
        }
        assert visible == {cust_a.id, cust_b.id}
