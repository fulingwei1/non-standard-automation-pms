#!/bin/bash

echo "修复timesheet子模块的双重prefix问题"
echo "========================================"

# 需要修复的文件
files=(
    "app/api/v1/endpoints/timesheet/records.py"
    "app/api/v1/endpoints/timesheet/pending.py"
    "app/api/v1/endpoints/timesheet/monthly.py"
    "app/api/v1/endpoints/timesheet/statistics.py"
    "app/api/v1/endpoints/timesheet/weekly.py"
    "app/api/v1/endpoints/timesheet/workflow.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo ""
        echo "修复: $file"
        
        # 备份
        cp "$file" "${file}.bak"
        
        # 移除 /timesheet/ 前缀
        sed -i '' 's|prefix="/timesheet/\([^"]*\)"|prefix="/\1"|g' "$file"
        sed -i '' 's|prefix="/timesheets"|prefix="/weekly"|g' "$file"
        
        # 显示修改
        echo "修改前:"
        grep "router = APIRouter(prefix=" "${file}.bak" | head -1
        echo "修改后:"
        grep "router = APIRouter(prefix=" "$file" | head -1
    else
        echo "⚠️  文件不存在: $file"
    fi
done

echo ""
echo "✅ 修复完成"
