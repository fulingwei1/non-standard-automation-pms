# Phase 1: API Test Repair and Contract Drift Detection

## Overview

This phase focuses on:
1. Identifying and fixing API-mismatched tests (align payloads with schemas, routes/params)
2. Adding contract drift detection CI job to detect removed endpoints or OpenAPI changes

## Current Issues

### Import Error
- pytest command failing due to conftest.py syntax error
- Chinese characters in docstrings causing parsing issues in Python 3.14
- Fix in progress: converting docstrings to English

### Known API Test Structure
- Tests located in `tests/api/` and `tests/integration/`
- Uses `APITestHelper` class for standardized testing
- Fixture-based auth with admin/user roles

## Test Categories for Repair

### Category 1: Authentication & Authorization Tests

**Priority: HIGH**
**Files:**
- `tests/api/test_auth.py`
- `tests/integration/test_auth_api.py`

**Common Issues to Fix:**
1. Token validation format mismatches
2. Permission check failures
3. Rate limiting 429 errors
4. User role assignment failures

**Test Cases:**
- Login with invalid credentials
- Login with valid credentials
- Token refresh
- Permission denied scenarios
- Role-based access control

### Category 2: Project CRUD Tests

**Priority: HIGH**
**Files:**
- `tests/api/test_projects_api.py`
- `tests/api/test_projects.py`
- `tests/integration/test_projects_api.py`

**Common Issues to Fix:**
1. Project code format validation
2. Stage transition validation
3. Pagination parameters
4. Field validation (email, phone, amount)
5. Foreign key relationship failures

**Test Cases:**
- Create project with valid data
- Create project with invalid email
- Create project with invalid phone
- Update project fields
- Delete project
- List projects with pagination
- Get project by ID

### Category 3: Machine Tests

**Priority: MEDIUM**
**Files:**
- `tests/api/test_machines.py`
- `tests/integration/test_machines_api.py`

**Common Issues to Fix:**
1. Machine code format validation
2. Machine type validation
3. Project relationship validation
4. Serial number uniqueness

**Test Cases:**
- Create machine
- Get machines
- Update machine status
- Delete machine
- Machine-project relationships

### Category 4: Data Model Validation Tests

**Priority: HIGH**
**Files:**
- `tests/api/test_costs.py`
- `tests/integration/test_costs_api.py`
- `tests/api/test_bom.py`

**Common Issues to Fix:**
1. Enum value validation
2. Decimal precision mismatches
3. Required field violations
4. Foreign key constraint violations

**Test Cases:**
- Create cost item with invalid enum
- Update cost amount precision
- Validate required fields
- Test BOM structure validation
- Material category validation

## Contract Drift Detection Strategy

### Step 1: Generate OpenAPI Schema Snapshot

**Approach:**
1. Extract current OpenAPI schema from FastAPI app
2. Store as baseline in `tests/openapi_baseline.json`
3. Track changes over time

**Implementation:**
```python
# tests/scripts/generate_openapi_baseline.py
import json
from app.main import app
from pathlib import Path

def generate_openapi_baseline():
    """Generate and save OpenAPI schema baseline."""
    openapi_schema = app.openapi()
    
    baseline_path = Path("tests/openapi_baseline.json")
    baseline_path.write_text(json.dumps(openapi_schema, indent=2))
    
    print(f"OpenAPI baseline generated: {baseline_path}")
    return baseline_path

if __name__ == "__main__":
    generate_openapi_baseline()
```

### Step 2: Contract Drift Detection

**Checks to Implement:**
1. **Endpoint Removal Detection:**
   - Compare baseline with current OpenAPI
   - List removed endpoints
   - Fail build if any endpoint removed without deprecation notice

2. **Breaking Change Detection:**
   - Detect schema changes in request/response models
   - Fail build if breaking changes detected without version bump
   - Require manual approval for breaking changes

3. **Deprecation Tracking:**
   - Maintain deprecation log in `tests/deprecations.json`
   - Track deprecated endpoints and versions
   - Remove endpoints after deprecation period

**Implementation:**
```python
# tests/scripts/contract_drift_detector.py
import json
from pathlib import Path

BASELINE_PATH = Path("tests/openapi_baseline.json")
DEPRECATIONS_PATH = Path("tests/deprecations.json")


def load_baseline():
    """Load stored OpenAPI baseline."""
    if not BASELINE_PATH.exists():
        raise FileNotFoundError("Baseline not found. Run generate_openapi_baseline.py first")
    
    with open(BASELINE_PATH) as f:
        return json.load(f)


def load_deprecations():
    """Load deprecation log."""
    if DEPRECATIONS_PATH.exists():
        with open(DEPRECATIONS_PATH) as f:
            return json.load(f)
    return {}


def check_endpoint_removal(current_openapi, baseline_openapi):
    """Check for removed endpoints."""
    baseline_paths = baseline_openapi.get('paths', {})
    current_paths = current_openapi.get('paths', {})
    
    removed = set(baseline_paths.keys()) - set(current_paths.keys())
    
    if removed:
        removed_list = sorted(removed)
        print(f"⚠️  REMOVED ENDPOINTS DETECTED:")
        for endpoint in removed_list:
            method = list(endpoint.keys())[0]
            path = list(endpoint.keys())[1]
            print(f"  {method.upper()} {path}")
        
        raise SystemExit(f"Removed endpoints detected: {len(removed_list)}")
    
    return len(removed)


def check_breaking_changes(current_openapi, baseline_openapi):
    """Check for breaking schema changes."""
    # Compare schemas for each endpoint
    baseline_schemas = extract_schemas(baseline_openapi)
    current_schemas = extract_schemas(current_openapi)
    
    breaking = []
    
    for path, schema in current_schemas.items():
        if path not in baseline_schemas:
            breaking.append(f"New endpoint: {path}")
            continue
        
        baseline_schema = baseline_schemas.get(path, {})
        current_schema = current_schemas.get(path, {})
        
        # Check for removed required fields
        baseline_required = set(baseline_schema.get('required', []))
        current_required = set(current_schema.get('required', []))
        
        if baseline_required - current_required:
            breaking.append(f"{path} - Removed required fields: {baseline_required - current_required}")
        
        # Check for type changes
        for field_name, field_schema in current_schema.get('properties', {}).items():
            baseline_type = baseline_schema.get('properties', {}).get(field_name, {}).get('type')
            current_type = field_schema.get('type')
            
            if baseline_type != current_type:
                breaking.append(f"{path} - Type changed for field '{field_name}': {baseline_type} -> {current_type}")
    
    if breaking:
        print("⚠️  BREAKING CHANGES DETECTED:")
        for change in breaking:
            print(f"  {change}")
        
        raise SystemExit(f"Breaking changes detected: {len(breaking)}")
    
    return len(breaking)


def extract_schemas(openapi_schema):
    """Extract schema information for all endpoints."""
    schemas = {}
    
    for path, path_spec in openapi_schema.get('paths', {}).items():
        # Get schema from GET method if available
        get_spec = path_spec.get('get', {})
        if get_spec:
            schema_ref = get_spec.get('responses', {}).get('200', {}).get('content', {}).get('schema', {})
            if '$ref' in schema_ref:
                schemas[path] = schema_ref
            continue
    
        # Get schema from POST/PUT if available
        for method in ['post', 'put', 'patch', 'delete']:
            if method in path_spec:
                schema_ref = path_spec.get(method, {}).get('responses', {}).get('200', {}).get('content', {}).get('schema', {})
                if '$ref' in schema_ref:
                    schemas[path] = schema_ref
                    break
    
    return schemas


def main():
    """Main entry point."""
    print("Checking contract drift...")
    
    try:
        # Load baseline
        baseline = load_baseline()
        deprecations = load_deprecations()
        
        # Get current OpenAPI
        from app.main import app
        current_openapi = app.openapi()
        
        # Run checks
        removals = check_endpoint_removal(current_openapi, baseline)
        breaking = check_breaking_changes(current_openapi, baseline)
        
        print(f"\nContract Drift Summary:")
        print(f"  Removed endpoints: {removals}")
        print(f"  Breaking changes: {breaking}")
        print(f"  Deprecations: {len(deprecations)}")
        
        if removals == 0 and breaking == 0:
            print("\n✅ No contract drift detected!")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"\n❌ Error checking contract drift: {e}")
        return 2


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### Step 3: Add to CI/CD Pipeline

**Update `.github/workflows/tests.yml`:**
```yaml
- name: Check OpenAPI baseline
  if: github.event_name == 'pull_request'
  run: |
    python3 tests/scripts/generate_openapi_baseline.py
    cp tests/openapi_baseline.json tests/openapi_baseline-pr.json
        git add tests/openapi_baseline-pr.json
    
- name: Contract drift detection
  if: github.event_name == 'pull_request'
  needs: openapi-baseline
  run: |
    python3 tests/scripts/contract_drift_detector.py
```

## Implementation Plan

### Week 1: Test Repair Sprint
**Goal:** Fix 50%+ of failing/mismatched API tests

**Priority Order:**
1. Authentication tests (2 days)
   - Fix token issues
   - Fix permission checks
   - Fix rate limiting
2. Project CRUD tests (3 days)
   - Fix validation errors
   - Fix foreign key issues
3. Machine tests (2 days)
   - Fix code format validation
   - Fix serial number checks

### Week 2: Contract Drift Implementation
**Goal:** Implement contract drift detection (2 days)

**Tasks:**
1. Generate OpenAPI baseline script
2. Implement contract drift detector
3. Add to CI pipeline
4. Update documentation

## Success Criteria

Phase 1 is complete when:
- [ ] pytest tests/api/ runs without failures
- [ ] pytest tests/integration/ -m api runs without failures
- [ ] OpenAPI baseline generated
- [ ] Contract drift detector script created
- [ ] CI workflow updated with contract checks
- [ ] Test repair document created with 100+ test cases fixed

## Risk Mitigation

1. **Rollback Strategy:**
   - Maintain baseline history
   - Allow manual deprecation approval
   - Version API changes properly

2. **Testing Strategy:**
   - Fix in feature branches
   - Test in staging environment first
   - Peer review all contract changes
   - Update baseline on merge

3. **Communication:**
   - Document breaking changes in PR descriptions
   - Tag related issues in deprecation PRs
   - Notify team of API changes

## Next Steps

After Phase 1 complete:
- Continue to Phase 2.1-2.6 (actual test writing)
- Write tests for high-priority modules
- Achieve 50%+ coverage target increment
