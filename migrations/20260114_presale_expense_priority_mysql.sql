-- ============================================
-- 售前费用与优先级管理模块 - MySQL 迁移文件
-- 创建日期: 2026-01-14
-- 说明: 添加售前费用表，扩展线索和商机表添加优先级字段
-- ============================================

-- 1. 创建售前费用表
CREATE TABLE IF NOT EXISTS presale_expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL COMMENT '项目ID（未中标项目）',
    project_code VARCHAR(50) COMMENT '项目编号（冗余字段）',
    project_name VARCHAR(200) COMMENT '项目名称（冗余字段）',
    lead_id INT COMMENT '关联线索ID',
    opportunity_id INT COMMENT '关联商机ID',
    expense_type VARCHAR(20) NOT NULL COMMENT '费用类型：LABOR_COST/TRAVEL_COST/OTHER',
    expense_category VARCHAR(50) NOT NULL COMMENT '费用分类：LOST_BID/ABANDONED',
    amount DECIMAL(14, 2) NOT NULL COMMENT '费用金额',
    labor_hours DECIMAL(10, 2) COMMENT '工时数（如果是工时费用）',
    hourly_rate DECIMAL(10, 2) COMMENT '工时单价',
    user_id INT COMMENT '人员ID（工时费用）',
    user_name VARCHAR(50) COMMENT '人员姓名（冗余）',
    department_id INT COMMENT '部门ID',
    department_name VARCHAR(100) COMMENT '部门名称（冗余）',
    salesperson_id INT COMMENT '销售人员ID',
    salesperson_name VARCHAR(50) COMMENT '销售人员姓名（冗余）',
    expense_date DATE NOT NULL COMMENT '费用发生日期',
    description TEXT COMMENT '费用说明',
    loss_reason VARCHAR(50) COMMENT '未中标原因',
    loss_reason_detail TEXT COMMENT '未中标原因详情',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (salesperson_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_presale_expense_project (project_id),
    INDEX idx_presale_expense_lead (lead_id),
    INDEX idx_presale_expense_opportunity (opportunity_id),
    INDEX idx_presale_expense_type (expense_type),
    INDEX idx_presale_expense_category (expense_category),
    INDEX idx_presale_expense_date (expense_date),
    INDEX idx_presale_expense_user (user_id),
    INDEX idx_presale_expense_salesperson (salesperson_id),
    INDEX idx_presale_expense_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='售前费用表';

-- 2. 扩展leads表添加优先级字段
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS priority_score INT COMMENT '优先级评分（0-100）',
ADD COLUMN IF NOT EXISTS is_key_lead BOOLEAN DEFAULT FALSE COMMENT '是否关键线索',
ADD COLUMN IF NOT EXISTS priority_level VARCHAR(10) COMMENT '优先级等级：P1/P2/P3/P4',
ADD COLUMN IF NOT EXISTS importance_level VARCHAR(10) COMMENT '重要程度：HIGH/MEDIUM/LOW',
ADD COLUMN IF NOT EXISTS urgency_level VARCHAR(10) COMMENT '紧急程度：HIGH/MEDIUM/LOW';

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_leads_priority_score ON leads(priority_score);
CREATE INDEX IF NOT EXISTS idx_leads_is_key ON leads(is_key_lead);
CREATE INDEX IF NOT EXISTS idx_leads_priority_level ON leads(priority_level);

-- 3. 扩展opportunities表添加优先级字段
ALTER TABLE opportunities 
ADD COLUMN IF NOT EXISTS priority_score INT COMMENT '优先级评分（0-100）',
ADD COLUMN IF NOT EXISTS is_key_opportunity BOOLEAN DEFAULT FALSE COMMENT '是否关键商机',
ADD COLUMN IF NOT EXISTS priority_level VARCHAR(10) COMMENT '优先级等级：P1/P2/P3/P4';

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_opportunities_priority_score ON opportunities(priority_score);
CREATE INDEX IF NOT EXISTS idx_opportunities_is_key ON opportunities(is_key_opportunity);
CREATE INDEX IF NOT EXISTS idx_opportunities_priority_level ON opportunities(priority_level);
