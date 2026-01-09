-- 销售目标表 (MySQL)
-- 创建时间: 2026-01-20
-- 说明: Issue 6.5 - 销售目标管理功能

CREATE TABLE IF NOT EXISTS sales_targets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_scope VARCHAR(20) NOT NULL COMMENT '目标范围：PERSONAL/TEAM/DEPARTMENT',
    user_id INT COMMENT '用户ID（个人目标）',
    department_id INT COMMENT '部门ID（部门目标）',
    team_id INT COMMENT '团队ID（团队目标）',
    target_type VARCHAR(20) NOT NULL COMMENT '目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT',
    target_period VARCHAR(20) NOT NULL COMMENT '目标周期：MONTHLY/QUARTERLY/YEARLY',
    period_value VARCHAR(20) NOT NULL COMMENT '周期标识：2025-01/2025-Q1/2025',
    target_value DECIMAL(14, 2) NOT NULL COMMENT '目标值',
    description TEXT COMMENT '目标描述',
    status VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE/COMPLETED/CANCELLED',
    created_by INT NOT NULL COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_sales_target_scope (target_scope, user_id, department_id),
    INDEX idx_sales_target_type_period (target_type, target_period, period_value),
    INDEX idx_sales_target_status (status),
    INDEX idx_sales_target_user (user_id),
    INDEX idx_sales_target_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售目标表';
