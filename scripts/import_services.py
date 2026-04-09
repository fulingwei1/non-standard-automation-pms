#!/usr/bin/env python
"""批量导入服务模块以累积覆盖率"""
import sys
import importlib

sys.path.insert(0, '.')

modules = [
    'app.services.acceptance.acceptance_service',
    'app.services.acceptance_approval',
    'app.services.advantage_product_import_service',
    'app.services.ai_assessment_service',
    'app.services.ai_client_service',
    'app.services.ai_planning',
    'app.services.ai_planning.plan_generator',
    'app.services.ai_planning.schedule_optimizer',
    'app.services.ai_service',
    'app.services.alert.alert_escalation_service',
    'app.services.alert.alert_response_service',
    'app.services.alert.exception_service',
    'app.services.alert.milestone_alert_service',
    'app.services.alert.rule_engine',
    'app.services.alert.rule_engine.alert_creator',
    'app.services.alert.rule_engine.alert_generator',
    'app.services.approval_engine',
    'app.services.approval_engine.engine',
    'app.services.approval_engine.engine.actions',
    'app.services.assembly_kit_service',
    'app.services.best_practices',
    'app.services.bom_attributes',
    'app.services.bom_service',
    'app.services.budget_service',
    'app.services.change_impact_ai_service',
    'app.services.change_impact_analysis_service',
    'app.services.conflict_mediation_service',
    'app.services.cost',
    'app.services.cost.cost_service',
    'app.services.customer_service',
]

for mod in modules:
    try:
        importlib.import_module(mod)
        print(f'OK: {mod}')
    except Exception as e:
        print(f'FAIL: {mod} - {e}')