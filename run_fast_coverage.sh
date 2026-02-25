#!/bin/bash
cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms
export SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
export DATABASE_URL="sqlite:///:memory:"
export REDIS_URL=""

python3 -m coverage erase

# Run a representative set of tests - pick one per service topic (avoid duplicates)
# Use parallel approach: run each file and append coverage
FILES=(
    tests/unit/test_acceptance_approval_service.py
    tests/unit/test_acceptance_bonus_service.py  
    tests/unit/test_acceptance_completion_service.py
    tests/unit/test_alert_response_service.py
    tests/unit/test_alert_trend_service.py
    tests/unit/test_approval_engine_service.py
    tests/unit/test_business_rules.py
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
    tests/unit/test_state_machine_service.py
    tests/unit/test_project_performance_service.py
    tests/unit/test_customer_service.py
    tests/unit/test_milestone_service.py
)

TOTAL=${#FILES[@]}
PASSED=0
FAILED=0
SKIPPED=0
i=0

for f in "${FILES[@]}"; do
    i=$((i + 1))
    if [ ! -f "$f" ]; then
        echo "SKIP: $f (not found)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    python3 -m coverage run --append --source=app -m pytest "$f" -o "addopts=" -q --tb=no --no-header --no-cov -x 2>/dev/null
    RC=$?
    
    if [ $RC -eq 0 ]; then
        PASSED=$((PASSED + 1))
        echo "PASS ($i/$TOTAL): $f"
    else
        FAILED=$((FAILED + 1))
        echo "FAIL ($i/$TOTAL): $f"
    fi
done

echo ""
echo "=== Summary ==="
echo "Total: $TOTAL, Passed: $PASSED, Failed: $FAILED, Skipped: $SKIPPED"
echo ""
echo "=== Coverage Report (services) ==="
python3 -m coverage report --include="app/services/*" --sort=cover | head -80
echo ""
echo "=== Overall Coverage ==="
python3 -m coverage report | tail -1
python3 -m coverage html
python3 -m coverage report --sort=cover > /tmp/coverage_full.txt
