#!/bin/bash
cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms
export SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
export DATABASE_URL="sqlite:///:memory:"
export REDIS_URL=""

python3 -m coverage erase

# All our comprehensive tests + schema imports
TESTS=(
    tests/unit/test_business_rules_comprehensive.py
    tests/unit/test_account_lockout_comprehensive.py
    tests/unit/test_session_service_comprehensive.py
    tests/unit/test_project_statistics_comprehensive.py
    tests/unit/test_notification_service_comprehensive.py
    tests/unit/test_pipeline_health_comprehensive.py
    tests/unit/test_budget_analysis_comprehensive.py
    tests/unit/test_collaboration_service_comprehensive.py
    tests/unit/test_cost_collection_comprehensive.py
    tests/unit/test_supplier_performance_comprehensive.py
    tests/unit/test_multi_services_batch2.py
    tests/unit/test_schemas_import_coverage.py
    # Previous tests
    tests/unit/test_acceptance_approval_service.py
    tests/unit/test_acceptance_bonus_service.py
    tests/unit/test_acceptance_completion_service.py
    tests/unit/test_alert_response_service.py
    tests/unit/test_alert_trend_service.py
    tests/unit/test_approval_engine_service.py
    tests/unit/test_change_impact_ai_service.py
    tests/unit/test_contract_revenue_recognition_service.py
    tests/unit/test_cost_dashboard_service.py
    tests/unit/test_cost_forecast_service.py
    tests/unit/test_cost_overrun_analysis_service.py
    tests/unit/test_cost_prediction_service.py
    tests/unit/test_cpq_pricing_service.py
    tests/unit/test_data_sync_service.py
    tests/unit/test_delay_root_cause_service.py
    tests/unit/test_financial_analysis_service.py
    tests/unit/test_inventory_management_service.py
    tests/unit/test_kit_rate_service.py
    tests/unit/test_labor_cost_service.py
    tests/unit/test_permission_cache_service.py
    tests/unit/test_permission_management_service.py
    tests/unit/test_permission_service.py
    tests/unit/test_presale_mobile_service.py
    tests/unit/test_production_progress_service.py
    tests/unit/test_production_schedule_service.py
    tests/unit/test_progress_service.py
    tests/unit/test_project_import_service.py
    tests/unit/test_quality_service.py
    tests/unit/test_report_service.py
    tests/unit/test_resource_scheduling_service.py
    tests/unit/test_role_management_service.py
    tests/unit/test_schedule_prediction_service.py
    tests/unit/test_solution_engineer_bonus_service.py
    tests/unit/test_timesheet_analytics_service.py
    tests/unit/test_timesheet_forecast_service.py
    tests/unit/test_project_performance_service.py
    tests/unit/test_customer_service.py
    tests/unit/test_milestone_service.py
    # Additional batch of existing tests for extra coverage
    tests/unit/test_acceptance_adapter_enhanced.py
    tests/unit/test_acceptance_adapter_rewrite.py
    tests/unit/test_acceptance_approval_service_cov57.py
    tests/unit/test_acceptance_approval_service_enhanced.py
    tests/unit/test_acceptance_approval_service_rewrite.py
    tests/unit/test_acceptance_bonus_service_comprehensive.py
    tests/unit/test_acceptance_bonus_service_cov14.py
    tests/unit/test_acceptance_completion_service_comprehensive.py
    tests/unit/test_acceptance_completion_service_cov21.py
    tests/unit/test_acceptance_cov14.py
    tests/unit/test_acceptance_completion_complete.py
    tests/unit/test_acceptance_issues_complete.py
    tests/unit/test_acceptance_order_crud_complete.py
    tests/unit/test_acceptance_report_service.py
    tests/unit/test_acceptance_service.py
    tests/unit/test_acceptance_utils.py
    tests/unit/test_acceptance_utils_complete.py
    tests/unit/test_alert_response_service_enhanced.py
    tests/unit/test_business_rules_enhanced.py
    tests/unit/test_business_rules_depth.py
    tests/unit/test_evm_service.py
    tests/unit/test_health_calculator.py
    tests/unit/test_state_machine_core.py
    tests/unit/test_permission_service_core.py
    tests/unit/test_auth.py
    tests/unit/test_security.py
    tests/unit/test_core_config.py
    tests/unit/test_common_utils.py
)

TOTAL=${#TESTS[@]}
PASSED=0
FAILED=0
i=0

for f in "${TESTS[@]}"; do
    i=$((i + 1))
    if [ ! -f "$f" ]; then
        continue
    fi
    python3 -m coverage run --append --source=app -m pytest "$f" -o "addopts=" -q --tb=no --no-header --no-cov -x 2>/dev/null
    RC=$?
    if [ $RC -eq 0 ]; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi
    if [ $((i % 10)) -eq 0 ]; then
        echo "Progress: $i/$TOTAL (pass=$PASSED fail=$FAILED)"
    fi
done

echo ""
echo "=== Summary ==="
echo "Total: $TOTAL, Passed: $PASSED, Failed: $FAILED"
echo ""
echo "=== Overall Coverage ==="
python3 -m coverage report 2>&1 | tail -1
echo ""
echo "=== Services Coverage ==="
python3 -m coverage report --include="app/services/*" 2>&1 | tail -1
python3 -m coverage html
python3 -m coverage report --sort=cover > /tmp/coverage_final2.txt
echo "Done"
