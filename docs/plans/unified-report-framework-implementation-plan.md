# 统一报表框架实施计划

> **创建日期**: 2026-01-24  
> **目标**: 统一所有报表服务使用 `report_framework`，减少代码重复，提高可维护性

---

## 一、现状分析

### 1.1 现有报表框架

**已存在**: `app/services/report_framework/` - 统一报表框架
- ✅ 配置驱动（YAML配置）
- ✅ 多数据源支持（SQL查询、服务调用、聚合函数）
- ✅ 多导出格式（JSON、PDF、Excel、Word）
- ✅ 缓存和定时预生成
- ✅ 权限控制
- ✅ 统一API端点 (`/reports/unified.py`)

### 1.2 分散的报表服务

| 服务/模块 | 位置 | 状态 | 问题 |
|----------|------|------|------|
| **report_data_generation** | `app/services/report_data_generation/` | 使用中 | 功能与report_framework重叠 |
| **template_report** | `app/services/template_report/` | 使用中 | 功能与report_framework重叠 |
| **timesheet_report_service** | `app/services/timesheet_report_service.py` | 使用中 | 独立实现，无统一接口 |
| **meeting_report_service** | `app/services/meeting_report_service.py` | 使用中 | 独立实现，无统一接口 |
| **acceptance_report_service** | `app/services/acceptance_report_service.py` | 使用中 | 独立实现，无统一接口 |
| **report_export_service** | `app/services/report_export_service.py` | 使用中 | 导出逻辑分散 |

### 1.3 主要问题

1. **功能重叠** - `report_data_generation` 和 `template_report` 与 `report_framework` 功能重叠
2. **无统一接口** - 各报表服务没有统一的基类/接口
3. **导出逻辑分散** - PDF、Excel、Word导出逻辑分散在各个服务中
4. **新增报表困难** - 需要写大量代码，无法配置驱动

---

## 二、设计方案

### 2.1 统一架构

```
┌─────────────────────────────────────────────────────────┐
│              Unified Report Framework                  │
│              (app/services/report_framework/)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                 │
│  │ YAML Configs │───▶│ Report Engine│                 │
│  │ (report_     │    │              │                 │
│  │  configs/)   │    └──────┬───────┘                 │
│  └──────────────┘           │                          │
│                             │                          │
│                  ┌──────────┼──────────┐               │
│                  ▼          ▼          ▼               │
│            ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│            │ Data    │ │ Cache   │ │ Export  │        │
│            │ Resolver│ │ Manager │ │ Pipeline│        │
│            └─────────┘ └─────────┘ └─────────┘        │
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │         Unified API Endpoints                 │     │
│  │  /reports/{report_code}/generate              │     │
│  │  /reports/{report_code}/preview               │     │
│  │  /reports/{report_code}/schema                 │     │
│  └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 迁移策略

#### Phase 1: 创建报表配置基类（1天）
- 创建统一的报表配置基类
- 定义标准报表接口
- 创建迁移工具

#### Phase 2: 迁移简单报表（2天）
- 迁移 `timesheet_report_service` → YAML配置
- 迁移 `acceptance_report_service` → YAML配置
- 创建测试验证

#### Phase 3: 迁移复杂报表（3天）
- 迁移 `meeting_report_service` → YAML配置
- 迁移 `report_data_generation` → YAML配置
- 迁移 `template_report` → YAML配置
- 创建测试验证

#### Phase 4: 统一导出服务（2天）
- 统一所有导出逻辑到 `report_framework`
- 废弃 `report_export_service` 或重构为适配器
- 创建测试验证

#### Phase 5: 清理和文档（1天）
- 清理废弃代码
- 更新文档
- 创建迁移指南

---

## 三、实施步骤

### Phase 1: 创建报表配置基类

**目标**: 为现有报表服务创建统一接口

1. 创建 `app/services/report_framework/adapters/` 目录
2. 创建 `BaseReportAdapter` 基类
3. 创建迁移工具 `migrate_report_to_yaml.py`

### Phase 2: 迁移简单报表

**目标**: 将简单报表迁移到YAML配置

1. **工时报表** (`timesheet_report_service`)
   - 创建 `app/report_configs/timesheet/weekly.yaml`
   - 创建 `app/report_configs/timesheet/monthly.yaml`
   - 测试验证

2. **验收报表** (`acceptance_report_service`)
   - 创建 `app/report_configs/acceptance/order.yaml`
   - 测试验证

### Phase 3: 迁移复杂报表

**目标**: 将复杂报表迁移到YAML配置

1. **会议报表** (`meeting_report_service`)
   - 创建 `app/report_configs/meeting/weekly.yaml`
   - 创建 `app/report_configs/meeting/monthly.yaml`
   - 测试验证

2. **项目报表** (`report_data_generation`)
   - 创建 `app/report_configs/project/weekly.yaml`
   - 创建 `app/report_configs/project/monthly.yaml`
   - 测试验证

3. **模板报表** (`template_report`)
   - 迁移到YAML配置
   - 测试验证

### Phase 4: 统一导出服务

**目标**: 统一所有导出逻辑

1. 重构 `report_export_service` 使用 `report_framework`
2. 更新所有报表端点使用统一导出
3. 测试验证

### Phase 5: 清理和文档

**目标**: 清理废弃代码，更新文档

1. 标记废弃的服务为 `@deprecated`
2. 更新API文档
3. 创建迁移指南

---

## 四、预期成果

### 4.1 代码减少

- **timesheet_report_service**: ~500行 → YAML配置（减少90%）
- **meeting_report_service**: ~300行 → YAML配置（减少90%）
- **acceptance_report_service**: ~300行 → YAML配置（减少90%）
- **report_data_generation**: ~1000行 → YAML配置（减少90%）
- **template_report**: ~800行 → YAML配置（减少90%）

### 4.2 功能增强

- ✅ 统一的报表API
- ✅ 配置驱动的报表生成
- ✅ 统一的导出格式
- ✅ 统一的权限控制
- ✅ 统一的缓存机制

### 4.3 可维护性提升

- ✅ 新增报表只需编写YAML配置
- ✅ 报表逻辑集中管理
- ✅ 易于修改和扩展

---

## 五、技术细节

### 5.1 YAML配置示例

```yaml
# app/report_configs/timesheet/weekly.yaml
meta:
  name: 工时周报
  code: TIMESHEET_WEEKLY
  description: 项目工时周报
  version: "1.0"

permissions:
  roles: [PROJECT_MANAGER, HR, ADMIN]
  data_scope: project

parameters:
  - name: project_id
    type: integer
    required: true
    description: 项目ID
  - name: start_date
    type: date
    required: false
    default: null
  - name: end_date
    type: date
    required: false
    default: null

data_sources:
  timesheet_data:
    type: service
    method: app.services.timesheet_report_service.get_weekly_data
    args:
      project_id: "{{ params.project_id }}"
      start_date: "{{ params.start_date }}"
      end_date: "{{ params.end_date }}"

sections:
  - id: summary
    title: 工时汇总
    type: metrics
    items:
      - label: 总工时
        value: "{{ timesheet_data.total_hours }}"
      - label: 参与人数
        value: "{{ timesheet_data.participants }}"
  
  - id: details
    title: 工时明细
    type: table
    source: timesheet_data
    columns:
      - field: user_name
        label: 姓名
      - field: work_date
        label: 日期
      - field: hours
        label: 工时

exports:
  json:
    enabled: true
  pdf:
    enabled: true
  excel:
    enabled: true
  word:
    enabled: false
```

### 5.2 迁移工具

```python
# app/services/report_framework/migrate_report_to_yaml.py
def migrate_service_to_yaml(service_class, report_code, output_path):
    """将现有报表服务迁移到YAML配置"""
    # 分析服务方法
    # 生成YAML配置
    # 保存到指定路径
```

---

## 六、实施时间

- **Phase 1**: 1天（创建报表配置基类）
- **Phase 2**: 2天（迁移简单报表）
- **Phase 3**: 3天（迁移复杂报表）
- **Phase 4**: 2天（统一导出服务）
- **Phase 5**: 1天（清理和文档）

**总计**: 9天

---

## 七、风险评估

### 7.1 低风险

- ✅ 简单报表迁移（工时、验收）
- ✅ 不影响现有功能

### 7.2 中风险

- ⚠️ 复杂报表迁移（会议、项目）
- ⚠️ 需要充分测试

### 7.3 建议

- ✅ 先实施Phase 1和Phase 2
- ✅ 充分测试后再实施Phase 3
- ⚠️ Phase 4和Phase 5可以分阶段进行

---

**文档版本**: v1.0  
**创建日期**: 2026-01-24  
**状态**: 📋 计划阶段
