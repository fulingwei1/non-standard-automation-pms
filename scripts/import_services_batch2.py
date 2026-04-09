#!/usr/bin/env python
"""批量导入服务模块批次2"""
import sys
import importlib

sys.path.insert(0, '.')

modules = [
    'app.services.data_scope',
    'app.services.data_scope.data_scope_service',
    'app.services.debug_issue_sync_service',
    'app.services.delivery_validation_service',
    'app.services.design_review_sync_service',
    'app.services.docx_content_builders',
    'app.services.ecn',
    'app.services.ecn.ecn_cost_impact_service',
    'app.services.ecn_cost_impact_service',
    'app.services.employee_import_service',
    'app.services.file_upload_service',
    'app.services.issue_statistics_service',
    'app.services.kitting_optimization_service',
    'app.services.knowledge_auto_identification_service',
    'app.services.knowledge_extraction_service',
    'app.services.lead_priority_scoring',
    'app.services.lead_priority_scoring.service',
    'app.services.material_service',
    'app.services.material_transfer_service',
    'app.services.milestone_service',
    'app.services.notification_service',
    'app.services.performance_service',
    'app.services.project.project_service',
    'app.services.project_contribution_service',
    'app.services.project_import_service',
    'app.services.project_meeting_service',
    'app.services.project_members',
    'app.services.project_relation_service',
    'app.services.project_risk',
    'app.services.project_solution_service',
    'app.services.project_statistics_service',
    'app.services.project_workspace_service',
    'app.services.purchase_intelligence',
    'app.services.purchase_order_from_bom_service',
    'app.services.purchase_request_from_bom_service',
    'app.services.purchase_suggestion_engine',
    'app.services.purchase_workflow',
    'app.services.quotation_pdf_service',
    'app.services.quote_approval',
    'app.services.rd_report_data_service',
    'app.services.relationship_scoring_service',
    'app.services.report',
    'app.services.report.report_service',
]

for mod in modules:
    try:
        importlib.import_module(mod)
    except Exception as e:
        print(f'FAIL: {mod} - {str(e)[:50]}')

print('Batch 2 done')