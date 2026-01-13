# 角色配置迁移指南

## 概述

本文档说明如何将硬编码的角色配置迁移到数据库，实现动态配置管理。

## 已完成的工作

### 1. 数据库模型扩展

在 `app/models/user.py` 中，`Role` 模型已添加以下字段：

```python
nav_groups = Column(JSON, comment="导航组配置（JSON数组）")
ui_config = Column(JSON, comment="UI配置（JSON对象，包含导航、权限等前端配置）")
```

### 2. API 端点

新增端点：`GET /api/v1/roles/config/all`

**响应格式**：
```json
{
  "roles": {
    "pm": {
      "name": "项目经理",
      "dataScope": "project",
      "description": "项目全生命周期管理、进度把控、客户对接",
      "navGroups": ["overview", "project", "operation", "quality", "personal"],
      "uiConfig": {
        "focusStages": [],
        "dashboard": "project_manager"
      }
    },
    ...
  }
}
```

### 3. 数据库迁移

执行迁移脚本：
```bash
# SQLite
sqlite3 data/app.db < migrations/20260106_add_role_ui_config.sql

# MySQL
mysql -u user -p database < migrations/20260106_add_role_ui_config.sql
```

## 前端迁移步骤

### 步骤 1: 创建角色配置服务

在 `frontend/src/services/roleConfigService.js` 中创建服务：

```javascript
import api from './api'

let cachedRoleConfig = null

export async function fetchRoleConfig() {
  if (cachedRoleConfig) {
    return cachedRoleConfig
  }
  
  try {
    const response = await api.get('/api/v1/roles/config/all')
    cachedRoleConfig = response.data.roles
    return cachedRoleConfig
  } catch (error) {
    console.error('Failed to fetch role config:', error)
    // Fallback to default config
    return getDefaultRoleConfig()
  }
}

export function getDefaultRoleConfig() {
  // 从 roleConfig.js 导入默认配置
  return require('../lib/roleConfig').ROLE_DEFINITIONS
}

export function clearRoleConfigCache() {
  cachedRoleConfig = null
}
```

### 步骤 2: 修改 roleConfig.js

修改 `frontend/src/lib/roleConfig.js`：

```javascript
import { fetchRoleConfig, getDefaultRoleConfig } from '../services/roleConfigService'

// 保留默认配置作为 fallback
export const DEFAULT_ROLE_DEFINITIONS = { ... }

// 动态加载角色配置
let roleDefinitions = null

export async function loadRoleConfig() {
  if (!roleDefinitions) {
    try {
      const config = await fetchRoleConfig()
      roleDefinitions = config
    } catch (error) {
      console.warn('Using default role config:', error)
      roleDefinitions = DEFAULT_ROLE_DEFINITIONS
    }
  }
  return roleDefinitions
}

// 同步获取（使用缓存或默认值）
export function getRoleDefinitions() {
  return roleDefinitions || DEFAULT_ROLE_DEFINITIONS
}
```

### 步骤 3: 在应用启动时加载配置

在 `frontend/src/App.jsx` 或入口文件中：

```javascript
import { loadRoleConfig } from './lib/roleConfig'

// 在应用启动时加载配置
useEffect(() => {
  loadRoleConfig().then(() => {
    // 配置加载完成，可以渲染应用
  })
}, [])
```

### 步骤 4: 更新使用角色配置的组件

将所有直接使用 `ROLE_DEFINITIONS` 的地方改为使用 `getRoleDefinitions()`：

```javascript
// 之前
import { ROLE_DEFINITIONS } from '../lib/roleConfig'
const roleConfig = ROLE_DEFINITIONS[roleCode]

// 之后
import { getRoleDefinitions } from '../lib/roleConfig'
const roleConfig = getRoleDefinitions()[roleCode]
```

## 数据迁移

### 将现有配置导入数据库

创建脚本 `scripts/migrate_role_config.py`：

```python
import json
from app.models.user import Role
from app.core.database import SessionLocal

# 从 roleConfig.js 提取的配置
ROLE_CONFIGS = {
    "pm": {
        "nav_groups": ["overview", "project", "operation", "quality", "personal"],
        "ui_config": {}
    },
    # ... 其他角色配置
}

def migrate_role_configs():
    db = SessionLocal()
    try:
        for role_code, config in ROLE_CONFIGS.items():
            role = db.query(Role).filter(Role.role_code == role_code).first()
            if role:
                role.nav_groups = config.get("nav_groups", [])
                role.ui_config = config.get("ui_config", {})
                db.add(role)
        db.commit()
        print("Role configs migrated successfully")
    except Exception as e:
        db.rollback()
        print(f"Error migrating role configs: {e}")
    finally:
        db.close()
```

## 角色管理界面增强

在角色管理页面添加配置编辑功能：

1. **导航组配置**：多选下拉框，选择该角色可见的导航组
2. **UI 配置**：JSON 编辑器，编辑 UI 相关配置
3. **配置预览**：实时预览配置效果

## 向后兼容性

- 如果数据库中没有配置，使用默认配置（`roleConfig.js`）
- 如果 API 调用失败，回退到默认配置
- 保留 `roleConfig.js` 作为默认配置源

## 测试建议

1. **单元测试**：测试配置加载和 fallback 逻辑
2. **集成测试**：测试 API 端点和前端配置加载
3. **性能测试**：确保配置加载不影响应用启动速度
4. **兼容性测试**：确保现有功能不受影响

## 注意事项

1. **缓存策略**：角色配置变化不频繁，可以缓存较长时间
2. **权限控制**：配置 API 需要适当的权限验证
3. **数据验证**：确保从数据库加载的配置格式正确
4. **错误处理**：API 失败时要有合理的 fallback 机制


