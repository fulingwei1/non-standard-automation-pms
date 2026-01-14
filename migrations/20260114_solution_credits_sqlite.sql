-- 方案生成积分系统迁移脚本
-- 日期: 2026-01-14
-- 功能:
--   1. 为用户表添加积分字段
--   2. 创建积分交易记录表
--   3. 为现有用户初始化积分

-- ==================== 1. 用户积分字段 ====================
-- 添加 solution_credits 字段到 users 表
ALTER TABLE users ADD COLUMN solution_credits INTEGER DEFAULT 100 NOT NULL;

-- 添加 credits_updated_at 字段记录最后积分变动时间
ALTER TABLE users ADD COLUMN credits_updated_at DATETIME;


-- ==================== 2. 积分交易记录表 ====================
CREATE TABLE IF NOT EXISTS solution_credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- 交易类型
    transaction_type VARCHAR(30) NOT NULL,
    -- INIT: 初始化积分
    -- GENERATE: 生成方案扣除
    -- ADMIN_ADD: 管理员充值
    -- ADMIN_DEDUCT: 管理员扣除
    -- SYSTEM_REWARD: 系统奖励
    -- REFUND: 退还（生成失败时）

    -- 积分变动
    amount INTEGER NOT NULL,              -- 变动数量（正数为增加，负数为减少）
    balance_before INTEGER NOT NULL,      -- 变动前余额
    balance_after INTEGER NOT NULL,       -- 变动后余额

    -- 关联信息
    related_type VARCHAR(50),             -- 关联对象类型（如 lead, solution 等）
    related_id INTEGER,                   -- 关联对象ID

    -- 操作信息
    operator_id INTEGER REFERENCES users(id),  -- 操作人ID（管理员充值时记录）
    remark TEXT,                          -- 备注说明

    -- 元数据
    ip_address VARCHAR(50),               -- 操作IP
    user_agent VARCHAR(500),              -- 用户代理

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_credit_trans_user ON solution_credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_trans_type ON solution_credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_trans_created ON solution_credit_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_credit_trans_operator ON solution_credit_transactions(operator_id);


-- ==================== 3. 积分配置表 ====================
CREATE TABLE IF NOT EXISTS solution_credit_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT OR IGNORE INTO solution_credit_configs (config_key, config_value, description) VALUES
    ('INITIAL_CREDITS', '100', '新用户初始积分'),
    ('GENERATE_COST', '10', '每次生成方案消耗积分'),
    ('MIN_CREDITS_TO_GENERATE', '10', '生成方案所需最低积分'),
    ('DAILY_FREE_GENERATIONS', '0', '每日免费生成次数（0表示无免费）'),
    ('MAX_CREDITS', '9999', '用户积分上限');


-- ==================== 4. 更新现有用户积分 ====================
-- 为所有现有用户设置初始积分（如果之前没有积分）
UPDATE users SET solution_credits = 100 WHERE solution_credits IS NULL OR solution_credits = 0;
UPDATE users SET credits_updated_at = CURRENT_TIMESTAMP WHERE credits_updated_at IS NULL;

