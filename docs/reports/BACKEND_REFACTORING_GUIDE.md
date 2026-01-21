# 后端代码拆分重构指南

## 📊 当前状态

### 已识别的大文件

| 文件 | 行数 | 复杂度 | 拆分优先级 | 状态 |
|------|------|--------|-----------|------|
| `utils/scheduled_tasks.py` | 3845 | 高 | P0 | 🔄 进行中 |
| `api/v1/endpoints/projects/extended.py` | 2476 | 高 | P0 | ⏳ 待处理 |
| `api/v1/endpoints/acceptance.py` | 2472 | 高 | P0 | ⏳ 待处理 |
| `api/v1/endpoints/issues.py` | 2408 | 高 | P1 | ⏳ 待处理 |
| `api/v1/endpoints/alerts.py` | 2232 | 中 | P1 | ⏳ 待处理 |
| `api/v1/endpoints/service.py` | 2208 | 中 | P1 | ⏳ 待处理 |

## 🎯 拆分策略

### 策略1：定时任务模块化（scheduled_tasks.py）

#### 当前结构
```
app/utils/scheduled_tasks.py (3845行，38个函数)
```

#### 目标结构
```
app/utils/scheduled_tasks/
├── __init__.py              # 统一导出
├── base.py                  # 基类和工具函数
├── project.py               # 项目健康度、里程碑、问题 (8个函数)
├── production.py            # 生产、齐套、交付 (7个函数)
├── timesheet.py             # 工时提醒和汇总 (10个函数)
├── sales.py                 # 销售收款和商机 (5个函数)
├── alerts.py                # 预警和超时检查 (5个函数)
├── notification.py          # 通知发送和重试 (4个函数)
└── maintenance.py           # 设备、合同、员工提醒 (3个函数)
```

#### 实施步骤

**步骤1：创建目录结构**
```bash
mkdir -p app/utils/scheduled_tasks
cd app/utils/scheduled_tasks
touch __init__.py base.py project.py production.py timesheet.py
touch sales.py alerts.py notification.py maintenance.py
```

**步骤2：提取公共导入和工具函数到 base.py**
```python
# base.py 应该包含：
# - 所有import语句
# - logger配置
# - send_notification_for_alert 辅助函数
```

**步骤3：按功能域提取函数**

使用以下命令提取函数：
```bash
# 提取项目相关函数 (行201-830)
sed -n '201,830p' app/utils/scheduled_tasks.py > temp_project.txt

# 提取生产相关函数 (行1118-1702)
sed -n '1118,1702p' app/utils/scheduled_tasks.py > temp_production.txt

# 提取工时相关函数 (行2478-2795)
sed -n '2478,2795p' app/utils/scheduled_tasks.py > temp_timesheet.txt
```

**步骤4：为每个模块创建文件**

每个模块文件的结构：
```python
# -*- coding: utf-8 -*-
"""
定时任务 - XXX 模块
"""
import logging
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.base import get_db_session
from app.models.project import Project
# ... 其他必要的导入

logger = logging.getLogger(__name__)

# ==================== XXX 定时任务 ====================

def task_function_1():
    """任务1的描述"""
    # 从原文件复制实现
    pass

def task_function_2():
    """任务2的描述"""
    # 从原文件复制实现
    pass
```

**步骤5：创建统一导出的 __init__.py**

```python
# -*- coding: utf-8 -*-
"""
定时任务模块统一导出

拆分后仍保持原有的导入方式，确保向后兼容
"""

# 项目相关
from app.utils.scheduled_tasks.project import (
    calculate_project_health,
    daily_health_snapshot,
    check_overdue_issues,
    check_blocking_issues,
    daily_issue_statistics_snapshot,
    check_milestone_alerts,
    check_milestone_status_and_adjust_payments,
    check_issue_timeout_escalation,
)

# 生产相关
from app.utils.scheduled_tasks.production import (
    check_task_delay_alerts,
    check_production_plan_alerts,
    check_work_report_timeout,
    daily_kit_check,
    check_delivery_delay,
    generate_production_daily_reports,
)

# ... 其他模块的导入

# 导出所有函数
__all__ = [
    'calculate_project_health',
    'daily_health_snapshot',
    # ... 所有38个函数名
]
```

**步骤6：更新导入引用**

查找所有引用 scheduled_tasks 的地方：
```bash
# 查找直接导入函数的地方
grep -r "from app.utils.scheduled_tasks import" app/ --include="*.py"

# 查找调用函数的地方
grep -r "calculate_project_health\|daily_health_snapshot" app/ --include="*.py"
```

**步骤7：测试验证**

```python
# 测试脚本 test_scheduled_tasks_refactor.py
def test_imports():
    """测试所有导入是否正常"""
    from app.utils.scheduled_tasks import (
        calculate_project_health,
        daily_health_snapshot,
        # ... 所有函数
    )
    assert callable(calculate_project_health)
    assert callable(daily_health_snapshot)
    print("✅ 所有导入测试通过")

def test_functionality():
    """测试功能是否正常"""
    from app.utils.scheduled_tasks import calculate_project_health
    # 测试实际功能
    result = calculate_project_health()
    assert result is not None
    print("✅ 功能测试通过")
```

### 策略2：API端点模块化

#### 目标结构（以acceptance.py为例）

**拆分前**：
```
app/api/v1/endpoints/acceptance.py (2472行)
```

**拆分后**：
```
app/api/v1/endpoints/acceptance/
├── __init__.py              # 路由聚合
├── templates.py             # 模板管理 CRUD
├── orders.py                # 验收单 CRUD
├── check_items.py           # 检查项管理
├── issues.py                # 问题管理
├── approvals.py             # 审批流程
└── reports.py               # 报告生成
```

#### 实施步骤

**步骤1：创建子路由包**
```bash
mkdir -p app/api/v1/endpoints/acceptance
cd app/api/v1/endpoints/acceptance
touch __init__.py templates.py orders.py check_items.py issues.py approvals.py reports.py
```

**步骤2：拆分路由到子文件**

原文件结构：
```python
# acceptance.py
router = APIRouter()

@router.get("/templates")
async def list_templates():
    pass

@router.post("/templates")
async def create_template():
    pass

# ... 50+ 个路由
```

拆分后：
```python
# templates.py
from fastapi import APIRouter
from sqlalchemy.orm import Session

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("")
async def list_templates(db: Session = Depends(get_db)):
    """获取模板列表"""
    pass

@router.post("")
async def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    """创建模板"""
    pass
```

```python
# __init__.py (路由聚合)
from fastapi import APIRouter
from .templates import router as templates_router
from .orders import router as orders_router
from .check_items import router as check_items_router

router = APIRouter(prefix="/acceptance", tags=["acceptance"])

# 聚合子路由
router.include_router(templates_router)
router.include_router(orders_router)
router.include_router(check_items_router)
```

**步骤3：更新API注册**

```python
# app/api/v1/api.py
from app.api.v1.endpoints import acceptance

# 旧方式
# api_router.include_router(acceptance.router, prefix="/acceptance", tags=["acceptance"])

# 新方式 - 不需要修改！
api_router.include_router(acceptance.router, prefix="/acceptance", tags=["acceptance"])
```

### 策略3：Schema和Model拆分

#### 目标结构

**拆分前**：
```
app/schemas/sales.py (1888行)
app/models/sales.py (1443行)
```

**拆分后**：
```
app/schemas/sales/
├── __init__.py
├── lead.py                  # 线索
├── opportunity.py           # 商机
├── quote.py                 # 报价
├── contract.py              # 合同
├── invoice.py               # 发票
└── payment.py               # 收款

app/models/sales/
├── __init__.py
├── lead.py
├── opportunity.py
├── quote.py
├── contract.py
└── invoice.py
```

## 🛠️ 实用工具脚本

### 脚本1：提取函数到新文件

```bash
#!/bin/bash
# extract_functions.sh
# 用法: ./extract_functions.sh source.py start_line end_line output.py

SOURCE=$1
START=$2
END=$3
OUTPUT=$4

sed -n "${START},${END}p" "$SOURCE" > "$OUTPUT"
echo "✅ 提取完成: $OUTPUT"
```

### 脚本2：自动生成__init__.py

```python
#!/usr/bin/env python3
# generate_init.py
import re
from pathlib import Path

def generate_init(module_dir):
    """为模块生成__init__.py"""
    module_path = Path(module_dir)
    py_files = list(module_path.glob("*.py"))
    py_files = [f for f in py_files if f.name != "__init__.py"]

    imports = []
    for py_file in py_files:
        module_name = py_file.stem
        imports.append(f"from app.{module_path.name}.{module_name} import *")

    init_content = "\n".join([
        "# -*- coding: utf-8 -*-",
        f"\"\"\"{module_path.name.upper()} 模块\"\"\"",
        "",
        *imports,
    ])

    (module_path / "__init__.py").write_text(init_content)
    print(f"✅ 生成 {module_path}/__init__.py")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_init(sys.argv[1])
```

### 脚本3：验证拆分后的导入

```python
#!/usr/bin/env python3
# verify_imports.py
import sys
import importlib

def verify_module_import(module_path):
    """验证模块导入是否正常"""
    try:
        module = importlib.import_module(module_path)
        functions = [attr for attr in dir(module) if not attr.startswith('_')]
        print(f"✅ {module_path}: {len(functions)} 个导出")
        return True
    except Exception as e:
        print(f"❌ {module_path}: {e}")
        return False

if __name__ == "__main__":
    modules = [
        "app.utils.scheduled_tasks",
        "app.api.v1.endpoints.acceptance",
        "app.schemas.sales",
    ]

    failed = 0
    for module in modules:
        if not verify_module_import(module):
            failed += 1

    if failed > 0:
        sys.exit(1)
```

## 📋 实施检查清单

### scheduled_tasks.py 拆分

- [ ] 创建 scheduled_tasks 包目录
- [ ] 创建 base.py（公共导入和工具）
- [ ] 提取项目相关函数到 project.py
- [ ] 提取生产相关函数到 production.py
- [ ] 提取工时相关函数到 timesheet.py
- [ ] 提取销售相关函数到 sales.py
- [ ] 提取预警相关函数到 alerts.py
- [ ] 提取通知相关函数到 notification.py
- [ ] 提取维护相关函数到 maintenance.py
- [ ] 创建 __init__.py 统一导出
- [ ] 运行导入验证测试
- [ ] 运行功能测试
- [ ] 备份并删除原文件

### acceptance.py 拆分

- [ ] 创建 acceptance 包目录
- [ ] 提取模板管理到 templates.py
- [ ] 提取验收单到 orders.py
- [ ] 提取检查项到 check_items.py
- [ ] 提取问题管理到 issues.py
- [ ] 提取审批流程到 approvals.py
- [ ] 提取报告生成到 reports.py
- [ ] 创建 __init__.py 聚合路由
- [ ] 更新 API 注册
- [ ] 测试所有端点

### projects/extended.py 拆分

- [ ] 分析文件结构和路由分组
- [ ] 创建子模块结构
- [ ] 按功能域拆分路由
- [ ] 创建统一导出
- [ ] 测试所有端点

## ⚠️ 注意事项

1. **不要删除原文件** - 直到所有测试通过
2. **保持向后兼容** - 使用 __init__.py 重新导出
3. **渐进式迁移** - 一次拆分一个文件，充分测试
4. **更新文档** - 记录所有变更
5. **团队沟通** - 通知团队成员新的导入方式

## 📞 需要帮助？

拆分过程中遇到问题时：

1. **导入错误** - 检查相对导入路径
2. **循环依赖** - 重新组织模块结构
3. **类型错误** - 更新类型注解
4. **路由冲突** - 检查路由前缀和标签

---

**创建时间**: 2026-01-14
**状态**: 准备就绪，可以开始实施
**预计工时**: 2-3天（完成所有后端文件拆分）
