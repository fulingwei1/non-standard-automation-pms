# 生产管理模块设计

## 一、生产部在公司中的角色定位

### 1.1 组织架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          生产部组织架构                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                         ┌──────────────┐                                │
│                         │  生产部经理   │                                │
│                         └──────┬───────┘                                │
│                                │                                        │
│          ┌─────────────────────┼─────────────────────┐                 │
│          │                     │                     │                 │
│    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐            │
│    │  机加车间   │        │  装配车间   │        │  调试车间   │            │
│    │  主管      │        │  主管      │        │  主管      │            │
│    └─────┬─────┘        └─────┬─────┘        └─────┬─────┘            │
│          │                     │                     │                 │
│    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐            │
│    │ • 车工    │        │ • 机械装配 │        │ • 电气调试 │            │
│    │ • 铣工    │        │ • 电气装配 │        │ • 软件调试 │            │
│    │ • 钳工    │        │ • 管路装配 │        │ • 整机调试 │            │
│    │ • 焊工    │        │           │        │           │            │
│    └───────────┘        └───────────┘        └───────────┘            │
│                                                                         │
│    人数配置(参考): 机加车间15人 + 装配车间20人 + 调试车间10人 = 45人     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 生产部核心职责

| 角色 | 职责范围 | 核心工作 |
|------|---------|---------|
| **生产部经理** | 统筹生产全局 | 生产计划、资源调配、进度管控、质量把控、成本控制 |
| **车间主管** | 管理本车间 | 任务分配、人员调度、进度跟踪、质量检验 |
| **生产工人** | 执行生产任务 | 接收任务、加工/装配/调试、报工、质量自检 |

### 1.3 生产部与其他部门的协作

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      生产部与其他部门协作关系                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐                                                        │
│  │  项目管理部  │ ──── 项目计划/交期要求 ────→  ┌─────────────┐         │
│  └─────────────┘                               │             │         │
│                                                │             │         │
│  ┌─────────────┐                               │             │         │
│  │   研发部    │ ──── 图纸/BOM/工艺 ─────────→ │   生产部    │         │
│  │(机械/电气)  │                               │             │         │
│  └─────────────┘ ←── 问题反馈/设计变更请求 ─── │             │         │
│                                                │             │         │
│  ┌─────────────┐                               │             │         │
│  │   采购部    │ ←── 物料需求计划 ────────────│             │         │
│  └─────────────┘ ──── 到货通知/缺料预警 ────→  │             │         │
│                                                │             │         │
│  ┌─────────────┐                               │             │         │
│  │   仓库      │ ←── 领料申请 ────────────────│             │         │
│  └─────────────┘ ──── 发料/库存信息 ─────────→ │             │         │
│                                                │             │         │
│  ┌─────────────┐                               │             │         │
│  │   品质部    │ ←── 送检申请 ────────────────│             │         │
│  └─────────────┘ ──── 检验结果/质量问题 ────→  └─────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 二、生产管理核心流程

### 2.1 生产计划流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         生产计划编制流程                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐          │
│  │ 项目计划 │ ──→ │ 需求分析 │ ──→ │ 产能评估 │ ──→ │ 排产计划 │          │
│  │ 输入    │     │         │     │         │     │ 编制    │          │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘          │
│       │               │               │               │                │
│       ▼               ▼               ▼               ▼                │
│  • 项目交期      • 工序分解      • 人员/设备      • 主生产计划          │
│  • BOM清单      • 工时估算      • 物料齐套      • 车间作业计划          │
│  • 图纸资料      • 优先级排序    • 负荷平衡      • 工位派工单            │
│                                                                         │
│                          ┌─────────┐                                   │
│                          │ 计划审批 │                                   │
│                          └────┬────┘                                   │
│                               │                                        │
│                    ┌──────────┴──────────┐                             │
│                    ▼                     ▼                             │
│              ┌─────────┐           ┌─────────┐                         │
│              │ 计划发布 │           │ 退回修改 │                         │
│              └─────────┘           └─────────┘                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 生产执行流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         生产执行流程                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│     车间主管                    生产工人                     系统        │
│        │                          │                          │         │
│        │  1.任务派工              │                          │         │
│        │ ─────────────────────→  │                          │         │
│        │                          │  2.接收任务              │         │
│        │                          │ ────────────────────────→│         │
│        │                          │                          │         │
│        │                          │  3.领料申请              │         │
│        │                          │ ────────────────────────→│         │
│        │                          │                          │ (仓库发料)│
│        │                          │  4.开工报告              │         │
│        │  5.进度监控              │ ────────────────────────→│         │
│        │ ←────────────────────── │                          │         │
│        │                          │                          │         │
│        │                          │  (执行加工/装配/调试)     │         │
│        │                          │                          │         │
│        │                          │  6.进度上报              │         │
│        │  7.查看进度              │ ────────────────────────→│         │
│        │ ←────────────────────────────────────────────────── │         │
│        │                          │                          │         │
│        │                          │  8.完工报告              │         │
│        │                          │ ────────────────────────→│         │
│        │                          │                          │         │
│        │  9.质量检验              │                          │         │
│        │ ─────────────────────→  │                          │         │
│        │                          │                          │         │
│        │  10.任务关闭             │                          │         │
│        │ ────────────────────────────────────────────────→  │         │
│        │                          │                          │         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 报工流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           报工流程                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  生产工人                                                               │
│     │                                                                   │
│     │  ┌─────────────────────────────────────────────────────────────┐ │
│     └─→│                    工人报工界面                              │ │
│        │  ┌─────────────────────────────────────────────────────────┐│ │
│        │  │ 今日待报工任务                                          ││ │
│        │  │ ┌─────────────────────────────────────────────────────┐ ││ │
│        │  │ │ 📦 XX项目-底板加工                                   │ ││ │
│        │  │ │    工序: 铣削     计划工时: 4h     状态: 进行中      │ ││ │
│        │  │ │    [开工] [报进度] [完工] [异常]                    │ ││ │
│        │  │ └─────────────────────────────────────────────────────┘ ││ │
│        │  │ ┌─────────────────────────────────────────────────────┐ ││ │
│        │  │ │ 📦 YY项目-支架装配                                   │ ││ │
│        │  │ │    工序: 装配     计划工时: 6h     状态: 待开工      │ ││ │
│        │  │ │    [开工]                                          │ ││ │
│        │  │ └─────────────────────────────────────────────────────┘ ││ │
│        │  └─────────────────────────────────────────────────────────┘│ │
│        │                                                             │ │
│        │  ┌─────────────────────────────────────────────────────────┐│ │
│        │  │ 报工记录                                                ││ │
│        │  │ • 开工时间: 08:30    完工时间: 12:15    实际工时: 3.75h ││ │
│        │  │ • 完成数量: 1件      合格数量: 1件      不良数: 0       ││ │
│        │  │ • 备注: 正常完成                                        ││ │
│        │  └─────────────────────────────────────────────────────────┘│ │
│        └─────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 三、角色功能设计

### 3.1 生产部经理功能

```
生产部经理功能模块
├── 📊 生产驾驶舱
│   ├── 生产概况(在产项目/今日产出/完成率)
│   ├── 各车间负荷
│   ├── 异常预警
│   ├── 关键节点
│   └── 产能趋势
│
├── 📅 生产计划
│   ├── 主生产计划(MPS)
│   │   ├── 计划编制
│   │   ├── 计划调整
│   │   └── 计划审批
│   ├── 车间作业计划
│   ├── 排产日历
│   └── 产能负荷分析
│
├── 👥 人员管理
│   ├── 人员花名册
│   ├── 技能矩阵
│   ├── 出勤管理
│   └── 绩效统计
│
├── 🔧 设备管理
│   ├── 设备台账
│   ├── 设备状态
│   ├── 保养计划
│   └── 故障记录
│
├── 📦 物料协调
│   ├── 物料需求计划
│   ├── 齐套分析
│   ├── 缺料预警
│   └── 到货跟踪
│
├── ⚠️ 异常管理
│   ├── 异常登记
│   ├── 异常处理
│   ├── 异常统计
│   └── 问题追溯
│
├── 📈 报表统计
│   ├── 生产日报
│   ├── 生产周报/月报
│   ├── 工时统计
│   ├── 效率分析
│   └── 质量分析
│
└── ⚙️ 基础配置
    ├── 工序管理
    ├── 工时标准
    └── 车间/工位配置
```

### 3.2 车间主管功能

```
车间主管功能模块
├── 📊 车间看板
│   ├── 今日任务
│   ├── 人员状态
│   ├── 设备状态
│   └── 进度概况
│
├── 📋 任务管理
│   ├── 任务列表
│   ├── 任务派工
│   ├── 任务调整
│   └── 进度跟踪
│
├── 👷 人员调度
│   ├── 人员排班
│   ├── 临时调配
│   └── 加班安排
│
├── ✅ 质量管理
│   ├── 首检确认
│   ├── 过程检验
│   ├── 完工检验
│   └── 不良处理
│
├── 📝 报工审核
│   ├── 待审核报工
│   ├── 工时确认
│   └── 异常复核
│
└── 📊 车间报表
    ├── 日产量统计
    ├── 人员工时
    └── 质量统计
```

### 3.3 生产工人功能

```
生产工人功能模块(移动端为主)
├── 📋 我的任务
│   ├── 待办任务
│   ├── 进行中任务
│   └── 已完成任务
│
├── ⏱️ 报工中心
│   ├── 扫码开工
│   ├── 进度上报
│   ├── 完工报告
│   └── 异常上报
│
├── 📦 领料申请
│   ├── 新建领料单
│   ├── 领料记录
│   └── 退料申请
│
├── 📄 技术资料
│   ├── 图纸查看
│   ├── 工艺文件
│   └── 作业指导书
│
├── 📊 我的统计
│   ├── 本月工时
│   ├── 完成任务数
│   └── 质量合格率
│
└── 🔔 消息通知
    ├── 任务通知
    ├── 催工提醒
    └── 异常反馈
```

---

## 四、数据库设计

### 4.1 核心表结构

```sql
-- =====================================================
-- 生产管理模块数据库设计
-- =====================================================

-- 1. 生产计划主表
CREATE TABLE prod_production_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_no VARCHAR(32) NOT NULL COMMENT '计划编号',
    plan_type ENUM('master', 'workshop', 'daily') NOT NULL COMMENT '计划类型:主计划/车间计划/日计划',
    
    -- 关联信息
    project_id BIGINT NOT NULL COMMENT '项目ID',
    project_no VARCHAR(32) COMMENT '项目编号',
    project_name VARCHAR(200) COMMENT '项目名称',
    
    -- 计划信息
    plan_name VARCHAR(200) NOT NULL COMMENT '计划名称',
    plan_start_date DATE NOT NULL COMMENT '计划开始日期',
    plan_end_date DATE NOT NULL COMMENT '计划结束日期',
    
    -- 状态
    status ENUM('draft', 'submitted', 'approved', 'executing', 'completed', 'cancelled') 
        DEFAULT 'draft' COMMENT '状态',
    
    -- 进度
    progress INT DEFAULT 0 COMMENT '完成进度(%)',
    
    -- 编制/审批
    prepared_by BIGINT COMMENT '编制人ID',
    prepared_name VARCHAR(50) COMMENT '编制人',
    prepared_at DATETIME COMMENT '编制时间',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_plan_no (plan_no),
    INDEX idx_project (project_id),
    INDEX idx_status (status)
) COMMENT '生产计划主表';


-- 2. 生产任务表(工单)
CREATE TABLE prod_work_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    work_order_no VARCHAR(32) NOT NULL COMMENT '工单编号',
    
    -- 关联信息
    plan_id BIGINT COMMENT '计划ID',
    project_id BIGINT NOT NULL COMMENT '项目ID',
    project_name VARCHAR(200) COMMENT '项目名称',
    
    -- 任务信息
    task_name VARCHAR(200) NOT NULL COMMENT '任务名称',
    task_type ENUM('machining', 'assembly', 'debugging', 'testing', 'other') 
        NOT NULL COMMENT '任务类型:机加/装配/调试/测试/其他',
    work_content TEXT COMMENT '工作内容',
    
    -- 物料信息
    material_code VARCHAR(50) COMMENT '物料编码',
    material_name VARCHAR(200) COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    
    -- 数量
    plan_qty INT DEFAULT 1 COMMENT '计划数量',
    completed_qty INT DEFAULT 0 COMMENT '完成数量',
    qualified_qty INT DEFAULT 0 COMMENT '合格数量',
    defect_qty INT DEFAULT 0 COMMENT '不良数量',
    
    -- 工序信息
    process_code VARCHAR(50) COMMENT '工序编码',
    process_name VARCHAR(100) COMMENT '工序名称',
    
    -- 工时
    standard_hours DECIMAL(10,2) COMMENT '标准工时(小时)',
    plan_hours DECIMAL(10,2) COMMENT '计划工时(小时)',
    actual_hours DECIMAL(10,2) DEFAULT 0 COMMENT '实际工时(小时)',
    
    -- 时间
    plan_start_date DATE COMMENT '计划开始日期',
    plan_end_date DATE COMMENT '计划结束日期',
    actual_start_time DATETIME COMMENT '实际开始时间',
    actual_end_time DATETIME COMMENT '实际结束时间',
    
    -- 分配
    workshop_id BIGINT COMMENT '车间ID',
    workshop_name VARCHAR(50) COMMENT '车间名称',
    workstation_id BIGINT COMMENT '工位ID',
    workstation_name VARCHAR(50) COMMENT '工位名称',
    assigned_to BIGINT COMMENT '指派人ID',
    assigned_name VARCHAR(50) COMMENT '指派人姓名',
    assigned_at DATETIME COMMENT '指派时间',
    
    -- 状态
    status ENUM('pending', 'assigned', 'started', 'paused', 'completed', 'cancelled') 
        DEFAULT 'pending' COMMENT '状态',
    
    -- 优先级
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    
    -- 质量
    quality_status ENUM('pending', 'inspecting', 'passed', 'failed') COMMENT '质量状态',
    
    -- 图纸/工艺
    drawing_no VARCHAR(50) COMMENT '图纸编号',
    process_route TEXT COMMENT '工艺路线',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT,
    
    INDEX idx_work_order_no (work_order_no),
    INDEX idx_project (project_id),
    INDEX idx_assigned (assigned_to),
    INDEX idx_workshop (workshop_id),
    INDEX idx_status (status),
    INDEX idx_plan_date (plan_start_date, plan_end_date)
) COMMENT '生产任务表(工单)';


-- 3. 报工记录表
CREATE TABLE prod_work_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_no VARCHAR(32) NOT NULL COMMENT '报工单号',
    
    -- 关联信息
    work_order_id BIGINT NOT NULL COMMENT '工单ID',
    work_order_no VARCHAR(32) COMMENT '工单编号',
    project_id BIGINT COMMENT '项目ID',
    
    -- 报工类型
    report_type ENUM('start', 'progress', 'complete', 'pause', 'resume') 
        NOT NULL COMMENT '报工类型:开工/进度/完工/暂停/恢复',
    
    -- 报工人
    worker_id BIGINT NOT NULL COMMENT '报工人ID',
    worker_name VARCHAR(50) COMMENT '报工人姓名',
    
    -- 时间
    report_time DATETIME NOT NULL COMMENT '报工时间',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    work_hours DECIMAL(10,2) COMMENT '工作时长(小时)',
    
    -- 数量
    completed_qty INT COMMENT '完成数量',
    qualified_qty INT COMMENT '合格数量',
    defect_qty INT COMMENT '不良数量',
    
    -- 进度
    progress_percent INT COMMENT '进度百分比',
    
    -- 描述
    work_description TEXT COMMENT '工作描述',
    problem_description TEXT COMMENT '问题描述',
    
    -- 审核
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '审核状态',
    reviewed_by BIGINT COMMENT '审核人ID',
    reviewed_at DATETIME COMMENT '审核时间',
    review_comment TEXT COMMENT '审核意见',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_report_no (report_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_worker (worker_id),
    INDEX idx_report_time (report_time)
) COMMENT '报工记录表';


-- 4. 生产异常表
CREATE TABLE prod_exception (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    exception_no VARCHAR(32) NOT NULL COMMENT '异常编号',
    
    -- 关联信息
    work_order_id BIGINT COMMENT '工单ID',
    project_id BIGINT COMMENT '项目ID',
    
    -- 异常信息
    exception_type ENUM('material', 'equipment', 'quality', 'process', 'personnel', 'other') 
        NOT NULL COMMENT '异常类型:物料/设备/质量/工艺/人员/其他',
    exception_level ENUM('minor', 'major', 'critical') DEFAULT 'minor' COMMENT '异常级别',
    
    title VARCHAR(200) NOT NULL COMMENT '异常标题',
    description TEXT NOT NULL COMMENT '异常描述',
    
    -- 影响
    impact_description TEXT COMMENT '影响描述',
    delay_hours DECIMAL(10,2) COMMENT '预计延误工时',
    
    -- 上报人
    reporter_id BIGINT NOT NULL COMMENT '上报人ID',
    reporter_name VARCHAR(50) COMMENT '上报人姓名',
    report_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上报时间',
    
    -- 处理信息
    handler_id BIGINT COMMENT '处理人ID',
    handler_name VARCHAR(50) COMMENT '处理人姓名',
    handle_plan TEXT COMMENT '处理方案',
    handle_result TEXT COMMENT '处理结果',
    handle_time DATETIME COMMENT '处理时间',
    
    -- 状态
    status ENUM('reported', 'handling', 'resolved', 'closed') DEFAULT 'reported' COMMENT '状态',
    
    -- 附件
    attachments JSON COMMENT '附件',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_exception_no (exception_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_status (status),
    INDEX idx_type (exception_type)
) COMMENT '生产异常表';


-- 5. 车间表
CREATE TABLE prod_workshop (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workshop_code VARCHAR(20) NOT NULL COMMENT '车间编码',
    workshop_name VARCHAR(50) NOT NULL COMMENT '车间名称',
    workshop_type ENUM('machining', 'assembly', 'debugging', 'testing', 'warehouse') 
        COMMENT '车间类型',
    
    -- 负责人
    manager_id BIGINT COMMENT '主管ID',
    manager_name VARCHAR(50) COMMENT '主管姓名',
    
    -- 产能信息
    capacity_hours DECIMAL(10,2) COMMENT '日产能(工时)',
    worker_count INT COMMENT '人员数量',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_code (workshop_code)
) COMMENT '车间表';


-- 6. 工位表
CREATE TABLE prod_workstation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workshop_id BIGINT NOT NULL COMMENT '车间ID',
    workstation_code VARCHAR(20) NOT NULL COMMENT '工位编码',
    workstation_name VARCHAR(50) NOT NULL COMMENT '工位名称',
    
    -- 工位类型
    workstation_type VARCHAR(50) COMMENT '工位类型',
    
    -- 关联设备
    equipment_id BIGINT COMMENT '设备ID',
    equipment_name VARCHAR(100) COMMENT '设备名称',
    
    -- 状态
    status ENUM('idle', 'working', 'maintenance', 'disabled') DEFAULT 'idle' COMMENT '状态',
    current_worker_id BIGINT COMMENT '当前操作人ID',
    current_work_order_id BIGINT COMMENT '当前工单ID',
    
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_workshop (workshop_id)
) COMMENT '工位表';


-- 7. 生产人员表(扩展用户信息)
CREATE TABLE prod_worker (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    
    -- 基本信息
    worker_no VARCHAR(20) COMMENT '工号',
    worker_name VARCHAR(50) COMMENT '姓名',
    
    -- 所属
    workshop_id BIGINT COMMENT '所属车间ID',
    workshop_name VARCHAR(50) COMMENT '车间名称',
    team_name VARCHAR(50) COMMENT '班组名称',
    
    -- 岗位
    position VARCHAR(50) COMMENT '岗位',
    skill_level ENUM('junior', 'intermediate', 'senior', 'expert') COMMENT '技能等级',
    
    -- 技能
    skills JSON COMMENT '技能列表',
    certifications JSON COMMENT '资质证书',
    
    -- 工时信息
    hourly_rate DECIMAL(10,2) COMMENT '小时工资',
    
    -- 状态
    status ENUM('active', 'leave', 'resigned') DEFAULT 'active' COMMENT '状态',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_user (user_id),
    INDEX idx_workshop (workshop_id)
) COMMENT '生产人员表';


-- 8. 工序字典表
CREATE TABLE prod_process (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    process_code VARCHAR(20) NOT NULL COMMENT '工序编码',
    process_name VARCHAR(50) NOT NULL COMMENT '工序名称',
    process_type ENUM('machining', 'assembly', 'debugging', 'testing', 'other') 
        COMMENT '工序类型',
    
    -- 标准工时
    standard_hours DECIMAL(10,2) COMMENT '标准工时',
    
    -- 所需技能
    required_skills JSON COMMENT '所需技能',
    
    -- 适用车间
    applicable_workshops JSON COMMENT '适用车间ID列表',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 备注
    description TEXT COMMENT '工序描述',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_code (process_code)
) COMMENT '工序字典表';


-- 9. 领料单表
CREATE TABLE prod_material_requisition (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    requisition_no VARCHAR(32) NOT NULL COMMENT '领料单号',
    
    -- 关联信息
    work_order_id BIGINT COMMENT '工单ID',
    project_id BIGINT COMMENT '项目ID',
    
    -- 申请信息
    applicant_id BIGINT NOT NULL COMMENT '申请人ID',
    applicant_name VARCHAR(50) COMMENT '申请人姓名',
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    
    -- 状态
    status ENUM('draft', 'submitted', 'approved', 'picking', 'completed', 'cancelled') 
        DEFAULT 'draft' COMMENT '状态',
    
    -- 审批
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    
    -- 发料
    issued_by BIGINT COMMENT '发料人ID',
    issued_at DATETIME COMMENT '发料时间',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_requisition_no (requisition_no),
    INDEX idx_work_order (work_order_id)
) COMMENT '领料单表';


-- 10. 领料单明细表
CREATE TABLE prod_material_requisition_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    requisition_id BIGINT NOT NULL COMMENT '领料单ID',
    
    -- 物料信息
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    unit VARCHAR(20) COMMENT '单位',
    
    -- 数量
    request_qty DECIMAL(12,4) NOT NULL COMMENT '申请数量',
    approved_qty DECIMAL(12,4) COMMENT '批准数量',
    issued_qty DECIMAL(12,4) COMMENT '发放数量',
    
    -- 备注
    remarks TEXT COMMENT '备注',
    
    INDEX idx_requisition (requisition_id)
) COMMENT '领料单明细表';


-- 11. 设备表
CREATE TABLE prod_equipment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    equipment_code VARCHAR(32) NOT NULL COMMENT '设备编码',
    equipment_name VARCHAR(100) NOT NULL COMMENT '设备名称',
    
    -- 分类
    equipment_type VARCHAR(50) COMMENT '设备类型',
    category VARCHAR(50) COMMENT '设备类别',
    
    -- 规格
    model VARCHAR(100) COMMENT '型号',
    manufacturer VARCHAR(100) COMMENT '制造商',
    
    -- 位置
    workshop_id BIGINT COMMENT '所属车间',
    location VARCHAR(100) COMMENT '位置',
    
    -- 状态
    status ENUM('idle', 'running', 'maintenance', 'repair', 'scrapped') 
        DEFAULT 'idle' COMMENT '状态',
    
    -- 维保
    last_maintenance_date DATE COMMENT '上次保养日期',
    next_maintenance_date DATE COMMENT '下次保养日期',
    
    -- 购置信息
    purchase_date DATE COMMENT '购置日期',
    purchase_cost DECIMAL(12,2) COMMENT '购置成本',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_code (equipment_code),
    INDEX idx_workshop (workshop_id)
) COMMENT '设备表';


-- 12. 生产日报表
CREATE TABLE prod_daily_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_date DATE NOT NULL COMMENT '报告日期',
    workshop_id BIGINT COMMENT '车间ID',
    
    -- 生产统计
    plan_qty INT COMMENT '计划产量',
    completed_qty INT COMMENT '完成产量',
    completion_rate DECIMAL(5,2) COMMENT '完成率(%)',
    
    -- 工时统计
    plan_hours DECIMAL(10,2) COMMENT '计划工时',
    actual_hours DECIMAL(10,2) COMMENT '实际工时',
    efficiency DECIMAL(5,2) COMMENT '效率(%)',
    
    -- 人员统计
    attendance_count INT COMMENT '出勤人数',
    absence_count INT COMMENT '缺勤人数',
    overtime_hours DECIMAL(10,2) COMMENT '加班工时',
    
    -- 质量统计
    qualified_qty INT COMMENT '合格数量',
    defect_qty INT COMMENT '不良数量',
    pass_rate DECIMAL(5,2) COMMENT '合格率(%)',
    
    -- 异常统计
    exception_count INT COMMENT '异常数量',
    resolved_count INT COMMENT '已解决数量',
    
    -- 汇报人
    reporter_id BIGINT COMMENT '汇报人ID',
    report_time DATETIME COMMENT '汇报时间',
    
    -- 备注
    summary TEXT COMMENT '工作总结',
    issues TEXT COMMENT '问题与建议',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_date_workshop (report_date, workshop_id),
    INDEX idx_report_date (report_date)
) COMMENT '生产日报表';
```

---

## 五、界面设计

### 5.1 生产部经理驾驶舱

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        生产管理驾驶舱                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 今日生产概况                                      2025年1月3日    │   │
│  ├─────────┬─────────┬─────────┬─────────┬─────────────────────────┤   │
│  │ 在产项目 │ 今日任务 │ 已完成  │ 异常数  │ 今日效率               │   │
│  │   12    │   45    │   32    │    3    │  87%  ████████░░       │   │
│  └─────────┴─────────┴─────────┴─────────┴─────────────────────────┘   │
│                                                                         │
│  ┌───────────────────────────────┐ ┌───────────────────────────────┐   │
│  │ 车间负荷                       │ │ 今日异常                       │   │
│  │                               │ │                               │   │
│  │  机加车间  ████████░░ 85%     │ │ 🔴 XX项目缺料，影响装配        │   │
│  │  装配车间  ██████████ 95% ⚠️  │ │ 🟡 CNC机床故障，已报修        │   │
│  │  调试车间  ██████░░░░ 68%     │ │ 🟡 YY项目图纸有误，待确认      │   │
│  └───────────────────────────────┘ └───────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 重点项目生产进度                                                 │   │
│  ├──────────────────────────────────────────────────────┬──────────┤   │
│  │ XX汽车传感器测试设备                                  │          │   │
│  │   机加: ██████████ 100%  装配: ████████░░ 75%  调试: ░░░░ 0%   │   │
│  │   交期: 2025-02-10  状态: 🟢正常                                │   │
│  ├──────────────────────────────────────────────────────┼──────────┤   │
│  │ YY新能源电池检测线                                    │          │   │
│  │   机加: ████████░░ 80%   装配: ████░░░░ 30%   调试: ░░░░ 0%    │   │
│  │   交期: 2025-03-15  状态: 🟡有风险(物料延迟)                     │   │
│  └──────────────────────────────────────────────────────┴──────────┘   │
│                                                                         │
│  ┌───────────────────────────────┐ ┌───────────────────────────────┐   │
│  │ 本周产能趋势                   │ │ 人员出勤                       │   │
│  │         完成 ─── 计划         │ │                               │   │
│  │  45 ┃    ╱╲                   │ │  出勤: 42人  请假: 2人        │   │
│  │     ┃   ╱  ╲  ╱╲             │ │  加班: 8人   培训: 1人        │   │
│  │  30 ┃──╱────╲╱──╲──          │ │                               │   │
│  │     ┃ ╱           ╲          │ │  机加车间: 14/15              │   │
│  │  15 ┃╱                       │ │  装配车间: 18/20              │   │
│  │     ┗━━━━━━━━━━━━━━━         │ │  调试车间: 10/10              │   │
│  │       周一 周二 周三 周四      │ │                               │   │
│  └───────────────────────────────┘ └───────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 车间任务看板

```
┌─────────────────────────────────────────────────────────────────────────┐
│  装配车间任务看板                                     [+ 派工] [刷新]    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐        │
│  │ 📋 待派工  │   │ ⏳ 待开工  │   │ 🔧 进行中  │   │ ✅ 已完成  │        │
│  │    (5)    │   │    (8)    │   │    (12)   │   │    (25)   │        │
│  ├───────────┤   ├───────────┤   ├───────────┤   ├───────────┤        │
│  │┌─────────┐│   │┌─────────┐│   │┌─────────┐│   │┌─────────┐│        │
│  ││ 🔴 紧急  ││   ││ XX项目  ││   ││ XX项目  ││   ││ AA项目  ││        │
│  ││ ZZ项目  ││   ││ 支架装配 ││   ││ 底座装配 ││   ││ 框架装配 ││        │
│  ││ 电气柜  ││   ││ 张三    ││   ││ 李四    ││   ││ 王五    ││        │
│  ││ 8h      ││   ││ 计划:6h ││   ││ 75%    ││   ││ ✓完成   ││        │
│  │└─────────┘│   │└─────────┘│   │└─────────┘│   │└─────────┘│        │
│  │┌─────────┐│   │┌─────────┐│   │┌─────────┐│   │┌─────────┐│        │
│  ││ YY项目  ││   ││ YY项目  ││   ││ BB项目  ││   ││ CC项目  ││        │
│  ││ 传动装配 ││   ││ 台面装配 ││   ││ 管路装配 ││   ││ 外壳装配 ││        │
│  ││ 6h      ││   ││ 王五    ││   ││ 赵六    ││   ││ ✓完成   ││        │
│  │└─────────┘│   │└─────────┘│   ││ 40%    ││   │└─────────┘│        │
│  │           │   │           │   │└─────────┘│   │           │        │
│  └───────────┘   └───────────┘   └───────────┘   └───────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 工人报工界面(移动端)

```
┌─────────────────────────────┐
│  ← 我的任务          张三    │
├─────────────────────────────┤
│                             │
│  今日任务 (3)               │
│                             │
│  ┌───────────────────────┐  │
│  │ 🔴 紧急               │  │
│  │ XX项目-支架装配       │  │
│  │ 工序: 机械装配        │  │
│  │ 计划: 6h  已用: 2.5h  │  │
│  │                       │  │
│  │ ████████░░░░ 65%      │  │
│  │                       │  │
│  │ [📷扫码] [⏱报进度] [✓完工]│
│  └───────────────────────┘  │
│                             │
│  ┌───────────────────────┐  │
│  │ YY项目-底座装配       │  │
│  │ 工序: 机械装配        │  │
│  │ 计划: 4h  状态: 待开工 │  │
│  │                       │  │
│  │ [▶ 开工]              │  │
│  └───────────────────────┘  │
│                             │
│  ┌───────────────────────┐  │
│  │ ✅ BB项目-框架装配    │  │
│  │ 已完成 用时: 3.5h     │  │
│  │ 合格: 1件             │  │
│  └───────────────────────┘  │
│                             │
├─────────────────────────────┤
│  📋任务  ⏱报工  📦领料  👤我的│
└─────────────────────────────┘
```

---

## 六、关键指标(KPI)

### 6.1 生产部经理KPI

| 指标 | 计算方式 | 目标值 |
|------|---------|--------|
| **生产计划达成率** | 按期完成工单数/计划工单数 | ≥95% |
| **生产效率** | 标准工时/实际工时 | ≥85% |
| **一次合格率** | 首检合格数/总检验数 | ≥98% |
| **设备利用率** | 设备运行时间/可用时间 | ≥80% |
| **人均产出** | 完成产值/人数 | 持续提升 |
| **异常关闭率** | 24h内关闭异常/总异常 | ≥90% |

### 6.2 生产工人KPI

| 指标 | 计算方式 | 目标值 |
|------|---------|--------|
| **任务完成率** | 按期完成任务/分配任务 | ≥95% |
| **工时效率** | 标准工时/实际工时 | ≥100% |
| **质量合格率** | 合格数量/完成数量 | ≥99% |
| **报工及时率** | 按时报工次数/应报工次数 | ≥98% |
| **出勤率** | 实际出勤/应出勤 | ≥95% |

---

## 七、实施建议

### 7.1 分阶段实施

| 阶段 | 内容 | 周期 |
|------|------|------|
| **第一期** | 工单管理+报工系统+基础看板 | 4周 |
| **第二期** | 计划排产+物料协调+异常管理 | 4周 |
| **第三期** | 质量管理+设备管理+人员管理 | 3周 |
| **第四期** | 报表统计+移动端+系统集成 | 3周 |

### 7.2 关键成功因素

1. **工人配合** - 培训工人使用移动端报工
2. **数据准确** - 工时标准、BOM数据准确
3. **流程规范** - 按标准流程执行
4. **快速响应** - 异常快速发现和处理
5. **持续优化** - 根据数据分析优化流程
