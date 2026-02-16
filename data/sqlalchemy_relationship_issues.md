# SQLAlchemy Relationship 问题报告

生成时间: 2026-02-16 15:28:56.209853

## 统计

- 总计模型: 496
- 总计问题: 358
  - P0 严重: 11 个
  - P1 重要: 347 个
  - P2 次要: 0 个

## P0 问题

### P0-1: back_populates_asymmetry

**消息**: Investor.equity_structures 的 back_populates='investor' 在 EquityStructure 中找不到对应关系

- **model**: `Investor`
- **relationship**: `equity_structures`
- **target_model**: `EquityStructure`
- **expected_back_populates**: `investor`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/finance.py`

### P0-2: back_populates_asymmetry

**消息**: RdProject.documents 的 back_populates='rd_project' 在 ProjectDocument 中找不到对应关系

- **model**: `RdProject`
- **relationship**: `documents`
- **target_model**: `ProjectDocument`
- **expected_back_populates**: `rd_project`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/rd_project.py`

### P0-3: back_populates_asymmetry

**消息**: TimesheetReportTemplate.archives 的 back_populates='template' 在 ReportArchive 中找不到对应关系

- **model**: `TimesheetReportTemplate`
- **relationship**: `archives`
- **target_model**: `ReportArchive`
- **expected_back_populates**: `template`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

### P0-4: back_populates_asymmetry

**消息**: TimesheetReportTemplate.recipients 的 back_populates='template' 在 ReportRecipient 中找不到对应关系

- **model**: `TimesheetReportTemplate`
- **relationship**: `recipients`
- **target_model**: `ReportRecipient`
- **expected_back_populates**: `template`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

### P0-5: back_populates_asymmetry

**消息**: ReportArchive.template 的 back_populates='archives' 在 ReportTemplate 中找不到对应关系

- **model**: `ReportArchive`
- **relationship**: `template`
- **target_model**: `ReportTemplate`
- **expected_back_populates**: `archives`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

### P0-6: back_populates_asymmetry

**消息**: ReportRecipient.template 的 back_populates='recipients' 在 ReportTemplate 中找不到对应关系

- **model**: `ReportRecipient`
- **relationship**: `template`
- **target_model**: `ReportTemplate`
- **expected_back_populates**: `recipients`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

### P0-7: back_populates_asymmetry

**消息**: Quote.approvals 的 back_populates='quote' 在 QuoteApproval 中找不到对应关系

- **model**: `Quote`
- **relationship**: `approvals`
- **target_model**: `QuoteApproval`
- **expected_back_populates**: `quote`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/quotes.py`

### P0-8: back_populates_asymmetry

**消息**: QuoteVersion.cost_approvals 的 back_populates='quote_version' 在 QuoteCostApproval 中找不到对应关系

- **model**: `QuoteVersion`
- **relationship**: `cost_approvals`
- **target_model**: `QuoteCostApproval`
- **expected_back_populates**: `quote_version`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/quotes.py`

### P0-9: back_populates_asymmetry

**消息**: QuoteVersion.cost_histories 的 back_populates='quote_version' 在 QuoteCostHistory 中找不到对应关系

- **model**: `QuoteVersion`
- **relationship**: `cost_histories`
- **target_model**: `QuoteCostHistory`
- **expected_back_populates**: `quote_version`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/quotes.py`

### P0-10: back_populates_asymmetry

**消息**: ProjectMember.team_members 的 back_populates='lead' 在 ProjectMember 中找不到对应关系

- **model**: `ProjectMember`
- **relationship**: `team_members`
- **target_model**: `ProjectMember`
- **expected_back_populates**: `lead`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/team.py`

### P0-11: back_populates_asymmetry

**消息**: Customer.opportunities 的 back_populates='customer' 在 Opportunity 中找不到对应关系

- **model**: `Customer`
- **relationship**: `opportunities`
- **target_model**: `Opportunity`
- **expected_back_populates**: `customer`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/customer.py`

## P1 问题

### P1-1: missing_relationship

**消息**: User 有外键 employee_id 指向 employees，但没有对应的 relationship

- **model**: `User`
- **foreign_key**: `employee_id`
- **target_table**: `employees`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/user.py`

### P1-2: missing_relationship

**消息**: Role 有外键 source_template_id 指向 role_templates，但没有对应的 relationship

- **model**: `Role`
- **foreign_key**: `source_template_id`
- **target_table**: `role_templates`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/user.py`

### P1-3: missing_relationship

**消息**: Material 有外键 default_supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `Material`
- **foreign_key**: `default_supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-4: missing_relationship

**消息**: Material 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `Material`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-5: missing_relationship

**消息**: BomHeader 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `BomHeader`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-6: missing_relationship

**消息**: BomHeader 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `BomHeader`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-7: missing_relationship

**消息**: BomItem 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `BomItem`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-8: missing_relationship

**消息**: MaterialShortage 有外键 bom_item_id 指向 bom_items，但没有对应的 relationship

- **model**: `MaterialShortage`
- **foreign_key**: `bom_item_id`
- **target_table**: `bom_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/material.py`

### P1-9: missing_relationship

**消息**: TaskUnified 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-10: missing_relationship

**消息**: TaskUnified 有外键 assignee_id 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `assignee_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-11: missing_relationship

**消息**: TaskUnified 有外键 assigner_id 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `assigner_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-12: missing_relationship

**消息**: TaskUnified 有外键 transfer_from_id 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `transfer_from_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-13: missing_relationship

**消息**: TaskUnified 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-14: missing_relationship

**消息**: TaskUnified 有外键 delay_reported_by 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `delay_reported_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-15: missing_relationship

**消息**: TaskUnified 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-16: missing_relationship

**消息**: TaskUnified 有外键 updated_by 指向 users，但没有对应的 relationship

- **model**: `TaskUnified`
- **foreign_key**: `updated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-17: missing_relationship

**消息**: TaskOperationLog 有外键 operator_id 指向 users，但没有对应的 relationship

- **model**: `TaskOperationLog`
- **foreign_key**: `operator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-18: missing_relationship

**消息**: TaskComment 有外键 commenter_id 指向 users，但没有对应的 relationship

- **model**: `TaskComment`
- **foreign_key**: `commenter_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-19: missing_relationship

**消息**: TaskReminder 有外键 task_id 指向 task_unified，但没有对应的 relationship

- **model**: `TaskReminder`
- **foreign_key**: `task_id`
- **target_table**: `task_unified`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-20: missing_relationship

**消息**: TaskReminder 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TaskReminder`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-21: missing_relationship

**消息**: TaskApprovalWorkflow 有外键 submitted_by 指向 users，但没有对应的 relationship

- **model**: `TaskApprovalWorkflow`
- **foreign_key**: `submitted_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-22: missing_relationship

**消息**: TaskApprovalWorkflow 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `TaskApprovalWorkflow`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-23: missing_relationship

**消息**: TaskCompletionProof 有外键 uploaded_by 指向 users，但没有对应的 relationship

- **model**: `TaskCompletionProof`
- **foreign_key**: `uploaded_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/task_center.py`

### P1-24: missing_relationship

**消息**: PresaleMobileAssistantChat 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleMobileAssistantChat`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_mobile.py`

### P1-25: missing_relationship

**消息**: PresaleVisitRecord 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleVisitRecord`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_mobile.py`

### P1-26: missing_relationship

**消息**: PresaleVisitRecord 有外键 customer_id 指向 customers，但没有对应的 relationship

- **model**: `PresaleVisitRecord`
- **foreign_key**: `customer_id`
- **target_table**: `customers`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_mobile.py`

### P1-27: missing_relationship

**消息**: PresaleMobileQuickEstimate 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleMobileQuickEstimate`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_mobile.py`

### P1-28: missing_relationship

**消息**: PresaleMobileQuickEstimate 有外键 customer_id 指向 customers，但没有对应的 relationship

- **model**: `PresaleMobileQuickEstimate`
- **foreign_key**: `customer_id`
- **target_table**: `customers`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_mobile.py`

### P1-29: missing_relationship

**消息**: Vendor 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `Vendor`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/vendor.py`

### P1-30: missing_relationship

**消息**: ReportTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ReportTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-31: missing_relationship

**消息**: ReportDefinition 有外键 template_id 指向 report_template，但没有对应的 relationship

- **model**: `ReportDefinition`
- **foreign_key**: `template_id`
- **target_table**: `report_template`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-32: missing_relationship

**消息**: ReportDefinition 有外键 owner_id 指向 users，但没有对应的 relationship

- **model**: `ReportDefinition`
- **foreign_key**: `owner_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-33: missing_relationship

**消息**: ReportGeneration 有外键 report_definition_id 指向 report_definition，但没有对应的 relationship

- **model**: `ReportGeneration`
- **foreign_key**: `report_definition_id`
- **target_table**: `report_definition`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-34: missing_relationship

**消息**: ReportGeneration 有外键 template_id 指向 report_template，但没有对应的 relationship

- **model**: `ReportGeneration`
- **foreign_key**: `template_id`
- **target_table**: `report_template`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-35: missing_relationship

**消息**: ReportGeneration 有外键 generated_by 指向 users，但没有对应的 relationship

- **model**: `ReportGeneration`
- **foreign_key**: `generated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-36: missing_relationship

**消息**: ReportSubscription 有外键 subscriber_id 指向 users，但没有对应的 relationship

- **model**: `ReportSubscription`
- **foreign_key**: `subscriber_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-37: missing_relationship

**消息**: ReportSubscription 有外键 report_definition_id 指向 report_definition，但没有对应的 relationship

- **model**: `ReportSubscription`
- **foreign_key**: `report_definition_id`
- **target_table**: `report_definition`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-38: missing_relationship

**消息**: ReportSubscription 有外键 template_id 指向 report_template，但没有对应的 relationship

- **model**: `ReportSubscription`
- **foreign_key**: `template_id`
- **target_table**: `report_template`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-39: missing_relationship

**消息**: DataImportTask 有外键 imported_by 指向 users，但没有对应的 relationship

- **model**: `DataImportTask`
- **foreign_key**: `imported_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-40: missing_relationship

**消息**: DataExportTask 有外键 exported_by 指向 users，但没有对应的 relationship

- **model**: `DataExportTask`
- **foreign_key**: `exported_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report_center.py`

### P1-41: missing_relationship

**消息**: NewProductRequest 有外键 lead_id 指向 leads，但没有对应的 relationship

- **model**: `NewProductRequest`
- **foreign_key**: `lead_id`
- **target_table**: `leads`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/advantage_product.py`

### P1-42: missing_relationship

**消息**: HrTransaction 有外键 applicant_id 指向 users，但没有对应的 relationship

- **model**: `HrTransaction`
- **foreign_key**: `applicant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/organization.py`

### P1-43: missing_relationship

**消息**: HrTransaction 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `HrTransaction`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/organization.py`

### P1-44: missing_relationship

**消息**: ContractReminder 有外键 handled_by 指向 users，但没有对应的 relationship

- **model**: `ContractReminder`
- **foreign_key**: `handled_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/organization.py`

### P1-45: missing_relationship

**消息**: TechnicalReview 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-46: missing_relationship

**消息**: TechnicalReview 有外键 equipment_id 指向 machines，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `equipment_id`
- **target_table**: `machines`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-47: missing_relationship

**消息**: TechnicalReview 有外键 host_id 指向 users，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `host_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-48: missing_relationship

**消息**: TechnicalReview 有外键 presenter_id 指向 users，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `presenter_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-49: missing_relationship

**消息**: TechnicalReview 有外键 recorder_id 指向 users，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `recorder_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-50: missing_relationship

**消息**: TechnicalReview 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `TechnicalReview`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-51: missing_relationship

**消息**: ReviewParticipant 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `ReviewParticipant`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-52: missing_relationship

**消息**: ReviewParticipant 有外键 delegate_id 指向 users，但没有对应的 relationship

- **model**: `ReviewParticipant`
- **foreign_key**: `delegate_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-53: missing_relationship

**消息**: ReviewMaterial 有外键 upload_by 指向 users，但没有对应的 relationship

- **model**: `ReviewMaterial`
- **foreign_key**: `upload_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-54: missing_relationship

**消息**: ReviewChecklistRecord 有外键 checker_id 指向 users，但没有对应的 relationship

- **model**: `ReviewChecklistRecord`
- **foreign_key**: `checker_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-55: missing_relationship

**消息**: ReviewIssue 有外键 assignee_id 指向 users，但没有对应的 relationship

- **model**: `ReviewIssue`
- **foreign_key**: `assignee_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-56: missing_relationship

**消息**: ReviewIssue 有外键 verifier_id 指向 users，但没有对应的 relationship

- **model**: `ReviewIssue`
- **foreign_key**: `verifier_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/technical_review.py`

### P1-57: missing_relationship

**消息**: OutsourcingOrder 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingOrder`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-58: missing_relationship

**消息**: OutsourcingDelivery 有外键 received_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingDelivery`
- **foreign_key**: `received_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-59: missing_relationship

**消息**: OutsourcingDelivery 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingDelivery`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-60: missing_relationship

**消息**: OutsourcingInspection 有外键 inspector_id 指向 users，但没有对应的 relationship

- **model**: `OutsourcingInspection`
- **foreign_key**: `inspector_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-61: missing_relationship

**消息**: OutsourcingPayment 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingPayment`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-62: missing_relationship

**消息**: OutsourcingPayment 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingPayment`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-63: missing_relationship

**消息**: OutsourcingEvaluation 有外键 order_id 指向 outsourcing_orders，但没有对应的 relationship

- **model**: `OutsourcingEvaluation`
- **foreign_key**: `order_id`
- **target_table**: `outsourcing_orders`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-64: missing_relationship

**消息**: OutsourcingEvaluation 有外键 evaluator_id 指向 users，但没有对应的 relationship

- **model**: `OutsourcingEvaluation`
- **foreign_key**: `evaluator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-65: missing_relationship

**消息**: OutsourcingProgress 有外键 order_item_id 指向 outsourcing_order_items，但没有对应的 relationship

- **model**: `OutsourcingProgress`
- **foreign_key**: `order_item_id`
- **target_table**: `outsourcing_order_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-66: missing_relationship

**消息**: OutsourcingProgress 有外键 reported_by 指向 users，但没有对应的 relationship

- **model**: `OutsourcingProgress`
- **foreign_key**: `reported_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/outsourcing.py`

### P1-67: missing_relationship

**消息**: AcceptanceTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-68: missing_relationship

**消息**: AcceptanceOrder 有外键 qa_signer_id 指向 users，但没有对应的 relationship

- **model**: `AcceptanceOrder`
- **foreign_key**: `qa_signer_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-69: missing_relationship

**消息**: AcceptanceOrder 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceOrder`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-70: missing_relationship

**消息**: AcceptanceOrderItem 有外键 category_id 指向 template_categories，但没有对应的 relationship

- **model**: `AcceptanceOrderItem`
- **foreign_key**: `category_id`
- **target_table**: `template_categories`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-71: missing_relationship

**消息**: AcceptanceOrderItem 有外键 template_item_id 指向 template_check_items，但没有对应的 relationship

- **model**: `AcceptanceOrderItem`
- **foreign_key**: `template_item_id`
- **target_table**: `template_check_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-72: missing_relationship

**消息**: AcceptanceOrderItem 有外键 checked_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceOrderItem`
- **foreign_key**: `checked_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-73: missing_relationship

**消息**: AcceptanceIssue 有外键 order_item_id 指向 acceptance_order_items，但没有对应的 relationship

- **model**: `AcceptanceIssue`
- **foreign_key**: `order_item_id`
- **target_table**: `acceptance_order_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-74: missing_relationship

**消息**: AcceptanceIssue 有外键 found_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceIssue`
- **foreign_key**: `found_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-75: missing_relationship

**消息**: AcceptanceIssue 有外键 assigned_to 指向 users，但没有对应的 relationship

- **model**: `AcceptanceIssue`
- **foreign_key**: `assigned_to`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-76: missing_relationship

**消息**: AcceptanceIssue 有外键 resolved_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceIssue`
- **foreign_key**: `resolved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-77: missing_relationship

**消息**: AcceptanceIssue 有外键 verified_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceIssue`
- **foreign_key**: `verified_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-78: missing_relationship

**消息**: IssueFollowUp 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `IssueFollowUp`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-79: missing_relationship

**消息**: AcceptanceSignature 有外键 signer_user_id 指向 users，但没有对应的 relationship

- **model**: `AcceptanceSignature`
- **foreign_key**: `signer_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-80: missing_relationship

**消息**: AcceptanceReport 有外键 generated_by 指向 users，但没有对应的 relationship

- **model**: `AcceptanceReport`
- **foreign_key**: `generated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/acceptance.py`

### P1-81: missing_relationship

**消息**: ResourceConflictDetection 有外键 allocation_a_id 指向 pmo_resource_allocation，但没有对应的 relationship

- **model**: `ResourceConflictDetection`
- **foreign_key**: `allocation_a_id`
- **target_table**: `pmo_resource_allocation`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/resource_scheduling.py`

### P1-82: missing_relationship

**消息**: ResourceConflictDetection 有外键 allocation_b_id 指向 pmo_resource_allocation，但没有对应的 relationship

- **model**: `ResourceConflictDetection`
- **foreign_key**: `allocation_b_id`
- **target_table**: `pmo_resource_allocation`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/resource_scheduling.py`

### P1-83: missing_relationship

**消息**: PresaleSupportTicket 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PresaleSupportTicket`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-84: missing_relationship

**消息**: PresaleSupportTicket 有外键 applicant_id 指向 users，但没有对应的 relationship

- **model**: `PresaleSupportTicket`
- **foreign_key**: `applicant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-85: missing_relationship

**消息**: PresaleSupportTicket 有外键 assignee_id 指向 users，但没有对应的 relationship

- **model**: `PresaleSupportTicket`
- **foreign_key**: `assignee_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-86: missing_relationship

**消息**: PresaleSupportTicket 有外键 pm_user_id 指向 users，但没有对应的 relationship

- **model**: `PresaleSupportTicket`
- **foreign_key**: `pm_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-87: missing_relationship

**消息**: PresaleSupportTicket 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PresaleSupportTicket`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-88: missing_relationship

**消息**: PresaleTicketDeliverable 有外键 reviewer_id 指向 users，但没有对应的 relationship

- **model**: `PresaleTicketDeliverable`
- **foreign_key**: `reviewer_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-89: missing_relationship

**消息**: PresaleTicketDeliverable 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PresaleTicketDeliverable`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-90: missing_relationship

**消息**: PresaleTicketProgress 有外键 operator_id 指向 users，但没有对应的 relationship

- **model**: `PresaleTicketProgress`
- **foreign_key**: `operator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-91: missing_relationship

**消息**: PresaleSolution 有外键 ticket_id 指向 presale_support_ticket，但没有对应的 relationship

- **model**: `PresaleSolution`
- **foreign_key**: `ticket_id`
- **target_table**: `presale_support_ticket`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-92: missing_relationship

**消息**: PresaleSolution 有外键 reviewer_id 指向 users，但没有对应的 relationship

- **model**: `PresaleSolution`
- **foreign_key**: `reviewer_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-93: missing_relationship

**消息**: PresaleSolution 有外键 author_id 指向 users，但没有对应的 relationship

- **model**: `PresaleSolution`
- **foreign_key**: `author_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-94: missing_relationship

**消息**: PresaleSolutionTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PresaleSolutionTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-95: missing_relationship

**消息**: PresaleWorkload 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `PresaleWorkload`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-96: missing_relationship

**消息**: PresaleTenderRecord 有外键 ticket_id 指向 presale_support_ticket，但没有对应的 relationship

- **model**: `PresaleTenderRecord`
- **foreign_key**: `ticket_id`
- **target_table**: `presale_support_ticket`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-97: missing_relationship

**消息**: PresaleTenderRecord 有外键 leader_id 指向 users，但没有对应的 relationship

- **model**: `PresaleTenderRecord`
- **foreign_key**: `leader_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale.py`

### P1-98: missing_relationship

**消息**: ManagementRhythmConfig 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ManagementRhythmConfig`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-99: missing_relationship

**消息**: StrategicMeeting 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `StrategicMeeting`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-100: missing_relationship

**消息**: StrategicMeeting 有外键 rhythm_config_id 指向 management_rhythm_config，但没有对应的 relationship

- **model**: `StrategicMeeting`
- **foreign_key**: `rhythm_config_id`
- **target_table**: `management_rhythm_config`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-101: missing_relationship

**消息**: StrategicMeeting 有外键 organizer_id 指向 users，但没有对应的 relationship

- **model**: `StrategicMeeting`
- **foreign_key**: `organizer_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-102: missing_relationship

**消息**: StrategicMeeting 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `StrategicMeeting`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-103: missing_relationship

**消息**: MeetingActionItem 有外键 owner_id 指向 users，但没有对应的 relationship

- **model**: `MeetingActionItem`
- **foreign_key**: `owner_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-104: missing_relationship

**消息**: MeetingActionItem 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MeetingActionItem`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-105: missing_relationship

**消息**: RhythmDashboardSnapshot 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `RhythmDashboardSnapshot`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-106: missing_relationship

**消息**: MeetingReport 有外键 generated_by 指向 users，但没有对应的 relationship

- **model**: `MeetingReport`
- **foreign_key**: `generated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-107: missing_relationship

**消息**: MeetingReportConfig 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MeetingReportConfig`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-108: missing_relationship

**消息**: ReportMetricDefinition 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ReportMetricDefinition`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/management_rhythm.py`

### P1-109: missing_relationship

**消息**: PurchaseOrder 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `PurchaseOrder`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-110: missing_relationship

**消息**: PurchaseOrder 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PurchaseOrder`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-111: missing_relationship

**消息**: PurchaseOrderItem 有外键 bom_item_id 指向 bom_items，但没有对应的 relationship

- **model**: `PurchaseOrderItem`
- **foreign_key**: `bom_item_id`
- **target_table**: `bom_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-112: missing_relationship

**消息**: GoodsReceipt 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `GoodsReceipt`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-113: missing_relationship

**消息**: GoodsReceipt 有外键 inspected_by 指向 users，但没有对应的 relationship

- **model**: `GoodsReceipt`
- **foreign_key**: `inspected_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-114: missing_relationship

**消息**: GoodsReceipt 有外键 warehoused_by 指向 users，但没有对应的 relationship

- **model**: `GoodsReceipt`
- **foreign_key**: `warehoused_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-115: missing_relationship

**消息**: GoodsReceipt 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `GoodsReceipt`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-116: missing_relationship

**消息**: PurchaseRequest 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `PurchaseRequest`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/purchase.py`

### P1-117: missing_relationship

**消息**: ShortageDetail 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `ShortageDetail`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/assembly_kit.py`

### P1-118: missing_relationship

**消息**: PresaleAIEmotionAnalysis 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleAIEmotionAnalysis`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_ai_emotion_analysis.py`

### P1-119: missing_relationship

**消息**: PresaleAIRequirementAnalysis 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleAIRequirementAnalysis`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_ai_requirement_analysis.py`

### P1-120: missing_relationship

**消息**: CultureWallContent 有外键 related_project_id 指向 projects，但没有对应的 relationship

- **model**: `CultureWallContent`
- **foreign_key**: `related_project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-121: missing_relationship

**消息**: CultureWallContent 有外键 related_department_id 指向 departments，但没有对应的 relationship

- **model**: `CultureWallContent`
- **foreign_key**: `related_department_id`
- **target_table**: `departments`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-122: missing_relationship

**消息**: CultureWallContent 有外键 published_by 指向 users，但没有对应的 relationship

- **model**: `CultureWallContent`
- **foreign_key**: `published_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-123: missing_relationship

**消息**: CultureWallContent 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `CultureWallContent`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-124: missing_relationship

**消息**: PersonalGoal 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `PersonalGoal`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-125: missing_relationship

**消息**: PersonalGoal 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PersonalGoal`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-126: missing_relationship

**消息**: CultureWallReadRecord 有外键 content_id 指向 culture_wall_content，但没有对应的 relationship

- **model**: `CultureWallReadRecord`
- **foreign_key**: `content_id`
- **target_table**: `culture_wall_content`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-127: missing_relationship

**消息**: CultureWallReadRecord 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `CultureWallReadRecord`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/culture_wall.py`

### P1-128: missing_relationship

**消息**: TimesheetAnalytics 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetAnalytics`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-129: missing_relationship

**消息**: TimesheetAnalytics 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TimesheetAnalytics`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-130: missing_relationship

**消息**: TimesheetTrend 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetTrend`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-131: missing_relationship

**消息**: TimesheetTrend 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TimesheetTrend`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-132: missing_relationship

**消息**: TimesheetForecast 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TimesheetForecast`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-133: missing_relationship

**消息**: TimesheetForecast 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetForecast`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-134: missing_relationship

**消息**: TimesheetAnomaly 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetAnomaly`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-135: missing_relationship

**消息**: TimesheetAnomaly 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TimesheetAnomaly`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-136: missing_relationship

**消息**: TimesheetAnomaly 有外键 timesheet_id 指向 timesheet，但没有对应的 relationship

- **model**: `TimesheetAnomaly`
- **foreign_key**: `timesheet_id`
- **target_table**: `timesheet`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-137: missing_relationship

**消息**: TimesheetAnomaly 有外键 resolved_by 指向 users，但没有对应的 relationship

- **model**: `TimesheetAnomaly`
- **foreign_key**: `resolved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_analytics.py`

### P1-138: missing_relationship

**消息**: BonusCalculation 有外键 period_id 指向 performance_period，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `period_id`
- **target_table**: `performance_period`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-139: missing_relationship

**消息**: BonusCalculation 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-140: missing_relationship

**消息**: BonusCalculation 有外键 milestone_id 指向 project_milestones，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `milestone_id`
- **target_table**: `project_milestones`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-141: missing_relationship

**消息**: BonusCalculation 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-142: missing_relationship

**消息**: BonusCalculation 有外键 performance_result_id 指向 performance_result，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `performance_result_id`
- **target_table**: `performance_result`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-143: missing_relationship

**消息**: BonusCalculation 有外键 project_contribution_id 指向 project_contribution，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `project_contribution_id`
- **target_table**: `project_contribution`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-144: missing_relationship

**消息**: BonusCalculation 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `BonusCalculation`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-145: missing_relationship

**消息**: BonusDistribution 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `BonusDistribution`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-146: missing_relationship

**消息**: BonusDistribution 有外键 paid_by 指向 users，但没有对应的 relationship

- **model**: `BonusDistribution`
- **foreign_key**: `paid_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-147: missing_relationship

**消息**: TeamBonusAllocation 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TeamBonusAllocation`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-148: missing_relationship

**消息**: TeamBonusAllocation 有外键 period_id 指向 performance_period，但没有对应的 relationship

- **model**: `TeamBonusAllocation`
- **foreign_key**: `period_id`
- **target_table**: `performance_period`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-149: missing_relationship

**消息**: TeamBonusAllocation 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `TeamBonusAllocation`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/bonus.py`

### P1-150: missing_relationship

**消息**: TimesheetReminderConfig 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `TimesheetReminderConfig`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet_reminder.py`

### P1-151: missing_relationship

**消息**: PresaleFollowUpReminder 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleFollowUpReminder`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_follow_up_reminder.py`

### P1-152: missing_relationship

**消息**: MaterialTransaction 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `MaterialTransaction`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-153: missing_relationship

**消息**: MaterialStock 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `MaterialStock`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-154: missing_relationship

**消息**: MaterialReservation 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `MaterialReservation`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-155: missing_relationship

**消息**: StockAdjustment 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `StockAdjustment`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-156: missing_relationship

**消息**: StockCountTask 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `StockCountTask`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-157: missing_relationship

**消息**: StockCountTask 有外键 category_id 指向 material_categories，但没有对应的 relationship

- **model**: `StockCountTask`
- **foreign_key**: `category_id`
- **target_table**: `material_categories`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-158: missing_relationship

**消息**: StockCountDetail 有外键 tenant_id 指向 tenants，但没有对应的 relationship

- **model**: `StockCountDetail`
- **foreign_key**: `tenant_id`
- **target_table**: `tenants`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/inventory_tracking.py`

### P1-159: missing_relationship

**消息**: Timesheet 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `Timesheet`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-160: missing_relationship

**消息**: Timesheet 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `Timesheet`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-161: missing_relationship

**消息**: Timesheet 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `Timesheet`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-162: missing_relationship

**消息**: Timesheet 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `Timesheet`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-163: missing_relationship

**消息**: TimesheetBatch 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetBatch`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-164: missing_relationship

**消息**: TimesheetBatch 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetBatch`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-165: missing_relationship

**消息**: TimesheetSummary 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetSummary`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-166: missing_relationship

**消息**: TimesheetSummary 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `TimesheetSummary`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-167: missing_relationship

**消息**: OvertimeApplication 有外键 applicant_id 指向 users，但没有对应的 relationship

- **model**: `OvertimeApplication`
- **foreign_key**: `applicant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-168: missing_relationship

**消息**: OvertimeApplication 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `OvertimeApplication`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-169: missing_relationship

**消息**: OvertimeApplication 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `OvertimeApplication`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-170: missing_relationship

**消息**: TimesheetApprovalLog 有外键 timesheet_id 指向 timesheet，但没有对应的 relationship

- **model**: `TimesheetApprovalLog`
- **foreign_key**: `timesheet_id`
- **target_table**: `timesheet`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-171: missing_relationship

**消息**: TimesheetApprovalLog 有外键 batch_id 指向 timesheet_batch，但没有对应的 relationship

- **model**: `TimesheetApprovalLog`
- **foreign_key**: `batch_id`
- **target_table**: `timesheet_batch`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-172: missing_relationship

**消息**: TimesheetApprovalLog 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `TimesheetApprovalLog`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/timesheet.py`

### P1-173: missing_relationship

**消息**: TimesheetReportTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `TimesheetReportTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/report.py`

### P1-174: missing_relationship

**消息**: PresaleEmotionTrend 有外键 presale_ticket_id 指向 presale_tickets，但没有对应的 relationship

- **model**: `PresaleEmotionTrend`
- **foreign_key**: `presale_ticket_id`
- **target_table**: `presale_tickets`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/presale_emotion_trend.py`

### P1-175: missing_relationship

**消息**: AlertRule 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AlertRule`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-176: missing_relationship

**消息**: AlertRecord 有外键 acknowledged_by 指向 users，但没有对应的 relationship

- **model**: `AlertRecord`
- **foreign_key**: `acknowledged_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-177: missing_relationship

**消息**: AlertRecord 有外键 handler_id 指向 users，但没有对应的 relationship

- **model**: `AlertRecord`
- **foreign_key**: `handler_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-178: missing_relationship

**消息**: AlertRecord 有外键 escalated_to 指向 users，但没有对应的 relationship

- **model**: `AlertRecord`
- **foreign_key**: `escalated_to`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-179: missing_relationship

**消息**: AlertNotification 有外键 notify_user_id 指向 users，但没有对应的 relationship

- **model**: `AlertNotification`
- **foreign_key**: `notify_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-180: missing_relationship

**消息**: ExceptionEvent 有外键 discovered_by 指向 users，但没有对应的 relationship

- **model**: `ExceptionEvent`
- **foreign_key**: `discovered_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-181: missing_relationship

**消息**: ExceptionEvent 有外键 responsible_user_id 指向 users，但没有对应的 relationship

- **model**: `ExceptionEvent`
- **foreign_key**: `responsible_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-182: missing_relationship

**消息**: ExceptionEvent 有外键 resolved_by 指向 users，但没有对应的 relationship

- **model**: `ExceptionEvent`
- **foreign_key**: `resolved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-183: missing_relationship

**消息**: ExceptionEvent 有外键 verified_by 指向 users，但没有对应的 relationship

- **model**: `ExceptionEvent`
- **foreign_key**: `verified_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-184: missing_relationship

**消息**: ExceptionEvent 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ExceptionEvent`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-185: missing_relationship

**消息**: ExceptionAction 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ExceptionAction`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-186: missing_relationship

**消息**: ExceptionEscalation 有外键 escalated_from 指向 users，但没有对应的 relationship

- **model**: `ExceptionEscalation`
- **foreign_key**: `escalated_from`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-187: missing_relationship

**消息**: ExceptionEscalation 有外键 escalated_to 指向 users，但没有对应的 relationship

- **model**: `ExceptionEscalation`
- **foreign_key**: `escalated_to`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/alert.py`

### P1-188: missing_relationship

**消息**: MaterialArrival 有外键 purchase_order_id 指向 purchase_orders，但没有对应的 relationship

- **model**: `MaterialArrival`
- **foreign_key**: `purchase_order_id`
- **target_table**: `purchase_orders`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/arrivals.py`

### P1-189: missing_relationship

**消息**: MaterialArrival 有外键 purchase_order_item_id 指向 purchase_order_items，但没有对应的 relationship

- **model**: `MaterialArrival`
- **foreign_key**: `purchase_order_item_id`
- **target_table**: `purchase_order_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/arrivals.py`

### P1-190: missing_relationship

**消息**: MaterialArrival 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `MaterialArrival`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/arrivals.py`

### P1-191: missing_relationship

**消息**: MaterialArrival 有外键 received_by 指向 users，但没有对应的 relationship

- **model**: `MaterialArrival`
- **foreign_key**: `received_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/arrivals.py`

### P1-192: missing_relationship

**消息**: ArrivalFollowUp 有外键 followed_by 指向 users，但没有对应的 relationship

- **model**: `ArrivalFollowUp`
- **foreign_key**: `followed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/arrivals.py`

### P1-193: missing_relationship

**消息**: MaterialSubstitution 有外键 shortage_report_id 指向 shortage_reports，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `shortage_report_id`
- **target_table**: `shortage_reports`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-194: missing_relationship

**消息**: MaterialSubstitution 有外键 bom_item_id 指向 bom_items，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `bom_item_id`
- **target_table**: `bom_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-195: missing_relationship

**消息**: MaterialSubstitution 有外键 tech_approver_id 指向 users，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `tech_approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-196: missing_relationship

**消息**: MaterialSubstitution 有外键 prod_approver_id 指向 users，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `prod_approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-197: missing_relationship

**消息**: MaterialSubstitution 有外键 executed_by 指向 users，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `executed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-198: missing_relationship

**消息**: MaterialSubstitution 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MaterialSubstitution`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-199: missing_relationship

**消息**: MaterialTransfer 有外键 shortage_report_id 指向 shortage_reports，但没有对应的 relationship

- **model**: `MaterialTransfer`
- **foreign_key**: `shortage_report_id`
- **target_table**: `shortage_reports`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-200: missing_relationship

**消息**: MaterialTransfer 有外键 approver_id 指向 users，但没有对应的 relationship

- **model**: `MaterialTransfer`
- **foreign_key**: `approver_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-201: missing_relationship

**消息**: MaterialTransfer 有外键 executed_by 指向 users，但没有对应的 relationship

- **model**: `MaterialTransfer`
- **foreign_key**: `executed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-202: missing_relationship

**消息**: MaterialTransfer 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MaterialTransfer`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/handling.py`

### P1-203: missing_relationship

**消息**: ShortageAlert 有外键 work_order_id 指向 production_work_orders，但没有对应的 relationship

- **model**: `ShortageAlert`
- **foreign_key**: `work_order_id`
- **target_table**: `production_work_orders`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/smart_alert.py`

### P1-204: missing_relationship

**消息**: ShortageHandlingPlan 有外键 target_supplier_id 指向 suppliers，但没有对应的 relationship

- **model**: `ShortageHandlingPlan`
- **foreign_key**: `target_supplier_id`
- **target_table**: `suppliers`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/smart_alert.py`

### P1-205: missing_relationship

**消息**: ShortageHandlingPlan 有外键 target_project_id 指向 projects，但没有对应的 relationship

- **model**: `ShortageHandlingPlan`
- **foreign_key**: `target_project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/smart_alert.py`

### P1-206: missing_relationship

**消息**: ShortageReport 有外键 work_order_id 指向 work_order，但没有对应的 relationship

- **model**: `ShortageReport`
- **foreign_key**: `work_order_id`
- **target_table**: `work_order`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/reports.py`

### P1-207: missing_relationship

**消息**: ShortageReport 有外键 reporter_id 指向 users，但没有对应的 relationship

- **model**: `ShortageReport`
- **foreign_key**: `reporter_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/reports.py`

### P1-208: missing_relationship

**消息**: ShortageReport 有外键 confirmed_by 指向 users，但没有对应的 relationship

- **model**: `ShortageReport`
- **foreign_key**: `confirmed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/reports.py`

### P1-209: missing_relationship

**消息**: ShortageReport 有外键 handler_id 指向 users，但没有对应的 relationship

- **model**: `ShortageReport`
- **foreign_key**: `handler_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/shortage/reports.py`

### P1-210: missing_relationship

**消息**: EngineerDimensionConfig 有外键 operator_id 指向 users，但没有对应的 relationship

- **model**: `EngineerDimensionConfig`
- **foreign_key**: `operator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/engineer_performance/common.py`

### P1-211: missing_relationship

**消息**: CollaborationRating 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `CollaborationRating`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/engineer_performance/common.py`

### P1-212: missing_relationship

**消息**: KnowledgeReuseLog 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `KnowledgeReuseLog`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/engineer_performance/common.py`

### P1-213: missing_relationship

**消息**: Invoice 有外键 payment_id 指向 project_payment_plans，但没有对应的 relationship

- **model**: `Invoice`
- **foreign_key**: `payment_id`
- **target_table**: `project_payment_plans`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/invoices.py`

### P1-214: missing_relationship

**消息**: ReceivableDispute 有外键 payment_id 指向 project_payment_plans，但没有对应的 relationship

- **model**: `ReceivableDispute`
- **foreign_key**: `payment_id`
- **target_table**: `project_payment_plans`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/invoices.py`

### P1-215: missing_relationship

**消息**: PurchaseMaterialCost 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `PurchaseMaterialCost`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/quotes.py`

### P1-216: missing_relationship

**消息**: SalesRankingConfig 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `SalesRankingConfig`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/workflow.py`

### P1-217: missing_relationship

**消息**: SalesRankingConfig 有外键 updated_by 指向 users，但没有对应的 relationship

- **model**: `SalesRankingConfig`
- **foreign_key**: `updated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/sales/workflow.py`

### P1-218: missing_relationship

**消息**: EcnLog 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `EcnLog`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ecn/log.py`

### P1-219: missing_relationship

**消息**: EcnAffectedMaterial 有外键 bom_item_id 指向 bom_items，但没有对应的 relationship

- **model**: `EcnAffectedMaterial`
- **foreign_key**: `bom_item_id`
- **target_table**: `bom_items`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ecn/impact.py`

### P1-220: missing_relationship

**消息**: EcnAffectedMaterial 有外键 old_supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `EcnAffectedMaterial`
- **foreign_key**: `old_supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ecn/impact.py`

### P1-221: missing_relationship

**消息**: EcnAffectedMaterial 有外键 new_supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `EcnAffectedMaterial`
- **foreign_key**: `new_supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ecn/impact.py`

### P1-222: missing_relationship

**消息**: EcnAffectedOrder 有外键 processed_by 指向 users，但没有对应的 relationship

- **model**: `EcnAffectedOrder`
- **foreign_key**: `processed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ecn/impact.py`

### P1-223: missing_relationship

**消息**: PmoProjectCost 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoProjectCost`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/cost_meeting.py`

### P1-224: missing_relationship

**消息**: PmoProjectCost 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PmoProjectCost`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/cost_meeting.py`

### P1-225: missing_relationship

**消息**: PmoMeeting 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoMeeting`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/cost_meeting.py`

### P1-226: missing_relationship

**消息**: PmoMeeting 有外键 organizer_id 指向 users，但没有对应的 relationship

- **model**: `PmoMeeting`
- **foreign_key**: `organizer_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/cost_meeting.py`

### P1-227: missing_relationship

**消息**: PmoMeeting 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `PmoMeeting`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/cost_meeting.py`

### P1-228: missing_relationship

**消息**: PmoProjectInitiation 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoProjectInitiation`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/initiation_phase.py`

### P1-229: missing_relationship

**消息**: PmoProjectInitiation 有外键 applicant_id 指向 users，但没有对应的 relationship

- **model**: `PmoProjectInitiation`
- **foreign_key**: `applicant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/initiation_phase.py`

### P1-230: missing_relationship

**消息**: PmoProjectInitiation 有外键 approved_pm_id 指向 users，但没有对应的 relationship

- **model**: `PmoProjectInitiation`
- **foreign_key**: `approved_pm_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/initiation_phase.py`

### P1-231: missing_relationship

**消息**: PmoProjectInitiation 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `PmoProjectInitiation`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/initiation_phase.py`

### P1-232: missing_relationship

**消息**: PmoProjectPhase 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoProjectPhase`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/initiation_phase.py`

### P1-233: missing_relationship

**消息**: PmoResourceAllocation 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoResourceAllocation`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/resource_closure.py`

### P1-234: missing_relationship

**消息**: PmoResourceAllocation 有外键 resource_id 指向 users，但没有对应的 relationship

- **model**: `PmoResourceAllocation`
- **foreign_key**: `resource_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/resource_closure.py`

### P1-235: missing_relationship

**消息**: PmoProjectClosure 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoProjectClosure`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/resource_closure.py`

### P1-236: missing_relationship

**消息**: PmoProjectClosure 有外键 reviewed_by 指向 users，但没有对应的 relationship

- **model**: `PmoProjectClosure`
- **foreign_key**: `reviewed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/resource_closure.py`

### P1-237: missing_relationship

**消息**: PmoChangeRequest 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoChangeRequest`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/change_risk.py`

### P1-238: missing_relationship

**消息**: PmoChangeRequest 有外键 requestor_id 指向 users，但没有对应的 relationship

- **model**: `PmoChangeRequest`
- **foreign_key**: `requestor_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/change_risk.py`

### P1-239: missing_relationship

**消息**: PmoProjectRisk 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `PmoProjectRisk`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/change_risk.py`

### P1-240: missing_relationship

**消息**: PmoProjectRisk 有外键 owner_id 指向 users，但没有对应的 relationship

- **model**: `PmoProjectRisk`
- **foreign_key**: `owner_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/pmo/change_risk.py`

### P1-241: missing_relationship

**消息**: Project 有外键 approval_record_id 指向 approval_records，但没有对应的 relationship

- **model**: `Project`
- **foreign_key**: `approval_record_id`
- **target_table**: `approval_records`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/core.py`

### P1-242: missing_relationship

**消息**: Project 有外键 dept_id 指向 departments，但没有对应的 relationship

- **model**: `Project`
- **foreign_key**: `dept_id`
- **target_table**: `departments`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/core.py`

### P1-243: missing_relationship

**消息**: Project 有外键 template_id 指向 project_templates，但没有对应的 relationship

- **model**: `Project`
- **foreign_key**: `template_id`
- **target_table**: `project_templates`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/core.py`

### P1-244: missing_relationship

**消息**: Project 有外键 template_version_id 指向 project_template_versions，但没有对应的 relationship

- **model**: `Project`
- **foreign_key**: `template_version_id`
- **target_table**: `project_template_versions`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/core.py`

### P1-245: missing_relationship

**消息**: ProjectMilestone 有外键 machine_id 指向 machines，但没有对应的 relationship

- **model**: `ProjectMilestone`
- **foreign_key**: `machine_id`
- **target_table**: `machines`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/financial.py`

### P1-246: missing_relationship

**消息**: ProjectMilestone 有外键 owner_id 指向 users，但没有对应的 relationship

- **model**: `ProjectMilestone`
- **foreign_key**: `owner_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/financial.py`

### P1-247: missing_relationship

**消息**: ProjectCost 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ProjectCost`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/financial.py`

### P1-248: missing_relationship

**消息**: ProjectDocument 有外键 rd_project_id 指向 rd_project，但没有对应的 relationship

- **model**: `ProjectDocument`
- **foreign_key**: `rd_project_id`
- **target_table**: `rd_project`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/document.py`

### P1-249: missing_relationship

**消息**: ProjectDocument 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `ProjectDocument`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/document.py`

### P1-250: missing_relationship

**消息**: ProjectDocument 有外键 uploaded_by 指向 users，但没有对应的 relationship

- **model**: `ProjectDocument`
- **foreign_key**: `uploaded_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/document.py`

### P1-251: missing_relationship

**消息**: ProjectTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ProjectTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/project/document.py`

### P1-252: missing_relationship

**消息**: Equipment 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `Equipment`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/equipment.py`

### P1-253: missing_relationship

**消息**: Worker 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `Worker`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/worker.py`

### P1-254: missing_relationship

**消息**: QualityInspection 有外键 work_order_id 指向 work_order，但没有对应的 relationship

- **model**: `QualityInspection`
- **foreign_key**: `work_order_id`
- **target_table**: `work_order`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-255: missing_relationship

**消息**: QualityInspection 有外键 material_id 指向 materials，但没有对应的 relationship

- **model**: `QualityInspection`
- **foreign_key**: `material_id`
- **target_table**: `materials`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-256: missing_relationship

**消息**: DefectAnalysis 有外键 inspection_id 指向 quality_inspection，但没有对应的 relationship

- **model**: `DefectAnalysis`
- **foreign_key**: `inspection_id`
- **target_table**: `quality_inspection`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-257: missing_relationship

**消息**: DefectAnalysis 有外键 related_equipment_id 指向 equipment，但没有对应的 relationship

- **model**: `DefectAnalysis`
- **foreign_key**: `related_equipment_id`
- **target_table**: `equipment`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-258: missing_relationship

**消息**: DefectAnalysis 有外键 related_worker_id 指向 worker，但没有对应的 relationship

- **model**: `DefectAnalysis`
- **foreign_key**: `related_worker_id`
- **target_table**: `worker`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-259: missing_relationship

**消息**: DefectAnalysis 有外键 related_material_id 指向 materials，但没有对应的 relationship

- **model**: `DefectAnalysis`
- **foreign_key**: `related_material_id`
- **target_table**: `materials`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-260: missing_relationship

**消息**: QualityAlertRule 有外键 target_material_id 指向 materials，但没有对应的 relationship

- **model**: `QualityAlertRule`
- **foreign_key**: `target_material_id`
- **target_table**: `materials`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-261: missing_relationship

**消息**: QualityAlertRule 有外键 target_process_id 指向 process_dict，但没有对应的 relationship

- **model**: `QualityAlertRule`
- **foreign_key**: `target_process_id`
- **target_table**: `process_dict`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-262: missing_relationship

**消息**: QualityAlertRule 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `QualityAlertRule`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-263: missing_relationship

**消息**: ReworkOrder 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `ReworkOrder`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-264: missing_relationship

**消息**: ReworkOrder 有外键 workstation_id 指向 workstation，但没有对应的 relationship

- **model**: `ReworkOrder`
- **foreign_key**: `workstation_id`
- **target_table**: `workstation`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-265: missing_relationship

**消息**: ReworkOrder 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ReworkOrder`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/quality_inspection.py`

### P1-266: missing_relationship

**消息**: WorkReport 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `WorkReport`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_report.py`

### P1-267: missing_relationship

**消息**: MaterialRequisition 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `MaterialRequisition`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-268: missing_relationship

**消息**: MaterialRequisition 有外键 applicant_id 指向 users，但没有对应的 relationship

- **model**: `MaterialRequisition`
- **foreign_key**: `applicant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-269: missing_relationship

**消息**: MaterialRequisition 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `MaterialRequisition`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-270: missing_relationship

**消息**: MaterialRequisition 有外键 issued_by 指向 users，但没有对应的 relationship

- **model**: `MaterialRequisition`
- **foreign_key**: `issued_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-271: missing_relationship

**消息**: MaterialRequisitionItem 有外键 material_id 指向 materials，但没有对应的 relationship

- **model**: `MaterialRequisitionItem`
- **foreign_key**: `material_id`
- **target_table**: `materials`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-272: missing_relationship

**消息**: ProductionDailyReport 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `ProductionDailyReport`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-273: missing_relationship

**消息**: ProductionDailyReport 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ProductionDailyReport`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material.py`

### P1-274: missing_relationship

**消息**: WorkerEfficiencyRecord 有外键 calculated_by 指向 users，但没有对应的 relationship

- **model**: `WorkerEfficiencyRecord`
- **foreign_key**: `calculated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/worker_efficiency_record.py`

### P1-275: missing_relationship

**消息**: WorkerEfficiencyRecord 有外键 confirmed_by 指向 users，但没有对应的 relationship

- **model**: `WorkerEfficiencyRecord`
- **foreign_key**: `confirmed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/worker_efficiency_record.py`

### P1-276: missing_relationship

**消息**: ProductionPlan 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `ProductionPlan`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_plan.py`

### P1-277: missing_relationship

**消息**: ProductionPlan 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `ProductionPlan`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_plan.py`

### P1-278: missing_relationship

**消息**: ProductionPlan 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ProductionPlan`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_plan.py`

### P1-279: missing_relationship

**消息**: ProductionPlan 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `ProductionPlan`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_plan.py`

### P1-280: missing_relationship

**消息**: Workshop 有外键 manager_id 指向 users，但没有对应的 relationship

- **model**: `Workshop`
- **foreign_key**: `manager_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/workshop.py`

### P1-281: missing_relationship

**消息**: Workstation 有外键 current_worker_id 指向 worker，但没有对应的 relationship

- **model**: `Workstation`
- **foreign_key**: `current_worker_id`
- **target_table**: `worker`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/workshop.py`

### P1-282: missing_relationship

**消息**: Workstation 有外键 current_work_order_id 指向 work_order，但没有对应的 relationship

- **model**: `Workstation`
- **foreign_key**: `current_work_order_id`
- **target_table**: `work_order`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/workshop.py`

### P1-283: missing_relationship

**消息**: MaterialBatch 有外键 supplier_id 指向 vendors，但没有对应的 relationship

- **model**: `MaterialBatch`
- **foreign_key**: `supplier_id`
- **target_table**: `vendors`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-284: missing_relationship

**消息**: MaterialBatch 有外键 quality_inspector_id 指向 users，但没有对应的 relationship

- **model**: `MaterialBatch`
- **foreign_key**: `quality_inspector_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-285: missing_relationship

**消息**: MaterialBatch 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MaterialBatch`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-286: missing_relationship

**消息**: MaterialConsumption 有外键 requisition_id 指向 material_requisition，但没有对应的 relationship

- **model**: `MaterialConsumption`
- **foreign_key**: `requisition_id`
- **target_table**: `material_requisition`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-287: missing_relationship

**消息**: MaterialConsumption 有外键 operator_id 指向 users，但没有对应的 relationship

- **model**: `MaterialConsumption`
- **foreign_key**: `operator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-288: missing_relationship

**消息**: MaterialConsumption 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `MaterialConsumption`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-289: missing_relationship

**消息**: MaterialAlert 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `MaterialAlert`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-290: missing_relationship

**消息**: MaterialAlertRule 有外键 category_id 指向 material_categories，但没有对应的 relationship

- **model**: `MaterialAlertRule`
- **foreign_key**: `category_id`
- **target_table**: `material_categories`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-291: missing_relationship

**消息**: MaterialAlertRule 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `MaterialAlertRule`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/material_tracking.py`

### P1-292: missing_relationship

**消息**: EquipmentOEERecord 有外键 calculated_by 指向 users，但没有对应的 relationship

- **model**: `EquipmentOEERecord`
- **foreign_key**: `calculated_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/equipment_oee_record.py`

### P1-293: missing_relationship

**消息**: WorkOrder 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-294: missing_relationship

**消息**: WorkOrder 有外键 machine_id 指向 machines，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `machine_id`
- **target_table**: `machines`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-295: missing_relationship

**消息**: WorkOrder 有外键 workstation_id 指向 workstation，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `workstation_id`
- **target_table**: `workstation`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-296: missing_relationship

**消息**: WorkOrder 有外键 material_id 指向 materials，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `material_id`
- **target_table**: `materials`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-297: missing_relationship

**消息**: WorkOrder 有外键 assigned_by 指向 users，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `assigned_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-298: missing_relationship

**消息**: WorkOrder 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `WorkOrder`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/work_order.py`

### P1-299: missing_relationship

**消息**: ProductionException 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `ProductionException`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_exception.py`

### P1-300: missing_relationship

**消息**: ProductionException 有外键 workshop_id 指向 workshop，但没有对应的 relationship

- **model**: `ProductionException`
- **foreign_key**: `workshop_id`
- **target_table**: `workshop`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_exception.py`

### P1-301: missing_relationship

**消息**: ProductionException 有外键 equipment_id 指向 equipment，但没有对应的 relationship

- **model**: `ProductionException`
- **foreign_key**: `equipment_id`
- **target_table**: `equipment`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_exception.py`

### P1-302: missing_relationship

**消息**: ProductionException 有外键 reporter_id 指向 users，但没有对应的 relationship

- **model**: `ProductionException`
- **foreign_key**: `reporter_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_exception.py`

### P1-303: missing_relationship

**消息**: ProductionException 有外键 handler_id 指向 users，但没有对应的 relationship

- **model**: `ProductionException`
- **foreign_key**: `handler_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_exception.py`

### P1-304: missing_relationship

**消息**: ProductionSchedule 有外键 process_id 指向 process_dict，但没有对应的 relationship

- **model**: `ProductionSchedule`
- **foreign_key**: `process_id`
- **target_table**: `process_dict`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-305: missing_relationship

**消息**: ProductionSchedule 有外键 adjusted_by 指向 users，但没有对应的 relationship

- **model**: `ProductionSchedule`
- **foreign_key**: `adjusted_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-306: missing_relationship

**消息**: ProductionSchedule 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ProductionSchedule`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-307: missing_relationship

**消息**: ProductionSchedule 有外键 confirmed_by 指向 users，但没有对应的 relationship

- **model**: `ProductionSchedule`
- **foreign_key**: `confirmed_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-308: missing_relationship

**消息**: ProductionResourceConflict 有外键 resolved_by 指向 users，但没有对应的 relationship

- **model**: `ProductionResourceConflict`
- **foreign_key**: `resolved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-309: missing_relationship

**消息**: ScheduleAdjustmentLog 有外键 adjusted_by 指向 users，但没有对应的 relationship

- **model**: `ScheduleAdjustmentLog`
- **foreign_key**: `adjusted_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-310: missing_relationship

**消息**: ScheduleAdjustmentLog 有外键 approved_by 指向 users，但没有对应的 relationship

- **model**: `ScheduleAdjustmentLog`
- **foreign_key**: `approved_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/production/production_schedule.py`

### P1-311: missing_relationship

**消息**: PerformanceResult 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `PerformanceResult`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/result_evaluation.py`

### P1-312: missing_relationship

**消息**: PerformanceResult 有外键 adjusted_by 指向 users，但没有对应的 relationship

- **model**: `PerformanceResult`
- **foreign_key**: `adjusted_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/result_evaluation.py`

### P1-313: missing_relationship

**消息**: PerformanceEvaluation 有外键 evaluator_id 指向 users，但没有对应的 relationship

- **model**: `PerformanceEvaluation`
- **foreign_key**: `evaluator_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/result_evaluation.py`

### P1-314: missing_relationship

**消息**: PerformanceAppeal 有外键 result_id 指向 performance_result，但没有对应的 relationship

- **model**: `PerformanceAppeal`
- **foreign_key**: `result_id`
- **target_table**: `performance_result`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/appeal_adjustment.py`

### P1-315: missing_relationship

**消息**: PerformanceAppeal 有外键 appellant_id 指向 users，但没有对应的 relationship

- **model**: `PerformanceAppeal`
- **foreign_key**: `appellant_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/appeal_adjustment.py`

### P1-316: missing_relationship

**消息**: PerformanceAppeal 有外键 handler_id 指向 users，但没有对应的 relationship

- **model**: `PerformanceAppeal`
- **foreign_key**: `handler_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/appeal_adjustment.py`

### P1-317: missing_relationship

**消息**: ProjectContribution 有外键 period_id 指向 performance_period，但没有对应的 relationship

- **model**: `ProjectContribution`
- **foreign_key**: `period_id`
- **target_table**: `performance_period`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/contribution_ranking.py`

### P1-318: missing_relationship

**消息**: ProjectContribution 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `ProjectContribution`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/contribution_ranking.py`

### P1-319: missing_relationship

**消息**: ProjectContribution 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `ProjectContribution`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/contribution_ranking.py`

### P1-320: missing_relationship

**消息**: PerformanceRankingSnapshot 有外键 period_id 指向 performance_period，但没有对应的 relationship

- **model**: `PerformanceRankingSnapshot`
- **foreign_key**: `period_id`
- **target_table**: `performance_period`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/performance/contribution_ranking.py`

### P1-321: missing_relationship

**消息**: AIResourceAllocation 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-322: missing_relationship

**消息**: AIResourceAllocation 有外键 wbs_suggestion_id 指向 ai_wbs_suggestions，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `wbs_suggestion_id`
- **target_table**: `ai_wbs_suggestions`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-323: missing_relationship

**消息**: AIResourceAllocation 有外键 task_id 指向 task_unified，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `task_id`
- **target_table**: `task_unified`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-324: missing_relationship

**消息**: AIResourceAllocation 有外键 user_id 指向 users，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-325: missing_relationship

**消息**: AIResourceAllocation 有外键 actual_user_id 指向 users，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `actual_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-326: missing_relationship

**消息**: AIResourceAllocation 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AIResourceAllocation`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/resource_allocation.py`

### P1-327: missing_relationship

**消息**: AIWbsSuggestion 有外键 project_id 指向 projects，但没有对应的 relationship

- **model**: `AIWbsSuggestion`
- **foreign_key**: `project_id`
- **target_table**: `projects`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/wbs_suggestion.py`

### P1-328: missing_relationship

**消息**: AIWbsSuggestion 有外键 template_id 指向 ai_project_plan_templates，但没有对应的 relationship

- **model**: `AIWbsSuggestion`
- **foreign_key**: `template_id`
- **target_table**: `ai_project_plan_templates`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/wbs_suggestion.py`

### P1-329: missing_relationship

**消息**: AIWbsSuggestion 有外键 parent_wbs_id 指向 ai_wbs_suggestions，但没有对应的 relationship

- **model**: `AIWbsSuggestion`
- **foreign_key**: `parent_wbs_id`
- **target_table**: `ai_wbs_suggestions`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/wbs_suggestion.py`

### P1-330: missing_relationship

**消息**: AIWbsSuggestion 有外键 actual_task_id 指向 task_unified，但没有对应的 relationship

- **model**: `AIWbsSuggestion`
- **foreign_key**: `actual_task_id`
- **target_table**: `task_unified`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/wbs_suggestion.py`

### P1-331: missing_relationship

**消息**: AIWbsSuggestion 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AIWbsSuggestion`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/wbs_suggestion.py`

### P1-332: missing_relationship

**消息**: AIProjectPlanTemplate 有外键 verified_by 指向 users，但没有对应的 relationship

- **model**: `AIProjectPlanTemplate`
- **foreign_key**: `verified_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/plan_template.py`

### P1-333: missing_relationship

**消息**: AIProjectPlanTemplate 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `AIProjectPlanTemplate`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/ai_planning/plan_template.py`

### P1-334: missing_relationship

**消息**: ApprovalCountersignResult 有外键 instance_id 指向 approval_instances，但没有对应的 relationship

- **model**: `ApprovalCountersignResult`
- **foreign_key**: `instance_id`
- **target_table**: `approval_instances`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/task.py`

### P1-335: missing_relationship

**消息**: ApprovalCountersignResult 有外键 node_id 指向 approval_node_definitions，但没有对应的 relationship

- **model**: `ApprovalCountersignResult`
- **foreign_key**: `node_id`
- **target_table**: `approval_node_definitions`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/task.py`

### P1-336: missing_relationship

**消息**: ApprovalActionLog 有外键 task_id 指向 approval_tasks，但没有对应的 relationship

- **model**: `ApprovalActionLog`
- **foreign_key**: `task_id`
- **target_table**: `approval_tasks`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/log.py`

### P1-337: missing_relationship

**消息**: ApprovalActionLog 有外键 node_id 指向 approval_node_definitions，但没有对应的 relationship

- **model**: `ApprovalActionLog`
- **foreign_key**: `node_id`
- **target_table**: `approval_node_definitions`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/log.py`

### P1-338: missing_relationship

**消息**: ApprovalComment 有外键 instance_id 指向 approval_instances，但没有对应的 relationship

- **model**: `ApprovalComment`
- **foreign_key**: `instance_id`
- **target_table**: `approval_instances`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/log.py`

### P1-339: missing_relationship

**消息**: ApprovalFlowDefinition 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ApprovalFlowDefinition`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/flow.py`

### P1-340: missing_relationship

**消息**: ApprovalRoutingRule 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ApprovalRoutingRule`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/flow.py`

### P1-341: missing_relationship

**消息**: ApprovalDelegateLog 有外键 delegate_config_id 指向 approval_delegates，但没有对应的 relationship

- **model**: `ApprovalDelegateLog`
- **foreign_key**: `delegate_config_id`
- **target_table**: `approval_delegates`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/delegate.py`

### P1-342: missing_relationship

**消息**: ApprovalDelegateLog 有外键 task_id 指向 approval_tasks，但没有对应的 relationship

- **model**: `ApprovalDelegateLog`
- **foreign_key**: `task_id`
- **target_table**: `approval_tasks`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/delegate.py`

### P1-343: missing_relationship

**消息**: ApprovalDelegateLog 有外键 instance_id 指向 approval_instances，但没有对应的 relationship

- **model**: `ApprovalDelegateLog`
- **foreign_key**: `instance_id`
- **target_table**: `approval_instances`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/delegate.py`

### P1-344: missing_relationship

**消息**: ApprovalDelegateLog 有外键 original_user_id 指向 users，但没有对应的 relationship

- **model**: `ApprovalDelegateLog`
- **foreign_key**: `original_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/delegate.py`

### P1-345: missing_relationship

**消息**: ApprovalDelegateLog 有外键 delegate_user_id 指向 users，但没有对应的 relationship

- **model**: `ApprovalDelegateLog`
- **foreign_key**: `delegate_user_id`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/delegate.py`

### P1-346: missing_relationship

**消息**: ApprovalTemplateVersion 有外键 template_id 指向 approval_templates，但没有对应的 relationship

- **model**: `ApprovalTemplateVersion`
- **foreign_key**: `template_id`
- **target_table**: `approval_templates`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/template.py`

### P1-347: missing_relationship

**消息**: ApprovalTemplateVersion 有外键 created_by 指向 users，但没有对应的 relationship

- **model**: `ApprovalTemplateVersion`
- **foreign_key**: `created_by`
- **target_table**: `users`
- **file**: `/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/app/models/approval/template.py`

