#!/usr/bin/env python
"""批量导入服务模块批次3"""
import sys
import importlib

sys.path.insert(0, '.')

modules = [
    'app.services.report_excel_service',
    'app.services.resource_plan_service',
    'app.services.resource_scheduling',
    'app.services.resource_scheduling_ai_service',
    'app.services.resource_waste_analysis',
    'app.services.resource_waste_analysis.core',
    'app.services.role_management',
    'app.services.role_service',
    'app.services.sales_ai_assistant_service',
    'app.services.sales_forecast_service',
    'app.services.sales_prediction_service',
    'app.services.sales_ranking_service',
    'app.services.sales_target_service',
    'app.services.sales_team_service',
    'app.services.schedule_generation_service',
    'app.services.schedule_optimization_service',
    'app.services.schedule_prediction_service',
    'app.services.scheduling_suggestion_service',
    'app.services.session_service',
    'app.services.shortage_alerts',
    'app.services.shortage_analytics',
    'app.services.shortage_report_service',
    'app.services.sla_service',
    'app.services.solution_credit_service',
    'app.services.spec_match_service',
    'app.services.staff_matching',
    'app.services.stage_advance_service',
    'app.services.stage_instance',
    'app.services.stage_instance.core',
    'app.services.stage_template',
    'app.services.stage_template.core',
    'app.services.stock_count_service',
    'app.services.task_progress_service',
    'app.services.team_generation_service',
    'app.services.team_performance',
    'app.services.technical_assessment_service',
    'app.services.template_recommendation_service',
    'app.services.template_report_data_service',
    'app.services.template_report_service',
    'app.services.tenant_service',
    'app.services.ticket_assignment_service',
    'app.services.timesheet',
    'app.services.timesheet.timesheet_service',
    'app.services.timesheet.overtime_calculation_service',
    'app.services.timesheet.records',
    'app.services.timesheet.reminder',
    'app.services.timesheet.reminders',
    'app.services.unified_import',
    'app.services.user_import_service',
    'app.services.user_sync_service',
    'app.services.vendor_service',
    'app.services.views',
    'app.services.work_log_auto_generator',
    'app.services.work_log_service',
]

for mod in modules:
    try:
        importlib.import_module(mod)
    except Exception:
        pass

print('Batch 3 done')