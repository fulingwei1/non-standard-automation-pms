-- TEN-03（全量铺开第一批）：customers/contracts/invoices/sales_orders 是审计
-- 明确点名"全无 tenant_id"的四张核心业务表，与已有 tenant_id 但模型未声明
-- 的 projects 幽灵列不同——这四张表连列都没有，需要真正的 ALTER TABLE。
--
-- 口径同 TEN-06 用户归户 / TEN-03 Project 切片：全部存量数据归入默认租户
-- （id=1 金凯博，active）。新增行今后由 app/core/database/tenant_scope.py
-- 的 before_flush 钩子按当前请求租户上下文自动补全，不需要逐个创建入口
-- 手工传参。

ALTER TABLE customers ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customers_tenant ON customers(tenant_id);
UPDATE customers
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;

ALTER TABLE contracts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contracts_tenant ON contracts(tenant_id);
UPDATE contracts
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;

ALTER TABLE invoices ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant ON invoices(tenant_id);
UPDATE invoices
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;

ALTER TABLE sales_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_orders_tenant ON sales_orders(tenant_id);
UPDATE sales_orders
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;
