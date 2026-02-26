# Test Coverage Analysis Report

**Date**: 2026-02-26
**Scope**: Full codebase static analysis of test coverage gaps

---

## Executive Summary

The project has **2,264 test files** spanning unit, integration, API, e2e, and performance categories. While the sheer volume is impressive, static analysis reveals significant structural gaps — particularly in **endpoint testing (95% untested)**, **model validation (99% untested)**, and **security-critical core modules**. Many unit tests also suffer from quality issues (134 test functions with no assertions).

---

## Current Test Inventory

| Category | Files | Notes |
|----------|-------|-------|
| Unit tests | 1,866 | Bulk of coverage, mostly service-layer |
| Integration tests | 101 | Good workflow coverage |
| API tests | 94 | Covers ~5% of 627 endpoint files |
| Performance tests | 18 | Solid benchmarking suite |
| E2E tests | 5 | Minimal — only 4 workflow tests |
| Other (root, ai_planning, scenarios) | ~80 | Mixed quality |
| **Total** | **~2,264** | |

### Source Code Scale

| Source Category | Files |
|-----------------|-------|
| Services (`app/services/`) | 569 |
| Endpoints (`app/api/v1/endpoints/`) | 627 |
| Models (`app/models/`) | ~199 |
| Core (`app/core/`) | ~38 |
| State machines (`app/core/state_machine/`) | 13 |

---

## Critical Coverage Gaps

### 1. API Endpoints — 95% Untested (CRITICAL)

Only **~33 of 627** endpoint files have corresponding API-level tests. The vast majority of user-facing routes have no direct API test coverage.

**Largest untested endpoint modules:**
- `sales/` — 47 untested files (sales orders, leads, opportunities, contracts)
- `projects/` — 30 untested files (stages, milestones, costs, members, resources)
- `production/` — 18 untested files (work orders, workshops, equipment)
- `ecn/` — 16 untested files (evaluations, tasks, affected materials)
- `task_center/` — 14 untested files
- `acceptance/` — 13 untested files

**Why this matters**: Service-layer unit tests mock the HTTP layer. Without API tests, issues like incorrect request validation, wrong status codes, broken serialization, and permission-check bypasses go undetected.

**Recommendation**: Prioritize API tests for the top 5 most-used modules (projects, sales, purchase, acceptance, ECN). Use the existing `TestClient` fixtures and `api_test_helper.py` to rapidly generate tests.

---

### 2. Data Models — 99% Untested (CRITICAL)

Only **2 of ~199** model files have dedicated model tests (`tests/unit/models/` has 16 files but covers only a handful of models).

**Untested model groups:**
- Production models (21 files) — Workshop, Workstation, Worker, WorkOrder, etc.
- Business support models (10 files) — SalesOrder, DeliveryOrder, BiddingProject
- Approval models (6 files) — ApprovalTemplate, Workflow, Instance, Task
- Service models — ServiceTicket, KnowledgeBase
- PMO models — PmoProjectInitiation, PmoChangeRequest, PmoRisk
- R&D project models — RdProject, RdCost, RdCostAllocationRule
- Alert models, Budget models, ECN config models

**What to test:**
- Column constraints (NOT NULL, unique, length limits)
- Relationship definitions (`back_populates` consistency)
- Index definitions
- Enum field values
- Default value behavior
- `TimestampMixin` correct application
- Soft-delete (`is_active`) behavior

**Recommendation**: Create a parametrized model test generator that validates schema constraints, relationships, and serialization for all 65+ primary models.

---

### 3. Security & Core Infrastructure (HIGH)

**Completely untested security-critical files:**

| File | Risk |
|------|------|
| `app/core/middleware/auth_middleware.py` | Auth bypass |
| `app/core/middleware/tenant_middleware.py` | Cross-tenant data leakage |
| `app/core/middleware/rate_limiting.py` | DoS vulnerability |
| `app/core/csrf.py` | CSRF attacks |
| `app/core/encryption.py` | Data exposure |
| `app/core/api_key_auth.py` | Unauthorized API access |
| `app/core/account_lockout.py` | Brute-force attacks |
| `app/core/secret_manager.py` | Secret exposure |
| `app/core/request_signature.py` | Request tampering |

Only **12 files** carry the `@pytest.mark.security` marker across the entire test suite — far too few for an enterprise system handling financial data.

**Recommendation**: This is the **highest priority**. Each of these files should have dedicated tests covering:
- Happy path + all error branches
- Bypass attempts (malformed tokens, expired tokens, missing headers)
- Tenant isolation verification
- Rate limit enforcement under load

---

### 4. State Machine Framework — Mostly Untested (HIGH)

The state machine base (`app/core/state_machine/base.py`) is **foundational** — all 11 business state machines inherit from it. Yet only a single test file (`tests/unit/core/state_machine/test_base.py`) exists for the framework.

**Untested state machines:**
- `opportunity.py` — Sales pipeline (lead → won/lost)
- `quote.py` — Quotation lifecycle
- `installation_dispatch.py` — Field installation workflow
- `milestone.py` — Project milestones
- `issue.py` — Issue tracking lifecycle
- `notifications.py` — State change notifications
- `permissions.py` — State-based permission checks
- `decorators.py` — State machine decorators

**What to test:**
- Every valid state transition
- Invalid transition rejection
- Permission checks per transition
- Hook execution (pre/post transition)
- Notification dispatch on state change
- Concurrent state transitions (race conditions)

**Recommendation**: Create a systematic state machine test suite that covers all transitions for each of the 11 state machines. Use parametrized tests with `(current_state, action, expected_state)` tuples.

---

### 5. Approval Engine — 22 Untested Files (HIGH)

The approval engine is a critical cross-cutting concern. While some adapter tests exist, the **core engine** and many adapters lack coverage.

**Untested components:**
- `engine/core.py` — Core approval logic
- `engine/submit.py` — Submission handling
- `engine/approve.py` — Approval processing
- `engine/actions.py` — Approval actions
- `engine/query.py` — Query service
- `workflow_engine.py` — Workflow execution
- `condition_parser.py` — Conditional routing
- `execution_logger.py` — Audit trail
- `adapters/base.py` — Base adapter (all others inherit)
- Several notification modules

**Recommendation**: Test the core engine exhaustively — multi-level approval chains, parallel approval, rejection handling, delegation, timeout handling. Then verify each adapter correctly maps business entities to the approval framework.

---

### 6. Report Framework — ~30 Untested Files (MEDIUM)

The entire `app/services/report_framework/` directory (data sources, adapters, expression engine, formatters, renderers, cache) has minimal test coverage.

**Recommendation**: Focus on the expression engine and data source adapters first, as calculation errors in reports can lead to incorrect business decisions.

---

### 7. New Modules — Shallow Coverage (MEDIUM)

Recently added modules have been tested at a surface level but lack depth:

| Module | Test Files Referencing | Concern |
|--------|----------------------|---------|
| Strategy/BEM | ~101 | Tests exist but mostly service-level; no model or API endpoint tests |
| Production | ~98 | Similar — service tests only |
| Service (aftermarket) | ~28 | Minimal coverage for tickets, knowledge base |
| Business Support | ~12 | Sales orders, delivery, bidding nearly untested |
| PMO | ~27 | Basic coverage only |
| R&D Projects | ~23 | Basic coverage only |

---

## Test Quality Issues

### 134 Test Functions With No Assertions

These tests execute code but never verify outcomes — they provide false confidence.

**Examples:**
- `test_acceptance_completion_service.py::test_not_passed`
- `test_acceptance_issues_complete.py::test_acceptance_order`
- `test_acceptance_order_crud_complete.py::test_project`

**Recommendation**: Audit all 134 assertion-less tests. Either add meaningful assertions or remove them to avoid false coverage metrics.

### Error Path Coverage — Only 38% of Unit Tests

Only **704 of 1,866** unit test files contain error/exception assertions (`HTTPException`, `raises`, 4xx/5xx status codes). The majority test only the happy path.

**Recommendation**: For each service, add tests for:
- Invalid input validation
- Not-found scenarios
- Permission denied cases
- Database constraint violations
- Concurrent modification conflicts

### Heavy Mock Usage — 93% of Unit Tests

**1,734 of 1,866** unit test files use mocks. While mocking is appropriate for unit tests, excessive mocking can hide integration bugs (e.g., incorrect SQL queries that pass unit tests but fail against a real database).

**Recommendation**: Ensure critical query logic is also tested in integration tests with a real (in-memory) database.

---

## E2E Test Suite — Nearly Empty (LOW but Important)

Only **4 E2E test files** exist:
- `test_business_workflows.py`
- `test_critical_apis.py`
- `test_critical_apis_extended.py`
- `test_project_lifecycle.py`

For an enterprise ERP system with 90+ modules, this is insufficient. Key business workflows that should have E2E coverage:

1. **Order-to-delivery** — Sales lead → opportunity → quote → contract → project → delivery → acceptance
2. **Procurement cycle** — Requisition → PO → goods receipt → invoice → payment
3. **ECN workflow** — Change request → evaluation → approval → implementation → verification
4. **Employee lifecycle** — Onboarding → role assignment → timesheet → performance review
5. **Financial close** — Cost collection → reconciliation → reporting

---

## Prioritized Improvement Plan

### Phase 1 — Security & Core (1-2 weeks)

| Priority | Area | Files | Impact |
|----------|------|-------|--------|
| P0 | Auth middleware tests | 3 | Prevents auth bypass |
| P0 | CSRF/encryption tests | 4 | Prevents security vulnerabilities |
| P0 | Tenant isolation tests | 2 | Prevents data leakage |
| P1 | State machine base tests | 1 | Foundation for 11 state machines |
| P1 | Account lockout tests | 1 | Prevents brute-force |

### Phase 2 — Core Business Logic (2-4 weeks)

| Priority | Area | Files | Impact |
|----------|------|-------|--------|
| P1 | Approval engine core | 8 | Cross-cutting approval reliability |
| P1 | State machine implementations | 8 | Business workflow correctness |
| P2 | Assertion-less test fixes | 134 funcs | Eliminates false coverage |
| P2 | Error path tests for top services | ~50 | Catches edge-case failures |

### Phase 3 — API & Model Coverage (4-8 weeks)

| Priority | Area | Files | Impact |
|----------|------|-------|--------|
| P2 | API tests for projects, sales, purchase | ~100 | HTTP-layer correctness |
| P2 | Model constraint tests | ~65 | Data integrity |
| P3 | Report framework tests | ~30 | Report accuracy |
| P3 | New module depth (Strategy, Production) | ~40 | New feature reliability |

### Phase 4 — E2E & Integration (2-4 weeks)

| Priority | Area | Tests | Impact |
|----------|------|-------|--------|
| P3 | Critical E2E workflows | 5-8 | End-to-end confidence |
| P3 | Cross-module integration tests | 10-15 | System integration |
| P4 | Performance regression tests | 5-10 | Performance baseline |

---

## Quick Wins

1. **Add `--cov-fail-under=X` to pytest.ini** — Enforce a minimum coverage threshold (start at current level, ratchet up over time)
2. **Fix 134 assertion-less tests** — Each one is a 5-minute fix that improves reliability
3. **Add `@pytest.mark.security` to all security tests** — Makes it easy to run `pytest -m security` before releases
4. **Create a model test generator script** — Parametrized tests can cover 65+ models in a single file
5. **Add mutation testing** (e.g., `mutmut`) — Identifies tests that pass even when code is broken

---

## Metrics to Track

| Metric | Current (estimated) | Target |
|--------|-------------------|--------|
| Line coverage | Unknown (no recent run) | 80%+ |
| Branch coverage | Unknown | 70%+ |
| Security test count | 12 marked files | 50+ |
| E2E test count | 4 files | 15+ |
| Assertion-less tests | 134 functions | 0 |
| API endpoint test coverage | ~5% | 60%+ |
| Model test coverage | ~1% | 80%+ |

---

*Generated by static analysis of the codebase. Actual line/branch coverage numbers require a successful `pytest --cov` run.*
