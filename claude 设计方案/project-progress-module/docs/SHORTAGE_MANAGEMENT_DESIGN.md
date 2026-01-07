# 缺料管理系统详细设计

## 一、系统概述

### 1.1 背景与目标

非标自动化设备制造企业面临的物料管理痛点：
- **物料种类多**：每个项目物料清单(BOM)不同，难以标准化管理
- **需求不确定**：设计变更频繁，物料需求随时变化
- **供应链复杂**：供应商多、交期不稳定
- **信息孤岛**：采购、仓库、车间信息不互通
- **响应滞后**：缺料发现晚，处理慢，导致停工等待

### 1.2 系统目标

| 目标 | 当前状态 | 期望状态 | 核心措施 |
|------|----------|----------|----------|
| 齐套率 | 70% | ≥95% | 提前预警、智能分析 |
| 缺料响应时间 | 4小时 | ≤30分钟 | 实时监控、自动通知 |
| 停工时长 | 20小时/月 | ≤4小时/月 | 预防为主、快速处理 |
| 信息透明度 | 30% | 100% | 全流程可视化 |

---

## 二、业务流程设计

### 2.1 整体业务流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        缺料管理全流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   │
│  │需求产生│──→│齐套检查│──→│缺料预警│──→│缺料处理│──→│闭环验证│   │
│  └────────┘   └────────┘   └────────┘   └────────┘   └────────┘   │
│       │            │            │            │            │         │
│       ▼            ▼            ▼            ▼            ▼         │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   │
│  │BOM分解 │   │库存比对│   │分级通知│   │多方案  │   │到货确认│   │
│  │需求汇总│   │在途检查│   │责任分派│   │并行处理│   │效果评估│   │
│  └────────┘   └────────┘   └────────┘   └────────┘   └────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心业务场景

#### 场景一：工单开工前齐套检查

```
触发条件: 工单计划开工前3天 / 手动发起
    │
    ▼
┌─────────────────┐
│ 1. 获取工单BOM  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 逐项检查库存 │───→ 可用库存 = 账面库存 - 已分配 - 安全库存
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 检查在途物料 │───→ 预计到货日期 vs 需求日期
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────┐
│ 4. 计算齐套状态 │────→│ 齐套率100% │───→ 确认可开工
└────────┬────────┘     └─────────────┘
         │
         │ 齐套率<100%
         ▼
┌─────────────────┐
│ 5. 生成缺料清单 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. 触发预警流程 │
└─────────────────┘
```

#### 场景二：车间现场缺料上报

```
工人发现缺料
    │
    ▼
┌─────────────────┐
│ 1. 扫码/选择    │───→ 工单号、物料信息
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 填写上报信息 │───→ 缺料数量、紧急程度、描述、拍照
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 系统自动匹配 │───→ 匹配在途物料、替代料、其他工单余料
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 通知相关人员 │───→ 仓管、采购、车间主任、项目经理
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 启动处理流程 │
└─────────────────┘
```

### 2.3 预警分级处理

| 级别 | 触发条件 | 响应时限 | 通知对象 | 处理措施 |
|------|----------|----------|----------|----------|
| 一级(提醒) | 开工前7天缺料，有替代料 | 24小时 | 采购员 | 常规采购 |
| 二级(警告) | 开工前3天缺料，在途可能延迟 | 8小时 | 采购主管、车间主任 | 加急采购、调整排产 |
| 三级(紧急) | 开工当天缺料，已影响生产 | 2小时 | 生产经理、项目经理 | 紧急调拨、替代料审批 |
| 四级(严重) | 缺料导致停工，影响交付 | 30分钟 | 总经理、供应链总监 | 特批处理、升级供应商 |

### 2.4 缺料处理决策树

```
                    ┌─────────────┐
                    │   缺料发生   │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │     检查库存/在途        │
              └────────────┬────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │ 有库存   │     │ 有在途   │     │ 都没有   │
   └────┬─────┘     └────┬─────┘     └────┬─────┘
        │                │                │
        ▼                ▼                ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │ 立即发料 │     │ 跟催到货 │     │ 紧急采购 │
   └──────────┘     └────┬─────┘     └────┬─────┘
                         │                │
              ┌──────────┴────┐     ┌─────┴─────┐
              │               │     │           │
              ▼               ▼     ▼           ▼
        ┌──────────┐   ┌──────┐ ┌────────┐ ┌────────┐
        │ 等待到货 │   │调整  │ │使用替代│ │外协加工│
        └──────────┘   │排产  │ └────────┘ └────────┘
                       └──────┘
```

---

## 三、数据模型设计

### 3.1 核心表结构

#### 1. 工单BOM明细表
```sql
CREATE TABLE mat_work_order_bom (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    work_order_id BIGINT NOT NULL COMMENT '工单ID',
    work_order_no VARCHAR(32) COMMENT '工单号',
    project_id BIGINT COMMENT '项目ID',
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    unit VARCHAR(20) DEFAULT '件' COMMENT '单位',
    bom_qty DECIMAL(12,4) NOT NULL COMMENT 'BOM用量',
    required_qty DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    required_date DATE NOT NULL COMMENT '需求日期',
    material_type ENUM('purchase','make','outsource') DEFAULT 'purchase',
    lead_time INT DEFAULT 0 COMMENT '采购提前期(天)',
    is_key_material BOOLEAN DEFAULT FALSE COMMENT '是否关键物料',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_work_order (work_order_id),
    INDEX idx_material (material_code)
) COMMENT '工单BOM明细表';
```

#### 2. 物料需求汇总表
```sql
CREATE TABLE mat_material_requirement (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    requirement_no VARCHAR(32) NOT NULL COMMENT '需求编号',
    source_type ENUM('work_order','project','manual') NOT NULL,
    work_order_id BIGINT COMMENT '工单ID',
    project_id BIGINT COMMENT '项目ID',
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    specification VARCHAR(200),
    unit VARCHAR(20),
    required_qty DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    stock_qty DECIMAL(12,4) DEFAULT 0 COMMENT '库存可用',
    allocated_qty DECIMAL(12,4) DEFAULT 0 COMMENT '已分配',
    in_transit_qty DECIMAL(12,4) DEFAULT 0 COMMENT '在途数量',
    shortage_qty DECIMAL(12,4) DEFAULT 0 COMMENT '缺料数量',
    required_date DATE NOT NULL,
    status ENUM('pending','partial','fulfilled','cancelled') DEFAULT 'pending',
    fulfill_method ENUM('stock','purchase','substitute','transfer'),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_requirement_no (requirement_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_material (material_code),
    INDEX idx_status (status)
) COMMENT '物料需求汇总表';
```

#### 3. 齐套检查记录表
```sql
CREATE TABLE mat_kit_check (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    check_no VARCHAR(32) NOT NULL COMMENT '检查编号',
    check_type ENUM('work_order','project','batch') NOT NULL,
    work_order_id BIGINT,
    project_id BIGINT,
    check_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    check_method ENUM('auto','manual') DEFAULT 'auto',
    checked_by BIGINT COMMENT '检查人',
    total_items INT DEFAULT 0 COMMENT '物料总项',
    fulfilled_items INT DEFAULT 0 COMMENT '已齐套项',
    shortage_items INT DEFAULT 0 COMMENT '缺料项',
    in_transit_items INT DEFAULT 0 COMMENT '在途项',
    kit_rate DECIMAL(5,2) DEFAULT 0 COMMENT '齐套率(%)',
    kit_status ENUM('complete','partial','shortage') DEFAULT 'shortage',
    shortage_summary JSON COMMENT '缺料汇总JSON',
    can_start BOOLEAN DEFAULT FALSE COMMENT '是否可开工',
    start_confirmed BOOLEAN DEFAULT FALSE COMMENT '已确认开工',
    confirm_time DATETIME,
    confirmed_by BIGINT,
    confirm_remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_check_no (check_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_kit_status (kit_status)
) COMMENT '齐套检查记录表';
```

#### 4. 缺料预警表
```sql
CREATE TABLE mat_shortage_alert (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_no VARCHAR(32) NOT NULL COMMENT '预警编号',
    work_order_id BIGINT,
    work_order_no VARCHAR(32),
    project_id BIGINT,
    project_name VARCHAR(200),
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    specification VARCHAR(200),
    shortage_qty DECIMAL(12,4) NOT NULL,
    shortage_value DECIMAL(12,2),
    required_date DATE NOT NULL,
    days_to_required INT,
    
    -- 预警级别: level1=提醒, level2=警告, level3=紧急, level4=严重
    alert_level ENUM('level1','level2','level3','level4') DEFAULT 'level1',
    
    -- 影响评估
    impact_type ENUM('none','delay','stop','delivery') DEFAULT 'none',
    impact_description TEXT,
    affected_process VARCHAR(100),
    estimated_delay_days INT DEFAULT 0,
    
    -- 通知信息
    notify_time DATETIME,
    notify_count INT DEFAULT 0,
    notified_users JSON,
    response_deadline DATETIME,
    is_overdue BOOLEAN DEFAULT FALSE,
    
    -- 处理状态
    status ENUM('pending','handling','resolved','escalated','closed') DEFAULT 'pending',
    
    -- 处理人
    handler_id BIGINT,
    handler_name VARCHAR(50),
    handle_start_time DATETIME,
    handle_plan TEXT,
    handle_method ENUM('wait_arrival','expedite','substitute','transfer',
                       'urgent_purchase','adjust_schedule','other'),
    expected_resolve_time DATETIME,
    
    -- 解决信息
    resolve_time DATETIME,
    resolve_method VARCHAR(50),
    resolve_description TEXT,
    actual_delay_days INT DEFAULT 0,
    
    -- 升级信息
    escalated BOOLEAN DEFAULT FALSE,
    escalate_time DATETIME,
    escalate_to BIGINT,
    escalate_reason TEXT,
    
    -- 关联单据
    related_po_no VARCHAR(50),
    related_transfer_no VARCHAR(50),
    related_substitute_no VARCHAR(50),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX idx_alert_no (alert_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_material (material_code),
    INDEX idx_alert_level (alert_level),
    INDEX idx_status (status),
    INDEX idx_handler (handler_id)
) COMMENT '缺料预警表';
```

#### 5. 缺料上报表
```sql
CREATE TABLE mat_shortage_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_no VARCHAR(32) NOT NULL,
    report_source ENUM('app','web','wechat','manual') DEFAULT 'app',
    work_order_id BIGINT NOT NULL,
    work_order_no VARCHAR(32),
    project_id BIGINT,
    workshop_id BIGINT,
    workstation VARCHAR(50),
    material_code VARCHAR(50),
    material_name VARCHAR(200) NOT NULL,
    specification VARCHAR(200),
    shortage_qty DECIMAL(12,4) NOT NULL,
    unit VARCHAR(20),
    reporter_id BIGINT NOT NULL,
    reporter_name VARCHAR(50),
    reporter_phone VARCHAR(20),
    report_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    urgency ENUM('normal','urgent','critical') DEFAULT 'normal',
    urgency_reason TEXT,
    description TEXT,
    images JSON COMMENT '图片URL列表',
    initial_cause ENUM('stock_error','bom_error','damage','quality_issue',
                       'not_delivered','other'),
    status ENUM('reported','confirmed','handling','resolved','closed','rejected') 
        DEFAULT 'reported',
    confirmed_by BIGINT,
    confirm_time DATETIME,
    confirm_result ENUM('confirmed','partially_confirmed','rejected'),
    confirm_remark TEXT,
    handler_id BIGINT,
    handler_name VARCHAR(50),
    handle_start_time DATETIME,
    handle_plan TEXT,
    resolve_time DATETIME,
    resolve_method TEXT,
    resolve_result TEXT,
    feedback_sent BOOLEAN DEFAULT FALSE,
    feedback_time DATETIME,
    feedback_content TEXT,
    alert_id BIGINT COMMENT '关联预警ID',
    reporter_rating INT,
    reporter_comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_report_no (report_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_reporter (reporter_id),
    INDEX idx_status (status),
    INDEX idx_urgency (urgency)
) COMMENT '缺料上报表';
```

#### 6. 到货跟踪表
```sql
CREATE TABLE mat_arrival_tracking (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    po_no VARCHAR(50) NOT NULL COMMENT '采购订单号',
    po_line_no INT DEFAULT 1,
    pr_no VARCHAR(50) COMMENT '请购单号',
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200),
    specification VARCHAR(200),
    unit VARCHAR(20),
    order_qty DECIMAL(12,4) NOT NULL,
    unit_price DECIMAL(12,4),
    total_amount DECIMAL(14,2),
    supplier_id BIGINT,
    supplier_code VARCHAR(50),
    supplier_name VARCHAR(100),
    supplier_contact VARCHAR(50),
    supplier_phone VARCHAR(20),
    order_date DATE,
    promised_date DATE COMMENT '承诺交期',
    expected_date DATE COMMENT '预计到货',
    actual_date DATE COMMENT '实际到货',
    ship_method ENUM('express','logistics','self_pickup','delivery'),
    carrier VARCHAR(50),
    tracking_no VARCHAR(100),
    ship_time DATETIME,
    status ENUM('ordered','confirmed','producing','shipped','arrived',
                'inspecting','warehoused','delayed','cancelled') DEFAULT 'ordered',
    is_delayed BOOLEAN DEFAULT FALSE,
    delay_days INT DEFAULT 0,
    delay_reason TEXT,
    delay_notified BOOLEAN DEFAULT FALSE,
    received_qty DECIMAL(12,4),
    qualified_qty DECIMAL(12,4),
    rejected_qty DECIMAL(12,4),
    quality_status ENUM('pending','qualified','partial','rejected'),
    receive_remark TEXT,
    related_requirements JSON,
    related_alerts JSON,
    priority_level INT DEFAULT 5,
    follow_up_count INT DEFAULT 0,
    last_follow_up_time DATETIME,
    next_follow_up_time DATETIME,
    buyer_id BIGINT,
    buyer_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_po_no (po_no),
    INDEX idx_material (material_code),
    INDEX idx_supplier (supplier_id),
    INDEX idx_expected_date (expected_date),
    INDEX idx_status (status),
    INDEX idx_is_delayed (is_delayed)
) COMMENT '到货跟踪表';
```

#### 7. 物料替代申请表
```sql
CREATE TABLE mat_substitution_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_no VARCHAR(32) NOT NULL,
    work_order_id BIGINT,
    project_id BIGINT,
    alert_id BIGINT,
    original_code VARCHAR(50) NOT NULL,
    original_name VARCHAR(200),
    original_spec VARCHAR(200),
    original_qty DECIMAL(12,4) NOT NULL,
    substitute_code VARCHAR(50) NOT NULL,
    substitute_name VARCHAR(200),
    substitute_spec VARCHAR(200),
    substitute_qty DECIMAL(12,4) NOT NULL,
    reason ENUM('shortage','cost','quality','delivery','other') DEFAULT 'shortage',
    reason_detail TEXT,
    cost_impact DECIMAL(12,2),
    quality_impact TEXT,
    schedule_impact TEXT,
    applicant_id BIGINT NOT NULL,
    applicant_name VARCHAR(50),
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','approved','rejected','executed','cancelled') DEFAULT 'pending',
    tech_approver_id BIGINT,
    tech_approver_name VARCHAR(50),
    tech_approve_time DATETIME,
    tech_approve_result ENUM('approved','rejected'),
    tech_approve_comment TEXT,
    prod_approver_id BIGINT,
    prod_approver_name VARCHAR(50),
    prod_approve_time DATETIME,
    prod_approve_result ENUM('approved','rejected'),
    prod_approve_comment TEXT,
    executed_time DATETIME,
    executed_by BIGINT,
    execute_remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_request_no (request_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_original (original_code),
    INDEX idx_status (status)
) COMMENT '物料替代申请表';
```

#### 8. 物料调拨申请表
```sql
CREATE TABLE mat_transfer_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    transfer_no VARCHAR(32) NOT NULL,
    from_work_order_id BIGINT,
    from_project_id BIGINT,
    from_warehouse VARCHAR(50),
    from_location VARCHAR(50),
    to_work_order_id BIGINT NOT NULL,
    to_project_id BIGINT,
    to_warehouse VARCHAR(50),
    material_code VARCHAR(50) NOT NULL,
    material_name VARCHAR(200),
    specification VARCHAR(200),
    transfer_qty DECIMAL(12,4) NOT NULL,
    unit VARCHAR(20),
    reason ENUM('shortage','priority','schedule','other') DEFAULT 'shortage',
    reason_detail TEXT,
    urgency ENUM('normal','urgent','critical') DEFAULT 'normal',
    alert_id BIGINT,
    applicant_id BIGINT NOT NULL,
    applicant_name VARCHAR(50),
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending','approved','rejected','executing','completed','cancelled') 
        DEFAULT 'pending',
    approver_id BIGINT,
    approver_name VARCHAR(50),
    approve_time DATETIME,
    approve_comment TEXT,
    execute_time DATETIME,
    executed_by BIGINT,
    actual_qty DECIMAL(12,4),
    execute_remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_transfer_no (transfer_no),
    INDEX idx_from_work_order (from_work_order_id),
    INDEX idx_to_work_order (to_work_order_id),
    INDEX idx_material (material_code),
    INDEX idx_status (status)
) COMMENT '物料调拨申请表';
```

#### 9. 预警处理日志表
```sql
CREATE TABLE mat_alert_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_id BIGINT NOT NULL,
    action_type ENUM('create','notify','assign','handle','update',
                     'escalate','resolve','close','reopen') NOT NULL,
    action_name VARCHAR(50),
    action_detail TEXT,
    before_status VARCHAR(20),
    after_status VARCHAR(20),
    before_level VARCHAR(20),
    after_level VARCHAR(20),
    operator_id BIGINT,
    operator_name VARCHAR(50),
    operator_role VARCHAR(50),
    action_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    extra_data JSON,
    INDEX idx_alert (alert_id),
    INDEX idx_action_time (action_time)
) COMMENT '预警处理日志表';
```

#### 10. 缺料统计日报表
```sql
CREATE TABLE mat_shortage_daily_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_date DATE NOT NULL,
    new_alerts INT DEFAULT 0,
    resolved_alerts INT DEFAULT 0,
    pending_alerts INT DEFAULT 0,
    overdue_alerts INT DEFAULT 0,
    level1_count INT DEFAULT 0,
    level2_count INT DEFAULT 0,
    level3_count INT DEFAULT 0,
    level4_count INT DEFAULT 0,
    new_reports INT DEFAULT 0,
    resolved_reports INT DEFAULT 0,
    total_work_orders INT DEFAULT 0,
    kit_complete_count INT DEFAULT 0,
    kit_rate DECIMAL(5,2) DEFAULT 0,
    expected_arrivals INT DEFAULT 0,
    actual_arrivals INT DEFAULT 0,
    delayed_arrivals INT DEFAULT 0,
    on_time_rate DECIMAL(5,2) DEFAULT 0,
    avg_response_minutes INT DEFAULT 0,
    avg_resolve_hours DECIMAL(5,2) DEFAULT 0,
    stoppage_count INT DEFAULT 0,
    stoppage_hours DECIMAL(8,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_date (report_date)
) COMMENT '缺料统计日报表';
```

---

## 四、API接口设计

### 4.1 接口清单

| 模块 | 接口 | 说明 |
|------|------|------|
| **齐套检查** | GET /kit-check/work-orders | 获取待检查工单列表 |
| | GET /kit-check/work-orders/{id} | 获取工单齐套详情 |
| | POST /kit-check/work-orders/{id}/check | 执行齐套检查 |
| | POST /kit-check/work-orders/{id}/confirm | 确认开工 |
| **缺料预警** | GET /alerts | 获取预警列表 |
| | GET /alerts/{id} | 获取预警详情 |
| | POST /alerts/{id}/assign | 分派处理人 |
| | POST /alerts/{id}/handle | 开始处理 |
| | POST /alerts/{id}/escalate | 升级预警 |
| | POST /alerts/{id}/resolve | 解决预警 |
| **缺料上报** | GET /reports | 获取上报列表 |
| | POST /reports | 创建上报 |
| | POST /reports/{id}/confirm | 确认上报 |
| | POST /reports/{id}/resolve | 解决上报 |
| **到货跟踪** | GET /arrivals | 获取到货列表 |
| | PUT /arrivals/{id}/status | 更新状态 |
| | POST /arrivals/{id}/follow-up | 创建跟催 |
| | POST /arrivals/{id}/receive | 确认收货 |
| **物料替代** | POST /substitutions | 创建替代申请 |
| | POST /substitutions/{id}/approve | 审批 |
| | POST /substitutions/{id}/execute | 执行 |
| **物料调拨** | POST /transfers | 创建调拨申请 |
| | POST /transfers/{id}/approve | 审批 |
| | POST /transfers/{id}/execute | 执行 |
| **统计分析** | GET /statistics/dashboard | 看板数据 |
| | GET /statistics/kit-rate | 齐套率统计 |
| | GET /statistics/shortage-analysis | 缺料分析 |
| | GET /statistics/supplier-delivery | 供应商交期 |

---

## 五、通知机制设计

### 5.1 通知渠道配置

| 渠道 | 时效性 | 触达率 | 适用场景 |
|------|--------|--------|----------|
| 企业微信 | 实时 | 95%+ | 日常通知 |
| 短信 | 实时 | 99%+ | 紧急通知 |
| 系统站内信 | 实时 | 80% | 一般通知 |
| 邮件 | 分钟级 | 70% | 汇总报告 |
| 语音电话 | 实时 | 99%+ | 特急通知 |

### 5.2 通知规则

```python
NOTIFICATION_RULES = {
    "shortage_alert": {
        "level1": {
            "channels": ["wechat", "system"],
            "recipients": ["buyer"],
            "delay": 0
        },
        "level2": {
            "channels": ["wechat", "system", "sms"],
            "recipients": ["buyer", "buyer_manager", "workshop_leader"],
            "delay": 0
        },
        "level3": {
            "channels": ["wechat", "sms", "system"],
            "recipients": ["buyer_manager", "production_manager", "project_manager"],
            "escalate_if_no_response": 30  # 30分钟无响应自动升级
        },
        "level4": {
            "channels": ["sms", "voice", "wechat"],
            "recipients": ["gm", "supply_chain_director"],
            "repeat_interval": 15  # 每15分钟重复
        }
    }
}
```

---

## 六、定时任务

| 任务 | 执行时间 | 说明 |
|------|----------|------|
| 每日齐套检查 | 每天06:00 | 检查未来7天工单齐套情况 |
| 预警级别升级 | 每30分钟 | 超时未响应自动升级 |
| 到货延迟检查 | 每2小时 | 检查并标记延迟订单 |
| 预警超时检查 | 每小时 | 标记超时预警 |
| 生成日报 | 每天22:00 | 生成当日统计日报 |
| 发送日报邮件 | 每天08:00 | 发送日报给管理层 |
| 同步ERP库存 | 每小时 | 从ERP同步库存数据 |
| 同步采购订单 | 每2小时 | 从ERP同步采购订单 |

---

## 七、权限设计

| 功能/角色 | 工人 | 仓管 | PMC | 采购员 | 采购主管 | 车间主任 | 生产经理 | 项目经理 | 总经理 |
|-----------|------|------|-----|--------|----------|----------|----------|----------|--------|
| 缺料上报 | ✓ | ✓ | ✓ | | | ✓ | | | |
| 齐套查看 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 齐套检查 | | ✓ | | | ✓ | ✓ | ✓ | |
| 开工确认 | | | | | ✓ | ✓ | | |
| 预警处理 | | | ✓ | ✓ | | ✓ | | |
| 预警升级 | | | | ✓ | | ✓ | | |
| 到货跟踪 | | ✓ | ✓ | ✓ | | | ✓ | |
| 到货确认 | | ✓ | | | | | | |
| 替代申请 | | | ✓ | ✓ | ✓ | ✓ | ✓ | |
| 替代审批 | | | | | | ✓ | | |
| 调拨申请 | | | | ✓ | ✓ | ✓ | ✓ | |
| 调拨审批 | | | | | | ✓ | | |
| 统计报表 | | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## 八、实施建议

### 8.1 实施阶段

**第一阶段（1-2周）：基础功能**
- 齐套检查功能
- 缺料预警基础
- 缺料上报
- 企业微信通知

**第二阶段（2-3周）：核心流程**
- 预警分级处理
- 到货跟踪
- 物料替代申请
- 物料调拨申请

**第三阶段（2周）：系统集成**
- ERP库存同步
- ERP采购单同步
- 审批流程集成

**第四阶段（1-2周）：统计分析**
- 统计报表
- 日报生成
- 绩效考核

### 8.2 预期效果

| 指标 | 当前 | 3个月目标 | 6个月目标 |
|------|------|-----------|-----------|
| 工单齐套率 | 70% | 80% | 90% |
| 缺料响应时间 | 4小时 | 2小时 | 30分钟 |
| 停工时长/月 | 20小时 | 12小时 | 4小时 |
| 预警解决率 | - | 85% | 95% |
| 供应商准时率 | 75% | 82% | 90% |

---

## 九、计算公式

### 齐套率
```
齐套率 = 已满足物料项数 / 物料总项数 × 100%

库存可用量 = 账面库存 - 已分配量 - 安全库存（可选）
```

### 预警级别判定
```python
def calculate_alert_level(shortage_info):
    days_to_required = (required_date - today).days
    
    if is_stopped:
        return 'level4'
    if days_to_required <= 0 and not in_transit:
        return 'level3'
    if days_to_required <= 3:
        return 'level3' if not in_transit_on_time else 'level2'
    if days_to_required <= 7:
        return 'level1' if has_substitute else 'level2'
    return 'level1'
```

### 供应商准时率
```
准时率 = 准时到货订单数 / 已到货订单总数 × 100%
延迟天数 = 实际到货日期 - 承诺交期
```
