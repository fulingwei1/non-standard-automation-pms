# 测试工程师绩效评价体系设计

## 一、岗位特点分析

### 1.1 工作职责

| 职责领域 | 具体内容 |
|---------|---------|
| **测试程序开发** | LabVIEW测试程序编写、测试流程设计、测试用例实现 |
| **上位机开发** | C#界面开发、数据采集与处理、与PLC/仪器通讯 |
| **系统集成** | 仪器驱动集成、硬件通讯调试、系统联调 |
| **现场调试** | 测试程序部署、参数调优、问题排查 |
| **技术支持** | 客户培训、远程支持、问题响应 |

### 1.2 技术栈要求

```
┌─────────────────────────────────────────────────────────────────┐
│                    测试工程师技术栈                               │
├─────────────────────────────────────────────────────────────────┤
│  核心技能                                                        │
│  ├─ LabVIEW：VI开发、状态机、生产者消费者、Actor Framework      │
│  ├─ C#/.NET：WinForms/WPF、数据库操作、串口/网口通讯            │
│  └─ 测试技术：测试方法论、测试用例设计、数据分析                 │
│                                                                  │
│  硬件接口                                                        │
│  ├─ 仪器通讯：VISA、GPIB、RS232/485、以太网                     │
│  ├─ 数据采集：DAQ、数字IO、模拟量采集                           │
│  └─ 运动控制：PLC通讯、运动卡驱动                                │
│                                                                  │
│  辅助技能                                                        │
│  ├─ 数据库：SQL Server、MySQL、SQLite                           │
│  ├─ 版本控制：Git、SVN                                          │
│  └─ 文档能力：测试规范、操作手册、技术文档                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、评价维度设计

### 2.1 五维评价体系

```
                        测试工程师评价维度
                              │
        ┌─────────┬─────────┼─────────┬─────────┐
        ▼         ▼         ▼         ▼         ▼
    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
    │技术能力│ │项目执行│ │质量保障│ │知识沉淀│ │团队协作│
    │ 30%   │ │ 25%   │ │ 20%   │ │ 15%   │ │ 10%   │
    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
    一次调通率  按时完成率  程序稳定性  代码复用率  跨部门评分
    Bug修复效率 任务产出    测试覆盖率  文档贡献    响应及时性
    技术难度    现场支持    客户投诉    技术分享    新人带教
```

### 2.2 指标详细定义

#### 技术能力（权重30%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **程序一次调通率** | 测试程序首次部署即可正常运行的比例 | 一次调通项目数 / 总项目数 × 100% | ≥80% |
| **Bug修复效率** | 从Bug报告到解决的平均时长 | 平均修复时长（小时） | ≤4小时（一般）≤24小时（复杂） |
| **技术难度系数** | 承担任务的技术复杂度 | 加权平均难度系数（1-5） | ≥3.0 |
| **代码规范符合率** | 代码审查通过率 | 审查通过数 / 提交数 × 100% | ≥90% |

#### 项目执行（权重25%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **任务按时完成率** | 在计划时间内完成的任务比例 | 按时完成数 / 总任务数 × 100% | ≥90% |
| **任务产出量** | 完成的任务数量（难度加权） | Σ(任务数 × 难度系数) | 根据级别定 |
| **现场支持响应** | 现场问题响应及时性 | 2小时内响应率 | ≥95% |
| **版本迭代效率** | 程序版本更新频率与质量 | 有效版本数 / 总版本数 | ≥85% |

#### 质量保障（权重20%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **程序稳定性** | 交付后运行稳定性 | 30天内无故障天数 / 30 × 100% | ≥95% |
| **测试覆盖率** | 测试用例覆盖程度 | 已覆盖测试点 / 总测试点 × 100% | ≥90% |
| **客户投诉率** | 因软件问题导致的客户投诉 | 投诉次数 / 交付项目数 | ≤5% |
| **误测率控制** | 假阳/假阴率 | 误测数 / 总测试数 × 100% | ≤0.1% |

#### 知识沉淀（权重15%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **代码/模块复用率** | VI/组件被其他项目复用的比例 | 被复用模块数 / 总模块数 × 100% | ≥30% |
| **文档贡献** | 技术文档、操作手册编写 | 文档数量 | ≥2篇/季度 |
| **技术分享** | 内部技术培训和分享 | 分享次数 | ≥1次/季度 |
| **代码库贡献** | 对公共代码库的贡献 | 提交的可复用模块数 | ≥2个/季度 |

#### 团队协作（权重10%）

| 指标 | 定义 | 计算方式 | 目标值 |
|-----|------|---------|--------|
| **跨部门协作评分** | 机械/电气部门的评价 | 协作评分（1-5） | ≥4.0 |
| **响应及时性** | 对内部需求的响应速度 | 24小时内响应率 | ≥95% |
| **新人带教** | 指导新人的效果 | 带教新人数 × 评价系数 | 按实际统计 |
| **代码审查参与** | 参与他人代码审查 | 审查次数 | ≥4次/月 |

---

## 三、数据采集设计

### 3.1 数据源映射

```
┌─────────────────────────────────────────────────────────────────┐
│                      数据采集架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  项目管理系统                  代码管理系统                       │
│  ├─ 任务分配表 ──────────┐    ├─ Git提交记录 ──────────┐        │
│  ├─ 任务完成记录 ────────┤    ├─ 代码审查记录 ────────┤        │
│  ├─ 里程碑节点 ──────────┤    └─ 分支合并记录 ────────┤        │
│  └─ 项目人员分配 ────────┤                            │        │
│                          ▼                            ▼        │
│                    ┌─────────────────────────────────────┐     │
│                    │       测试工程师绩效数据库           │     │
│                    └─────────────────────────────────────┘     │
│                          ▲                            ▲        │
│  问题跟踪系统            │    质量管理系统              │        │
│  ├─ Bug报告 ─────────────┤    ├─ 客户投诉 ─────────────┤        │
│  ├─ 修复记录 ────────────┤    ├─ 现场问题 ────────────┤        │
│  └─ 现场支持工单 ────────┘    └─ 误测记录 ────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 现有系统数据复用

| 评价指标 | 数据来源 | 提取方式 |
|---------|---------|---------|
| 任务完成率 | project_task | 直接提取 `actual_end <= planned_end` |
| 项目参与 | pmo_resource_allocation | 按 `resource_id` 统计 |
| Bug修复 | 问题跟踪表 | 统计 `issue_type='软件Bug'` |
| 现场支持 | 客服工单表 | 统计 `responsible_dept='测试部'` |
| 客户投诉 | 客户反馈表 | 统计 `complaint_type='软件问题'` |

### 3.3 需补充的数据采集

#### 任务表补充字段

```sql
ALTER TABLE project_task 
ADD COLUMN first_debug_pass TINYINT(1) DEFAULT NULL COMMENT '程序是否一次调通：0否 1是',
ADD COLUMN code_review_status ENUM('pending','approved','rejected') COMMENT '代码审查状态',
ADD COLUMN code_review_score DECIMAL(3,1) COMMENT '代码审查评分(1-5)',
ADD COLUMN test_coverage DECIMAL(5,2) COMMENT '测试覆盖率(%)',
ADD COLUMN difficulty_level INT DEFAULT 3 COMMENT '任务难度(1-5)';
```

#### 新增程序版本记录表

```sql
CREATE TABLE test_program_version (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    program_name VARCHAR(200) NOT NULL COMMENT '程序名称',
    version VARCHAR(20) NOT NULL COMMENT '版本号',
    
    -- 开发者信息
    developer_id BIGINT NOT NULL COMMENT '开发者ID',
    developer_name VARCHAR(50) COMMENT '开发者姓名',
    
    -- 版本信息
    version_type ENUM('major','minor','patch','hotfix') COMMENT '版本类型',
    change_log TEXT COMMENT '变更说明',
    
    -- 质量指标
    first_debug_pass BOOLEAN COMMENT '一次调通',
    test_coverage DECIMAL(5,2) COMMENT '测试覆盖率',
    code_lines INT COMMENT '代码行数',
    
    -- 部署信息
    deploy_date DATE COMMENT '部署日期',
    deploy_status ENUM('success','failed','rollback') COMMENT '部署状态',
    
    -- 运行稳定性（30天跟踪）
    stability_score DECIMAL(5,2) COMMENT '稳定性评分',
    bug_count_30days INT DEFAULT 0 COMMENT '30天内Bug数',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_developer (developer_id),
    INDEX idx_deploy_date (deploy_date)
) COMMENT '测试程序版本记录表';
```

#### 新增Bug跟踪表（测试专用）

```sql
CREATE TABLE test_bug_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bug_no VARCHAR(30) NOT NULL COMMENT 'Bug编号',
    project_id BIGINT NOT NULL COMMENT '项目ID',
    program_version_id BIGINT COMMENT '程序版本ID',
    
    -- Bug信息
    bug_title VARCHAR(200) NOT NULL COMMENT 'Bug标题',
    bug_type ENUM('功能缺陷','性能问题','界面问题','通讯异常','数据异常','其他') COMMENT 'Bug类型',
    severity ENUM('致命','严重','一般','轻微') NOT NULL COMMENT '严重程度',
    priority ENUM('紧急','高','中','低') NOT NULL COMMENT '优先级',
    
    -- 责任信息
    reporter_id BIGINT COMMENT '报告人',
    reporter_name VARCHAR(50) COMMENT '报告人姓名',
    assignee_id BIGINT COMMENT '负责人',
    assignee_name VARCHAR(50) COMMENT '负责人姓名',
    
    -- 来源
    source ENUM('内部测试','现场调试','客户反馈','运维监控') COMMENT 'Bug来源',
    
    -- 时间跟踪
    reported_at DATETIME NOT NULL COMMENT '报告时间',
    assigned_at DATETIME COMMENT '分配时间',
    started_at DATETIME COMMENT '开始处理时间',
    resolved_at DATETIME COMMENT '解决时间',
    closed_at DATETIME COMMENT '关闭时间',
    
    -- 解决方案
    root_cause TEXT COMMENT '根因分析',
    solution TEXT COMMENT '解决方案',
    
    -- 状态
    status ENUM('新建','已分配','处理中','已解决','已验证','已关闭','重新打开') DEFAULT '新建',
    
    -- 统计字段
    response_hours DECIMAL(6,2) COMMENT '响应时长(小时)',
    resolve_hours DECIMAL(6,2) COMMENT '解决时长(小时)',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_assignee (assignee_id),
    INDEX idx_status (status),
    INDEX idx_reported_at (reported_at)
) COMMENT '测试Bug跟踪表';

-- 触发器：自动计算响应和解决时长
DELIMITER //
CREATE TRIGGER calc_bug_hours BEFORE UPDATE ON test_bug_record
FOR EACH ROW
BEGIN
    IF NEW.assigned_at IS NOT NULL AND OLD.assigned_at IS NULL THEN
        SET NEW.response_hours = TIMESTAMPDIFF(MINUTE, NEW.reported_at, NEW.assigned_at) / 60.0;
    END IF;
    IF NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL THEN
        SET NEW.resolve_hours = TIMESTAMPDIFF(MINUTE, 
            COALESCE(NEW.started_at, NEW.assigned_at, NEW.reported_at), 
            NEW.resolved_at) / 60.0;
    END IF;
END //
DELIMITER ;
```

#### 新增代码复用记录表

```sql
CREATE TABLE code_reuse_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 原始模块
    original_module_id BIGINT NOT NULL COMMENT '原始模块ID',
    original_module_name VARCHAR(200) COMMENT '模块名称',
    original_project_id BIGINT COMMENT '原始项目ID',
    original_developer_id BIGINT COMMENT '原始开发者',
    
    -- 复用信息
    reuse_project_id BIGINT NOT NULL COMMENT '复用项目ID',
    reuse_developer_id BIGINT NOT NULL COMMENT '复用者ID',
    reuse_type ENUM('直接复用','修改复用','参考借鉴') COMMENT '复用类型',
    
    -- 模块类型
    module_type ENUM('LabVIEW_VI','LabVIEW_Class','CSharp_Class','CSharp_Control','通用工具','仪器驱动') COMMENT '模块类型',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_original_developer (original_developer_id),
    INDEX idx_reuse_project (reuse_project_id)
) COMMENT '代码复用记录表';
```

#### 测试工程师绩效汇总表

```sql
CREATE TABLE test_engineer_performance (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    engineer_id BIGINT NOT NULL COMMENT '工程师ID',
    engineer_name VARCHAR(50) COMMENT '工程师姓名',
    
    period_type ENUM('monthly','quarterly','yearly') NOT NULL,
    period_value VARCHAR(10) NOT NULL COMMENT '2024-11/2024Q4',
    
    -- 技术能力指标
    first_debug_pass_rate DECIMAL(5,2) COMMENT '一次调通率(%)',
    avg_bug_resolve_hours DECIMAL(6,2) COMMENT '平均Bug修复时长(小时)',
    code_review_pass_rate DECIMAL(5,2) COMMENT '代码审查通过率(%)',
    avg_difficulty_level DECIMAL(3,1) COMMENT '平均任务难度',
    
    -- 项目执行指标
    task_count INT COMMENT '完成任务数',
    on_time_rate DECIMAL(5,2) COMMENT '按时完成率(%)',
    weighted_output DECIMAL(8,2) COMMENT '难度加权产出',
    field_support_count INT COMMENT '现场支持次数',
    field_response_rate DECIMAL(5,2) COMMENT '现场2小时响应率(%)',
    
    -- 质量指标
    program_stability DECIMAL(5,2) COMMENT '程序稳定性(%)',
    avg_test_coverage DECIMAL(5,2) COMMENT '平均测试覆盖率(%)',
    customer_complaint_count INT COMMENT '客户投诉次数',
    false_test_rate DECIMAL(5,4) COMMENT '误测率(%)',
    
    -- 知识沉淀指标
    reused_module_count INT COMMENT '被复用模块数',
    doc_contribution_count INT COMMENT '文档贡献数',
    tech_share_count INT COMMENT '技术分享次数',
    code_lib_contribution INT COMMENT '代码库贡献数',
    
    -- 协作指标
    cross_dept_score DECIMAL(3,1) COMMENT '跨部门协作评分',
    code_review_participation INT COMMENT '代码审查参与次数',
    mentee_count INT COMMENT '带教新人数',
    
    -- 维度得分
    technical_score DECIMAL(5,2) COMMENT '技术能力得分',
    execution_score DECIMAL(5,2) COMMENT '项目执行得分',
    quality_score DECIMAL(5,2) COMMENT '质量保障得分',
    knowledge_score DECIMAL(5,2) COMMENT '知识沉淀得分',
    collaboration_score DECIMAL(5,2) COMMENT '团队协作得分',
    
    -- 综合结果
    total_score DECIMAL(5,2) COMMENT '综合得分',
    grade ENUM('优秀','良好','合格','待改进') COMMENT '评价等级',
    department_rank INT COMMENT '部门排名',
    
    calculated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_engineer_period (engineer_id, period_type, period_value),
    INDEX idx_period (period_type, period_value)
) COMMENT '测试工程师绩效汇总表';
```

---

## 四、评分算法

### 4.1 权重配置

```python
# 测试工程师评价权重配置
TEST_ENGINEER_WEIGHTS = {
    "技术能力": {
        "weight": 0.30,
        "sub_items": {
            "一次调通率": 0.35,
            "Bug修复效率": 0.30,
            "代码审查通过率": 0.20,
            "技术难度系数": 0.15
        }
    },
    "项目执行": {
        "weight": 0.25,
        "sub_items": {
            "按时完成率": 0.40,
            "难度加权产出": 0.30,
            "现场响应率": 0.30
        }
    },
    "质量保障": {
        "weight": 0.20,
        "sub_items": {
            "程序稳定性": 0.40,
            "测试覆盖率": 0.30,
            "客户投诉控制": 0.20,
            "误测率控制": 0.10
        }
    },
    "知识沉淀": {
        "weight": 0.15,
        "sub_items": {
            "模块复用率": 0.40,
            "文档贡献": 0.30,
            "技术分享": 0.20,
            "代码库贡献": 0.10
        }
    },
    "团队协作": {
        "weight": 0.10,
        "sub_items": {
            "跨部门评分": 0.50,
            "代码审查参与": 0.30,
            "新人带教": 0.20
        }
    }
}
```

### 4.2 评分计算逻辑

```python
def calculate_test_engineer_score(engineer_id, period):
    """计算测试工程师综合绩效得分"""
    
    scores = {}
    
    # 1. 技术能力得分
    versions = get_program_versions(engineer_id, period)
    first_debug_rate = sum(1 for v in versions if v.first_debug_pass) / max(len(versions), 1)
    
    bugs = get_bug_records(engineer_id, period)
    avg_resolve_hours = sum(b.resolve_hours for b in bugs if b.resolve_hours) / max(len(bugs), 1)
    
    tasks = get_tasks(engineer_id, period)
    code_review_pass = sum(1 for t in tasks if t.code_review_status == 'approved') / max(len(tasks), 1)
    avg_difficulty = sum(t.difficulty_level for t in tasks) / max(len(tasks), 1)
    
    scores["技术能力"] = (
        normalize_score(first_debug_rate, target=0.80) * 0.35 +
        normalize_score(1 / (1 + avg_resolve_hours / 8), target=0.70) * 0.30 +  # 8小时为基准
        normalize_score(code_review_pass, target=0.90) * 0.20 +
        normalize_score(avg_difficulty / 5, target=0.60) * 0.15
    )
    
    # 2. 项目执行得分
    on_time_rate = sum(1 for t in tasks if t.actual_end <= t.planned_end) / max(len(tasks), 1)
    weighted_output = sum(t.difficulty_level for t in tasks if t.status == '已完成')
    
    field_supports = get_field_supports(engineer_id, period)
    field_response_rate = sum(1 for f in field_supports if f.response_hours <= 2) / max(len(field_supports), 1)
    
    scores["项目执行"] = (
        normalize_score(on_time_rate, target=0.90) * 0.40 +
        normalize_score(weighted_output / 20, target=0.70) * 0.30 +  # 20为月度基准
        normalize_score(field_response_rate, target=0.95) * 0.30
    )
    
    # 3. 质量保障得分
    stability = get_program_stability(engineer_id, period)
    avg_coverage = sum(v.test_coverage for v in versions if v.test_coverage) / max(len(versions), 1)
    complaints = get_customer_complaints(engineer_id, period)
    false_test_rate = get_false_test_rate(engineer_id, period)
    
    scores["质量保障"] = (
        normalize_score(stability / 100, target=0.95) * 0.40 +
        normalize_score(avg_coverage / 100, target=0.90) * 0.30 +
        normalize_score(1 - len(complaints) / 10, target=0.90) * 0.20 +
        normalize_score(1 - false_test_rate * 100, target=0.99) * 0.10
    )
    
    # 4. 知识沉淀得分
    reuse_records = get_reuse_records(engineer_id, period)
    docs = get_doc_contributions(engineer_id, period)
    shares = get_tech_shares(engineer_id, period)
    lib_contributions = get_code_lib_contributions(engineer_id, period)
    
    scores["知识沉淀"] = (
        normalize_score(len(reuse_records) / 5, target=0.60) * 0.40 +
        normalize_score(len(docs) / 2, target=0.80) * 0.30 +
        normalize_score(len(shares) / 1, target=0.80) * 0.20 +
        normalize_score(len(lib_contributions) / 2, target=0.80) * 0.10
    )
    
    # 5. 团队协作得分
    collab_ratings = get_collaboration_ratings(engineer_id, period)
    avg_collab = sum(r.avg_score for r in collab_ratings) / max(len(collab_ratings), 1)
    code_reviews = get_code_review_participation(engineer_id, period)
    mentees = get_mentees(engineer_id, period)
    
    scores["团队协作"] = (
        normalize_score(avg_collab / 5, target=0.80) * 0.50 +
        normalize_score(len(code_reviews) / 4, target=0.80) * 0.30 +
        normalize_score(len(mentees) / 1, target=0.80) * 0.20
    )
    
    # 计算综合得分
    total_score = sum(
        scores[dim] * TEST_ENGINEER_WEIGHTS[dim]["weight"]
        for dim in scores
    ) * 100
    
    return {
        "dimension_scores": scores,
        "total_score": total_score,
        "grade": get_grade(total_score)
    }
```

---

## 五、与机械工程师的对比

| 维度 | 机械工程师 | 测试工程师 |
|-----|-----------|-----------|
| **技术能力** | 设计一次通过率、ECN责任率 | 程序一次调通率、Bug修复效率 |
| **项目执行** | BOM提交及时性 | 现场响应速度 |
| **质量指标** | 调试问题数、验收通过 | 程序稳定性、误测率 |
| **成本/复用** | 标准件使用率、设计复用率 | 代码复用率、模块贡献 |
| **特殊指标** | - | 测试覆盖率、代码审查 |

---

## 六、实施建议

### 6.1 数据采集入口优化

```
┌─────────────────────────────────────────────────────────────────┐
│                   任务完成确认弹窗（测试专用）                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  任务：P2024-156 测试程序开发                                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  程序是否一次调通？  ○ 是  ○ 否（需修改后重新部署）       │    │
│  │                                                          │    │
│  │  代码审查状态：      ○ 已通过  ○ 待审查  ○ 需修改       │    │
│  │                                                          │    │
│  │  测试覆盖率：        [  85  ] %                          │    │
│  │                                                          │    │
│  │  任务难度：          ○ 1  ○ 2  ● 3  ○ 4  ○ 5            │    │
│  │                      简单 ←───────────────→ 复杂          │    │
│  │                                                          │    │
│  │  版本号：            [ V1.2.0 ]                          │    │
│  │                                                          │    │
│  │  变更说明：          [                                ]  │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                    [取消]  [确认完成]                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Git集成（可选）

如果公司使用Git管理LabVIEW项目，可以自动采集：

```python
# Git提交统计自动化采集
def sync_git_statistics(engineer_id, period):
    """从Git仓库同步代码统计"""
    
    commits = git_api.get_commits(
        author=get_git_username(engineer_id),
        since=period.start_date,
        until=period.end_date
    )
    
    return {
        "commit_count": len(commits),
        "lines_added": sum(c.additions for c in commits),
        "lines_deleted": sum(c.deletions for c in commits),
        "files_changed": sum(c.files_changed for c in commits),
        "merge_requests": git_api.get_merge_requests(author=engineer_id),
        "code_reviews": git_api.get_reviews(reviewer=engineer_id)
    }
```

### 6.3 分阶段实施

| 阶段 | 时间 | 内容 |
|-----|------|------|
| 第一阶段 | 1-2周 | 任务表补充字段，完成确认弹窗增加测试专用字段 |
| 第二阶段 | 2-3周 | 创建Bug跟踪表，与现场问题系统打通 |
| 第三阶段 | 3-4周 | 创建程序版本表，跟踪稳定性 |
| 第四阶段 | 4-5周 | 开发绩效计算逻辑和看板 |
| 第五阶段 | 5-6周 | 集成代码复用统计，完善知识沉淀指标 |

