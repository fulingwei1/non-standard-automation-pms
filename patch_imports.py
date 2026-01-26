import os

files_to_patch = [
    "app/services/data_scope/custom_rule.py",
    "app/services/permission_service.py",
    "app/services/data_scope_service_v2.py",  # Patch this too before moving it
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
