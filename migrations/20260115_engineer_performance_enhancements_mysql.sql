-- 工程师绩效管理系统增强功能迁移（MySQL版本）
-- 日期: 2026-01-15
-- 说明: 添加部门经理调整、调整历史记录等功能

-- 1. 扩展 performance_result 表，添加部门经理调整字段
ALTER TABLE performance_result 
ADD COLUMN original_total_score DECIMAL(5,2) COMMENT '原始综合得分（调整前）',
ADD COLUMN adjusted_total_score DECIMAL(5,2) COMMENT '调整后综合得分',
ADD COLUMN original_dept_rank INT COMMENT '原始部门排名（调整前）',
ADD COLUMN adjusted_dept_rank INT COMMENT '调整后部门排名',
ADD COLUMN original_company_rank INT COMMENT '原始公司排名（调整前）',
ADD COLUMN adjusted_company_rank INT COMMENT '调整后公司排名',
ADD COLUMN adjustment_reason TEXT COMMENT '调整理由（必填）',
ADD COLUMN adjusted_by INT COMMENT '调整人ID（部门经理）',
ADD COLUMN adjusted_at DATETIME COMMENT '调整时间',
ADD COLUMN is_adjusted BOOLEAN DEFAULT FALSE COMMENT '是否已调整';

-- 添加索引
CREATE INDEX idx_perf_result_adjusted ON performance_result(is_adjusted);

-- 2. 创建绩效调整历史记录表
CREATE TABLE IF NOT EXISTS performance_adjustment_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_id BIGINT NOT NULL COMMENT '绩效结果ID',
    original_total_score DECIMAL(5,2) COMMENT '原始综合得分',
    original_dept_rank INT COMMENT '原始部门排名',
    original_company_rank INT COMMENT '原始公司排名',
    original_level VARCHAR(20) COMMENT '原始等级',
    adjusted_total_score DECIMAL(5,2) COMMENT '调整后综合得分',
    adjusted_dept_rank INT COMMENT '调整后部门排名',
    adjusted_company_rank INT COMMENT '调整后公司排名',
    adjusted_level VARCHAR(20) COMMENT '调整后等级',
    adjustment_reason TEXT NOT NULL COMMENT '调整理由（必填）',
    adjusted_by BIGINT NOT NULL COMMENT '调整人ID',
    adjusted_by_name VARCHAR(50) COMMENT '调整人姓名',
    adjusted_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '调整时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id),
    FOREIGN KEY (adjusted_by) REFERENCES users(id),
    INDEX idx_adj_history_result (result_id),
    INDEX idx_adj_history_adjuster (adjusted_by),
    INDEX idx_adj_history_time (adjusted_at)
) COMMENT '绩效调整历史记录表';
