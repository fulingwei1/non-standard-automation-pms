# 统一报表框架 (ReportEngine)

## 概述

统一报表框架是一个配置驱动的报表生成系统，支持通过 YAML 配置文件定义报表，无需编写代码即可创建新的报表。

## 核心特性

- ✅ **配置驱动** - 通过 YAML 配置文件定义报表
- ✅ **多数据源** - 支持 SQL 查询、服务方法调用、聚合函数
- ✅ **多格式导出** - 支持 JSON、PDF、Excel、Word
- ✅ **权限控制** - 基于角色的访问控制
- ✅ **缓存支持** - 内存缓存和 Redis 缓存
- ✅ **表达式引擎** - 基于 Jinja2 的表达式计算
- ✅ **定时任务** - 支持定时预生成报表

## 快速开始

### 1. 创建报表配置

在 `app/report_configs/` 目录下创建 YAML 配置文件：

```yaml
# app/report_configs/project/weekly.yaml
meta:
  name: 项目周报
  code: PROJECT_WEEKLY
  description: 项目经理每周汇报项目进展
  version: "1.0"

permissions:
  roles:
    - PROJECT_MANAGER
    - DEPARTMENT_MANAGER
    - ADMIN
  data_scope: project

parameters:
  - name: project_id
    type: integer
    required: true
    description: 项目ID
  - name: start_date
    type: date
    required: true
    description: 开始日期
  - name: end_date
    type: date
    required: true
    description: 结束日期

data_sources:
  tasks:
    type: query
    sql: |
      SELECT t.*, u.name as assignee_name
      FROM tasks t
      LEFT JOIN users u ON t.assignee_id = u.id
      WHERE t.project_id = :project_id
        AND t.updated_at BETWEEN :start_date AND :end_date

sections:
  - id: summary
    title: 概览
    type: metrics
    items:
      - label: 任务总数
        value: "{{ tasks | length }}"
      - label: 已完成
        value: "{{ tasks | count_by('status', 'DONE') }}"

  - id: task_list
    title: 任务列表
    type: table
    source: tasks
    columns:
      - field: task_name
        label: 任务名称
      - field: status
        label: 状态
        format: status_badge

exports:
  json:
    enabled: true
  pdf:
    enabled: true
    template: project_weekly.html
  excel:
    enabled: true
    sheets:
      - name: 概览
        section: summary
      - name: 任务明细
        section: task_list
```

### 2. 使用 ReportEngine 生成报表

```python
from app.services.report_framework import ReportEngine
from app.api.deps import get_db

# 初始化引擎
engine = ReportEngine(db=get_db())

# 生成报表
result = engine.generate(
    report_code="PROJECT_WEEKLY",
    params={
        "project_id": 123,
        "start_date": "2026-01-20",
        "end_date": "2026-01-26"
    },
    format="json",
    user=current_user
)

# 获取报表数据
report_data = result.data
```

### 3. 通过 API 访问

```bash
# 获取可用报表列表
GET /api/v1/reports/unified/reports

# 获取报表参数 Schema
GET /api/v1/reports/unified/reports/PROJECT_WEEKLY/schema

# 生成报表（JSON）
POST /api/v1/reports/unified/generate
{
  "report_code": "PROJECT_WEEKLY",
  "params": {
    "project_id": 123,
    "start_date": "2026-01-20",
    "end_date": "2026-01-26"
  },
  "format": "json"
}

# 下载报表（PDF/Excel/Word）
POST /api/v1/reports/unified/generate/download
{
  "report_code": "PROJECT_WEEKLY",
  "params": {...},
  "format": "pdf"
}
```

## 配置说明

### 元数据 (meta)

```yaml
meta:
  name: 报表名称
  code: 报表代码（唯一标识）
  description: 报表描述
  version: 版本号
```

### 权限配置 (permissions)

```yaml
permissions:
  roles:
    - PROJECT_MANAGER
    - ADMIN
  data_scope: project  # project | department | company | custom
```

### 参数定义 (parameters)

```yaml
parameters:
  - name: project_id
    type: integer      # integer | string | date | boolean | float | list
    required: true
    default: null
    description: 参数说明
```

### 数据源 (data_sources)

#### SQL 查询数据源

```yaml
data_sources:
  tasks:
    type: query
    sql: |
      SELECT * FROM tasks
      WHERE project_id = :project_id
```

#### 服务方法数据源

```yaml
data_sources:
  statistics:
    type: service
    method: ProjectStatisticsService.get_project_stats
    args:
      project_id: "{{ params.project_id }}"
```

### 报表结构 (sections)

#### 指标卡片 (metrics)

```yaml
sections:
  - id: summary
    title: 概览
    type: metrics
    items:
      - label: 任务总数
        value: "{{ tasks | length }}"
      - label: 完成率
        value: "{{ (completed / total * 100) | round_num(1) }}%"
```

#### 表格 (table)

```yaml
sections:
  - id: task_list
    title: 任务列表
    type: table
    source: tasks
    columns:
      - field: task_name
        label: 任务名称
      - field: status
        label: 状态
        format: status_badge
      - field: created_at
        label: 创建时间
        format: date
```

#### 图表 (chart)

```yaml
sections:
  - id: status_chart
    title: 状态分布
    type: chart
    chart_type: pie  # pie | bar | line | area
    source: tasks
    label_field: status
    value_field: count
```

### 导出配置 (exports)

```yaml
exports:
  json:
    enabled: true
  pdf:
    enabled: true
    template: project_weekly.html
    orientation: portrait  # portrait | landscape
  excel:
    enabled: true
    sheets:
      - name: 概览
        section: summary
      - name: 任务明细
        section: task_list
  word:
    enabled: false
    template: project_weekly.docx
```

## 表达式语法

报表框架使用 Jinja2 表达式引擎，支持：

### 变量访问

```jinja2
{{ tasks }}
{{ project.name }}
{{ params.project_id }}
```

### 过滤器

```jinja2
{{ tasks | length }}                    # 列表长度
{{ tasks | count_by('status', 'DONE') }} # 统计
{{ tasks | sum_by('amount') }}          # 求和
{{ tasks | avg_by('score') }}            # 平均值
{{ tasks | group_by('category') }}       # 分组
{{ amount | currency('¥', 2) }}         # 货币格式化
{{ ratio | percentage(1) }}            # 百分比
{{ date | date_format('%Y-%m-%d') }}     # 日期格式化
```

### 全局函数

```jinja2
{{ today() }}              # 今天
{{ now() }}                # 当前时间
{{ last_monday() }}        # 上周一
{{ last_sunday() }}        # 上周日
{{ this_month_start() }}   # 本月第一天
{{ this_month_end() }}     # 本月最后一天
```

## 自定义过滤器

在 `app/services/report_framework/expressions/filters.py` 中添加自定义过滤器：

```python
def filter_custom_format(value: Any) -> str:
    """自定义格式化器"""
    return f"自定义: {value}"

# 注册过滤器
env.filters["custom_format"] = filter_custom_format
```

## 缓存配置

```yaml
cache:
  enabled: true
  ttl: 3600  # 缓存时间（秒）
  key_pattern: "report:{code}:{project_id}:{start_date}"
```

## 定时任务配置

```yaml
schedule:
  enabled: true
  cron: "0 8 * * 1"  # 每周一 8:00
  params:
    start_date: "{{ last_monday() }}"
    end_date: "{{ last_sunday() }}"
```

## API 端点

### 列出可用报表

```http
GET /api/v1/reports/unified/reports
```

### 获取报表 Schema

```http
GET /api/v1/reports/unified/reports/{report_code}/schema
```

### 生成报表

```http
POST /api/v1/reports/unified/generate
Content-Type: application/json

{
  "report_code": "PROJECT_WEEKLY",
  "params": {...},
  "format": "json",
  "skip_cache": false
}
```

### 下载报表

```http
POST /api/v1/reports/unified/generate/download
Content-Type: application/json

{
  "report_code": "PROJECT_WEEKLY",
  "params": {...},
  "format": "pdf"
}
```

### 预览报表

```http
GET /api/v1/reports/unified/reports/{report_code}/preview?project_id=123&start_date=2026-01-20
```

## 错误处理

框架定义了以下异常类型：

- `ConfigError` - 配置错误（400）
- `PermissionError` - 权限错误（403）
- `ParameterError` - 参数错误（422）
- `DataSourceError` - 数据源错误（500）
- `RenderError` - 渲染错误（500）

## 最佳实践

1. **配置组织** - 按模块组织配置文件（project/、department/、sales/）
2. **参数验证** - 明确定义所有必需参数和类型
3. **权限控制** - 为每个报表配置适当的角色权限
4. **缓存策略** - 为频繁访问的报表启用缓存
5. **SQL 安全** - 使用参数化查询，避免 SQL 注入
6. **表达式简化** - 复杂计算尽量在数据源中完成

## 示例配置

查看 `app/report_configs/` 目录下的示例配置文件：

- `project/weekly.yaml` - 项目周报
- `project/monthly.yaml` - 项目月报
- `department/monthly.yaml` - 部门月报
- `meeting/monthly.yaml` - 会议月报
- `timesheet/hr_monthly.yaml` - HR 工时报表

## 扩展开发

### 添加自定义数据源

```python
from app.services.report_framework.data_sources.base import DataSource

class CustomDataSource(DataSource):
    def fetch(self, params: Dict[str, Any]) -> Any:
        # 实现数据获取逻辑
        return data

# 注册数据源
engine.data_resolver.register_data_source(
    DataSourceType.CUSTOM,
    CustomDataSource
)
```

### 添加自定义渲染器

```python
from app.services.report_framework.renderers.base import Renderer

class CustomRenderer(Renderer):
    @property
    def format_name(self) -> str:
        return "custom"
    
    def render(self, sections, metadata):
        # 实现渲染逻辑
        return ReportResult(...)

# 注册渲染器
engine.register_renderer("custom", CustomRenderer())
```

## 故障排查

### 配置加载失败

- 检查 YAML 文件语法
- 验证配置是否符合 Schema
- 查看 `ConfigError` 异常信息

### 数据源错误

- 检查 SQL 语法
- 验证参数是否正确传递
- 查看 `DataSourceError` 异常信息

### 表达式计算错误

- 检查变量名是否正确
- 验证过滤器是否存在
- 查看 `ExpressionError` 异常信息

## 相关文档

- [报表框架设计文档](../../../docs/plans/2026-01-21-unified-report-framework-design.md)
- [报表迁移计划](../../../docs/plans/unified-report-framework-implementation-plan.md)
- [报表配置示例](../../../app/report_configs/)
