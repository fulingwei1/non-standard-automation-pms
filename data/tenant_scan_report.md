# 数据模型租户隔离扫描报告

扫描时间: Mon Feb 16 04:36:18 CST 2026

================================================================================

## 统计摘要

- 总表数: 479
- 已包含 tenant_id: 6
- 缺少 tenant_id: 473

## ✅ 已包含 tenant_id 的表 (6)

- api_keys
- api_permissions
- data_scope_rules
- menu_permissions
- roles
- users

## ⚠️  缺少 tenant_id 的核心业务表 (473)

### AI规划 (3)

- `ai_project_plan_templates` (AIProjectPlanTemplate) - app/models/ai_planning/plan_template.py
- `ai_resource_allocations` (AIResourceAllocation) - app/models/ai_planning/resource_allocation.py
- `ai_wbs_suggestions` (AIWbsSuggestion) - app/models/ai_planning/wbs_suggestion.py

### PMO管理 (8)

- `pmo_change_request` (PmoChangeRequest) - app/models/pmo/change_risk.py
- `pmo_meeting` (PmoMeeting) - app/models/pmo/cost_meeting.py
- `pmo_project_closure` (PmoProjectClosure) - app/models/pmo/resource_closure.py
- `pmo_project_cost` (PmoProjectCost) - app/models/pmo/cost_meeting.py
- `pmo_project_initiation` (PmoProjectInitiation) - app/models/pmo/initiation_phase.py
- `pmo_project_phase` (PmoProjectPhase) - app/models/pmo/initiation_phase.py
- `pmo_project_risk` (PmoProjectRisk) - app/models/pmo/change_risk.py
- `pmo_resource_allocation` (PmoResourceAllocation) - app/models/pmo/resource_closure.py

### 售后服务 (8)

- `customer_communications` (CustomerCommunication) - app/models/service/communication_satisfaction.py
- `customer_satisfactions` (CustomerSatisfaction) - app/models/service/communication_satisfaction.py
- `knowledge_base` (KnowledgeBase) - app/models/service/knowledge.py
- `satisfaction_survey_templates` (SatisfactionSurveyTemplate) - app/models/service/communication_satisfaction.py
- `service_records` (ServiceRecord) - app/models/service/record.py
- `service_ticket_cc_users` (ServiceTicketCcUser) - app/models/service/ticket.py
- `service_ticket_projects` (ServiceTicketProject) - app/models/service/ticket.py
- `service_tickets` (ServiceTicket) - app/models/service/ticket.py

### 商务支撑 (14)

- `acceptance_tracking` (AcceptanceTracking) - app/models/business_support/acceptance.py
- `acceptance_tracking_records` (AcceptanceTrackingRecord) - app/models/business_support/acceptance.py
- `bidding_documents` (BiddingDocument) - app/models/business_support/bidding.py
- `bidding_projects` (BiddingProject) - app/models/business_support/bidding.py
- `contract_reviews` (ContractReview) - app/models/business_support/contract.py
- `contract_seal_records` (ContractSealRecord) - app/models/business_support/contract.py
- `customer_supplier_registrations` (CustomerSupplierRegistration) - app/models/business_support/registration.py
- `delivery_orders` (DeliveryOrder) - app/models/business_support/delivery.py
- `document_archives` (DocumentArchive) - app/models/business_support/document.py
- `invoice_requests` (InvoiceRequest) - app/models/business_support/invoice.py
- `payment_reminders` (PaymentReminder) - app/models/business_support/payment.py
- `reconciliations` (Reconciliation) - app/models/business_support/reconciliation.py
- `sales_order_items` (SalesOrderItem) - app/models/business_support/sales_order.py
- `sales_orders` (SalesOrder) - app/models/business_support/sales_order.py

### 审批流程 (13)

- `approval_action_logs` (ApprovalActionLog) - app/models/approval/log.py
- `approval_carbon_copies` (ApprovalCarbonCopy) - app/models/approval/task.py
- `approval_comments` (ApprovalComment) - app/models/approval/log.py
- `approval_countersign_results` (ApprovalCountersignResult) - app/models/approval/task.py
- `approval_delegate_logs` (ApprovalDelegateLog) - app/models/approval/delegate.py
- `approval_delegates` (ApprovalDelegate) - app/models/approval/delegate.py
- `approval_flow_definitions` (ApprovalFlowDefinition) - app/models/approval/flow.py
- `approval_instances` (ApprovalInstance) - app/models/approval/instance.py
- `approval_node_definitions` (ApprovalNodeDefinition) - app/models/approval/flow.py
- `approval_routing_rules` (ApprovalRoutingRule) - app/models/approval/flow.py
- `approval_tasks` (ApprovalTask) - app/models/approval/task.py
- `approval_template_versions` (ApprovalTemplateVersion) - app/models/approval/template.py
- `approval_templates` (ApprovalTemplate) - app/models/approval/template.py

### 工程变更 (12)

- `ecn` (Ecn) - app/models/ecn/core.py
- `ecn_affected_materials` (EcnAffectedMaterial) - app/models/ecn/impact.py
- `ecn_affected_orders` (EcnAffectedOrder) - app/models/ecn/impact.py
- `ecn_approval_matrix` (EcnApprovalMatrix) - app/models/ecn/config.py
- `ecn_approvals` (EcnApproval) - app/models/ecn/evaluation_approval.py
- `ecn_bom_impacts` (EcnBomImpact) - app/models/ecn/impact.py
- `ecn_evaluations` (EcnEvaluation) - app/models/ecn/evaluation_approval.py
- `ecn_logs` (EcnLog) - app/models/ecn/log.py
- `ecn_responsibilities` (EcnResponsibility) - app/models/ecn/responsibility_template.py
- `ecn_solution_templates` (EcnSolutionTemplate) - app/models/ecn/responsibility_template.py
- `ecn_tasks` (EcnTask) - app/models/ecn/execution.py
- `ecn_types` (EcnType) - app/models/ecn/config.py

### 战略管理 (12)

- `annual_key_work_project_links` (AnnualKeyWorkProjectLink) - app/models/strategy/annual_work.py
- `annual_key_works` (AnnualKeyWork) - app/models/strategy/annual_work.py
- `csfs` (CSF) - app/models/strategy/core.py
- `department_objectives` (DepartmentObjective) - app/models/strategy/decomposition.py
- `kpi_data_sources` (KPIDataSource) - app/models/strategy/core.py
- `kpi_history` (KPIHistory) - app/models/strategy/core.py
- `kpis` (KPI) - app/models/strategy/core.py
- `personal_kpis` (PersonalKPI) - app/models/strategy/decomposition.py
- `strategies` (Strategy) - app/models/strategy/core.py
- `strategy_calendar_events` (StrategyCalendarEvent) - app/models/strategy/review.py
- `strategy_comparisons` (StrategyComparison) - app/models/strategy/comparison.py
- `strategy_reviews` (StrategyReview) - app/models/strategy/review.py

### 核心模块 (251)

- `acceptance_issues` (AcceptanceIssue) - app/models/acceptance.py
- `acceptance_order_items` (AcceptanceOrderItem) - app/models/acceptance.py
- `acceptance_orders` (AcceptanceOrder) - app/models/acceptance.py
- `acceptance_reports` (AcceptanceReport) - app/models/acceptance.py
- `acceptance_signatures` (AcceptanceSignature) - app/models/acceptance.py
- `acceptance_templates` (AcceptanceTemplate) - app/models/acceptance.py
- `accountability_records` (AccountabilityRecord) - app/models/pipeline_analysis.py
- `advantage_product_categories` (AdvantageProductCategory) - app/models/advantage_product.py
- `advantage_products` (AdvantageProduct) - app/models/advantage_product.py
- `alert_notifications` (AlertNotification) - app/models/alert.py
- `alert_records` (AlertRecord) - app/models/alert.py
- `alert_rule_templates` (AlertRuleTemplate) - app/models/alert.py
- `alert_rules` (AlertRule) - app/models/alert.py
- `alert_statistics` (AlertStatistics) - app/models/alert.py
- `alert_subscriptions` (AlertSubscription) - app/models/alert.py
- `baseline_tasks` (BaselineTask) - app/models/progress.py
- `bom_headers` (BomHeader) - app/models/material.py
- `bom_item_assembly_attrs` (BomItemAssemblyAttrs) - app/models/assembly_kit.py
- `bom_items` (BomItem) - app/models/material.py
- `bonus_allocation_sheets` (BonusAllocationSheet) - app/models/bonus.py
- `bonus_calculations` (BonusCalculation) - app/models/bonus.py
- `bonus_distributions` (BonusDistribution) - app/models/bonus.py
- `bonus_rules` (BonusRule) - app/models/bonus.py
- `change_approval_records` (ChangeApprovalRecord) - app/models/change_request.py
- `change_impact_analysis` (ChangeImpactAnalysis) - app/models/change_impact.py
- `change_notifications` (ChangeNotification) - app/models/change_request.py
- `change_requests` (ChangeRequest) - app/models/change_request.py
- `change_response_suggestions` (ChangeResponseSuggestion) - app/models/change_impact.py
- `contract_reminders` (ContractReminder) - app/models/organization.py
- `cost_optimization_suggestions` (CostOptimizationSuggestion) - app/models/cost_prediction.py
- `cost_prediction` (CostPrediction) - app/models/cost_prediction.py
- `culture_wall_config` (CultureWallConfig) - app/models/culture_wall_config.py
- `culture_wall_content` (CultureWallContent) - app/models/culture_wall.py
- `culture_wall_read_record` (CultureWallReadRecord) - app/models/culture_wall.py
- `data_export_task` (DataExportTask) - app/models/report_center.py
- `data_import_task` (DataImportTask) - app/models/report_center.py
- `departments` (Department) - app/models/organization.py
- `earned_value_data` (EarnedValueData) - app/models/earned_value.py
- `earned_value_snapshots` (EarnedValueSnapshot) - app/models/earned_value.py
- `employee_contracts` (EmployeeContract) - app/models/organization.py
- `employee_hr_profiles` (EmployeeHrProfile) - app/models/organization.py
- `employee_org_assignments` (EmployeeOrgAssignment) - app/models/organization.py
- `employee_qualification` (EmployeeQualification) - app/models/qualification.py
- `employees` (Employee) - app/models/organization.py
- `employees` (Employee) - app/models/employee_encrypted_example.py
- `equity_structures` (EquityStructure) - app/models/finance.py
- `exception_actions` (ExceptionAction) - app/models/alert.py
- `exception_escalations` (ExceptionEscalation) - app/models/alert.py
- `exception_events` (ExceptionEvent) - app/models/alert.py
- `funding_records` (FundingRecord) - app/models/finance.py
- `funding_rounds` (FundingRound) - app/models/finance.py
- `funding_usages` (FundingUsage) - app/models/finance.py
- `goods_receipt_items` (GoodsReceiptItem) - app/models/purchase.py
- `goods_receipts` (GoodsReceipt) - app/models/purchase.py
- `holidays` (Holiday) - app/models/holiday.py
- `hourly_rate_configs` (HourlyRateConfig) - app/models/hourly_rate.py
- `hr_ai_matching_log` (HrAIMatchingLog) - app/models/staff_matching.py
- `hr_employee_profile` (HrEmployeeProfile) - app/models/staff_matching.py
- `hr_employee_tag_evaluation` (HrEmployeeTagEvaluation) - app/models/staff_matching.py
- `hr_project_performance` (HrProjectPerformance) - app/models/staff_matching.py
- `hr_tag_dict` (HrTagDict) - app/models/staff_matching.py
- `hr_transactions` (HrTransaction) - app/models/organization.py
- `import_template` (ImportTemplate) - app/models/report_center.py
- `industries` (Industry) - app/models/advantage_product.py
- `industry_category_mappings` (IndustryCategoryMapping) - app/models/advantage_product.py
- `installation_dispatch_orders` (InstallationDispatchOrder) - app/models/installation_dispatch.py
- `investors` (Investor) - app/models/finance.py
- `issue_follow_up_records` (IssueFollowUpRecord) - app/models/issue.py
- `issue_follow_ups` (IssueFollowUp) - app/models/acceptance.py
- `issue_statistics_snapshots` (IssueStatisticsSnapshot) - app/models/issue.py
- `issue_templates` (IssueTemplate) - app/models/issue.py
- `issues` (Issue) - app/models/issue.py
- `job_duty_template` (JobDutyTemplate) - app/models/task_center.py
- `job_levels` (JobLevel) - app/models/organization.py
- `management_rhythm_config` (ManagementRhythmConfig) - app/models/management_rhythm.py
- `material_categories` (MaterialCategory) - app/models/material.py
- `material_shortages` (MaterialShortage) - app/models/material.py
- `material_suppliers` (MaterialSupplier) - app/models/material.py
- `materials` (Material) - app/models/material.py
- `meeting_action_item` (MeetingActionItem) - app/models/management_rhythm.py
- `meeting_report` (MeetingReport) - app/models/management_rhythm.py
- `meeting_report_config` (MeetingReportConfig) - app/models/management_rhythm.py
- `mes_assembly_stage` (AssemblyStage) - app/models/assembly_kit.py
- `mes_assembly_template` (AssemblyTemplate) - app/models/assembly_kit.py
- `mes_category_stage_mapping` (CategoryStageMapping) - app/models/assembly_kit.py
- `mes_kit_rate_snapshot` (KitRateSnapshot) - app/models/assembly_kit.py
- `mes_material_readiness` (MaterialReadiness) - app/models/assembly_kit.py
- `mes_project_staffing_need` (MesProjectStaffingNeed) - app/models/staff_matching.py
- `mes_scheduling_suggestion` (SchedulingSuggestion) - app/models/assembly_kit.py
- `mes_shortage_alert_rule` (ShortageAlertRule) - app/models/assembly_kit.py
- `mes_shortage_detail` (ShortageDetail) - app/models/assembly_kit.py
- `new_product_requests` (NewProductRequest) - app/models/advantage_product.py
- `node_definitions` (NodeDefinition) - app/models/stage_template.py
- `node_tasks` (NodeTask) - app/models/stage_instance.py
- `notification_settings` (NotificationSettings) - app/models/notification.py
- `notifications` (Notification) - app/models/notification.py
- `organization_units` (OrganizationUnit) - app/models/organization.py
- `outsourcing_deliveries` (OutsourcingDelivery) - app/models/outsourcing.py
- `outsourcing_delivery_items` (OutsourcingDeliveryItem) - app/models/outsourcing.py
- `outsourcing_evaluations` (OutsourcingEvaluation) - app/models/outsourcing.py
- `outsourcing_inspections` (OutsourcingInspection) - app/models/outsourcing.py
- `outsourcing_order_items` (OutsourcingOrderItem) - app/models/outsourcing.py
- `outsourcing_orders` (OutsourcingOrder) - app/models/outsourcing.py
- `outsourcing_payments` (OutsourcingPayment) - app/models/outsourcing.py
- `outsourcing_progress` (OutsourcingProgress) - app/models/outsourcing.py
- `overtime_application` (OvertimeApplication) - app/models/timesheet.py
- `permission_audits` (PermissionAudit) - app/models/user.py
- `permission_groups` (PermissionGroup) - app/models/permission.py
- `personal_goal` (PersonalGoal) - app/models/culture_wall.py
- `pipeline_break_records` (PipelineBreakRecord) - app/models/pipeline_analysis.py
- `pipeline_health_snapshots` (PipelineHealthSnapshot) - app/models/pipeline_analysis.py
- `pitfall_learning_progress` (PitfallLearningProgress) - app/models/pitfall.py
- `pitfall_recommendations` (PitfallRecommendation) - app/models/pitfall.py
- `pitfalls` (Pitfall) - app/models/pitfall.py
- `position_competency_model` (PositionCompetencyModel) - app/models/qualification.py
- `position_roles` (PositionRole) - app/models/organization.py
- `positions` (Position) - app/models/organization.py
- `presale_ai_audit_log` (PresaleAIAuditLog) - app/models/presale_ai.py
- `presale_ai_config` (PresaleAIConfig) - app/models/presale_ai.py
- `presale_ai_emotion_analysis` (PresaleAIEmotionAnalysis) - app/models/presale_ai_emotion_analysis.py
- `presale_ai_feedback` (PresaleAIFeedback) - app/models/presale_ai.py
- `presale_ai_generation_log` (PresaleAIGenerationLog) - app/models/presale_ai_solution.py
- `presale_ai_qa` (PresaleAIQA) - app/models/presale_ai_qa.py
- `presale_ai_quotation` (PresaleAIQuotation) - app/models/presale_ai_quotation.py
- `presale_ai_requirement_analysis` (PresaleAIRequirementAnalysis) - app/models/presale_ai_requirement_analysis.py
- `presale_ai_solution` (PresaleAISolution) - app/models/presale_ai_solution.py
- `presale_ai_usage_stats` (PresaleAIUsageStats) - app/models/presale_ai.py
- `presale_ai_workflow_log` (PresaleAIWorkflowLog) - app/models/presale_ai.py
- `presale_customer_tech_profile` (PresaleCustomerTechProfile) - app/models/presale.py
- `presale_emotion_trend` (PresaleEmotionTrend) - app/models/presale_emotion_trend.py
- `presale_expenses` (PresaleExpense) - app/models/presale_expense.py
- `presale_follow_up_reminder` (PresaleFollowUpReminder) - app/models/presale_follow_up_reminder.py
- `presale_knowledge_case` (PresaleKnowledgeCase) - app/models/presale_knowledge_case.py
- `presale_mobile_assistant_chat` (PresaleMobileAssistantChat) - app/models/presale_mobile.py
- `presale_mobile_offline_data` (PresaleMobileOfflineData) - app/models/presale_mobile.py
- `presale_mobile_quick_estimate` (PresaleMobileQuickEstimate) - app/models/presale_mobile.py
- `presale_solution` (PresaleSolution) - app/models/presale.py
- `presale_solution_cost` (PresaleSolutionCost) - app/models/presale.py
- `presale_solution_template` (PresaleSolutionTemplate) - app/models/presale.py
- `presale_solution_templates` (PresaleSolutionTemplate) - app/models/presale_ai_solution.py
- `presale_support_ticket` (PresaleSupportTicket) - app/models/presale.py
- `presale_tender_record` (PresaleTenderRecord) - app/models/presale.py
- `presale_ticket_deliverable` (PresaleTicketDeliverable) - app/models/presale.py
- `presale_ticket_progress` (PresaleTicketProgress) - app/models/presale.py
- `presale_visit_record` (PresaleVisitRecord) - app/models/presale_mobile.py
- `presale_workload` (PresaleWorkload) - app/models/presale.py
- `progress_logs` (ProgressLog) - app/models/progress.py
- `progress_reports` (ProgressReport) - app/models/progress.py
- `project_best_practices` (ProjectBestPractice) - app/models/project_review.py
- `project_budget_items` (ProjectBudgetItem) - app/models/budget.py
- `project_budgets` (ProjectBudget) - app/models/budget.py
- `project_cost_allocation_rules` (ProjectCostAllocationRule) - app/models/budget.py
- `project_evaluation_dimensions` (ProjectEvaluationDimension) - app/models/project_evaluation.py
- `project_evaluations` (ProjectEvaluation) - app/models/project_evaluation.py
- `project_health_snapshots` (ProjectHealthSnapshot) - app/models/alert.py
- `project_lessons` (ProjectLesson) - app/models/project_review.py
- `project_node_instances` (ProjectNodeInstance) - app/models/stage_instance.py
- `project_reviews` (ProjectReview) - app/models/project_review.py
- `project_risks` (ProjectRisk) - app/models/project_risk.py
- `project_role_configs` (ProjectRoleConfig) - app/models/project_role.py
- `project_role_types` (ProjectRoleType) - app/models/project_role.py
- `project_stage_instances` (ProjectStageInstance) - app/models/stage_instance.py
- `purchase_order_items` (PurchaseOrderItem) - app/models/purchase.py
- `purchase_orders` (PurchaseOrder) - app/models/purchase.py
- `purchase_request_items` (PurchaseRequestItem) - app/models/purchase.py
- `purchase_requests` (PurchaseRequest) - app/models/purchase.py
- `qualification_assessment` (QualificationAssessment) - app/models/qualification.py
- `qualification_level` (QualificationLevel) - app/models/qualification.py
- `quality_risk_detection` (QualityRiskDetection) - app/models/quality_risk_detection.py
- `quality_test_recommendations` (QualityTestRecommendation) - app/models/quality_risk_detection.py
- `quotation_approvals` (QuotationApproval) - app/models/presale_ai_quotation.py
- `quotation_templates` (QuotationTemplate) - app/models/presale_ai_quotation.py
- `quotation_versions` (QuotationVersion) - app/models/presale_ai_quotation.py
- `rd_cost` (RdCost) - app/models/rd_project.py
- `rd_cost_allocation_rule` (RdCostAllocationRule) - app/models/rd_project.py
- `rd_cost_type` (RdCostType) - app/models/rd_project.py
- `rd_project` (RdProject) - app/models/rd_project.py
- `rd_project_category` (RdProjectCategory) - app/models/rd_project.py
- `rd_report_record` (RdReportRecord) - app/models/rd_project.py
- `report_archive` (ReportArchive) - app/models/report.py
- `report_definition` (ReportDefinition) - app/models/report_center.py
- `report_generation` (ReportGeneration) - app/models/report_center.py
- `report_metric_definition` (ReportMetricDefinition) - app/models/management_rhythm.py
- `report_recipient` (ReportRecipient) - app/models/report.py
- `report_subscription` (ReportSubscription) - app/models/report_center.py
- `report_template` (ReportTemplate) - app/models/report_center.py
- `report_template` (ReportTemplate) - app/models/report.py
- `resource_conflict_detection` (ResourceConflictDetection) - app/models/resource_scheduling.py
- `resource_demand_forecast` (ResourceDemandForecast) - app/models/resource_scheduling.py
- `resource_scheduling_logs` (ResourceSchedulingLog) - app/models/resource_scheduling.py
- `resource_scheduling_suggestions` (ResourceSchedulingSuggestion) - app/models/resource_scheduling.py
- `resource_utilization_analysis` (ResourceUtilizationAnalysis) - app/models/resource_scheduling.py
- `review_checklist_records` (ReviewChecklistRecord) - app/models/technical_review.py
- `review_issues` (ReviewIssue) - app/models/technical_review.py
- `review_materials` (ReviewMaterial) - app/models/technical_review.py
- `review_participants` (ReviewParticipant) - app/models/technical_review.py
- `rhythm_dashboard_snapshot` (RhythmDashboardSnapshot) - app/models/management_rhythm.py
- `role_api_permissions` (RoleApiPermission) - app/models/user.py
- `role_data_scopes` (RoleDataScope) - app/models/permission.py
- `role_menus` (RoleMenu) - app/models/permission.py
- `role_templates` (RoleTemplate) - app/models/user.py
- `salary_records` (SalaryRecord) - app/models/organization.py
- `schedule_baselines` (ScheduleBaseline) - app/models/progress.py
- `scheduler_task_configs` (SchedulerTaskConfig) - app/models/scheduler_config.py
- `sla_monitors` (SLAMonitor) - app/models/sla.py
- `sla_policies` (SLAPolicy) - app/models/sla.py
- `solution_credit_configs` (SolutionCreditConfig) - app/models/user.py
- `solution_credit_transactions` (SolutionCreditTransaction) - app/models/user.py
- `solution_templates` (SolutionTemplate) - app/models/issue.py
- `spec_match_records` (SpecMatchRecord) - app/models/technical_spec.py
- `stage_definitions` (StageDefinition) - app/models/stage_template.py
- `stage_templates` (StageTemplate) - app/models/stage_template.py
- `standard_cost_history` (StandardCostHistory) - app/models/standard_cost.py
- `standard_costs` (StandardCost) - app/models/standard_cost.py
- `state_transition_logs` (StateTransitionLog) - app/models/state_machine.py
- `strategic_meeting` (StrategicMeeting) - app/models/management_rhythm.py
- `task_approval_workflows` (TaskApprovalWorkflow) - app/models/task_center.py
- `task_comment` (TaskComment) - app/models/task_center.py
- `task_completion_proofs` (TaskCompletionProof) - app/models/task_center.py
- `task_dependencies` (TaskDependency) - app/models/progress.py
- `task_operation_log` (TaskOperationLog) - app/models/task_center.py
- `task_reminder` (TaskReminder) - app/models/task_center.py
- `task_unified` (TaskUnified) - app/models/task_center.py
- `tasks` (Task) - app/models/progress.py
- `team_bonus_allocations` (TeamBonusAllocation) - app/models/bonus.py
- `technical_reviews` (TechnicalReview) - app/models/technical_review.py
- `technical_spec_requirements` (TechnicalSpecRequirement) - app/models/technical_spec.py
- `template_categories` (TemplateCategory) - app/models/acceptance.py
- `template_check_items` (TemplateCheckItem) - app/models/acceptance.py
- `timesheet` (Timesheet) - app/models/timesheet.py
- `timesheet_analytics` (TimesheetAnalytics) - app/models/timesheet_analytics.py
- `timesheet_anomaly` (TimesheetAnomaly) - app/models/timesheet_analytics.py
- `timesheet_anomaly_record` (TimesheetAnomalyRecord) - app/models/timesheet_reminder.py
- `timesheet_approval_log` (TimesheetApprovalLog) - app/models/timesheet.py
- `timesheet_batch` (TimesheetBatch) - app/models/timesheet.py
- `timesheet_forecast` (TimesheetForecast) - app/models/timesheet_analytics.py
- `timesheet_reminder_config` (TimesheetReminderConfig) - app/models/timesheet_reminder.py
- `timesheet_reminder_record` (TimesheetReminderRecord) - app/models/timesheet_reminder.py
- `timesheet_rule` (TimesheetRule) - app/models/timesheet.py
- `timesheet_summary` (TimesheetSummary) - app/models/timesheet.py
- `timesheet_trend` (TimesheetTrend) - app/models/timesheet_analytics.py
- `user_2fa_backup_codes` (User2FABackupCode) - app/models/two_factor.py
- `user_2fa_secrets` (User2FASecret) - app/models/two_factor.py
- `user_roles` (UserRole) - app/models/user.py
- `user_sessions` (UserSession) - app/models/session.py
- `vendors` (Vendor) - app/models/vendor.py
- `wbs_template_tasks` (WbsTemplateTask) - app/models/progress.py
- `wbs_templates` (WbsTemplate) - app/models/progress.py
- `work_log_configs` (WorkLogConfig) - app/models/work_log.py
- `work_log_mentions` (WorkLogMention) - app/models/work_log.py
- `work_logs` (WorkLog) - app/models/work_log.py

### 生产管理 (33)

- `defect_analysis` (DefectAnalysis) - app/models/production/quality_inspection.py
- `equipment` (Equipment) - app/models/production/equipment.py
- `equipment_maintenance` (EquipmentMaintenance) - app/models/production/equipment.py
- `equipment_oee_record` (EquipmentOEERecord) - app/models/production/equipment_oee_record.py
- `exception_handling_flow` (ExceptionHandlingFlow) - app/models/production/exception_handling_flow.py
- `exception_knowledge` (ExceptionKnowledge) - app/models/production/exception_knowledge.py
- `exception_pdca` (ExceptionPDCA) - app/models/production/exception_pdca.py
- `material_alert` (MaterialAlert) - app/models/production/material_tracking.py
- `material_alert_rule` (MaterialAlertRule) - app/models/production/material_tracking.py
- `material_batch` (MaterialBatch) - app/models/production/material_tracking.py
- `material_consumption` (MaterialConsumption) - app/models/production/material_tracking.py
- `material_requisition` (MaterialRequisition) - app/models/production/material.py
- `material_requisition_item` (MaterialRequisitionItem) - app/models/production/material.py
- `process_dict` (ProcessDict) - app/models/production/process.py
- `production_daily_report` (ProductionDailyReport) - app/models/production/material.py
- `production_exception` (ProductionException) - app/models/production/production_exception.py
- `production_plan` (ProductionPlan) - app/models/production/production_plan.py
- `production_progress_log` (ProductionProgressLog) - app/models/production/production_progress_log.py
- `production_schedule` (ProductionSchedule) - app/models/production/production_schedule.py
- `progress_alert` (ProgressAlert) - app/models/production/progress_alert.py
- `quality_alert_rule` (QualityAlertRule) - app/models/production/quality_inspection.py
- `quality_inspection` (QualityInspection) - app/models/production/quality_inspection.py
- `resource_conflict` (ResourceConflict) - app/models/production/production_schedule.py
- `rework_order` (ReworkOrder) - app/models/production/quality_inspection.py
- `schedule_adjustment_log` (ScheduleAdjustmentLog) - app/models/production/production_schedule.py
- `work_order` (WorkOrder) - app/models/production/work_order.py
- `work_report` (WorkReport) - app/models/production/work_report.py
- `worker` (Worker) - app/models/production/worker.py
- `worker_efficiency_record` (WorkerEfficiencyRecord) - app/models/production/worker_efficiency_record.py
- `worker_skill` (WorkerSkill) - app/models/production/worker.py
- `workshop` (Workshop) - app/models/production/workshop.py
- `workstation` (Workstation) - app/models/production/workshop.py
- `workstation_status` (WorkstationStatus) - app/models/production/workstation_status.py

### 绩效管理 (27)

- `code_module` (CodeModule) - app/models/engineer_performance/test.py
- `code_review_record` (CodeReviewRecord) - app/models/engineer_performance/test.py
- `collaboration_rating` (CollaborationRating) - app/models/engineer_performance/common.py
- `component_selection` (ComponentSelection) - app/models/engineer_performance/electrical.py
- `design_reuse_record` (DesignReuseRecord) - app/models/engineer_performance/mechanical.py
- `design_review` (DesignReview) - app/models/engineer_performance/mechanical.py
- `electrical_drawing_version` (ElectricalDrawingVersion) - app/models/engineer_performance/electrical.py
- `electrical_fault_record` (ElectricalFaultRecord) - app/models/engineer_performance/electrical.py
- `engineer_dimension_config` (EngineerDimensionConfig) - app/models/engineer_performance/common.py
- `engineer_profile` (EngineerProfile) - app/models/engineer_performance/common.py
- `evaluation_weight_config` (EvaluationWeightConfig) - app/models/performance/monthly_system.py
- `knowledge_contribution` (KnowledgeContribution) - app/models/engineer_performance/common.py
- `knowledge_reuse_log` (KnowledgeReuseLog) - app/models/engineer_performance/common.py
- `mechanical_debug_issue` (MechanicalDebugIssue) - app/models/engineer_performance/mechanical.py
- `monthly_work_summary` (MonthlyWorkSummary) - app/models/performance/monthly_system.py
- `performance_adjustment_history` (PerformanceAdjustmentHistory) - app/models/performance/appeal_adjustment.py
- `performance_appeal` (PerformanceAppeal) - app/models/performance/appeal_adjustment.py
- `performance_evaluation` (PerformanceEvaluation) - app/models/performance/result_evaluation.py
- `performance_evaluation_record` (PerformanceEvaluationRecord) - app/models/performance/monthly_system.py
- `performance_indicator` (PerformanceIndicator) - app/models/performance/period_indicator.py
- `performance_period` (PerformancePeriod) - app/models/performance/period_indicator.py
- `performance_ranking_snapshot` (PerformanceRankingSnapshot) - app/models/performance/contribution_ranking.py
- `performance_result` (PerformanceResult) - app/models/performance/result_evaluation.py
- `plc_module_library` (PlcModuleLibrary) - app/models/engineer_performance/electrical.py
- `plc_program_version` (PlcProgramVersion) - app/models/engineer_performance/electrical.py
- `project_contribution` (ProjectContribution) - app/models/performance/contribution_ranking.py
- `test_bug_record` (TestBugRecord) - app/models/engineer_performance/test.py

### 缺料管理 (10)

- `arrival_follow_ups` (ArrivalFollowUp) - app/models/shortage/arrivals.py
- `mat_alert_log` (AlertHandleLog) - app/models/shortage/alerts.py
- `mat_kit_check` (KitCheck) - app/models/shortage/requirements.py
- `mat_material_requirement` (MaterialRequirement) - app/models/shortage/requirements.py
- `mat_shortage_daily_report` (ShortageDailyReport) - app/models/shortage/alerts.py
- `mat_work_order_bom` (WorkOrderBom) - app/models/shortage/requirements.py
- `material_arrivals` (MaterialArrival) - app/models/shortage/arrivals.py
- `material_substitutions` (MaterialSubstitution) - app/models/shortage/handling.py
- `material_transfers` (MaterialTransfer) - app/models/shortage/handling.py
- `shortage_reports` (ShortageReport) - app/models/shortage/reports.py

### 销售管理 (54)

- `ai_clarifications` (AIClarification) - app/models/sales/technical_assessment.py
- `approval_history` (ApprovalHistory) - app/models/sales/workflow.py
- `approval_records` (ApprovalRecord) - app/models/sales/workflow.py
- `approval_workflow_steps` (ApprovalWorkflowStep) - app/models/sales/workflow.py
- `approval_workflows` (ApprovalWorkflow) - app/models/sales/workflow.py
- `contacts` (Contact) - app/models/sales/contacts.py
- `contract_amendments` (ContractAmendment) - app/models/sales/contracts.py
- `contract_approvals` (ContractApproval) - app/models/sales/contracts.py
- `contract_attachments` (ContractAttachment) - app/models/sales/contracts.py
- `contract_deliverables` (ContractDeliverable) - app/models/sales/contracts.py
- `contract_template_versions` (ContractTemplateVersion) - app/models/sales/contracts.py
- `contract_templates` (ContractTemplate) - app/models/sales/contracts.py
- `contract_terms` (ContractTerm) - app/models/sales/contracts.py
- `contracts` (Contract) - app/models/sales/contracts.py
- `cpq_rule_sets` (CpqRuleSet) - app/models/sales/quotes.py
- `customer_tags` (CustomerTag) - app/models/sales/customer_tags.py
- `failure_cases` (FailureCase) - app/models/sales/technical_assessment.py
- `invoice_approvals` (InvoiceApproval) - app/models/sales/invoices.py
- `invoices` (Invoice) - app/models/sales/invoices.py
- `lead_follow_ups` (LeadFollowUp) - app/models/sales/leads.py
- `lead_requirement_details` (LeadRequirementDetail) - app/models/sales/technical_assessment.py
- `leads` (Lead) - app/models/sales/leads.py
- `material_cost_update_reminders` (MaterialCostUpdateReminder) - app/models/sales/quotes.py
- `open_items` (OpenItem) - app/models/sales/technical_assessment.py
- `opportunities` (Opportunity) - app/models/sales/leads.py
- `opportunity_requirements` (OpportunityRequirement) - app/models/sales/leads.py
- `presale_ai_cost_estimation` (PresaleAICostEstimation) - app/models/sales/presale_ai_cost.py
- `presale_ai_win_rate` (PresaleAIWinRate) - app/models/sales/presale_ai_win_rate.py
- `presale_cost_history` (PresaleCostHistory) - app/models/sales/presale_ai_cost.py
- `presale_cost_optimization_record` (PresaleCostOptimizationRecord) - app/models/sales/presale_ai_cost.py
- `presale_win_rate_history` (PresaleWinRateHistory) - app/models/sales/presale_ai_win_rate.py
- `purchase_material_costs` (PurchaseMaterialCost) - app/models/sales/quotes.py
- `quote_approvals` (QuoteApproval) - app/models/sales/technical_assessment.py
- `quote_cost_approvals` (QuoteCostApproval) - app/models/sales/quotes.py
- `quote_cost_histories` (QuoteCostHistory) - app/models/sales/quotes.py
- `quote_cost_templates` (QuoteCostTemplate) - app/models/sales/quotes.py
- `quote_items` (QuoteItem) - app/models/sales/quotes.py
- `quote_template_versions` (QuoteTemplateVersion) - app/models/sales/quotes.py
- `quote_templates` (QuoteTemplate) - app/models/sales/quotes.py
- `quote_versions` (QuoteVersion) - app/models/sales/quotes.py
- `quotes` (Quote) - app/models/sales/quotes.py
- `receivable_disputes` (ReceivableDispute) - app/models/sales/invoices.py
- `requirement_freezes` (RequirementFreeze) - app/models/sales/technical_assessment.py
- `sales_ranking_configs` (SalesRankingConfig) - app/models/sales/workflow.py
- `sales_regions` (SalesRegion) - app/models/sales/region.py
- `sales_targets` (SalesTarget) - app/models/sales/workflow.py
- `sales_targets_v2` (SalesTargetV2) - app/models/sales/target_v2.py
- `sales_team_members` (SalesTeamMember) - app/models/sales/team.py
- `sales_teams` (SalesTeam) - app/models/sales/team.py
- `scoring_rules` (ScoringRule) - app/models/sales/technical_assessment.py
- `target_breakdown_logs` (TargetBreakdownLog) - app/models/sales/target_v2.py
- `team_performance_snapshots` (TeamPerformanceSnapshot) - app/models/sales/team.py
- `team_pk_records` (TeamPKRecord) - app/models/sales/team.py
- `technical_assessments` (TechnicalAssessment) - app/models/sales/technical_assessment.py

### 项目管理 (30)

- `catch_up_solutions` (CatchUpSolution) - app/models/project/schedule_prediction.py
- `cost_alert_rules` (CostAlertRule) - app/models/project/cost_forecast.py
- `cost_alerts` (CostAlert) - app/models/project/cost_forecast.py
- `cost_forecasts` (CostForecast) - app/models/project/cost_forecast.py
- `customers` (Customer) - app/models/project/customer.py
- `financial_project_costs` (FinancialProjectCost) - app/models/project/financial.py
- `machines` (Machine) - app/models/project/core.py
- `project_costs` (ProjectCost) - app/models/project/financial.py
- `project_documents` (ProjectDocument) - app/models/project/document.py
- `project_erp` (ProjectERP) - app/models/project/extensions.py
- `project_financials` (ProjectFinancial) - app/models/project/extensions.py
- `project_implementations` (ProjectImplementation) - app/models/project/extensions.py
- `project_member_contributions` (ProjectMemberContribution) - app/models/project/team.py
- `project_members` (ProjectMember) - app/models/project/team.py
- `project_milestones` (ProjectMilestone) - app/models/project/financial.py
- `project_payment_plans` (ProjectPaymentPlan) - app/models/project/financial.py
- `project_presales` (ProjectPresale) - app/models/project/extensions.py
- `project_risk_history` (ProjectRiskHistory) - app/models/project/risk_history.py
- `project_risk_snapshot` (ProjectRiskSnapshot) - app/models/project/risk_history.py
- `project_schedule_prediction` (ProjectSchedulePrediction) - app/models/project/schedule_prediction.py
- `project_stage_resource_plan` (ProjectStageResourcePlan) - app/models/project/resource_plan.py
- `project_stages` (ProjectStage) - app/models/project/lifecycle.py
- `project_status_logs` (ProjectStatusLog) - app/models/project/lifecycle.py
- `project_statuses` (ProjectStatus) - app/models/project/lifecycle.py
- `project_template_versions` (ProjectTemplateVersion) - app/models/project/document.py
- `project_templates` (ProjectTemplate) - app/models/project/document.py
- `project_warranties` (ProjectWarranty) - app/models/project/extensions.py
- `projects` (Project) - app/models/project/core.py
- `resource_conflicts` (ResourceConflict) - app/models/project/resource_plan.py
- `schedule_alerts` (ScheduleAlert) - app/models/project/schedule_prediction.py

## 📊 完整模型清单

❌ `acceptance_issues` - AcceptanceIssue - app/models/acceptance.py
❌ `acceptance_order_items` - AcceptanceOrderItem - app/models/acceptance.py
❌ `acceptance_orders` - AcceptanceOrder - app/models/acceptance.py
❌ `acceptance_reports` - AcceptanceReport - app/models/acceptance.py
❌ `acceptance_signatures` - AcceptanceSignature - app/models/acceptance.py
❌ `acceptance_templates` - AcceptanceTemplate - app/models/acceptance.py
❌ `acceptance_tracking` - AcceptanceTracking - app/models/business_support/acceptance.py
❌ `acceptance_tracking_records` - AcceptanceTrackingRecord - app/models/business_support/acceptance.py
❌ `accountability_records` - AccountabilityRecord - app/models/pipeline_analysis.py
❌ `advantage_product_categories` - AdvantageProductCategory - app/models/advantage_product.py
❌ `advantage_products` - AdvantageProduct - app/models/advantage_product.py
❌ `ai_clarifications` - AIClarification - app/models/sales/technical_assessment.py
❌ `ai_project_plan_templates` - AIProjectPlanTemplate - app/models/ai_planning/plan_template.py
❌ `ai_resource_allocations` - AIResourceAllocation - app/models/ai_planning/resource_allocation.py
❌ `ai_wbs_suggestions` - AIWbsSuggestion - app/models/ai_planning/wbs_suggestion.py
❌ `alert_notifications` - AlertNotification - app/models/alert.py
❌ `alert_records` - AlertRecord - app/models/alert.py
❌ `alert_rule_templates` - AlertRuleTemplate - app/models/alert.py
❌ `alert_rules` - AlertRule - app/models/alert.py
❌ `alert_statistics` - AlertStatistics - app/models/alert.py
❌ `alert_subscriptions` - AlertSubscription - app/models/alert.py
❌ `annual_key_work_project_links` - AnnualKeyWorkProjectLink - app/models/strategy/annual_work.py
❌ `annual_key_works` - AnnualKeyWork - app/models/strategy/annual_work.py
✅ `api_keys` - APIKey - app/models/api_key.py
✅ `api_permissions` - ApiPermission - app/models/user.py
❌ `approval_action_logs` - ApprovalActionLog - app/models/approval/log.py
❌ `approval_carbon_copies` - ApprovalCarbonCopy - app/models/approval/task.py
❌ `approval_comments` - ApprovalComment - app/models/approval/log.py
❌ `approval_countersign_results` - ApprovalCountersignResult - app/models/approval/task.py
❌ `approval_delegate_logs` - ApprovalDelegateLog - app/models/approval/delegate.py
❌ `approval_delegates` - ApprovalDelegate - app/models/approval/delegate.py
❌ `approval_flow_definitions` - ApprovalFlowDefinition - app/models/approval/flow.py
❌ `approval_history` - ApprovalHistory - app/models/sales/workflow.py
❌ `approval_instances` - ApprovalInstance - app/models/approval/instance.py
❌ `approval_node_definitions` - ApprovalNodeDefinition - app/models/approval/flow.py
❌ `approval_records` - ApprovalRecord - app/models/sales/workflow.py
❌ `approval_routing_rules` - ApprovalRoutingRule - app/models/approval/flow.py
❌ `approval_tasks` - ApprovalTask - app/models/approval/task.py
❌ `approval_template_versions` - ApprovalTemplateVersion - app/models/approval/template.py
❌ `approval_templates` - ApprovalTemplate - app/models/approval/template.py
❌ `approval_workflow_steps` - ApprovalWorkflowStep - app/models/sales/workflow.py
❌ `approval_workflows` - ApprovalWorkflow - app/models/sales/workflow.py
❌ `arrival_follow_ups` - ArrivalFollowUp - app/models/shortage/arrivals.py
❌ `baseline_tasks` - BaselineTask - app/models/progress.py
❌ `bidding_documents` - BiddingDocument - app/models/business_support/bidding.py
❌ `bidding_projects` - BiddingProject - app/models/business_support/bidding.py
❌ `bom_headers` - BomHeader - app/models/material.py
❌ `bom_item_assembly_attrs` - BomItemAssemblyAttrs - app/models/assembly_kit.py
❌ `bom_items` - BomItem - app/models/material.py
❌ `bonus_allocation_sheets` - BonusAllocationSheet - app/models/bonus.py
❌ `bonus_calculations` - BonusCalculation - app/models/bonus.py
❌ `bonus_distributions` - BonusDistribution - app/models/bonus.py
❌ `bonus_rules` - BonusRule - app/models/bonus.py
❌ `catch_up_solutions` - CatchUpSolution - app/models/project/schedule_prediction.py
❌ `change_approval_records` - ChangeApprovalRecord - app/models/change_request.py
❌ `change_impact_analysis` - ChangeImpactAnalysis - app/models/change_impact.py
❌ `change_notifications` - ChangeNotification - app/models/change_request.py
❌ `change_requests` - ChangeRequest - app/models/change_request.py
❌ `change_response_suggestions` - ChangeResponseSuggestion - app/models/change_impact.py
❌ `code_module` - CodeModule - app/models/engineer_performance/test.py
❌ `code_review_record` - CodeReviewRecord - app/models/engineer_performance/test.py
❌ `collaboration_rating` - CollaborationRating - app/models/engineer_performance/common.py
❌ `component_selection` - ComponentSelection - app/models/engineer_performance/electrical.py
❌ `contacts` - Contact - app/models/sales/contacts.py
❌ `contract_amendments` - ContractAmendment - app/models/sales/contracts.py
❌ `contract_approvals` - ContractApproval - app/models/sales/contracts.py
❌ `contract_attachments` - ContractAttachment - app/models/sales/contracts.py
❌ `contract_deliverables` - ContractDeliverable - app/models/sales/contracts.py
❌ `contract_reminders` - ContractReminder - app/models/organization.py
❌ `contract_reviews` - ContractReview - app/models/business_support/contract.py
❌ `contract_seal_records` - ContractSealRecord - app/models/business_support/contract.py
❌ `contract_template_versions` - ContractTemplateVersion - app/models/sales/contracts.py
❌ `contract_templates` - ContractTemplate - app/models/sales/contracts.py
❌ `contract_terms` - ContractTerm - app/models/sales/contracts.py
❌ `contracts` - Contract - app/models/sales/contracts.py
❌ `cost_alert_rules` - CostAlertRule - app/models/project/cost_forecast.py
❌ `cost_alerts` - CostAlert - app/models/project/cost_forecast.py
❌ `cost_forecasts` - CostForecast - app/models/project/cost_forecast.py
❌ `cost_optimization_suggestions` - CostOptimizationSuggestion - app/models/cost_prediction.py
❌ `cost_prediction` - CostPrediction - app/models/cost_prediction.py
❌ `cpq_rule_sets` - CpqRuleSet - app/models/sales/quotes.py
❌ `csfs` - CSF - app/models/strategy/core.py
❌ `culture_wall_config` - CultureWallConfig - app/models/culture_wall_config.py
❌ `culture_wall_content` - CultureWallContent - app/models/culture_wall.py
❌ `culture_wall_read_record` - CultureWallReadRecord - app/models/culture_wall.py
❌ `customer_communications` - CustomerCommunication - app/models/service/communication_satisfaction.py
❌ `customer_satisfactions` - CustomerSatisfaction - app/models/service/communication_satisfaction.py
❌ `customer_supplier_registrations` - CustomerSupplierRegistration - app/models/business_support/registration.py
❌ `customer_tags` - CustomerTag - app/models/sales/customer_tags.py
❌ `customers` - Customer - app/models/project/customer.py
❌ `data_export_task` - DataExportTask - app/models/report_center.py
❌ `data_import_task` - DataImportTask - app/models/report_center.py
✅ `data_scope_rules` - DataScopeRule - app/models/permission.py
❌ `defect_analysis` - DefectAnalysis - app/models/production/quality_inspection.py
❌ `delivery_orders` - DeliveryOrder - app/models/business_support/delivery.py
❌ `department_objectives` - DepartmentObjective - app/models/strategy/decomposition.py
❌ `departments` - Department - app/models/organization.py
❌ `design_reuse_record` - DesignReuseRecord - app/models/engineer_performance/mechanical.py
❌ `design_review` - DesignReview - app/models/engineer_performance/mechanical.py
❌ `document_archives` - DocumentArchive - app/models/business_support/document.py
❌ `earned_value_data` - EarnedValueData - app/models/earned_value.py
❌ `earned_value_snapshots` - EarnedValueSnapshot - app/models/earned_value.py
❌ `ecn` - Ecn - app/models/ecn/core.py
❌ `ecn_affected_materials` - EcnAffectedMaterial - app/models/ecn/impact.py
❌ `ecn_affected_orders` - EcnAffectedOrder - app/models/ecn/impact.py
❌ `ecn_approval_matrix` - EcnApprovalMatrix - app/models/ecn/config.py
❌ `ecn_approvals` - EcnApproval - app/models/ecn/evaluation_approval.py
❌ `ecn_bom_impacts` - EcnBomImpact - app/models/ecn/impact.py
❌ `ecn_evaluations` - EcnEvaluation - app/models/ecn/evaluation_approval.py
❌ `ecn_logs` - EcnLog - app/models/ecn/log.py
❌ `ecn_responsibilities` - EcnResponsibility - app/models/ecn/responsibility_template.py
❌ `ecn_solution_templates` - EcnSolutionTemplate - app/models/ecn/responsibility_template.py
❌ `ecn_tasks` - EcnTask - app/models/ecn/execution.py
❌ `ecn_types` - EcnType - app/models/ecn/config.py
❌ `electrical_drawing_version` - ElectricalDrawingVersion - app/models/engineer_performance/electrical.py
❌ `electrical_fault_record` - ElectricalFaultRecord - app/models/engineer_performance/electrical.py
❌ `employee_contracts` - EmployeeContract - app/models/organization.py
❌ `employee_hr_profiles` - EmployeeHrProfile - app/models/organization.py
❌ `employee_org_assignments` - EmployeeOrgAssignment - app/models/organization.py
❌ `employee_qualification` - EmployeeQualification - app/models/qualification.py
❌ `employees` - Employee - app/models/organization.py
❌ `employees` - Employee - app/models/employee_encrypted_example.py
❌ `engineer_dimension_config` - EngineerDimensionConfig - app/models/engineer_performance/common.py
❌ `engineer_profile` - EngineerProfile - app/models/engineer_performance/common.py
❌ `equipment` - Equipment - app/models/production/equipment.py
❌ `equipment_maintenance` - EquipmentMaintenance - app/models/production/equipment.py
❌ `equipment_oee_record` - EquipmentOEERecord - app/models/production/equipment_oee_record.py
❌ `equity_structures` - EquityStructure - app/models/finance.py
❌ `evaluation_weight_config` - EvaluationWeightConfig - app/models/performance/monthly_system.py
❌ `exception_actions` - ExceptionAction - app/models/alert.py
❌ `exception_escalations` - ExceptionEscalation - app/models/alert.py
❌ `exception_events` - ExceptionEvent - app/models/alert.py
❌ `exception_handling_flow` - ExceptionHandlingFlow - app/models/production/exception_handling_flow.py
❌ `exception_knowledge` - ExceptionKnowledge - app/models/production/exception_knowledge.py
❌ `exception_pdca` - ExceptionPDCA - app/models/production/exception_pdca.py
❌ `failure_cases` - FailureCase - app/models/sales/technical_assessment.py
❌ `financial_project_costs` - FinancialProjectCost - app/models/project/financial.py
❌ `funding_records` - FundingRecord - app/models/finance.py
❌ `funding_rounds` - FundingRound - app/models/finance.py
❌ `funding_usages` - FundingUsage - app/models/finance.py
❌ `goods_receipt_items` - GoodsReceiptItem - app/models/purchase.py
❌ `goods_receipts` - GoodsReceipt - app/models/purchase.py
❌ `holidays` - Holiday - app/models/holiday.py
❌ `hourly_rate_configs` - HourlyRateConfig - app/models/hourly_rate.py
❌ `hr_ai_matching_log` - HrAIMatchingLog - app/models/staff_matching.py
❌ `hr_employee_profile` - HrEmployeeProfile - app/models/staff_matching.py
❌ `hr_employee_tag_evaluation` - HrEmployeeTagEvaluation - app/models/staff_matching.py
❌ `hr_project_performance` - HrProjectPerformance - app/models/staff_matching.py
❌ `hr_tag_dict` - HrTagDict - app/models/staff_matching.py
❌ `hr_transactions` - HrTransaction - app/models/organization.py
❌ `import_template` - ImportTemplate - app/models/report_center.py
❌ `industries` - Industry - app/models/advantage_product.py
❌ `industry_category_mappings` - IndustryCategoryMapping - app/models/advantage_product.py
❌ `installation_dispatch_orders` - InstallationDispatchOrder - app/models/installation_dispatch.py
❌ `investors` - Investor - app/models/finance.py
❌ `invoice_approvals` - InvoiceApproval - app/models/sales/invoices.py
❌ `invoice_requests` - InvoiceRequest - app/models/business_support/invoice.py
❌ `invoices` - Invoice - app/models/sales/invoices.py
❌ `issue_follow_up_records` - IssueFollowUpRecord - app/models/issue.py
❌ `issue_follow_ups` - IssueFollowUp - app/models/acceptance.py
❌ `issue_statistics_snapshots` - IssueStatisticsSnapshot - app/models/issue.py
❌ `issue_templates` - IssueTemplate - app/models/issue.py
❌ `issues` - Issue - app/models/issue.py
❌ `job_duty_template` - JobDutyTemplate - app/models/task_center.py
❌ `job_levels` - JobLevel - app/models/organization.py
❌ `knowledge_base` - KnowledgeBase - app/models/service/knowledge.py
❌ `knowledge_contribution` - KnowledgeContribution - app/models/engineer_performance/common.py
❌ `knowledge_reuse_log` - KnowledgeReuseLog - app/models/engineer_performance/common.py
❌ `kpi_data_sources` - KPIDataSource - app/models/strategy/core.py
❌ `kpi_history` - KPIHistory - app/models/strategy/core.py
❌ `kpis` - KPI - app/models/strategy/core.py
❌ `lead_follow_ups` - LeadFollowUp - app/models/sales/leads.py
❌ `lead_requirement_details` - LeadRequirementDetail - app/models/sales/technical_assessment.py
❌ `leads` - Lead - app/models/sales/leads.py
❌ `machines` - Machine - app/models/project/core.py
❌ `management_rhythm_config` - ManagementRhythmConfig - app/models/management_rhythm.py
❌ `mat_alert_log` - AlertHandleLog - app/models/shortage/alerts.py
❌ `mat_kit_check` - KitCheck - app/models/shortage/requirements.py
❌ `mat_material_requirement` - MaterialRequirement - app/models/shortage/requirements.py
❌ `mat_shortage_daily_report` - ShortageDailyReport - app/models/shortage/alerts.py
❌ `mat_work_order_bom` - WorkOrderBom - app/models/shortage/requirements.py
❌ `material_alert` - MaterialAlert - app/models/production/material_tracking.py
❌ `material_alert_rule` - MaterialAlertRule - app/models/production/material_tracking.py
❌ `material_arrivals` - MaterialArrival - app/models/shortage/arrivals.py
❌ `material_batch` - MaterialBatch - app/models/production/material_tracking.py
❌ `material_categories` - MaterialCategory - app/models/material.py
❌ `material_consumption` - MaterialConsumption - app/models/production/material_tracking.py
❌ `material_cost_update_reminders` - MaterialCostUpdateReminder - app/models/sales/quotes.py
❌ `material_requisition` - MaterialRequisition - app/models/production/material.py
❌ `material_requisition_item` - MaterialRequisitionItem - app/models/production/material.py
❌ `material_shortages` - MaterialShortage - app/models/material.py
❌ `material_substitutions` - MaterialSubstitution - app/models/shortage/handling.py
❌ `material_suppliers` - MaterialSupplier - app/models/material.py
❌ `material_transfers` - MaterialTransfer - app/models/shortage/handling.py
❌ `materials` - Material - app/models/material.py
❌ `mechanical_debug_issue` - MechanicalDebugIssue - app/models/engineer_performance/mechanical.py
❌ `meeting_action_item` - MeetingActionItem - app/models/management_rhythm.py
❌ `meeting_report` - MeetingReport - app/models/management_rhythm.py
❌ `meeting_report_config` - MeetingReportConfig - app/models/management_rhythm.py
✅ `menu_permissions` - MenuPermission - app/models/permission.py
❌ `mes_assembly_stage` - AssemblyStage - app/models/assembly_kit.py
❌ `mes_assembly_template` - AssemblyTemplate - app/models/assembly_kit.py
❌ `mes_category_stage_mapping` - CategoryStageMapping - app/models/assembly_kit.py
❌ `mes_kit_rate_snapshot` - KitRateSnapshot - app/models/assembly_kit.py
❌ `mes_material_readiness` - MaterialReadiness - app/models/assembly_kit.py
❌ `mes_project_staffing_need` - MesProjectStaffingNeed - app/models/staff_matching.py
❌ `mes_scheduling_suggestion` - SchedulingSuggestion - app/models/assembly_kit.py
❌ `mes_shortage_alert_rule` - ShortageAlertRule - app/models/assembly_kit.py
❌ `mes_shortage_detail` - ShortageDetail - app/models/assembly_kit.py
❌ `monthly_work_summary` - MonthlyWorkSummary - app/models/performance/monthly_system.py
❌ `new_product_requests` - NewProductRequest - app/models/advantage_product.py
❌ `node_definitions` - NodeDefinition - app/models/stage_template.py
❌ `node_tasks` - NodeTask - app/models/stage_instance.py
❌ `notification_settings` - NotificationSettings - app/models/notification.py
❌ `notifications` - Notification - app/models/notification.py
❌ `open_items` - OpenItem - app/models/sales/technical_assessment.py
❌ `opportunities` - Opportunity - app/models/sales/leads.py
❌ `opportunity_requirements` - OpportunityRequirement - app/models/sales/leads.py
❌ `organization_units` - OrganizationUnit - app/models/organization.py
❌ `outsourcing_deliveries` - OutsourcingDelivery - app/models/outsourcing.py
❌ `outsourcing_delivery_items` - OutsourcingDeliveryItem - app/models/outsourcing.py
❌ `outsourcing_evaluations` - OutsourcingEvaluation - app/models/outsourcing.py
❌ `outsourcing_inspections` - OutsourcingInspection - app/models/outsourcing.py
❌ `outsourcing_order_items` - OutsourcingOrderItem - app/models/outsourcing.py
❌ `outsourcing_orders` - OutsourcingOrder - app/models/outsourcing.py
❌ `outsourcing_payments` - OutsourcingPayment - app/models/outsourcing.py
❌ `outsourcing_progress` - OutsourcingProgress - app/models/outsourcing.py
❌ `overtime_application` - OvertimeApplication - app/models/timesheet.py
❌ `payment_reminders` - PaymentReminder - app/models/business_support/payment.py
❌ `performance_adjustment_history` - PerformanceAdjustmentHistory - app/models/performance/appeal_adjustment.py
❌ `performance_appeal` - PerformanceAppeal - app/models/performance/appeal_adjustment.py
❌ `performance_evaluation` - PerformanceEvaluation - app/models/performance/result_evaluation.py
❌ `performance_evaluation_record` - PerformanceEvaluationRecord - app/models/performance/monthly_system.py
❌ `performance_indicator` - PerformanceIndicator - app/models/performance/period_indicator.py
❌ `performance_period` - PerformancePeriod - app/models/performance/period_indicator.py
❌ `performance_ranking_snapshot` - PerformanceRankingSnapshot - app/models/performance/contribution_ranking.py
❌ `performance_result` - PerformanceResult - app/models/performance/result_evaluation.py
❌ `permission_audits` - PermissionAudit - app/models/user.py
❌ `permission_groups` - PermissionGroup - app/models/permission.py
❌ `personal_goal` - PersonalGoal - app/models/culture_wall.py
❌ `personal_kpis` - PersonalKPI - app/models/strategy/decomposition.py
❌ `pipeline_break_records` - PipelineBreakRecord - app/models/pipeline_analysis.py
❌ `pipeline_health_snapshots` - PipelineHealthSnapshot - app/models/pipeline_analysis.py
❌ `pitfall_learning_progress` - PitfallLearningProgress - app/models/pitfall.py
❌ `pitfall_recommendations` - PitfallRecommendation - app/models/pitfall.py
❌ `pitfalls` - Pitfall - app/models/pitfall.py
❌ `plc_module_library` - PlcModuleLibrary - app/models/engineer_performance/electrical.py
❌ `plc_program_version` - PlcProgramVersion - app/models/engineer_performance/electrical.py
❌ `pmo_change_request` - PmoChangeRequest - app/models/pmo/change_risk.py
❌ `pmo_meeting` - PmoMeeting - app/models/pmo/cost_meeting.py
❌ `pmo_project_closure` - PmoProjectClosure - app/models/pmo/resource_closure.py
❌ `pmo_project_cost` - PmoProjectCost - app/models/pmo/cost_meeting.py
❌ `pmo_project_initiation` - PmoProjectInitiation - app/models/pmo/initiation_phase.py
❌ `pmo_project_phase` - PmoProjectPhase - app/models/pmo/initiation_phase.py
❌ `pmo_project_risk` - PmoProjectRisk - app/models/pmo/change_risk.py
❌ `pmo_resource_allocation` - PmoResourceAllocation - app/models/pmo/resource_closure.py
❌ `position_competency_model` - PositionCompetencyModel - app/models/qualification.py
❌ `position_roles` - PositionRole - app/models/organization.py
❌ `positions` - Position - app/models/organization.py
❌ `presale_ai_audit_log` - PresaleAIAuditLog - app/models/presale_ai.py
❌ `presale_ai_config` - PresaleAIConfig - app/models/presale_ai.py
❌ `presale_ai_cost_estimation` - PresaleAICostEstimation - app/models/sales/presale_ai_cost.py
❌ `presale_ai_emotion_analysis` - PresaleAIEmotionAnalysis - app/models/presale_ai_emotion_analysis.py
❌ `presale_ai_feedback` - PresaleAIFeedback - app/models/presale_ai.py
❌ `presale_ai_generation_log` - PresaleAIGenerationLog - app/models/presale_ai_solution.py
❌ `presale_ai_qa` - PresaleAIQA - app/models/presale_ai_qa.py
❌ `presale_ai_quotation` - PresaleAIQuotation - app/models/presale_ai_quotation.py
❌ `presale_ai_requirement_analysis` - PresaleAIRequirementAnalysis - app/models/presale_ai_requirement_analysis.py
❌ `presale_ai_solution` - PresaleAISolution - app/models/presale_ai_solution.py
❌ `presale_ai_usage_stats` - PresaleAIUsageStats - app/models/presale_ai.py
❌ `presale_ai_win_rate` - PresaleAIWinRate - app/models/sales/presale_ai_win_rate.py
❌ `presale_ai_workflow_log` - PresaleAIWorkflowLog - app/models/presale_ai.py
❌ `presale_cost_history` - PresaleCostHistory - app/models/sales/presale_ai_cost.py
❌ `presale_cost_optimization_record` - PresaleCostOptimizationRecord - app/models/sales/presale_ai_cost.py
❌ `presale_customer_tech_profile` - PresaleCustomerTechProfile - app/models/presale.py
❌ `presale_emotion_trend` - PresaleEmotionTrend - app/models/presale_emotion_trend.py
❌ `presale_expenses` - PresaleExpense - app/models/presale_expense.py
❌ `presale_follow_up_reminder` - PresaleFollowUpReminder - app/models/presale_follow_up_reminder.py
❌ `presale_knowledge_case` - PresaleKnowledgeCase - app/models/presale_knowledge_case.py
❌ `presale_mobile_assistant_chat` - PresaleMobileAssistantChat - app/models/presale_mobile.py
❌ `presale_mobile_offline_data` - PresaleMobileOfflineData - app/models/presale_mobile.py
❌ `presale_mobile_quick_estimate` - PresaleMobileQuickEstimate - app/models/presale_mobile.py
❌ `presale_solution` - PresaleSolution - app/models/presale.py
❌ `presale_solution_cost` - PresaleSolutionCost - app/models/presale.py
❌ `presale_solution_template` - PresaleSolutionTemplate - app/models/presale.py
❌ `presale_solution_templates` - PresaleSolutionTemplate - app/models/presale_ai_solution.py
❌ `presale_support_ticket` - PresaleSupportTicket - app/models/presale.py
❌ `presale_tender_record` - PresaleTenderRecord - app/models/presale.py
❌ `presale_ticket_deliverable` - PresaleTicketDeliverable - app/models/presale.py
❌ `presale_ticket_progress` - PresaleTicketProgress - app/models/presale.py
❌ `presale_visit_record` - PresaleVisitRecord - app/models/presale_mobile.py
❌ `presale_win_rate_history` - PresaleWinRateHistory - app/models/sales/presale_ai_win_rate.py
❌ `presale_workload` - PresaleWorkload - app/models/presale.py
❌ `process_dict` - ProcessDict - app/models/production/process.py
❌ `production_daily_report` - ProductionDailyReport - app/models/production/material.py
❌ `production_exception` - ProductionException - app/models/production/production_exception.py
❌ `production_plan` - ProductionPlan - app/models/production/production_plan.py
❌ `production_progress_log` - ProductionProgressLog - app/models/production/production_progress_log.py
❌ `production_schedule` - ProductionSchedule - app/models/production/production_schedule.py
❌ `progress_alert` - ProgressAlert - app/models/production/progress_alert.py
❌ `progress_logs` - ProgressLog - app/models/progress.py
❌ `progress_reports` - ProgressReport - app/models/progress.py
❌ `project_best_practices` - ProjectBestPractice - app/models/project_review.py
❌ `project_budget_items` - ProjectBudgetItem - app/models/budget.py
❌ `project_budgets` - ProjectBudget - app/models/budget.py
❌ `project_contribution` - ProjectContribution - app/models/performance/contribution_ranking.py
❌ `project_cost_allocation_rules` - ProjectCostAllocationRule - app/models/budget.py
❌ `project_costs` - ProjectCost - app/models/project/financial.py
❌ `project_documents` - ProjectDocument - app/models/project/document.py
❌ `project_erp` - ProjectERP - app/models/project/extensions.py
❌ `project_evaluation_dimensions` - ProjectEvaluationDimension - app/models/project_evaluation.py
❌ `project_evaluations` - ProjectEvaluation - app/models/project_evaluation.py
❌ `project_financials` - ProjectFinancial - app/models/project/extensions.py
❌ `project_health_snapshots` - ProjectHealthSnapshot - app/models/alert.py
❌ `project_implementations` - ProjectImplementation - app/models/project/extensions.py
❌ `project_lessons` - ProjectLesson - app/models/project_review.py
❌ `project_member_contributions` - ProjectMemberContribution - app/models/project/team.py
❌ `project_members` - ProjectMember - app/models/project/team.py
❌ `project_milestones` - ProjectMilestone - app/models/project/financial.py
❌ `project_node_instances` - ProjectNodeInstance - app/models/stage_instance.py
❌ `project_payment_plans` - ProjectPaymentPlan - app/models/project/financial.py
❌ `project_presales` - ProjectPresale - app/models/project/extensions.py
❌ `project_reviews` - ProjectReview - app/models/project_review.py
❌ `project_risk_history` - ProjectRiskHistory - app/models/project/risk_history.py
❌ `project_risk_snapshot` - ProjectRiskSnapshot - app/models/project/risk_history.py
❌ `project_risks` - ProjectRisk - app/models/project_risk.py
❌ `project_role_configs` - ProjectRoleConfig - app/models/project_role.py
❌ `project_role_types` - ProjectRoleType - app/models/project_role.py
❌ `project_schedule_prediction` - ProjectSchedulePrediction - app/models/project/schedule_prediction.py
❌ `project_stage_instances` - ProjectStageInstance - app/models/stage_instance.py
❌ `project_stage_resource_plan` - ProjectStageResourcePlan - app/models/project/resource_plan.py
❌ `project_stages` - ProjectStage - app/models/project/lifecycle.py
❌ `project_status_logs` - ProjectStatusLog - app/models/project/lifecycle.py
❌ `project_statuses` - ProjectStatus - app/models/project/lifecycle.py
❌ `project_template_versions` - ProjectTemplateVersion - app/models/project/document.py
❌ `project_templates` - ProjectTemplate - app/models/project/document.py
❌ `project_warranties` - ProjectWarranty - app/models/project/extensions.py
❌ `projects` - Project - app/models/project/core.py
❌ `purchase_material_costs` - PurchaseMaterialCost - app/models/sales/quotes.py
❌ `purchase_order_items` - PurchaseOrderItem - app/models/purchase.py
❌ `purchase_orders` - PurchaseOrder - app/models/purchase.py
❌ `purchase_request_items` - PurchaseRequestItem - app/models/purchase.py
❌ `purchase_requests` - PurchaseRequest - app/models/purchase.py
❌ `qualification_assessment` - QualificationAssessment - app/models/qualification.py
❌ `qualification_level` - QualificationLevel - app/models/qualification.py
❌ `quality_alert_rule` - QualityAlertRule - app/models/production/quality_inspection.py
❌ `quality_inspection` - QualityInspection - app/models/production/quality_inspection.py
❌ `quality_risk_detection` - QualityRiskDetection - app/models/quality_risk_detection.py
❌ `quality_test_recommendations` - QualityTestRecommendation - app/models/quality_risk_detection.py
❌ `quotation_approvals` - QuotationApproval - app/models/presale_ai_quotation.py
❌ `quotation_templates` - QuotationTemplate - app/models/presale_ai_quotation.py
❌ `quotation_versions` - QuotationVersion - app/models/presale_ai_quotation.py
❌ `quote_approvals` - QuoteApproval - app/models/sales/technical_assessment.py
❌ `quote_cost_approvals` - QuoteCostApproval - app/models/sales/quotes.py
❌ `quote_cost_histories` - QuoteCostHistory - app/models/sales/quotes.py
❌ `quote_cost_templates` - QuoteCostTemplate - app/models/sales/quotes.py
❌ `quote_items` - QuoteItem - app/models/sales/quotes.py
❌ `quote_template_versions` - QuoteTemplateVersion - app/models/sales/quotes.py
❌ `quote_templates` - QuoteTemplate - app/models/sales/quotes.py
❌ `quote_versions` - QuoteVersion - app/models/sales/quotes.py
❌ `quotes` - Quote - app/models/sales/quotes.py
❌ `rd_cost` - RdCost - app/models/rd_project.py
❌ `rd_cost_allocation_rule` - RdCostAllocationRule - app/models/rd_project.py
❌ `rd_cost_type` - RdCostType - app/models/rd_project.py
❌ `rd_project` - RdProject - app/models/rd_project.py
❌ `rd_project_category` - RdProjectCategory - app/models/rd_project.py
❌ `rd_report_record` - RdReportRecord - app/models/rd_project.py
❌ `receivable_disputes` - ReceivableDispute - app/models/sales/invoices.py
❌ `reconciliations` - Reconciliation - app/models/business_support/reconciliation.py
❌ `report_archive` - ReportArchive - app/models/report.py
❌ `report_definition` - ReportDefinition - app/models/report_center.py
❌ `report_generation` - ReportGeneration - app/models/report_center.py
❌ `report_metric_definition` - ReportMetricDefinition - app/models/management_rhythm.py
❌ `report_recipient` - ReportRecipient - app/models/report.py
❌ `report_subscription` - ReportSubscription - app/models/report_center.py
❌ `report_template` - ReportTemplate - app/models/report_center.py
❌ `report_template` - ReportTemplate - app/models/report.py
❌ `requirement_freezes` - RequirementFreeze - app/models/sales/technical_assessment.py
❌ `resource_conflict` - ResourceConflict - app/models/production/production_schedule.py
❌ `resource_conflict_detection` - ResourceConflictDetection - app/models/resource_scheduling.py
❌ `resource_conflicts` - ResourceConflict - app/models/project/resource_plan.py
❌ `resource_demand_forecast` - ResourceDemandForecast - app/models/resource_scheduling.py
❌ `resource_scheduling_logs` - ResourceSchedulingLog - app/models/resource_scheduling.py
❌ `resource_scheduling_suggestions` - ResourceSchedulingSuggestion - app/models/resource_scheduling.py
❌ `resource_utilization_analysis` - ResourceUtilizationAnalysis - app/models/resource_scheduling.py
❌ `review_checklist_records` - ReviewChecklistRecord - app/models/technical_review.py
❌ `review_issues` - ReviewIssue - app/models/technical_review.py
❌ `review_materials` - ReviewMaterial - app/models/technical_review.py
❌ `review_participants` - ReviewParticipant - app/models/technical_review.py
❌ `rework_order` - ReworkOrder - app/models/production/quality_inspection.py
❌ `rhythm_dashboard_snapshot` - RhythmDashboardSnapshot - app/models/management_rhythm.py
❌ `role_api_permissions` - RoleApiPermission - app/models/user.py
❌ `role_data_scopes` - RoleDataScope - app/models/permission.py
❌ `role_menus` - RoleMenu - app/models/permission.py
❌ `role_templates` - RoleTemplate - app/models/user.py
✅ `roles` - Role - app/models/user.py
❌ `salary_records` - SalaryRecord - app/models/organization.py
❌ `sales_order_items` - SalesOrderItem - app/models/business_support/sales_order.py
❌ `sales_orders` - SalesOrder - app/models/business_support/sales_order.py
❌ `sales_ranking_configs` - SalesRankingConfig - app/models/sales/workflow.py
❌ `sales_regions` - SalesRegion - app/models/sales/region.py
❌ `sales_targets` - SalesTarget - app/models/sales/workflow.py
❌ `sales_targets_v2` - SalesTargetV2 - app/models/sales/target_v2.py
❌ `sales_team_members` - SalesTeamMember - app/models/sales/team.py
❌ `sales_teams` - SalesTeam - app/models/sales/team.py
❌ `satisfaction_survey_templates` - SatisfactionSurveyTemplate - app/models/service/communication_satisfaction.py
❌ `schedule_adjustment_log` - ScheduleAdjustmentLog - app/models/production/production_schedule.py
❌ `schedule_alerts` - ScheduleAlert - app/models/project/schedule_prediction.py
❌ `schedule_baselines` - ScheduleBaseline - app/models/progress.py
❌ `scheduler_task_configs` - SchedulerTaskConfig - app/models/scheduler_config.py
❌ `scoring_rules` - ScoringRule - app/models/sales/technical_assessment.py
❌ `service_records` - ServiceRecord - app/models/service/record.py
❌ `service_ticket_cc_users` - ServiceTicketCcUser - app/models/service/ticket.py
❌ `service_ticket_projects` - ServiceTicketProject - app/models/service/ticket.py
❌ `service_tickets` - ServiceTicket - app/models/service/ticket.py
❌ `shortage_reports` - ShortageReport - app/models/shortage/reports.py
❌ `sla_monitors` - SLAMonitor - app/models/sla.py
❌ `sla_policies` - SLAPolicy - app/models/sla.py
❌ `solution_credit_configs` - SolutionCreditConfig - app/models/user.py
❌ `solution_credit_transactions` - SolutionCreditTransaction - app/models/user.py
❌ `solution_templates` - SolutionTemplate - app/models/issue.py
❌ `spec_match_records` - SpecMatchRecord - app/models/technical_spec.py
❌ `stage_definitions` - StageDefinition - app/models/stage_template.py
❌ `stage_templates` - StageTemplate - app/models/stage_template.py
❌ `standard_cost_history` - StandardCostHistory - app/models/standard_cost.py
❌ `standard_costs` - StandardCost - app/models/standard_cost.py
❌ `state_transition_logs` - StateTransitionLog - app/models/state_machine.py
❌ `strategic_meeting` - StrategicMeeting - app/models/management_rhythm.py
❌ `strategies` - Strategy - app/models/strategy/core.py
❌ `strategy_calendar_events` - StrategyCalendarEvent - app/models/strategy/review.py
❌ `strategy_comparisons` - StrategyComparison - app/models/strategy/comparison.py
❌ `strategy_reviews` - StrategyReview - app/models/strategy/review.py
❌ `target_breakdown_logs` - TargetBreakdownLog - app/models/sales/target_v2.py
❌ `task_approval_workflows` - TaskApprovalWorkflow - app/models/task_center.py
❌ `task_comment` - TaskComment - app/models/task_center.py
❌ `task_completion_proofs` - TaskCompletionProof - app/models/task_center.py
❌ `task_dependencies` - TaskDependency - app/models/progress.py
❌ `task_operation_log` - TaskOperationLog - app/models/task_center.py
❌ `task_reminder` - TaskReminder - app/models/task_center.py
❌ `task_unified` - TaskUnified - app/models/task_center.py
❌ `tasks` - Task - app/models/progress.py
❌ `team_bonus_allocations` - TeamBonusAllocation - app/models/bonus.py
❌ `team_performance_snapshots` - TeamPerformanceSnapshot - app/models/sales/team.py
❌ `team_pk_records` - TeamPKRecord - app/models/sales/team.py
❌ `technical_assessments` - TechnicalAssessment - app/models/sales/technical_assessment.py
❌ `technical_reviews` - TechnicalReview - app/models/technical_review.py
❌ `technical_spec_requirements` - TechnicalSpecRequirement - app/models/technical_spec.py
❌ `template_categories` - TemplateCategory - app/models/acceptance.py
❌ `template_check_items` - TemplateCheckItem - app/models/acceptance.py
❌ `test_bug_record` - TestBugRecord - app/models/engineer_performance/test.py
❌ `timesheet` - Timesheet - app/models/timesheet.py
❌ `timesheet_analytics` - TimesheetAnalytics - app/models/timesheet_analytics.py
❌ `timesheet_anomaly` - TimesheetAnomaly - app/models/timesheet_analytics.py
❌ `timesheet_anomaly_record` - TimesheetAnomalyRecord - app/models/timesheet_reminder.py
❌ `timesheet_approval_log` - TimesheetApprovalLog - app/models/timesheet.py
❌ `timesheet_batch` - TimesheetBatch - app/models/timesheet.py
❌ `timesheet_forecast` - TimesheetForecast - app/models/timesheet_analytics.py
❌ `timesheet_reminder_config` - TimesheetReminderConfig - app/models/timesheet_reminder.py
❌ `timesheet_reminder_record` - TimesheetReminderRecord - app/models/timesheet_reminder.py
❌ `timesheet_rule` - TimesheetRule - app/models/timesheet.py
❌ `timesheet_summary` - TimesheetSummary - app/models/timesheet.py
❌ `timesheet_trend` - TimesheetTrend - app/models/timesheet_analytics.py
❌ `user_2fa_backup_codes` - User2FABackupCode - app/models/two_factor.py
❌ `user_2fa_secrets` - User2FASecret - app/models/two_factor.py
❌ `user_roles` - UserRole - app/models/user.py
❌ `user_sessions` - UserSession - app/models/session.py
✅ `users` - User - app/models/user.py
❌ `vendors` - Vendor - app/models/vendor.py
❌ `wbs_template_tasks` - WbsTemplateTask - app/models/progress.py
❌ `wbs_templates` - WbsTemplate - app/models/progress.py
❌ `work_log_configs` - WorkLogConfig - app/models/work_log.py
❌ `work_log_mentions` - WorkLogMention - app/models/work_log.py
❌ `work_logs` - WorkLog - app/models/work_log.py
❌ `work_order` - WorkOrder - app/models/production/work_order.py
❌ `work_report` - WorkReport - app/models/production/work_report.py
❌ `worker` - Worker - app/models/production/worker.py
❌ `worker_efficiency_record` - WorkerEfficiencyRecord - app/models/production/worker_efficiency_record.py
❌ `worker_skill` - WorkerSkill - app/models/production/worker.py
❌ `workshop` - Workshop - app/models/production/workshop.py
❌ `workstation` - Workstation - app/models/production/workshop.py
❌ `workstation_status` - WorkstationStatus - app/models/production/workstation_status.py
