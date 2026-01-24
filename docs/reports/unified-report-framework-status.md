# 统一报表框架实施状态

> **创建日期**: 2026-01-24  
> **状态**: 📋 计划阶段，开始实施

---

## 🎯 目标

统一所有报表服务使用 `report_framework`，实现：
- ✅ 配置驱动的报表生成
- ✅ 统一的报表API
- ✅ 统一的导出格式
- ✅ 减少代码重复

---

## 📊 现状分析

### 已存在的框架

- ✅ **report_framework** - 统一报表框架（配置驱动，YAML配置）
- ✅ **统一API端点** - `/reports/unified.py`
- ✅ **多格式支持** - JSON、PDF、Excel、Word
- ✅ **已有配置** - `app/report_configs/` 目录下已有部分YAML配置

### 分散的报表服务

| 服务 | 位置 | 状态 | 迁移优先级 |
|------|------|------|----------|
| **report_data_generation** | `app/services/report_data_generation/` | 使用中 | 🔴 高 |
| **template_report** | `app/services/template_report/` | 使用中 | 🔴 高 |
| **timesheet_report_service** | `app/services/timesheet_report_service.py` | 使用中 | 🟡 中 |
| **meeting_report_service** | `app/services/meeting_report_service.py` | 使用中 | 🟡 中 |
| **acceptance_report_service** | `app/services/acceptance_report_service.py` | 使用中 | 🟢 低 |
| **report_export_service** | `app/services/report_export_service.py` | 使用中 | 🔴 高 |

---

## 🚀 实施计划

### Phase 1: 创建报表适配器基类 ✅

- ✅ 创建 `BaseReportAdapter` 基类
- ✅ 提供统一接口
- ✅ 支持YAML配置和适配器两种模式

### Phase 2: 迁移简单报表（进行中）

- ⏳ 迁移 `timesheet_report_service` → YAML配置
- ⏳ 迁移 `acceptance_report_service` → YAML配置

### Phase 3: 迁移复杂报表

- ⏳ 迁移 `meeting_report_service` → YAML配置
- ⏳ 迁移 `report_data_generation` → YAML配置
- ⏳ 迁移 `template_report` → YAML配置

### Phase 4: 统一导出服务

- ⏳ 统一所有导出逻辑到 `report_framework`
- ⏳ 废弃或重构 `report_export_service`

### Phase 5: 清理和文档

- ⏳ 清理废弃代码
- ⏳ 更新文档
- ⏳ 创建迁移指南

---

## 📝 已完成的配置

### 项目报表

- ✅ `app/report_configs/project/weekly.yaml` - 项目周报
- ✅ `app/report_configs/project/monthly.yaml` - 项目月报

### 部门报表

- ✅ `app/report_configs/department/monthly.yaml` - 部门月报

### 会议报表

- ✅ `app/report_configs/meeting/monthly.yaml` - 会议月报

### 销售报表

- ✅ `app/report_configs/sales/monthly.yaml` - 销售月报

### 验收报表

- ✅ `app/report_configs/acceptance/report.yaml` - 验收报表

### 库存报表

- ✅ `app/report_configs/inventory/shortage_daily.yaml` - 缺料日报

---

## 🔧 技术实现

### 报表适配器基类

```python
class BaseReportAdapter(ABC):
    """报表适配器基类"""
    
    def generate(
        self,
        params: Dict[str, Any],
        format: str = "json",
        user: Optional[User] = None,
        skip_cache: bool = False,
    ) -> Any:
        """生成报表（使用统一报表框架）"""
        # 优先使用YAML配置
        # 如果不存在，使用适配器方法
```

### YAML配置示例

```yaml
meta:
  name: 项目周报
  code: PROJECT_WEEKLY
  description: 项目经理每周汇报项目进展

permissions:
  roles: [PROJECT_MANAGER, DEPARTMENT_MANAGER, ADMIN]
  data_scope: project

parameters:
  - name: project_id
    type: integer
    required: true

data_sources:
  project_data:
    type: service
    method: app.services.project_service.get_project_data
    args:
      project_id: "{{ params.project_id }}"

sections:
  - id: summary
    title: 项目汇总
    type: metrics
    items:
      - label: 项目名称
        value: "{{ project_data.name }}"
```

---

## 📈 预期成果

### 代码减少

- **timesheet_report_service**: ~500行 → YAML配置（减少90%）
- **meeting_report_service**: ~300行 → YAML配置（减少90%）
- **acceptance_report_service**: ~300行 → YAML配置（减少90%）
- **report_data_generation**: ~1000行 → YAML配置（减少90%）
- **template_report**: ~800行 → YAML配置（减少90%）

### 功能增强

- ✅ 统一的报表API
- ✅ 配置驱动的报表生成
- ✅ 统一的导出格式
- ✅ 统一的权限控制
- ✅ 统一的缓存机制

---

## 📚 相关文档

- [统一报表框架实施计划](./plans/unified-report-framework-implementation-plan.md)
- [统一报表框架设计方案](./plans/2026-01-21-unified-report-framework-design.md)

---

**文档版本**: v1.0  
**创建日期**: 2026-01-24  
**状态**: 📋 计划阶段，开始实施
