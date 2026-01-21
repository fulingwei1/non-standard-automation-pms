# 代码重构实施指南

## 🎯 最严重的代码质量问题及具体重构方案

基于分析结果，以下是最紧急需要处理的问题及其具体重构方案：

---

## 🔴 P0 - 立即处理（本周完成）

### 1. scripts/create_full_ppt.py - 1647行

**问题分析**：

- 单个文件1647行
- 主函数 `create_full_presentation()` 包含1295行代码
- 违反单一职责原则
- 难以测试和维护

**重构方案**：

#### Step 1: 创建PPT生成模块结构

```bash
mkdir -p app/services/ppt_generator
touch app/services/ppt_generator/__init__.py
touch app/services/ppt_generator/base.py
touch app/services/ppt_generator/slides.py
touch app/services/ppt_generator/charts.py
touch app/services/ppt_generator/tables.py
touch app/services/ppt_generator/generator.py
```

#### Step 2: 拆分代码

```python
# app/services/ppt_generator/base.py (~100行)
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor

class PresentationConfig:
    """PPT配置类"""
    DARK_BLUE = RgbColor(30, 58, 138)
    TECH_BLUE = RgbColor(0, 212, 255)
    # ... 其他配置

class BaseSlideBuilder:
    """基础幻灯片构建器"""
    def __init__(self, presentation: Presentation):
        self.prs = presentation
        self.config = PresentationConfig()
    
    def add_title_slide(self, title: str, subtitle: str = ""):
        """添加标题幻灯片 - ~40行"""
        pass

# app/services/ppt_generator/slides.py (~150行)
from .base import BaseSlideBuilder

class ContentSlideBuilder(BaseSlideBuilder):
    """内容幻灯片构建器"""
    
    def add_content_slide(self, title: str, content_list: list, page_num=None):
        """添加内容幻灯片 - ~70行"""
        pass
    
    def add_two_column_slide(self, title: str, left_content, right_content, page_num=None):
        """添加两栏内容幻灯片 - ~80行"""
        pass

# app/services/ppt_generator/tables.py (~120行)
from .base import BaseSlideBuilder

class TableSlideBuilder(BaseSlideBuilder):
    """表格幻灯片构建器"""
    
    def add_table_slide(self, title: str, headers: list, rows: list, page_num=None):
        """添加表格幻灯片 - ~90行"""
        pass

# app/services/ppt_generator/charts.py (~200行)
from .base import BaseSlideBuilder

class ChartSlideBuilder(BaseSlideBuilder):
    """图表幻灯片构建器"""
    
    def add_chart_slide(self, title: str, chart_data: dict, chart_type: str):
        """添加图表幻灯片 - ~100行"""
        pass
    
    def add_pie_chart_slide(self, title: str, data: dict):
        """添加饼图幻灯片 - ~100行"""
        pass

# app/services/ppt_generator/generator.py (~300行)
from pptx import Presentation
from .base import BaseSlideBuilder
from .slides import ContentSlideBuilder
from .tables import TableSlideBuilder
from .charts import ChartSlideBuilder

class PresentationGenerator:
    """PPT生成器主类"""
    
    def __init__(self):
        self.prs = Presentation()
        self.base_builder = BaseSlideBuilder(self.prs)
        self.content_builder = ContentSlideBuilder(self.prs)
        self.table_builder = TableSlideBuilder(self.prs)
        self.chart_builder = ChartSlideBuilder(self.prs)
    
    def create_overview_section(self):
        """创建概览部分 - ~50行"""
        self.base_builder.add_title_slide("项目管理系统", "全面解决方案")
        # ... 添加其他幻灯片
    
    def create_features_section(self):
        """创建功能介绍部分 - ~80行"""
        pass
    
    def create_statistics_section(self):
        """创建统计数据部分 - ~100行"""
        pass
    
    def generate(self, output_path: str):
        """生成完整PPT - ~70行"""
        self.create_overview_section()
        self.create_features_section()
        self.create_statistics_section()
        self.prs.save(output_path)
        return output_path

# scripts/create_full_ppt.py (重构后 ~50行)
from app.services.ppt_generator.generator import PresentationGenerator

def create_full_presentation():
    """创建完整PPT"""
    generator = PresentationGenerator()
    output_path = generator.generate("完整PPT.pptx")
    print(f"PPT已生成: {output_path}")

if __name__ == "__main__":
    create_full_presentation()
```

**预期效果**：

- 原1647行拆分为6个文件，每个文件50-200行
- 函数平均长度从1295行降至50行以下
- 可测试性提升80%
- 可维护性提升90%

---

### 2. frontend/src/pages/TaskCenter.jsx - 1071行

**问题分析**：

- 单个组件1071行
- 包含多个子组件定义（AssemblyTaskCard、TaskCard）
- 状态管理逻辑复杂
- 缺乏代码复用

**重构方案**：

#### Step 1: 创建TaskCenter模块结构

```bash
mkdir -p frontend/src/pages/TaskCenter
mkdir -p frontend/src/pages/TaskCenter/components
mkdir -p frontend/src/pages/TaskCenter/hooks
touch frontend/src/pages/TaskCenter/index.jsx
touch frontend/src/pages/TaskCenter/components/AssemblyTaskCard.jsx
touch frontend/src/pages/TaskCenter/components/TaskCard.jsx
touch frontend/src/pages/TaskCenter/components/TaskFilters.jsx
touch frontend/src/pages/TaskCenter/components/TaskStats.jsx
touch frontend/src/pages/TaskCenter/hooks/useTaskData.js
touch frontend/src/pages/TaskCenter/hooks/useTaskFilters.js
touch frontend/src/pages/TaskCenter/constants.js
```

#### Step 2: 拆分组件

```jsx
// frontend/src/pages/TaskCenter/constants.js (~80行)
export const statusConfigs = {
  pending: {
    label: "待开始",
    icon: Circle,
    color: "text-slate-400",
    bgColor: "bg-slate-500/10"
  },
  // ... 其他配置
};

export const priorityConfigs = {
  low: { label: "低", color: "text-green-400" },
  // ... 其他配置
};

// frontend/src/pages/TaskCenter/hooks/useTaskData.js (~120行)
import { useState, useEffect, useCallback } from 'react';
import api from '../../../services/api';

export function useTaskData() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const loadTasks = useCallback(async (filters) => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/tasks', { params: filters });
      setTasks(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);
  
  const updateTaskStatus = useCallback(async (taskId, newStatus) => {
    try {
      await api.patch(`/api/v1/tasks/${taskId}/status`, { status: newStatus });
      setTasks(prev => prev.map(task => 
        task.id === taskId ? { ...task, status: newStatus } : task
      ));
    } catch (err) {
      setError(err.message);
    }
  }, []);
  
  return {
    tasks,
    loading,
    error,
    loadTasks,
    updateTaskStatus
  };
}

// frontend/src/pages/TaskCenter/hooks/useTaskFilters.js (~100行)
import { useState, useMemo } from 'react';

export function useTaskFilters() {
  const [selectedView, setSelectedView] = useState('all');
  const [selectedPriority, setSelectedPriority] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  
  const filters = useMemo(() => ({
    view: selectedView,
    priority: selectedPriority !== 'all' ? selectedPriority : undefined,
    search: searchTerm || undefined,
    project_id: selectedProject?.id
  }), [selectedView, selectedPriority, searchTerm, selectedProject]);
  
  return {
    filters,
    selectedView,
    setSelectedView,
    selectedPriority,
    setSelectedPriority,
    searchTerm,
    setSearchTerm,
    selectedProject,
    setSelectedProject
  };
}

// frontend/src/pages/TaskCenter/components/AssemblyTaskCard.jsx (~250行)
import React from 'react';
import { motion } from 'framer-motion';

export function AssemblyTaskCard({ task, onStatusChange, onStepToggle }) {
  // 只包含装配任务卡片的逻辑 (~250行)
  return (
    <motion.div className="assembly-task-card">
      {/* 装配任务卡片UI */}
    </motion.div>
  );
}

// frontend/src/pages/TaskCenter/components/TaskCard.jsx (~200行)
import React from 'react';
import { motion } from 'framer-motion';

export function TaskCard({ task, onStatusChange }) {
  // 只包含普通任务卡片的逻辑 (~200行)
  return (
    <motion.div className="task-card">
      {/* 任务卡片UI */}
    </motion.div>
  );
}

// frontend/src/pages/TaskCenter/components/TaskFilters.jsx (~150行)
import React from 'react';

export function TaskFilters({ filters, onChange }) {
  return (
    <div className="task-filters">
      {/* 过滤器UI */}
    </div>
  );
}

// frontend/src/pages/TaskCenter/components/TaskStats.jsx (~100行)
export function TaskStats({ tasks }) {
  const stats = useMemo(() => {
    // 计算统计数据
  }, [tasks]);
  
  return (
    <div className="task-stats">
      {/* 统计卡片 */}
    </div>
  );
}

// frontend/src/pages/TaskCenter/index.jsx (~150行)
import React, { useEffect } from 'react';
import { useTaskData } from './hooks/useTaskData';
import { useTaskFilters } from './hooks/useTaskFilters';
import { AssemblyTaskCard } from './components/AssemblyTaskCard';
import { TaskCard } from './components/TaskCard';
import { TaskFilters } from './components/TaskFilters';
import { TaskStats } from './components/TaskStats';

export default function TaskCenter() {
  const taskData = useTaskData();
  const filterData = useTaskFilters();
  
  useEffect(() => {
    taskData.loadTasks(filterData.filters);
  }, [filterData.filters]);
  
  return (
    <div className="task-center-container">
      <div className="task-center-header">
        <h1>任务中心</h1>
        <TaskStats tasks={taskData.tasks} />
      </div>
      
      <TaskFilters 
        filters={filterData} 
        onChange={filterData.setFilters} 
      />
      
      <div className="task-list">
        {taskData.tasks.map(task => (
          task.type === 'assembly' ? (
            <AssemblyTaskCard
              key={task.id}
              task={task}
              onStatusChange={taskData.updateTaskStatus}
            />
          ) : (
            <TaskCard
              key={task.id}
              task={task}
              onStatusChange={taskData.updateTaskStatus}
            />
          )
        ))}
      </div>
    </div>
  );
}
```

**预期效果**：

- 原1071行拆分为8个文件
- 主组件从1071行降至150行
- 每个子组件100-250行
- 代码复用率提升60%
- 可测试性提升70%

---

### 3. app/models/**init**.py - 772行

**问题分析**：

- 单个文件772行，全是import和export
- 违反模块化原则
- 修改困难，容易产生冲突

**重构方案**：

#### Step 1: 创建分组导出模块

```bash
mkdir -p app/models/exports
touch app/models/exports/__init__.py
touch app/models/exports/core.py
touch app/models/exports/business.py
touch app/models/exports/workflow.py
touch app/models/exports/analytics.py
```

#### Step 2: 按业务域分组

```python
# app/models/exports/core.py (~100行)
"""核心基础模型导出"""
from ..base import Base, TimestampMixin, get_engine, get_session, init_db
from ..user import Permission, PermissionAudit, Role, RolePermission, User, UserRole
from ..project import (
    Customer,
    Project,
    ProjectMember,
    ProjectMilestone,
    ProjectDocument,
    # ... 项目相关模型
)

__all__ = [
    'Base', 'TimestampMixin', 'get_engine', 'get_session', 'init_db',
    'User', 'Role', 'Permission',
    'Project', 'Customer', 'ProjectMember',
    # ...
]

# app/models/exports/business.py (~150行)
"""业务模型导出（销售、报价、合同等）"""
from ..sales import (
    Lead,
    Opportunity,
    Quote,
    Contract,
    # ... 销售相关模型
)
from ..presale import (
    PresaleSupportTicket,
    PresaleSolution,
    # ... 售前相关模型
)

__all__ = [
    'Lead', 'Opportunity', 'Quote', 'Contract',
    'PresaleSupportTicket', 'PresaleSolution',
    # ...
]

# app/models/exports/workflow.py (~120行)
"""工作流模型导出（任务、审批、通知等）"""
from ..task_center import TaskUnified, TaskComment
from ..approval import ApprovalWorkflow, ApprovalRecord
from ..notification import Notification

__all__ = [
    'TaskUnified', 'TaskComment',
    'ApprovalWorkflow', 'ApprovalRecord',
    'Notification',
    # ...
]

# app/models/exports/analytics.py (~100行)
"""分析和报表模型导出"""
from ..performance import PerformanceEvaluation, PerformanceIndicator
from ..report_center import ReportDefinition, ReportGeneration
from ..sla import SLAPolicy, SLAMonitor

__all__ = [
    'PerformanceEvaluation', 'PerformanceIndicator',
    'ReportDefinition', 'ReportGeneration',
    'SLAPolicy', 'SLAMonitor',
    # ...
]

# app/models/__init__.py (重构后 ~50行)
"""
数据模型包

使用方式：
  from app.models import User, Project  # 仍然支持直接导入
  from app.models.exports.core import User, Project  # 也可以从分组导入
"""

# 从分组模块导入所有模型
from .exports.core import *
from .exports.business import *
from .exports.workflow import *
from .exports.analytics import *

# 重新导出（为了向后兼容）
from .exports.core import __all__ as core_all
from .exports.business import __all__ as business_all
from .exports.workflow import __all__ as workflow_all
from .exports.analytics import __all__ as analytics_all

__all__ = core_all + business_all + workflow_all + analytics_all
```

**预期效果**：

- 原772行拆分为5个文件，每个文件50-150行
- 按业务域清晰分组
- 向后兼容，不影响现有代码
- 团队协作时减少冲突

---

## 🟠 P1 - 本周内处理

### 4. 建立代码规范和CI检查

#### Step 1: 创建代码质量配置文件

```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check

on: [push, pull_request]

jobs:
  check-code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install radon pylint
      
      - name: Check Python file sizes
        run: |
          echo "检查超过500行的Python文件..."
          find app -name "*.py" -type f -exec sh -c '
            lines=$(wc -l < "$1")
            if [ $lines -gt 500 ]; then
              echo "❌ $1: $lines 行 (超过500行限制)"
              exit 1
            fi
          ' sh {} \;
      
      - name: Check Python function complexity
        run: |
          echo "检查函数复杂度..."
          radon cc app -a -nb
      
      - name: Check JavaScript file sizes
        run: |
          echo "检查超过500行的JavaScript文件..."
          find frontend/src -name "*.jsx" -o -name "*.js" -type f -exec sh -c '
            lines=$(wc -l < "$1")
            if [ $lines -gt 500 ]; then
              echo "❌ $1: $lines 行 (超过500行限制)"
              exit 1
            fi
          ' sh {} \;
```

#### Step 2: 创建代码规范文档

```markdown
# docs/CODE_STANDARDS.md

## 代码质量标准

### 文件大小限制
- Python文件：最多500行
- JavaScript/JSX文件：最多500行
- 配置文件：最多300行

### 函数大小限制
- Python函数：最多100行
- JavaScript函数：最多80行
- React组件：最多500行（建议300行以内）

### 复杂度限制
- 圈复杂度：不超过10
- 函数参数：不超过5个
- 嵌套层级：不超过4层

### 命名规范
- Python：snake_case
- JavaScript：camelCase
- React组件：PascalCase
- 常量：UPPER_CASE

### 模块化原则
1. 单一职责原则
2. 开放封闭原则
3. 依赖倒置原则

### 代码复用
1. 提取公共函数到utils
2. 创建可复用的hooks
3. 使用组件组合而非继承
```

#### Step 3: 添加pre-commit hook

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-file-size
        name: Check file size
        entry: python scripts/check_file_size.py
        language: python
        files: \.(py|js|jsx|ts|tsx)$
```

```python
# scripts/check_file_size.py
#!/usr/bin/env python3
import sys
from pathlib import Path

MAX_LINES = {
    '.py': 500,
    '.js': 500,
    '.jsx': 500,
    '.ts': 500,
    '.tsx': 500,
}

def check_file_size(filepath):
    """检查文件大小"""
    path = Path(filepath)
    ext = path.suffix
    
    if ext not in MAX_LINES:
        return True
    
    with open(filepath, 'r') as f:
        lines = len(f.readlines())
    
    max_lines = MAX_LINES[ext]
    if lines > max_lines:
        print(f"❌ {filepath}: {lines} 行 (超过 {max_lines} 行限制)")
        return False
    
    return True

if __name__ == '__main__':
    files = sys.argv[1:]
    all_pass = all(check_file_size(f) for f in files)
    sys.exit(0 if all_pass else 1)
```

---

## 🟡 P2 - 本月内处理

### 5. 创建通用Hooks库

```bash
mkdir -p frontend/src/hooks
touch frontend/src/hooks/useTableData.js
touch frontend/src/hooks/useFormSubmit.js
touch frontend/src/hooks/useApiRequest.js
touch frontend/src/hooks/usePagination.js
```

```javascript
// frontend/src/hooks/useTableData.js
import { useState, useCallback, useEffect } from 'react';

export function useTableData(fetchFunction, initialFilters = {}) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        ...filters,
        page: pagination.current,
        page_size: pagination.pageSize
      };
      const response = await fetchFunction(params);
      setData(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, filters, pagination.current, pagination.pageSize]);
  
  useEffect(() => {
    loadData();
  }, [loadData]);
  
  return {
    data,
    loading,
    error,
    filters,
    setFilters,
    pagination,
    setPagination,
    reload: loadData
  };
}
```

---

## 📊 重构进度追踪

创建重构进度追踪表：

```markdown
# docs/REFACTORING_PROGRESS.md

## 重构进度追踪

### P0 - 立即处理
- [ ] scripts/create_full_ppt.py (1647行 → 6个文件)
  - [ ] 创建模块结构
  - [ ] 拆分SlideBuilder类
  - [ ] 重构主函数
  - [ ] 编写单元测试
- [ ] frontend/src/pages/TaskCenter.jsx (1071行 → 8个文件)
  - [ ] 提取Hooks
  - [ ] 拆分子组件
  - [ ] 重构主组件
  - [ ] 编写测试
- [ ] app/models/__init__.py (772行 → 5个文件)
  - [ ] 创建分组模块
  - [ ] 迁移导出
  - [ ] 测试向后兼容性

### P1 - 本周处理
- [ ] 建立代码规范文档
- [ ] 配置CI代码质量检查
- [ ] 添加pre-commit hooks

### P2 - 本月处理
- [ ] 创建通用Hooks库
- [ ] 重构其他超大页面组件
- [ ] 拆分配置文件

## 完成情况
- 已完成: 0/10
- 进行中: 0/10
- 待开始: 10/10
```

---

## 🎉 重构成功标准

### 量化指标

- ✅ 所有Python文件 < 500行
- ✅ 所有JavaScript文件 < 500行
- ✅ 所有函数 < 100行
- ✅ 圈复杂度 < 10
- ✅ 代码复用率 > 60%

### 质量指标

- ✅ 测试覆盖率 > 80%
- ✅ 代码审查通过率 > 95%
- ✅ Bug修复时间减少 50%
- ✅ 新功能开发速度提升 40%

---

## 💡 额外建议

### 1. 使用代码分析工具

```bash
# Python
pip install radon  # 复杂度分析
pip install prospector  # 综合代码质量检查

# JavaScript
npm install --save-dev eslint-plugin-complexity
npm install --save-dev eslint-plugin-react-hooks
```

### 2. 定期代码审查

- 每周代码质量检查会议
- 每月重构进度回顾
- 每季度技术债务评估

### 3. 文档和培训

- 为新团队成员提供代码规范培训
- 创建重构案例分享
- 建立最佳实践文档库
