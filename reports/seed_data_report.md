# Seed Data Report

- Generated at: 2026-03-01T23:06:03
- Database: `sqlite:///data/app.db`
- Total tables: **507**
- Non-empty tables: **507** (100.00%)
- Core tables: **102**
- Core tables non-empty: **102** (100.00%)

## Module Progress

| Module | Tables | Success | Inserted Rows |
| --- | ---: | ---: | ---: |
| base | 25 | 25 | 0 |
| hr | 30 | 30 | 0 |
| sales | 18 | 18 | 0 |
| project | 78 | 78 | 0 |
| purchase | 34 | 34 | 0 |
| production | 20 | 20 | 0 |
| service | 3 | 3 | 0 |
| finance | 20 | 20 | 0 |
| strategy | 7 | 7 | 0 |
| other | 272 | 272 | 0 |

## Integrity Checks

- Foreign-key issues found: **0**

## Business Rule Checks

- [PASS] `lead_to_opportunity` - opportunities without leads: 0
- [PASS] `opportunity_to_contract` - contracts without opportunities: 0
- [PASS] `contract_to_project` - projects without contracts: 0
- [PASS] `timestamp_sequence` - tables_checked=505, invalid_rows=0
- [PASS] `period_sequence` - tables_checked=26, invalid_rows=0
- [PASS] `amount_consistency` - tables_checked=5, invalid_rows=0

## Table Row Counts

| Module | Table | Rows |
| --- | --- | ---: |
| other | acceptance_issues | 3 |
| other | acceptance_order_items | 8 |
| other | acceptance_orders | 3 |
| other | acceptance_reports | 3 |
| other | acceptance_signatures | 3 |
| other | acceptance_templates | 3 |
| other | acceptance_tracking | 3 |
| other | acceptance_tracking_records | 3 |
| other | accountability_records | 3 |
| other | advantage_product_categories | 8 |
| other | advantage_products | 133 |
| other | ai_clarifications | 3 |
| project | ai_project_plan_templates | 3 |
| other | ai_resource_allocations | 3 |
| project | ai_wbs_suggestions | 3 |
| other | alert_notifications | 3 |
| other | alert_records | 3 |
| other | alert_rule_templates | 3 |
| other | alert_rules | 3 |
| other | alert_statistics | 3 |
| other | alert_subscriptions | 3 |
| project | annual_key_work_project_links | 3 |
| other | annual_key_works | 3 |
| other | api_keys | 3 |
| base | api_permissions | 31 |
| other | approval_action_logs | 20 |
| other | approval_carbon_copies | 3 |
| other | approval_comments | 3 |
| other | approval_countersign_results | 3 |
| other | approval_delegate_logs | 20 |
| other | approval_delegates | 3 |
| other | approval_flow_definitions | 3 |
| other | approval_history | 20 |
| other | approval_instances | 3 |
| other | approval_node_definitions | 3 |
| other | approval_records | 3 |
| other | approval_routing_rules | 3 |
| project | approval_tasks | 8 |
| other | approval_template_versions | 3 |
| other | approval_templates | 3 |
| other | approval_workflow_steps | 8 |
| other | approval_workflows | 3 |
| other | arrival_follow_ups | 3 |
| project | baseline_tasks | 8 |
| other | bidding_documents | 3 |
| project | bidding_projects | 3 |
| other | bom_headers | 3 |
| production | bom_item_assembly_attrs | 8 |
| other | bom_items | 8 |
| other | bom_versions | 3 |
| hr | bonus_allocation_sheets | 3 |
| hr | bonus_calculations | 3 |
| hr | bonus_distributions | 3 |
| hr | bonus_rules | 3 |
| other | catch_up_solutions | 3 |
| project | change_approval_records | 3 |
| project | change_impact_analysis | 3 |
| project | change_notifications | 3 |
| project | change_requests | 3 |
| project | change_response_suggestions | 3 |
| other | code_module | 3 |
| other | code_review_record | 3 |
| other | collaboration_rating | 3 |
| other | component_selection | 3 |
| sales | contacts | 3 |
| other | contract_amendments | 3 |
| other | contract_approvals | 3 |
| other | contract_attachments | 3 |
| other | contract_deliverables | 3 |
| other | contract_reminders | 3 |
| other | contract_reviews | 3 |
| other | contract_seal_records | 3 |
| other | contract_template_versions | 3 |
| other | contract_templates | 3 |
| other | contract_terms | 3 |
| sales | contracts | 60 |
| finance | cost_alert_rules | 3 |
| finance | cost_alerts | 3 |
| finance | cost_forecasts | 3 |
| finance | cost_optimization_suggestions | 3 |
| finance | cost_prediction | 3 |
| other | cpq_rule_sets | 3 |
| other | csfs | 3 |
| base | culture_wall_config | 6 |
| other | culture_wall_content | 3 |
| other | culture_wall_read_record | 3 |
| other | currency_history | 20 |
| other | currency_rates | 7 |
| sales | customer_communications | 30 |
| sales | customer_satisfactions | 30 |
| sales | customer_supplier_registrations | 30 |
| sales | customer_tags | 30 |
| sales | customers | 30 |
| project | data_export_task | 8 |
| project | data_import_task | 8 |
| other | data_scope_rules | 3 |
| other | defect_analysis | 3 |
| other | delivery_orders | 3 |
| base | department_default_roles | 6 |
| strategy | department_objectives | 6 |
| other | department_role_admins | 6 |
| hr | departments | 30 |
| other | design_reuse_record | 3 |
| other | design_review | 3 |
| other | document_archives | 3 |
| other | earned_value_data | 3 |
| other | earned_value_snapshots | 3 |
| other | ecn | 3 |
| purchase | ecn_affected_materials | 6 |
| other | ecn_affected_orders | 3 |
| other | ecn_approval_matrix | 3 |
| other | ecn_approvals | 3 |
| other | ecn_bom_changes | 3 |
| other | ecn_bom_impacts | 3 |
| other | ecn_evaluations | 3 |
| other | ecn_logs | 20 |
| other | ecn_records | 3 |
| other | ecn_responsibilities | 3 |
| other | ecn_solution_templates | 3 |
| project | ecn_tasks | 8 |
| other | ecn_types | 3 |
| other | electrical_drawing_version | 3 |
| other | electrical_fault_record | 3 |
| hr | employee_contracts | 30 |
| hr | employee_hr_profiles | 30 |
| hr | employee_org_assignments | 30 |
| hr | employee_qualification | 30 |
| hr | employees | 30 |
| base | engineer_dimension_config | 6 |
| other | engineer_profile | 3 |
| other | equipment | 3 |
| production | equipment_maintenance | 3 |
| production | equipment_oee_record | 3 |
| other | equity_structures | 3 |
| base | evaluation_weight_config | 6 |
| other | exception_actions | 3 |
| other | exception_escalations | 3 |
| other | exception_events | 20 |
| other | exception_handling_flow | 3 |
| other | exception_knowledge | 3 |
| other | exception_pdca | 3 |
| other | failure_cases | 3 |
| other | field_checkins | 3 |
| other | field_issues | 3 |
| project | field_tasks | 8 |
| project | financial_project_costs | 3 |
| other | funding_records | 3 |
| other | funding_rounds | 3 |
| other | funding_usages | 3 |
| purchase | goods_receipt_items | 8 |
| purchase | goods_receipts | 25 |
| other | holidays | 33 |
| base | hourly_rate_configs | 6 |
| hr | hr_ai_matching_log | 500 |
| hr | hr_employee_profile | 30 |
| hr | hr_employee_tag_evaluation | 30 |
| hr | hr_project_performance | 60 |
| hr | hr_tag_dict | 25 |
| hr | hr_transactions | 25 |
| other | import_template | 3 |
| other | industries | 37 |
| other | industry_category_mappings | 44 |
| service | installation_dispatch_orders | 3 |
| other | investors | 3 |
| finance | invoice_approvals | 60 |
| finance | invoice_requests | 60 |
| finance | invoices | 60 |
| project | issue_follow_up_records | 3 |
| project | issue_follow_ups | 3 |
| project | issue_statistics_snapshots | 3 |
| project | issue_templates | 3 |
| other | issues | 25 |
| other | job_duty_template | 3 |
| other | job_levels | 3 |
| other | knowledge_base | 3 |
| other | knowledge_contribution | 3 |
| other | knowledge_reuse_log | 20 |
| other | kpi_data_sources | 3 |
| other | kpi_history | 20 |
| strategy | kpis | 25 |
| other | lead_follow_ups | 3 |
| other | lead_requirement_details | 8 |
| sales | leads | 60 |
| other | lessons_learned | 3 |
| other | login_attempts | 53 |
| other | machines | 3 |
| base | management_rhythm_config | 6 |
| other | mat_alert_log | 20 |
| other | mat_kit_check | 3 |
| purchase | mat_material_requirement | 6 |
| other | mat_shortage_alert | 3 |
| other | mat_shortage_daily_report | 3 |
| production | mat_work_order_bom | 3 |
| purchase | material_alert | 6 |
| purchase | material_alert_rule | 6 |
| purchase | material_arrivals | 6 |
| purchase | material_batch | 6 |
| purchase | material_categories | 30 |
| purchase | material_consumption | 6 |
| purchase | material_cost_update_reminders | 6 |
| purchase | material_demand_forecasts | 6 |
| purchase | material_requisition | 6 |
| purchase | material_requisition_item | 8 |
| purchase | material_reservation | 6 |
| purchase | material_shortages | 6 |
| purchase | material_stock | 6 |
| purchase | material_substitutions | 6 |
| purchase | material_suppliers | 6 |
| purchase | material_transaction | 6 |
| purchase | material_transfers | 6 |
| purchase | materials | 30 |
| other | mechanical_debug_issue | 3 |
| project | meeting_action_item | 8 |
| project | meeting_report | 3 |
| base | meeting_report_config | 6 |
| base | menu_permissions | 3 |
| production | mes_assembly_stage | 8 |
| production | mes_assembly_template | 3 |
| other | mes_category_stage_mapping | 8 |
| other | mes_kit_rate_snapshot | 3 |
| purchase | mes_material_readiness | 6 |
| project | mes_project_staffing_need | 3 |
| other | mes_scheduling_suggestion | 3 |
| other | mes_shortage_alert_rule | 3 |
| other | mes_shortage_detail | 8 |
| other | monthly_work_summary | 3 |
| other | new_product_requests | 3 |
| other | node_definitions | 148 |
| project | node_tasks | 8 |
| other | notification_settings | 3 |
| other | notifications | 25 |
| other | open_items | 8 |
| sales | opportunities | 25 |
| other | opportunity_requirements | 3 |
| other | organization_units | 3 |
| other | outsourcing_deliveries | 3 |
| other | outsourcing_delivery_items | 8 |
| other | outsourcing_evaluations | 3 |
| other | outsourcing_inspections | 3 |
| other | outsourcing_order_items | 8 |
| other | outsourcing_orders | 3 |
| finance | outsourcing_payments | 3 |
| other | outsourcing_progress | 3 |
| other | outsourcing_vendors | 3 |
| other | overtime_application | 3 |
| finance | payment_reminders | 3 |
| finance | payments | 60 |
| hr | performance_adjustment_history | 20 |
| hr | performance_appeal | 3 |
| hr | performance_contract_items | 8 |
| hr | performance_contracts | 3 |
| hr | performance_evaluation | 3 |
| hr | performance_evaluation_record | 3 |
| hr | performance_indicator | 3 |
| hr | performance_period | 3 |
| hr | performance_ranking_snapshot | 3 |
| hr | performance_result | 3 |
| other | permission_audits | 20 |
| other | permission_groups | 3 |
| base | permissions | 323 |
| other | personal_goal | 3 |
| strategy | personal_kpis | 3 |
| other | pipeline_break_records | 3 |
| other | pipeline_health_snapshots | 3 |
| other | pitfall_learning_progress | 3 |
| other | pitfall_recommendations | 3 |
| other | pitfalls | 3 |
| other | plc_module_library | 3 |
| other | plc_program_version | 3 |
| project | pmo_change_request | 3 |
| other | pmo_meeting | 3 |
| project | pmo_project_closure | 3 |
| project | pmo_project_cost | 3 |
| project | pmo_project_initiation | 3 |
| project | pmo_project_phase | 3 |
| project | pmo_project_risk | 3 |
| other | pmo_resource_allocation | 3 |
| other | position_competency_model | 6 |
| other | position_role_mapping | 38 |
| base | position_roles | 6 |
| hr | positions | 30 |
| other | presale_ai_audit_log | 20 |
| base | presale_ai_config | 6 |
| finance | presale_ai_cost_estimation | 3 |
| other | presale_ai_emotion_analysis | 3 |
| other | presale_ai_feedback | 3 |
| other | presale_ai_generation_log | 20 |
| other | presale_ai_qa | 3 |
| other | presale_ai_quotation | 3 |
| other | presale_ai_requirement_analysis | 3 |
| other | presale_ai_solution | 3 |
| other | presale_ai_usage_stats | 3 |
| other | presale_ai_win_rate | 3 |
| other | presale_ai_workflow_log | 20 |
| finance | presale_cost_history | 20 |
| finance | presale_cost_optimization_record | 3 |
| sales | presale_customer_tech_profile | 6 |
| other | presale_emotion_trend | 3 |
| other | presale_expenses | 3 |
| other | presale_follow_up_reminder | 3 |
| other | presale_knowledge_case | 3 |
| other | presale_mobile_assistant_chat | 3 |
| other | presale_mobile_offline_data | 3 |
| other | presale_mobile_quick_estimate | 3 |
| other | presale_solution | 3 |
| other | presale_solution_cost | 3 |
| other | presale_solution_template | 3 |
| other | presale_solution_templates | 3 |
| other | presale_support_ticket | 3 |
| other | presale_tender_record | 3 |
| other | presale_ticket_deliverable | 3 |
| other | presale_ticket_progress | 3 |
| other | presale_visit_record | 3 |
| other | presale_win_rate_history | 20 |
| other | presale_workload | 3 |
| other | process_dict | 3 |
| production | production_daily_report | 25 |
| production | production_exception | 25 |
| production | production_plan | 60 |
| production | production_progress_log | 500 |
| production | production_schedule | 25 |
| other | progress_alert | 3 |
| other | progress_logs | 20 |
| other | progress_reports | 3 |
| project | project_best_practices | 60 |
| project | project_budget_items | 120 |
| project | project_budgets | 60 |
| project | project_contribution | 60 |
| project | project_cost_allocation_rules | 60 |
| project | project_costs | 60 |
| project | project_documents | 60 |
| project | project_erp | 60 |
| project | project_evaluation_dimensions | 60 |
| project | project_evaluations | 60 |
| project | project_financials | 60 |
| project | project_health_snapshots | 60 |
| project | project_implementations | 60 |
| project | project_lessons | 60 |
| project | project_member_contributions | 60 |
| project | project_members | 60 |
| project | project_milestones | 60 |
| project | project_node_instances | 60 |
| project | project_payment_plans | 60 |
| project | project_presales | 60 |
| project | project_reviews | 60 |
| project | project_risk_history | 500 |
| project | project_risk_snapshot | 60 |
| base | project_role_configs | 30 |
| project | project_role_types | 30 |
| project | project_schedule_prediction | 60 |
| project | project_stage_instances | 120 |
| project | project_stage_resource_plan | 120 |
| project | project_stages | 120 |
| project | project_status_logs | 500 |
| project | project_statuses | 60 |
| project | project_template_versions | 60 |
| project | project_templates | 60 |
| project | project_warranties | 60 |
| project | projects | 60 |
| purchase | purchase_material_costs | 30 |
| purchase | purchase_order_items | 120 |
| purchase | purchase_order_trackings | 60 |
| purchase | purchase_orders | 60 |
| purchase | purchase_request_items | 120 |
| purchase | purchase_requests | 25 |
| purchase | purchase_suggestions | 25 |
| other | qualification_assessment | 3 |
| other | qualification_level | 3 |
| production | quality_alert_rule | 3 |
| production | quality_inspection | 3 |
| project | quality_risk_detection | 3 |
| production | quality_test_recommendations | 3 |
| other | quotation_approvals | 3 |
| other | quotation_templates | 3 |
| other | quotation_versions | 3 |
| other | quote_approvals | 3 |
| finance | quote_cost_approvals | 3 |
| finance | quote_cost_histories | 3 |
| finance | quote_cost_templates | 3 |
| other | quote_items | 8 |
| other | quote_template_versions | 3 |
| other | quote_templates | 3 |
| other | quote_versions | 3 |
| sales | quotes | 60 |
| other | rd_cost | 3 |
| finance | rd_cost_allocation_rule | 3 |
| finance | rd_cost_type | 3 |
| other | rd_project | 3 |
| project | rd_project_category | 3 |
| other | rd_report_record | 3 |
| other | receivable_disputes | 3 |
| other | reconciliations | 3 |
| other | report_archive | 3 |
| other | report_definition | 3 |
| other | report_generation | 3 |
| other | report_metric_definition | 3 |
| other | report_recipient | 3 |
| other | report_subscription | 3 |
| other | report_template | 3 |
| other | requirement_freezes | 3 |
| other | resource_conflict | 3 |
| other | resource_conflicts | 3 |
| other | review_checklist_records | 3 |
| other | review_issues | 3 |
| purchase | review_materials | 6 |
| other | review_participants | 3 |
| production | rework_order | 3 |
| other | rhythm_dashboard_snapshot | 3 |
| base | role_api_permissions | 47 |
| other | role_assignment_approvals | 6 |
| other | role_audits | 20 |
| other | role_data_scopes | 6 |
| other | role_exclusions | 6 |
| base | role_menus | 6 |
| base | role_permissions | 6 |
| base | role_template_permissions | 6 |
| other | role_templates | 6 |
| base | roles | 30 |
| hr | salary_records | 3 |
| sales | sales_order_items | 120 |
| sales | sales_orders | 60 |
| base | sales_ranking_configs | 30 |
| sales | sales_regions | 25 |
| sales | sales_targets | 25 |
| sales | sales_targets_v2 | 25 |
| sales | sales_team_members | 25 |
| sales | sales_teams | 25 |
| other | satisfaction_survey_templates | 3 |
| other | schedule_adjustment_log | 20 |
| other | schedule_alerts | 3 |
| other | schedule_baselines | 3 |
| base | scheduler_task_configs | 8 |
| other | scoring_rules | 3 |
| service | service_records | 60 |
| base | service_ticket_cc_users | 30 |
| project | service_ticket_projects | 60 |
| service | service_tickets | 60 |
| other | shortage_alerts | 3 |
| other | shortage_alerts_enhanced | 3 |
| other | shortage_handling_plans | 3 |
| other | shortage_reports | 3 |
| other | sla_monitors | 3 |
| other | sla_policies | 3 |
| base | solution_credit_configs | 6 |
| other | solution_credit_transactions | 3 |
| other | solution_templates | 3 |
| other | spec_match_records | 3 |
| other | stage_definitions | 39 |
| other | stage_templates | 4 |
| finance | standard_cost_history | 20 |
| other | standard_costs | 3 |
| other | state_transition_logs | 20 |
| other | stock_adjustment | 3 |
| other | stock_count_detail | 8 |
| project | stock_count_task | 8 |
| other | strategic_meeting | 3 |
| strategy | strategies | 25 |
| strategy | strategy_calendar_events | 500 |
| strategy | strategy_comparisons | 25 |
| strategy | strategy_reviews | 25 |
| purchase | supplier_performances | 30 |
| purchase | supplier_quotations | 30 |
| purchase | suppliers | 30 |
| other | target_breakdown_logs | 20 |
| project | task_approval_workflows | 3 |
| project | task_comment | 3 |
| project | task_completion_proofs | 3 |
| project | task_dependencies | 3 |
| project | task_operation_log | 20 |
| project | task_reminder | 3 |
| project | task_unified | 3 |
| project | tasks | 3 |
| hr | team_bonus_allocations | 3 |
| hr | team_performance_snapshots | 3 |
| other | team_pk_records | 3 |
| other | technical_assessments | 3 |
| other | technical_reviews | 3 |
| other | technical_spec_requirements | 3 |
| other | template_categories | 3 |
| other | template_check_items | 8 |
| other | tenants | 3 |
| other | test_bug_record | 3 |
| other | timesheet | 3 |
| other | timesheet_approval_log | 20 |
| other | timesheet_batch | 3 |
| other | timesheet_rule | 3 |
| other | timesheet_summary | 3 |
| other | user_2fa_backup_codes | 6 |
| other | user_2fa_secrets | 6 |
| other | user_role_assignments | 6 |
| base | user_roles | 6 |
| other | user_sessions | 35 |
| base | users | 30 |
| other | vendors | 3 |
| project | wbs_template_tasks | 8 |
| project | wbs_templates | 25 |
| base | work_log_configs | 20 |
| other | work_log_mentions | 20 |
| other | work_logs | 20 |
| production | work_order | 3 |
| other | work_report | 3 |
| production | worker | 3 |
| production | worker_efficiency_record | 3 |
| production | worker_skill | 3 |
| production | workshop | 3 |
| other | workstation | 3 |
| other | workstation_status | 3 |

## Per-table Seed Results

| Table | Module | Before | Target | Inserted | After | Status | Message |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| acceptance_issues | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_order_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| acceptance_orders | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_reports | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_signatures | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_tracking | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| acceptance_tracking_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| accountability_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| advantage_product_categories | other | 8 | 3 | 0 | 8 | OK | already has enough rows |
| advantage_products | other | 133 | 3 | 0 | 133 | OK | already has enough rows |
| ai_clarifications | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ai_project_plan_templates | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ai_resource_allocations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ai_wbs_suggestions | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_notifications | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_rule_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_rules | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_statistics | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| alert_subscriptions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| annual_key_work_project_links | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| annual_key_works | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| api_keys | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| api_permissions | base | 31 | 3 | 0 | 31 | OK | already has enough rows |
| approval_action_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| approval_carbon_copies | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_comments | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_countersign_results | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_delegate_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| approval_delegates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_flow_definitions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_history | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| approval_instances | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_node_definitions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_routing_rules | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| approval_template_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| approval_workflow_steps | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| approval_workflows | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| arrival_follow_ups | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| baseline_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| bidding_documents | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bidding_projects | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bom_headers | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bom_item_assembly_attrs | production | 8 | 8 | 0 | 8 | OK | already has enough rows |
| bom_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| bom_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bonus_allocation_sheets | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bonus_calculations | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bonus_distributions | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| bonus_rules | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| catch_up_solutions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| change_approval_records | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| change_impact_analysis | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| change_notifications | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| change_requests | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| change_response_suggestions | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| code_module | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| code_review_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| collaboration_rating | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| component_selection | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contacts | sales | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_amendments | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_approvals | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_attachments | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_deliverables | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_reminders | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_reviews | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_seal_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_template_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contract_terms | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| contracts | sales | 60 | 60 | 0 | 60 | OK | already has enough rows |
| cost_alert_rules | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| cost_alerts | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| cost_forecasts | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| cost_optimization_suggestions | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| cost_prediction | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| cpq_rule_sets | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| csfs | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| culture_wall_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| culture_wall_content | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| culture_wall_read_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| currency_history | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| currency_rates | other | 7 | 3 | 0 | 7 | OK | already has enough rows |
| customer_communications | sales | 30 | 30 | 0 | 30 | OK | already has enough rows |
| customer_satisfactions | sales | 30 | 30 | 0 | 30 | OK | already has enough rows |
| customer_supplier_registrations | sales | 30 | 30 | 0 | 30 | OK | already has enough rows |
| customer_tags | sales | 30 | 30 | 0 | 30 | OK | already has enough rows |
| customers | sales | 30 | 30 | 0 | 30 | OK | already has enough rows |
| data_export_task | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| data_import_task | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| data_scope_rules | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| defect_analysis | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| delivery_orders | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| department_default_roles | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| department_objectives | strategy | 6 | 6 | 0 | 6 | OK | already has enough rows |
| department_role_admins | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| departments | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| design_reuse_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| design_review | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| document_archives | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| earned_value_data | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| earned_value_snapshots | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_affected_materials | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| ecn_affected_orders | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_approval_matrix | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_approvals | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_bom_changes | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_bom_impacts | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_evaluations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| ecn_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_responsibilities | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_solution_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| ecn_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| ecn_types | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| electrical_drawing_version | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| electrical_fault_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| employee_contracts | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| employee_hr_profiles | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| employee_org_assignments | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| employee_qualification | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| employees | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| engineer_dimension_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| engineer_profile | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| equipment | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| equipment_maintenance | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| equipment_oee_record | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| equity_structures | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| evaluation_weight_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| exception_actions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| exception_escalations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| exception_events | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| exception_handling_flow | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| exception_knowledge | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| exception_pdca | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| failure_cases | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| field_checkins | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| field_issues | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| field_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| financial_project_costs | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| funding_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| funding_rounds | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| funding_usages | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| goods_receipt_items | purchase | 8 | 8 | 0 | 8 | OK | already has enough rows |
| goods_receipts | purchase | 25 | 25 | 0 | 25 | OK | already has enough rows |
| holidays | other | 33 | 3 | 0 | 33 | OK | already has enough rows |
| hourly_rate_configs | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| hr_ai_matching_log | hr | 500 | 500 | 0 | 500 | OK | already has enough rows |
| hr_employee_profile | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| hr_employee_tag_evaluation | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| hr_project_performance | hr | 60 | 60 | 0 | 60 | OK | already has enough rows |
| hr_tag_dict | hr | 25 | 25 | 0 | 25 | OK | already has enough rows |
| hr_transactions | hr | 25 | 25 | 0 | 25 | OK | already has enough rows |
| import_template | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| industries | other | 37 | 3 | 0 | 37 | OK | already has enough rows |
| industry_category_mappings | other | 44 | 3 | 0 | 44 | OK | already has enough rows |
| installation_dispatch_orders | service | 3 | 3 | 0 | 3 | OK | already has enough rows |
| investors | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| invoice_approvals | finance | 60 | 60 | 0 | 60 | OK | already has enough rows |
| invoice_requests | finance | 60 | 60 | 0 | 60 | OK | already has enough rows |
| invoices | finance | 60 | 60 | 0 | 60 | OK | already has enough rows |
| issue_follow_up_records | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| issue_follow_ups | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| issue_statistics_snapshots | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| issue_templates | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| issues | other | 25 | 25 | 0 | 25 | OK | already has enough rows |
| job_duty_template | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| job_levels | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| knowledge_base | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| knowledge_contribution | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| knowledge_reuse_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| kpi_data_sources | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| kpi_history | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| kpis | strategy | 25 | 25 | 0 | 25 | OK | already has enough rows |
| lead_follow_ups | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| lead_requirement_details | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| leads | sales | 60 | 60 | 0 | 60 | OK | already has enough rows |
| lessons_learned | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| login_attempts | other | 53 | 20 | 0 | 53 | OK | already has enough rows |
| machines | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| management_rhythm_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| mat_alert_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| mat_kit_check | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mat_material_requirement | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| mat_shortage_alert | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mat_shortage_daily_report | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mat_work_order_bom | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| material_alert | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_alert_rule | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_arrivals | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_batch | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_categories | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| material_consumption | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_cost_update_reminders | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_demand_forecasts | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_requisition | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_requisition_item | purchase | 8 | 8 | 0 | 8 | OK | already has enough rows |
| material_reservation | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_shortages | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_stock | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_substitutions | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_suppliers | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_transaction | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| material_transfers | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| materials | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| mechanical_debug_issue | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| meeting_action_item | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| meeting_report | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| meeting_report_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| menu_permissions | base | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_assembly_stage | production | 8 | 8 | 0 | 8 | OK | already has enough rows |
| mes_assembly_template | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_category_stage_mapping | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| mes_kit_rate_snapshot | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_material_readiness | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| mes_project_staffing_need | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_scheduling_suggestion | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_shortage_alert_rule | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| mes_shortage_detail | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| monthly_work_summary | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| new_product_requests | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| node_definitions | other | 148 | 3 | 0 | 148 | OK | already has enough rows |
| node_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| notification_settings | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| notifications | other | 25 | 25 | 0 | 25 | OK | already has enough rows |
| open_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| opportunities | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| opportunity_requirements | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| organization_units | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_deliveries | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_delivery_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| outsourcing_evaluations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_inspections | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_order_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| outsourcing_orders | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_payments | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_progress | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| outsourcing_vendors | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| overtime_application | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| payment_reminders | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| payments | finance | 60 | 60 | 0 | 60 | OK | already has enough rows |
| performance_adjustment_history | hr | 20 | 20 | 0 | 20 | OK | already has enough rows |
| performance_appeal | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_contract_items | hr | 8 | 8 | 0 | 8 | OK | already has enough rows |
| performance_contracts | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_evaluation | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_evaluation_record | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_indicator | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_period | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_ranking_snapshot | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| performance_result | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| permission_audits | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| permission_groups | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| permissions | base | 323 | 25 | 0 | 323 | OK | already has enough rows |
| personal_goal | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| personal_kpis | strategy | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pipeline_break_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pipeline_health_snapshots | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pitfall_learning_progress | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pitfall_recommendations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pitfalls | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| plc_module_library | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| plc_program_version | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_change_request | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_meeting | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_project_closure | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_project_cost | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_project_initiation | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_project_phase | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_project_risk | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| pmo_resource_allocation | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| position_competency_model | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| position_role_mapping | other | 38 | 6 | 0 | 38 | OK | already has enough rows |
| position_roles | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| positions | hr | 30 | 30 | 0 | 30 | OK | already has enough rows |
| presale_ai_audit_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| presale_ai_config | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| presale_ai_cost_estimation | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_emotion_analysis | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_feedback | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_generation_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| presale_ai_qa | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_quotation | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_requirement_analysis | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_solution | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_usage_stats | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_win_rate | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ai_workflow_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| presale_cost_history | finance | 20 | 20 | 0 | 20 | OK | already has enough rows |
| presale_cost_optimization_record | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_customer_tech_profile | sales | 6 | 6 | 0 | 6 | OK | already has enough rows |
| presale_emotion_trend | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_expenses | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_follow_up_reminder | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_knowledge_case | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_mobile_assistant_chat | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_mobile_offline_data | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_mobile_quick_estimate | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_solution | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_solution_cost | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_solution_template | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_solution_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_support_ticket | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_tender_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ticket_deliverable | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_ticket_progress | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_visit_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| presale_win_rate_history | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| presale_workload | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| process_dict | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| production_daily_report | production | 25 | 25 | 0 | 25 | OK | already has enough rows |
| production_exception | production | 25 | 25 | 0 | 25 | OK | already has enough rows |
| production_plan | production | 60 | 60 | 0 | 60 | OK | already has enough rows |
| production_progress_log | production | 500 | 500 | 0 | 500 | OK | already has enough rows |
| production_schedule | production | 25 | 25 | 0 | 25 | OK | already has enough rows |
| progress_alert | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| progress_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| progress_reports | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| project_best_practices | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_budget_items | project | 120 | 120 | 0 | 120 | OK | already has enough rows |
| project_budgets | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_contribution | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_cost_allocation_rules | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_costs | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_documents | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_erp | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_evaluation_dimensions | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_evaluations | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_financials | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_health_snapshots | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_implementations | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_lessons | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_member_contributions | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_members | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_milestones | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_node_instances | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_payment_plans | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_presales | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_reviews | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_risk_history | project | 500 | 500 | 0 | 500 | OK | already has enough rows |
| project_risk_snapshot | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_role_configs | base | 30 | 30 | 0 | 30 | OK | already has enough rows |
| project_role_types | project | 30 | 30 | 0 | 30 | OK | already has enough rows |
| project_schedule_prediction | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_stage_instances | project | 120 | 120 | 0 | 120 | OK | already has enough rows |
| project_stage_resource_plan | project | 120 | 120 | 0 | 120 | OK | already has enough rows |
| project_stages | project | 120 | 120 | 0 | 120 | OK | already has enough rows |
| project_status_logs | project | 500 | 500 | 0 | 500 | OK | already has enough rows |
| project_statuses | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_template_versions | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_templates | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| project_warranties | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| projects | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| purchase_material_costs | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| purchase_order_items | purchase | 120 | 120 | 0 | 120 | OK | already has enough rows |
| purchase_order_trackings | purchase | 60 | 60 | 0 | 60 | OK | already has enough rows |
| purchase_orders | purchase | 60 | 60 | 0 | 60 | OK | already has enough rows |
| purchase_request_items | purchase | 120 | 120 | 0 | 120 | OK | already has enough rows |
| purchase_requests | purchase | 25 | 25 | 0 | 25 | OK | already has enough rows |
| purchase_suggestions | purchase | 25 | 25 | 0 | 25 | OK | already has enough rows |
| qualification_assessment | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| qualification_level | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quality_alert_rule | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quality_inspection | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quality_risk_detection | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quality_test_recommendations | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quotation_approvals | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quotation_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quotation_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_approvals | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_cost_approvals | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_cost_histories | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_cost_templates | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| quote_template_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quote_versions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| quotes | sales | 60 | 60 | 0 | 60 | OK | already has enough rows |
| rd_cost | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rd_cost_allocation_rule | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rd_cost_type | finance | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rd_project | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rd_project_category | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rd_report_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| receivable_disputes | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| reconciliations | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_archive | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_definition | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_generation | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_metric_definition | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_recipient | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_subscription | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| report_template | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| requirement_freezes | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| resource_conflict | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| resource_conflicts | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| review_checklist_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| review_issues | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| review_materials | purchase | 6 | 6 | 0 | 6 | OK | already has enough rows |
| review_participants | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rework_order | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| rhythm_dashboard_snapshot | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| role_api_permissions | base | 47 | 6 | 0 | 47 | OK | already has enough rows |
| role_assignment_approvals | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_audits | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| role_data_scopes | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_exclusions | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_menus | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_permissions | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_template_permissions | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| role_templates | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| roles | base | 30 | 30 | 0 | 30 | OK | already has enough rows |
| salary_records | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| sales_order_items | sales | 120 | 120 | 0 | 120 | OK | already has enough rows |
| sales_orders | sales | 60 | 60 | 0 | 60 | OK | already has enough rows |
| sales_ranking_configs | base | 30 | 30 | 0 | 30 | OK | already has enough rows |
| sales_regions | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| sales_targets | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| sales_targets_v2 | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| sales_team_members | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| sales_teams | sales | 25 | 25 | 0 | 25 | OK | already has enough rows |
| satisfaction_survey_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| schedule_adjustment_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| schedule_alerts | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| schedule_baselines | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| scheduler_task_configs | base | 8 | 8 | 0 | 8 | OK | already has enough rows |
| scoring_rules | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| service_records | service | 60 | 60 | 0 | 60 | OK | already has enough rows |
| service_ticket_cc_users | base | 30 | 30 | 0 | 30 | OK | already has enough rows |
| service_ticket_projects | project | 60 | 60 | 0 | 60 | OK | already has enough rows |
| service_tickets | service | 60 | 60 | 0 | 60 | OK | already has enough rows |
| shortage_alerts | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| shortage_alerts_enhanced | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| shortage_handling_plans | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| shortage_reports | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| sla_monitors | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| sla_policies | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| solution_credit_configs | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| solution_credit_transactions | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| solution_templates | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| spec_match_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| stage_definitions | other | 39 | 3 | 0 | 39 | OK | already has enough rows |
| stage_templates | other | 4 | 3 | 0 | 4 | OK | already has enough rows |
| standard_cost_history | finance | 20 | 20 | 0 | 20 | OK | already has enough rows |
| standard_costs | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| state_transition_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| stock_adjustment | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| stock_count_detail | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| stock_count_task | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| strategic_meeting | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| strategies | strategy | 25 | 25 | 0 | 25 | OK | already has enough rows |
| strategy_calendar_events | strategy | 500 | 500 | 0 | 500 | OK | already has enough rows |
| strategy_comparisons | strategy | 25 | 25 | 0 | 25 | OK | already has enough rows |
| strategy_reviews | strategy | 25 | 25 | 0 | 25 | OK | already has enough rows |
| supplier_performances | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| supplier_quotations | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| suppliers | purchase | 30 | 30 | 0 | 30 | OK | already has enough rows |
| target_breakdown_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| task_approval_workflows | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| task_comment | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| task_completion_proofs | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| task_dependencies | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| task_operation_log | project | 20 | 20 | 0 | 20 | OK | already has enough rows |
| task_reminder | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| task_unified | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| tasks | project | 3 | 3 | 0 | 3 | OK | already has enough rows |
| team_bonus_allocations | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| team_performance_snapshots | hr | 3 | 3 | 0 | 3 | OK | already has enough rows |
| team_pk_records | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| technical_assessments | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| technical_reviews | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| technical_spec_requirements | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| template_categories | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| template_check_items | other | 8 | 8 | 0 | 8 | OK | already has enough rows |
| tenants | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| test_bug_record | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| timesheet | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| timesheet_approval_log | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| timesheet_batch | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| timesheet_rule | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| timesheet_summary | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| user_2fa_backup_codes | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| user_2fa_secrets | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| user_role_assignments | other | 6 | 6 | 0 | 6 | OK | already has enough rows |
| user_roles | base | 6 | 6 | 0 | 6 | OK | already has enough rows |
| user_sessions | other | 35 | 6 | 0 | 35 | OK | already has enough rows |
| users | base | 30 | 30 | 0 | 30 | OK | already has enough rows |
| vendors | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| wbs_template_tasks | project | 8 | 8 | 0 | 8 | OK | already has enough rows |
| wbs_templates | project | 25 | 25 | 0 | 25 | OK | already has enough rows |
| work_log_configs | base | 20 | 20 | 0 | 20 | OK | already has enough rows |
| work_log_mentions | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| work_logs | other | 20 | 20 | 0 | 20 | OK | already has enough rows |
| work_order | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| work_report | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| worker | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| worker_efficiency_record | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| worker_skill | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| workshop | production | 3 | 3 | 0 | 3 | OK | already has enough rows |
| workstation | other | 3 | 3 | 0 | 3 | OK | already has enough rows |
| workstation_status | other | 3 | 3 | 0 | 3 | OK | already has enough rows |