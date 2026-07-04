-- TEN-03（全量铺开第四批）：剩余约 400 张真正的业务实体表批量加 tenant_id。
-- 口径同前几批：全部存量数据归入默认租户（id=1 金凯博，active）；新增行由
-- app/core/database/tenant_scope.py 的 before_flush 钩子按当前请求租户
-- 上下文自动补全，不需要逐个创建入口手工传参。
--
-- 范围说明：本批次排除了系统基础设施类表（缓存/审计日志/会话/迁移追踪/
-- 任务队列/调度器配置等，约30张）与共享主数据/目录/字典/模板/规则/
-- 权限菜单类表（约100张，多为"全租户共享默认配置"语义，强行加租户过滤
-- 反而会破坏共享可见性）——这些表被认为不需要或不适合直接租户隔离，
-- 已在功能审计台账中说明排除理由，非本迁移遗漏。
--
-- 另有 16 张表当前 data/app.db 里尚不存在（模型已声明但表未创建，
-- 属既有缺口，与本次改动无关）：模型层已经补了 tenant_id 声明，等这些表
-- 将来被创建（无论是 create_all 还是专门迁移）时会自带这一列，此处跳过
-- ALTER TABLE 避免对不存在的表报错。

ALTER TABLE acceptance_issues ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_issues_tenant ON acceptance_issues(tenant_id);
UPDATE acceptance_issues SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_order_items_tenant ON acceptance_order_items(tenant_id);
UPDATE acceptance_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_orders_tenant ON acceptance_orders(tenant_id);
UPDATE acceptance_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_reports ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_reports_tenant ON acceptance_reports(tenant_id);
UPDATE acceptance_reports SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_signatures ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_signatures_tenant ON acceptance_signatures(tenant_id);
UPDATE acceptance_signatures SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE issue_follow_ups ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_issue_follow_ups_tenant ON issue_follow_ups(tenant_id);
UPDATE issue_follow_ups SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_assets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_assets_tenant ON admin_assets(tenant_id);
UPDATE admin_assets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_expenses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_expenses_tenant ON admin_expenses(tenant_id);
UPDATE admin_expenses SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_supplies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_supplies_tenant ON admin_supplies(tenant_id);
UPDATE admin_supplies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_supply_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_supply_requests_tenant ON admin_supply_requests(tenant_id);
UPDATE admin_supply_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_vehicle_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_vehicle_requests_tenant ON admin_vehicle_requests(tenant_id);
UPDATE admin_vehicle_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE admin_vehicles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_admin_vehicles_tenant ON admin_vehicles(tenant_id);
UPDATE admin_vehicles SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE after_sales_feedback ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_after_sales_feedback_tenant ON after_sales_feedback(tenant_id);
UPDATE after_sales_feedback SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE after_sales_maintenance ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_after_sales_maintenance_tenant ON after_sales_maintenance(tenant_id);
UPDATE after_sales_maintenance SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE after_sales_support_tickets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_after_sales_support_tickets_tenant ON after_sales_support_tickets(tenant_id);
UPDATE after_sales_support_tickets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ai_output_feedbacks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_output_feedbacks_tenant ON ai_output_feedbacks(tenant_id);
UPDATE ai_output_feedbacks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE alert_notifications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_tenant ON alert_notifications(tenant_id);
UPDATE alert_notifications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE alert_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_records_tenant ON alert_records(tenant_id);
UPDATE alert_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE alert_statistics ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_statistics_tenant ON alert_statistics(tenant_id);
UPDATE alert_statistics SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE alert_subscriptions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_tenant ON alert_subscriptions(tenant_id);
UPDATE alert_subscriptions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_actions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_actions_tenant ON exception_actions(tenant_id);
UPDATE exception_actions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_escalations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_escalations_tenant ON exception_escalations(tenant_id);
UPDATE exception_escalations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_events ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_events_tenant ON exception_events(tenant_id);
UPDATE exception_events SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_health_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_health_snapshots_tenant ON project_health_snapshots(tenant_id);
UPDATE project_health_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_delegates ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_delegates_tenant ON approval_delegates(tenant_id);
UPDATE approval_delegates SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_flow_definitions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_flow_definitions_tenant ON approval_flow_definitions(tenant_id);
UPDATE approval_flow_definitions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_node_definitions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_node_definitions_tenant ON approval_node_definitions(tenant_id);
UPDATE approval_node_definitions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_instances ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_instances_tenant ON approval_instances(tenant_id);
UPDATE approval_instances SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_comments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_comments_tenant ON approval_comments(tenant_id);
UPDATE approval_comments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_carbon_copies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_carbon_copies_tenant ON approval_carbon_copies(tenant_id);
UPDATE approval_carbon_copies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_countersign_results ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_countersign_results_tenant ON approval_countersign_results(tenant_id);
UPDATE approval_countersign_results SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_tasks_tenant ON approval_tasks(tenant_id);
UPDATE approval_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bom_item_assembly_attrs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bom_item_assembly_attrs_tenant ON bom_item_assembly_attrs(tenant_id);
UPDATE bom_item_assembly_attrs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_assembly_stage ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_assembly_stage_tenant ON mes_assembly_stage(tenant_id);
UPDATE mes_assembly_stage SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_kit_rate_snapshot ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_kit_rate_snapshot_tenant ON mes_kit_rate_snapshot(tenant_id);
UPDATE mes_kit_rate_snapshot SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_material_readiness ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_material_readiness_tenant ON mes_material_readiness(tenant_id);
UPDATE mes_material_readiness SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_scheduling_suggestion ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_scheduling_suggestion_tenant ON mes_scheduling_suggestion(tenant_id);
UPDATE mes_scheduling_suggestion SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_shortage_detail ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_shortage_detail_tenant ON mes_shortage_detail(tenant_id);
UPDATE mes_shortage_detail SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bonus_allocation_sheets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bonus_allocation_sheets_tenant ON bonus_allocation_sheets(tenant_id);
UPDATE bonus_allocation_sheets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bonus_calculations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bonus_calculations_tenant ON bonus_calculations(tenant_id);
UPDATE bonus_calculations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bonus_distributions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bonus_distributions_tenant ON bonus_distributions(tenant_id);
UPDATE bonus_distributions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE team_bonus_allocations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_team_bonus_allocations_tenant ON team_bonus_allocations(tenant_id);
UPDATE team_bonus_allocations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_budget_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_budget_items_tenant ON project_budget_items(tenant_id);
UPDATE project_budget_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_budgets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_budgets_tenant ON project_budgets(tenant_id);
UPDATE project_budgets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_tracking ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_tracking_tenant ON acceptance_tracking(tenant_id);
UPDATE acceptance_tracking SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE acceptance_tracking_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_acceptance_tracking_records_tenant ON acceptance_tracking_records(tenant_id);
UPDATE acceptance_tracking_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bidding_documents ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bidding_documents_tenant ON bidding_documents(tenant_id);
UPDATE bidding_documents SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bidding_projects ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bidding_projects_tenant ON bidding_projects(tenant_id);
UPDATE bidding_projects SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_reviews ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_reviews_tenant ON contract_reviews(tenant_id);
UPDATE contract_reviews SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_seal_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_seal_records_tenant ON contract_seal_records(tenant_id);
UPDATE contract_seal_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE delivery_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_delivery_order_items_tenant ON delivery_order_items(tenant_id);
UPDATE delivery_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE delivery_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_delivery_orders_tenant ON delivery_orders(tenant_id);
UPDATE delivery_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE document_archives ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_document_archives_tenant ON document_archives(tenant_id);
UPDATE document_archives SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE invoice_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_invoice_requests_tenant ON invoice_requests(tenant_id);
UPDATE invoice_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE payment_reminders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_tenant ON payment_reminders(tenant_id);
UPDATE payment_reminders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE reconciliations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_reconciliations_tenant ON reconciliations(tenant_id);
UPDATE reconciliations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE customer_supplier_registrations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customer_supplier_registrations_tenant ON customer_supplier_registrations(tenant_id);
UPDATE customer_supplier_registrations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_order_items_tenant ON sales_order_items(tenant_id);
UPDATE sales_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE change_impact_analysis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_change_impact_analysis_tenant ON change_impact_analysis(tenant_id);
UPDATE change_impact_analysis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE change_response_suggestions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_change_response_suggestions_tenant ON change_response_suggestions(tenant_id);
UPDATE change_response_suggestions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE change_approval_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_change_approval_records_tenant ON change_approval_records(tenant_id);
UPDATE change_approval_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE change_notifications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_change_notifications_tenant ON change_notifications(tenant_id);
UPDATE change_notifications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE change_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_change_requests_tenant ON change_requests(tenant_id);
UPDATE change_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE cost_optimization_suggestions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cost_optimization_suggestions_tenant ON cost_optimization_suggestions(tenant_id);
UPDATE cost_optimization_suggestions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE cost_prediction ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cost_prediction_tenant ON cost_prediction(tenant_id);
UPDATE cost_prediction SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE culture_wall_content ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_culture_wall_content_tenant ON culture_wall_content(tenant_id);
UPDATE culture_wall_content SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE culture_wall_read_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_culture_wall_read_record_tenant ON culture_wall_read_record(tenant_id);
UPDATE culture_wall_read_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE personal_goal ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_personal_goal_tenant ON personal_goal(tenant_id);
UPDATE personal_goal SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE earned_value_data ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_earned_value_data_tenant ON earned_value_data(tenant_id);
UPDATE earned_value_data SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE earned_value_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_earned_value_snapshots_tenant ON earned_value_snapshots(tenant_id);
UPDATE earned_value_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_approval_matrix ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_approval_matrix_tenant ON ecn_approval_matrix(tenant_id);
UPDATE ecn_approval_matrix SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_tenant ON ecn(tenant_id);
UPDATE ecn SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_cost_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_cost_records_tenant ON ecn_cost_records(tenant_id);
UPDATE ecn_cost_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_approvals_tenant ON ecn_approvals(tenant_id);
UPDATE ecn_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_evaluations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_evaluations_tenant ON ecn_evaluations(tenant_id);
UPDATE ecn_evaluations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_tasks_tenant ON ecn_tasks(tenant_id);
UPDATE ecn_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_affected_materials ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_affected_materials_tenant ON ecn_affected_materials(tenant_id);
UPDATE ecn_affected_materials SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_affected_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_affected_orders_tenant ON ecn_affected_orders(tenant_id);
UPDATE ecn_affected_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_bom_changes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_bom_changes_tenant ON ecn_bom_changes(tenant_id);
UPDATE ecn_bom_changes SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_bom_impacts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_bom_impacts_tenant ON ecn_bom_impacts(tenant_id);
UPDATE ecn_bom_impacts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_execution_progress ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_execution_progress_tenant ON ecn_execution_progress(tenant_id);
UPDATE ecn_execution_progress SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_material_dispositions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_material_dispositions_tenant ON ecn_material_dispositions(tenant_id);
UPDATE ecn_material_dispositions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_stakeholders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_stakeholders_tenant ON ecn_stakeholders(tenant_id);
UPDATE ecn_stakeholders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_responsibilities ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_responsibilities_tenant ON ecn_responsibilities(tenant_id);
UPDATE ecn_responsibilities SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE engineer_task_assignments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_engineer_task_assignments_tenant ON engineer_task_assignments(tenant_id);
UPDATE engineer_task_assignments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE collaboration_rating ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_collaboration_rating_tenant ON collaboration_rating(tenant_id);
UPDATE collaboration_rating SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE engineer_profile ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_engineer_profile_tenant ON engineer_profile(tenant_id);
UPDATE engineer_profile SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE knowledge_contribution ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_knowledge_contribution_tenant ON knowledge_contribution(tenant_id);
UPDATE knowledge_contribution SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE component_selection ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_component_selection_tenant ON component_selection(tenant_id);
UPDATE component_selection SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE electrical_drawing_version ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_electrical_drawing_version_tenant ON electrical_drawing_version(tenant_id);
UPDATE electrical_drawing_version SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE electrical_fault_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_electrical_fault_record_tenant ON electrical_fault_record(tenant_id);
UPDATE electrical_fault_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE plc_module_library ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_plc_module_library_tenant ON plc_module_library(tenant_id);
UPDATE plc_module_library SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE plc_program_version ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_plc_program_version_tenant ON plc_program_version(tenant_id);
UPDATE plc_program_version SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE design_reuse_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_design_reuse_record_tenant ON design_reuse_record(tenant_id);
UPDATE design_reuse_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE design_review ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_design_review_tenant ON design_review(tenant_id);
UPDATE design_review SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mechanical_debug_issue ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mechanical_debug_issue_tenant ON mechanical_debug_issue(tenant_id);
UPDATE mechanical_debug_issue SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE code_module ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_code_module_tenant ON code_module(tenant_id);
UPDATE code_module SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE code_review_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_code_review_record_tenant ON code_review_record(tenant_id);
UPDATE code_review_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE test_bug_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_test_bug_record_tenant ON test_bug_record(tenant_id);
UPDATE test_bug_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE field_checkins ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_field_checkins_tenant ON field_checkins(tenant_id);
UPDATE field_checkins SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE field_issues ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_field_issues_tenant ON field_issues(tenant_id);
UPDATE field_issues SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE field_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_field_tasks_tenant ON field_tasks(tenant_id);
UPDATE field_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE installation_dispatch_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_installation_dispatch_orders_tenant ON installation_dispatch_orders(tenant_id);
UPDATE installation_dispatch_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE issue_follow_up_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_issue_follow_up_records_tenant ON issue_follow_up_records(tenant_id);
UPDATE issue_follow_up_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE issue_statistics_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_issue_statistics_snapshots_tenant ON issue_statistics_snapshots(tenant_id);
UPDATE issue_statistics_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE issues ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_issues_tenant ON issues(tenant_id);
UPDATE issues SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE meeting_action_item ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_meeting_action_item_tenant ON meeting_action_item(tenant_id);
UPDATE meeting_action_item SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE meeting_report ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_meeting_report_tenant ON meeting_report(tenant_id);
UPDATE meeting_report SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_metric_definition ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_metric_definition_tenant ON report_metric_definition(tenant_id);
UPDATE report_metric_definition SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE rhythm_dashboard_snapshot ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rhythm_dashboard_snapshot_tenant ON rhythm_dashboard_snapshot(tenant_id);
UPDATE rhythm_dashboard_snapshot SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE strategic_meeting ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_strategic_meeting_tenant ON strategic_meeting(tenant_id);
UPDATE strategic_meeting SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bom_headers ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bom_headers_tenant ON bom_headers(tenant_id);
UPDATE bom_headers SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE bom_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_bom_items_tenant ON bom_items(tenant_id);
UPDATE bom_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_shortages ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_shortages_tenant ON material_shortages(tenant_id);
UPDATE material_shortages SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_suppliers ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_suppliers_tenant ON material_suppliers(tenant_id);
UPDATE material_suppliers SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE materials ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_materials_tenant ON materials(tenant_id);
UPDATE materials SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE notification_settings ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_notification_settings_tenant ON notification_settings(tenant_id);
UPDATE notification_settings SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE notifications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_notifications_tenant ON notifications(tenant_id);
UPDATE notifications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_reminders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_reminders_tenant ON contract_reminders(tenant_id);
UPDATE contract_reminders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE departments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_departments_tenant ON departments(tenant_id);
UPDATE departments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE employee_contracts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_employee_contracts_tenant ON employee_contracts(tenant_id);
UPDATE employee_contracts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE employee_hr_profiles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_employee_hr_profiles_tenant ON employee_hr_profiles(tenant_id);
UPDATE employee_hr_profiles SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE employee_org_assignments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_employee_org_assignments_tenant ON employee_org_assignments(tenant_id);
UPDATE employee_org_assignments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE employees ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_employees_tenant ON employees(tenant_id);
UPDATE employees SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE hr_transactions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_transactions_tenant ON hr_transactions(tenant_id);
UPDATE hr_transactions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE organization_units ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_organization_units_tenant ON organization_units(tenant_id);
UPDATE organization_units SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE position_roles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_position_roles_tenant ON position_roles(tenant_id);
UPDATE position_roles SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE positions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_positions_tenant ON positions(tenant_id);
UPDATE positions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE salary_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_salary_records_tenant ON salary_records(tenant_id);
UPDATE salary_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE otd_risk_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_otd_risk_snapshots_tenant ON otd_risk_snapshots(tenant_id);
UPDATE otd_risk_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_deliveries ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_deliveries_tenant ON outsourcing_deliveries(tenant_id);
UPDATE outsourcing_deliveries SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_delivery_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_delivery_items_tenant ON outsourcing_delivery_items(tenant_id);
UPDATE outsourcing_delivery_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_evaluations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_evaluations_tenant ON outsourcing_evaluations(tenant_id);
UPDATE outsourcing_evaluations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_inspections ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_inspections_tenant ON outsourcing_inspections(tenant_id);
UPDATE outsourcing_inspections SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_order_items_tenant ON outsourcing_order_items(tenant_id);
UPDATE outsourcing_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_orders_tenant ON outsourcing_orders(tenant_id);
UPDATE outsourcing_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_payments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_payments_tenant ON outsourcing_payments(tenant_id);
UPDATE outsourcing_payments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE outsourcing_progress ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_outsourcing_progress_tenant ON outsourcing_progress(tenant_id);
UPDATE outsourcing_progress SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_adjustment_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_adjustment_history_tenant ON performance_adjustment_history(tenant_id);
UPDATE performance_adjustment_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_appeal ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_appeal_tenant ON performance_appeal(tenant_id);
UPDATE performance_appeal SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_contract_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_contract_items_tenant ON performance_contract_items(tenant_id);
UPDATE performance_contract_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_contracts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_contracts_tenant ON performance_contracts(tenant_id);
UPDATE performance_contracts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_ranking_snapshot ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_ranking_snapshot_tenant ON performance_ranking_snapshot(tenant_id);
UPDATE performance_ranking_snapshot SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_contribution ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_contribution_tenant ON project_contribution(tenant_id);
UPDATE project_contribution SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE monthly_work_summary ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_monthly_work_summary_tenant ON monthly_work_summary(tenant_id);
UPDATE monthly_work_summary SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_evaluation_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_evaluation_record_tenant ON performance_evaluation_record(tenant_id);
UPDATE performance_evaluation_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_indicator ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_indicator_tenant ON performance_indicator(tenant_id);
UPDATE performance_indicator SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_period ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_period_tenant ON performance_period(tenant_id);
UPDATE performance_period SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_evaluation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_evaluation_tenant ON performance_evaluation(tenant_id);
UPDATE performance_evaluation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE performance_result ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_performance_result_tenant ON performance_result(tenant_id);
UPDATE performance_result SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE role_data_scopes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_role_data_scopes_tenant ON role_data_scopes(tenant_id);
UPDATE role_data_scopes SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE accountability_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_accountability_records_tenant ON accountability_records(tenant_id);
UPDATE accountability_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pipeline_break_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pipeline_break_records_tenant ON pipeline_break_records(tenant_id);
UPDATE pipeline_break_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pipeline_health_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pipeline_health_snapshots_tenant ON pipeline_health_snapshots(tenant_id);
UPDATE pipeline_health_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pitfall_learning_progress ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pitfall_learning_progress_tenant ON pitfall_learning_progress(tenant_id);
UPDATE pitfall_learning_progress SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pitfall_recommendations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pitfall_recommendations_tenant ON pitfall_recommendations(tenant_id);
UPDATE pitfall_recommendations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pitfalls ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pitfalls_tenant ON pitfalls(tenant_id);
UPDATE pitfalls SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_change_request ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_change_request_tenant ON pmo_change_request(tenant_id);
UPDATE pmo_change_request SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_project_risk ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_project_risk_tenant ON pmo_project_risk(tenant_id);
UPDATE pmo_project_risk SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_meeting ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_meeting_tenant ON pmo_meeting(tenant_id);
UPDATE pmo_meeting SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_project_cost ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_project_cost_tenant ON pmo_project_cost(tenant_id);
UPDATE pmo_project_cost SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_project_initiation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_project_initiation_tenant ON pmo_project_initiation(tenant_id);
UPDATE pmo_project_initiation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_project_phase ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_project_phase_tenant ON pmo_project_phase(tenant_id);
UPDATE pmo_project_phase SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_project_closure ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_project_closure_tenant ON pmo_project_closure(tenant_id);
UPDATE pmo_project_closure SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE pmo_resource_allocation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_pmo_resource_allocation_tenant ON pmo_resource_allocation(tenant_id);
UPDATE pmo_resource_allocation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_customer_tech_profile ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_customer_tech_profile_tenant ON presale_customer_tech_profile(tenant_id);
UPDATE presale_customer_tech_profile SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_solution ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_solution_tenant ON presale_solution(tenant_id);
UPDATE presale_solution SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_solution_cost ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_solution_cost_tenant ON presale_solution_cost(tenant_id);
UPDATE presale_solution_cost SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_support_ticket ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_support_ticket_tenant ON presale_support_ticket(tenant_id);
UPDATE presale_support_ticket SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_tender_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_tender_record_tenant ON presale_tender_record(tenant_id);
UPDATE presale_tender_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ticket_deliverable ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_deliverable_tenant ON presale_ticket_deliverable(tenant_id);
UPDATE presale_ticket_deliverable SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ticket_progress ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ticket_progress_tenant ON presale_ticket_progress(tenant_id);
UPDATE presale_ticket_progress SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_workload ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_workload_tenant ON presale_workload(tenant_id);
UPDATE presale_workload SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_feedback ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_feedback_tenant ON presale_ai_feedback(tenant_id);
UPDATE presale_ai_feedback SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_usage_stats ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_usage_stats_tenant ON presale_ai_usage_stats(tenant_id);
UPDATE presale_ai_usage_stats SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_emotion_analysis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_emotion_analysis_tenant ON presale_ai_emotion_analysis(tenant_id);
UPDATE presale_ai_emotion_analysis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_qa ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_qa_tenant ON presale_ai_qa(tenant_id);
UPDATE presale_ai_qa SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_quotation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_quotation_tenant ON presale_ai_quotation(tenant_id);
UPDATE presale_ai_quotation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quotation_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quotation_approvals_tenant ON quotation_approvals(tenant_id);
UPDATE quotation_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quotation_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quotation_versions_tenant ON quotation_versions(tenant_id);
UPDATE quotation_versions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_requirement_analysis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_requirement_analysis_tenant ON presale_ai_requirement_analysis(tenant_id);
UPDATE presale_ai_requirement_analysis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_solution ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_solution_tenant ON presale_ai_solution(tenant_id);
UPDATE presale_ai_solution SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_emotion_trend ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_emotion_trend_tenant ON presale_emotion_trend(tenant_id);
UPDATE presale_emotion_trend SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_expenses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_expenses_tenant ON presale_expenses(tenant_id);
UPDATE presale_expenses SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_follow_up_reminder ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_follow_up_reminder_tenant ON presale_follow_up_reminder(tenant_id);
UPDATE presale_follow_up_reminder SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_knowledge_case ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_knowledge_case_tenant ON presale_knowledge_case(tenant_id);
UPDATE presale_knowledge_case SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_mobile_assistant_chat ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_mobile_assistant_chat_tenant ON presale_mobile_assistant_chat(tenant_id);
UPDATE presale_mobile_assistant_chat SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_mobile_offline_data ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_mobile_offline_data_tenant ON presale_mobile_offline_data(tenant_id);
UPDATE presale_mobile_offline_data SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_mobile_quick_estimate ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_mobile_quick_estimate_tenant ON presale_mobile_quick_estimate(tenant_id);
UPDATE presale_mobile_quick_estimate SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_visit_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_visit_record_tenant ON presale_visit_record(tenant_id);
UPDATE presale_visit_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE equipment ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_equipment_tenant ON equipment(tenant_id);
UPDATE equipment SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE equipment_maintenance ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_tenant ON equipment_maintenance(tenant_id);
UPDATE equipment_maintenance SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE equipment_oee_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_equipment_oee_record_tenant ON equipment_oee_record(tenant_id);
UPDATE equipment_oee_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_handling_flow ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_handling_flow_tenant ON exception_handling_flow(tenant_id);
UPDATE exception_handling_flow SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_knowledge ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_knowledge_tenant ON exception_knowledge(tenant_id);
UPDATE exception_knowledge SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE exception_pdca ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_exception_pdca_tenant ON exception_pdca(tenant_id);
UPDATE exception_pdca SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_requisition ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_requisition_tenant ON material_requisition(tenant_id);
UPDATE material_requisition SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_requisition_item ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_requisition_item_tenant ON material_requisition_item(tenant_id);
UPDATE material_requisition_item SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE production_daily_report ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_production_daily_report_tenant ON production_daily_report(tenant_id);
UPDATE production_daily_report SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_alert ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_alert_tenant ON material_alert(tenant_id);
UPDATE material_alert SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_batch ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_batch_tenant ON material_batch(tenant_id);
UPDATE material_batch SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_consumption ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_consumption_tenant ON material_consumption(tenant_id);
UPDATE material_consumption SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE production_exception ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_production_exception_tenant ON production_exception(tenant_id);
UPDATE production_exception SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE production_plan ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_production_plan_tenant ON production_plan(tenant_id);
UPDATE production_plan SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE production_schedule ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_production_schedule_tenant ON production_schedule(tenant_id);
UPDATE production_schedule SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE resource_conflict ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_resource_conflict_tenant ON resource_conflict(tenant_id);
UPDATE resource_conflict SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE progress_alert ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_progress_alert_tenant ON progress_alert(tenant_id);
UPDATE progress_alert SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE defect_analysis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_defect_analysis_tenant ON defect_analysis(tenant_id);
UPDATE defect_analysis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quality_inspection ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quality_inspection_tenant ON quality_inspection(tenant_id);
UPDATE quality_inspection SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE rework_order ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rework_order_tenant ON rework_order(tenant_id);
UPDATE rework_order SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE work_order ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_work_order_tenant ON work_order(tenant_id);
UPDATE work_order SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE work_report ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_work_report_tenant ON work_report(tenant_id);
UPDATE work_report SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE worker ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_worker_tenant ON worker(tenant_id);
UPDATE worker SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE worker_skill ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_worker_skill_tenant ON worker_skill(tenant_id);
UPDATE worker_skill SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE worker_efficiency_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_worker_efficiency_record_tenant ON worker_efficiency_record(tenant_id);
UPDATE worker_efficiency_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE workshop ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_workshop_tenant ON workshop(tenant_id);
UPDATE workshop SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE workstation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_workstation_tenant ON workstation(tenant_id);
UPDATE workstation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE workstation_status ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_workstation_status_tenant ON workstation_status(tenant_id);
UPDATE workstation_status SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE baseline_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_baseline_tasks_tenant ON baseline_tasks(tenant_id);
UPDATE baseline_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE progress_reports ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_progress_reports_tenant ON progress_reports(tenant_id);
UPDATE progress_reports SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE schedule_baselines ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_schedule_baselines_tenant ON schedule_baselines(tenant_id);
UPDATE schedule_baselines SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_dependencies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_tenant ON task_dependencies(tenant_id);
UPDATE task_dependencies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_change_impacts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_change_impacts_tenant ON project_change_impacts(tenant_id);
UPDATE project_change_impacts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE machines ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_machines_tenant ON machines(tenant_id);
UPDATE machines SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE cost_alerts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cost_alerts_tenant ON cost_alerts(tenant_id);
UPDATE cost_alerts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE cost_forecasts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_cost_forecasts_tenant ON cost_forecasts(tenant_id);
UPDATE cost_forecasts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_documents ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_documents_tenant ON project_documents(tenant_id);
UPDATE project_documents SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_erp ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_erp_tenant ON project_erp(tenant_id);
UPDATE project_erp SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_financials ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_financials_tenant ON project_financials(tenant_id);
UPDATE project_financials SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_implementations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_implementations_tenant ON project_implementations(tenant_id);
UPDATE project_implementations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_presales ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_presales_tenant ON project_presales(tenant_id);
UPDATE project_presales SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_warranties ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_warranties_tenant ON project_warranties(tenant_id);
UPDATE project_warranties SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE financial_project_costs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_financial_project_costs_tenant ON financial_project_costs(tenant_id);
UPDATE financial_project_costs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_costs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_costs_tenant ON project_costs(tenant_id);
UPDATE project_costs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_milestones ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_milestones_tenant ON project_milestones(tenant_id);
UPDATE project_milestones SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_payment_plans ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_payment_plans_tenant ON project_payment_plans(tenant_id);
UPDATE project_payment_plans SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_stages ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_stages_tenant ON project_stages(tenant_id);
UPDATE project_stages SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_statuses ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_statuses_tenant ON project_statuses(tenant_id);
UPDATE project_statuses SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_stage_resource_plan ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_stage_resource_plan_tenant ON project_stage_resource_plan(tenant_id);
UPDATE project_stage_resource_plan SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE resource_conflicts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_resource_conflicts_tenant ON resource_conflicts(tenant_id);
UPDATE resource_conflicts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_risk_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_risk_history_tenant ON project_risk_history(tenant_id);
UPDATE project_risk_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_risk_snapshot ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_risk_snapshot_tenant ON project_risk_snapshot(tenant_id);
UPDATE project_risk_snapshot SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE catch_up_solutions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_catch_up_solutions_tenant ON catch_up_solutions(tenant_id);
UPDATE catch_up_solutions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_schedule_prediction ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_schedule_prediction_tenant ON project_schedule_prediction(tenant_id);
UPDATE project_schedule_prediction SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE schedule_alerts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_schedule_alerts_tenant ON schedule_alerts(tenant_id);
UPDATE schedule_alerts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_member_contributions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_member_contributions_tenant ON project_member_contributions(tenant_id);
UPDATE project_member_contributions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_members ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_members_tenant ON project_members(tenant_id);
UPDATE project_members SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_dependencies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_dependencies_tenant ON project_delivery_dependencies(tenant_id);
UPDATE project_delivery_dependencies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_long_cycle_purchases ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_long_cycle_purchases_tenant ON project_delivery_long_cycle_purchases(tenant_id);
UPDATE project_delivery_long_cycle_purchases SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_mechanical_designs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_mechanical_designs_tenant ON project_delivery_mechanical_designs(tenant_id);
UPDATE project_delivery_mechanical_designs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_schedules ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_schedules_tenant ON project_delivery_schedules(tenant_id);
UPDATE project_delivery_schedules SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_tasks_tenant ON project_delivery_tasks(tenant_id);
UPDATE project_delivery_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_evaluation_dimensions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_evaluation_dimensions_tenant ON project_evaluation_dimensions(tenant_id);
UPDATE project_evaluation_dimensions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_evaluations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_evaluations_tenant ON project_evaluations(tenant_id);
UPDATE project_evaluations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_margin_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_margin_snapshots_tenant ON project_margin_snapshots(tenant_id);
UPDATE project_margin_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_best_practices ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_best_practices_tenant ON project_best_practices(tenant_id);
UPDATE project_best_practices SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_lessons ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_lessons_tenant ON project_lessons(tenant_id);
UPDATE project_lessons SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_reviews ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_reviews_tenant ON project_reviews(tenant_id);
UPDATE project_reviews SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE goods_receipt_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_goods_receipt_items_tenant ON goods_receipt_items(tenant_id);
UPDATE goods_receipt_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE goods_receipts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_goods_receipts_tenant ON goods_receipts(tenant_id);
UPDATE goods_receipts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE purchase_order_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_tenant ON purchase_order_items(tenant_id);
UPDATE purchase_order_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE purchase_orders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_tenant ON purchase_orders(tenant_id);
UPDATE purchase_orders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE purchase_request_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_purchase_request_items_tenant ON purchase_request_items(tenant_id);
UPDATE purchase_request_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE purchase_requests ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_purchase_requests_tenant ON purchase_requests(tenant_id);
UPDATE purchase_requests SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE employee_qualification ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_employee_qualification_tenant ON employee_qualification(tenant_id);
UPDATE employee_qualification SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE position_competency_model ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_position_competency_model_tenant ON position_competency_model(tenant_id);
UPDATE position_competency_model SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE qualification_assessment ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_qualification_assessment_tenant ON qualification_assessment(tenant_id);
UPDATE qualification_assessment SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE qualification_level ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_qualification_level_tenant ON qualification_level(tenant_id);
UPDATE qualification_level SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quality_risk_detection ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quality_risk_detection_tenant ON quality_risk_detection(tenant_id);
UPDATE quality_risk_detection SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quality_test_recommendations ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quality_test_recommendations_tenant ON quality_test_recommendations(tenant_id);
UPDATE quality_test_recommendations SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE rd_cost ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_cost_tenant ON rd_cost(tenant_id);
UPDATE rd_cost SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE rd_project ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_project_tenant ON rd_project(tenant_id);
UPDATE rd_project SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE rd_report_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_rd_report_record_tenant ON rd_report_record(tenant_id);
UPDATE rd_report_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_archive ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_archive_tenant ON report_archive(tenant_id);
UPDATE report_archive SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_recipient ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_recipient_tenant ON report_recipient(tenant_id);
UPDATE report_recipient SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE data_export_task ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_data_export_task_tenant ON data_export_task(tenant_id);
UPDATE data_export_task SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE data_import_task ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_data_import_task_tenant ON data_import_task(tenant_id);
UPDATE data_import_task SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_definition ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_definition_tenant ON report_definition(tenant_id);
UPDATE report_definition SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_generation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_generation_tenant ON report_generation(tenant_id);
UPDATE report_generation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE report_subscription ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_report_subscription_tenant ON report_subscription(tenant_id);
UPDATE report_subscription SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE assessment_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_assessment_items_tenant ON assessment_items(tenant_id);
UPDATE assessment_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE assessment_risks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_assessment_risks_tenant ON assessment_risks(tenant_id);
UPDATE assessment_risks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE assessment_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_assessment_versions_tenant ON assessment_versions(tenant_id);
UPDATE assessment_versions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contacts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contacts_tenant ON contacts(tenant_id);
UPDATE contacts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_amendments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_amendments_tenant ON contract_amendments(tenant_id);
UPDATE contract_amendments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_approvals_tenant ON contract_approvals(tenant_id);
UPDATE contract_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_attachments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_attachments_tenant ON contract_attachments(tenant_id);
UPDATE contract_attachments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_deliverables ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_deliverables_tenant ON contract_deliverables(tenant_id);
UPDATE contract_deliverables SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE contract_terms ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_contract_terms_tenant ON contract_terms(tenant_id);
UPDATE contract_terms SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE customer_tags ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customer_tags_tenant ON customer_tags(tenant_id);
UPDATE customer_tags SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE invoice_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_invoice_approvals_tenant ON invoice_approvals(tenant_id);
UPDATE invoice_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE receivable_disputes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_receivable_disputes_tenant ON receivable_disputes(tenant_id);
UPDATE receivable_disputes SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE lead_follow_ups ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_lead_follow_ups_tenant ON lead_follow_ups(tenant_id);
UPDATE lead_follow_ups SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE leads ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads(tenant_id);
UPDATE leads SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE opportunity_requirements ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_opportunity_requirements_tenant ON opportunity_requirements(tenant_id);
UPDATE opportunity_requirements SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE margin_alert_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_margin_alert_records_tenant ON margin_alert_records(tenant_id);
UPDATE margin_alert_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_cost_estimation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_cost_estimation_tenant ON presale_ai_cost_estimation(tenant_id);
UPDATE presale_ai_cost_estimation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_cost_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_cost_history_tenant ON presale_cost_history(tenant_id);
UPDATE presale_cost_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_cost_optimization_record ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_cost_optimization_record_tenant ON presale_cost_optimization_record(tenant_id);
UPDATE presale_cost_optimization_record SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_win_rate ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_win_rate_tenant ON presale_ai_win_rate(tenant_id);
UPDATE presale_ai_win_rate SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_win_rate_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_win_rate_history_tenant ON presale_win_rate_history(tenant_id);
UPDATE presale_win_rate_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_cost_update_reminders ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_cost_update_reminders_tenant ON material_cost_update_reminders(tenant_id);
UPDATE material_cost_update_reminders SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE purchase_material_costs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_purchase_material_costs_tenant ON purchase_material_costs(tenant_id);
UPDATE purchase_material_costs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quote_cost_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_cost_approvals_tenant ON quote_cost_approvals(tenant_id);
UPDATE quote_cost_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quote_cost_histories ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_cost_histories_tenant ON quote_cost_histories(tenant_id);
UPDATE quote_cost_histories SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quote_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_items_tenant ON quote_items(tenant_id);
UPDATE quote_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_regions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_regions_tenant ON sales_regions(tenant_id);
UPDATE sales_regions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE customer_relationship_scores ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customer_relationship_scores_tenant ON customer_relationship_scores(tenant_id);
UPDATE customer_relationship_scores SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE funnel_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_funnel_snapshots_tenant ON funnel_snapshots(tenant_id);
UPDATE funnel_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_funnel_stages ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_funnel_stages_tenant ON sales_funnel_stages(tenant_id);
UPDATE sales_funnel_stages SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE stage_dwell_time_alerts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_dwell_time_alerts_tenant ON stage_dwell_time_alerts(tenant_id);
UPDATE stage_dwell_time_alerts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE stage_gate_results ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_gate_results_tenant ON stage_gate_results(tenant_id);
UPDATE stage_gate_results SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE solution_versions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_solution_versions_tenant ON solution_versions(tenant_id);
UPDATE solution_versions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_targets_v2 ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_targets_v2_tenant ON sales_targets_v2(tenant_id);
UPDATE sales_targets_v2 SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_team_members ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_team_members_tenant ON sales_team_members(tenant_id);
UPDATE sales_team_members SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_teams ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_teams_tenant ON sales_teams(tenant_id);
UPDATE sales_teams SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE team_performance_snapshots ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_team_performance_snapshots_tenant ON team_performance_snapshots(tenant_id);
UPDATE team_performance_snapshots SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE team_pk_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_team_pk_records_tenant ON team_pk_records(tenant_id);
UPDATE team_pk_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ai_clarifications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_clarifications_tenant ON ai_clarifications(tenant_id);
UPDATE ai_clarifications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE failure_cases ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_failure_cases_tenant ON failure_cases(tenant_id);
UPDATE failure_cases SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE lead_requirement_details ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_lead_requirement_details_tenant ON lead_requirement_details(tenant_id);
UPDATE lead_requirement_details SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE open_items ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_open_items_tenant ON open_items(tenant_id);
UPDATE open_items SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE quote_approvals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_quote_approvals_tenant ON quote_approvals(tenant_id);
UPDATE quote_approvals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE requirement_freezes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_requirement_freezes_tenant ON requirement_freezes(tenant_id);
UPDATE requirement_freezes SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE technical_assessments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_technical_assessments_tenant ON technical_assessments(tenant_id);
UPDATE technical_assessments SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_history_tenant ON approval_history(tenant_id);
UPDATE approval_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_records_tenant ON approval_records(tenant_id);
UPDATE approval_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_workflow_steps ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_workflow_steps_tenant ON approval_workflow_steps(tenant_id);
UPDATE approval_workflow_steps SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_workflows ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_tenant ON approval_workflows(tenant_id);
UPDATE approval_workflows SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sales_targets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sales_targets_tenant ON sales_targets(tenant_id);
UPDATE sales_targets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE customer_communications ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customer_communications_tenant ON customer_communications(tenant_id);
UPDATE customer_communications SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE customer_satisfactions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_customer_satisfactions_tenant ON customer_satisfactions(tenant_id);
UPDATE customer_satisfactions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE knowledge_base ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_tenant ON knowledge_base(tenant_id);
UPDATE knowledge_base SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE service_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_service_records_tenant ON service_records(tenant_id);
UPDATE service_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE service_ticket_cc_users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_service_ticket_cc_users_tenant ON service_ticket_cc_users(tenant_id);
UPDATE service_ticket_cc_users SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE service_ticket_projects ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_service_ticket_projects_tenant ON service_ticket_projects(tenant_id);
UPDATE service_ticket_projects SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE service_tickets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_service_tickets_tenant ON service_tickets(tenant_id);
UPDATE service_tickets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mat_shortage_daily_report ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mat_shortage_daily_report_tenant ON mat_shortage_daily_report(tenant_id);
UPDATE mat_shortage_daily_report SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE arrival_follow_ups ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_arrival_follow_ups_tenant ON arrival_follow_ups(tenant_id);
UPDATE arrival_follow_ups SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_arrivals ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_arrivals_tenant ON material_arrivals(tenant_id);
UPDATE material_arrivals SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_substitutions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_substitutions_tenant ON material_substitutions(tenant_id);
UPDATE material_substitutions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_transfers ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_transfers_tenant ON material_transfers(tenant_id);
UPDATE material_transfers SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE shortage_reports ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_shortage_reports_tenant ON shortage_reports(tenant_id);
UPDATE shortage_reports SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mat_kit_check ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mat_kit_check_tenant ON mat_kit_check(tenant_id);
UPDATE mat_kit_check SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mat_material_requirement ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mat_material_requirement_tenant ON mat_material_requirement(tenant_id);
UPDATE mat_material_requirement SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mat_work_order_bom ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mat_work_order_bom_tenant ON mat_work_order_bom(tenant_id);
UPDATE mat_work_order_bom SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE material_demand_forecasts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_material_demand_forecasts_tenant ON material_demand_forecasts(tenant_id);
UPDATE material_demand_forecasts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE shortage_alerts_enhanced ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_shortage_alerts_enhanced_tenant ON shortage_alerts_enhanced(tenant_id);
UPDATE shortage_alerts_enhanced SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE shortage_handling_plans ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_shortage_handling_plans_tenant ON shortage_handling_plans(tenant_id);
UPDATE shortage_handling_plans SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sla_monitors ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sla_monitors_tenant ON sla_monitors(tenant_id);
UPDATE sla_monitors SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE sla_policies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_sla_policies_tenant ON sla_policies(tenant_id);
UPDATE sla_policies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE hr_employee_profile ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_employee_profile_tenant ON hr_employee_profile(tenant_id);
UPDATE hr_employee_profile SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE hr_employee_tag_evaluation ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_employee_tag_evaluation_tenant ON hr_employee_tag_evaluation(tenant_id);
UPDATE hr_employee_tag_evaluation SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE hr_project_performance ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_project_performance_tenant ON hr_project_performance(tenant_id);
UPDATE hr_project_performance SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mes_project_staffing_need ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mes_project_staffing_need_tenant ON mes_project_staffing_need(tenant_id);
UPDATE mes_project_staffing_need SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE node_tasks ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_node_tasks_tenant ON node_tasks(tenant_id);
UPDATE node_tasks SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_node_instances ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_node_instances_tenant ON project_node_instances(tenant_id);
UPDATE project_node_instances SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_stage_instances ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_stage_instances_tenant ON project_stage_instances(tenant_id);
UPDATE project_stage_instances SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE node_definitions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_node_definitions_tenant ON node_definitions(tenant_id);
UPDATE node_definitions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE stage_definitions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_stage_definitions_tenant ON stage_definitions(tenant_id);
UPDATE stage_definitions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE annual_key_work_project_links ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_annual_key_work_project_links_tenant ON annual_key_work_project_links(tenant_id);
UPDATE annual_key_work_project_links SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE annual_key_works ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_annual_key_works_tenant ON annual_key_works(tenant_id);
UPDATE annual_key_works SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE strategy_comparisons ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_strategy_comparisons_tenant ON strategy_comparisons(tenant_id);
UPDATE strategy_comparisons SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE csfs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_csfs_tenant ON csfs(tenant_id);
UPDATE csfs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE kpi_data_sources ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_kpi_data_sources_tenant ON kpi_data_sources(tenant_id);
UPDATE kpi_data_sources SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE kpi_history ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_kpi_history_tenant ON kpi_history(tenant_id);
UPDATE kpi_history SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE kpis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_kpis_tenant ON kpis(tenant_id);
UPDATE kpis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE strategies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_strategies_tenant ON strategies(tenant_id);
UPDATE strategies SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE department_objectives ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_department_objectives_tenant ON department_objectives(tenant_id);
UPDATE department_objectives SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE personal_kpis ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_personal_kpis_tenant ON personal_kpis(tenant_id);
UPDATE personal_kpis SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE strategy_calendar_events ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_strategy_calendar_events_tenant ON strategy_calendar_events(tenant_id);
UPDATE strategy_calendar_events SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE strategy_reviews ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_strategy_reviews_tenant ON strategy_reviews(tenant_id);
UPDATE strategy_reviews SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_approval_workflows ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_approval_workflows_tenant ON task_approval_workflows(tenant_id);
UPDATE task_approval_workflows SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_comment ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_comment_tenant ON task_comment(tenant_id);
UPDATE task_comment SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_completion_proofs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_completion_proofs_tenant ON task_completion_proofs(tenant_id);
UPDATE task_completion_proofs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_reminder ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_reminder_tenant ON task_reminder(tenant_id);
UPDATE task_reminder SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_unified ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_unified_tenant ON task_unified(tenant_id);
UPDATE task_unified SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE review_checklist_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_review_checklist_records_tenant ON review_checklist_records(tenant_id);
UPDATE review_checklist_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE review_issues ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_review_issues_tenant ON review_issues(tenant_id);
UPDATE review_issues SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE review_materials ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_review_materials_tenant ON review_materials(tenant_id);
UPDATE review_materials SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE review_participants ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_review_participants_tenant ON review_participants(tenant_id);
UPDATE review_participants SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE technical_reviews ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_technical_reviews_tenant ON technical_reviews(tenant_id);
UPDATE technical_reviews SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE spec_match_records ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_spec_match_records_tenant ON spec_match_records(tenant_id);
UPDATE spec_match_records SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE technical_spec_requirements ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_technical_spec_requirements_tenant ON technical_spec_requirements(tenant_id);
UPDATE technical_spec_requirements SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE overtime_application ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_overtime_application_tenant ON overtime_application(tenant_id);
UPDATE overtime_application SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE timesheet ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_timesheet_tenant ON timesheet(tenant_id);
UPDATE timesheet SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE timesheet_batch ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_timesheet_batch_tenant ON timesheet_batch(tenant_id);
UPDATE timesheet_batch SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE timesheet_summary ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_timesheet_summary_tenant ON timesheet_summary(tenant_id);
UPDATE timesheet_summary SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE user_2fa_secrets ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_user_2fa_secrets_tenant ON user_2fa_secrets(tenant_id);
UPDATE user_2fa_secrets SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE solution_credit_transactions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_solution_credit_transactions_tenant ON solution_credit_transactions(tenant_id);
UPDATE solution_credit_transactions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE user_roles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_user_roles_tenant ON user_roles(tenant_id);
UPDATE user_roles SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE vendors ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_vendors_tenant ON vendors(tenant_id);
UPDATE vendors SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

