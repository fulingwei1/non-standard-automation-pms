-- ============================================
-- 缺料管理模块扩展表 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 工单BOM明细、物料需求汇总、齐套检查记录、预警处理日志、缺料统计日报
-- ============================================

-- ============================================
-- 1. 工单BOM明细表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_work_order_bom (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    work_order_id       BIGINT NOT NULL COMMENT '工单ID',
    work_order_no       VARCHAR(32) COMMENT '工单号',
    project_id          BIGINT COMMENT '项目ID',
    
    -- 物料信息
    material_id         BIGINT COMMENT '物料ID',
    material_code       VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name       VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification       VARCHAR(200) COMMENT '规格型号',
    unit                VARCHAR(20) DEFAULT '件' COMMENT '单位',
    
    -- 数量信息
    bom_qty             DECIMAL(12,4) NOT NULL COMMENT 'BOM用量',
    required_qty        DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    required_date       DATE NOT NULL COMMENT '需求日期',
    
    -- 物料类型
    material_type       VARCHAR(20) DEFAULT 'purchase' COMMENT 'purchase/make/outsource',
    lead_time           INT DEFAULT 0 COMMENT '采购提前期(天)',
    is_key_material     BOOLEAN DEFAULT FALSE COMMENT '是否关键物料',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    
    INDEX idx_work_order_bom_wo (work_order_id),
    INDEX idx_work_order_bom_material (material_code),
    INDEX idx_work_order_bom_date (required_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工单BOM明细表';

-- ============================================
-- 2. 物料需求汇总表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_material_requirement (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    requirement_no      VARCHAR(32) NOT NULL UNIQUE COMMENT '需求编号',
    
    -- 来源信息
    source_type         VARCHAR(20) NOT NULL COMMENT 'work_order/project/manual',
    work_order_id       BIGINT COMMENT '工单ID',
    project_id          BIGINT COMMENT '项目ID',
    
    -- 物料信息
    material_id         BIGINT COMMENT '物料ID',
    material_code       VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name       VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification       VARCHAR(200) COMMENT '规格型号',
    unit                VARCHAR(20) COMMENT '单位',
    
    -- 数量信息
    required_qty        DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    stock_qty           DECIMAL(12,4) DEFAULT 0 COMMENT '库存可用',
    allocated_qty       DECIMAL(12,4) DEFAULT 0 COMMENT '已分配',
    in_transit_qty      DECIMAL(12,4) DEFAULT 0 COMMENT '在途数量',
    shortage_qty        DECIMAL(12,4) DEFAULT 0 COMMENT '缺料数量',
    required_date       DATE NOT NULL COMMENT '需求日期',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/partial/fulfilled/cancelled',
    fulfill_method      VARCHAR(20) COMMENT 'stock/purchase/substitute/transfer',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    
    INDEX idx_requirement_no (requirement_no),
    INDEX idx_requirement_wo (work_order_id),
    INDEX idx_requirement_material (material_code),
    INDEX idx_requirement_status (status),
    INDEX idx_requirement_date (required_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料需求汇总表';

-- ============================================
-- 3. 齐套检查记录表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_kit_check (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    check_no            VARCHAR(32) NOT NULL UNIQUE COMMENT '检查编号',
    
    -- 检查对象
    check_type          VARCHAR(20) NOT NULL COMMENT 'work_order/project/batch',
    work_order_id       BIGINT COMMENT '工单ID',
    project_id          BIGINT COMMENT '项目ID',
    
    -- 检查结果
    total_items         INT DEFAULT 0 COMMENT '物料总项',
    fulfilled_items     INT DEFAULT 0 COMMENT '已齐套项',
    shortage_items      INT DEFAULT 0 COMMENT '缺料项',
    in_transit_items    INT DEFAULT 0 COMMENT '在途项',
    kit_rate            DECIMAL(5,2) DEFAULT 0 COMMENT '齐套率(%)',
    kit_status          VARCHAR(20) DEFAULT 'shortage' COMMENT 'complete/partial/shortage',
    shortage_summary    JSON COMMENT '缺料汇总JSON',
    
    -- 检查信息
    check_time          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    check_method        VARCHAR(20) DEFAULT 'auto' COMMENT 'auto/manual',
    checked_by          BIGINT COMMENT '检查人ID',
    
    -- 开工确认
    can_start           BOOLEAN DEFAULT FALSE COMMENT '是否可开工',
    start_confirmed     BOOLEAN DEFAULT FALSE COMMENT '已确认开工',
    confirm_time        DATETIME COMMENT '确认时间',
    confirmed_by        BIGINT COMMENT '确认人ID',
    confirm_remark      TEXT COMMENT '确认备注',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (checked_by) REFERENCES users(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id),
    
    INDEX idx_kit_check_no (check_no),
    INDEX idx_kit_check_wo (work_order_id),
    INDEX idx_kit_check_project (project_id),
    INDEX idx_kit_check_status (kit_status),
    INDEX idx_kit_check_time (check_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='齐套检查记录表';

-- ============================================
-- 4. 预警处理日志表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_alert_log (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    alert_id            BIGINT NOT NULL COMMENT '预警ID',
    
    -- 操作信息
    action_type         VARCHAR(20) NOT NULL COMMENT 'create/handle/update/escalate/resolve/close',
    action_description  TEXT COMMENT '操作描述',
    
    -- 操作人
    operator_id         BIGINT COMMENT '操作人ID',
    operator_name       VARCHAR(50) COMMENT '操作人姓名',
    action_time         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    
    -- 操作前后状态
    before_status       VARCHAR(20) COMMENT '操作前状态',
    after_status        VARCHAR(20) COMMENT '操作后状态',
    before_level        VARCHAR(20) COMMENT '操作前级别',
    after_level         VARCHAR(20) COMMENT '操作后级别',
    
    -- 扩展数据
    extra_data          JSON COMMENT '扩展数据JSON',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (operator_id) REFERENCES users(id),
    
    INDEX idx_alert_log_alert (alert_id),
    INDEX idx_alert_log_time (action_time),
    INDEX idx_alert_log_operator (operator_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警处理日志表';

-- ============================================
-- 5. 缺料统计日报表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_shortage_daily_report (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    report_date         DATE NOT NULL UNIQUE COMMENT '报告日期',
    
    -- 预警统计
    new_alerts          INT DEFAULT 0 COMMENT '新增预警数',
    resolved_alerts     INT DEFAULT 0 COMMENT '已解决预警数',
    pending_alerts      INT DEFAULT 0 COMMENT '待处理预警数',
    overdue_alerts      INT DEFAULT 0 COMMENT '逾期预警数',
    level1_count        INT DEFAULT 0 COMMENT '一级预警数',
    level2_count        INT DEFAULT 0 COMMENT '二级预警数',
    level3_count        INT DEFAULT 0 COMMENT '三级预警数',
    level4_count        INT DEFAULT 0 COMMENT '四级预警数',
    
    -- 上报统计
    new_reports         INT DEFAULT 0 COMMENT '新增上报数',
    resolved_reports    INT DEFAULT 0 COMMENT '已解决上报数',
    
    -- 工单统计
    total_work_orders   INT DEFAULT 0 COMMENT '总工单数',
    kit_complete_count  INT DEFAULT 0 COMMENT '齐套完成工单数',
    kit_rate            DECIMAL(5,2) DEFAULT 0 COMMENT '平均齐套率',
    
    -- 到货统计
    expected_arrivals   INT DEFAULT 0 COMMENT '预期到货数',
    actual_arrivals     INT DEFAULT 0 COMMENT '实际到货数',
    delayed_arrivals    INT DEFAULT 0 COMMENT '延迟到货数',
    on_time_rate        DECIMAL(5,2) DEFAULT 0 COMMENT '准时到货率',
    
    -- 响应时效
    avg_response_minutes INT DEFAULT 0 COMMENT '平均响应时间(分钟)',
    avg_resolve_hours   DECIMAL(5,2) DEFAULT 0 COMMENT '平均解决时间(小时)',
    
    -- 停工统计
    stoppage_count      INT DEFAULT 0 COMMENT '停工次数',
    stoppage_hours      DECIMAL(8,2) DEFAULT 0 COMMENT '停工时长(小时)',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_daily_report_date (report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺料统计日报表';

-- ============================================
-- 6. 缺料预警表（完整版）
-- ============================================

CREATE TABLE IF NOT EXISTS mat_shortage_alert (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    alert_no            VARCHAR(32) NOT NULL UNIQUE COMMENT '预警编号',
    work_order_id       BIGINT COMMENT '工单ID',
    work_order_no       VARCHAR(32) COMMENT '工单号',
    project_id          BIGINT COMMENT '项目ID',
    project_name        VARCHAR(200) COMMENT '项目名称',
    
    -- 物料信息
    material_id         BIGINT COMMENT '物料ID',
    material_code        VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name        VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification        VARCHAR(200) COMMENT '规格型号',
    shortage_qty         DECIMAL(12,4) NOT NULL COMMENT '缺料数量',
    shortage_value       DECIMAL(12,2) COMMENT '缺料金额',
    required_date        DATE NOT NULL COMMENT '需求日期',
    days_to_required     INT COMMENT '距离需求日期天数',
    
    -- 预警级别: level1=提醒, level2=警告, level3=紧急, level4=严重
    alert_level          VARCHAR(20) DEFAULT 'level1' COMMENT '预警级别：level1/level2/level3/level4',
    
    -- 影响评估
    impact_type          VARCHAR(20) DEFAULT 'none' COMMENT '影响类型：none/delay/stop/delivery',
    impact_description   TEXT COMMENT '影响描述',
    affected_process     VARCHAR(100) COMMENT '受影响工序',
    estimated_delay_days INT DEFAULT 0 COMMENT '预计延迟天数',
    
    -- 通知信息
    notify_time          DATETIME COMMENT '通知时间',
    notify_count         INT DEFAULT 0 COMMENT '通知次数',
    notified_users       JSON COMMENT '已通知用户列表（JSON）',
    response_deadline    DATETIME COMMENT '响应时限',
    is_overdue           BOOLEAN DEFAULT FALSE COMMENT '是否逾期',
    
    -- 处理状态
    status               VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/handling/resolved/escalated/closed',
    
    -- 处理人信息
    handler_id           BIGINT COMMENT '处理人ID',
    handler_name         VARCHAR(50) COMMENT '处理人姓名',
    handle_start_time    DATETIME COMMENT '开始处理时间',
    handle_plan          TEXT COMMENT '处理方案',
    handle_method        VARCHAR(20) COMMENT '处理方式：wait_arrival/expedite/substitute/transfer/urgent_purchase/adjust_schedule/other',
    expected_resolve_time DATETIME COMMENT '预计解决时间',
    
    -- 解决信息
    resolve_time         DATETIME COMMENT '实际解决时间',
    resolve_method       VARCHAR(50) COMMENT '解决方式',
    resolve_description  TEXT COMMENT '解决说明',
    actual_delay_days    INT DEFAULT 0 COMMENT '实际延迟天数',
    
    -- 升级信息
    escalated            BOOLEAN DEFAULT FALSE COMMENT '是否已升级',
    escalate_time        DATETIME COMMENT '升级时间',
    escalate_to          BIGINT COMMENT '升级给谁（用户ID）',
    escalate_reason      TEXT COMMENT '升级原因',
    
    -- 关联单据
    related_po_no        VARCHAR(50) COMMENT '关联采购订单号',
    related_transfer_no   VARCHAR(50) COMMENT '关联调拨单号',
    related_substitute_no VARCHAR(50) COMMENT '关联替代单号',
    
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (handler_id) REFERENCES users(id),
    FOREIGN KEY (escalate_to) REFERENCES users(id),
    
    INDEX idx_alert_no (alert_no),
    INDEX idx_alert_work_order (work_order_id),
    INDEX idx_alert_material (material_code),
    INDEX idx_alert_level (alert_level),
    INDEX idx_alert_status (status),
    INDEX idx_alert_handler (handler_id),
    INDEX idx_alert_required_date (required_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺料预警表';

