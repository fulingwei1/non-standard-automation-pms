BEGIN;

CREATE TABLE IF NOT EXISTS `sales_ranking_configs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `metrics` JSON NOT NULL COMMENT '指标配置(JSON数组)',
    `created_by` INT NULL COMMENT '创建人ID',
    `updated_by` INT NULL COMMENT '更新人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT `fk_sales_ranking_config_created_by` FOREIGN KEY (`created_by`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_sales_ranking_config_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售排名权重配置表';

CREATE INDEX `idx_sales_ranking_config_updated_at`
    ON `sales_ranking_configs` (`updated_at`);

COMMIT;
