-- ===========================================
-- 物料保障模块数据库设计
-- ===========================================

-- 1. 物料需求表
CREATE TABLE mat_material_requirement (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    requirement_no VARCHAR(32) NOT NULL COMMENT '需求编号',
    
    -- 来源信息
    source_type ENUM('project', 'work_order', 'manual') NOT NULL COMMENT '来源类型:项目/工单/手工',
    project_id BIGINT COMMENT '项目ID',
    work_order_id BIGINT COMMENT '工单ID',
    
    -- 物料信息
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    unit VARCHAR(20) COMMENT '单位',
    
    -- 数量信息
    required_qty DECIMAL(12,4) NOT NULL COMMENT '需求数量',
    allocated_qty DECIMAL(12,4) DEFAULT 0 COMMENT '已分配数量',
    shortage_qty DECIMAL(12,4) DEFAULT 0 COMMENT '缺料数量',
    
    -- 时间信息
    required_date DATE NOT NULL COMMENT '需求日期',
    
    -- 状态
    status ENUM('pending', 'partial', 'fulfilled', 'cancelled') DEFAULT 'pending' COMMENT '状态',
    
    -- 审计字段
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_requirement_no (requirement_no),
    INDEX idx_project (project_id),
    INDEX idx_work_order (work_order_id),
    INDEX idx_material (material_code),
    INDEX idx_required_date (required_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料需求表';


-- 2. 齐套检查记录表
CREATE TABLE mat_kit_check (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    check_no VARCHAR(32) NOT NULL COMMENT '检查编号',
    
    -- 检查对象
    check_type ENUM('project', 'work_order') NOT NULL COMMENT '检查类型',
    project_id BIGINT COMMENT '项目ID',
    work_order_id BIGINT COMMENT '工单ID',
    
    -- 检查结果
    total_items INT DEFAULT 0 COMMENT '物料总项数',
    fulfilled_items INT DEFAULT 0 COMMENT '齐套项数',
    shortage_items INT DEFAULT 0 COMMENT '缺料项数',
    in_transit_items INT DEFAULT 0 COMMENT '在途项数',
    kit_rate DECIMAL(5,2) DEFAULT 0 COMMENT '齐套率(%)',
    is_kit_complete BOOLEAN DEFAULT FALSE COMMENT '是否完全齐套',
    kit_status ENUM('complete', 'partial', 'shortage') DEFAULT 'shortage' COMMENT '齐套状态',
    
    -- 检查详情
    shortage_details JSON COMMENT '缺料明细(JSON格式)',
    
    -- 检查信息
    check_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    checked_by BIGINT COMMENT '检查人ID',
    check_method ENUM('auto', 'manual') DEFAULT 'auto' COMMENT '检查方式',
    
    -- 开工确认
    start_confirmed BOOLEAN DEFAULT FALSE COMMENT '是否已确认开工',
    confirm_time DATETIME COMMENT '确认时间',
    confirmed_by BIGINT COMMENT '确认人ID',
    confirm_type ENUM('start_now', 'wait', 'partial_start') COMMENT '确认类型',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_check_no (check_no),
    INDEX idx_project (project_id),
    INDEX idx_work_order (work_order_id),
    INDEX idx_check_time (check_time),
    INDEX idx_kit_status (kit_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='齐套检查记录表';


-- 3. 缺料预警表
CREATE TABLE mat_shortage_alert (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    alert_no VARCHAR(32) NOT NULL COMMENT '预警编号',
    
    -- 关联信息
    project_id BIGINT COMMENT '项目ID',
    work_order_id BIGINT COMMENT '工单ID',
    
    -- 物料信息
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    shortage_qty DECIMAL(12,4) NOT NULL COMMENT '缺料数量',
    required_date DATE COMMENT '需求日期',
    
    -- 预警级别: level1=一级提醒, level2=二级警告, level3=三级紧急, level4=四级严重
    alert_level ENUM('level1', 'level2', 'level3', 'level4') DEFAULT 'level1' COMMENT '预警级别',
    
    -- 影响信息
    impact_description TEXT COMMENT '影响描述',
    affected_process VARCHAR(100) COMMENT '受影响工序',
    
    -- 处理状态
    status ENUM('pending', 'handling', 'resolved', 'escalated', 'closed') DEFAULT 'pending' COMMENT '状态',
    
    -- 处理信息
    handler_id BIGINT COMMENT '处理人ID',
    handler_name VARCHAR(50) COMMENT '处理人姓名',
    handle_time DATETIME COMMENT '开始处理时间',
    handle_plan TEXT COMMENT '处理方案',
    expected_resolve_time DATETIME COMMENT '预计解决时间',
    
    -- 解决信息
    resolve_time DATETIME COMMENT '实际解决时间',
    resolve_method ENUM('arrived', 'substitute', 'transfer', 'other') COMMENT '解决方式',
    resolve_description TEXT COMMENT '解决说明',
    
    -- 升级信息
    escalate_time DATETIME COMMENT '升级时间',
    escalate_to BIGINT COMMENT '升级给谁',
    escalate_reason TEXT COMMENT '升级原因',
    
    -- 响应时限
    response_deadline DATETIME COMMENT '响应时限',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE INDEX idx_alert_no (alert_no),
    INDEX idx_project (project_id),
    INDEX idx_work_order (work_order_id),
    INDEX idx_material (material_code),
    INDEX idx_alert_level (alert_level),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺料预警表';


-- 4. 缺料上报表(工人上报)
CREATE TABLE mat_shortage_report (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    report_no VARCHAR(32) NOT NULL COMMENT '上报编号',
    
    -- 关联信息
    work_order_id BIGINT NOT NULL COMMENT '工单ID',
    project_id BIGINT COMMENT '项目ID',
    
    -- 物料信息
    material_code VARCHAR(50) COMMENT '物料编码',
    material_name VARCHAR(200) NOT NULL COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    shortage_qty DECIMAL(12,4) NOT NULL COMMENT '缺料数量',
    
    -- 上报人信息
    reporter_id BIGINT NOT NULL COMMENT '上报人ID',
    reporter_name VARCHAR(50) COMMENT '上报人姓名',
    report_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上报时间',
    
    -- 紧急程度: normal=一般, urgent=紧急, critical=非常紧急
    urgency ENUM('normal', 'urgent', 'critical') DEFAULT 'normal' COMMENT '紧急程度',
    
    -- 描述信息
    description TEXT COMMENT '问题描述',
    images JSON COMMENT '图片URL列表',
    
    -- 处理状态
    status ENUM('reported', 'confirmed', 'handling', 'resolved', 'closed') DEFAULT 'reported' COMMENT '状态',
    
    -- 处理信息
    handler_id BIGINT COMMENT '处理人ID',
    handler_name VARCHAR(50) COMMENT '处理人姓名',
    handle_time DATETIME COMMENT '开始处理时间',
    handle_method TEXT COMMENT '处理方式',
    
    -- 解决信息
    resolve_time DATETIME COMMENT '解决时间',
    resolve_result TEXT COMMENT '解决结果',
    
    -- 通知工人
    notified BOOLEAN DEFAULT FALSE COMMENT '是否已通知工人',
    notify_time DATETIME COMMENT '通知时间',
    
    -- 关联预警
    alert_id BIGINT COMMENT '关联的预警ID',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE INDEX idx_report_no (report_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_project (project_id),
    INDEX idx_reporter (reporter_id),
    INDEX idx_status (status),
    INDEX idx_urgency (urgency),
    INDEX idx_report_time (report_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺料上报表';


-- 5. 到货跟踪表
CREATE TABLE mat_arrival_tracking (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    -- 采购订单信息
    po_no VARCHAR(50) NOT NULL COMMENT '采购订单号',
    po_line_no INT DEFAULT 1 COMMENT '行号',
    
    -- 物料信息
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) COMMENT '物料名称',
    specification VARCHAR(200) COMMENT '规格型号',
    unit VARCHAR(20) COMMENT '单位',
    order_qty DECIMAL(12,4) NOT NULL COMMENT '订购数量',
    
    -- 供应商信息
    supplier_id BIGINT COMMENT '供应商ID',
    supplier_name VARCHAR(100) COMMENT '供应商名称',
    supplier_contact VARCHAR(100) COMMENT '供应商联系人',
    
    -- 交期信息
    order_date DATE COMMENT '下单日期',
    promised_date DATE COMMENT '承诺交期',
    expected_date DATE COMMENT '预计到货日期',
    actual_date DATE COMMENT '实际到货日期',
    
    -- 状态
    status ENUM('ordered', 'confirmed', 'shipped', 'arrived', 'delayed', 'cancelled') DEFAULT 'ordered' COMMENT '状态',
    
    -- 延迟信息
    is_delayed BOOLEAN DEFAULT FALSE COMMENT '是否延迟',
    delay_days INT DEFAULT 0 COMMENT '延迟天数',
    delay_reason TEXT COMMENT '延迟原因',
    
    -- 物流信息
    carrier VARCHAR(50) COMMENT '承运商',
    tracking_no VARCHAR(100) COMMENT '物流单号',
    shipped_time DATETIME COMMENT '发货时间',
    
    -- 到货信息
    received_qty DECIMAL(12,4) COMMENT '实收数量',
    quality_status ENUM('pending', 'qualified', 'partial', 'unqualified') COMMENT '质量状态',
    receive_remarks TEXT COMMENT '收货备注',
    
    -- 关联需求
    related_projects JSON COMMENT '关联项目(JSON数组)',
    related_work_orders JSON COMMENT '关联工单(JSON数组)',
    
    -- 跟催记录
    follow_up_count INT DEFAULT 0 COMMENT '跟催次数',
    last_follow_up_time DATETIME COMMENT '最后跟催时间',
    
    created_by BIGINT COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_po_no (po_no),
    INDEX idx_material (material_code),
    INDEX idx_supplier (supplier_id),
    INDEX idx_expected_date (expected_date),
    INDEX idx_status (status),
    INDEX idx_is_delayed (is_delayed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='到货跟踪表';


-- 6. 物料替代记录表
CREATE TABLE mat_substitution (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    substitution_no VARCHAR(32) NOT NULL COMMENT '替代单号',
    
    -- 关联信息
    work_order_id BIGINT COMMENT '工单ID',
    project_id BIGINT COMMENT '项目ID',
    
    -- 原物料信息
    original_material_code VARCHAR(50) NOT NULL COMMENT '原物料编码',
    original_material_name VARCHAR(200) COMMENT '原物料名称',
    original_specification VARCHAR(200) COMMENT '原物料规格',
    
    -- 替代料信息
    substitute_material_code VARCHAR(50) NOT NULL COMMENT '替代物料编码',
    substitute_material_name VARCHAR(200) COMMENT '替代物料名称',
    substitute_specification VARCHAR(200) COMMENT '替代物料规格',
    
    -- 替代数量
    qty DECIMAL(12,4) NOT NULL COMMENT '替代数量',
    
    -- 申请信息
    applicant_id BIGINT NOT NULL COMMENT '申请人ID',
    applicant_name VARCHAR(50) COMMENT '申请人姓名',
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    apply_reason TEXT COMMENT '申请原因',
    
    -- 审批信息
    status ENUM('pending', 'approved', 'rejected', 'executed') DEFAULT 'pending' COMMENT '状态',
    approver_id BIGINT COMMENT '审批人ID',
    approver_name VARCHAR(50) COMMENT '审批人姓名',
    approve_time DATETIME COMMENT '审批时间',
    approve_comment TEXT COMMENT '审批意见',
    
    -- 执行信息
    executed_time DATETIME COMMENT '执行时间',
    executed_by BIGINT COMMENT '执行人ID',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE INDEX idx_substitution_no (substitution_no),
    INDEX idx_work_order (work_order_id),
    INDEX idx_project (project_id),
    INDEX idx_original_material (original_material_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料替代记录表';


-- 7. 物料替代关系表(标准替代料)
CREATE TABLE mat_substitute_relation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    -- 原物料
    material_code VARCHAR(50) NOT NULL COMMENT '物料编码',
    material_name VARCHAR(200) COMMENT '物料名称',
    
    -- 替代料
    substitute_code VARCHAR(50) NOT NULL COMMENT '替代物料编码',
    substitute_name VARCHAR(200) COMMENT '替代物料名称',
    
    -- 替代属性
    compatibility ENUM('full', 'partial', 'conditional') DEFAULT 'full' COMMENT '兼容性',
    priority INT DEFAULT 1 COMMENT '优先级(数字越小越优先)',
    price_diff DECIMAL(12,2) DEFAULT 0 COMMENT '价格差异',
    remarks TEXT COMMENT '备注说明',
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    
    created_by BIGINT COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE INDEX idx_material_substitute (material_code, substitute_code),
    INDEX idx_material (material_code),
    INDEX idx_substitute (substitute_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料替代关系表';


-- 8. 预警处理记录表
CREATE TABLE mat_alert_handle_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    alert_id BIGINT NOT NULL COMMENT '预警ID',
    
    -- 操作信息
    action_type ENUM('create', 'handle', 'update', 'escalate', 'resolve', 'close') NOT NULL COMMENT '操作类型',
    action_description TEXT COMMENT '操作描述',
    
    -- 操作人
    operator_id BIGINT COMMENT '操作人ID',
    operator_name VARCHAR(50) COMMENT '操作人姓名',
    
    -- 操作时间
    action_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    
    -- 操作前后状态
    before_status VARCHAR(20) COMMENT '操作前状态',
    after_status VARCHAR(20) COMMENT '操作后状态',
    before_level VARCHAR(20) COMMENT '操作前级别',
    after_level VARCHAR(20) COMMENT '操作后级别',
    
    INDEX idx_alert (alert_id),
    INDEX idx_action_time (action_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警处理记录表';


-- 9. 到货跟催记录表
CREATE TABLE mat_arrival_follow_up (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    arrival_id BIGINT NOT NULL COMMENT '到货跟踪ID',
    
    -- 跟催信息
    follow_up_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '跟催时间',
    follow_up_method ENUM('phone', 'email', 'wechat', 'visit', 'other') DEFAULT 'phone' COMMENT '跟催方式',
    follow_up_content TEXT COMMENT '跟催内容',
    follow_up_result TEXT COMMENT '跟催结果',
    
    -- 供应商反馈
    supplier_feedback TEXT COMMENT '供应商反馈',
    new_expected_date DATE COMMENT '新预计到货日期',
    
    -- 跟催人
    follower_id BIGINT COMMENT '跟催人ID',
    follower_name VARCHAR(50) COMMENT '跟催人姓名',
    
    INDEX idx_arrival (arrival_id),
    INDEX idx_follow_up_time (follow_up_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='到货跟催记录表';


-- 10. 缺料通知记录表
CREATE TABLE mat_shortage_notification (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    
    -- 关联信息
    source_type ENUM('alert', 'report', 'arrival') NOT NULL COMMENT '来源类型',
    source_id BIGINT NOT NULL COMMENT '来源ID',
    
    -- 通知信息
    notify_type ENUM('wechat', 'sms', 'email', 'system') NOT NULL COMMENT '通知方式',
    notify_content TEXT COMMENT '通知内容',
    
    -- 接收人
    receiver_id BIGINT COMMENT '接收人ID',
    receiver_name VARCHAR(50) COMMENT '接收人姓名',
    receiver_contact VARCHAR(100) COMMENT '接收人联系方式',
    
    -- 发送状态
    send_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
    send_status ENUM('pending', 'sent', 'failed') DEFAULT 'pending' COMMENT '发送状态',
    send_result TEXT COMMENT '发送结果',
    
    -- 已读状态
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    read_time DATETIME COMMENT '已读时间',
    
    INDEX idx_source (source_type, source_id),
    INDEX idx_receiver (receiver_id),
    INDEX idx_send_time (send_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺料通知记录表';


-- ===========================================
-- 视图定义
-- ===========================================

-- 工单齐套状态视图
CREATE OR REPLACE VIEW v_work_order_kit_status AS
SELECT 
    wo.id AS work_order_id,
    wo.work_order_no,
    wo.task_name,
    wo.project_id,
    p.project_name,
    wo.workshop_id,
    ws.workshop_name,
    wo.plan_start_date,
    kc.total_items,
    kc.fulfilled_items,
    kc.shortage_items,
    kc.kit_rate,
    kc.kit_status,
    kc.check_time AS last_check_time,
    kc.start_confirmed
FROM ppm_work_order wo
LEFT JOIN ppm_project p ON wo.project_id = p.id
LEFT JOIN ppm_workshop ws ON wo.workshop_id = ws.id
LEFT JOIN mat_kit_check kc ON wo.id = kc.work_order_id
WHERE wo.status != 'completed';


-- 缺料预警统计视图
CREATE OR REPLACE VIEW v_shortage_alert_summary AS
SELECT 
    DATE(created_at) AS alert_date,
    alert_level,
    COUNT(*) AS total_count,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'handling' THEN 1 ELSE 0 END) AS handling_count,
    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_count,
    AVG(TIMESTAMPDIFF(HOUR, created_at, COALESCE(resolve_time, NOW()))) AS avg_resolve_hours
FROM mat_shortage_alert
GROUP BY DATE(created_at), alert_level;


-- 供应商交期统计视图
CREATE OR REPLACE VIEW v_supplier_delivery_stats AS
SELECT 
    supplier_id,
    supplier_name,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN is_delayed = FALSE THEN 1 ELSE 0 END) AS on_time_orders,
    SUM(CASE WHEN is_delayed = TRUE THEN 1 ELSE 0 END) AS delayed_orders,
    ROUND(SUM(CASE WHEN is_delayed = FALSE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS on_time_rate,
    AVG(CASE WHEN is_delayed = TRUE THEN delay_days ELSE 0 END) AS avg_delay_days
FROM mat_arrival_tracking
WHERE status IN ('arrived', 'delayed')
GROUP BY supplier_id, supplier_name;
