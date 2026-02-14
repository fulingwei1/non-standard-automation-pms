#!/bin/bash
# API权限数据初始化脚本（简化版）

cd ~/.openclaw/workspace/non-standard-automation-pms

echo "======================================================================="
echo " API权限数据初始化工具"
echo "======================================================================="
echo

# 设置环境变量
export SECRET_KEY="dev-secret-key-for-testing"

# 检查权限状态
echo "步骤1: 检查权限数据状态..."
echo "-----------------------------------------------------------------------"

PERM_COUNT=$(sqlite3 data/app.db "SELECT COUNT(*) FROM api_permissions;" 2>/dev/null || echo "0")
MAPPING_COUNT=$(sqlite3 data/app.db "SELECT COUNT(*) FROM role_api_permissions;" 2>/dev/null || echo "0")

echo "📊 API权限记录: $PERM_COUNT 条"
echo "📊 角色权限映射: $MAPPING_COUNT 条"
echo

if [ "$PERM_COUNT" -gt "0" ] && [ "$MAPPING_COUNT" -gt "50" ]; then
    echo "✓ 权限数据已存在，无需初始化"
    echo
    
    # 显示前几条权限
    echo "权限示例:"
    sqlite3 data/app.db "SELECT perm_code, perm_name FROM api_permissions LIMIT 5;" | sed 's/|/ - /'
    
    echo
    echo "======================================================================="
    exit 0
fi

echo "⚠️  需要初始化权限数据"
echo

# 执行初始化
echo "步骤2: 执行权限数据初始化..."
echo "-----------------------------------------------------------------------"

python3 -c "
import sys
sys.path.insert(0, '.')

# 导入所有模型（避免关系错误）
from app.models.base import SessionLocal

# 简化版：直接执行SQL
db = SessionLocal()
try:
    from app.utils.init_permissions_data import init_api_permissions_data, ensure_admin_permissions
    
    result = init_api_permissions_data(db)
    
    print(f'权限记录: 新建 {result[\"permissions_created\"]} 个，已存在 {result[\"permissions_existing\"]} 个')
    print(f'角色映射: 新建 {result[\"role_mappings_created\"]} 条，已存在 {result[\"role_mappings_existing\"]} 条')
    
    if result.get('errors'):
        print(f'错误: {result[\"errors\"]}')
        sys.exit(1)
    
    # 确保ADMIN权限
    ensure_admin_permissions(db)
    print('✓ ADMIN权限检查完成')
    
except Exception as e:
    print(f'❌ 初始化失败: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
"

if [ $? -eq 0 ]; then
    echo
    echo "======================================================================="
    echo "✓ 初始化成功！"
    echo "======================================================================="
    echo
    
    # 再次检查
    PERM_COUNT=$(sqlite3 data/app.db "SELECT COUNT(*) FROM api_permissions;")
    MAPPING_COUNT=$(sqlite3 data/app.db "SELECT COUNT(*) FROM role_api_permissions;")
    
    echo "最终状态:"
    echo "  - API权限: $PERM_COUNT 条"
    echo "  - 角色映射: $MAPPING_COUNT 条"
    echo
    
    # 检查ADMIN权限
    ADMIN_PERM=$(sqlite3 data/app.db "
        SELECT COUNT(*) 
        FROM role_api_permissions rap
        JOIN roles r ON rap.role_id = r.id
        WHERE r.role_code = 'ADMIN';
    ")
    echo "  - ADMIN权限: $ADMIN_PERM 个"
    echo
else
    echo
    echo "======================================================================="
    echo "❌ 初始化失败"
    echo "======================================================================="
    echo
    exit 1
fi
