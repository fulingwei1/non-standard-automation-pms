-- ============================================================
-- 生产管理模块 DDL - MySQL 版本
-- 创建日期：2026-01-04
-- 包含：车间、工位、生产人员、工序、设备、生产计划、工单、报工、异常、领料、日报
-- ============================================================

-- ==================== 车间管理 ====================

-- 车间表
CREATE TABLE IF NOT EXISTS `workshop` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `workshop_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '车间编码',
    `workshop_name` VARCHAR(100) NOT NULL COMMENT '车间名称',
    `workshop_type` VARCHAR(20) NOT NULL DEFAULT 'OTHER' COMMENT '类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/WAREHOUSE/OTHER',
    `manager_id` INT NULL COMMENT '车间主管ID',
    `location` VARCHAR(200) NULL COMMENT '车间位置',
    `capacity_hours` DECIMAL(10,2) NULL COMMENT '日产能(工时)',
    `description` TEXT NULL COMMENT '描述',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_workshop_code` (`workshop_code`),
    INDEX `idx_workshop_type` (`workshop_type`),
    FOREIGN KEY (`manager_id`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='车间表';

-- 工位表
CREATE TABLE IF NOT EXISTS `workstation` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `workstation_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '工位编码',
    `workstation_name` VARCHAR(100) NOT NULL COMMENT '工位名称',
    `workshop_id` INT NOT NULL COMMENT '所属车间ID',
    `equipment_id` INT NULL COMMENT '关联设备ID',
    `status` VARCHAR(20) NOT NULL DEFAULT 'IDLE' COMMENT '状态:IDLE/WORKING/MAINTENANCE/DISABLED',
    `current_worker_id` INT NULL COMMENT '当前操作工ID',
    `current_work_order_id` INT NULL COMMENT '当前工单ID',
    `description` TEXT NULL COMMENT '描述',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_workstation_code` (`workstation_code`),
    INDEX `idx_workstation_workshop` (`workshop_id`),
    INDEX `idx_workstation_status` (`status`),
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`equipment_id`) REFERENCES `equipment`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工位表';


-- ==================== 人员管理 ====================

-- 生产人员表
CREATE TABLE IF NOT EXISTS `worker` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `worker_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '工号',
    `user_id` INT NULL COMMENT '关联用户ID',
    `worker_name` VARCHAR(50) NOT NULL COMMENT '姓名',
    `workshop_id` INT NULL COMMENT '所属车间ID',
    `position` VARCHAR(50) NULL COMMENT '岗位',
    `skill_level` VARCHAR(20) DEFAULT 'JUNIOR' COMMENT '技能等级:JUNIOR/INTERMEDIATE/SENIOR/EXPERT',
    `phone` VARCHAR(20) NULL COMMENT '联系电话',
    `entry_date` DATE NULL COMMENT '入职日期',
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态:ACTIVE/LEAVE/RESIGNED',
    `hourly_rate` DECIMAL(10,2) NULL COMMENT '时薪(元)',
    `remark` TEXT NULL COMMENT '备注',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否在职',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_worker_no` (`worker_no`),
    INDEX `idx_worker_workshop` (`workshop_id`),
    INDEX `idx_worker_status` (`status`),
    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产人员表';

-- 工人技能表
CREATE TABLE IF NOT EXISTS `worker_skill` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `worker_id` INT NOT NULL COMMENT '工人ID',
    `process_id` INT NOT NULL COMMENT '工序ID',
    `skill_level` VARCHAR(20) NOT NULL DEFAULT 'JUNIOR' COMMENT '技能等级',
    `certified_date` DATE NULL COMMENT '认证日期',
    `expiry_date` DATE NULL COMMENT '有效期',
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_worker_skill_worker` (`worker_id`),
    INDEX `idx_worker_skill_process` (`process_id`),
    FOREIGN KEY (`worker_id`) REFERENCES `worker`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`process_id`) REFERENCES `process_dict`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工人技能表';


-- ==================== 工序字典 ====================

-- 工序字典表
CREATE TABLE IF NOT EXISTS `process_dict` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `process_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '工序编码',
    `process_name` VARCHAR(100) NOT NULL COMMENT '工序名称',
    `process_type` VARCHAR(20) NOT NULL DEFAULT 'OTHER' COMMENT '类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/INSPECTION/OTHER',
    `standard_hours` DECIMAL(10,2) NULL COMMENT '标准工时(小时)',
    `description` TEXT NULL COMMENT '描述',
    `work_instruction` TEXT NULL COMMENT '作业指导',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_process_code` (`process_code`),
    INDEX `idx_process_type` (`process_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工序字典表';


-- ==================== 设备管理 ====================

-- 设备表
CREATE TABLE IF NOT EXISTS `equipment` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `equipment_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '设备编码',
    `equipment_name` VARCHAR(100) NOT NULL COMMENT '设备名称',
    `model` VARCHAR(100) NULL COMMENT '型号规格',
    `manufacturer` VARCHAR(100) NULL COMMENT '生产厂家',
    `workshop_id` INT NULL COMMENT '所属车间ID',
    `purchase_date` DATE NULL COMMENT '购置日期',
    `status` VARCHAR(20) NOT NULL DEFAULT 'IDLE' COMMENT '状态:IDLE/RUNNING/MAINTENANCE/REPAIR/DISABLED',
    `last_maintenance_date` DATE NULL COMMENT '上次保养日期',
    `next_maintenance_date` DATE NULL COMMENT '下次保养日期',
    `asset_no` VARCHAR(50) NULL COMMENT '固定资产编号',
    `remark` TEXT NULL COMMENT '备注',
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_equipment_code` (`equipment_code`),
    INDEX `idx_equipment_workshop` (`workshop_id`),
    INDEX `idx_equipment_status` (`status`),
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备表';

-- 设备保养维修记录表
CREATE TABLE IF NOT EXISTS `equipment_maintenance` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `equipment_id` INT NOT NULL COMMENT '设备ID',
    `maintenance_type` VARCHAR(20) NOT NULL COMMENT '类型:maintenance/repair',
    `maintenance_date` DATE NOT NULL COMMENT '保养/维修日期',
    `content` TEXT NULL COMMENT '保养/维修内容',
    `cost` DECIMAL(14,2) NULL COMMENT '费用',
    `performed_by` VARCHAR(50) NULL COMMENT '执行人',
    `next_maintenance_date` DATE NULL COMMENT '下次保养日期',
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_equip_maint_equipment` (`equipment_id`),
    INDEX `idx_equip_maint_date` (`maintenance_date`),
    FOREIGN KEY (`equipment_id`) REFERENCES `equipment`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备保养维修记录表';


-- ==================== 生产计划 ====================

-- 生产计划表
CREATE TABLE IF NOT EXISTS `production_plan` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `plan_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '计划编号',
    `plan_name` VARCHAR(200) NOT NULL COMMENT '计划名称',
    `plan_type` VARCHAR(20) NOT NULL DEFAULT 'MASTER' COMMENT '类型:MASTER(主计划)/WORKSHOP(车间计划)',
    `project_id` INT NULL COMMENT '关联项目ID',
    `workshop_id` INT NULL COMMENT '车间ID(车间计划用)',
    `plan_start_date` DATE NOT NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NOT NULL COMMENT '计划结束日期',
    `status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT' COMMENT '状态:DRAFT/SUBMITTED/APPROVED/PUBLISHED/EXECUTING/COMPLETED/CANCELLED',
    `progress` INT DEFAULT 0 COMMENT '进度(%)',
    `description` TEXT NULL COMMENT '计划说明',
    `created_by` INT NULL COMMENT '创建人ID',
    `approved_by` INT NULL COMMENT '审批人ID',
    `approved_at` DATETIME NULL COMMENT '审批时间',
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_prod_plan_no` (`plan_no`),
    INDEX `idx_prod_plan_project` (`project_id`),
    INDEX `idx_prod_plan_workshop` (`workshop_id`),
    INDEX `idx_prod_plan_status` (`status`),
    INDEX `idx_prod_plan_dates` (`plan_start_date`, `plan_end_date`),
    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`approved_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产计划表';


-- ==================== 生产工单 ====================

-- 生产工单表
CREATE TABLE IF NOT EXISTS `work_order` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `work_order_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '工单编号',
    `task_name` VARCHAR(200) NOT NULL COMMENT '任务名称',
    `task_type` VARCHAR(20) NOT NULL DEFAULT 'OTHER' COMMENT '类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/INSPECTION/OTHER',
    `project_id` INT NULL COMMENT '项目ID',
    `machine_id` INT NULL COMMENT '机台ID',
    `production_plan_id` INT NULL COMMENT '生产计划ID',
    `process_id` INT NULL COMMENT '工序ID',
    `workshop_id` INT NULL COMMENT '车间ID',
    `workstation_id` INT NULL COMMENT '工位ID',
    
    -- 物料相关
    `material_id` INT NULL COMMENT '物料ID',
    `material_name` VARCHAR(200) NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `drawing_no` VARCHAR(100) NULL COMMENT '图纸编号',
    
    -- 计划信息
    `plan_qty` INT DEFAULT 1 COMMENT '计划数量',
    `completed_qty` INT DEFAULT 0 COMMENT '完成数量',
    `qualified_qty` INT DEFAULT 0 COMMENT '合格数量',
    `defect_qty` INT DEFAULT 0 COMMENT '不良数量',
    `standard_hours` DECIMAL(10,2) NULL COMMENT '标准工时(小时)',
    `actual_hours` DECIMAL(10,2) DEFAULT 0 COMMENT '实际工时(小时)',
    
    -- 时间安排
    `plan_start_date` DATE NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NULL COMMENT '计划结束日期',
    `actual_start_time` DATETIME NULL COMMENT '实际开始时间',
    `actual_end_time` DATETIME NULL COMMENT '实际结束时间',
    
    -- 派工信息
    `assigned_to` INT NULL COMMENT '指派给(工人ID)',
    `assigned_at` DATETIME NULL COMMENT '派工时间',
    `assigned_by` INT NULL COMMENT '派工人ID',
    
    -- 状态信息
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态:PENDING/ASSIGNED/STARTED/PAUSED/COMPLETED/APPROVED/CANCELLED',
    `priority` VARCHAR(20) NOT NULL DEFAULT 'NORMAL' COMMENT '优先级:LOW/NORMAL/HIGH/URGENT',
    `progress` INT DEFAULT 0 COMMENT '进度(%)',
    
    -- 其他
    `work_content` TEXT NULL COMMENT '工作内容',
    `remark` TEXT NULL COMMENT '备注',
    `pause_reason` TEXT NULL COMMENT '暂停原因',
    `created_by` INT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_work_order_no` (`work_order_no`),
    INDEX `idx_work_order_project` (`project_id`),
    INDEX `idx_work_order_plan` (`production_plan_id`),
    INDEX `idx_work_order_workshop` (`workshop_id`),
    INDEX `idx_work_order_assigned` (`assigned_to`),
    INDEX `idx_work_order_status` (`status`),
    INDEX `idx_work_order_priority` (`priority`),
    INDEX `idx_work_order_dates` (`plan_start_date`, `plan_end_date`),
    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`machine_id`) REFERENCES `machine`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`production_plan_id`) REFERENCES `production_plan`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`process_id`) REFERENCES `process_dict`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`workstation_id`) REFERENCES `workstation`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`material_id`) REFERENCES `material`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`assigned_to`) REFERENCES `worker`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`assigned_by`) REFERENCES `user`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产工单表';


-- ==================== 报工管理 ====================

-- 报工记录表
CREATE TABLE IF NOT EXISTS `work_report` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `report_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '报工单号',
    `work_order_id` INT NOT NULL COMMENT '工单ID',
    `worker_id` INT NOT NULL COMMENT '工人ID',
    `report_type` VARCHAR(20) NOT NULL COMMENT '类型:START/PROGRESS/PAUSE/RESUME/COMPLETE',
    `report_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '报工时间',
    
    -- 进度信息
    `progress_percent` INT NULL COMMENT '进度百分比',
    `work_hours` DECIMAL(10,2) NULL COMMENT '本次工时(小时)',
    
    -- 完工信息
    `completed_qty` INT NULL COMMENT '完成数量',
    `qualified_qty` INT NULL COMMENT '合格数量',
    `defect_qty` INT NULL COMMENT '不良数量',
    
    -- 审核信息
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '状态:PENDING/APPROVED/REJECTED',
    `approved_by` INT NULL COMMENT '审核人ID',
    `approved_at` DATETIME NULL COMMENT '审核时间',
    `approve_comment` TEXT NULL COMMENT '审核意见',
    
    -- 其他
    `description` TEXT NULL COMMENT '工作描述',
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_work_report_no` (`report_no`),
    INDEX `idx_work_report_order` (`work_order_id`),
    INDEX `idx_work_report_worker` (`worker_id`),
    INDEX `idx_work_report_type` (`report_type`),
    INDEX `idx_work_report_status` (`status`),
    INDEX `idx_work_report_time` (`report_time`),
    FOREIGN KEY (`work_order_id`) REFERENCES `work_order`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`worker_id`) REFERENCES `worker`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`approved_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报工记录表';


-- ==================== 生产异常 ====================

-- 生产异常表
CREATE TABLE IF NOT EXISTS `production_exception` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `exception_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '异常编号',
    `exception_type` VARCHAR(20) NOT NULL COMMENT '类型:MATERIAL/EQUIPMENT/QUALITY/PROCESS/SAFETY/OTHER',
    `exception_level` VARCHAR(20) NOT NULL DEFAULT 'MINOR' COMMENT '级别:MINOR/MAJOR/CRITICAL',
    `title` VARCHAR(200) NOT NULL COMMENT '异常标题',
    `description` TEXT NULL COMMENT '异常描述',
    
    -- 关联信息
    `work_order_id` INT NULL COMMENT '关联工单ID',
    `project_id` INT NULL COMMENT '关联项目ID',
    `workshop_id` INT NULL COMMENT '车间ID',
    `equipment_id` INT NULL COMMENT '设备ID',
    
    -- 上报信息
    `reporter_id` INT NOT NULL COMMENT '上报人ID',
    `report_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上报时间',
    
    -- 处理信息
    `status` VARCHAR(20) NOT NULL DEFAULT 'REPORTED' COMMENT '状态:REPORTED/HANDLING/RESOLVED/CLOSED',
    `handler_id` INT NULL COMMENT '处理人ID',
    `handle_plan` TEXT NULL COMMENT '处理方案',
    `handle_result` TEXT NULL COMMENT '处理结果',
    `handle_time` DATETIME NULL COMMENT '处理时间',
    `resolved_at` DATETIME NULL COMMENT '解决时间',
    
    -- 影响评估
    `impact_hours` DECIMAL(10,2) NULL COMMENT '影响工时(小时)',
    `impact_cost` DECIMAL(14,2) NULL COMMENT '影响成本(元)',
    
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_prod_exc_no` (`exception_no`),
    INDEX `idx_prod_exc_type` (`exception_type`),
    INDEX `idx_prod_exc_level` (`exception_level`),
    INDEX `idx_prod_exc_status` (`status`),
    INDEX `idx_prod_exc_work_order` (`work_order_id`),
    INDEX `idx_prod_exc_project` (`project_id`),
    FOREIGN KEY (`work_order_id`) REFERENCES `work_order`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`equipment_id`) REFERENCES `equipment`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`reporter_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`handler_id`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产异常表';


-- ==================== 领料管理 ====================

-- 领料单表
CREATE TABLE IF NOT EXISTS `material_requisition` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `requisition_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '领料单号',
    `work_order_id` INT NULL COMMENT '关联工单ID',
    `project_id` INT NULL COMMENT '项目ID',
    
    -- 申请信息
    `applicant_id` INT NOT NULL COMMENT '申请人ID',
    `apply_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    `apply_reason` TEXT NULL COMMENT '申请原因',
    
    -- 审批信息
    `status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT' COMMENT '状态:DRAFT/SUBMITTED/APPROVED/REJECTED/ISSUED/COMPLETED/CANCELLED',
    `approved_by` INT NULL COMMENT '审批人ID',
    `approved_at` DATETIME NULL COMMENT '审批时间',
    `approve_comment` TEXT NULL COMMENT '审批意见',
    
    -- 发料信息
    `issued_by` INT NULL COMMENT '发料人ID',
    `issued_at` DATETIME NULL COMMENT '发料时间',
    
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_mat_req_no` (`requisition_no`),
    INDEX `idx_mat_req_work_order` (`work_order_id`),
    INDEX `idx_mat_req_project` (`project_id`),
    INDEX `idx_mat_req_status` (`status`),
    FOREIGN KEY (`work_order_id`) REFERENCES `work_order`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`project_id`) REFERENCES `project`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`applicant_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`approved_by`) REFERENCES `user`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`issued_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='领料单表';

-- 领料单明细表
CREATE TABLE IF NOT EXISTS `material_requisition_item` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `requisition_id` INT NOT NULL COMMENT '领料单ID',
    `material_id` INT NOT NULL COMMENT '物料ID',
    
    `request_qty` DECIMAL(14,4) NOT NULL COMMENT '申请数量',
    `approved_qty` DECIMAL(14,4) NULL COMMENT '批准数量',
    `issued_qty` DECIMAL(14,4) NULL COMMENT '发放数量',
    `unit` VARCHAR(20) NULL COMMENT '单位',
    
    `remark` TEXT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_mat_req_item_requisition` (`requisition_id`),
    INDEX `idx_mat_req_item_material` (`material_id`),
    FOREIGN KEY (`requisition_id`) REFERENCES `material_requisition`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`material_id`) REFERENCES `material`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='领料单明细表';


-- ==================== 生产日报 ====================

-- 生产日报表
CREATE TABLE IF NOT EXISTS `production_daily_report` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `report_date` DATE NOT NULL COMMENT '报告日期',
    `workshop_id` INT NULL COMMENT '车间ID(空表示全厂)',
    
    -- 生产统计
    `plan_qty` INT DEFAULT 0 COMMENT '计划数量',
    `completed_qty` INT DEFAULT 0 COMMENT '完成数量',
    `completion_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '完成率(%)',
    
    -- 工时统计
    `plan_hours` DECIMAL(10,2) DEFAULT 0 COMMENT '计划工时',
    `actual_hours` DECIMAL(10,2) DEFAULT 0 COMMENT '实际工时',
    `overtime_hours` DECIMAL(10,2) DEFAULT 0 COMMENT '加班工时',
    `efficiency` DECIMAL(5,2) DEFAULT 0 COMMENT '效率(%)',
    
    -- 出勤统计
    `should_attend` INT DEFAULT 0 COMMENT '应出勤人数',
    `actual_attend` INT DEFAULT 0 COMMENT '实际出勤',
    `leave_count` INT DEFAULT 0 COMMENT '请假人数',
    
    -- 质量统计
    `total_qty` INT DEFAULT 0 COMMENT '生产总数',
    `qualified_qty` INT DEFAULT 0 COMMENT '合格数量',
    `pass_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '合格率(%)',
    
    -- 异常统计
    `new_exception_count` INT DEFAULT 0 COMMENT '新增异常数',
    `resolved_exception_count` INT DEFAULT 0 COMMENT '解决异常数',
    
    `summary` TEXT NULL COMMENT '日报总结',
    `created_by` INT NULL COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX `idx_prod_daily_date` (`report_date`),
    INDEX `idx_prod_daily_workshop` (`workshop_id`),
    UNIQUE KEY `uk_prod_daily_date_workshop` (`report_date`, `workshop_id`),
    FOREIGN KEY (`workshop_id`) REFERENCES `workshop`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产日报表';


-- ==================== 初始化数据 ====================

-- 初始化车间
INSERT IGNORE INTO `workshop` (`workshop_code`, `workshop_name`, `workshop_type`, `capacity_hours`, `is_active`) VALUES
('WS-MACH', '机加车间', 'MACHINING', 120, 1),
('WS-ASSY', '装配车间', 'ASSEMBLY', 160, 1),
('WS-DBUG', '调试车间', 'DEBUGGING', 80, 1),
('WS-WELD', '焊接车间', 'WELDING', 60, 1);

-- 初始化工序字典
INSERT IGNORE INTO `process_dict` (`process_code`, `process_name`, `process_type`, `standard_hours`, `is_active`) VALUES
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

