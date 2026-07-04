-- TEN-03（全量铺开第三批）：opportunities/quotes/quote_versions——contracts
-- 在销售链路上的直接上游对象，与 customers/contracts/invoices/sales_orders
-- 同批次处理方式：真的从零加列，不是幽灵列。
--
-- 口径同前几批：全部存量数据归入默认租户（id=1 金凯博，active）。新增行
-- 由 app/core/database/tenant_scope.py 的 before_flush 钩子按当前请求
-- 租户上下文自动补全。

ALTER TABLE opportunities ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_opportunities_tenant ON opportunities(tenant_id);
UPDATE opportunities
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;

ALTER TABLE quotes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quotes_tenant ON quotes(tenant_id);
UPDATE quotes
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;

ALTER TABLE quote_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_versions_tenant ON quote_versions(tenant_id);
UPDATE quote_versions
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;
