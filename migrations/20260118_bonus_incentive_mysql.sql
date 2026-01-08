-- ============================================
-- 奖金激励体系模块 - MySQL 迁移
-- 创建日期: 2026-01-18
-- ============================================

-- ============================================
-- 1. 奖金规则表
-- ============================================

CREATE TABLE IF NOT EXISTS `bonus_rules` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `rule_code` VARCHAR(50) NOT NULL COMMENT '规则编码',
    `rule_name` VARCHAR(200) NOT NULL COMMENT '规则名称',
    `bonus_type` VARCHAR(20) NOT NULL COMMENT '奖金类型',
    `calculation_formula` TEXT COMMENT '计算公式说明',
    `base_amount` DECIMAL(14, 2) COMMENT '基础金额',
    `coefficient` DECIMAL(5, 2) COMMENT '系数',
    `trigger_condition` JSON COMMENT '触发条件(JSON)',
    `apply_to_roles` JSON COMMENT '适用角色列表(JSON)',
    `apply_to_depts` JSON COMMENT '适用部门列表(JSON)',
    `apply_to_projects` JSON COMMENT '适用项目类型列表(JSON)',
    `effective_start_date` DATE COMMENT '生效开始日期',
    `effective_end_date` DATE COMMENT '生效结束日期',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `require_approval` TINYINT(1) DEFAULT 1 COMMENT '是否需要审批',
    `approval_workflow` JSON COMMENT '审批流程(JSON)',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_rule_code` (`rule_code`),
    KEY `idx_bonus_rule_type` (`bonus_type`),
    KEY `idx_bonus_rule_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='奖金规则表';

-- ============================================
-- 2. 奖金计算记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `bonus_calculations` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `calculation_code` VARCHAR(50) NOT NULL COMMENT '计算单号',
    `rule_id` INT UNSIGNED NOT NULL COMMENT '规则ID',
    `period_id` INT UNSIGNED COMMENT '考核周期ID（绩效奖金）',
    `project_id` INT UNSIGNED COMMENT '项目ID（项目奖金）',
    `milestone_id` INT UNSIGNED COMMENT '里程碑ID（里程碑奖金）',
    `user_id` INT UNSIGNED NOT NULL COMMENT '受益人ID',
    `performance_result_id` INT UNSIGNED COMMENT '绩效结果ID',
    `project_contribution_id` INT UNSIGNED COMMENT '项目贡献ID',
    `calculation_basis` JSON COMMENT '计算依据详情(JSON)',
    `calculated_amount` DECIMAL(14, 2) NOT NULL COMMENT '计算金额',
    `calculation_detail` JSON COMMENT '计算明细(JSON)',
    `status` VARCHAR(20) DEFAULT 'CALCULATED' COMMENT '状态',
    `approved_by` INT UNSIGNED COMMENT '审批人',
    `approved_at` DATETIME COMMENT '审批时间',
    `approval_comment` TEXT COMMENT '审批意见',
    `calculated_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '计算时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_calculation_code` (`calculation_code`),
    KEY `idx_bonus_calc_rule` (`rule_id`),
    KEY `idx_bonus_calc_user` (`user_id`),
    KEY `idx_bonus_calc_project` (`project_id`),
    KEY `idx_bonus_calc_period` (`period_id`),
    KEY `idx_bonus_calc_status` (`status`),
    CONSTRAINT `fk_bonus_calc_rule` FOREIGN KEY (`rule_id`) REFERENCES `bonus_rules` (`id`),
    CONSTRAINT `fk_bonus_calc_period` FOREIGN KEY (`period_id`) REFERENCES `performance_period` (`id`),
    CONSTRAINT `fk_bonus_calc_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_bonus_calc_milestone` FOREIGN KEY (`milestone_id`) REFERENCES `project_milestones` (`id`),
    CONSTRAINT `fk_bonus_calc_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_bonus_calc_perf_result` FOREIGN KEY (`performance_result_id`) REFERENCES `performance_result` (`id`),
    CONSTRAINT `fk_bonus_calc_contrib` FOREIGN KEY (`project_contribution_id`) REFERENCES `project_contribution` (`id`),
    CONSTRAINT `fk_bonus_calc_approver` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='奖金计算记录表';

-- ============================================
-- 3. 奖金发放记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `bonus_distributions` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `distribution_code` VARCHAR(50) NOT NULL COMMENT '发放单号',
    `calculation_id` INT UNSIGNED NOT NULL COMMENT '计算记录ID',
    `user_id` INT UNSIGNED NOT NULL COMMENT '受益人ID',
    `distributed_amount` DECIMAL(14, 2) NOT NULL COMMENT '发放金额',
    `distribution_date` DATE NOT NULL COMMENT '发放日期',
    `payment_method` VARCHAR(20) COMMENT '发放方式',
    `status` VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',
    `voucher_no` VARCHAR(50) COMMENT '凭证号',
    `payment_account` VARCHAR(100) COMMENT '付款账户',
    `payment_remark` TEXT COMMENT '付款备注',
    `paid_by` INT UNSIGNED COMMENT '发放人',
    `paid_at` DATETIME COMMENT '发放时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_distribution_code` (`distribution_code`),
    KEY `idx_bonus_dist_calc` (`calculation_id`),
    KEY `idx_bonus_dist_user` (`user_id`),
    KEY `idx_bonus_dist_status` (`status`),
    KEY `idx_bonus_dist_date` (`distribution_date`),
    CONSTRAINT `fk_bonus_dist_calc` FOREIGN KEY (`calculation_id`) REFERENCES `bonus_calculations` (`id`),
    CONSTRAINT `fk_bonus_dist_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_bonus_dist_payer` FOREIGN KEY (`paid_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='奖金发放记录表';

-- ============================================
-- 4. 团队奖金分配表
-- ============================================

CREATE TABLE IF NOT EXISTS `team_bonus_allocations` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id` INT UNSIGNED NOT NULL COMMENT '项目ID',
    `period_id` INT UNSIGNED COMMENT '周期ID',
    `total_bonus_amount` DECIMAL(14, 2) NOT NULL COMMENT '团队总奖金',
    `allocation_method` VARCHAR(20) COMMENT '分配方式',
    `allocation_detail` JSON COMMENT '分配明细(JSON)',
    `status` VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态',
    `approved_by` INT UNSIGNED COMMENT '审批人',
    `approved_at` DATETIME COMMENT '审批时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_team_bonus_project` (`project_id`),
    KEY `idx_team_bonus_period` (`period_id`),
    KEY `idx_team_bonus_status` (`status`),
    CONSTRAINT `fk_team_bonus_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_team_bonus_period` FOREIGN KEY (`period_id`) REFERENCES `performance_period` (`id`),
    CONSTRAINT `fk_team_bonus_approver` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='团队奖金分配表';






