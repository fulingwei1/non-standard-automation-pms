#!/bin/bash
# 角色继承功能测试脚本

export ENVIRONMENT=development
export SECRET_KEY=test_secret_key_for_role_inheritance_testing
export SQLITE_DB_PATH=:memory:

cd ~/.openclaw/workspace/non-standard-automation-pms

echo "🧪 运行角色继承测试..."
echo "================================"

python3 -m pytest tests/test_role_inheritance.py -v --tb=short --no-header

echo ""
echo "================================"
echo "✅ 测试完成！"
