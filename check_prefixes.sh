#!/bin/bash

echo "检查所有endpoint模块的prefix定义："
echo "========================================"

for module in shortage rd_project approvals presale; do
    echo ""
    echo "=== $module ==="
    
    # 查找__init__.py
    init_file=$(find app/api/v1/endpoints -type f -path "*/${module}/__init__.py" 2>/dev/null | head -1)
    if [ -f "$init_file" ]; then
        grep -n "router = APIRouter" "$init_file" | head -3
    fi
    
    # 查找同名.py
    py_file="app/api/v1/endpoints/${module}.py"
    if [ -f "$py_file" ]; then
        grep -n "router = APIRouter" "$py_file" | head -3
    fi
    
    # 如果都没找到
    if [ ! -f "$init_file" ] && [ ! -f "$py_file" ]; then
        echo "文件不存在: ${module}/__init__.py 和 ${module}.py"
    fi
done
