-- ============================================
-- 财务历史项目成本模块 - MySQL 迁移文件
-- 创建日期: 2025-01-15
-- 说明: 添加财务历史项目成本表（财务部维护的非物料成本）
-- ============================================

-- 财务历史项目成本表
CREATE TABLE IF NOT EXISTS financial_project_costs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL COMMENT '项目ID',
    project_code VARCHAR(50) COMMENT '项目编号（冗余字段）',
    project_name VARCHAR(200) COMMENT '项目名称（冗余字段）',
    machine_id INT COMMENT '设备ID',
    cost_type VARCHAR(50) NOT NULL COMMENT '成本类型：LABOR/TRAVEL/ENTERTAINMENT/OTHER',
    cost_category VARCHAR(50) NOT NULL COMMENT '成本分类：出差费/人工费/招待费/其他',
    cost_item VARCHAR(200) COMMENT '成本项名称',
    amount DECIMAL(14, 2) NOT NULL COMMENT '金额',
    tax_amount DECIMAL(12, 2) DEFAULT 0 COMMENT '税额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    cost_date DATE NOT NULL COMMENT '发生日期',
    cost_month VARCHAR(7) COMMENT '成本月份(YYYY-MM)',
    description TEXT COMMENT '费用说明',
    location VARCHAR(200) COMMENT '地点（出差费用）',
    participants VARCHAR(500) COMMENT '参与人员（逗号分隔）',
    purpose VARCHAR(500) COMMENT '用途/目的',
    user_id INT COMMENT '人员ID（人工费用）',
    user_name VARCHAR(50) COMMENT '人员姓名（冗余）',
    hours DECIMAL(10, 2) COMMENT '工时（人工费用）',
    hourly_rate DECIMAL(10, 2) COMMENT '时薪（人工费用）',
    source_type VARCHAR(50) DEFAULT 'FINANCIAL_UPLOAD' COMMENT '来源类型',
    source_no VARCHAR(100) COMMENT '来源单号',
    invoice_no VARCHAR(100) COMMENT '发票号',
    upload_batch_no VARCHAR(50) COMMENT '上传批次号',
    uploaded_by INT NOT NULL COMMENT '上传人ID（财务部）',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已核实',
    verified_by INT COMMENT '核实人ID',
    verified_at DATETIME COMMENT '核实时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    INDEX idx_financial_cost_project (project_id),
    INDEX idx_financial_cost_type (cost_type),
    INDEX idx_financial_cost_category (cost_category),
    INDEX idx_financial_cost_date (cost_date),
    INDEX idx_financial_cost_month (cost_month),
    INDEX idx_financial_cost_upload_batch (upload_batch_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='财务历史项目成本表';
