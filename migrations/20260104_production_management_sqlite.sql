-- ============================================================
-- 生产管理模块 DDL - SQLite 版本
-- 创建日期：2026-01-04
-- 包含：车间、工位、生产人员、工序、设备、生产计划、工单、报工、异常、领料、日报
-- ============================================================

-- ==================== 车间管理 ====================

-- 车间表
CREATE TABLE IF NOT EXISTS workshop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workshop_code VARCHAR(50) NOT NULL UNIQUE,               -- 车间编码
    workshop_name VARCHAR(100) NOT NULL,                     -- 车间名称
    workshop_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',      -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/WAREHOUSE/OTHER
    manager_id INTEGER,                                      -- 车间主管ID
    location VARCHAR(200),                                   -- 车间位置
    capacity_hours DECIMAL(10,2),                           -- 日产能(工时)
    description TEXT,                                        -- 描述
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    -- FOREIGN KEY (manager_id) REFERENCES user(id) -- Deferred: user table created by ORM
);

CREATE INDEX IF NOT EXISTS idx_workshop_code ON workshop(workshop_code);
CREATE INDEX IF NOT EXISTS idx_workshop_type ON workshop(workshop_type);

-- 工位表
CREATE TABLE IF NOT EXISTS workstation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workstation_code VARCHAR(50) NOT NULL UNIQUE,            -- 工位编码
    workstation_name VARCHAR(100) NOT NULL,                  -- 工位名称
    workshop_id INTEGER NOT NULL,                            -- 所属车间ID
    equipment_id INTEGER,                                    -- 关联设备ID
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',              -- 状态:IDLE/WORKING/MAINTENANCE/DISABLED
    current_worker_id INTEGER,                               -- 当前操作工ID
    current_work_order_id INTEGER,                           -- 当前工单ID
    description TEXT,                                        -- 描述
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE INDEX IF NOT EXISTS idx_workstation_code ON workstation(workstation_code);
CREATE INDEX IF NOT EXISTS idx_workstation_workshop ON workstation(workshop_id);
CREATE INDEX IF NOT EXISTS idx_workstation_status ON workstation(status);


-- ==================== 人员管理 ====================

-- 生产人员表
CREATE TABLE IF NOT EXISTS worker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_no VARCHAR(50) NOT NULL UNIQUE,                   -- 工号
    user_id INTEGER,                                         -- 关联用户ID
    worker_name VARCHAR(50) NOT NULL,                        -- 姓名
    workshop_id INTEGER,                                     -- 所属车间ID
    position VARCHAR(50),                                    -- 岗位
    skill_level VARCHAR(20) DEFAULT 'JUNIOR',                -- 技能等级:JUNIOR/INTERMEDIATE/SENIOR/EXPERT
    phone VARCHAR(20),                                       -- 联系电话
    entry_date DATE,                                         -- 入职日期
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',            -- 状态:ACTIVE/LEAVE/RESIGNED
    hourly_rate DECIMAL(10,2),                              -- 时薪(元)
    remark TEXT,                                             -- 备注
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否在职
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
    -- FOREIGN KEY (user_id) REFERENCES user(id) -- Deferred: user table created by ORM
);

CREATE INDEX IF NOT EXISTS idx_worker_no ON worker(worker_no);
CREATE INDEX IF NOT EXISTS idx_worker_workshop ON worker(workshop_id);
CREATE INDEX IF NOT EXISTS idx_worker_status ON worker(status);

-- 工人技能表
CREATE TABLE IF NOT EXISTS worker_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,                              -- 工人ID
    process_id INTEGER NOT NULL,                             -- 工序ID
    skill_level VARCHAR(20) NOT NULL DEFAULT 'JUNIOR',       -- 技能等级
    certified_date DATE,                                     -- 认证日期
    expiry_date DATE,                                        -- 有效期
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES worker(id),
    FOREIGN KEY (process_id) REFERENCES process_dict(id)
);

CREATE INDEX IF NOT EXISTS idx_worker_skill_worker ON worker_skill(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_skill_process ON worker_skill(process_id);


-- ==================== 工序字典 ====================

-- 工序字典表
CREATE TABLE IF NOT EXISTS process_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_code VARCHAR(50) NOT NULL UNIQUE,                -- 工序编码
    process_name VARCHAR(100) NOT NULL,                      -- 工序名称
    process_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',       -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/INSPECTION/OTHER
    standard_hours DECIMAL(10,2),                           -- 标准工时(小时)
    description TEXT,                                        -- 描述
    work_instruction TEXT,                                   -- 作业指导
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_process_code ON process_dict(process_code);
CREATE INDEX IF NOT EXISTS idx_process_type ON process_dict(process_type);


-- ==================== 设备管理 ====================

-- 设备表
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_code VARCHAR(50) NOT NULL UNIQUE,              -- 设备编码
    equipment_name VARCHAR(100) NOT NULL,                    -- 设备名称
    model VARCHAR(100),                                      -- 型号规格
    manufacturer VARCHAR(100),                               -- 生产厂家
    workshop_id INTEGER,                                     -- 所属车间ID
    purchase_date DATE,                                      -- 购置日期
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',              -- 状态:IDLE/RUNNING/MAINTENANCE/REPAIR/DISABLED
    last_maintenance_date DATE,                              -- 上次保养日期
    next_maintenance_date DATE,                              -- 下次保养日期
    asset_no VARCHAR(50),                                    -- 固定资产编号
    remark TEXT,                                             -- 备注
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
);

CREATE INDEX IF NOT EXISTS idx_equipment_code ON equipment(equipment_code);
CREATE INDEX IF NOT EXISTS idx_equipment_workshop ON equipment(workshop_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);

-- 设备保养维修记录表
CREATE TABLE IF NOT EXISTS equipment_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,                           -- 设备ID
    maintenance_type VARCHAR(20) NOT NULL,                   -- 类型:maintenance/repair
    maintenance_date DATE NOT NULL,                          -- 保养/维修日期
    content TEXT,                                            -- 保养/维修内容
    cost DECIMAL(14,2),                                     -- 费用
    performed_by VARCHAR(50),                                -- 执行人
    next_maintenance_date DATE,                              -- 下次保养日期
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE INDEX IF NOT EXISTS idx_equip_maint_equipment ON equipment_maintenance(equipment_id);
CREATE INDEX IF NOT EXISTS idx_equip_maint_date ON equipment_maintenance(maintenance_date);


-- ==================== 生产计划 ====================

-- 生产计划表
CREATE TABLE IF NOT EXISTS production_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_no VARCHAR(50) NOT NULL UNIQUE,                     -- 计划编号
    plan_name VARCHAR(200) NOT NULL,                         -- 计划名称
    plan_type VARCHAR(20) NOT NULL DEFAULT 'MASTER',         -- 类型:MASTER(主计划)/WORKSHOP(车间计划)
    project_id INTEGER,                                      -- 关联项目ID
    workshop_id INTEGER,                                     -- 车间ID(车间计划用)
    plan_start_date DATE NOT NULL,                           -- 计划开始日期
    plan_end_date DATE NOT NULL,                             -- 计划结束日期
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',             -- 状态:DRAFT/SUBMITTED/APPROVED/PUBLISHED/EXECUTING/COMPLETED/CANCELLED
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    description TEXT,                                        -- 计划说明
    created_by INTEGER,                                      -- 创建人ID
    approved_by INTEGER,                                     -- 审批人ID
    approved_at DATETIME,                                    -- 审批时间
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
    -- Note: FKs to project/user tables deferred (created by ORM or other migrations)
);

CREATE INDEX IF NOT EXISTS idx_prod_plan_no ON production_plan(plan_no);
CREATE INDEX IF NOT EXISTS idx_prod_plan_project ON production_plan(project_id);
CREATE INDEX IF NOT EXISTS idx_prod_plan_workshop ON production_plan(workshop_id);
CREATE INDEX IF NOT EXISTS idx_prod_plan_status ON production_plan(status);
CREATE INDEX IF NOT EXISTS idx_prod_plan_dates ON production_plan(plan_start_date, plan_end_date);


-- ==================== 生产工单 ====================

-- 生产工单表
CREATE TABLE IF NOT EXISTS work_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_no VARCHAR(50) NOT NULL UNIQUE,               -- 工单编号
    task_name VARCHAR(200) NOT NULL,                         -- 任务名称
    task_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',          -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/INSPECTION/OTHER
    project_id INTEGER,                                      -- 项目ID
    machine_id INTEGER,                                      -- 机台ID
    production_plan_id INTEGER,                              -- 生产计划ID
    process_id INTEGER,                                      -- 工序ID
    workshop_id INTEGER,                                     -- 车间ID
    workstation_id INTEGER,                                  -- 工位ID
    
    -- 物料相关
    material_id INTEGER,                                     -- 物料ID
    material_name VARCHAR(200),                              -- 物料名称
    specification VARCHAR(200),                              -- 规格型号
    drawing_no VARCHAR(100),                                 -- 图纸编号
    
    -- 计划信息
    plan_qty INTEGER DEFAULT 1,                              -- 计划数量
    completed_qty INTEGER DEFAULT 0,                         -- 完成数量
    qualified_qty INTEGER DEFAULT 0,                         -- 合格数量
    defect_qty INTEGER DEFAULT 0,                            -- 不良数量
    standard_hours DECIMAL(10,2),                           -- 标准工时(小时)
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时(小时)
    
    -- 时间安排
    plan_start_date DATE,                                    -- 计划开始日期
    plan_end_date DATE,                                      -- 计划结束日期
    actual_start_time DATETIME,                              -- 实际开始时间
    actual_end_time DATETIME,                                -- 实际结束时间
    
    -- 派工信息
    assigned_to INTEGER,                                     -- 指派给(工人ID)
    assigned_at DATETIME,                                    -- 派工时间
    assigned_by INTEGER,                                     -- 派工人ID
    
    -- 状态信息
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',           -- 状态:PENDING/ASSIGNED/STARTED/PAUSED/COMPLETED/APPROVED/CANCELLED
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL',          -- 优先级:LOW/NORMAL/HIGH/URGENT
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    
    -- 其他
    work_content TEXT,                                       -- 工作内容
    remark TEXT,                                             -- 备注
    pause_reason TEXT,                                       -- 暂停原因
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (production_plan_id) REFERENCES production_plan(id),
    FOREIGN KEY (process_id) REFERENCES process_dict(id),
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (workstation_id) REFERENCES workstation(id),
    FOREIGN KEY (assigned_to) REFERENCES worker(id)
    -- Note: FKs to project/machine/material/user tables deferred
);

CREATE INDEX IF NOT EXISTS idx_work_order_no ON work_order(work_order_no);
CREATE INDEX IF NOT EXISTS idx_work_order_project ON work_order(project_id);
CREATE INDEX IF NOT EXISTS idx_work_order_plan ON work_order(production_plan_id);
CREATE INDEX IF NOT EXISTS idx_work_order_workshop ON work_order(workshop_id);
CREATE INDEX IF NOT EXISTS idx_work_order_assigned ON work_order(assigned_to);
CREATE INDEX IF NOT EXISTS idx_work_order_status ON work_order(status);
CREATE INDEX IF NOT EXISTS idx_work_order_priority ON work_order(priority);
CREATE INDEX IF NOT EXISTS idx_work_order_dates ON work_order(plan_start_date, plan_end_date);


-- ==================== 报工管理 ====================

-- 报工记录表
CREATE TABLE IF NOT EXISTS work_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_no VARCHAR(50) NOT NULL UNIQUE,                   -- 报工单号
    work_order_id INTEGER NOT NULL,                          -- 工单ID
    worker_id INTEGER NOT NULL,                              -- 工人ID
    report_type VARCHAR(20) NOT NULL,                        -- 类型:START/PROGRESS/PAUSE/RESUME/COMPLETE
    report_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 报工时间
    
    -- 进度信息
    progress_percent INTEGER,                                -- 进度百分比
    work_hours DECIMAL(10,2),                               -- 本次工时(小时)
    
    -- 完工信息
    completed_qty INTEGER,                                   -- 完成数量
    qualified_qty INTEGER,                                   -- 合格数量
    defect_qty INTEGER,                                      -- 不良数量
    
    -- 审核信息
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',           -- 状态:PENDING/APPROVED/REJECTED
    approved_by INTEGER,                                     -- 审核人ID
    approved_at DATETIME,                                    -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    
    -- 其他
    description TEXT,                                        -- 工作描述
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (worker_id) REFERENCES worker(id)
    -- Note: FK to user table deferred
);

CREATE INDEX IF NOT EXISTS idx_work_report_no ON work_report(report_no);
CREATE INDEX IF NOT EXISTS idx_work_report_order ON work_report(work_order_id);
CREATE INDEX IF NOT EXISTS idx_work_report_worker ON work_report(worker_id);
CREATE INDEX IF NOT EXISTS idx_work_report_type ON work_report(report_type);
CREATE INDEX IF NOT EXISTS idx_work_report_status ON work_report(status);
CREATE INDEX IF NOT EXISTS idx_work_report_time ON work_report(report_time);


-- ==================== 生产异常 ====================

-- 生产异常表
CREATE TABLE IF NOT EXISTS production_exception (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_no VARCHAR(50) NOT NULL UNIQUE,                -- 异常编号
    exception_type VARCHAR(20) NOT NULL,                     -- 类型:MATERIAL/EQUIPMENT/QUALITY/PROCESS/SAFETY/OTHER
    exception_level VARCHAR(20) NOT NULL DEFAULT 'MINOR',    -- 级别:MINOR/MAJOR/CRITICAL
    title VARCHAR(200) NOT NULL,                             -- 异常标题
    description TEXT,                                        -- 异常描述
    
    -- 关联信息
    work_order_id INTEGER,                                   -- 关联工单ID
    project_id INTEGER,                                      -- 关联项目ID
    workshop_id INTEGER,                                     -- 车间ID
    equipment_id INTEGER,                                    -- 设备ID
    
    -- 上报信息
    reporter_id INTEGER NOT NULL,                            -- 上报人ID
    report_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 上报时间
    
    -- 处理信息
    status VARCHAR(20) NOT NULL DEFAULT 'REPORTED',          -- 状态:REPORTED/HANDLING/RESOLVED/CLOSED
    handler_id INTEGER,                                      -- 处理人ID
    handle_plan TEXT,                                        -- 处理方案
    handle_result TEXT,                                      -- 处理结果
    handle_time DATETIME,                                    -- 处理时间
    resolved_at DATETIME,                                    -- 解决时间
    
    -- 影响评估
    impact_hours DECIMAL(10,2),                             -- 影响工时(小时)
    impact_cost DECIMAL(14,2),                              -- 影响成本(元)
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
    -- Note: FKs to project/user tables deferred
);

CREATE INDEX IF NOT EXISTS idx_prod_exc_no ON production_exception(exception_no);
CREATE INDEX IF NOT EXISTS idx_prod_exc_type ON production_exception(exception_type);
CREATE INDEX IF NOT EXISTS idx_prod_exc_level ON production_exception(exception_level);
CREATE INDEX IF NOT EXISTS idx_prod_exc_status ON production_exception(status);
CREATE INDEX IF NOT EXISTS idx_prod_exc_work_order ON production_exception(work_order_id);
CREATE INDEX IF NOT EXISTS idx_prod_exc_project ON production_exception(project_id);


-- ==================== 领料管理 ====================

-- 领料单表
CREATE TABLE IF NOT EXISTS material_requisition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requisition_no VARCHAR(50) NOT NULL UNIQUE,              -- 领料单号
    work_order_id INTEGER,                                   -- 关联工单ID
    project_id INTEGER,                                      -- 项目ID
    
    -- 申请信息
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    apply_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 申请时间
    apply_reason TEXT,                                       -- 申请原因
    
    -- 审批信息
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',             -- 状态:DRAFT/SUBMITTED/APPROVED/REJECTED/ISSUED/COMPLETED/CANCELLED
    approved_by INTEGER,                                     -- 审批人ID
    approved_at DATETIME,                                    -- 审批时间
    approve_comment TEXT,                                    -- 审批意见
    
    -- 发料信息
    issued_by INTEGER,                                       -- 发料人ID
    issued_at DATETIME,                                      -- 发料时间
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id)
    -- Note: FKs to project/user tables deferred
);

CREATE INDEX IF NOT EXISTS idx_mat_req_no ON material_requisition(requisition_no);
CREATE INDEX IF NOT EXISTS idx_mat_req_work_order ON material_requisition(work_order_id);
CREATE INDEX IF NOT EXISTS idx_mat_req_project ON material_requisition(project_id);
CREATE INDEX IF NOT EXISTS idx_mat_req_status ON material_requisition(status);

-- 领料单明细表
CREATE TABLE IF NOT EXISTS material_requisition_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requisition_id INTEGER NOT NULL,                         -- 领料单ID
    material_id INTEGER NOT NULL,                            -- 物料ID
    
    request_qty DECIMAL(14,4) NOT NULL,                     -- 申请数量
    approved_qty DECIMAL(14,4),                             -- 批准数量
    issued_qty DECIMAL(14,4),                               -- 发放数量
    unit VARCHAR(20),                                        -- 单位
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (requisition_id) REFERENCES material_requisition(id)
    -- Note: FK to material table deferred
);

CREATE INDEX IF NOT EXISTS idx_mat_req_item_requisition ON material_requisition_item(requisition_id);
CREATE INDEX IF NOT EXISTS idx_mat_req_item_material ON material_requisition_item(material_id);


-- ==================== 生产日报 ====================

-- 生产日报表
CREATE TABLE IF NOT EXISTS production_daily_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE NOT NULL,                               -- 报告日期
    workshop_id INTEGER,                                     -- 车间ID(空表示全厂)
    
    -- 生产统计
    plan_qty INTEGER DEFAULT 0,                              -- 计划数量
    completed_qty INTEGER DEFAULT 0,                         -- 完成数量
    completion_rate DECIMAL(5,2) DEFAULT 0,                 -- 完成率(%)
    
    -- 工时统计
    plan_hours DECIMAL(10,2) DEFAULT 0,                     -- 计划工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    overtime_hours DECIMAL(10,2) DEFAULT 0,                 -- 加班工时
    efficiency DECIMAL(5,2) DEFAULT 0,                      -- 效率(%)
    
    -- 出勤统计
    should_attend INTEGER DEFAULT 0,                         -- 应出勤人数
    actual_attend INTEGER DEFAULT 0,                         -- 实际出勤
    leave_count INTEGER DEFAULT 0,                           -- 请假人数
    
    -- 质量统计
    total_qty INTEGER DEFAULT 0,                             -- 生产总数
    qualified_qty INTEGER DEFAULT 0,                         -- 合格数量
    pass_rate DECIMAL(5,2) DEFAULT 0,                       -- 合格率(%)
    
    -- 异常统计
    new_exception_count INTEGER DEFAULT 0,                   -- 新增异常数
    resolved_exception_count INTEGER DEFAULT 0,              -- 解决异常数
    
    summary TEXT,                                            -- 日报总结
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    UNIQUE(report_date, workshop_id)
    -- Note: FK to user table deferred
);

CREATE INDEX IF NOT EXISTS idx_prod_daily_date ON production_daily_report(report_date);
CREATE INDEX IF NOT EXISTS idx_prod_daily_workshop ON production_daily_report(workshop_id);


-- ==================== 初始化数据 ====================

-- 初始化车间
INSERT OR IGNORE INTO workshop (workshop_code, workshop_name, workshop_type, capacity_hours, is_active) VALUES
('WS-MACH', '机加车间', 'MACHINING', 120, 1),
('WS-ASSY', '装配车间', 'ASSEMBLY', 160, 1),
('WS-DBUG', '调试车间', 'DEBUGGING', 80, 1),
('WS-WELD', '焊接车间', 'WELDING', 60, 1);

-- 初始化工序字典
INSERT OR IGNORE INTO process_dict (process_code, process_name, process_type, standard_hours, is_active) VALUES
('CNC-MILL', 'CNC铣削', 'MACHINING', 4.0, 1),
('CNC-TURN', 'CNC车削', 'MACHINING', 3.0, 1),
('CNC-DRILL', '钻孔加工', 'MACHINING', 2.0, 1),
('GRIND', '磨削加工', 'MACHINING', 3.0, 1),
('WELD-ARC', '弧焊', 'WELDING', 4.0, 1),
('WELD-SPOT', '点焊', 'WELDING', 2.0, 1),
('MECH-ASM', '机械装配', 'ASSEMBLY', 6.0, 1),
('ELEC-ASM', '电气装配', 'ASSEMBLY', 8.0, 1),
('PIPE-ASM', '管路装配', 'ASSEMBLY', 4.0, 1),
('ELEC-DBG', '电气调试', 'DEBUGGING', 8.0, 1),
('SOFT-DBG', '软件调试', 'DEBUGGING', 16.0, 1),
('FINAL-DBG', '整机调试', 'DEBUGGING', 24.0, 1),
('QC-INSP', '质量检验', 'INSPECTION', 2.0, 1);

