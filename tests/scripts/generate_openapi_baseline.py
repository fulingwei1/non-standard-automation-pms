# OpenAPI Baseline Generator
# Generates and stores OpenAPI schema baseline for contract drift detection

import json
from pathlib import Path

# Try to import app module directly
try:
    from app.main import app
except ImportError:
    # If app.main import fails, add parent directory to sys.path
    import sys

    parent_dir = str(Path(__file__).parent.parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Try importing with absolute path
    from app.main import app


def generate_openapi_baseline():
    """Generate and save OpenAPI schema baseline."""
    try:
        openapi_schema = app.openapi()
    except Exception as e:
        print(f"Warning: Could not load OpenAPI schema: {e}")
        openapi_schema = {}

    baseline_path = Path("tests/openapi_baseline.json")
    baseline_path.write_text(json.dumps(openapi_schema, indent=2))

    print(f"OpenAPI baseline generated: {baseline_path}")
    return baseline_path


def load_baseline():
    """Load stored OpenAPI baseline."""
    baseline_path = Path("tests/openapi_baseline.json")
    if not baseline_path.exists():
        raise FileNotFoundError(
            "Baseline not found. Run generate_openapi_baseline.py first"
        )

    with open(baseline_path) as f:
        return json.load(f)


def check_endpoint_removal(current_openapi, baseline_openapi):
    """Check for removed endpoints."""
    baseline_paths = baseline_openapi.get("paths", {})
    current_paths = current_openapi.get("paths", {})

    removed = set(baseline_paths.keys()) - set(current_paths.keys())

    if removed:
        removed_list = sorted(removed)
        print("⚠️  REMOVED ENDPOINTS DETECTED:")
        for endpoint in removed_list:
            method = list(endpoint.keys())[0]
            path = list(endpoint.keys())[1]
            print(f"  {method.upper()} {path}")

        print(f"❌ Fail build: {len(removed_list)} endpoints removed")
        raise SystemExit(f"Removed endpoints detected: {len(removed_list)}")

    return len(removed)


def check_breaking_changes(current_openapi, baseline_openapi):
    """Check for breaking schema changes."""
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
        baseline_required = set(baseline_schema.get("required", []))
        current_required = set(current_schema.get("required", []))

        if baseline_required - current_required:
            breaking.append(
                f"{path} - Removed required fields: {baseline_required - current_required}"
            )

        # Check for type changes
        for field_name, field_schema in current_schema.get("properties", {}).items():
            baseline_type = (
                baseline_schema.get("properties", {}).get(field_name, {}).get("type")
            )
            current_type = field_schema.get("type")

            if baseline_type != current_type:
                breaking.append(
                    f"{path} - Type changed for field '{field_name}': {baseline_type} -> {current_type}"
                )

    if breaking:
        print("\n⚠️  BREAKING CHANGES DETECTED:")
        for change in breaking:
            print(f"  {change}")

        print(f"❌ Fail build: Breaking changes detected: {len(breaking)}")
        raise SystemExit(f"Breaking changes detected: {len(breaking)}")

    return len(breaking)


def extract_schemas(openapi_schema):
    """Extract schema information for all endpoints."""
    schemas = {}

    for path, path_spec in openapi_schema.get("paths", {}).items():
        # Get schema from GET method if available
        get_spec = path_spec.get("get", {})
        if get_spec:
            schema_ref = (
                get_spec.get("responses", {})
                .get("200", {})
                .get("content", {})
                .get("schema", {})
            )
            if "$ref" in schema_ref:
                schemas[path] = schema_ref
            continue

        # Get schema from POST/PUT if available
        for method in ["post", "put", "patch", "delete"]:
            if method in path_spec:
                schema_ref = (
                    path_spec.get(method, {})
                    .get("responses", {})
                    .get("200", {})
                    .get("content", {})
                    .get("schema", {})
                )
                if "$ref" in schema_ref:
                    schemas[path] = schema_ref
                    break

    return schemas


def main():
    """Main entry point."""
    print("Checking contract drift...")

    try:
        baseline = load_baseline()

        # Get current OpenAPI
        try:
            from app.main import app

            openapi_schema = app.openapi()
        except ImportError:
            print("Warning: Could not import app, using cached schema if available")
            # Try to use importlib to load app module
            try:
                import importlib
                import app

                openapi_schema = app.openapi()
            except ImportError:
                print("Warning: importlib failed too, using empty schema")
                openapi_schema = {}

        # Run checks
        removals = check_endpoint_removal(openapi_schema, baseline)
        breaking = check_breaking_changes(openapi_schema, baseline)

        print("\nContract Drift Summary:")
        print(f"  Removed endpoints: {removals}")
        print(f"  Breaking changes: {breaking}")
        print(f"  Deprecations: {len(openapi_schema.get('deprecated', {}))}")

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
