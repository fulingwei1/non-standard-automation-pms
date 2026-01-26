-- =============================================
-- 项目进度管理模块 DDL脚本
-- 数据库：MySQL 8.0+
-- 创建日期：2025-01
-- =============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 1. 项目主表
-- ----------------------------
DROP TABLE IF EXISTS `project`;
CREATE TABLE `project` (
    `project_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `project_name` VARCHAR(200) NOT NULL COMMENT '项目名称',
    `project_type` VARCHAR(20) NOT NULL DEFAULT '订单' COMMENT '项目类型：订单/研发/改造/维保',
    `project_level` VARCHAR(10) NOT NULL DEFAULT 'B' COMMENT '项目等级：A/B/C/D',
    `contract_id` BIGINT NULL COMMENT '关联合同ID',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `pm_id` BIGINT NOT NULL COMMENT '项目经理ID',
    `pm_name` VARCHAR(50) NOT NULL COMMENT '项目经理姓名',
    `te_id` BIGINT NULL COMMENT '技术经理ID',
    `te_name` VARCHAR(50) NULL COMMENT '技术经理姓名',
    `sc_id` BIGINT NULL COMMENT '供应链经理ID',
    `sc_name` VARCHAR(50) NULL COMMENT '供应链经理姓名',
    `plan_start_date` DATE NOT NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NOT NULL COMMENT '计划结束日期',
    `baseline_start_date` DATE NULL COMMENT '基线开始日期',
    `baseline_end_date` DATE NULL COMMENT '基线结束日期',
    `actual_start_date` DATE NULL COMMENT '实际开始日期',
    `actual_end_date` DATE NULL COMMENT '实际结束日期',
    `plan_duration` INT NOT NULL DEFAULT 0 COMMENT '计划工期（工作日）',
    `progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '进度完成率%',
    `plan_progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '计划进度率%',
    `spi` DECIMAL(5,2) NOT NULL DEFAULT 1.00 COMMENT 'SPI进度绩效指数',
    `plan_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '计划总工时',
    `actual_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '已消耗工时',
    `current_phase` VARCHAR(30) NOT NULL DEFAULT '立项启动' COMMENT '当前阶段',
    `status` VARCHAR(20) NOT NULL DEFAULT '未启动' COMMENT '项目状态',
    `health_status` VARCHAR(10) NOT NULL DEFAULT '绿' COMMENT '健康状态：绿/黄/红',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_by` BIGINT NULL COMMENT '更新人ID',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`project_id`),
    UNIQUE KEY `uk_project_code` (`project_code`),
    KEY `idx_project_customer` (`customer_id`),
    KEY `idx_project_pm` (`pm_id`),
    KEY `idx_project_status` (`status`),
    KEY `idx_project_date` (`plan_start_date`, `plan_end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目主表';

-- ----------------------------
-- 2. WBS任务表
-- ----------------------------
DROP TABLE IF EXISTS `wbs_task`;
CREATE TABLE `wbs_task` (
    `task_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `wbs_code` VARCHAR(20) NOT NULL COMMENT 'WBS编码',
    `task_name` VARCHAR(200) NOT NULL COMMENT '任务名称',
    `parent_id` BIGINT NULL COMMENT '父任务ID',
    `level` TINYINT NOT NULL DEFAULT 1 COMMENT '层级：1阶段/2任务/3子任务',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '同级排序号',
    `path` VARCHAR(200) NULL COMMENT '层级路径',
    `phase` VARCHAR(30) NOT NULL COMMENT '所属阶段',
    `task_type` VARCHAR(30) NOT NULL COMMENT '任务类型',
    `plan_start_date` DATE NOT NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NOT NULL COMMENT '计划结束日期',
    `baseline_start_date` DATE NULL COMMENT '基线开始日期',
    `baseline_end_date` DATE NULL COMMENT '基线结束日期',
    `actual_start_date` DATE NULL COMMENT '实际开始日期',
    `actual_end_date` DATE NULL COMMENT '实际结束日期',
    `plan_duration` INT NOT NULL DEFAULT 1 COMMENT '计划工期（工作日）',
    `plan_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '计划工时',
    `actual_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '实际工时',
    `progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '进度完成率%',
    `progress_method` VARCHAR(20) NOT NULL DEFAULT '工时法' COMMENT '进度计算方式',
    `weight` DECIMAL(5,2) NOT NULL DEFAULT 1.00 COMMENT '权重',
    `owner_id` BIGINT NULL COMMENT '主负责人ID',
    `owner_name` VARCHAR(50) NULL COMMENT '主负责人姓名',
    `owner_dept_id` BIGINT NULL COMMENT '负责部门ID',
    `owner_dept_name` VARCHAR(50) NULL COMMENT '负责部门',
    `is_critical` TINYINT NOT NULL DEFAULT 0 COMMENT '是否关键路径',
    `is_milestone` TINYINT NOT NULL DEFAULT 0 COMMENT '是否里程碑',
    `float_days` INT DEFAULT 0 COMMENT '浮动时间（天）',
    `earliest_start` DATE NULL COMMENT '最早开始时间',
    `latest_finish` DATE NULL COMMENT '最迟完成时间',
    `status` VARCHAR(20) NOT NULL DEFAULT '未开始' COMMENT '状态',
    `block_reason` VARCHAR(200) NULL COMMENT '阻塞原因',
    `block_type` VARCHAR(30) NULL COMMENT '阻塞类型',
    `deliverable` VARCHAR(500) NULL COMMENT '交付物说明',
    `priority` TINYINT NOT NULL DEFAULT 3 COMMENT '优先级：1-5',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`task_id`),
    KEY `idx_task_project` (`project_id`),
    KEY `idx_task_parent` (`parent_id`),
    KEY `idx_task_owner` (`owner_id`),
    KEY `idx_task_status` (`status`),
    KEY `idx_task_date` (`plan_start_date`, `plan_end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='WBS任务表';

-- ----------------------------
-- 3. 任务分配表
-- ----------------------------
DROP TABLE IF EXISTS `task_assignment`;
CREATE TABLE `task_assignment` (
    `assign_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '分配ID',
    `task_id` BIGINT NOT NULL COMMENT '任务ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `user_id` BIGINT NOT NULL COMMENT '工程师ID',
    `user_name` VARCHAR(50) NOT NULL COMMENT '工程师姓名',
    `dept_id` BIGINT NOT NULL COMMENT '部门ID',
    `dept_name` VARCHAR(50) NOT NULL COMMENT '部门名称',
    `role` VARCHAR(20) NOT NULL DEFAULT '参与人' COMMENT '角色：负责人/参与人',
    `plan_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '计划工时',
    `actual_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '实际工时',
    `remaining_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '剩余工时',
    `plan_start_date` DATE NOT NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NOT NULL COMMENT '计划结束日期',
    `actual_start_date` DATE NULL COMMENT '实际开始日期',
    `actual_end_date` DATE NULL COMMENT '实际结束日期',
    `progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '个人进度%',
    `status` VARCHAR(20) NOT NULL DEFAULT '未开始' COMMENT '状态',
    `assigned_by` BIGINT NOT NULL COMMENT '分配人ID',
    `assigned_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    `priority` TINYINT NOT NULL DEFAULT 3 COMMENT '优先级',
    PRIMARY KEY (`assign_id`),
    KEY `idx_assign_task` (`task_id`),
    KEY `idx_assign_user` (`user_id`),
    KEY `idx_assign_project` (`project_id`),
    UNIQUE KEY `uk_task_user` (`task_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务分配表';

-- ----------------------------
-- 4. 任务依赖表
-- ----------------------------
DROP TABLE IF EXISTS `task_dependency`;
CREATE TABLE `task_dependency` (
    `depend_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '依赖ID',
    `task_id` BIGINT NOT NULL COMMENT '任务ID（后置任务）',
    `predecessor_id` BIGINT NOT NULL COMMENT '前置任务ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `depend_type` VARCHAR(10) NOT NULL DEFAULT 'FS' COMMENT '依赖类型：FS/SS/FF/SF',
    `lag_days` INT NOT NULL DEFAULT 0 COMMENT '延迟天数',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`depend_id`),
    KEY `idx_depend_task` (`task_id`),
    KEY `idx_depend_pred` (`predecessor_id`),
    UNIQUE KEY `uk_task_pred` (`task_id`, `predecessor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务依赖表';

-- ----------------------------
-- 5. 工时记录表
-- ----------------------------
DROP TABLE IF EXISTS `timesheet`;
CREATE TABLE `timesheet` (
    `timesheet_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '工时ID',
    `user_id` BIGINT NOT NULL COMMENT '工程师ID',
    `user_name` VARCHAR(50) NOT NULL COMMENT '工程师姓名',
    `dept_id` BIGINT NOT NULL COMMENT '部门ID',
    `work_date` DATE NOT NULL COMMENT '工作日期',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `task_id` BIGINT NOT NULL COMMENT '任务ID',
    `assign_id` BIGINT NULL COMMENT '分配ID',
    `hours` DECIMAL(4,1) NOT NULL DEFAULT 0 COMMENT '工时数',
    `overtime_hours` DECIMAL(4,1) NOT NULL DEFAULT 0 COMMENT '加班工时',
    `work_content` VARCHAR(500) NULL COMMENT '工作内容描述',
    `status` VARCHAR(20) NOT NULL DEFAULT '待审核' COMMENT '状态',
    `approved_by` BIGINT NULL COMMENT '审核人ID',
    `approved_time` DATETIME NULL COMMENT '审核时间',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`timesheet_id`),
    KEY `idx_ts_user_date` (`user_id`, `work_date`),
    KEY `idx_ts_task` (`task_id`),
    KEY `idx_ts_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工时记录表';

-- ----------------------------
-- 6. 任务日志表
-- ----------------------------
DROP TABLE IF EXISTS `task_log`;
CREATE TABLE `task_log` (
    `log_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `task_id` BIGINT NOT NULL COMMENT '任务ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `action` VARCHAR(50) NOT NULL COMMENT '操作类型',
    `field_name` VARCHAR(50) NULL COMMENT '变更字段名',
    `old_value` VARCHAR(500) NULL COMMENT '旧值',
    `new_value` VARCHAR(500) NULL COMMENT '新值',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `operator_id` BIGINT NOT NULL COMMENT '操作人ID',
    `operator_name` VARCHAR(50) NOT NULL COMMENT '操作人姓名',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (`log_id`),
    KEY `idx_log_task` (`task_id`),
    KEY `idx_log_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务日志表';

-- ----------------------------
-- 7. 进度预警表
-- ----------------------------
DROP TABLE IF EXISTS `progress_alert`;
CREATE TABLE `progress_alert` (
    `alert_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '预警ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `task_id` BIGINT NULL COMMENT '任务ID',
    `alert_type` VARCHAR(50) NOT NULL COMMENT '预警类型',
    `alert_level` VARCHAR(10) NOT NULL COMMENT '预警级别：红/橙/黄',
    `alert_title` VARCHAR(200) NOT NULL COMMENT '预警标题',
    `alert_content` TEXT NULL COMMENT '预警内容',
    `trigger_value` VARCHAR(100) NULL COMMENT '触发值',
    `threshold_value` VARCHAR(100) NULL COMMENT '阈值',
    `notify_users` VARCHAR(500) NULL COMMENT '通知人员ID列表',
    `status` VARCHAR(20) NOT NULL DEFAULT '待处理' COMMENT '状态：待处理/处理中/已关闭',
    `handle_user_id` BIGINT NULL COMMENT '处理人ID',
    `handle_time` DATETIME NULL COMMENT '处理时间',
    `handle_remark` VARCHAR(500) NULL COMMENT '处理备注',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`alert_id`),
    KEY `idx_alert_project` (`project_id`),
    KEY `idx_alert_status` (`status`),
    KEY `idx_alert_time` (`created_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='进度预警表';

-- ----------------------------
-- 8. 工程师负荷快照表
-- ----------------------------
DROP TABLE IF EXISTS `workload_snapshot`;
CREATE TABLE `workload_snapshot` (
    `snapshot_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '快照ID',
    `user_id` BIGINT NOT NULL COMMENT '工程师ID',
    `user_name` VARCHAR(50) NOT NULL COMMENT '工程师姓名',
    `dept_id` BIGINT NOT NULL COMMENT '部门ID',
    `snapshot_date` DATE NOT NULL COMMENT '快照日期',
    `period_type` VARCHAR(10) NOT NULL DEFAULT '日' COMMENT '周期类型：日/周',
    `available_hours` DECIMAL(10,2) NOT NULL DEFAULT 8 COMMENT '可用工时',
    `allocated_hours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '已分配工时',
    `actual_hours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '实际工时',
    `allocation_rate` DECIMAL(5,2) NOT NULL DEFAULT 0 COMMENT '分配负荷率%',
    `task_count` INT NOT NULL DEFAULT 0 COMMENT '任务数量',
    `project_count` INT NOT NULL DEFAULT 0 COMMENT '参与项目数',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`snapshot_id`),
    UNIQUE KEY `uk_user_date` (`user_id`, `snapshot_date`, `period_type`),
    KEY `idx_snapshot_date` (`snapshot_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工程师负荷快照表';

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- 初始化数据
-- =============================================

-- 插入示例项目
INSERT INTO `project` (
    `project_code`, `project_name`, `project_type`, `project_level`,
    `customer_id`, `customer_name`, `pm_id`, `pm_name`,
    `plan_start_date`, `plan_end_date`, `plan_duration`,
    `status`, `created_by`
) VALUES (
    'PRJ-2025-001', '某客户自动化测试设备项目', '订单', 'A',
    1, '某大客户', 1, '项目经理张三',
    '2025-01-06', '2025-04-30', 80,
    '进行中', 1
);

-- 插入示例WBS任务
INSERT INTO `wbs_task` (
    `project_id`, `wbs_code`, `task_name`, `level`, `sort_order`,
    `phase`, `task_type`, `plan_start_date`, `plan_end_date`,
    `plan_duration`, `weight`, `created_by`
) VALUES 
(1, '1', '立项启动', 1, 1, '立项启动', '阶段', '2025-01-06', '2025-01-10', 5, 5.00, 1),
(1, '2', '方案设计', 1, 2, '方案设计', '阶段', '2025-01-13', '2025-01-31', 15, 15.00, 1),
(1, '3', '结构设计', 1, 3, '结构设计', '阶段', '2025-02-01', '2025-02-28', 20, 20.00, 1),
(1, '4', '电气设计', 1, 4, '电气设计', '阶段', '2025-02-01', '2025-02-28', 20, 15.00, 1),
(1, '5', '采购制造', 1, 5, '采购制造', '阶段', '2025-03-01', '2025-03-21', 15, 20.00, 1),
(1, '6', '装配调试', 1, 6, '装配调试', '阶段', '2025-03-24', '2025-04-18', 20, 20.00, 1),
(1, '7', '验收交付', 1, 7, '验收交付', '阶段', '2025-04-21', '2025-04-30', 8, 5.00, 1);
