#!/bin/bash
# 快速修复API测试中发现的问题

set -e

echo "================================"
echo "API错误快速修复脚本"
echo "================================"
echo ""

# 1. 检查数据库模式
echo "1. 检查数据库模式..."
if [ -f "data/pms.db" ]; then
    echo "✓ 数据库文件存在"
    
    # 检查projects表结构
    echo ""
    echo "Projects表当前结构:"
    sqlite3 data/pms.db ".schema projects" 2>/dev/null || echo "❌ Projects表不存在或无法访问"
    echo ""
else
    echo "❌ 数据库文件不存在: data/pms.db"
fi

# 2. 检查迁移状态
echo "2. 检查数据库迁移状态..."
if [ -d "migrations" ]; then
    echo "✓ migrations目录存在"
    
    # 显示最新的迁移文件
    echo ""
    echo "最近的迁移文件:"
    ls -lt migrations/versions/*.py 2>/dev/null | head -5 || echo "没有迁移文件"
    echo ""
else
    echo "❌ migrations目录不存在"
fi

# 3. 检查API路由文件
echo "3. 检查API路由文件..."
echo ""

# 检查生产管理路由
if [ -d "app/api/v1/endpoints/production" ]; then
    echo "✓ 生产管理路由目录存在"
    ls -la app/api/v1/endpoints/production/ 2>/dev/null | grep ".py$" || echo "  但是没有Python文件"
else
    echo "❌ 生产管理路由目录不存在: app/api/v1/endpoints/production"
fi

# 检查销售管理路由
if [ -d "app/api/v1/endpoints/sales" ]; then
    echo "✓ 销售管理路由目录存在"
    echo "  文件列表:"
    ls app/api/v1/endpoints/sales/*.py 2>/dev/null | head -10
else
    echo "❌ 销售管理路由目录不存在: app/api/v1/endpoints/sales"
fi
echo ""

# 4. 检查权限API路由
echo "4. 检查权限API路由..."
if grep -r "permissions" app/api/v1/ --include="*.py" | grep -q "router"; then
    echo "✓ 找到permissions相关路由定义"
    echo "  位置:"
    grep -r "permissions" app/api/v1/ --include="*.py" -l | head -5
else
    echo "❌ 未找到permissions路由定义"
fi
echo ""

# 5. 检查路由注册
echo "5. 检查路由注册（app/api/v1/__init__.py）..."
if [ -f "app/api/v1/__init__.py" ]; then
    echo "✓ 路由注册文件存在"
    echo ""
    echo "已注册的路由:"
    grep "include_router\|router.include" app/api/v1/__init__.py 2>/dev/null | head -20
else
    echo "❌ 路由注册文件不存在"
fi
echo ""

# 6. 生成修复建议
echo "================================"
echo "修复建议"
echo "================================"
echo ""

echo "🔴 P0 - 立即修复:"
echo ""
echo "1. 数据库模式修复"
echo "   如果projects表缺少customer_address列:"
echo "   方案A: 运行迁移"
echo "     alembic upgrade head"
echo ""
echo "   方案B: 从模型中移除该字段"
echo "     编辑 app/models/project.py"
echo "     注释或删除 customer_address 字段"
echo ""
echo "2. 检查是否有未应用的迁移"
echo "     alembic current"
echo "     alembic history"
echo ""

echo "🟡 P1 - 今日完成:"
echo ""
echo "1. 确认API路径"
echo "   检查实际的API定义与测试脚本是否匹配"
echo ""
echo "2. 注册缺失的路由"
echo "   如果功能已实现但未注册，添加到 app/api/v1/__init__.py"
echo ""

echo "🟢 P2 - 本周完成:"
echo ""
echo "1. 修复所有500错误"
echo "   启用详细日志，逐个分析错误原因"
echo ""
echo "2. 补全API测试覆盖率"
echo "   扩展测试脚本，覆盖更多API"
echo ""

echo "================================"
echo "✅ 检查完成"
echo "================================"
