
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code VARCHAR(10) UNIQUE NOT NULL,     -- E0001
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50),                        -- 机械部/电气部/PMC
    role VARCHAR(50),                              -- 机械工程师/调试工程师
    phone VARCHAR(20),
    wechat_userid VARCHAR(50),                     -- 企业微信UserID
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
