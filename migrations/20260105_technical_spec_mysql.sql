-- ============================================
-- 技术规格管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 技术规格要求表、规格匹配记录表
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 技术规格要求表
-- ============================================

CREATE TABLE IF NOT EXISTS `technical_spec_requirements` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `document_id`         INT UNSIGNED DEFAULT NULL COMMENT '关联技术规格书文档',

    -- 物料信息
    `material_code`       VARCHAR(50) DEFAULT NULL COMMENT '物料编码（可选）',
    `material_name`       VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification`       VARCHAR(500) NOT NULL COMMENT '规格型号要求',
    `brand`               VARCHAR(100) DEFAULT NULL COMMENT '品牌要求',
    `model`               VARCHAR(100) DEFAULT NULL COMMENT '型号要求',

    -- 关键参数（JSON格式，用于智能匹配）
    `key_parameters`      JSON DEFAULT NULL COMMENT '关键参数：电压、电流、精度、温度范围等',

    -- 要求级别
    `requirement_level`   VARCHAR(20) DEFAULT 'REQUIRED' COMMENT '要求级别：REQUIRED/OPTIONAL/STRICT',

    -- 备注
    `remark`              TEXT DEFAULT NULL COMMENT '备注说明',
    `extracted_by`        INT UNSIGNED DEFAULT NULL COMMENT '提取人',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    KEY `idx_spec_req_project` (`project_id`),
    KEY `idx_spec_req_document` (`document_id`),
    KEY `idx_spec_req_material` (`material_code`),
    CONSTRAINT `fk_spec_req_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_spec_req_document` FOREIGN KEY (`document_id`) REFERENCES `project_documents` (`id`),
    CONSTRAINT `fk_spec_req_extracted_by` FOREIGN KEY (`extracted_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技术规格要求表';

-- ============================================
-- 2. 规格匹配记录表
-- ============================================

CREATE TABLE IF NOT EXISTS `spec_match_records` (
    `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `project_id`          INT UNSIGNED NOT NULL COMMENT '项目ID',
    `spec_requirement_id` INT UNSIGNED DEFAULT NULL COMMENT '规格要求ID',

    -- 匹配对象
    `match_type`          VARCHAR(20) NOT NULL COMMENT '匹配类型：BOM/PURCHASE_ORDER',
    `match_target_id`     INT UNSIGNED NOT NULL COMMENT '匹配对象ID（BOM行ID或采购订单行ID）',

    -- 匹配结果
    `match_status`        VARCHAR(20) NOT NULL COMMENT '匹配状态：MATCHED/MISMATCHED/UNKNOWN',
    `match_score`         DECIMAL(5,2) DEFAULT NULL COMMENT '匹配度（0-100）',

    -- 差异详情（JSON）
    `differences`         JSON DEFAULT NULL COMMENT '差异详情',

    -- 预警
    `alert_id`           BIGINT UNSIGNED DEFAULT NULL COMMENT '关联预警ID',

    `created_at`          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    KEY `idx_match_record_project` (`project_id`),
    KEY `idx_match_record_spec` (`spec_requirement_id`),
    KEY `idx_match_record_type` (`match_type`, `match_target_id`),
    KEY `idx_match_record_status` (`match_status`),
    KEY `idx_match_record_alert` (`alert_id`),
    CONSTRAINT `fk_match_record_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
    CONSTRAINT `fk_match_record_spec` FOREIGN KEY (`spec_requirement_id`) REFERENCES `technical_spec_requirements` (`id`),
    CONSTRAINT `fk_match_record_alert` FOREIGN KEY (`alert_id`) REFERENCES `alert_records` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='规格匹配记录表';

SET FOREIGN_KEY_CHECKS = 1;




