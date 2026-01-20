-- 节假日配置表
-- 用于存储法定节假日、调休日等，支持工时类型判断

CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    holiday_type VARCHAR(20) NOT NULL,  -- HOLIDAY: 法定节假日, WORKDAY: 调休工作日, COMPANY: 公司假期
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_holiday_date ON holidays(holiday_date);
CREATE INDEX IF NOT EXISTS idx_holiday_year ON holidays(year);
CREATE INDEX IF NOT EXISTS idx_holiday_type ON holidays(holiday_type);

-- 插入2025年常见节假日数据（示例）
INSERT OR IGNORE INTO holidays (holiday_date, year, holiday_type, name, description) VALUES
-- 元旦
('2025-01-01', 2025, 'HOLIDAY', '元旦', '新年元旦'),
-- 春节
('2025-01-28', 2025, 'HOLIDAY', '春节', '除夕'),
('2025-01-29', 2025, 'HOLIDAY', '春节', '春节第一天'),
('2025-01-30', 2025, 'HOLIDAY', '春节', '春节第二天'),
('2025-01-31', 2025, 'HOLIDAY', '春节', '春节第三天'),
('2025-02-01', 2025, 'HOLIDAY', '春节', '春节第四天'),
('2025-02-02', 2025, 'HOLIDAY', '春节', '春节第五天'),
('2025-02-03', 2025, 'HOLIDAY', '春节', '春节第六天'),
('2025-02-04', 2025, 'HOLIDAY', '春节', '春节第七天'),
-- 春节调休（周末上班）
('2025-01-26', 2025, 'WORKDAY', '春节调休', '周日调休上班'),
('2025-02-08', 2025, 'WORKDAY', '春节调休', '周六调休上班'),
-- 清明节
('2025-04-04', 2025, 'HOLIDAY', '清明节', '清明节'),
('2025-04-05', 2025, 'HOLIDAY', '清明节', '清明节假期'),
('2025-04-06', 2025, 'HOLIDAY', '清明节', '清明节假期'),
-- 劳动节
('2025-05-01', 2025, 'HOLIDAY', '劳动节', '国际劳动节'),
('2025-05-02', 2025, 'HOLIDAY', '劳动节', '劳动节假期'),
('2025-05-03', 2025, 'HOLIDAY', '劳动节', '劳动节假期'),
('2025-05-04', 2025, 'HOLIDAY', '劳动节', '劳动节假期'),
('2025-05-05', 2025, 'HOLIDAY', '劳动节', '劳动节假期'),
-- 劳动节调休
('2025-04-27', 2025, 'WORKDAY', '劳动节调休', '周日调休上班'),
-- 端午节
('2025-05-31', 2025, 'HOLIDAY', '端午节', '端午节'),
('2025-06-01', 2025, 'HOLIDAY', '端午节', '端午节假期'),
('2025-06-02', 2025, 'HOLIDAY', '端午节', '端午节假期'),
-- 中秋节
('2025-10-06', 2025, 'HOLIDAY', '中秋节', '中秋节'),
-- 国庆节
('2025-10-01', 2025, 'HOLIDAY', '国庆节', '国庆节'),
('2025-10-02', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
('2025-10-03', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
('2025-10-04', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
('2025-10-05', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
('2025-10-07', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
('2025-10-08', 2025, 'HOLIDAY', '国庆节', '国庆节假期'),
-- 国庆节调休
('2025-09-28', 2025, 'WORKDAY', '国庆节调休', '周日调休上班'),
('2025-10-11', 2025, 'WORKDAY', '国庆节调休', '周六调休上班');
