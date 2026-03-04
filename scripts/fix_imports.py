#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复导入问题
"""

import os
import re


def fix_file_imports(file_path):
    """修复单个文件的导入问题"""
    if not os.path.exists(file_path):
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 修复 common 问题
        content = content.replace(
            "from app.schemas.response import Response", "from app.schemas.common import Response"
        )

        # 修复 deps 导入问题
        content = re.sub(
            r"from app\.api import deps",
            "from app.api.deps import get_db, get_current_active_user",
            content,
        )
        content = re.sub(r"Depends\(deps\.get_db\)", "Depends(get_db)", content)
        content = re.sub(
            r"Depends\(deps\.get_current_active_user\)", "Depends(get_current_active_user)", content
        )

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"修复 {file_path} 时出错: {e}")
        return False


# 需要修复的文件列表
files_to_fix = [
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_approvals_multi.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_approvals_simple.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_cost_analysis.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_cost_approvals.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_cost_breakdown.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_cost_calculations.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_exports.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_items.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_quotes_crud.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_status.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_templates.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_versions.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quote_workflow.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/communications.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/knowledge.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/knowledge_features.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/records.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/statistics.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/survey_templates.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/surveys.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service/tickets.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_best_practices.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_costs.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_lessons.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_relations.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_resources.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_reviews.py",
    "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/projects/ext_risks.py",
]

fixed_count = 0
for file_path in files_to_fix:
    if fix_file_imports(file_path):
        fixed_count += 1
        print(f"✅ 修复: {os.path.basename(file_path)}")
    else:
        print(f"❌ 跳过: {os.path.basename(file_path)}")

print(f"\n🎉 导入修复完成! 共修复 {fixed_count} 个文件")
