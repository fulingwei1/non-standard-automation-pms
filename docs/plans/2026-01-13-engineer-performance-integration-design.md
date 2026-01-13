# 工程师绩效系统集成设计方案

> **版本**: 1.0
> **日期**: 2026-01-13
> **方案类型**: 扩展集成（基于现有绩效系统扩展）

---

## 一、集成策略

### 1.1 方案选择：扩展现有系统

经评估，选择**扩展方案**而非替换或共存：

| 维度 | 替换 | 共存 | 扩展（选定） |
|------|------|------|-------------|
| 数据一致性 | 丢失历史数据 | 数据分散 | ✅ 统一管理 |
| 维护成本 | 中 | 高（两套系统） | ✅ 低 |
| 未来扩展 | 需重建基础设施 | 难以统一 | ✅ 易于扩展 |
| 复用现有代码 | ❌ 浪费 | 部分 | ✅ 最大化复用 |

### 1.2 复用与扩展

**复用现有模块：**
- `PerformancePeriod` - 考核周期管理
- `PerformanceAppeal` - 绩效申诉流程
- `PerformanceRankingSnapshot` - 排行榜快照
- `MonthlyWorkSummary` - 月度工作总结

**扩展现有模块：**
- `PerformanceResult` - 增加五维得分字段和岗位类型
- `PerformanceIndicator` - 扩展工程师专属指标

**新增模块：**
- 工程师档案、跨部门互评、知识贡献
- 机械/测试/电气工程师专属数据表

---

## 二、数据模型设计

### 2.1 扩展 PerformanceResult

修改现有字段映射到五维框架：

```python
# 字段映射
workload_score      → technical_score      # 技术能力 (30%)
task_score          → execution_score      # 项目执行 (25%)
quality_score       → cost_quality_score   # 成本/质量 (20%)
collaboration_score → collaboration_score  # 团队协作 (10%) - 保留
growth_score        → knowledge_score      # 知识沉淀 (15%)

# 新增字段
job_type            # 岗位类型：mechanical/test/electrical
job_level           # 职级：junior/intermediate/senior/expert
dimension_details   # JSON，各维度具体指标得分
```

### 2.2 新增核心模型

#### EngineerProfile（工程师档案）

```python
class EngineerProfile(Base, TimestampMixin):
    """工程师档案 - 扩展用户信息"""
    __tablename__ = 'engineer_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)

    # 岗位信息
    job_type = Column(String(20))      # mechanical/test/electrical
    job_level = Column(String(20))     # junior/intermediate/senior/expert

    # 技能标签
    skills = Column(JSON)              # ["SolidWorks", "AutoCAD"] 等
    certifications = Column(JSON)      # 资质证书

    # 入职/晋升时间
    job_start_date = Column(Date)
    level_start_date = Column(Date)
```

#### CollaborationRating（跨部门互评）

```python
class CollaborationRating(Base, TimestampMixin):
    """跨部门协作评价"""
    __tablename__ = 'collaboration_rating'

    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('performance_period.id'))

    # 评价双方
    rater_id = Column(Integer, ForeignKey('users.id'))
    ratee_id = Column(Integer, ForeignKey('users.id'))
    rater_job_type = Column(String(20))
    ratee_job_type = Column(String(20))

    # 四维评分（1-5分）
    communication_score = Column(Integer)   # 沟通配合
    response_score = Column(Integer)        # 响应速度
    delivery_score = Column(Integer)        # 交付质量
    interface_score = Column(Integer)       # 接口规范

    comment = Column(Text)
```

#### KnowledgeContribution（知识贡献）

```python
class KnowledgeContribution(Base, TimestampMixin):
    """知识贡献记录"""
    __tablename__ = 'knowledge_contribution'

    id = Column(Integer, primary_key=True)
    contributor_id = Column(Integer, ForeignKey('users.id'))

    # 贡献类型
    contribution_type = Column(String(30))  # document/template/module/training/patent
    job_type = Column(String(20))

    # 贡献内容
    title = Column(String(200))
    description = Column(Text)
    file_path = Column(String(500))

    # 复用统计
    reuse_count = Column(Integer, default=0)
    rating_score = Column(Numeric(3,2))
    rating_count = Column(Integer, default=0)

    # 审核状态
    status = Column(String(20))             # draft/pending/approved/rejected
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
```

### 2.3 机械工程师专属模型

#### DesignReview（设计评审）

```python
class DesignReview(Base, TimestampMixin):
    """设计评审记录"""
    __tablename__ = 'design_review'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    designer_id = Column(Integer, ForeignKey('users.id'))

    design_name = Column(String(200))
    design_type = Column(String(50))        # assembly/part/drawing
    version = Column(String(20))

    review_date = Column(Date)
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    result = Column(String(20))             # passed/rejected/conditional
    is_first_pass = Column(Boolean)
    issues_found = Column(Integer, default=0)
    review_comments = Column(Text)
```

#### MechanicalDebugIssue（机械调试问题）

```python
class MechanicalDebugIssue(Base, TimestampMixin):
    """机械调试问题记录"""
    __tablename__ = 'mechanical_debug_issue'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    responsible_id = Column(Integer, ForeignKey('users.id'))

    issue_description = Column(Text)
    severity = Column(String(20))           # critical/major/minor
    root_cause = Column(String(50))         # design/process/material/other

    found_date = Column(Date)
    resolved_date = Column(Date)
    resolution = Column(Text)
    cost_impact = Column(Numeric(12,2))
```

### 2.4 测试工程师专属模型

#### TestBugRecord（Bug记录）

```python
class TestBugRecord(Base, TimestampMixin):
    """测试Bug记录"""
    __tablename__ = 'test_bug_record'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    reporter_id = Column(Integer, ForeignKey('users.id'))
    assignee_id = Column(Integer, ForeignKey('users.id'))

    title = Column(String(200))
    description = Column(Text)
    severity = Column(String(20))           # critical/major/normal/minor
    bug_type = Column(String(30))           # logic/interface/performance/compatibility
    found_stage = Column(String(30))        # internal_debug/site_debug/acceptance/production

    status = Column(String(20))             # open/in_progress/resolved/closed
    found_time = Column(DateTime)
    resolved_time = Column(DateTime)
    fix_duration_hours = Column(Numeric(6,2))
    resolution = Column(Text)
```

#### CodeModule（代码模块库）

```python
class CodeModule(Base, TimestampMixin):
    """代码模块库"""
    __tablename__ = 'code_module'

    id = Column(Integer, primary_key=True)
    contributor_id = Column(Integer, ForeignKey('users.id'))

    module_name = Column(String(100))
    category = Column(String(50))           # communication/data/ui/driver/utility
    language = Column(String(30))           # labview/csharp/python
    description = Column(Text)

    reuse_count = Column(Integer, default=0)
    projects_used = Column(JSON)
```

### 2.5 电气工程师专属模型

#### PlcProgramVersion（PLC程序版本）

```python
class PlcProgramVersion(Base, TimestampMixin):
    """PLC程序版本"""
    __tablename__ = 'plc_program_version'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    programmer_id = Column(Integer, ForeignKey('users.id'))

    program_name = Column(String(200))
    plc_brand = Column(String(30))          # siemens/mitsubishi/omron/beckhoff/inovance
    version = Column(String(20))

    first_debug_date = Column(Date)
    is_first_pass = Column(Boolean)
    debug_issues = Column(Integer, default=0)
    debug_hours = Column(Numeric(6,2))
```

#### PlcModuleLibrary（PLC功能块库）

```python
class PlcModuleLibrary(Base, TimestampMixin):
    """PLC功能块库"""
    __tablename__ = 'plc_module_library'

    id = Column(Integer, primary_key=True)
    contributor_id = Column(Integer, ForeignKey('users.id'))

    module_name = Column(String(100))
    category = Column(String(50))           # motion/io/communication/data/alarm/process
    plc_brand = Column(String(30))
    description = Column(Text)

    reuse_count = Column(Integer, default=0)
    rating_score = Column(Numeric(3,2))
```

---

## 三、API 端点设计

### 3.1 主要端点结构

```
/api/v1/engineer-performance/
├── /summary                      # 总览
│   ├── GET /company              # 公司整体概况
│   └── GET /by-job-type/{type}   # 按岗位类型概况
│
├── /ranking                      # 排名
│   ├── GET /                     # 综合排名（支持筛选）
│   ├── GET /by-department        # 按部门排名
│   ├── GET /by-job-type          # 按岗位类型排名
│   └── GET /top                  # Top N 工程师
│
├── /engineer/{id}                # 个人绩效
│   ├── GET /                     # 个人绩效详情
│   ├── GET /trend                # 历史趋势
│   ├── GET /comparison           # 同岗位对比
│   └── GET /metrics              # 指标明细
│
├── /collaboration                # 跨部门协作
│   ├── GET /matrix               # 协作评价矩阵
│   ├── GET /received/{id}        # 收到的评价
│   ├── GET /given/{id}           # 给出的评价
│   └── POST /                    # 提交互评
│
├── /knowledge                    # 知识贡献
│   ├── GET /                     # 贡献列表
│   ├── GET /ranking              # 贡献排行
│   ├── POST /                    # 提交贡献
│   └── POST /{id}/reuse          # 记录复用
│
├── /config                       # 配置管理
│   ├── GET /weights              # 权重配置列表
│   ├── PUT /weights              # 更新权重配置
│   └── GET /grades               # 等级规则
│
└── /calculate                    # 计算任务
    ├── POST /trigger             # 触发计算
    └── GET /status/{task_id}     # 计算状态
```

### 3.2 岗位专属端点

```
/api/v1/engineer-performance/mechanical/
├── /design-reviews               # 设计评审管理
├── /debug-issues                 # 调试问题管理
└── /reuse-records                # 设计复用记录

/api/v1/engineer-performance/test/
├── /bugs                         # Bug 管理
├── /code-reviews                 # 代码评审
└── /code-modules                 # 代码模块库

/api/v1/engineer-performance/electrical/
├── /plc-programs                 # PLC 程序版本
├── /plc-modules                  # PLC 模块库
└── /drawings                     # 电气图纸版本
```

---

## 四、Service 层设计

| Service | 职责 |
|---------|------|
| `EngineerPerformanceService` | 绩效计算核心逻辑 |
| `EngineerRankingService` | 排名计算与统计 |
| `CollaborationService` | 跨部门互评管理 |
| `KnowledgeContributionService` | 知识贡献管理 |
| `EngineerMetricsCollector` | 从各系统采集指标数据 |
| `PerformanceScoreCalculator` | 五维得分计算引擎 |

---

## 五、文件结构

```
app/
├── models/
│   └── engineer_performance.py      # 所有新增模型
│
├── schemas/
│   └── engineer_performance.py      # Pydantic schemas
│
├── services/
│   ├── engineer_performance_service.py
│   ├── engineer_ranking_service.py
│   ├── engineer_metrics_collector.py
│   ├── collaboration_service.py
│   └── knowledge_contribution_service.py
│
├── api/v1/endpoints/
│   └── engineer_performance/
│       ├── __init__.py
│       ├── summary.py
│       ├── ranking.py
│       ├── engineer.py
│       ├── collaboration.py
│       ├── knowledge.py
│       ├── config.py
│       ├── mechanical.py
│       ├── test.py
│       └── electrical.py

migrations/
└── 20260113_engineer_performance_sqlite.sql

frontend/src/pages/
├── EngineerPerformanceDashboard.jsx
├── EngineerPerformanceRanking.jsx
├── EngineerPerformanceDetail.jsx
├── EngineerCollaboration.jsx
├── EngineerKnowledge.jsx
└── EngineerPerformanceConfig.jsx
```

---

## 六、实施步骤

| 步骤 | 内容 | 依赖 |
|------|------|------|
| 1 | 创建数据库迁移文件 | - |
| 2 | 创建 `engineer_performance.py` 模型 | 步骤 1 |
| 3 | 创建 Pydantic schemas | 步骤 2 |
| 4 | 实现 `EngineerMetricsCollector` | 步骤 2 |
| 5 | 实现 `PerformanceScoreCalculator` | 步骤 4 |
| 6 | 实现 `EngineerPerformanceService` | 步骤 5 |
| 7 | 实现其他 Services | 步骤 6 |
| 8 | 创建 API 端点 | 步骤 7 |
| 9 | 注册路由到主 API | 步骤 8 |
| 10 | 创建前端页面 | 步骤 8 |

---

## 七、五维评价框架

### 7.1 各岗位指标对照

| 维度 | 权重 | 机械工程师 | 测试工程师 | 电气工程师 |
|-----|------|-----------|-----------|-----------|
| **技术能力** | 30% | 设计一次通过率、ECN责任率、调试问题密度 | 程序一次调通率、Bug修复时长、代码审查通过率 | 图纸一次通过率、PLC一次调通率、调试效率 |
| **项目执行** | 25% | 按时完成率、BOM交付及时率、难度加权产出 | 按时完成率、现场响应率、版本迭代效率 | 按时完成率、图纸交付及时率、现场响应率 |
| **成本/质量** | 20% | 标准件使用率、设计复用率 | 程序稳定性、测试覆盖率、误测率 | 标准件使用率、选型准确率 |
| **知识沉淀** | 15% | 技术文档、标准模板、被引用次数 | 代码模块复用率、公共模块贡献 | PLC模块贡献、标准模板 |
| **团队协作** | 10% | 电气/测试部配合评分 | 机械/电气部配合评分 | 机械/测试部配合评分 |

### 7.2 等级划分

| 等级 | 名称 | 分数范围 |
|-----|------|---------|
| S | 优秀 | 85-100分 |
| A | 良好 | 70-84分 |
| B | 合格 | 60-69分 |
| C | 待改进 | 40-59分 |
| D | 不合格 | 0-39分 |

### 7.3 权重配置原则

**重要：权重只能按「岗位类型 + 职级」配置，不能针对个人！**

确保同一岗位同一级别的所有工程师使用相同的评价标准。
