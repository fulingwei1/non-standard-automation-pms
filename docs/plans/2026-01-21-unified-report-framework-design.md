# 统一报告框架设计方案

> 日期: 2026-01-21
> 状态: 设计完成，待实施

## 背景

当前系统存在报告/统计系统重复实现问题：

| 现有结构 | 问题 |
|---------|------|
| `report_data_generation/` | 有核心权限类 + 按类型分模块 |
| `template_report/` | 功能与上面重复 |
| 独立服务 (`*_report_service.py`) | 无统一基类/接口 |
| 统计服务 (`*_statistics_service.py`) | 分散，无公共模式 |

**主要问题：**
- 两个报告生成包功能重叠
- 各服务没有统一的基类/接口
- 报告导出逻辑分散（PDF、Excel、Word）
- 新增报告需要写大量代码

## 设计目标

1. **代码复用** - 减少重复代码，共享权限检查、导出逻辑
2. **统一 API** - 所有报告通过一个入口生成
3. **扩展性** - 配置驱动，零代码添加新报告类型
4. **全格式支持** - JSON + PDF + Excel + Word
5. **性能优化** - 缓存 + 定时预生成

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Unified Report Framework                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Report YAML  │───▶│ Config Loader │───▶│ Report Engine │      │
│  │ Definitions  │    │ & Validator   │    │              │       │
│  └──────────────┘    └──────────────┘    └──────┬───────┘       │
│                                                  │               │
│                    ┌─────────────────────────────┼─────────┐     │
│                    ▼                             ▼         ▼     │
│            ┌─────────────┐              ┌──────────┐ ┌────────┐  │
│            │ Data Source │              │ Cache    │ │Schedule│  │
│            │ Resolver    │              │ Manager  │ │Manager │  │
│            └──────┬──────┘              └──────────┘ └────────┘  │
│                   │                                              │
│       ┌───────────┼───────────┐                                  │
│       ▼           ▼           ▼                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│  │SQL Query│ │Service  │ │Aggregate│                            │
│  │Executor │ │Invoker  │ │Function │                            │
│  └─────────┘ └─────────┘ └─────────┘                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Export Pipeline                         │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐          │   │
│  │  │  JSON  │  │  PDF   │  │ Excel  │  │  Word  │          │   │
│  │  │Renderer│  │Renderer│  │Renderer│  │Renderer│          │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**核心组件：**

1. **Config Loader** - 加载并验证 YAML 配置，转为内部 Report 对象
2. **Report Engine** - 核心编排器，协调数据获取、缓存、导出
3. **Data Source Resolver** - 解析配置中的数据源，支持三种类型：
   - SQL Query：直接执行参数化 SQL
   - Service Invoker：调用现有服务方法
   - Aggregate Function：内置聚合函数（sum, avg, count 等）
4. **Cache Manager** - Redis/内存缓存，按配置的 TTL 管理
5. **Schedule Manager** - 与现有 APScheduler 集成，定时预生成
6. **Export Pipeline** - 统一导出接口，插件式渲染器

## YAML 配置 Schema

```yaml
# app/report_configs/project/weekly.yaml
# 报告配置完整示例

# === 元数据 ===
meta:
  name: 项目周报
  code: PROJECT_WEEKLY
  description: 项目经理每周汇报项目进展
  version: "1.0"

# === 权限控制 ===
permissions:
  roles: [PROJECT_MANAGER, DEPARTMENT_MANAGER, ADMIN]
  data_scope: project  # project | department | company | custom

# === 参数定义 ===
parameters:
  - name: project_id
    type: integer
    required: true
  - name: start_date
    type: date
    required: true
  - name: end_date
    type: date
    required: true
  - name: include_subtasks
    type: boolean
    default: true

# === 缓存策略 ===
cache:
  enabled: true
  ttl: 3600  # 秒
  key_pattern: "report:{code}:{project_id}:{start_date}"

# === 定时任务 ===
schedule:
  enabled: true
  cron: "0 8 * * 1"  # 每周一 8:00
  params:
    start_date: "{{ last_monday }}"
    end_date: "{{ last_sunday }}"

# === 数据源 ===
data_sources:
  tasks:
    type: query
    sql: |
      SELECT t.*, u.name as assignee_name
      FROM tasks t
      LEFT JOIN users u ON t.assignee_id = u.id
      WHERE t.project_id = :project_id
        AND t.updated_at BETWEEN :start_date AND :end_date

  issues:
    type: service
    method: IssueStatisticsService.count_by_project
    args:
      project_id: "{{ params.project_id }}"

  milestones:
    type: query
    sql: "SELECT * FROM milestones WHERE project_id = :project_id"

# === 报告结构 ===
sections:
  - id: summary
    title: 概览
    type: metrics
    items:
      - label: 任务总数
        value: "{{ tasks | length }}"
      - label: 已完成
        value: "{{ tasks | selectattr('status', 'eq', 'DONE') | length }}"
      - label: 完成率
        value: "{{ (tasks | selectattr('status', 'eq', 'DONE') | length / tasks | length * 100) | round(1) }}%"

  - id: task_list
    title: 本周任务
    type: table
    source: tasks
    columns:
      - field: task_name
        label: 任务名称
      - field: status
        label: 状态
        format: status_badge
      - field: assignee_name
        label: 负责人
      - field: progress
        label: 进度
        format: percentage

  - id: issue_chart
    title: 问题分布
    type: chart
    chart_type: pie
    source: issues
    label_field: severity
    value_field: count

# === 导出配置 ===
exports:
  json:
    enabled: true
  pdf:
    enabled: true
    template: project_weekly.html
    orientation: portrait
  excel:
    enabled: true
    sheets:
      - name: 概览
        section: summary
      - name: 任务明细
        section: task_list
  word:
    enabled: false
```

**关键设计点：**

1. **Jinja2 表达式** - 用 `{{ }}` 支持动态值计算
2. **类型化参数** - 自动验证输入参数
3. **多数据源** - 可混合 SQL 查询和服务调用
4. **Section 类型** - `metrics`（指标卡）、`table`（表格）、`chart`（图表）
5. **格式化器** - `status_badge`、`percentage` 等内置格式化

## 目录结构

```
app/services/report_framework/
├── __init__.py
├── engine.py              # 报告引擎核心
├── config_loader.py       # YAML 配置加载与验证
├── data_resolver.py       # 数据源解析器
├── cache_manager.py       # 缓存管理
├── schedule_manager.py    # 定时任务管理
│
├── data_sources/          # 数据源类型
│   ├── __init__.py
│   ├── base.py            # DataSource 基类
│   ├── query.py           # SQL 查询执行器
│   ├── service.py         # 服务方法调用器
│   └── aggregate.py       # 聚合函数
│
├── renderers/             # 导出渲染器
│   ├── __init__.py
│   ├── base.py            # Renderer 基类
│   ├── json_renderer.py
│   ├── pdf_renderer.py
│   ├── excel_renderer.py
│   └── word_renderer.py
│
├── formatters/            # 值格式化器
│   ├── __init__.py
│   └── builtin.py         # status_badge, percentage, currency 等
│
├── expressions/           # 表达式引擎
│   ├── __init__.py
│   ├── parser.py          # Jinja2 环境配置
│   └── filters.py         # 自定义过滤器
│
└── templates/             # 导出模板
    ├── pdf/
    │   └── base.html
    └── word/
        └── base.docx

app/report_configs/        # 报告配置文件（YAML）
├── project/
│   ├── weekly.yaml
│   ├── monthly.yaml
│   └── cost_analysis.yaml
├── department/
│   ├── workload.yaml
│   └── monthly.yaml
├── sales/
│   ├── funnel.yaml
│   └── forecast.yaml
└── _schema.yaml           # 配置 JSON Schema（用于验证）
```

## 核心类设计

```python
# engine.py
class ReportEngine:
    """报告引擎 - 核心编排器"""

    def __init__(self, db: Session, config_dir: str = "app/report_configs"):
        self.db = db
        self.config_loader = ConfigLoader(config_dir)
        self.data_resolver = DataResolver(db)
        self.cache = CacheManager()
        self.renderers = {
            "json": JsonRenderer(),
            "pdf": PdfRenderer(),
            "excel": ExcelRenderer(),
            "word": WordRenderer(),
        }

    def generate(
        self,
        report_code: str,
        params: dict,
        format: str = "json",
        user: User = None,
    ) -> ReportResult:
        """
        生成报告

        Args:
            report_code: 报告代码，如 "PROJECT_WEEKLY"
            params: 参数字典
            format: 导出格式
            user: 当前用户（用于权限检查）

        Returns:
            ReportResult: 包含 data, file_path, metadata
        """
        # 1. 加载配置
        config = self.config_loader.get(report_code)

        # 2. 权限检查
        self._check_permission(config, user)

        # 3. 参数验证
        validated_params = self._validate_params(config, params)

        # 4. 检查缓存
        if cached := self.cache.get(config, validated_params):
            return cached

        # 5. 获取数据
        context = self.data_resolver.resolve_all(
            config.data_sources,
            validated_params
        )

        # 6. 渲染 sections
        rendered_sections = self._render_sections(config.sections, context)

        # 7. 导出
        result = self.renderers[format].render(config, rendered_sections)

        # 8. 缓存结果
        self.cache.set(config, validated_params, result)

        return result
```

## 统一 API 端点

```python
# app/api/v1/endpoints/reports/unified.py

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/available")
def list_available_reports(current_user, db) -> List[ReportMeta]:
    """获取当前用户可访问的报告列表"""

@router.post("/{report_code}/generate")
def generate_report(report_code, params, format, current_user, db) -> ReportResponse:
    """生成报告"""

@router.get("/download/{file_id}")
def download_report(file_id, current_user) -> FileResponse:
    """下载已生成的报告文件"""

@router.get("/{report_code}/schema")
def get_report_schema(report_code, current_user, db) -> ReportSchema:
    """获取报告配置 Schema（前端用于动态渲染表单）"""

@router.post("/{report_code}/preview")
def preview_report(report_code, params, current_user, db) -> ReportPreview:
    """预览报告（只返回前 N 条数据）"""
```

**API 使用示例：**

```bash
# 1. 获取可用报告
GET /api/v1/reports/available

# 2. 获取报告参数 Schema
GET /api/v1/reports/PROJECT_WEEKLY/schema

# 3. 生成 JSON 报告
POST /api/v1/reports/PROJECT_WEEKLY/generate?format=json
{"project_id": 123, "start_date": "2026-01-13", "end_date": "2026-01-19"}

# 4. 生成 PDF 报告
POST /api/v1/reports/PROJECT_WEEKLY/generate?format=pdf
{"project_id": 123, "start_date": "2026-01-13", "end_date": "2026-01-19"}
# 返回: {"download_url": "/api/v1/reports/download/abc123"}
```

## 迁移策略

### 阶段划分

| 阶段 | 内容 |
|------|------|
| Phase 1 | 框架搭建 - 核心组件 + JSON 渲染器 + 示例配置 |
| Phase 2 | 渲染器完善 - PDF/Excel/Word 渲染器 |
| Phase 3 | 报告迁移 - 现有服务转为 YAML 配置 |
| Phase 4 | 清理旧代码 - 删除重复服务 |

### 现有服务迁移映射

| 现有服务 | 迁移方式 | 目标配置 |
|---------|---------|---------|
| `report_data_generation/project_reports.py` | 转为 YAML | `project/weekly.yaml`, `project/monthly.yaml` |
| `report_data_generation/dept_reports.py` | 转为 YAML | `department/monthly.yaml` |
| `report_data_generation/analysis_reports.py` | 转为 YAML | `analysis/cost.yaml`, `analysis/risk.yaml` |
| `template_report/*` | 删除（重复） | - |
| `acceptance_report_service.py` | 转为 YAML + PDF 模板 | `acceptance/fat.yaml` |
| `meeting_report_service.py` | 转为 YAML + Word 模板 | `meeting/weekly.yaml` |
| `shortage_report_service.py` | 转为 YAML | `inventory/shortage.yaml` |

### 保留为数据源的服务

以下统计服务保留，作为数据源被报告配置引用：

- `issue_statistics_service.py`
- `payment_statistics_service.py`
- `kit_rate_statistics_service.py`
- `alert/alert_statistics_service.py`

### 删除清单（Phase 4）

```
删除:
├── app/services/report_data_generation/
├── app/services/template_report/
├── app/services/acceptance_report_service.py
├── app/services/meeting_report_service.py
├── app/services/meeting_report_docx_service.py
├── app/services/meeting_report_helpers.py
├── app/services/shortage_report_service.py
├── app/services/sales_monthly_report_service.py
├── app/services/timesheet_report_service.py
├── app/services/rd_report_data_service.py
└── app/services/report_export_service.py
```

## 错误处理

```python
# 异常类层次
class ReportError(Exception): pass
class ConfigError(ReportError): pass      # 配置错误
class PermissionError(ReportError): pass  # 权限错误
class ParameterError(ReportError): pass   # 参数错误
class DataSourceError(ReportError): pass  # 数据源错误
class RenderError(ReportError): pass      # 渲染错误
```

**API 层统一错误响应：**

| 异常类型 | HTTP 状态码 |
|---------|------------|
| ConfigError | 400 |
| PermissionError | 403 |
| ParameterError | 422 |
| DataSourceError | 500 |
| RenderError | 500 |

## 测试策略

```
tests/unit/test_report_framework/
├── test_config_loader.py      # 配置加载测试
├── test_data_resolver.py      # 数据源解析测试
├── test_expressions.py        # Jinja2 表达式测试
├── test_renderers/
│   ├── test_json_renderer.py
│   ├── test_pdf_renderer.py
│   ├── test_excel_renderer.py
│   └── test_word_renderer.py
└── test_engine.py             # 集成测试
```

## 总结

统一报告框架通过配置驱动的方式，实现：

- **零代码添加报告** - 新报告只需编写 YAML 配置
- **统一入口** - 所有报告通过 `/api/v1/reports` 访问
- **全格式支持** - JSON/PDF/Excel/Word 一键导出
- **性能优化** - 缓存 + 定时预生成
- **代码精简** - 删除 12+ 个重复服务文件
