#!/usr/bin/env python3
"""
Batch fix skip/limit Query params -> get_pagination_query
"""
import re

files = [
    "app/api/v1/endpoints/projects/ext_lessons.py",
    "app/api/v1/endpoints/projects/ext_resources.py",
    "app/api/v1/endpoints/projects/ext_reviews.py",
    "app/api/v1/endpoints/projects/ext_risks.py",
    "app/api/v1/endpoints/projects/pipeline.py",
    "app/api/v1/endpoints/projects/work_logs/crud.py",
    "app/api/v1/endpoints/sales/quote_items.py",
    "app/api/v1/endpoints/sales/quote_templates.py",
    "app/api/v1/endpoints/staff_matching/evaluations.py",
    "app/api/v1/endpoints/staff_matching/performance.py",
    "app/api/v1/endpoints/staff_matching/profiles.py",
    "app/api/v1/endpoints/staff_matching/staffing_needs.py",
    "app/api/v1/endpoints/staff_matching/tags.py",
    "app/api/v1/endpoints/strategy/annual_work.py",
    "app/api/v1/endpoints/strategy/comparison.py",
    "app/api/v1/endpoints/strategy/csf.py",
    "app/api/v1/endpoints/strategy/decomposition.py",
    "app/api/v1/endpoints/strategy/kpi.py",
    "app/api/v1/endpoints/strategy/review.py",
    "app/api/v1/endpoints/strategy/strategy.py",
    "app/api/v1/endpoints/analytics/resource_conflicts.py",
    "app/api/v1/endpoints/pitfalls/crud_refactored.py",
]

IMPORT_LINE = "from app.common.pagination import PaginationParams, get_pagination_query"

# Pattern to match skip/limit Query params  
SKIP_LIMIT_PATTERN = re.compile(
    r'(\s+)skip:\s*int\s*=\s*Query\([^)]*\),?\s*\n\s*limit:\s*int\s*=\s*Query\([^)]*\),?\s*\n'
)

count = 0
for filepath in files:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"SKIP (not found): {filepath}")
        continue
    
    original = content
    
    # Add import if not present
    if "get_pagination_query" not in content:
        # Find a good place to add import - after existing app imports
        # Try to insert after "from app." imports
        lines = content.split('\n')
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith('from app.') or line.startswith('from app '):
                insert_idx = i
        if insert_idx is not None:
            lines.insert(insert_idx + 1, IMPORT_LINE)
            content = '\n'.join(lines)
        else:
            # Insert after last import
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_idx = i
            if insert_idx:
                lines.insert(insert_idx + 1, IMPORT_LINE)
                content = '\n'.join(lines)
    elif "PaginationParams" not in content:
        content = content.replace(
            "from app.common.pagination import get_pagination_query",
            IMPORT_LINE
        )
    
    # Replace skip/limit Query params with pagination: PaginationParams = Depends(get_pagination_query)
    def replace_skip_limit(match):
        indent = match.group(1)
        return f'{indent}pagination: PaginationParams = Depends(get_pagination_query),\n'
    
    content = SKIP_LIMIT_PATTERN.sub(replace_skip_limit, content)
    
    # Replace usages of skip and limit with pagination.offset and pagination.limit
    # Common patterns: skip=skip -> skip=pagination.offset, limit=limit -> limit=pagination.limit
    content = re.sub(r'\bskip=skip\b', 'skip=pagination.offset', content)
    content = re.sub(r'\blimit=limit\b', 'limit=pagination.limit', content)
    # Also handle direct .offset(skip) and .limit(limit)
    content = re.sub(r'\.offset\(skip\)', '.offset(pagination.offset)', content)
    content = re.sub(r'\.limit\(limit\)', '.limit(pagination.limit)', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        changes = original.count('skip: int = Query') + original.count('skip: int=Query')
        count += changes
        print(f"FIXED ({changes} occurrences): {filepath}")
    else:
        print(f"NO CHANGE: {filepath}")

print(f"\nTotal files with skip/limit pattern fixes: {count}")
