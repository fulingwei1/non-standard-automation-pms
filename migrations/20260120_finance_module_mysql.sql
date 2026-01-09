-- ============================================
-- 融资管理模块 - MySQL 迁移文件
-- 创建日期: 2025-01-20
-- 说明: 创建融资管理模块相关表
-- ============================================

-- ============================================
-- 1. 融资轮次表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_rounds (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    round_code VARCHAR(50) NOT NULL UNIQUE COMMENT '轮次编码',
    round_name VARCHAR(100) NOT NULL COMMENT '轮次名称',
    round_type VARCHAR(20) NOT NULL COMMENT '轮次类型：SEED/A/B/C/D/E/PRE_IPO/IPO',
    round_order INT NOT NULL COMMENT '轮次顺序（1,2,3...）',
    
    -- 融资信息
    target_amount DECIMAL(15, 2) NOT NULL COMMENT '目标融资金额',
    actual_amount DECIMAL(15, 2) DEFAULT 0 COMMENT '实际融资金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    valuation_pre DECIMAL(15, 2) COMMENT '投前估值',
    valuation_post DECIMAL(15, 2) COMMENT '投后估值',
    
    -- 时间信息
    launch_date DATE COMMENT '启动日期',
    closing_date DATE COMMENT '交割日期',
    expected_closing_date DATE COMMENT '预期交割日期',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNING' COMMENT '状态：PLANNING/IN_PROGRESS/CLOSED/CANCELLED',
    
    -- 负责人
    lead_investor_id INT UNSIGNED COMMENT '领投方ID',
    lead_investor_name VARCHAR(200) COMMENT '领投方名称（冗余）',
    responsible_person_id INT UNSIGNED COMMENT '负责人ID',
    responsible_person_name VARCHAR(50) COMMENT '负责人姓名（冗余）',
    
    -- 备注
    description TEXT COMMENT '轮次说明',
    notes TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (lead_investor_id) REFERENCES investors(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id),
    
    INDEX idx_funding_round_code (round_code),
    INDEX idx_funding_round_type (round_type),
    INDEX idx_funding_round_status (status),
    INDEX idx_funding_round_order (round_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='融资轮次表';

-- ============================================
-- 2. 投资方表
-- ============================================
CREATE TABLE IF NOT EXISTS investors (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    investor_code VARCHAR(50) NOT NULL UNIQUE COMMENT '投资方编码',
    investor_name VARCHAR(200) NOT NULL COMMENT '投资方名称',
    investor_type VARCHAR(20) NOT NULL COMMENT '投资方类型：VC/PE/ANGEL/STRATEGIC/GOVERNMENT/CORPORATE/INDIVIDUAL',
    
    -- 基本信息
    legal_name VARCHAR(200) COMMENT '法人名称',
    registration_no VARCHAR(100) COMMENT '注册号/统一社会信用代码',
    country VARCHAR(50) DEFAULT '中国' COMMENT '国家',
    region VARCHAR(50) COMMENT '地区（省/市）',
    address VARCHAR(500) COMMENT '地址',
    
    -- 联系信息
    contact_person VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(50) COMMENT '联系电话',
    contact_email VARCHAR(100) COMMENT '联系邮箱',
    website VARCHAR(200) COMMENT '官网',
    
    -- 投资信息
    investment_focus TEXT COMMENT '投资领域/关注行业',
    investment_stage VARCHAR(100) COMMENT '投资阶段偏好（如：A轮-B轮）',
    typical_ticket_size DECIMAL(15, 2) COMMENT '典型投资金额',
    portfolio_companies TEXT COMMENT '投资组合（JSON或文本）',
    
    -- 状态
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否有效',
    is_lead_investor TINYINT(1) DEFAULT 0 COMMENT '是否曾作为领投方',
    
    -- 备注
    description TEXT COMMENT '投资方说明',
    notes TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_investor_code (investor_code),
    INDEX idx_investor_type (investor_type),
    INDEX idx_investor_name (investor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投资方表';

-- ============================================
-- 3. 融资记录表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_records (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    record_code VARCHAR(50) NOT NULL UNIQUE COMMENT '记录编码',
    
    -- 关联信息
    funding_round_id INT UNSIGNED NOT NULL COMMENT '融资轮次ID',
    investor_id INT UNSIGNED NOT NULL COMMENT '投资方ID',
    
    -- 投资信息
    investment_amount DECIMAL(15, 2) NOT NULL COMMENT '投资金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    share_percentage DECIMAL(8, 4) COMMENT '持股比例（%）',
    share_count DECIMAL(15, 2) COMMENT '持股数量',
    price_per_share DECIMAL(10, 4) COMMENT '每股价格',
    
    -- 时间信息
    commitment_date DATE COMMENT '承诺日期',
    payment_date DATE COMMENT '付款日期',
    actual_payment_date DATE COMMENT '实际付款日期',
    
    -- 付款信息
    payment_method VARCHAR(20) COMMENT '付款方式：WIRE/CHECK/CASH/OTHER',
    payment_status VARCHAR(20) DEFAULT 'PENDING' COMMENT '付款状态：PENDING/PARTIAL/COMPLETED',
    paid_amount DECIMAL(15, 2) DEFAULT 0 COMMENT '已付金额',
    remaining_amount DECIMAL(15, 2) COMMENT '剩余金额',
    
    -- 合同信息
    contract_no VARCHAR(100) COMMENT '合同编号',
    contract_date DATE COMMENT '合同签署日期',
    contract_file VARCHAR(500) COMMENT '合同文件路径',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'COMMITTED' COMMENT '状态：COMMITTED/PAID/CANCELLED',
    
    -- 备注
    description TEXT COMMENT '投资说明',
    notes TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id),
    
    INDEX idx_funding_record_round (funding_round_id),
    INDEX idx_funding_record_investor (investor_id),
    INDEX idx_funding_record_status (status),
    INDEX idx_funding_record_payment (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='融资记录表';

-- ============================================
-- 4. 股权结构表
-- ============================================
CREATE TABLE IF NOT EXISTS equity_structures (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    
    -- 关联信息
    funding_round_id INT UNSIGNED NOT NULL COMMENT '融资轮次ID',
    investor_id INT UNSIGNED COMMENT '投资方ID（为空表示创始人/员工等）',
    
    -- 股东信息
    shareholder_name VARCHAR(200) NOT NULL COMMENT '股东名称',
    shareholder_type VARCHAR(20) NOT NULL COMMENT '股东类型：FOUNDER/EMPLOYEE/INVESTOR/OTHER',
    
    -- 股权信息
    share_percentage DECIMAL(8, 4) NOT NULL COMMENT '持股比例（%）',
    share_count DECIMAL(15, 2) COMMENT '持股数量',
    share_class VARCHAR(20) COMMENT '股份类别：COMMON/PREFERRED/OPTION',
    
    -- 时间信息
    effective_date DATE NOT NULL COMMENT '生效日期',
    
    -- 备注
    description TEXT COMMENT '说明',
    notes TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id),
    
    INDEX idx_equity_round (funding_round_id),
    INDEX idx_equity_investor (investor_id),
    INDEX idx_equity_type (shareholder_type),
    INDEX idx_equity_date (effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股权结构表';

-- ============================================
-- 5. 融资用途表
-- ============================================
CREATE TABLE IF NOT EXISTS funding_usages (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    
    -- 关联信息
    funding_round_id INT UNSIGNED NOT NULL COMMENT '融资轮次ID',
    
    -- 用途信息
    usage_category VARCHAR(50) NOT NULL COMMENT '用途分类：R&D/MARKETING/OPERATIONS/EQUIPMENT/FACILITIES/WORKING_CAPITAL/OTHER',
    usage_item VARCHAR(200) NOT NULL COMMENT '用途项目',
    planned_amount DECIMAL(15, 2) NOT NULL COMMENT '计划金额',
    actual_amount DECIMAL(15, 2) DEFAULT 0 COMMENT '实际金额',
    percentage DECIMAL(5, 2) COMMENT '占比（%）',
    
    -- 时间信息
    planned_start_date DATE COMMENT '计划开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNED' COMMENT '状态：PLANNED/IN_PROGRESS/COMPLETED/CANCELLED',
    
    -- 负责人
    responsible_person_id INT UNSIGNED COMMENT '负责人ID',
    responsible_person_name VARCHAR(50) COMMENT '负责人姓名（冗余）',
    
    -- 备注
    description TEXT COMMENT '用途说明',
    notes TEXT COMMENT '备注',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id),
    
    INDEX idx_funding_usage_round (funding_round_id),
    INDEX idx_funding_usage_category (usage_category),
    INDEX idx_funding_usage_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='融资用途表';
