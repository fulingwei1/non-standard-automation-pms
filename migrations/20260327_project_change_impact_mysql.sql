-- ============================================================
-- 项目-变更单联动集成：project_change_impacts 表
-- 支持数据库：MySQL
-- 日期：2026-03-27
-- ============================================================

CREATE TABLE IF NOT EXISTS `project_change_impacts` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,

    -- 双向关联
    `ecn_id` INT NOT NULL COMMENT 'ECN ID',
    `ecn_no` VARCHAR(50) NOT NULL COMMENT 'ECN编号',
    `project_id` INT NOT NULL COMMENT '项目ID',
    `machine_id` INT DEFAULT NULL COMMENT '设备ID',

    -- 评估阶段：项目状态快照
    `project_stage_snapshot` VARCHAR(20) DEFAULT NULL COMMENT '评估时项目阶段',
    `project_progress_snapshot` DECIMAL(5,2) DEFAULT NULL COMMENT '评估时项目进度(%)',

    -- 进度影响
    `schedule_impact_days` INT DEFAULT 0 COMMENT '预计延期天数',
    `affected_milestones` JSON DEFAULT NULL COMMENT '受影响的里程碑列表',

    -- 成本影响
    `rework_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '返工成本',
    `scrap_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '报废成本',
    `additional_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '新增成本',
    `total_cost_impact` DECIMAL(14,2) DEFAULT 0 COMMENT '总成本影响',
    `cost_breakdown` JSON DEFAULT NULL COMMENT '成本明细',

    -- 风险评估
    `risk_level` VARCHAR(20) DEFAULT 'LOW' COMMENT '风险等级',
    `risk_description` TEXT DEFAULT NULL COMMENT '风险描述',

    -- 综合影响报告
    `impact_summary` TEXT DEFAULT NULL COMMENT '影响摘要',
    `impact_report` JSON DEFAULT NULL COMMENT '完整影响报告',

    `assessed_by` INT DEFAULT NULL COMMENT '评估人',
    `assessed_at` DATETIME DEFAULT NULL COMMENT '评估时间',

    -- 执行阶段
    `milestones_updated` TINYINT(1) DEFAULT 0 COMMENT '里程碑是否已更新',
    `milestone_update_detail` JSON DEFAULT NULL COMMENT '里程碑更新明细',

    `costs_recorded` TINYINT(1) DEFAULT 0 COMMENT '成本是否已记录',
    `cost_record_ids` JSON DEFAULT NULL COMMENT '关联的项目成本记录ID',

    `risk_created` TINYINT(1) DEFAULT 0 COMMENT '风险记录是否已创建',
    `risk_record_id` INT DEFAULT NULL COMMENT '关联的风险记录ID',

    `actual_delay_days` INT DEFAULT NULL COMMENT '实际延期天数',
    `actual_cost_impact` DECIMAL(14,2) DEFAULT NULL COMMENT '实际成本影响',

    -- 状态
    `status` VARCHAR(20) DEFAULT 'ASSESSED' COMMENT '状态',

    `executed_by` INT DEFAULT NULL COMMENT '执行人',
    `executed_at` DATETIME DEFAULT NULL COMMENT '执行完成时间',

    `remark` TEXT DEFAULT NULL COMMENT '备注',

    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键
    CONSTRAINT `fk_pci_ecn` FOREIGN KEY (`ecn_id`) REFERENCES `ecn`(`id`),
    CONSTRAINT `fk_pci_project` FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`),
    CONSTRAINT `fk_pci_machine` FOREIGN KEY (`machine_id`) REFERENCES `machines`(`id`),
    CONSTRAINT `fk_pci_assessed_by` FOREIGN KEY (`assessed_by`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_pci_executed_by` FOREIGN KEY (`executed_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目变更影响记录表';

-- 索引
CREATE INDEX `idx_pci_ecn` ON `project_change_impacts`(`ecn_id`);
CREATE INDEX `idx_pci_project` ON `project_change_impacts`(`project_id`);
CREATE INDEX `idx_pci_ecn_project` ON `project_change_impacts`(`ecn_id`, `project_id`);
CREATE INDEX `idx_pci_status` ON `project_change_impacts`(`status`);
CREATE INDEX `idx_pci_risk_level` ON `project_change_impacts`(`risk_level`);
