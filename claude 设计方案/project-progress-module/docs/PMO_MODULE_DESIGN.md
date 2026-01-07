# 项目管理部模块设计

## 一、项目管理部在公司中的角色定位

### 1.1 组织架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          公司组织架构                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         ┌──────────┐                                    │
│                         │  总经理   │                                    │
│                         └────┬─────┘                                    │
│                              │                                          │
│     ┌────────────┬──────────┼──────────┬────────────┐                  │
│     │            │          │          │            │                  │
│ ┌───┴───┐  ┌────┴────┐ ┌───┴───┐ ┌───┴───┐  ┌────┴────┐              │
│ │ 销售部 │  │项目管理部│ │ 研发部 │ │ 生产部 │  │ 财务部  │              │
│ └───────┘  └────┬────┘ └───────┘ └───────┘  └─────────┘              │
│                 │                                                       │
│     ┌───────────┼───────────┐                                          │
│     │           │           │                                          │
│ ┌───┴───┐  ┌───┴───┐  ┌───┴───┐                                       │
│ │项目经理│  │项目经理│  │项目经理│   (多个项目经理)                       │
│ └───────┘  └───────┘  └───────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 项目管理部核心职责

| 职责领域 | 具体内容 | 价值体现 |
|---------|---------|---------|
| **项目立项** | 组织立项评审、资源评估、风险识别 | 确保项目可行性 |
| **项目规划** | 制定项目计划、里程碑、WBS分解 | 明确目标和路径 |
| **进度管控** | 监控项目进度、预警偏差、推动纠偏 | 保障按期交付 |
| **资源协调** | 跨部门资源调配、冲突协调 | 优化资源利用 |
| **质量管理** | 节点评审、质量检查、问题跟踪 | 保障交付质量 |
| **成本控制** | 成本监控、预算执行、偏差分析 | 控制项目成本 |
| **风险管理** | 风险识别、评估、应对措施跟踪 | 降低项目风险 |
| **沟通协调** | 项目会议、状态报告、干系人管理 | 信息透明同步 |
| **知识沉淀** | 项目复盘、经验总结、模板积累 | 持续改进优化 |

### 1.3 项目管理部与其他部门的关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    项目管理部与其他部门协作关系                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐                                      ┌─────────┐          │
│  │  销售部  │ ──── 合同/需求/客户信息 ────────→   │         │          │
│  └─────────┘                                      │         │          │
│                                                   │         │          │
│  ┌─────────┐                                      │         │          │
│  │ 售前技术 │ ──── 技术方案/成本估算 ────────→   │ 项目    │          │
│  └─────────┘                                      │ 管理部  │          │
│                                                   │         │          │
│  ┌─────────┐                                      │         │          │
│  │  研发部  │ ←──→ 任务分配/进度反馈 ←──────→   │         │          │
│  │(机械/电气│                                     │         │          │
│  │ /软件)  │                                      │         │          │
│  └─────────┘                                      │         │          │
│                                                   │         │          │
│  ┌─────────┐                                      │         │          │
│  │  生产部  │ ←──→ 生产计划/物料需求 ←──────→   │         │          │
│  └─────────┘                                      │         │          │
│                                                   │         │          │
│  ┌─────────┐                                      │         │          │
│  │  采购部  │ ←──→ 采购需求/到货跟踪 ←──────→   │         │          │
│  └─────────┘                                      │         │          │
│                                                   │         │          │
│  ┌─────────┐                                      │         │          │
│  │  财务部  │ ←──→ 预算/成本/回款 ────────────→  │         │          │
│  └─────────┘                                      └─────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、项目全生命周期管理

### 2.1 项目阶段划分

```
项目生命周期：

┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│  商机  │ → │  立项  │ → │  设计  │ → │  生产  │ → │  交付  │ → │  结项  │
│  阶段  │   │  阶段  │   │  阶段  │   │  阶段  │   │  阶段  │   │  阶段  │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘
    │            │            │            │            │            │
    ▼            ▼            ▼            ▼            ▼            ▼
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│• 需求  │   │• 立项  │   │• 方案  │   │• 零件  │   │• 现场  │   │• 验收  │
│  收集  │   │  评审  │   │  设计  │   │  加工  │   │  安装  │   │  确认  │
│• 方案  │   │• 资源  │   │• 图纸  │   │• 采购  │   │• 调试  │   │• 回款  │
│  报价  │   │  分配  │   │  评审  │   │  到货  │   │  培训  │   │• 复盘  │
│• 合同  │   │• 计划  │   │• BOM   │   │• 装配  │   │• 客户  │   │• 归档  │
│  签订  │   │  制定  │   │  输出  │   │  调试  │   │  验收  │   │        │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘   └────────┘
```

### 2.2 阶段门控(Stage-Gate)

| 阶段 | 入口条件 | 出口条件 | 关键交付物 |
|------|---------|---------|-----------|
| **立项** | 合同签订 | 立项评审通过 | 项目任命书、初步计划 |
| **设计** | 立项完成 | 设计评审通过 | 设计图纸、BOM清单 |
| **生产** | 设计冻结 | 出厂检验通过 | 设备成品、检验报告 |
| **交付** | 生产完成 | 客户验收通过 | 验收报告、培训记录 |
| **结项** | 验收完成 | 结项评审通过 | 项目总结、归档资料 |

---

## 三、项目管理部核心业务流程

### 3.1 项目立项流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          项目立项流程                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐          │
│  │ 合同签订 │ ──→ │ 销售提交 │ ──→ │ PMO接收 │ ──→ │ 初步评估 │          │
│  │         │     │ 立项申请 │     │ 立项资料 │     │ 项目信息 │          │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘          │
│                                                       │                 │
│                                                       ▼                 │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐          │
│  │ 项目启动 │ ←── │ 发布项目 │ ←── │ 评审通过 │ ←── │ 立项评审 │          │
│  │ 会议    │     │ 任命书   │     │         │     │ 会议    │          │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘          │
│       │                                               ↑                 │
│       │                                          ┌────┴────┐           │
│       │                                          │ 评审不通过│           │
│       │                                          │ 返回补充 │           │
│       │                                          └─────────┘           │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       项目正式启动                               │   │
│  │  • 项目经理到位        • WBS分解完成        • 资源分配确认       │   │
│  │  • 项目团队组建        • 进度计划发布        • 项目群创建         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 项目监控流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         项目监控体系                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                          ┌─────────────┐                                │
│                          │ 项目管理部  │                                │
│                          │   监控中心   │                                │
│                          └──────┬──────┘                                │
│                                 │                                       │
│     ┌───────────────────────────┼───────────────────────────┐          │
│     │                           │                           │          │
│     ▼                           ▼                           ▼          │
│ ┌─────────┐             ┌─────────────┐             ┌─────────┐        │
│ │ 日报/周报 │             │  里程碑检查  │             │ 预警处理 │        │
│ │ 收集分析 │             │  节点评审   │             │ 问题跟踪 │        │
│ └────┬────┘             └──────┬──────┘             └────┬────┘        │
│      │                         │                         │             │
│      ▼                         ▼                         ▼             │
│ ┌─────────┐             ┌─────────────┐             ┌─────────┐        │
│ │ 进度偏差 │             │  质量检查   │             │ 风险评估 │        │
│ │ 分析    │             │  问题记录   │             │ 应对措施 │        │
│ └────┬────┘             └──────┬──────┘             └────┬────┘        │
│      │                         │                         │             │
│      └─────────────────────────┼─────────────────────────┘             │
│                                │                                       │
│                                ▼                                       │
│                    ┌───────────────────────┐                           │
│                    │    管理层报告/决策     │                           │
│                    │  • 项目状态周报        │                           │
│                    │  • 异常问题升级        │                           │
│                    │  • 资源协调请求        │                           │
│                    └───────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 项目变更管理流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        项目变更管理流程                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐          │
│  │ 变更申请 │ ──→ │ 影响评估 │ ──→ │ 变更审批 │ ──→ │ 变更执行 │          │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘          │
│       │               │               │               │                │
│       ▼               ▼               ▼               ▼                │
│  • 变更原因      • 进度影响      • 项目经理      • 计划调整            │
│  • 变更内容      • 成本影响      • 部门经理      • 资源调配            │
│  • 申请人       • 质量影响      • 客户确认      • 通知相关方           │
│  • 紧急程度      • 资源影响      • 高层审批      • 跟踪闭环            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 四、项目管理部系统功能设计

### 4.1 功能模块架构

```
项目管理部系统
├── 📊 管理驾驶舱
│   ├── 项目全景视图
│   ├── 资源负荷总览
│   ├── 进度健康度
│   ├── 成本执行率
│   └── 风险预警墙
│
├── 📁 项目全生命周期
│   ├── 立项管理
│   │   ├── 立项申请
│   │   ├── 立项评审
│   │   └── 项目任命
│   ├── 项目规划
│   │   ├── WBS分解
│   │   ├── 进度计划
│   │   ├── 资源计划
│   │   └── 成本预算
│   ├── 项目执行
│   │   ├── 任务跟踪
│   │   ├── 工时填报
│   │   ├── 进度更新
│   │   └── 问题管理
│   ├── 项目监控
│   │   ├── 里程碑检查
│   │   ├── 偏差分析
│   │   ├── 预警管理
│   │   └── 变更控制
│   └── 项目收尾
│       ├── 验收管理
│       ├── 项目复盘
│       └── 知识归档
│
├── 🔄 资源管理
│   ├── 资源池管理
│   ├── 资源分配
│   ├── 负荷分析
│   └── 冲突协调
│
├── ⚠️ 风险管理
│   ├── 风险识别
│   ├── 风险评估
│   ├── 应对计划
│   └── 风险跟踪
│
├── 💰 成本管理
│   ├── 预算编制
│   ├── 成本归集
│   ├── 偏差分析
│   └── 成本预测
│
├── 📋 会议管理
│   ├── 立项评审会
│   ├── 周例会
│   ├── 里程碑评审
│   └── 结项评审会
│
├── 📈 报表中心
│   ├── 项目状态报告
│   ├── 资源利用报告
│   ├── 成本分析报告
│   ├── 绩效分析报告
│   └── 管理层周报
│
└── ⚙️ 配置管理
    ├── 项目模板
    ├── WBS模板
    ├── 流程配置
    └── 权限设置
```

### 4.2 项目全景视图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        项目管理驾驶舱                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 项目概览                                         2025年1月        │   │
│  ├─────────┬─────────┬─────────┬─────────┬─────────────────────────┤   │
│  │ 在建项目 │ A级项目 │ 本月交付 │ 预警项目 │ 平均进度健康度          │   │
│  │   45    │   12    │    5    │    8    │    82%  ████████░░     │   │
│  └─────────┴─────────┴─────────┴─────────┴─────────────────────────┘   │
│                                                                         │
│  ┌───────────────────────────────┐ ┌───────────────────────────────┐   │
│  │ 项目状态分布                   │ │ 部门资源负荷                   │   │
│  │                               │ │                               │   │
│  │  立项中 ██ 3                  │ │  机械部  ████████░░ 85%       │   │
│  │  设计中 ██████ 15             │ │  电气部  ██████████ 95%  ⚠️   │   │
│  │  生产中 ████████ 18           │ │  软件部  ██████░░░░ 72%       │   │
│  │  调试中 ████ 6                │ │  装配组  ███████░░░ 78%       │   │
│  │  交付中 ██ 3                  │ │                               │   │
│  └───────────────────────────────┘ └───────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 重点项目进度                                                     │   │
│  ├──────────────────────────────────────────────────────┬──────────┤   │
│  │ 项目名称                               │ 进度 │ 状态 │ 项目经理  │   │
│  ├──────────────────────────────────────────────────────┼──────────┤   │
│  │ XX汽车传感器测试设备          ████████░░ 78%  │ 🟢   │ 王经理   │   │
│  │ YY新能源电池检测线            ██████░░░░ 55%  │ 🟡   │ 李经理   │   │
│  │ ZZ医疗器械测试系统            ████░░░░░░ 35%  │ 🔴   │ 张经理   │   │
│  │ AA电子连接器寿命测试机        ██████████ 100% │ ✅   │ 赵经理   │   │
│  └──────────────────────────────────────────────────────┴──────────┘   │
│                                                                         │
│  ┌───────────────────────────────┐ ┌───────────────────────────────┐   │
│  │ 本周预警 TOP5                  │ │ 即将到期里程碑                 │   │
│  │                               │ │                               │   │
│  │ 🔴 ZZ项目机械设计延期3天       │ │ • XX项目 电气设计评审 1月5日   │   │
│  │ 🔴 YY项目关键物料未到货        │ │ • YY项目 软件联调   1月8日    │   │
│  │ 🟡 AA项目客户需求变更          │ │ • BB项目 出厂检验   1月10日   │   │
│  │ 🟡 BB项目电气工程师请假        │ │ • CC项目 发货计划   1月12日   │   │
│  │ 🟡 CC项目成本超预算5%          │ │                               │   │
│  └───────────────────────────────┘ └───────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 五、数据库设计

### 5.1 核心表结构

```sql
-- =====================================================
-- 项目管理部模块数据库设计
-- =====================================================

-- 1. 项目主表（扩展）
CREATE TABLE pmo_project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_no VARCHAR(32) NOT NULL COMMENT '项目编号',
    project_name VARCHAR(200) NOT NULL COMMENT '项目名称',
    
    -- 分类信息
    project_type ENUM('new', 'upgrade', 'maintain') DEFAULT 'new' COMMENT '项目类型',
    project_level ENUM('A', 'B', 'C') DEFAULT 'B' COMMENT '项目级别',
    industry VARCHAR(50) COMMENT '所属行业',
    
    -- 客户信息
    customer_id BIGINT COMMENT '客户ID',
    customer_name VARCHAR(100) COMMENT '客户名称',
    customer_contact VARCHAR(50) COMMENT '客户联系人',
    customer_phone VARCHAR(20) COMMENT '联系电话',
    
    -- 合同信息
    contract_no VARCHAR(50) COMMENT '合同编号',
    contract_amount DECIMAL(14,2) COMMENT '合同金额',
    
    -- 项目团队
    pm_id BIGINT NOT NULL COMMENT '项目经理ID',
    pm_name VARCHAR(50) COMMENT '项目经理姓名',
    sales_id BIGINT COMMENT '销售负责人ID',
    sales_name VARCHAR(50) COMMENT '销售负责人',
    
    -- 时间计划
    plan_start_date DATE COMMENT '计划开始日期',
    plan_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',
    
    -- 阶段状态
    current_phase ENUM('initiation', 'design', 'production', 'delivery', 'closure') 
        DEFAULT 'initiation' COMMENT '当前阶段',
    status ENUM('pending', 'active', 'suspended', 'completed', 'cancelled') 
        DEFAULT 'pending' COMMENT '项目状态',
    
    -- 进度信息
    overall_progress INT DEFAULT 0 COMMENT '整体进度(0-100)',
    health_status ENUM('green', 'yellow', 'red') DEFAULT 'green' COMMENT '健康状态',
    
    -- 预算成本
    budget_amount DECIMAL(14,2) COMMENT '预算金额',
    actual_cost DECIMAL(14,2) DEFAULT 0 COMMENT '实际成本',
    
    -- 工时信息
    planned_hours INT COMMENT '计划工时',
    actual_hours INT DEFAULT 0 COMMENT '实际工时',
    
    -- 描述
    description TEXT COMMENT '项目描述',
    remarks TEXT COMMENT '备注',
    
    -- 系统字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    
    INDEX idx_project_no (project_no),
    INDEX idx_pm (pm_id),
    INDEX idx_status (status),
    INDEX idx_phase (current_phase),
    INDEX idx_customer (customer_id)
) COMMENT '项目主表';


-- 2. 项目立项申请表
CREATE TABLE pmo_project_initiation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT COMMENT '项目ID(审批通过后关联)',
    application_no VARCHAR(32) NOT NULL COMMENT '申请编号',
    
    -- 申请信息
    project_name VARCHAR(200) NOT NULL COMMENT '项目名称',
    project_type ENUM('new', 'upgrade', 'maintain') DEFAULT 'new' COMMENT '项目类型',
    project_level ENUM('A', 'B', 'C') COMMENT '建议级别',
    
    -- 客户合同
    customer_name VARCHAR(100) NOT NULL COMMENT '客户名称',
    contract_no VARCHAR(50) COMMENT '合同编号',
    contract_amount DECIMAL(14,2) COMMENT '合同金额',
    
    -- 时间要求
    required_start_date DATE COMMENT '要求开始日期',
    required_end_date DATE COMMENT '要求交付日期',
    
    -- 技术信息
    technical_solution_id BIGINT COMMENT '关联技术方案ID',
    requirement_summary TEXT COMMENT '需求概述',
    technical_difficulty ENUM('low', 'medium', 'high') COMMENT '技术难度',
    
    -- 资源需求
    estimated_hours INT COMMENT '预估工时',
    resource_requirements TEXT COMMENT '资源需求说明',
    
    -- 风险评估
    risk_assessment TEXT COMMENT '初步风险评估',
    
    -- 申请人
    applicant_id BIGINT NOT NULL COMMENT '申请人ID',
    applicant_name VARCHAR(50) COMMENT '申请人姓名',
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    
    -- 审批状态
    status ENUM('draft', 'submitted', 'reviewing', 'approved', 'rejected') 
        DEFAULT 'draft' COMMENT '状态',
    
    -- 审批信息
    review_result TEXT COMMENT '评审结论',
    approved_pm_id BIGINT COMMENT '指定项目经理ID',
    approved_level ENUM('A', 'B', 'C') COMMENT '评定级别',
    approved_at DATETIME COMMENT '审批时间',
    approved_by BIGINT COMMENT '审批人',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_application_no (application_no),
    INDEX idx_status (status)
) COMMENT '项目立项申请表';


-- 3. 项目阶段表
CREATE TABLE pmo_project_phase (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    
    -- 阶段信息
    phase_code VARCHAR(20) NOT NULL COMMENT '阶段编码',
    phase_name VARCHAR(50) NOT NULL COMMENT '阶段名称',
    phase_order INT DEFAULT 0 COMMENT '阶段顺序',
    
    -- 时间
    plan_start_date DATE COMMENT '计划开始',
    plan_end_date DATE COMMENT '计划结束',
    actual_start_date DATE COMMENT '实际开始',
    actual_end_date DATE COMMENT '实际结束',
    
    -- 状态
    status ENUM('pending', 'in_progress', 'completed', 'skipped') 
        DEFAULT 'pending' COMMENT '状态',
    progress INT DEFAULT 0 COMMENT '进度',
    
    -- 入口/出口条件
    entry_criteria TEXT COMMENT '入口条件',
    exit_criteria TEXT COMMENT '出口条件',
    entry_check_result TEXT COMMENT '入口检查结果',
    exit_check_result TEXT COMMENT '出口检查结果',
    
    -- 评审
    review_required BOOLEAN DEFAULT TRUE COMMENT '是否需要评审',
    review_date DATE COMMENT '评审日期',
    review_result ENUM('passed', 'conditional', 'failed') COMMENT '评审结果',
    review_notes TEXT COMMENT '评审记录',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_phase_code (phase_code)
) COMMENT '项目阶段表';


-- 4. 项目里程碑表
CREATE TABLE pmo_milestone (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    phase_id BIGINT COMMENT '所属阶段ID',
    
    -- 里程碑信息
    milestone_name VARCHAR(100) NOT NULL COMMENT '里程碑名称',
    milestone_type ENUM('design_review', 'production_start', 'factory_test', 
        'delivery', 'acceptance', 'payment', 'other') COMMENT '里程碑类型',
    description TEXT COMMENT '描述',
    
    -- 时间
    plan_date DATE NOT NULL COMMENT '计划日期',
    actual_date DATE COMMENT '实际完成日期',
    
    -- 状态
    status ENUM('pending', 'in_progress', 'completed', 'delayed', 'cancelled') 
        DEFAULT 'pending' COMMENT '状态',
    
    -- 负责人
    owner_id BIGINT COMMENT '负责人ID',
    owner_name VARCHAR(50) COMMENT '负责人',
    
    -- 关联
    deliverables TEXT COMMENT '交付物',
    
    -- 预警
    warning_days INT DEFAULT 3 COMMENT '提前预警天数',
    is_warned BOOLEAN DEFAULT FALSE COMMENT '是否已预警',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_plan_date (plan_date),
    INDEX idx_status (status)
) COMMENT '项目里程碑表';


-- 5. 项目变更记录表
CREATE TABLE pmo_change_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    change_no VARCHAR(32) NOT NULL COMMENT '变更编号',
    
    -- 变更信息
    change_type ENUM('scope', 'schedule', 'cost', 'resource', 'requirement', 'other') 
        NOT NULL COMMENT '变更类型',
    change_level ENUM('minor', 'major', 'critical') DEFAULT 'minor' COMMENT '变更级别',
    title VARCHAR(200) NOT NULL COMMENT '变更标题',
    description TEXT NOT NULL COMMENT '变更描述',
    reason TEXT COMMENT '变更原因',
    
    -- 影响评估
    schedule_impact TEXT COMMENT '进度影响',
    cost_impact DECIMAL(12,2) COMMENT '成本影响',
    quality_impact TEXT COMMENT '质量影响',
    resource_impact TEXT COMMENT '资源影响',
    
    -- 申请人
    requestor_id BIGINT NOT NULL COMMENT '申请人ID',
    requestor_name VARCHAR(50) COMMENT '申请人',
    request_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    
    -- 审批状态
    status ENUM('draft', 'submitted', 'reviewing', 'approved', 'rejected', 'cancelled') 
        DEFAULT 'draft' COMMENT '状态',
    
    -- 审批记录
    pm_approval BOOLEAN COMMENT '项目经理审批',
    pm_approval_time DATETIME COMMENT '项目经理审批时间',
    manager_approval BOOLEAN COMMENT '部门经理审批',
    manager_approval_time DATETIME COMMENT '部门经理审批时间',
    customer_approval BOOLEAN COMMENT '客户确认',
    customer_approval_time DATETIME COMMENT '客户确认时间',
    
    -- 执行情况
    execution_status ENUM('pending', 'executing', 'completed') COMMENT '执行状态',
    execution_notes TEXT COMMENT '执行说明',
    completed_time DATETIME COMMENT '完成时间',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_change_no (change_no),
    INDEX idx_status (status)
) COMMENT '项目变更记录表';


-- 6. 项目风险表
CREATE TABLE pmo_project_risk (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    risk_no VARCHAR(32) NOT NULL COMMENT '风险编号',
    
    -- 风险信息
    risk_category ENUM('technical', 'schedule', 'cost', 'resource', 'external', 'other') 
        NOT NULL COMMENT '风险类别',
    risk_name VARCHAR(200) NOT NULL COMMENT '风险名称',
    description TEXT COMMENT '风险描述',
    
    -- 风险评估
    probability ENUM('low', 'medium', 'high') COMMENT '发生概率',
    impact ENUM('low', 'medium', 'high') COMMENT '影响程度',
    risk_level ENUM('low', 'medium', 'high', 'critical') COMMENT '风险等级',
    
    -- 应对措施
    response_strategy ENUM('avoid', 'mitigate', 'transfer', 'accept') COMMENT '应对策略',
    response_plan TEXT COMMENT '应对措施',
    
    -- 责任人
    owner_id BIGINT COMMENT '责任人ID',
    owner_name VARCHAR(50) COMMENT '责任人',
    
    -- 状态
    status ENUM('identified', 'analyzing', 'responding', 'monitoring', 'closed') 
        DEFAULT 'identified' COMMENT '状态',
    
    -- 跟踪
    follow_up_date DATE COMMENT '跟踪日期',
    last_update TEXT COMMENT '最新进展',
    
    -- 触发/关闭
    trigger_condition TEXT COMMENT '触发条件',
    is_triggered BOOLEAN DEFAULT FALSE COMMENT '是否已触发',
    triggered_date DATE COMMENT '触发日期',
    closed_date DATE COMMENT '关闭日期',
    closed_reason TEXT COMMENT '关闭原因',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_status (status)
) COMMENT '项目风险表';


-- 7. 项目成本表
CREATE TABLE pmo_project_cost (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    
    -- 成本类别
    cost_category VARCHAR(50) NOT NULL COMMENT '成本类别',
    cost_item VARCHAR(100) NOT NULL COMMENT '成本项',
    
    -- 金额
    budget_amount DECIMAL(12,2) DEFAULT 0 COMMENT '预算金额',
    actual_amount DECIMAL(12,2) DEFAULT 0 COMMENT '实际金额',
    
    -- 时间
    cost_month VARCHAR(7) COMMENT '成本月份(YYYY-MM)',
    record_date DATE COMMENT '记录日期',
    
    -- 来源
    source_type VARCHAR(50) COMMENT '来源类型',
    source_id BIGINT COMMENT '来源ID',
    source_no VARCHAR(50) COMMENT '来源单号',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT,
    
    INDEX idx_project (project_id),
    INDEX idx_category (cost_category),
    INDEX idx_month (cost_month)
) COMMENT '项目成本表';


-- 8. 项目会议记录表
CREATE TABLE pmo_meeting (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT COMMENT '项目ID(可为空表示跨项目会议)',
    
    -- 会议信息
    meeting_type ENUM('kickoff', 'weekly', 'milestone_review', 'change_review', 
        'risk_review', 'closure', 'other') NOT NULL COMMENT '会议类型',
    meeting_name VARCHAR(200) NOT NULL COMMENT '会议名称',
    
    -- 时间地点
    meeting_date DATE NOT NULL COMMENT '会议日期',
    start_time TIME COMMENT '开始时间',
    end_time TIME COMMENT '结束时间',
    location VARCHAR(100) COMMENT '会议地点',
    
    -- 人员
    organizer_id BIGINT COMMENT '组织者ID',
    organizer_name VARCHAR(50) COMMENT '组织者',
    attendees JSON COMMENT '参会人员',
    
    -- 内容
    agenda TEXT COMMENT '会议议程',
    minutes TEXT COMMENT '会议纪要',
    decisions TEXT COMMENT '会议决议',
    action_items JSON COMMENT '待办事项',
    
    -- 附件
    attachments JSON COMMENT '会议附件',
    
    -- 状态
    status ENUM('scheduled', 'ongoing', 'completed', 'cancelled') 
        DEFAULT 'scheduled' COMMENT '状态',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    
    INDEX idx_project (project_id),
    INDEX idx_meeting_date (meeting_date),
    INDEX idx_meeting_type (meeting_type)
) COMMENT '项目会议记录表';


-- 9. 项目资源分配表
CREATE TABLE pmo_resource_allocation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    task_id BIGINT COMMENT '任务ID',
    
    -- 资源信息
    resource_id BIGINT NOT NULL COMMENT '资源ID(人员ID)',
    resource_name VARCHAR(50) COMMENT '资源名称',
    resource_dept VARCHAR(50) COMMENT '所属部门',
    resource_role VARCHAR(50) COMMENT '项目角色',
    
    -- 分配信息
    allocation_percent INT DEFAULT 100 COMMENT '分配比例(%)',
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    planned_hours INT COMMENT '计划工时',
    actual_hours INT DEFAULT 0 COMMENT '实际工时',
    
    -- 状态
    status ENUM('planned', 'active', 'completed', 'released') 
        DEFAULT 'planned' COMMENT '状态',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_resource (resource_id),
    INDEX idx_dates (start_date, end_date)
) COMMENT '项目资源分配表';


-- 10. 项目结项表
CREATE TABLE pmo_project_closure (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL COMMENT '项目ID',
    
    -- 验收信息
    acceptance_date DATE COMMENT '验收日期',
    acceptance_result ENUM('passed', 'conditional', 'failed') COMMENT '验收结果',
    acceptance_notes TEXT COMMENT '验收说明',
    
    -- 项目总结
    project_summary TEXT COMMENT '项目总结',
    achievement TEXT COMMENT '项目成果',
    lessons_learned TEXT COMMENT '经验教训',
    improvement_suggestions TEXT COMMENT '改进建议',
    
    -- 成本核算
    final_budget DECIMAL(14,2) COMMENT '最终预算',
    final_cost DECIMAL(14,2) COMMENT '最终成本',
    cost_variance DECIMAL(14,2) COMMENT '成本偏差',
    
    -- 工时核算
    final_planned_hours INT COMMENT '最终计划工时',
    final_actual_hours INT COMMENT '最终实际工时',
    hours_variance INT COMMENT '工时偏差',
    
    -- 进度核算
    plan_duration INT COMMENT '计划周期(天)',
    actual_duration INT COMMENT '实际周期(天)',
    schedule_variance INT COMMENT '进度偏差(天)',
    
    -- 质量评估
    quality_score INT COMMENT '质量评分',
    customer_satisfaction INT COMMENT '客户满意度',
    
    -- 文档归档
    archive_status ENUM('pending', 'archiving', 'completed') COMMENT '归档状态',
    archive_path VARCHAR(500) COMMENT '归档路径',
    
    -- 结项评审
    closure_date DATE COMMENT '结项日期',
    reviewed_by BIGINT COMMENT '评审人',
    review_date DATE COMMENT '评审日期',
    review_result ENUM('approved', 'rejected') COMMENT '评审结果',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_project (project_id)
) COMMENT '项目结项表';
```

---

## 六、角色权限设计

### 6.1 项目管理部角色

| 角色 | 职责范围 | 系统权限 |
|------|---------|---------|
| **PMO总监** | 统筹项目管理工作 | 全部权限 |
| **项目经理** | 负责具体项目 | 本项目全部权限 |
| **PMO专员** | 辅助项目监控 | 查看权限+部分编辑 |
| **资源经理** | 资源调配管理 | 资源模块权限 |

### 6.2 权限矩阵

| 功能 | PMO总监 | 项目经理 | PMO专员 | 部门经理 |
|------|--------|---------|---------|---------|
| 查看所有项目 | ✓ | 部分 | ✓ | 部分 |
| 立项审批 | ✓ | - | - | - |
| 项目规划 | ✓ | ✓(本项目) | - | - |
| 进度更新 | ✓ | ✓(本项目) | - | - |
| 变更审批 | ✓ | ✓(小变更) | - | ✓ |
| 资源分配 | ✓ | ✓(本项目) | - | ✓(本部门) |
| 风险管理 | ✓ | ✓(本项目) | ✓ | ✓ |
| 结项审批 | ✓ | - | - | - |
| 报表查看 | 全部 | 本项目 | 全部 | 本部门 |

---

## 七、关键报表

### 7.1 项目状态周报

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     项目管理部周报 (2025年第1周)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  一、项目总体情况                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 在建项目: 45个 | A级: 12个 | B级: 20个 | C级: 13个               │   │
│  │ 本周新立项: 3个 | 本周结项: 2个 | 暂停: 1个                      │   │
│  │ 健康项目: 35个(78%) | 预警项目: 8个(18%) | 问题项目: 2个(4%)    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  二、重点项目进展                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 项目           │ 本周进展        │ 下周计划       │ 风险/问题   │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ XX汽车项目     │ 电气设计完成80% │ 完成电气评审   │ 无          │   │
│  │ YY新能源项目   │ 机械设计延期    │ 加班赶工       │ 进度滞后3天 │   │
│  │ ZZ医疗项目     │ 等待客户确认    │ 跟进客户反馈   │ 客户响应慢  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  三、本周预警事项                                                        │
│  • 🔴 YY项目关键物料供应商交期延迟一周，已启动备选方案                  │
│  • 🟡 电气部人员超负荷，建议协调支援或调整计划                          │
│  • 🟡 3个项目本周到期里程碑未完成，需跟进                               │
│                                                                         │
│  四、下周工作计划                                                        │
│  • 组织XX项目电气设计评审会议                                            │
│  • 协调解决YY项目物料问题                                                │
│  • 完成新立项项目的启动会议                                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 关键指标

| 指标 | 计算方式 | 目标值 | 当前值 |
|------|---------|--------|--------|
| **项目按期完成率** | 按期完成项目/总完成项目 | ≥90% | 85% |
| **项目成本控制率** | 成本未超预算项目/总项目 | ≥95% | 92% |
| **里程碑达成率** | 按期完成里程碑/总里程碑 | ≥85% | 80% |
| **资源利用率** | 实际工时/可用工时 | 75-85% | 82% |
| **客户满意度** | 满意度评分平均 | ≥4.5 | 4.3 |
| **变更控制率** | 主动变更/总变更 | ≥70% | 65% |

---

## 八、与其他模块集成

### 8.1 与任务中心集成

```
项目管理部                           任务中心
    │                                   │
    │ ── 项目WBS分解 ──────────────→    │ 生成任务
    │                                   │
    │ ← 任务进度/工时 ─────────────────│ 汇总上报
    │                                   │
    │ ── 里程碑检查 ──────────────→     │ 催办提醒
    │                                   │
```

### 8.2 与售前模块集成

```
售前技术支持                         项目管理部
    │                                   │
    │ ── 技术方案 ──────────────────→   │ 立项参考
    │ ── 成本估算 ──────────────────→   │ 预算编制
    │                                   │
    │ ←── 项目经验反馈 ────────────────│ 方案优化
    │                                   │
```

### 8.3 与财务模块集成

```
项目管理部                           财务部
    │                                   │
    │ ── 成本归集请求 ─────────────→    │ 成本核算
    │                                   │
    │ ← 成本数据 ──────────────────────│ 返回结果
    │                                   │
    │ ── 回款节点 ──────────────────→   │ 应收跟踪
    │                                   │
```

---

## 九、实施建议

### 9.1 分阶段实施

| 阶段 | 内容 | 周期 |
|------|------|------|
| **第一期** | 项目立项+基本监控+里程碑管理 | 4周 |
| **第二期** | 资源管理+成本管理+风险管理 | 4周 |
| **第三期** | 会议管理+变更管理+结项管理 | 3周 |
| **第四期** | 报表中心+系统集成+移动端 | 3周 |

### 9.2 关键成功因素

1. **领导支持** - 公司高层重视项目管理
2. **流程规范** - 制定并执行标准化流程
3. **数据质量** - 确保项目数据及时准确
4. **工具适配** - 系统功能符合业务需求
5. **持续改进** - 定期复盘优化管理方法
