-- ============================================
-- 奖金分配明细表上传功能 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-01-15
-- 说明: 添加奖金分配明细表上传记录表
-- ============================================

-- ============================================
-- 创建奖金分配明细表上传记录表
-- ============================================

CREATE TABLE IF NOT EXISTS bonus_allocation_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_code VARCHAR(50) NOT NULL UNIQUE,          -- 明细表编号
    sheet_name VARCHAR(200) NOT NULL,                -- 明细表名称
    
    -- 文件信息
    file_path VARCHAR(500) NOT NULL,                  -- 文件路径
    file_name VARCHAR(200),                          -- 原始文件名
    file_size INTEGER,                               -- 文件大小（字节）
    
    -- 关联信息
    project_id INTEGER,                              -- 项目ID（可选）
    period_id INTEGER,                                -- 考核周期ID（可选）
    
    -- 统计信息
    total_rows INTEGER DEFAULT 0,                    -- 总行数
    valid_rows INTEGER DEFAULT 0,                    -- 有效行数
    invalid_rows INTEGER DEFAULT 0,                   -- 无效行数
    
    -- 状态
    status VARCHAR(20) DEFAULT 'UPLOADED',           -- 状态：UPLOADED/PARSED/DISTRIBUTED
    
    -- 解析结果
    parse_result TEXT,                               -- 解析结果(JSON)
    parse_errors TEXT,                               -- 解析错误(JSON)
    
    -- 线下确认标记
    finance_confirmed BOOLEAN DEFAULT 0,            -- 财务部确认
    hr_confirmed BOOLEAN DEFAULT 0,                  -- 人力资源部确认
    manager_confirmed BOOLEAN DEFAULT 0,             -- 总经理确认
    confirmed_at DATETIME,                           -- 确认完成时间
    
    -- 发放信息
    distributed_at DATETIME,                         -- 发放时间
    distributed_by INTEGER,                           -- 发放人
    distribution_count INTEGER DEFAULT 0,             -- 发放记录数
    
    uploaded_by INTEGER NOT NULL,                     -- 上传人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (distributed_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bonus_sheet_code ON bonus_allocation_sheets(sheet_code);
CREATE INDEX IF NOT EXISTS idx_bonus_sheet_status ON bonus_allocation_sheets(status);
CREATE INDEX IF NOT EXISTS idx_bonus_sheet_project ON bonus_allocation_sheets(project_id);
CREATE INDEX IF NOT EXISTS idx_bonus_sheet_period ON bonus_allocation_sheets(period_id);


