-- TEN-03（全量铺开第五批，SHARED-DEFAULT 子集）：模板/规则/字典/配置类表，
-- 语义上是"可复用的定义"而非某个租户独占的业务记录（比如合同模板、
-- 奖金规则、工序字典）。参照 Role/ApiPermission/DataScopeRule/
-- MenuPermission 已验证过的 NULL=系统级共享 模式：只加列不回填，存量数据
-- 保持 tenant_id=NULL（=系统默认，所有租户可见），配合
-- app/core/database/tenant_scope.py 的 _SHARED_WHEN_NULL_MODEL_NAMES
-- 白名单，查询时用 (tenant_id == 当前租户) OR (tenant_id IS NULL) 放行，
-- 不会因为强行按租户过滤而让所有非默认租户看到空列表。后续如果某个
-- 租户想自定义自己的模板/规则，创建时显式传 tenant_id 即可，与共享
-- 默认数据共存。

ALTER TABLE acceptance_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_templates_tenant ON acceptance_templates(tenant_id);

ALTER TABLE template_categories ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_template_categories_tenant ON template_categories(tenant_id);

ALTER TABLE template_check_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_template_check_items_tenant ON template_check_items(tenant_id);

ALTER TABLE alert_rule_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_rule_templates_tenant ON alert_rule_templates(tenant_id);

ALTER TABLE alert_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_tenant ON alert_rules(tenant_id);

ALTER TABLE approval_routing_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_routing_rules_tenant ON approval_routing_rules(tenant_id);

ALTER TABLE approval_template_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_template_versions_tenant ON approval_template_versions(tenant_id);

ALTER TABLE approval_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_templates_tenant ON approval_templates(tenant_id);

ALTER TABLE mes_assembly_template ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_assembly_template_tenant ON mes_assembly_template(tenant_id);

ALTER TABLE mes_category_stage_mapping ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_category_stage_mapping_tenant ON mes_category_stage_mapping(tenant_id);

ALTER TABLE mes_shortage_alert_rule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_shortage_alert_rule_tenant ON mes_shortage_alert_rule(tenant_id);

ALTER TABLE bonus_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bonus_rules_tenant ON bonus_rules(tenant_id);

ALTER TABLE project_cost_allocation_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_cost_allocation_rules_tenant ON project_cost_allocation_rules(tenant_id);

ALTER TABLE culture_wall_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_culture_wall_config_tenant ON culture_wall_config(tenant_id);

ALTER TABLE dashboard_chart_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_dashboard_chart_configs_tenant ON dashboard_chart_configs(tenant_id);

ALTER TABLE ecn_types ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_types_tenant ON ecn_types(tenant_id);

ALTER TABLE ecn_solution_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_solution_templates_tenant ON ecn_solution_templates(tenant_id);

ALTER TABLE engineer_dimension_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_engineer_dimension_config_tenant ON engineer_dimension_config(tenant_id);

ALTER TABLE hourly_rate_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hourly_rate_configs_tenant ON hourly_rate_configs(tenant_id);

ALTER TABLE issue_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_issue_templates_tenant ON issue_templates(tenant_id);

ALTER TABLE solution_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_solution_templates_tenant ON solution_templates(tenant_id);

ALTER TABLE management_rhythm_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_management_rhythm_config_tenant ON management_rhythm_config(tenant_id);

ALTER TABLE meeting_report_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_meeting_report_config_tenant ON meeting_report_config(tenant_id);

ALTER TABLE material_categories ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_categories_tenant ON material_categories(tenant_id);

ALTER TABLE otd_threshold_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_otd_threshold_configs_tenant ON otd_threshold_configs(tenant_id);

ALTER TABLE evaluation_weight_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_evaluation_weight_config_tenant ON evaluation_weight_config(tenant_id);

ALTER TABLE permission_groups ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_permission_groups_tenant ON permission_groups(tenant_id);

ALTER TABLE role_menus ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_role_menus_tenant ON role_menus(tenant_id);

ALTER TABLE presale_solution_template ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_solution_template_tenant ON presale_solution_template(tenant_id);

ALTER TABLE technical_parameter_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_technical_parameter_templates_tenant ON technical_parameter_templates(tenant_id);

ALTER TABLE presale_ai_config ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_config_tenant ON presale_ai_config(tenant_id);

ALTER TABLE quotation_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quotation_templates_tenant ON quotation_templates(tenant_id);

ALTER TABLE presale_solution_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_solution_templates_tenant ON presale_solution_templates(tenant_id);

ALTER TABLE material_alert_rule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_alert_rule_tenant ON material_alert_rule(tenant_id);

ALTER TABLE process_dict ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_process_dict_tenant ON process_dict(tenant_id);

ALTER TABLE quality_alert_rule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quality_alert_rule_tenant ON quality_alert_rule(tenant_id);

ALTER TABLE wbs_template_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_wbs_template_tasks_tenant ON wbs_template_tasks(tenant_id);

ALTER TABLE wbs_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_wbs_templates_tenant ON wbs_templates(tenant_id);

ALTER TABLE benchmark_configurations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_benchmark_configurations_tenant ON benchmark_configurations(tenant_id);

ALTER TABLE cost_alert_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_rules_tenant ON cost_alert_rules(tenant_id);

ALTER TABLE project_template_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_template_versions_tenant ON project_template_versions(tenant_id);

ALTER TABLE project_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_templates_tenant ON project_templates(tenant_id);

ALTER TABLE project_role_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_role_configs_tenant ON project_role_configs(tenant_id);

ALTER TABLE project_role_types ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_role_types_tenant ON project_role_types(tenant_id);

ALTER TABLE rd_cost_allocation_rule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_cost_allocation_rule_tenant ON rd_cost_allocation_rule(tenant_id);

ALTER TABLE rd_cost_type ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_cost_type_tenant ON rd_cost_type(tenant_id);

ALTER TABLE rd_project_category ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_project_category_tenant ON rd_project_category(tenant_id);

ALTER TABLE import_template ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_import_template_tenant ON import_template(tenant_id);

ALTER TABLE report_template ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_template_tenant ON report_template(tenant_id);

ALTER TABLE assessment_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_assessment_templates_tenant ON assessment_templates(tenant_id);

ALTER TABLE contract_template_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_template_versions_tenant ON contract_template_versions(tenant_id);

ALTER TABLE contract_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_templates_tenant ON contract_templates(tenant_id);

ALTER TABLE margin_alert_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_margin_alert_configs_tenant ON margin_alert_configs(tenant_id);

ALTER TABLE cpq_rule_sets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cpq_rule_sets_tenant ON cpq_rule_sets(tenant_id);

ALTER TABLE quote_cost_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_cost_templates_tenant ON quote_cost_templates(tenant_id);

ALTER TABLE quote_template_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_template_versions_tenant ON quote_template_versions(tenant_id);

ALTER TABLE quote_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_templates_tenant ON quote_templates(tenant_id);

ALTER TABLE stage_dwell_time_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_dwell_time_configs_tenant ON stage_dwell_time_configs(tenant_id);

ALTER TABLE stage_gate_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_gate_configs_tenant ON stage_gate_configs(tenant_id);

ALTER TABLE scoring_rules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_scoring_rules_tenant ON scoring_rules(tenant_id);

ALTER TABLE sales_ranking_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_ranking_configs_tenant ON sales_ranking_configs(tenant_id);

ALTER TABLE scheduler_task_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_scheduler_task_configs_tenant ON scheduler_task_configs(tenant_id);

ALTER TABLE satisfaction_survey_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_satisfaction_survey_templates_tenant ON satisfaction_survey_templates(tenant_id);

ALTER TABLE hr_tag_dict ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_tag_dict_tenant ON hr_tag_dict(tenant_id);

ALTER TABLE stage_templates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_templates_tenant ON stage_templates(tenant_id);

ALTER TABLE standard_cost_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_standard_cost_history_tenant ON standard_cost_history(tenant_id);

ALTER TABLE standard_costs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_standard_costs_tenant ON standard_costs(tenant_id);

ALTER TABLE timesheet_rule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_timesheet_rule_tenant ON timesheet_rule(tenant_id);

ALTER TABLE role_api_permissions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_role_api_permissions_tenant ON role_api_permissions(tenant_id);

ALTER TABLE solution_credit_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_solution_credit_configs_tenant ON solution_credit_configs(tenant_id);

ALTER TABLE job_levels ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_job_levels_tenant ON job_levels(tenant_id);

ALTER TABLE job_duty_template ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_job_duty_template_tenant ON job_duty_template(tenant_id);

