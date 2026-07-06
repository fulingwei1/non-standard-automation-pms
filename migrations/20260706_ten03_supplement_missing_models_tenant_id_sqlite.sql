-- TEN-03补遗批（2026-07-06）：batch4 Base.registry.mappers 普查时未被 import 的漏网模型，
-- 共45张表补 tenant_id。口径同 ten03 前五批：STRICT 业务表回填默认租户；
-- SHARED 字典/模板/日历表只加列不回填（NULL=共享，见 tenant_scope._SHARED_WHEN_NULL_MODEL_NAMES）。
-- report_template 的 DB 列已存在（幽灵列），本批只补模型声明，无DDL。

ALTER TABLE warehouses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_warehouses_tenant ON warehouses(tenant_id);
UPDATE warehouses SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE warehouse_locations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_tenant ON warehouse_locations(tenant_id);
UPDATE warehouse_locations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE inbound_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_inbound_orders_tenant ON inbound_orders(tenant_id);
UPDATE inbound_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE inbound_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_inbound_order_items_tenant ON inbound_order_items(tenant_id);
UPDATE inbound_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outbound_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outbound_orders_tenant ON outbound_orders(tenant_id);
UPDATE outbound_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outbound_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outbound_order_items_tenant ON outbound_order_items(tenant_id);
UPDATE outbound_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE inventory ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_inventory_tenant ON inventory(tenant_id);
UPDATE inventory SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE stock_count_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stock_count_orders_tenant ON stock_count_orders(tenant_id);
UPDATE stock_count_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE stock_count_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stock_count_items_tenant ON stock_count_items(tenant_id);
UPDATE stock_count_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_requirements ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_requirements_tenant ON project_requirements(tenant_id);
UPDATE project_requirements SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE engineer_recommendations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_engineer_recommendations_tenant ON engineer_recommendations(tenant_id);
UPDATE engineer_recommendations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_risks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_risks_tenant ON project_risks(tenant_id);
UPDATE project_risks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_schedule_plans ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_schedule_plans_tenant ON project_schedule_plans(tenant_id);
UPDATE project_schedule_plans SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE audit_pack_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_audit_pack_requests_tenant ON audit_pack_requests(tenant_id);
UPDATE audit_pack_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE company_certifications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_company_certifications_tenant ON company_certifications(tenant_id);
UPDATE company_certifications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_proposals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_proposals_tenant ON presale_proposals(tenant_id);
UPDATE presale_proposals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_proposal_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_proposal_versions_tenant ON presale_proposal_versions(tenant_id);
UPDATE presale_proposal_versions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_usage_feedback ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_usage_feedback_tenant ON presale_usage_feedback(tenant_id);
UPDATE presale_usage_feedback SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_agent_metrics ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_agent_metrics_tenant ON presale_agent_metrics(tenant_id);
UPDATE presale_agent_metrics SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_agent_revisions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_agent_revisions_tenant ON presale_agent_revisions(tenant_id);
UPDATE presale_agent_revisions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE advantage_products ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_advantage_products_tenant ON advantage_products(tenant_id);
UPDATE advantage_products SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE new_product_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_new_product_requests_tenant ON new_product_requests(tenant_id);
UPDATE new_product_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ai_wbs_suggestions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_wbs_suggestions_tenant ON ai_wbs_suggestions(tenant_id);
UPDATE ai_wbs_suggestions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ai_resource_allocations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_resource_allocations_tenant ON ai_resource_allocations(tenant_id);
UPDATE ai_resource_allocations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE company_profile ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_company_profile_tenant ON company_profile(tenant_id);
UPDATE company_profile SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE competitors ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_competitors_tenant ON competitors(tenant_id);
UPDATE competitors SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE industries ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_industries_tenant ON industries(tenant_id);

ALTER TABLE industry_category_mappings ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_industry_category_mappings_tenant ON industry_category_mappings(tenant_id);

ALTER TABLE advantage_product_categories ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_advantage_product_categories_tenant ON advantage_product_categories(tenant_id);

ALTER TABLE holidays ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_holidays_tenant ON holidays(tenant_id);

ALTER TABLE project_template_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_template_configs_tenant ON project_template_configs(tenant_id);

ALTER TABLE stage_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_configs_tenant ON stage_configs(tenant_id);

ALTER TABLE node_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_node_configs_tenant ON node_configs(tenant_id);

ALTER TABLE ai_project_plan_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_project_plan_templates_tenant ON ai_project_plan_templates(tenant_id);

-- 以下 11 张表 DB 中不存在，按模型 DDL 直接创建（自带 tenant_id）：
CREATE TABLE project_team_plans (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	plan_no VARCHAR(50), 
	project_id INTEGER NOT NULL, 
	project_name VARCHAR(200), 
	version INTEGER, 
	generated_by VARCHAR(50), 
	total_members INTEGER, 
	total_estimated_hours FLOAT, 
	estimated_duration_days INTEGER, 
	overall_score FLOAT, 
	skill_coverage FLOAT, 
	capacity_balance FLOAT, 
	cost_efficiency FLOAT, 
	team_structure TEXT, 
	role_assignments TEXT, 
	timeline TEXT, 
	advantages TEXT, 
	risks TEXT, 
	recommendations TEXT, 
	status VARCHAR(20), 
	submitted_by INTEGER, 
	submitted_at DATETIME, 
	approved_by INTEGER, 
	approved_at DATETIME, 
	rejected_reason TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (plan_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(submitted_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_project_team_plans_tenant ON project_team_plans(tenant_id);

CREATE TABLE project_team_members (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	team_plan_id INTEGER NOT NULL, 
	engineer_id INTEGER NOT NULL, 
	engineer_name VARCHAR(100), 
	role VARCHAR(50) NOT NULL, 
	role_name VARCHAR(100), 
	responsibilities TEXT, 
	estimated_hours FLOAT, 
	start_date DATE, 
	end_date DATE, 
	allocation_percentage FLOAT, 
	match_score FLOAT, 
	match_reason TEXT, 
	status VARCHAR(20), 
	confirmed_by_engineer BOOLEAN, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(team_plan_id) REFERENCES project_team_plans (id), 
	FOREIGN KEY(engineer_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_project_team_members_tenant ON project_team_members(tenant_id);

CREATE TABLE project_team_approvals (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	approval_no VARCHAR(50), 
	team_plan_id INTEGER NOT NULL, 
	approver_id INTEGER NOT NULL, 
	approver_name VARCHAR(100), 
	approver_role VARCHAR(50), 
	decision VARCHAR(20) NOT NULL, 
	comments TEXT, 
	modifications TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (approval_no), 
	FOREIGN KEY(team_plan_id) REFERENCES project_team_plans (id), 
	FOREIGN KEY(approver_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_project_team_approvals_tenant ON project_team_approvals(tenant_id);

CREATE TABLE schedule_tasks (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	schedule_plan_id INTEGER NOT NULL, 
	task_no VARCHAR(50), 
	task_name VARCHAR(200) NOT NULL, 
	task_type VARCHAR(50), 
	phase VARCHAR(50), 
	planned_start_date DATE, 
	planned_end_date DATE, 
	duration_days INTEGER, 
	working_hours FLOAT, 
	predecessor_tasks TEXT, 
	dependency_type VARCHAR(20), 
	lag_days INTEGER, 
	assigned_engineer_id INTEGER, 
	assigned_engineer_name VARCHAR(100), 
	allocation_percentage FLOAT, 
	base_duration INTEGER, 
	efficiency_adjusted_duration INTEGER, 
	efficiency_factors TEXT, 
	status VARCHAR(20), 
	progress_percentage FLOAT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(schedule_plan_id) REFERENCES project_schedule_plans (id), 
	FOREIGN KEY(assigned_engineer_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_schedule_tasks_tenant ON schedule_tasks(tenant_id);

-- 补遗（模型不在 app.main import 链上，显式导入后生成）：
CREATE TABLE timesheet_reminder_config (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	rule_code VARCHAR(50) NOT NULL, 
	rule_name VARCHAR(100) NOT NULL, 
	reminder_type VARCHAR(17) NOT NULL, 
	apply_to_departments JSON, 
	apply_to_roles JSON, 
	apply_to_users JSON, 
	rule_parameters JSON, 
	notification_channels JSON, 
	notification_template TEXT, 
	remind_frequency VARCHAR(20), 
	max_reminders_per_day INTEGER, 
	priority VARCHAR(20), 
	is_active BOOLEAN, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (rule_code), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_timesheet_reminder_config_tenant ON timesheet_reminder_config(tenant_id);

CREATE TABLE timesheet_reminder_record (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	reminder_no VARCHAR(50) NOT NULL, 
	reminder_type VARCHAR(17) NOT NULL, 
	config_id INTEGER, 
	user_id INTEGER NOT NULL, 
	user_name VARCHAR(50), 
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	source_type VARCHAR(50), 
	source_id INTEGER, 
	extra_data JSON, 
	status VARCHAR(9), 
	notification_channels JSON, 
	sent_at DATETIME, 
	read_at DATETIME, 
	dismissed_at DATETIME, 
	dismissed_by INTEGER, 
	dismissed_reason TEXT, 
	resolved_at DATETIME, 
	priority VARCHAR(20), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (reminder_no), 
	FOREIGN KEY(config_id) REFERENCES timesheet_reminder_config (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(dismissed_by) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_timesheet_reminder_record_tenant ON timesheet_reminder_record(tenant_id);

CREATE TABLE timesheet_anomaly_record (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	timesheet_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	user_name VARCHAR(50), 
	anomaly_type VARCHAR(17) NOT NULL, 
	description TEXT NOT NULL, 
	anomaly_data JSON, 
	severity VARCHAR(20), 
	detected_at DATETIME NOT NULL, 
	is_resolved BOOLEAN, 
	resolved_at DATETIME, 
	resolved_by INTEGER, 
	resolution_note TEXT, 
	reminder_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(timesheet_id) REFERENCES timesheet (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(resolved_by) REFERENCES users (id), 
	FOREIGN KEY(reminder_id) REFERENCES timesheet_reminder_record (id)
);
CREATE INDEX IF NOT EXISTS idx_timesheet_anomaly_record_tenant ON timesheet_anomaly_record(tenant_id);

CREATE TABLE knowledge_entries (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	entry_code VARCHAR(50) NOT NULL, 
	knowledge_type VARCHAR(14) NOT NULL, 
	source_type VARCHAR(6) NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	summary TEXT NOT NULL, 
	detail TEXT, 
	problem_description TEXT, 
	solution TEXT, 
	root_cause TEXT, 
	impact TEXT, 
	prevention TEXT, 
	source_project_id INTEGER, 
	source_record_id INTEGER, 
	source_record_type VARCHAR(30), 
	project_type VARCHAR(50), 
	product_category VARCHAR(50), 
	industry VARCHAR(50), 
	customer_id INTEGER, 
	applicable_stages JSON, 
	tags JSON, 
	risk_type VARCHAR(30), 
	issue_category VARCHAR(30), 
	change_type VARCHAR(30), 
	view_count INTEGER, 
	cite_count INTEGER, 
	usefulness_score FLOAT, 
	vote_count INTEGER, 
	status VARCHAR(9) NOT NULL, 
	ai_generated BOOLEAN, 
	ai_confidence NUMERIC(5, 4), 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	UNIQUE (entry_code), 
	FOREIGN KEY(source_project_id) REFERENCES projects (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_entries_tenant ON knowledge_entries(tenant_id);

CREATE TABLE knowledge_alerts (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	target_project_id INTEGER NOT NULL, 
	knowledge_entry_id INTEGER NOT NULL, 
	match_reason VARCHAR(200), 
	match_score FLOAT, 
	is_read BOOLEAN, 
	is_adopted BOOLEAN, 
	feedback TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(target_project_id) REFERENCES projects (id), 
	FOREIGN KEY(knowledge_entry_id) REFERENCES knowledge_entries (id)
);
CREATE INDEX IF NOT EXISTS idx_knowledge_alerts_tenant ON knowledge_alerts(tenant_id);

CREATE TABLE cost_breakdowns (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	machine_id INTEGER, 
	bom_item_id INTEGER, 
	cost_category VARCHAR(50) NOT NULL, 
	cost_subcategory VARCHAR(100), 
	source_type VARCHAR(50), 
	source_id INTEGER, 
	source_ref VARCHAR(100), 
	item_name VARCHAR(200) NOT NULL, 
	item_code VARCHAR(100), 
	specification VARCHAR(500), 
	unit VARCHAR(20), 
	quantity NUMERIC(10, 4), 
	unit_price NUMERIC(12, 4), 
	estimated_amount NUMERIC(14, 2), 
	actual_amount NUMERIC(14, 2), 
	variance_amount NUMERIC(14, 2), 
	supplier_id INTEGER, 
	supplier_name VARCHAR(200), 
	is_confirmed BOOLEAN, 
	confirmed_by INTEGER, 
	confirmed_at DATETIME, 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(machine_id) REFERENCES machines (id), 
	FOREIGN KEY(bom_item_id) REFERENCES bom_items (id), 
	FOREIGN KEY(supplier_id) REFERENCES vendors (id), 
	FOREIGN KEY(confirmed_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS idx_cost_breakdowns_tenant ON cost_breakdowns(tenant_id);

CREATE TABLE project_cost_summaries (
	tenant_id INTEGER, 
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	cost_category VARCHAR(50) NOT NULL, 
	estimated_amount NUMERIC(14, 2), 
	actual_amount NUMERIC(14, 2), 
	variance_amount NUMERIC(14, 2), 
	variance_ratio NUMERIC(5, 2), 
	estimated_ratio NUMERIC(5, 2), 
	actual_ratio NUMERIC(5, 2), 
	item_count INTEGER, 
	confirmed_count INTEGER, 
	calculated_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE INDEX IF NOT EXISTS idx_project_cost_summaries_tenant ON project_cost_summaries(tenant_id);
