-- ============================================
-- 项目评价模块 - MySQL 迁移
-- 创建日期: 2026-01-18
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 项目评价记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_evaluations` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `evaluation_code` VARCHAR(50) NOT NULL COMMENT '评价编号',
    `project_id` INT UNSIGNED NOT NULL COMMENT '项目ID',
    `novelty_score` DECIMAL(3, 1) COMMENT '项目新旧得分（1-10分）',
    `new_tech_score` DECIMAL(3, 1) COMMENT '新技术得分（1-10分）',
    `difficulty_score` DECIMAL(3, 1) COMMENT '项目难度得分（1-10分）',
    `workload_score` DECIMAL(3, 1) COMMENT '项目工作量得分（1-10分）',
    `amount_score` DECIMAL(3, 1) COMMENT '项目金额得分（1-10分）',
    `total_score` DECIMAL(5, 2) COMMENT '综合得分',
    `evaluation_level` VARCHAR(20) COMMENT '评价等级：S/A/B/C/D',
    `evaluation_detail` JSON COMMENT '评价详情(JSON)',
    `weights` JSON COMMENT '权重配置(JSON)',
    `evaluator_id` INT UNSIGNED NOT NULL COMMENT '评价人ID',
    `evaluator_name` VARCHAR(50) COMMENT '评价人姓名',
    `evaluation_date` DATE NOT NULL COMMENT '评价日期',
    `evaluation_note` TEXT COMMENT '评价说明',
    `status` VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_eval_code` (`evaluation_code`),
    KEY `idx_proj_eval_project` (`project_id`),
    KEY `idx_proj_eval_date` (`evaluation_date`),
    KEY `idx_proj_eval_level` (`evaluation_level`),
    CONSTRAINT `fk_proj_eval_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_proj_eval_evaluator` FOREIGN KEY (`evaluator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目评价记录表';

-- ============================================
-- 2. 项目评价维度配置表
-- ============================================

CREATE TABLE IF NOT EXISTS `project_evaluation_dimensions` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `dimension_code` VARCHAR(50) NOT NULL COMMENT '维度编码',
    `dimension_name` VARCHAR(100) NOT NULL COMMENT '维度名称',
    `dimension_type` VARCHAR(20) NOT NULL COMMENT '维度类型',
    `scoring_rules` JSON COMMENT '评分规则(JSON)',
    `default_weight` DECIMAL(5, 2) COMMENT '默认权重(%)',
    `calculation_method` VARCHAR(20) DEFAULT 'MANUAL' COMMENT '计算方式',
    `auto_calculation_rule` JSON COMMENT '自动计算规则(JSON)',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `sort_order` INT DEFAULT 0 COMMENT '排序',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_dim_code` (`dimension_code`),
    KEY `idx_eval_dim_type` (`dimension_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目评价维度配置表';

-- ============================================
-- 3. 初始化评价维度配置
-- ============================================

INSERT INTO `project_evaluation_dimensions` (`dimension_code`, `dimension_name`, `dimension_type`, `default_weight`, `calculation_method`, `scoring_rules`, `sort_order`) VALUES
('NOVELTY', '项目新旧', 'NOVELTY', 15.00, 'HYBRID', '{"ranges": [{"min": 1, "max": 3, "label": "全新项目", "description": "从未做过类似项目"}, {"min": 4, "max": 6, "label": "类似项目", "description": "做过类似项目"}, {"min": 7, "max": 9, "label": "标准项目", "description": "做过多次"}, {"min": 10, "max": 10, "label": "完全标准", "description": "完全标准项目"}]}', 1),
('NEW_TECH', '新技术', 'NEW_TECH', 20.00, 'MANUAL', '{"ranges": [{"min": 1, "max": 3, "label": "大量新技术", "description": "技术风险高"}, {"min": 4, "max": 6, "label": "部分新技术", "description": "有一定风险"}, {"min": 7, "max": 9, "label": "少量新技术", "description": "风险可控"}, {"min": 10, "max": 10, "label": "无新技术", "description": "成熟技术"}]}', 2),
('DIFFICULTY', '项目难度', 'DIFFICULTY', 30.00, 'MANUAL', '{"ranges": [{"min": 1, "max": 3, "label": "极高难度", "description": "技术挑战极大"}, {"min": 4, "max": 6, "label": "高难度", "description": "技术挑战大"}, {"min": 7, "max": 8, "label": "中等难度", "description": "技术挑战一般"}, {"min": 9, "max": 10, "label": "低难度", "description": "技术挑战小"}]}', 3),
('WORKLOAD', '项目工作量', 'WORKLOAD', 20.00, 'MANUAL', '{"ranges": [{"min": 1, "max": 3, "label": "工作量极大", "description": ">1000人天"}, {"min": 4, "max": 6, "label": "工作量大", "description": "500-1000人天"}, {"min": 7, "max": 8, "label": "工作量中等", "description": "200-500人天"}, {"min": 9, "max": 10, "label": "工作量小", "description": "<200人天"}]}', 4),
('AMOUNT', '项目金额', 'AMOUNT', 15.00, 'AUTO', '{"ranges": [{"min": 1, "max": 3, "label": "超大项目", "description": ">500万"}, {"min": 4, "max": 6, "label": "大项目", "description": "200-500万"}, {"min": 7, "max": 8, "label": "中等项目", "description": "50-200万"}, {"min": 9, "max": 10, "label": "小项目", "description": "<50万"}]}', 5);

SET FOREIGN_KEY_CHECKS = 1;






