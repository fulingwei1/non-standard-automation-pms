import os

files_to_patch = [
    "app/models/exports/other_models.py",
    "app/models/exports/complete/other_modules.py",
    "app/models/exports/complete/performance_organization.py",
    "app/models/exports/organization_models.py",
    "app/models/exports/core.py",
    "app/api/v1/endpoints/roles/crud/data_scope.py",
]

base_dir = "/Users/flw/non-standard-automation-pm"

replacements = [
]


def patch_file(filepath):
    abs_path = os.path.join(base_dir, filepath)
    if not os.path.exists(abs_path):
        print(f"Skipping {filepath}, file not found.")
        return
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)

    if new_content != content:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {filepath}")


for f in files_to_patch:
    patch_file(f)
