# API权限自动初始化说明

**创建时间**: 2026-02-14 17:50  
**问题**: 如何初始化API权限数据？能否自动初始化？

---

## ✅ 答案：已实现自动初始化

**是的，系统已经实现了自动初始化机制！** 

每次服务启动时，会自动检查并初始化API权限数据（如果不存在的话）。

---

## 🔄 自动初始化机制

### 工作流程

```
服务启动 (app/main.py)
    ↓
触发 startup_event
    ↓
调用 init_all_data() (app/utils/init_data.py)
    ↓
调用 init_api_permissions() 
    ↓
调用 init_api_permissions_data() (新建)
    ↓
1. 检查 api_permissions 表是否为空
2. 如果为空，创建 33 个基础权限
3. 为 9 个角色分配权限
4. 确保 ADMIN 拥有所有权限
    ↓
完成（幂等，可重复执行）
```

### 初始化内容

#### 1. API权限（33个）

| 模块 | 权限数量 | 示例 |
|-----|---------|------|
| USER | 4 | user:view, user:create, user:update, user:delete |
| ROLE | 5 | role:view, role:create, role:update, role:delete, role:assign |
| PERMISSION | 2 | permission:view, permission:update |
| PROJECT | 4 | project:view, project:create, project:update, project:delete |
| OPPORTUNITY | 4 | opportunity:view, opportunity:create, opportunity:update, opportunity:delete |
| CONTRACT | 4 | contract:view, contract:create, contract:update, contract:delete |
| TASK | 4 | task:view, task:create, task:update, task:delete |
| FINANCE | 4 | finance:view, finance:create, finance:update, finance:delete |

#### 2. 角色权限映射

| 角色 | 权限数量 | 说明 |
|-----|---------|------|
| ADMIN | 33 | 所有权限 |
| GM | 11 | 总经理 - 查看所有，部分修改 |
| PM | 9 | 项目经理 - 项目和任务全权限 |
| SALES_DIR | 9 | 销售总监 - 销售相关全权限 |
| SALES | 4 | 销售专员 - 基础销售权限 |
| ENGINEER | 3 | 工程师 - 项目和任务查看 |
| ME | 3 | 机械工程师 |
| EE | 3 | 电气工程师 |
| SW | 3 | 软件工程师 |

---

## 🛠️ 手动初始化方式

虽然有自动初始化，但你也可以手动执行：

### 方式1: 使用初始化工具（推荐）✨

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms

# 1. 检查权限状态
python3 init_permissions.py --check

# 2. 自动检查并按需初始化（推荐）
python3 init_permissions.py --auto

# 3. 完整初始化
python3 init_permissions.py

# 4. 只修复ADMIN权限
python3 init_permissions.py --admin
```

### 方式2: 重启服务

```bash
# 停止服务
pkill -f "uvicorn.*main:app"

# 启动服务（自动初始化）
SECRET_KEY="dev-key" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 方式3: 直接调用Python模块

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms

SECRET_KEY="dev-key" python3 -c "
from app.utils.init_permissions_data import init_api_permissions_data, ensure_admin_permissions
from app.models.base import SessionLocal

db = SessionLocal()
try:
    # 初始化权限
    result = init_api_permissions_data(db)
    print(f'权限: +{result[\"permissions_created\"]}, 已有{result[\"permissions_existing\"]}')
    print(f'映射: +{result[\"role_mappings_created\"]}, 已有{result[\"role_mappings_existing\"]}')
    
    # 确保ADMIN权限
    ensure_admin_permissions(db)
    print('✓ 完成')
finally:
    db.close()
"
```

---

## 🔍 验证初始化是否成功

### 方法1: 使用检查工具

```bash
python3 init_permissions.py --check
```

**输出示例**:
```
======================================================================
API权限数据状态检查
======================================================================

📊 API权限记录: 33 条
   ✓ 权限数量正常

📊 角色权限映射: 150 条
   ✓ 映射数量正常

📊 ADMIN角色权限: 33 个
   ✓ ADMIN拥有所有权限

📋 权限示例（前10个）:
   - user:view: 查看用户
   - user:create: 创建用户
   - user:update: 编辑用户
   ...

✓ 权限数据状态正常
```

### 方法2: 查询数据库

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms

sqlite3 data/app.db "
SELECT 'API权限', COUNT(*) FROM api_permissions
UNION ALL
SELECT '角色映射', COUNT(*) FROM role_api_permissions;
"
```

**期望输出**:
```
API权限|33
角色映射|150+
```

### 方法3: 测试管理员访问

```bash
# 1. 登录
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  | python3 -c "import json, sys; print(json.load(sys.stdin)['access_token'])")

# 2. 测试访问用户列表
curl -H "Authorization: Bearer $TOKEN" \
  http://127.0.0.1:8000/api/v1/users

# 期望: 200 + 用户列表 JSON
# 如果返回 403，说明权限未初始化
```

---

## 📋 初始化文件清单

| 文件 | 作用 | 说明 |
|-----|------|------|
| `app/utils/init_permissions_data.py` | 权限数据定义 | 内嵌33个权限，9个角色映射 |
| `app/utils/init_data.py` | 初始化入口 | 调用权限初始化 |
| `app/main.py` | 自动触发 | 启动时调用init_all_data() |
| `init_permissions.py` | 手动工具 | 独立初始化脚本 |

---

## ⚙️ 幂等性保证

**所有初始化函数都是幂等的**，可以安全地重复执行：

### 检查逻辑

```python
# 1. 检查权限是否存在
existing = db.query(ApiPermission).filter(
    ApiPermission.perm_code == "user:view"
).first()

if existing:
    # 已存在，跳过
    return existing
else:
    # 不存在，创建
    create_permission(...)

# 2. 检查映射是否存在
existing_mapping = db.query(RoleApiPermission).filter(
    RoleApiPermission.role_id == role.id,
    RoleApiPermission.permission_id == perm.id
).first()

if not existing_mapping:
    # 不存在，创建映射
    create_mapping(...)
```

### 安全性

- ✅ 不会重复创建权限
- ✅ 不会重复创建映射
- ✅ 可以多次运行修复数据
- ✅ 不会影响已有数据

---

## 🐛 故障排除

### 问题1: 服务启动时没有自动初始化

**检查**:
```bash
# 查看启动日志
tail -100 server.log | grep -i "init\|permission"
```

**可能原因**:
1. SECRET_KEY未设置（阻止服务启动）
2. 数据库连接失败
3. 初始化函数抛出异常

**解决**:
```bash
# 手动运行初始化
python3 init_permissions.py --auto
```

---

### 问题2: ADMIN仍然返回403

**检查ADMIN权限**:
```bash
python3 init_permissions.py --check
```

**如果ADMIN权限不完整**:
```bash
# 修复ADMIN权限
python3 init_permissions.py --admin
```

**重启服务**:
```bash
pkill -f "uvicorn.*main:app"
SECRET_KEY="dev-key" nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > server.log 2>&1 &
```

---

### 问题3: 权限数量不对

**预期数量**:
- API权限: 33 个
- 角色映射: 150+ 条（9个角色 × 各自权限）

**如果数量少于预期**:
```bash
# 重新初始化（幂等，安全）
python3 init_permissions.py
```

---

## 📈 扩展权限

如果需要添加新权限，修改 `app/utils/init_permissions_data.py`:

```python
API_PERMISSIONS = [
    # ... 现有权限 ...
    
    # 添加新权限
    {"perm_code": "new:view", "perm_name": "查看新功能", "module": "NEW", "action": "VIEW"},
]

ROLE_PERMISSIONS_MAPPING = {
    "ADMIN": [p["perm_code"] for p in API_PERMISSIONS],  # ADMIN自动获得所有权限
    
    "PM": [
        # ... 现有权限 ...
        "new:view",  # 给PM添加新权限
    ],
}
```

**重新初始化**:
```bash
python3 init_permissions.py
```

---

## ✅ 总结

### 自动初始化 ✨
- ✅ **服务启动时自动执行**
- ✅ **幂等设计，可重复运行**
- ✅ **不依赖外部SQL文件**
- ✅ **包含33个基础权限**
- ✅ **为9个角色分配权限**
- ✅ **确保ADMIN拥有所有权限**

### 手动初始化工具
```bash
# 推荐：自动检查并按需初始化
python3 init_permissions.py --auto

# 检查状态
python3 init_permissions.py --check

# 修复ADMIN权限
python3 init_permissions.py --admin
```

### 验证方法
1. 运行检查工具：`python3 init_permissions.py --check`
2. 测试管理员登录和API访问
3. 查询数据库确认记录数量

---

**文档创建**: 2026-02-14 17:55  
**工具位置**: `init_permissions.py`  
**数据定义**: `app/utils/init_permissions_data.py`
