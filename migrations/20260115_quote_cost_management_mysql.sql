-- ============================================
-- 报价成本管理模块 - MySQL 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加报价成本模板、成本审批、成本历史记录表
-- ============================================

-- 1. 报价成本模板表
CREATE TABLE IF NOT EXISTS quote_cost_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(50) UNIQUE NOT NULL COMMENT '模板编码',
    template_name VARCHAR(200) NOT NULL COMMENT '模板名称',
    template_type VARCHAR(50) COMMENT '模板类型：STANDARD/CUSTOM/PROJECT',
    equipment_type VARCHAR(50) COMMENT '适用设备类型',
    industry VARCHAR(50) COMMENT '适用行业',
    cost_structure JSON COMMENT '成本结构（分类、明细项、默认值）',
    total_cost DECIMAL(12, 2) COMMENT '模板总成本',
    cost_categories TEXT COMMENT '成本分类（逗号分隔）',
    description TEXT COMMENT '模板说明',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_template_type (template_type),
    INDEX idx_equipment_type (equipment_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价成本模板表';

-- 2. 报价成本审批表
CREATE TABLE IF NOT EXISTS quote_cost_approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_id INT NOT NULL COMMENT '报价ID',
    quote_version_id INT NOT NULL COMMENT '报价版本ID',
    approval_status VARCHAR(20) DEFAULT 'PENDING' COMMENT '审批状态：PENDING/APPROVED/REJECTED',
    approval_level INT DEFAULT 1 COMMENT '审批层级（1=销售经理，2=销售总监，3=财务）',
    current_approver_id INT COMMENT '当前审批人ID',
    total_price DECIMAL(12, 2) COMMENT '总价',
    total_cost DECIMAL(12, 2) COMMENT '总成本',
    gross_margin DECIMAL(5, 2) COMMENT '毛利率',
    margin_threshold DECIMAL(5, 2) DEFAULT 20.00 COMMENT '毛利率阈值',
    margin_status VARCHAR(20) COMMENT '毛利率状态：PASS/WARNING/FAIL',
    cost_complete BOOLEAN DEFAULT FALSE COMMENT '成本拆解是否完整',
    delivery_check BOOLEAN DEFAULT FALSE COMMENT '交期校验是否通过',
    risk_terms_check BOOLEAN DEFAULT FALSE COMMENT '风险条款是否检查',
    approval_comment TEXT COMMENT '审批意见',
    approved_by INT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    rejected_reason TEXT COMMENT '驳回原因',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (current_approver_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    INDEX idx_quote_id (quote_id),
    INDEX idx_approval_status (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价成本审批表';

-- 3. 报价成本历史记录表
CREATE TABLE IF NOT EXISTS quote_cost_histories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_id INT NOT NULL COMMENT '报价ID',
    quote_version_id INT NOT NULL COMMENT '报价版本ID',
    total_price DECIMAL(12, 2) COMMENT '总价',
    total_cost DECIMAL(12, 2) COMMENT '总成本',
    gross_margin DECIMAL(5, 2) COMMENT '毛利率',
    cost_breakdown JSON COMMENT '成本拆解明细',
    change_type VARCHAR(50) COMMENT '变更类型：CREATE/UPDATE/DELETE/APPROVE',
    change_reason TEXT COMMENT '变更原因',
    changed_by INT COMMENT '变更人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (changed_by) REFERENCES users(id),
    INDEX idx_quote_id (quote_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价成本历史记录表';

-- 4. 扩展 quote_versions 表
-- 添加成本管理相关字段
ALTER TABLE quote_versions 
    ADD COLUMN cost_template_id INT COMMENT '使用的成本模板ID' AFTER approved_at,
    ADD COLUMN cost_breakdown_complete BOOLEAN DEFAULT FALSE COMMENT '成本拆解是否完整' AFTER cost_template_id,
    ADD COLUMN margin_warning BOOLEAN DEFAULT FALSE COMMENT '毛利率预警标志' AFTER cost_breakdown_complete,
    ADD FOREIGN KEY (cost_template_id) REFERENCES quote_cost_templates(id);

-- 5. 扩展 quote_items 表
-- 添加成本管理相关字段
ALTER TABLE quote_items 
    ADD COLUMN cost_category VARCHAR(50) COMMENT '成本分类' AFTER remark,
    ADD COLUMN cost_source VARCHAR(50) COMMENT '成本来源：TEMPLATE/MANUAL/HISTORY' AFTER cost_category,
    ADD COLUMN specification TEXT COMMENT '规格型号' AFTER cost_source,
    ADD COLUMN unit VARCHAR(20) COMMENT '单位' AFTER specification;

-- 注释说明
-- quote_cost_templates: 报价成本模板表，存储可复用的成本结构模板
-- quote_cost_approvals: 报价成本审批表，记录成本审批流程和结果
-- quote_cost_histories: 报价成本历史记录表，记录成本变更历史
-- quote_versions扩展: 添加成本模板关联、完整性检查、预警标志
-- quote_items扩展: 添加成本分类、来源、规格、单位等字段








