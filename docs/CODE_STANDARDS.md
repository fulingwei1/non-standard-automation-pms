# 代码规范文档

## 📋 概述

本文档定义了项目的代码质量标准，所有开发人员必须遵守这些规范以确保代码的一致性、可维护性和可读性。

---

## 🎯 核心原则

### 1. 单一职责原则 (SRP)

- 每个文件、类、函数只做一件事
- 文件行数不超过 **500行**
- 函数行数不超过 **50行**

### 2. 开放封闭原则 (OCP)

- 对扩展开放，对修改封闭
- 使用配置和组合而非硬编码

### 3. 依赖倒置原则 (DIP)

- 依赖抽象而非具体实现
- 使用依赖注入

---

## 📏 文件大小限制

| 类型 | 最大行数 | 最大大小 |
|------|----------|----------|
| Python 文件 | 500行 | 50KB |
| JavaScript/JSX 文件 | 500行 | 50KB |
| CSS/SCSS 文件 | 300行 | 30KB |
| 配置文件 | 200行 | 20KB |
| 测试文件 | 800行 | 80KB |

### 超出限制时的处理

如果文件超出限制，必须进行重构：

1. 拆分为多个模块
2. 提取公共逻辑到工具类/Hooks
3. 分离配置到独立文件

---

## 🐍 Python 代码规范

### 文件结构

```python
# -*- coding: utf-8 -*-
"""
模块说明

详细描述模块的功能和用途
"""

# 标准库导入
import os
import sys

# 第三方库导入
from fastapi import APIRouter
from pydantic import BaseModel

# 本地模块导入
from app.core import config
from app.models import User

# 常量定义
MAX_RETRY_COUNT = 3

# 类和函数定义
class MyService:
    """服务类说明"""
    pass
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `user_service.py` |
| 类 | PascalCase | `UserService` |
| 函数 | snake_case | `get_user_by_id` |
| 变量 | snake_case | `user_count` |
| 常量 | UPPER_SNAKE_CASE | `MAX_CONNECTIONS` |
| 私有成员 | _前缀 | `_internal_method` |

### 函数规范

```python
def calculate_discount(
    price: float,
    discount_rate: float,
    max_discount: float = 100.0
) -> float:
    """
    计算折扣后的价格
    
    Args:
        price: 原价
        discount_rate: 折扣率 (0-1)
        max_discount: 最大折扣金额
    
    Returns:
        折扣后的价格
    
    Raises:
        ValueError: 当折扣率不在有效范围内时
    """
    if not 0 <= discount_rate <= 1:
        raise ValueError(f"折扣率必须在0-1之间: {discount_rate}")
    
    discount = min(price * discount_rate, max_discount)
    return price - discount
```

### 类规范

```python
class UserService:
    """
    用户服务类
    
    处理用户相关的业务逻辑
    
    Attributes:
        db: 数据库会话
        cache: 缓存客户端
    """
    
    def __init__(self, db: Session, cache: CacheClient):
        self.db = db
        self.cache = cache
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户信息"""
        # 先查缓存
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        
        # 查数据库
        user = self.db.query(User).get(user_id)
        if user:
            self.cache.set(f"user:{user_id}", user)
        
        return user
```

---

## ⚛️ JavaScript/React 代码规范

### 文件结构

```javascript
/**
 * 组件说明
 * 
 * @description 详细描述组件的功能和用途
 */

// 第三方库导入
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// UI组件导入
import { Button, Input } from '../components/ui';

// Hooks导入
import { useTaskData } from '../hooks';

// 工具函数导入
import { formatDate, cn } from '../lib/utils';

// 常量
const MAX_ITEMS = 50;

// 组件定义
export function MyComponent({ prop1, prop2 }) {
  // ...
}
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase.jsx | `TaskCard.jsx` |
| Hook文件 | camelCase.js | `useTaskData.js` |
| 工具文件 | camelCase.js | `formatUtils.js` |
| 常量文件 | camelCase.js | `constants.js` |
| 组件 | PascalCase | `TaskCard` |
| 函数 | camelCase | `handleSubmit` |
| 变量 | camelCase | `userName` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY` |
| CSS类 | kebab-case | `task-card` |

### 组件规范

```jsx
/**
 * 任务卡片组件
 * 
 * @param {Object} props
 * @param {Object} props.task - 任务数据
 * @param {Function} props.onStatusChange - 状态变更回调
 */
export function TaskCard({ task, onStatusChange }) {
  // 1. Hooks声明
  const [expanded, setExpanded] = useState(false);
  const taskData = useTaskData(task.id);
  
  // 2. 派生状态
  const isOverdue = new Date(task.dueDate) < new Date();
  
  // 3. 事件处理函数
  const handleClick = useCallback(() => {
    setExpanded(!expanded);
  }, [expanded]);
  
  // 4. 副作用
  useEffect(() => {
    taskData.load();
  }, [taskData.load]);
  
  // 5. 渲染
  return (
    <div className="task-card">
      <h3>{task.title}</h3>
      {/* ... */}
    </div>
  );
}

// PropTypes 或 TypeScript 类型定义
TaskCard.propTypes = {
  task: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  }).isRequired,
  onStatusChange: PropTypes.func,
};
```

### 自定义Hook规范

```javascript
/**
 * 任务数据管理Hook
 * 
 * @param {Object} filters - 过滤参数
 * @returns {Object} 任务数据和操作函数
 */
export function useTaskData(filters = {}) {
  // 状态
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // 加载数据
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await taskApi.list(filters);
      setTasks(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);
  
  // 副作用
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);
  
  // 返回值
  return {
    tasks,
    loading,
    error,
    loadTasks,
    // 其他操作...
  };
}
```

---

## 📁 目录结构规范

### 后端 (Python)

```
app/
├── api/
│   └── v1/
│       └── endpoints/
│           └── module_name/          # 模块目录
│               ├── __init__.py
│               ├── router.py         # 路由定义
│               ├── views.py          # 视图函数
│               └── schemas.py        # 请求/响应模型
├── core/                             # 核心配置
├── models/                           # 数据模型
│   └── exports/                      # 分组导出
├── services/                         # 业务逻辑
│   └── module_name/
│       ├── __init__.py
│       ├── service.py
│       └── utils.py
└── utils/                            # 工具函数
```

### 前端 (React)

```
src/
├── components/
│   ├── ui/                           # 基础UI组件
│   └── common/                       # 通用业务组件
├── hooks/                            # 全局通用Hooks
│   ├── index.js
│   ├── useApi.js
│   └── useLocalStorage.js
├── lib/                              # 工具库
├── pages/
│   └── ModuleName/                   # 页面模块
│       ├── index.jsx                 # 主组件
│       ├── constants.js              # 常量配置
│       ├── components/               # 子组件
│       │   ├── index.js
│       │   └── SubComponent.jsx
│       └── hooks/                    # 模块专用Hooks
│           ├── index.js
│           └── useModuleData.js
└── services/                         # API服务
```

---

## 🚫 禁止事项

### 绝对禁止

1. ❌ 硬编码敏感信息（密码、API密钥等）
2. ❌ 未处理的异常和Promise rejection
3. ❌ 直接操作DOM（React中）
4. ❌ 魔法数字（使用常量代替）
5. ❌ 超过3层的嵌套

### 强烈不建议

1. ⚠️ 单文件超过500行
2. ⚠️ 函数超过50行
3. ⚠️ 超过5个参数的函数
4. ⚠️ 重复代码（提取为函数/组件）
5. ⚠️ 注释掉的代码

---

## ✅ 代码审查检查清单

### 功能性

- [ ] 代码是否实现了预期功能？
- [ ] 边界情况是否处理？
- [ ] 错误处理是否完善？

### 可读性

- [ ] 命名是否清晰明确？
- [ ] 注释是否必要且准确？
- [ ] 代码结构是否清晰？

### 可维护性

- [ ] 是否符合单一职责原则？
- [ ] 是否有重复代码？
- [ ] 是否容易测试？

### 性能

- [ ] 是否有不必要的计算？
- [ ] 是否有内存泄漏风险？
- [ ] API调用是否合理？

### 安全性

- [ ] 是否有XSS风险？
- [ ] 是否有SQL注入风险？
- [ ] 敏感数据是否加密？

---

## 📝 Git 提交规范

### 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档更新 |
| style | 代码格式调整 |
| refactor | 重构 |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具变更 |

### 示例

```
feat(task-center): 添加任务筛选功能

- 添加按状态筛选
- 添加关键词搜索
- 优化列表性能

Closes #123
```

---

## 🔧 工具配置

### ESLint (前端)

详见 `.eslintrc.js`

### Pylint (后端)

详见 `.pylintrc`

### Prettier (前端)

详见 `.prettierrc`

### Pre-commit Hooks

详见 `.pre-commit-config.yaml`

---

## 📚 参考资源

- [Python PEP 8](https://pep8.org/)
- [React 官方文档](https://react.dev/)
- [Clean Code 原则](https://github.com/ryanmcdermott/clean-code-javascript)
- [Git Commit 规范](https://www.conventionalcommits.org/)

---

*最后更新: 2026-01-20*
