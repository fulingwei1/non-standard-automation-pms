#!/bin/bash

# 测试修复效果的脚本

export SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
export DATABASE_URL="sqlite:///:memory:"
export REDIS_URL="redis://localhost:6379/0"

echo "========================================"
echo "测试问题1：验收管理API (5个测试)"
echo "========================================"

python3 -m pytest \
  tests/api/test_acceptance.py::TestAcceptanceTemplates::test_list_templates \
  tests/api/test_acceptance.py::TestAcceptanceTemplates::test_create_template \
  tests/api/test_acceptance.py::TestAcceptanceOrders::test_list_orders \
  tests/api/test_acceptance.py::TestAcceptanceOrders::test_list_orders_with_filters \
  tests/api/test_acceptance_report_unified_api.py::TestAcceptanceReportUnifiedAPI::test_list_available_reports \
  -v --tb=short

echo ""
echo "========================================"
echo "测试问题2：采购&库存集成测试 (5个测试)"
echo "========================================"

python3 -m pytest \
  tests/integration/purchase_material_inventory/test_01_complete_purchase_flow.py::TestCompletePurchaseFlow::test_purchase_request_to_stock_update \
  tests/integration/purchase_material_inventory/test_01_complete_purchase_flow.py::TestCompletePurchaseFlow::test_purchase_workflow_validation \
  tests/integration/purchase_material_inventory/test_02_shortage_emergency_purchase.py::TestShortageEmergencyPurchase::test_low_stock_alert_and_emergency_purchase \
  tests/integration/purchase_material_inventory/test_02_shortage_emergency_purchase.py::TestShortageEmergencyPurchase::test_critical_shortage_alert_level \
  tests/integration/purchase_material_inventory/test_03_15_business_scenarios.py::TestMaterialReservationAndIssue::test_material_reservation_flow \
  -v --tb=short
