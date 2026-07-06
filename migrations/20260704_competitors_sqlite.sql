-- 竞争对手库
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    short_name VARCHAR(50),
    competitor_type VARCHAR(50),
    strengths TEXT,
    weaknesses TEXT,
    good_at TEXT,
    typical_projects TEXT,
    price_level VARCHAR(20),
    delivery_time VARCHAR(50),
    service_area VARCHAR(100),
    counter_strategy TEXT,
    encounter_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);
