import os

files = [
    "app/api/v1/endpoints/timesheet/records.py",
    "app/api/v1/endpoints/timesheet/pending.py",
    "app/api/v1/endpoints/timesheet/reports.py",
    "app/api/v1/endpoints/timesheet/approval.py",
    "app/api/v1/endpoints/timesheet/statistics.py",
    "app/api/v1/endpoints/timesheet/monthly.py",
]

base_dir = "/Users/flw/non-standard-automation-pm"

import_line = (
    "from app.core.permissions.timesheet import check_timesheet_approval_permission\n"
)


def patch_file(filepath):
    abs_path = os.path.join(base_dir, filepath)
    with open(abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Target content to replace
    target_start = "def check_timesheet_approval_permission("
    target_end = "    return False"

    if target_start in content:
        start_idx = content.find(target_start)
        # Find the next 'return False' after the function definition
        end_idx = content.find(target_end, start_idx)
        if end_idx != -1:
            end_idx += len(target_end)
            new_content = content[:start_idx] + import_line + content[end_idx:]
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Patched {filepath}")
        else:
            print(f"Could not find end of function in {filepath}")
    else:
        print(f"Could not find function in {filepath}")


for f in files:
    patch_file(f)
