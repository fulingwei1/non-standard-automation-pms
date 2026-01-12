-- -*- coding: utf-8 -*-
-- 性能优化：数据库索引添加脚本（SQLite版本）
--
-- 用途：为常用查询字段添加索引，提升查询性能
-- 执行时机：在生产环境部署前或性能调优时执行
--
-- 注意事项：
-- 1. 索引会占用额外存储空间，权衡后添加
-- 2. 写入密集型表慎用过多索引
-- 3. 索引名格式：idx_表名_字段名_用途

-- ============================================
-- 项目相关索引
-- ============================================

-- 项目列表常用查询索引
CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(code);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_stage ON projects(stage);
CREATE INDEX IF NOT EXISTS idx_projects_health ON projects(health);
CREATE INDEX IF NOT EXISTS idx_projects_pm_id ON projects(pm_id);
CREATE INDEX IF NOT EXISTS idx_projects_customer_id ON projects(customer_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- 项目状态日志查询索引
CREATE INDEX IF NOT EXISTS idx_project_status_logs_project_id ON project_status_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_project_status_logs_created_at ON project_status_logs(created_at);

-- 项目阶段查询索引
CREATE INDEX IF NOT EXISTS idx_project_stages_project_id ON project_stages(project_id);
CREATE INDEX IF NOT EXISTS idx_project_stages_stage_code ON project_stages(stage_code);

-- 项目成员查询索引
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_project_members_role ON project_members(role);

-- 机台查询索引
CREATE INDEX IF NOT EXISTS idx_machines_project_id ON machines(project_id);
CREATE INDEX IF NOT EXISTS idx_machines_code ON machines(code);

-- ============================================
-- 客户和销售相关索引
-- ============================================

-- 客户查询索引
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code);
CREATE INDEX IF NOT EXISTS idx_customers_contact_person ON customers(contact_person);

-- 合同查询索引
CREATE INDEX IF NOT EXISTS idx_contracts_code ON contracts(code);
CREATE INDEX IF NOT EXISTS idx_contracts_customer_id ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts(project_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON contracts(created_at);

-- 发票查询索引
CREATE INDEX IF NOT EXISTS idx_invoices_contract_id ON invoices(contract_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at);

-- 线索查询索引
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- ============================================
-- 物料和BOM相关索引
-- ============================================

-- 物料查询索引
CREATE INDEX IF NOT EXISTS idx_materials_code ON materials(code);
CREATE INDEX IF NOT EXISTS idx_materials_name ON materials(name);
CREATE INDEX IF NOT EXISTS idx_materials_category_id ON materials(category_id);
CREATE INDEX IF NOT EXISTS idx_materials_type ON materials(type);
CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);

-- 物料分类索引
CREATE INDEX IF NOT EXISTS idx_material_categories_name ON material_categories(name);

-- BOM头表索引
CREATE INDEX IF NOT EXISTS idx_bom_headers_project_id ON bom_headers(project_id);
CREATE INDEX IF NOT EXISTS idx_bom_headers_code ON bom_headers(code);
CREATE INDEX IF NOT EXISTS idx_bom_headers_version ON bom_headers(version);
CREATE INDEX IF NOT EXISTS idx_bom_headers_status ON bom_headers(status);

-- BOM明细索引
CREATE INDEX IF NOT EXISTS idx_bom_items_header_id ON bom_items(header_id);
CREATE INDEX IF NOT EXISTS idx_bom_items_material_id ON bom_items(material_id);

-- ============================================
-- 采购相关索引
-- ============================================

-- 供应商查询索引
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);
CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(code);
CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status);

-- 采购订单索引
CREATE INDEX IF NOT EXISTS idx_purchase_orders_code ON purchase_orders(code);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_created_at ON purchase_orders(created_at);

-- 采购订单明细索引
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_order_id ON purchase_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_material_id ON purchase_order_items(material_id);

-- 收货单索引
CREATE INDEX IF NOT EXISTS idx_goods_receipts_order_id ON goods_receipts(order_id);
CREATE INDEX IF NOT EXISTS idx_goods_receipts_material_id ON goods_receipts(material_id);
CREATE INDEX IF NOT EXISTS idx_goods_receipts_created_at ON goods_receipts(created_at);

-- ============================================
-- 任务和进度相关索引
-- ============================================

-- 任务索引
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_stage_code ON tasks(stage_code);

-- ============================================
-- 用户和权限相关索引
-- ============================================

-- 用户查询索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);

-- 角色查询索引
CREATE INDEX IF NOT EXISTS idx_roles_code ON roles(code);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- ============================================
-- ECN（工程变更通知）相关索引
-- ============================================

-- ECN索引
CREATE INDEX IF NOT EXISTS idx_ecns_code ON ecns(code);
CREATE INDEX IF NOT EXISTS idx_ecns_project_id ON ecns(project_id);
CREATE INDEX IF NOT EXISTS idx_ecns_status ON ecns(status);
CREATE INDEX IF NOT EXISTS idx_ecns_type ON ecns(type);
CREATE INDEX IF NOT EXISTS idx_ecns_created_at ON ecns(created_at);

-- ============================================
-- 验收相关索引
-- ============================================

-- 验收订单索引
CREATE INDEX IF NOT EXISTS idx_acceptance_orders_project_id ON acceptance_orders(project_id);
CREATE INDEX IF NOT EXISTS idx_acceptance_orders_type ON acceptance_orders(type);
CREATE INDEX IF NOT EXISTS idx_acceptance_orders_status ON acceptance_orders(status);

-- ============================================
-- 外协相关索引
-- ============================================

-- 外协供应商索引
CREATE INDEX IF NOT EXISTS idx_outsourcing_vendors_name ON outsourcing_vendors(name);
CREATE INDEX IF NOT EXISTS idx_outsourcing_vendors_status ON outsourcing_vendors(status);

-- 外协订单索引
CREATE INDEX IF NOT EXISTS idx_outsourcing_orders_vendor_id ON outsourcing_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_orders_status ON outsourcing_orders(status);
CREATE INDEX IF NOT EXISTS idx_outsourcing_orders_created_at ON outsourcing_orders(created_at);

-- ============================================
-- 预警和异常相关索引
-- ============================================

-- 预警记录索引
CREATE INDEX IF NOT EXISTS idx_alert_records_project_id ON alert_records(project_id);
CREATE INDEX IF NOT EXISTS idx_alert_records_level ON alert_records(level);
CREATE INDEX IF NOT EXISTS idx_alert_records_status ON alert_records(status);
CREATE INDEX IF NOT EXISTS idx_alert_records_created_at ON alert_records(created_at);

-- 异常事件索引
CREATE INDEX IF NOT EXISTS idx_exception_events_project_id ON exception_events(project_id);
CREATE INDEX IF NOT EXISTS idx_exception_events_type ON exception_events(type);
CREATE INDEX IF NOT EXISTS idx_exception_events_created_at ON exception_events(created_at);

-- ============================================
-- 问题管理相关索引
-- ============================================

-- 问题索引
CREATE INDEX IF NOT EXISTS idx_issues_project_id ON issues(project_id);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_priority ON issues(priority);
CREATE INDEX IF NOT EXISTS idx_issues_assigned_to ON issues(assigned_to);
CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues(created_at);

-- ============================================
-- 绩效相关索引
-- ============================================

-- 绩效记录索引
CREATE INDEX IF NOT EXISTS idx_performance_records_user_id ON performance_records(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_records_period ON performance_records(period);
CREATE INDEX IF NOT EXISTS idx_performance_records_metric_type ON performance_records(metric_type);

-- ============================================
-- 复合索引（针对常用多字段查询）
-- ============================================

-- 项目列表常用组合查询
CREATE INDEX IF NOT EXISTS idx_projects_status_stage ON projects(status, stage);
CREATE INDEX IF NOT EXISTS idx_projects_health_status ON projects(health, status);
CREATE INDEX IF NOT EXISTS idx_projects_pm_status ON projects(pm_id, status);

-- 任务列表常用组合查询
CREATE INDEX IF NOT EXISTS idx_tasks_status_assigned ON tasks(status, assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_project_stage ON tasks(project_id, stage_code);

-- 采购订单常用组合查询
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_status ON purchase_orders(supplier_id, status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status_created ON purchase_orders(status, created_at);

-- ============================================
-- 创建完成提示
-- ============================================

-- 可以查询这些索引来验证是否创建成功
-- SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';
