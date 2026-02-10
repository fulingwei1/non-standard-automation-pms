#!/usr/bin/env python3
"""Fix the import in labor_cost_service.py"""
import sys

TARGET = "/Users/flw/non-standard-automation-pm/app/services/labor_cost_service.py"

with open(TARGET, "r") as f:
  content = f.read()

# Show actual content of lines 72-78 for debugging
lines = content.split("\n")
print("Current lines 72-78:")
for i in range(71, min(78, len(lines))):
 print(f" Line {i+1}: {repr(lines[i])}")

# Replace the import block
old_import = (
 "  from app.services.labor_cost.utils import (\n"
 "  delete_existing_costs,\n"
  "   group_timesheets_by_user,\n"
  "   query_approved_timesheets,\n"
  "  )\n"
  "  from app.services.labor_cost_calculation_service import process_user_costs"
)

new_import = (
 "  from app.services.labor_cost.utils import (\n"
  "  delete_existing_costs,\n"
 "   group_timesheets_by_user,\n"
  "   process_user_costs,\n"
 "  query_approved_timesheets,\n"
 " )"
)

if old_import in content:
  content = content.replace(old_import, new_import)
 with open(TARGET, "w") as f:
  f.write(content)
 print("\nOK: import replaced successfully")
else:
 print("\nERROR: old import string not found in file")
 sys.exit(1)
