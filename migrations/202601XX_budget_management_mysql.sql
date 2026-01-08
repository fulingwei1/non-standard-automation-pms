-- 项目预算管理模块 - MySQL 迁移文件
-- 创建日期：2025-01-XX

-- ============================================
-- 1. 项目预算表
-- ============================================

CREATE TABLE IF NOT EXISTS project_budgets (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    budget_no           VARCHAR(50) UNIQUE NOT NULL COMMENT '预算编号',
    project_id          BIGINT NOT NULL COMMENT '项目ID',
    budget_name         VARCHAR(200) NOT NULL COMMENT '预算名称',
    budget_type         VARCHAR(20) DEFAULT 'INITIAL' COMMENT '预算类型：INITIAL/REVISED/SUPPLEMENT',
    version             VARCHAR(20) DEFAULT 'V1.0' COMMENT '预算版本号',
    total_amount        DECIMAL(14, 2) NOT NULL DEFAULT 0 COMMENT '预算总额',
    budget_breakdown    JSON COMMENT '预算明细（JSON格式）',
    status              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/SUBMITTED/APPROVED/REJECTED',
    submitted_at        DATETIME COMMENT '提交时间',
    submitted_by        BIGINT COMMENT '提交人ID',
    approved_by         BIGINT COMMENT '审批人ID',
    approved_at         DATETIME COMMENT '审批时间',
    approval_note       TEXT COMMENT '审批意见',
    effective_date      DATE COMMENT '生效日期',
    expiry_date         DATE COMMENT '失效日期',
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否生效',
    remark              TEXT COMMENT '备注',
    created_by          BIGINT COMMENT '创建人ID',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    
    INDEX idx_budget_project (project_id),
    INDEX idx_budget_status (status),
    INDEX idx_budget_version (project_id, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目预算表';

-- ============================================
-- 2. 项目预算明细表
-- ============================================

CREATE TABLE IF NOT EXISTS project_budget_items (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    budget_id           BIGINT NOT NULL COMMENT '预算ID',
    item_no             INT NOT NULL COMMENT '行号',
    cost_category       VARCHAR(50) NOT NULL COMMENT '成本类别',
    cost_item           VARCHAR(200) NOT NULL COMMENT '成本项',
    description         TEXT COMMENT '说明',
    budget_amount       DECIMAL(14, 2) NOT NULL DEFAULT 0 COMMENT '预算金额',
    machine_id          BIGINT COMMENT '机台ID（可选）',
    remark              TEXT COMMENT '备注',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (budget_id) REFERENCES project_budgets(id) ON DELETE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    
    INDEX idx_budget_item_budget (budget_id),
    INDEX idx_budget_item_category (cost_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目预算明细表';

-- ============================================
-- 3. 项目成本分摊规则表
-- ============================================

CREATE TABLE IF NOT EXISTS project_cost_allocation_rules (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    rule_name           VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type           VARCHAR(20) NOT NULL COMMENT '分摊类型：PROPORTION/MANUAL',
    allocation_basis    VARCHAR(20) NOT NULL COMMENT '分摊依据：MACHINE_COUNT/REVENUE/MANUAL',
    allocation_formula  JSON COMMENT '分摊公式（JSON格式）',
    cost_type           VARCHAR(50) COMMENT '适用成本类型',
    cost_category       VARCHAR(50) COMMENT '适用成本分类',
    project_ids         JSON COMMENT '适用项目ID列表',
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    effective_date      DATE COMMENT '生效日期',
    expiry_date         DATE COMMENT '失效日期',
    remark              TEXT COMMENT '备注',
    created_by          BIGINT COMMENT '创建人ID',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    
    INDEX idx_allocation_rule_name (rule_name),
    INDEX idx_allocation_rule_type (rule_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目成本分摊规则表';






