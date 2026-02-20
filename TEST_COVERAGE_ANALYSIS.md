# Test Coverage Analysis Report

**Date**: 2026-02-20
**Codebase**: Non-Standard Automation PMS
**Overall Line Coverage**: 37.8% (46,976 / 104,884 statements)
**Overall Branch Coverage**: 6.3% (1,456 / 23,110 branches)
**Total Test Files**: ~1,777

---

## Executive Summary

The codebase has a large test suite (1,777 files) but effective coverage is low at **37.8% line / 6.3% branch**. Out of 346 analyzed modules, **35.5% have less than 10% coverage** and **69% are below 50%**. There are **140 source files with >50 lines that have 0% coverage**. The test suite is heavily skewed toward unit tests with mocks, with limited integration and end-to-end testing.

### Key Numbers

| Metric | Value |
|--------|-------|
| Source files analyzed | 1,445 |
| Source files with 0% coverage (>50 lines) | 140 |
| Source files with 1-20% coverage (>50 lines) | 179 |
| Modules below 50% coverage | 239 / 346 (69%) |
| Test files | ~1,777 |
| Unit tests | ~1,489 |
| Integration tests | ~66 |
| API tests | ~74 |
| E2E tests | 4 |
| Security tests | 9 |
| Performance tests | 3 |

---

## Priority 1: Critical Infrastructure with 0% Coverage

These are core system services that affect many downstream modules but have **zero test coverage**:

| Service | Lines | Purpose | Risk |
|---------|-------|---------|------|
| `services/alert_rule_engine/` | 319 | Alert/warning rule evaluation engine | System health monitoring depends on this |
| `services/unified_import/` | 440 | Excel/data import framework | Data integrity risk |
| `services/performance_collector/` | 337 | Engineer performance data collection | Incorrect metrics affect evaluations |
| `services/health_calculator.py` | 138 | Project health score computation | Dashboard accuracy |
| `services/data_sync_service.py` | 141 | Cross-system data synchronization | Data consistency |
| `services/status_transition_service.py` | 75 | Business object state transitions | Workflow correctness |
| `services/stage_transition_checks.py` | 66 | Stage advancement validation | Project lifecycle integrity |
| `services/cost_collection_service.py` | 174 | Multi-source cost data collection | Financial accuracy |
| `services/progress_integration_service.py` | 181 | Progress data aggregation | Dashboard/reporting accuracy |
| `services/data_scope_service_enhanced.py` | 179 | Enhanced data access control | Security/authorization |

**Recommendation**: These services form the backbone of business logic. Prioritize writing tests for `alert_rule_engine`, `health_calculator`, `status_transition_service`, and `stage_transition_checks` first, as bugs here cascade into visible system failures.

---

## Priority 2: Approval Engine (21.9% coverage, 2,331 missing lines)

The approval engine is the second-largest coverage gap by missing lines and is **critical business infrastructure** used by 11 different business types.

### Current State

| Component | Coverage Status |
|-----------|----------------|
| `adapters/` (11 adapters) | Mostly untested |
| `engine/core.py` | Low coverage |
| `engine/submit.py` | Low coverage |
| `engine/approve.py` | Low coverage |
| `workflow/engine.py` | ~9.6% |
| `workflow/condition_parser.py` | ~6.2% |
| `notifications/` | Partially covered |

### What to Test

- **Adapter correctness**: Each of the 11 adapters (acceptance, contract, ECN, invoice, outsourcing, project, purchase, quote, timesheet) should have tests verifying they correctly translate business objects into approval workflows.
- **Workflow transitions**: Submit → approve → reject → delegate → escalate flows.
- **Condition parsing**: The condition parser evaluates dynamic approval rules; edge cases around malformed conditions and boundary values need coverage.
- **Concurrency**: Simultaneous approval/rejection of the same instance.

---

## Priority 3: Branch Coverage is Critically Low (6.3% overall)

Branch coverage measures whether both sides of every `if/else`, `try/except`, and conditional expression are tested. At 6.3%, almost no error paths or alternative branches are tested.

### Worst Offenders (decent line coverage, near-zero branch coverage)

| File | Line% | Branch% | Branches |
|------|-------|---------|----------|
| `endpoints/projects/costs/cost_prediction_ai.py` | 44.1% | 0.0% | 0/48 |
| `endpoints/projects/costs/evm.py` | 44.4% | 0.0% | 0/32 |
| `endpoints/two_factor.py` | 41.0% | 0.0% | 0/28 |
| `models/project/core.py` | 68.1% | 0.0% | 0/28 |
| `endpoints/production/work_orders/crud.py` | 30.4% | 0.0% | 0/22 |
| `endpoints/production/capacity/calculation.py` | 41.3% | 0.0% | 0/20 |

**Recommendation**: Existing tests appear to only exercise happy paths. Add tests for:
- Error/exception branches in service methods
- Validation failures (invalid input, missing required fields)
- Authorization failures (wrong role, insufficient permissions)
- Empty result sets and boundary conditions
- `try/except` blocks (verify exception handling works)

---

## Priority 4: API Layer (37.6% coverage, 14,489 missing lines)

The API layer is the single largest gap by absolute missing lines.

### Coverage by Endpoint Module

| Module | Files | Lines | Coverage | Missing |
|--------|-------|-------|----------|---------|
| `sales/` | 82 | 5,780 | 36.8% | 3,653 |
| `projects/` | 77 | 5,131 | 37.0% | 3,230 |
| `production/` | 23 | 2,234 | 26.9% | 1,632 |
| `business_support_orders/` | 14 | 1,262 | 35.6% | 813 |
| `shortage/` | 9 | 1,072 | 46.3% | 576 |
| `assembly_kit/` | 13 | 807 | 34.4% | 529 |
| `timesheet/` | 8 | 724 | 28.3% | 519 |
| `organization/` | 9 | 656 | 35.7% | 422 |
| `approvals/` | 5 | 501 | 31.7% | 342 |
| `permissions/` | 2 | 225 | 23.6% | 172 |

### What's Missing in API Tests

The existing 74 API test files focus on basic CRUD happy paths. Key gaps:

1. **Authorization testing**: Most endpoints use `require_permission()` but tests don't verify that unauthorized users are rejected. No test sends a request with a non-admin user and asserts 403.
2. **Input validation**: Pydantic validation errors, malformed request bodies, invalid query parameters. No tests verify 422 responses for bad payloads.
3. **Pagination and filtering**: Tests only request page 1 with default size. No tests for page=0, page_size > max, page > total_pages, or keyword filtering.
4. **Error responses**: No tests for 404 (missing resources), 409 (conflicts/duplicates), or 422 (schema violations).
5. **Production and sales modules**: The two largest API modules (5,780 and 5,131 lines respectively) both sit below 40% coverage.

**Specific example** — `tests/api/test_alerts.py`:
- Lines 20-59: Only GET requests
- Lines 60-84: Only successful POST (status 201)
- Lines 87-119: Only GET by ID success
- Missing: 400/403/404/409/422 error cases, pagination edge cases, rate limiting behavior

**Specific example** — `tests/api/test_auth.py` (lines 26-32):
```python
def test_login_wrong_password(...):
    # Only checks "!= 200" — doesn't verify specific 401 status
    # Doesn't check error message content
    # Doesn't test rate limiting after 5 wrong attempts
    # Doesn't test account lockout behavior
```

---

## Priority 5: Service Modules with 0% Coverage (High Business Value)

Beyond infrastructure, these business services have zero coverage:

| Service | Lines | Business Impact |
|---------|-------|----------------|
| `timesheet_forecast_service.py` | 270 | Workforce planning |
| `presale_ai_knowledge_service.py` | 265 | Presale decision support |
| `change_impact_ai_service.py` | 235 | ECN impact assessment |
| `ecn_bom_analysis_service/` | 227 | BOM change cascade analysis |
| `procurement_analysis/` | 221 | Procurement decision analytics |
| `collaboration_rating/` | 218 | Cross-department evaluation |
| `ai_emotion_service.py` | 215 | Customer emotion analysis |
| `timesheet_analytics_service.py` | 211 | Work time analytics |
| `invoice_auto_service/` | 208 | Automated invoice generation |
| `presale_ai_requirement_service.py` | 199 | AI requirement analysis |
| `report_excel_service.py` | 199 | Excel report generation |
| `presale_ai_service.py` | 198 | AI presale assistance |
| `performance_service/` | 196 | Performance evaluation |
| `supplier_performance_evaluator.py` | 190 | Supplier scoring |
| `work_log_ai/` | 187 | AI work log analysis |
| `metric_calculation_service.py` | 180 | KPI metric calculation |

---

## Priority 6: Test Quality Issues

### 6a. Weak Assertions

Sampling 200 test files revealed:
- **45 files** contain weak assertions like `assert result is not None` or `assert True` as the only verification.
- **68 out of 713 test functions** (in 50 sampled files) contain **no assertions at all**.
- These tests provide a false sense of coverage without actually verifying behavior.

**Specific examples found:**

`tests/unit/test_acceptance_bonus_service_comprehensive.py` (lines 106, 133, 240, 267):
```python
assert result is not None  # Only checks existence — never validates bonus values
```

`tests/api/test_approvals_api.py` (lines 48, 91, 93):
```python
assert "total" in data or "items" in data  # OR condition too loose — accepts any shape
assert response.status_code in [200, 201]  # Accepts either — doesn't know which to expect
assert "id" in data or "template_code" in data  # Accepts any shape
```

**Pattern to follow instead** (from `tests/unit/test_auth.py` lines 95-120):
```python
payload = jwt.decode(token, ...)
assert payload["sub"] == user_id       # Validates specific content
assert "exp" in payload                # Validates structure
assert len(payload["jti"]) == 32       # Validates value properties
```

### 6b. Over-Mocking

30% of sampled unit test files use mocks. While mocking is appropriate for external dependencies (Redis, email, AI APIs), some tests mock the database layer so heavily that they don't verify actual query logic or ORM relationships work.

**Specific example** — `tests/services/test_approval_approve.py` (lines 47-120):
```python
class MockEngine(ApprovalProcessMixin):
    def __init__(self):
        self.db = MagicMock()
        self.executor = MagicMock()
        self.notify = MagicMock()
        self.delegate_service = MagicMock()
```
Everything is stubbed — tests pass even if underlying approval logic is broken. The test verifies mock behavior, not actual workflow state transitions.

**Contrast with good pattern** — `tests/unit/test_auth.py` (lines 33-75):
- Uses real `get_password_hash()` and `verify_password()`, not mocks
- Creates actual JWT tokens and decodes them with real crypto
- These tests catch real authentication bugs

### 6c. Missing Error Path Tests

State machine implementations (`app/core/state_machine/`) define valid transitions but tests primarily verify the happy path.

**State machine** (`app/core/state_machine/base.py` lines 74-114):
- Has enum handling with `.rsplit(".", 1)[-1]` fallback (line 87-93) — **no test covers this path**
- Has validator exception handling (lines 106-112) — **no test triggers validator failures**
- `can_transition_to()` validation — **no test for invalid target states**

**Auth module** (`app/core/auth.py` lines 107-118):
```python
if user_is_superuser and user_tenant_id is not None:
    raise ValueError("Invalid superuser data...")
```
This `validate_user_tenant_consistency()` function is **never tested** despite being a security-critical validation.

**Approval engine** — `tests/services/test_approval_approve.py`:
- Tests empty comment rejection but not `None` comment, whitespace-only comment, or max-length comment
- No tests for concurrent approvals of the same instance
- No tests for approval callback failures

### 6d. High Test Skip Rate

The test suite has **2,663+ `pytest.skip()` calls**, indicating many tests are routinely skipped. This inflates the test file count while reducing actual coverage.

---

## Priority 7: Integration and E2E Test Gaps

### Integration Tests (66 files)

Covered workflows:
- Authentication flow
- Purchase-material-inventory flow (4 dedicated files)
- Approval flow
- ECN approval flow
- Acceptance workflow
- CRUD API integration

Missing workflows:
- **Complete project lifecycle** (S1 through S9 with all stage transitions)
- **Shortage detection → urgent purchase generation** flow
- **ECN → BOM update → cost recalculation** cascade
- **Timesheet submission → approval → payroll calculation** flow
- **Strategy → KPI → department objectives → personal KPI** decomposition
- **Production plan → work order → completion → quality check** flow
- **Customer complaint → service ticket → resolution → satisfaction survey** flow

### E2E Tests (4 files)

The e2e test suite is minimal:
- `test_project_lifecycle.py` - Covers the primary lifecycle
- `test_business_workflows.py` - Some business flows
- `test_critical_apis.py` / `test_critical_apis_extended.py` - Critical API checks

Missing:
- Multi-tenant isolation E2E scenarios
- Cross-module workflow E2E (e.g., presale → project → production → acceptance → service)
- Performance degradation E2E (large data volumes)

### Security Tests (9 files)

Existing coverage:
- CSRF protection, security headers, tenant isolation, API key auth

Missing:
- SQL injection testing on search/filter endpoints
- JWT token expiration and refresh edge cases
- Rate limiting behavior verification
- Permission escalation attempts
- Bulk API abuse scenarios

---

## Recommended Action Plan

### Phase 1: Critical Infrastructure (Highest ROI)

1. **Alert rule engine** (`alert_rule_engine/`) - Write unit tests for condition evaluation, alert generation, level determination, and alert upgrading.
2. **Status/stage transition services** (`status_transition_service.py`, `stage_transition_checks.py`) - Test all valid and invalid transitions.
3. **Health calculator** (`health_calculator.py`) - Test health score computation with various project states.
4. **Permission service** (`permission_service.py` at 45.7%) - Increase to >80%, test cache invalidation and role inheritance.

### Phase 2: Approval Engine

5. Test each of the 11 approval adapters with at least: submit, approve, reject, delegate scenarios.
6. Test the workflow engine's condition parser with boundary conditions.
7. Test approval notification dispatch.

### Phase 3: Branch Coverage Improvement

8. Audit existing tests with >30% line coverage but <15% branch coverage (34 files identified).
9. Add negative test cases: invalid input, unauthorized access, resource not found.
10. Add boundary condition tests: empty lists, null values, max values.

### Phase 4: API Layer

11. Add authorization tests to all endpoint modules (verify 403 for unauthorized users).
12. Add input validation tests (verify 422 for invalid payloads).
13. Prioritize `production/` (26.9%) and `timesheet/` (28.3%) endpoint modules.

### Phase 5: Integration Tests

14. Add complete project lifecycle integration test (S1→S9 with all stakeholders).
15. Add ECN cascade integration test (change → evaluation → approval → BOM update).
16. Add shortage-to-purchase integration test.

### Phase 6: Fix Test Quality

17. Audit and strengthen tests that only assert `is not None`.
18. Remove or rewrite test functions with zero assertions.
19. Replace over-mocked unit tests with integration tests where database interaction is the core logic.

---

## Appendix: Module Coverage Summary

### By Coverage Tier

| Tier | Module Count | % of Total |
|------|-------------|-----------|
| 0% (no coverage) | 123 | 35.5% |
| 1-9% | 0 | 0% |
| 10-49% | 116 | 33.5% |
| 50-79% | 25 | 7.2% |
| 80-99% | 43 | 12.4% |
| 100% | 39 | 11.3% |

### Models vs Services vs API

| Layer | Avg Coverage | Notes |
|-------|-------------|-------|
| Models | ~85%+ | Well covered (ORM definitions are simpler to test) |
| Services | ~20-30% | Largest gap; business logic undertested |
| API endpoints | ~37.6% | Happy paths partially covered |
| Core (auth, state machine) | ~40-50% | Moderate, but branch coverage near 0% |
