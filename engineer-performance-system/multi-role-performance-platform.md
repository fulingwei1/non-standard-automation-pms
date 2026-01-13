# 多岗位工程师绩效管理平台

## 一、平台概述

### 1.1 设计目标

构建一个统一的绩效管理平台，支持非标自动化设备公司三类核心工程师岗位的绩效评价，并支持按职级分组评价：

### 1.2 职级分组评价体系

**核心原则：同职级、同岗位内部对比排名**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        职级分组评价体系                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  职级层次                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  高级工程师 (Senior)     │ 承担复杂项目、技术攻关、指导下级      │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  中级工程师 (Middle)     │ 独立完成中等难度任务、项目骨干        │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  初级工程师 (Junior)     │ 在指导下完成常规任务                  │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │  助理工程师 (Assistant)  │ 辅助性工作、学习成长阶段              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  评价分组示例（以机械工程师为例）                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  机械-高级 (8人)  │ 组内排名 1-8，独立评优                       │    │
│  │  机械-中级 (12人) │ 组内排名 1-12，独立评优                      │    │
│  │  机械-初级 (10人) │ 组内排名 1-10，独立评优                      │    │
│  │  机械-助理 (5人)  │ 组内排名 1-5，独立评优                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  分类管理权限                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  部门经理   │ 可管理本部门工程师的职级分类                       │    │
│  │  人力资源   │ 可管理所有工程师的职级分类                         │    │
│  │  系统管理员 │ 可管理所有工程师的职级分类 + 系统配置              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 不同职级的评价差异

| 维度 | 高级工程师 | 中级工程师 | 初级工程师 | 助理工程师 |
|-----|-----------|-----------|-----------|-----------|
| **技术能力权重** | 25% | 30% | 35% | 40% |
| **项目执行权重** | 25% | 25% | 25% | 25% |
| **成本/质量权重** | 20% | 20% | 20% | 15% |
| **知识沉淀权重** | 20% | 15% | 10% | 5% |
| **团队协作权重** | 10% | 10% | 10% | 15% |
| **任务难度要求** | ≥4.0 | ≥3.0 | ≥2.0 | ≥1.0 |
| **带教要求** | ≥2人/年 | ≥1人/年 | 无 | 无 |
| **知识贡献要求** | ≥4篇/年 | ≥2篇/年 | ≥1篇/年 

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    多岗位工程师绩效管理平台                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│   │  机械工程师  │     │  测试工程师  │     │  电气工程师  │              │
│   │             │     │             │     │             │              │
│   │  结构设计   │     │  LabVIEW    │     │  PLC编程    │              │
│   │  3D建模    │     │  C#开发     │     │  EPLAN设计  │              │
│   │  BOM编制   │     │  自动化测试  │     │  电气图纸   │              │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘              │
│          │                   │                   │                      │
│          └───────────────────┼───────────────────┘                      │
│                              ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                      统一评价框架                                 │  │
│   │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐            │  │
│   │  │技术能力 │项目执行 │成本/质量│知识沉淀 │团队协作 │            │  │
│   │  │  30%   │  25%   │  20%   │  15%   │  10%   │            │  │
│   │  └─────────┴─────────┴─────────┴─────────┴─────────┘            │  │
│   │                              ▼                                   │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │     岗位专属指标 + 通用指标 = 综合绩效得分               │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心特性

| 特性 | 说明 |
|-----|------|
| **统一框架** | 三类岗位共享五维评价框架，权重可按岗位调整 |
| **差异化指标** | 每类岗位有专属的技术指标和评价标准 |
| **跨部门协作** | 支持机械↔电气↔测试的互评机制 |
| **数据复用** | 从现有项目管理系统自动提取80%数据 |
| **灵活配置** | 支持动态调整权重、目标值、等级规则 |

---

## 二、统一评价框架

### 2.1 五维评价体系

```
                           统一五维评价框架
                                 │
    ┌────────────┬────────────┬──┴──┬────────────┬────────────┐
    ▼            ▼            ▼     ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│技术能力│  │项目执行│  │成本/质量│  │知识沉淀│  │团队协作│
│ 30%   │  │ 25%   │  │ 20%   │  │ 15%   │  │ 10%   │
└───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
    │            │            │            │            │
    ▼            ▼            ▼            ▼            ▼
┌────────────────────────────────────────────────────────────┐
│                      岗位专属指标                           │
├────────────────────────────────────────────────────────────┤
│ 机械: 设计一次通过 │ 测试: 程序一次调通 │ 电气: 图纸一次通过 │
│      ECN责任率    │      Bug修复效率   │      PLC调通率    │
│      标准件使用   │      测试覆盖率    │      选型准确率   │
└────────────────────────────────────────────────────────────┘
```

### 2.2 各岗位指标对照表

| 维度 | 权重 | 机械工程师 | 测试工程师 | 电气工程师 |
|-----|------|-----------|-----------|-----------|
| **技术能力** | 30% | 设计一次通过率 ≥85%<br>ECN责任率 ≤10%<br>调试问题密度 ≤0.5 | 程序一次调通率 ≥80%<br>Bug修复时长 ≤4h<br>代码审查通过率 ≥90% | 图纸一次通过率 ≥85%<br>PLC一次调通率 ≥80%<br>调试效率 ≥90% |
| **项目执行** | 25% | 任务按时完成率 ≥90%<br>BOM提交及时率 ≥95%<br>难度加权产出 | 任务按时完成率 ≥90%<br>现场2h响应率 ≥95%<br>版本迭代效率 | 任务按时完成率 ≥90%<br>图纸交付及时率 ≥95%<br>现场4h响应率 ≥90% |
| **成本/质量** | 20% | 标准件使用率 ≥60%<br>设计复用率 ≥30%<br>成本节约贡献 | 程序稳定性 ≥95%<br>测试覆盖率 ≥90%<br>误测率 ≤0.1% | 标准件使用率 ≥70%<br>选型准确率 ≥95%<br>故障密度 ≤0.2 |
| **知识沉淀** | 15% | 文档贡献 ≥2篇/季<br>被引用次数<br>技术分享 | 模块复用率<br>代码库贡献 ≥2个/季<br>技术分享 | PLC模块贡献 ≥2个/季<br>标准模板<br>被复用次数 |
| **团队协作** | 10% | 电气配合评分 ≥4.0<br>测试配合评分 ≥4.0<br>新人带教 | 机械配合评分 ≥4.0<br>电气配合评分 ≥4.0<br>代码审查参与 | 机械配合评分 ≥4.0<br>测试配合评分 ≥4.0<br>接口文档完整性 |

### 2.3 跨部门互评矩阵

```
              评价者
被评价者    机械部    测试部    电气部
  ─────────────────────────────────
  机械部      -      配合度    接口配合
  测试部    需求响应    -      通讯配合  
  电气部    图纸准确  程序接口    -
```

---

## 三、统一数据模型

### 3.1 数据库架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           数据库架构                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  通用表                                                                  │
│  ├─ engineer_info          工程师基础信息（含岗位类型）                   │
│  ├─ performance_dimension  评价维度配置                                  │
│  ├─ performance_metric     评价指标配置                                  │
│  ├─ performance_weight     权重配置（按岗位）                            │
│  ├─ performance_summary    绩效汇总表（所有岗位通用）                     │
│  ├─ collaboration_rating   跨部门互评记录                                │
│  └─ knowledge_contribution 知识贡献记录                                  │
│                                                                          │
│  岗位专属表                                                              │
│  ├─ mechanical_*           机械工程师专用表                              │
│  │   ├─ design_review      设计评审记录                                 │
│  │   ├─ ecn_record         ECN变更记录                                  │
│  │   └─ debug_issue        调试问题记录                                 │
│  │                                                                       │
│  ├─ test_*                 测试工程师专用表                              │
│  │   ├─ program_version    测试程序版本                                 │
│  │   ├─ bug_record         Bug跟踪记录                                  │
│  │   └─ code_reuse         代码复用记录                                 │
│  │                                                                       │
│  └─ electrical_*           电气工程师专用表                              │
│      ├─ drawing_version    电气图纸版本                                 │
│      ├─ plc_program        PLC程序版本                                  │
│      ├─ component_selection 元器件选型                                  │
│      └─ plc_module_library PLC模块库                                    │
│                                                                          │
│  共享数据源（现有系统）                                                   │
│  ├─ project_task           项目任务表                                   │
│  ├─ pmo_resource_allocation 资源分配表                                  │
│  ├─ bom_submission         BOM提交记录                                  │
│  └─ design_change          设计变更记录                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心通用表设计

```sql
-- ============================================================
-- 1. 工程师信息表（扩展现有员工表）
-- ============================================================
CREATE TABLE engineer_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    employee_id BIGINT NOT NULL COMMENT '员工ID',
    employee_name VARCHAR(50) NOT NULL,
    
    -- 岗位信息
    job_type ENUM('mechanical','test','electrical') NOT NULL COMMENT '岗位类型',
    job_level ENUM('初级','中级','高级','资深','专家') DEFAULT '中级',
    department_id BIGINT,
    department_name VARCHAR(100),
    
    -- 专业技能标签
    skill_tags JSON COMMENT '技能标签，如["SolidWorks","EPLAN","西门子"]',
    primary_skill VARCHAR(50) COMMENT '主要技能',
    
    -- 入职信息
    join_date DATE,
    
    -- 状态
    status ENUM('active','inactive') DEFAULT 'active',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_employee (employee_id),
    INDEX idx_job_type (job_type),
    INDEX idx_department (department_id)
) COMMENT '工程师信息表';


-- ============================================================
-- 2. 评价维度配置表
-- ============================================================
CREATE TABLE performance_dimension (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dimension_code VARCHAR(30) NOT NULL COMMENT '维度编码',
    dimension_name VARCHAR(50) NOT NULL COMMENT '维度名称',
    description TEXT COMMENT '维度描述',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY uk_code (dimension_code)
) COMMENT '评价维度配置表';

-- 初始化五个维度
INSERT INTO performance_dimension (dimension_code, dimension_name, display_order) VALUES
('technical', '技术能力', 1),
('execution', '项目执行', 2),
('cost_quality', '成本/质量', 3),
('knowledge', '知识沉淀', 4),
('collaboration', '团队协作', 5);


-- ============================================================
-- 3. 评价指标配置表
-- ============================================================
CREATE TABLE performance_metric (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 归属
    dimension_code VARCHAR(30) NOT NULL COMMENT '所属维度',
    job_type ENUM('mechanical','test','electrical','all') NOT NULL COMMENT '适用岗位',
    
    -- 指标定义
    metric_code VARCHAR(50) NOT NULL COMMENT '指标编码',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    description TEXT COMMENT '指标说明',
    
    -- 计算方式
    calc_type ENUM('percentage','count','average','ratio','score') COMMENT '计算类型',
    calc_formula TEXT COMMENT '计算公式/SQL',
    data_source VARCHAR(100) COMMENT '数据来源表',
    
    -- 目标值
    target_value DECIMAL(10,2) COMMENT '目标值',
    target_direction ENUM('higher_better','lower_better','equal_better') DEFAULT 'higher_better',
    
    -- 权重
    weight_in_dimension INT DEFAULT 25 COMMENT '在维度内的权重(%)',
    
    -- 显示
    unit VARCHAR(20) COMMENT '单位',
    display_format VARCHAR(50) COMMENT '显示格式',
    
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY uk_metric (job_type, metric_code),
    INDEX idx_dimension (dimension_code),
    INDEX idx_job_type (job_type)
) COMMENT '评价指标配置表';


-- ============================================================
-- 4. 权重配置表
-- ============================================================
-- 【重要原则】权重只能按"岗位类型+级别"配置，不能针对个人！
-- 这是绩效评价公平性的基本保障
CREATE TABLE performance_weight (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- 配置范围（岗位+级别，不涉及个人）
    job_type ENUM('mechanical','test','electrical') NOT NULL COMMENT '岗位类型',
    job_level ENUM('初级','中级','高级','资深','专家','all') DEFAULT 'all' COMMENT '适用级别',
    
    -- 维度权重
    dimension_code VARCHAR(30) NOT NULL,
    weight INT NOT NULL COMMENT '权重百分比',
    
    -- 版本控制
    effective_date DATE NOT NULL COMMENT '生效日期',
    expire_date DATE COMMENT '失效日期',
    version INT DEFAULT 1 COMMENT '版本号',
    
    -- 审批信息
    created_by BIGINT,
    approved_by BIGINT COMMENT '审批人',
    approved_at DATETIME COMMENT '审批时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：同一岗位+级别+维度+生效日期只能有一条配置
    UNIQUE KEY uk_weight (job_type, job_level, dimension_code, effective_date)
) COMMENT '权重配置表（按岗位+级别，不针对个人）';

-- 初始化默认权重
INSERT INTO performance_weight (job_type, job_level, dimension_code, weight, effective_date) VALUES
-- 机械工程师
('mechanical', 'all', 'technical', 30, '2024-01-01'),
('mechanical', 'all', 'execution', 25, '2024-01-01'),
('mechanical', 'all', 'cost_quality', 20, '2024-01-01'),
('mechanical', 'all', 'knowledge', 15, '2024-01-01'),
('mechanical', 'all', 'collaboration', 10, '2024-01-01'),
-- 测试工程师
('test', 'all', 'technical', 30, '2024-01-01'),
('test', 'all', 'execution', 25, '2024-01-01'),
('test', 'all', 'cost_quality', 20, '2024-01-01'),
('test', 'all', 'knowledge', 15, '2024-01-01'),
('test', 'all', 'collaboration', 10, '2024-01-01'),
-- 电气工程师
('electrical', 'all', 'technical', 30, '2024-01-01'),
('electrical', 'all', 'execution', 25, '2024-01-01'),
('electrical', 'all', 'cost_quality', 20, '2024-01-01'),
('electrical', 'all', 'knowledge', 15, '2024-01-01'),
('electrical', 'all', 'collaboration', 10, '2024-01-01');


-- ============================================================
-- 5. 统一绩效汇总表
-- ============================================================
CREATE TABLE performance_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 工程师信息
    engineer_id BIGINT NOT NULL,
    engineer_name VARCHAR(50),
    job_type ENUM('mechanical','test','electrical') NOT NULL,
    department_id BIGINT,
    
    -- 周期
    period_type ENUM('monthly','quarterly','yearly') NOT NULL,
    period_value VARCHAR(10) NOT NULL COMMENT '如 2024-11, 2024Q4, 2024',
    period_start DATE,
    period_end DATE,
    
    -- 维度得分 (JSON存储灵活扩展)
    dimension_scores JSON COMMENT '{"technical":85,"execution":82,...}',
    
    -- 核心指标快照 (便于快速查询和排序)
    technical_score DECIMAL(5,2),
    execution_score DECIMAL(5,2),
    cost_quality_score DECIMAL(5,2),
    knowledge_score DECIMAL(5,2),
    collaboration_score DECIMAL(5,2),
    
    -- 指标明细 (JSON存储所有具体指标)
    metric_details JSON COMMENT '存储所有具体指标值',
    
    -- 综合结果
    total_score DECIMAL(5,2) NOT NULL,
    grade ENUM('S','A','B','C','D') COMMENT 'S优秀 A良好 B合格 C待改进 D不合格',
    grade_cn VARCHAR(10) COMMENT '中文等级',
    
    -- 排名
    department_rank INT COMMENT '部门内排名',
    department_total INT COMMENT '部门总人数',
    job_type_rank INT COMMENT '岗位类型排名',
    job_type_total INT COMMENT '岗位类型总人数',
    company_rank INT COMMENT '公司排名（可选）',
    
    -- 同比环比
    prev_period_score DECIMAL(5,2) COMMENT '上期得分',
    score_change DECIMAL(5,2) COMMENT '得分变化',
    
    -- 计算信息
    calculated_at DATETIME,
    calculation_version VARCHAR(20) COMMENT '计算版本',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_engineer_period (engineer_id, period_type, period_value),
    INDEX idx_job_type (job_type),
    INDEX idx_period (period_type, period_value),
    INDEX idx_score (total_score DESC),
    INDEX idx_department (department_id, period_type, period_value)
) COMMENT '工程师绩效汇总表';


-- ============================================================
-- 6. 跨部门协作评价表
-- ============================================================
CREATE TABLE collaboration_rating (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 评价周期
    rating_period VARCHAR(10) NOT NULL COMMENT '评价周期，如 2024Q4',
    
    -- 被评价人
    rated_engineer_id BIGINT NOT NULL,
    rated_engineer_name VARCHAR(50),
    rated_job_type ENUM('mechanical','test','electrical') NOT NULL,
    rated_department_id BIGINT,
    
    -- 评价人
    rater_engineer_id BIGINT NOT NULL,
    rater_engineer_name VARCHAR(50),
    rater_job_type ENUM('mechanical','test','electrical') NOT NULL,
    rater_department_id BIGINT,
    
    -- 评分项
    communication_score DECIMAL(2,1) COMMENT '沟通配合(1-5)',
    response_score DECIMAL(2,1) COMMENT '响应速度(1-5)',
    quality_score DECIMAL(2,1) COMMENT '交付质量(1-5)',
    interface_score DECIMAL(2,1) COMMENT '接口规范(1-5)',
    
    -- 综合
    avg_score DECIMAL(3,2),
    
    -- 评语
    comments TEXT,
    
    -- 项目关联（可选）
    project_id BIGINT COMMENT '关联项目',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_rating (rated_engineer_id, rater_engineer_id, rating_period),
    INDEX idx_rated (rated_engineer_id, rating_period),
    INDEX idx_rater (rater_engineer_id)
) COMMENT '跨部门协作评价表';


-- ============================================================
-- 7. 知识贡献记录表（通用）
-- ============================================================
CREATE TABLE knowledge_contribution (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 贡献者
    engineer_id BIGINT NOT NULL,
    engineer_name VARCHAR(50),
    job_type ENUM('mechanical','test','electrical') NOT NULL,
    
    -- 贡献类型
    contribution_type ENUM(
        'document',          -- 技术文档
        'template',          -- 标准模板
        'module',            -- 代码/程序模块
        'training',          -- 培训分享
        'patent',            -- 专利
        'standard'           -- 企业标准
    ) NOT NULL,
    
    -- 贡献内容
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) COMMENT '分类',
    tags JSON COMMENT '标签',
    
    -- 附件
    attachments JSON COMMENT '附件列表',
    
    -- 状态
    status ENUM('draft','reviewing','published','deprecated') DEFAULT 'draft',
    published_at DATETIME,
    
    -- 使用统计
    view_count INT DEFAULT 0,
    download_count INT DEFAULT 0,
    reuse_count INT DEFAULT 0 COMMENT '被复用次数',
    rating DECIMAL(2,1) COMMENT '评分',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_engineer (engineer_id),
    INDEX idx_job_type (job_type),
    INDEX idx_type (contribution_type),
    INDEX idx_status (status)
) COMMENT '知识贡献记录表';


-- ============================================================
-- 8. 等级规则配置表
-- ============================================================
CREATE TABLE grade_rule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    job_type ENUM('mechanical','test','electrical','all') DEFAULT 'all',
    
    grade_code VARCHAR(10) NOT NULL,
    grade_name VARCHAR(20) NOT NULL,
    min_score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2),
    
    -- 颜色和样式
    color_code VARCHAR(20),
    
    display_order INT,
    is_active BOOLEAN DEFAULT TRUE,
    
    effective_date DATE
) COMMENT '等级规则配置表';

INSERT INTO grade_rule (job_type, grade_code, grade_name, min_score, max_score, color_code, display_order, effective_date) VALUES
('all', 'S', '优秀', 85, 100, '#22c55e', 1, '2024-01-01'),
('all', 'A', '良好', 70, 84.99, '#3b82f6', 2, '2024-01-01'),
('all', 'B', '合格', 60, 69.99, '#f59e0b', 3, '2024-01-01'),
('all', 'C', '待改进', 40, 59.99, '#f97316', 4, '2024-01-01'),
('all', 'D', '不合格', 0, 39.99, '#ef4444', 5, '2024-01-01');
```

---

## 四、统一API设计

### 4.1 API架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API 架构                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  /api/v1/performance                                                     │
│  ├── /summary                  # 综合概览                                │
│  │   ├── GET /company          # 公司整体概览                            │
│  │   ├── GET /department/{id}  # 部门概览                                │
│  │   └── GET /job-type/{type}  # 按岗位类型概览                          │
│  │                                                                       │
│  ├── /ranking                  # 排名                                    │
│  │   ├── GET /                 # 综合排名                                │
│  │   ├── GET /by-department    # 按部门排名                              │
│  │   └── GET /by-job-type      # 按岗位排名                              │
│  │                                                                       │
│  ├── /engineer                 # 工程师绩效                              │
│  │   ├── GET /{id}             # 个人绩效详情                            │
│  │   ├── GET /{id}/trend       # 个人趋势                                │
│  │   ├── GET /{id}/comparison  # 对比分析                                │
│  │   └── GET /{id}/metrics     # 指标明细                                │
│  │                                                                       │
│  ├── /metrics                  # 指标数据                                │
│  │   ├── /mechanical/*         # 机械专属指标接口                        │
│  │   ├── /test/*               # 测试专属指标接口                        │
│  │   └── /electrical/*         # 电气专属指标接口                        │
│  │                                                                       │
│  ├── /collaboration            # 协作评价                                │
│  │   ├── GET /received/{id}    # 收到的评价                              │
│  │   ├── GET /given/{id}       # 给出的评价                              │
│  │   └── POST /                # 提交评价                                │
│  │                                                                       │
│  ├── /knowledge                # 知识贡献                                │
│  │   ├── GET /                 # 贡献列表                                │
│  │   ├── GET /ranking          # 贡献排行                                │
│  │   └── POST /                # 提交贡献                                │
│  │                                                                       │
│  ├── /config                   # 配置管理                                │
│  │   ├── GET /weights          # 获取权重配置                            │
│  │   ├── PUT /weights          # 更新权重配置                            │
│  │   ├── GET /metrics          # 获取指标配置                            │
│  │   ├── PUT /metrics          # 更新指标配置                            │
│  │   └── GET /grades           # 获取等级规则                            │
│  │                                                                       │
│  └── /calculate                # 计算任务                                │
│      ├── POST /trigger         # 触发计算                                │
│      └── GET /status/{taskId}  # 计算状态                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 核心接口定义

```yaml
# ==================== 综合概览 ====================

GET /api/v1/performance/summary/company
Query:
  period_type: monthly | quarterly
  period_value: string  # 2024-11

Response:
{
  "code": 200,
  "data": {
    "period": { "type": "monthly", "value": "2024-11" },
    "overview": {
      "total_engineers": 80,
      "avg_score": 81.5,
      "score_change": 1.2,
      "by_job_type": [
        { "job_type": "mechanical", "count": 35, "avg_score": 82.1 },
        { "job_type": "test", "count": 15, "avg_score": 83.2 },
        { "job_type": "electrical", "count": 30, "avg_score": 80.5 }
      ],
      "grade_distribution": [
        { "grade": "S", "count": 15, "percentage": 18.75 },
        { "grade": "A", "count": 35, "percentage": 43.75 },
        { "grade": "B", "count": 25, "percentage": 31.25 },
        { "grade": "C", "count": 5, "percentage": 6.25 }
      ]
    },
    "dimension_comparison": {
      "mechanical": { "technical": 84, "execution": 82, "cost_quality": 80, "knowledge": 75, "collaboration": 85 },
      "test": { "technical": 86, "execution": 84, "cost_quality": 82, "knowledge": 78, "collaboration": 88 },
      "electrical": { "technical": 83, "execution": 80, "cost_quality": 78, "knowledge": 72, "collaboration": 84 }
    },
    "trend": [
      { "period": "2024-07", "mechanical": 80, "test": 81, "electrical": 78 },
      { "period": "2024-11", "mechanical": 82, "test": 83, "electrical": 80 }
    ]
  }
}


# ==================== 综合排名 ====================

GET /api/v1/performance/ranking
Query:
  period_type: monthly | quarterly
  period_value: string
  job_type: mechanical | test | electrical (optional)
  department_id: int (optional)
  page: int
  page_size: int

Response:
{
  "code": 200,
  "data": {
    "total": 80,
    "list": [
      {
        "rank": 1,
        "engineer_id": 1001,
        "engineer_name": "张三",
        "job_type": "test",
        "job_type_name": "测试工程师",
        "department": "测试部",
        "level": "高级",
        "scores": {
          "technical": 92,
          "execution": 88,
          "cost_quality": 85,
          "knowledge": 82,
          "collaboration": 90
        },
        "total_score": 88.5,
        "grade": "S",
        "grade_name": "优秀",
        "trend": "up",
        "score_change": 3.2
      }
    ]
  }
}


# ==================== 个人绩效详情 ====================

GET /api/v1/performance/engineer/{engineer_id}
Query:
  period_type: monthly | quarterly
  period_value: string

Response:
{
  "code": 200,
  "data": {
    "engineer": {
      "id": 1001,
      "name": "张三",
      "job_type": "mechanical",
      "job_type_name": "机械工程师",
      "level": "高级工程师",
      "department": "机械设计部",
      "skills": ["SolidWorks", "AutoCAD"],
      "join_date": "2019-03-15"
    },
    "summary": {
      "total_score": 85.5,
      "grade": "S",
      "grade_name": "优秀",
      "department_rank": 2,
      "department_total": 35,
      "job_type_rank": 3,
      "job_type_total": 35,
      "score_change": 2.5
    },
    "dimension_scores": {
      "technical": { "score": 88, "weight": 30, "weighted": 26.4 },
      "execution": { "score": 85, "weight": 25, "weighted": 21.25 },
      "cost_quality": { "score": 82, "weight": 20, "weighted": 16.4 },
      "knowledge": { "score": 80, "weight": 15, "weighted": 12.0 },
      "collaboration": { "score": 88, "weight": 10, "weighted": 8.8 }
    },
    "metrics": {
      "technical": [
        { "code": "first_pass_rate", "name": "设计一次通过率", "value": 90, "target": 85, "unit": "%", "status": "good" },
        { "code": "ecn_responsibility_rate", "name": "ECN责任率", "value": 8, "target": 10, "unit": "%", "status": "good" }
      ],
      "execution": [...],
      "cost_quality": [...],
      "knowledge": [...],
      "collaboration": [...]
    },
    "collaboration_ratings": {
      "from_electrical": { "avg": 4.5, "count": 5 },
      "from_test": { "avg": 4.3, "count": 3 }
    },
    "projects": [...],
    "knowledge_contributions": [...]
  }
}


# ==================== 跨部门评价 ====================

POST /api/v1/performance/collaboration
Body:
{
  "rating_period": "2024Q4",
  "rated_engineer_id": 1001,
  "communication_score": 4.5,
  "response_score": 4.0,
  "quality_score": 4.5,
  "interface_score": 4.0,
  "comments": "配合良好，响应及时",
  "project_id": 156
}


# ==================== 配置管理 ====================

GET /api/v1/performance/config/weights
Query:
  job_type: mechanical | test | electrical

Response:
{
  "code": 200,
  "data": {
    "job_type": "mechanical",
    "dimensions": [
      { "code": "technical", "name": "技术能力", "weight": 30 },
      { "code": "execution", "name": "项目执行", "weight": 25 },
      { "code": "cost_quality", "name": "成本/质量", "weight": 20 },
      { "code": "knowledge", "name": "知识沉淀", "weight": 15 },
      { "code": "collaboration", "name": "团队协作", "weight": 10 }
    ],
    "metrics": {
      "technical": [
        { "code": "first_pass_rate", "name": "设计一次通过率", "weight": 35, "target": 85 },
        { "code": "ecn_responsibility_rate", "name": "ECN责任率", "weight": 25, "target": 10, "inverse": true }
      ]
    }
  }
}
```

---

## 五、前端页面设计

### 5.1 页面结构

```
多岗位工程师绩效管理平台
│
├── 🏠 首页总览
│   ├── 公司整体绩效概况
│   ├── 三类岗位对比雷达图
│   ├── 等级分布饼图
│   └── 月度趋势折线图
│
├── 📊 绩效排名
│   ├── 综合排名（可筛选岗位/部门）
│   ├── 分岗位排名Tab
│   └── 对比分析工具
│
├── 👤 个人绩效
│   ├── 工程师选择器
│   ├── 综合得分卡片
│   ├── 五维雷达图
│   ├── 指标明细表
│   ├── 项目参与记录
│   └── 趋势分析
│
├── 🤝 跨部门协作
│   ├── 协作评价录入
│   ├── 评价统计看板
│   └── 协作网络图
│
├── 📚 知识贡献
│   ├── 贡献排行榜
│   ├── 资源库浏览
│   └── 提交新贡献
│
├── 🔧 岗位专区
│   ├── 机械工程师
│   │   ├── 设计评审记录
│   │   ├── ECN统计
│   │   └── BOM管理
│   ├── 测试工程师
│   │   ├── 程序版本管理
│   │   ├── Bug跟踪
│   │   └── 代码复用库
│   └── 电气工程师
│       ├── 图纸管理
│       ├── PLC程序管理
│       └── 模块库
│
└── ⚙️ 系统配置
    ├── 权重配置
    ├── 指标配置
    ├── 等级规则
    └── 计算任务管理
```
