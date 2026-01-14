-- 行业与产品映射扩展迁移脚本
-- 日期: 2026-01-14
-- 功能:
--   1. 新增行业分类表
--   2. 新增行业-产品类别映射表
--   3. 新增新产品请求表
--   4. 扩展优势产品表和类别表字段

-- ==================== 1. 行业分类表 ====================
CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES industries(id),
    description TEXT,
    typical_products TEXT,
    typical_tests TEXT,
    market_size VARCHAR(50),
    growth_potential VARCHAR(50),
    company_experience VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_industry_code ON industries(code);
CREATE INDEX IF NOT EXISTS idx_industry_parent ON industries(parent_id);
CREATE INDEX IF NOT EXISTS idx_industry_active ON industries(is_active);


-- ==================== 2. 行业-产品类别映射表 ====================
CREATE TABLE IF NOT EXISTS industry_category_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_id INTEGER NOT NULL REFERENCES industries(id),
    category_id INTEGER NOT NULL REFERENCES advantage_product_categories(id),
    match_score INTEGER DEFAULT 100,
    is_primary BOOLEAN DEFAULT 0,
    typical_scenarios TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ind_cat_mapping_industry ON industry_category_mappings(industry_id);
CREATE INDEX IF NOT EXISTS idx_ind_cat_mapping_category ON industry_category_mappings(category_id);
CREATE INDEX IF NOT EXISTS idx_ind_cat_mapping_primary ON industry_category_mappings(is_primary);


-- ==================== 3. 新产品请求表 ====================
CREATE TABLE IF NOT EXISTS new_product_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    product_name VARCHAR(200) NOT NULL,
    product_type VARCHAR(100),
    industry_id INTEGER REFERENCES industries(id),
    category_id INTEGER REFERENCES advantage_product_categories(id),
    test_requirements TEXT,
    capacity_requirements TEXT,
    special_requirements TEXT,
    market_potential VARCHAR(50),
    similar_customers TEXT,
    estimated_annual_demand INTEGER,
    review_status VARCHAR(20) DEFAULT 'PENDING',
    reviewer_id INTEGER REFERENCES users(id),
    reviewed_at DATETIME,
    review_comment TEXT,
    converted_product_id INTEGER REFERENCES advantage_products(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_new_product_lead ON new_product_requests(lead_id);
CREATE INDEX IF NOT EXISTS idx_new_product_status ON new_product_requests(review_status);
CREATE INDEX IF NOT EXISTS idx_new_product_industry ON new_product_requests(industry_id);


-- ==================== 4. 扩展优势产品类别表 ====================
-- 添加新字段（如果不存在）

-- 检查并添加 test_types 字段
SELECT CASE
    WHEN COUNT(*) = 0 THEN
        'ALTER TABLE advantage_product_categories ADD COLUMN test_types TEXT;'
    ELSE 'SELECT 1;'
END
FROM pragma_table_info('advantage_product_categories')
WHERE name = 'test_types';

-- 由于 SQLite 不支持动态 DDL，直接尝试添加（会忽略已存在的错误）
ALTER TABLE advantage_product_categories ADD COLUMN test_types TEXT;
ALTER TABLE advantage_product_categories ADD COLUMN typical_ct_range VARCHAR(50);
ALTER TABLE advantage_product_categories ADD COLUMN automation_levels TEXT;


-- ==================== 5. 扩展优势产品表 ====================
ALTER TABLE advantage_products ADD COLUMN test_types TEXT;
ALTER TABLE advantage_products ADD COLUMN typical_ct_seconds INTEGER;
ALTER TABLE advantage_products ADD COLUMN max_throughput_uph INTEGER;
ALTER TABLE advantage_products ADD COLUMN automation_level VARCHAR(50);
ALTER TABLE advantage_products ADD COLUMN rail_type VARCHAR(50);
ALTER TABLE advantage_products ADD COLUMN workstation_count INTEGER;
ALTER TABLE advantage_products ADD COLUMN applicable_products TEXT;
ALTER TABLE advantage_products ADD COLUMN applicable_interfaces TEXT;
ALTER TABLE advantage_products ADD COLUMN special_features TEXT;
ALTER TABLE advantage_products ADD COLUMN reference_price_min NUMERIC(14, 2);
ALTER TABLE advantage_products ADD COLUMN reference_price_max NUMERIC(14, 2);
ALTER TABLE advantage_products ADD COLUMN typical_lead_time_days INTEGER;
ALTER TABLE advantage_products ADD COLUMN match_keywords TEXT;
ALTER TABLE advantage_products ADD COLUMN priority_score INTEGER DEFAULT 50;


-- ==================== 6. 插入默认行业数据 ====================

-- 一级行业
INSERT OR IGNORE INTO industries (code, name, sort_order, market_size, growth_potential, company_experience) VALUES
    ('3C_ELECTRONICS', '3C电子', 1, 'LARGE', 'MEDIUM', 'EXPERT'),
    ('AUTOMOTIVE', '汽车电子', 2, 'LARGE', 'HIGH', 'EXPERT'),
    ('NEW_ENERGY', '新能源', 3, 'LARGE', 'HIGH', 'EXPERIENCED'),
    ('HOME_APPLIANCE', '家电', 4, 'LARGE', 'LOW', 'EXPERT'),
    ('MEDICAL_DEVICE', '医疗器械', 5, 'MEDIUM', 'HIGH', 'LEARNING'),
    ('INDUSTRIAL_CONTROL', '工业控制', 6, 'MEDIUM', 'MEDIUM', 'EXPERIENCED'),
    ('SEMICONDUCTOR', '半导体', 7, 'LARGE', 'HIGH', 'EXPERIENCED'),
    ('COMMUNICATION', '通信设备', 8, 'LARGE', 'MEDIUM', 'EXPERIENCED'),
    ('POWER_TOOLS', '电动工具', 9, 'MEDIUM', 'MEDIUM', 'EXPERT'),
    ('LIGHTING', '照明', 10, 'MEDIUM', 'LOW', 'EXPERIENCED'),
    ('AEROSPACE', '航空航天', 11, 'MEDIUM', 'HIGH', 'LEARNING'),
    ('MILITARY', '军工', 12, 'MEDIUM', 'MEDIUM', 'LEARNING'),
    ('EDUCATION', '教育科研', 13, 'SMALL', 'MEDIUM', 'EXPERIENCED'),
    ('OTHER', '其他行业', 99, 'SMALL', 'LOW', 'LEARNING');

-- 二级行业（3C电子）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('MOBILE_PHONE', '手机', (SELECT id FROM industries WHERE code = '3C_ELECTRONICS'), 1, '["手机主板", "摄像头模组", "触摸屏", "电池"]'),
    ('TABLET', '平板电脑', (SELECT id FROM industries WHERE code = '3C_ELECTRONICS'), 2, '["主板", "显示屏", "电池包"]'),
    ('LAPTOP', '笔记本电脑', (SELECT id FROM industries WHERE code = '3C_ELECTRONICS'), 3, '["主板", "键盘", "电源适配器"]'),
    ('WEARABLE', '可穿戴设备', (SELECT id FROM industries WHERE code = '3C_ELECTRONICS'), 4, '["智能手表", "TWS耳机", "手环"]'),
    ('CHARGER', '充电器/适配器', (SELECT id FROM industries WHERE code = '3C_ELECTRONICS'), 5, '["充电器", "适配器", "充电宝"]');

-- 二级行业（汽车电子）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('AUTO_ECU', 'ECU/控制器', (SELECT id FROM industries WHERE code = 'AUTOMOTIVE'), 1, '["域控制器", "BMS", "MCU", "VCU"]'),
    ('AUTO_SENSOR', '汽车传感器', (SELECT id FROM industries WHERE code = 'AUTOMOTIVE'), 2, '["毫米波雷达", "激光雷达", "摄像头"]'),
    ('AUTO_MOTOR', '汽车电机', (SELECT id FROM industries WHERE code = 'AUTOMOTIVE'), 3, '["驱动电机", "转向电机", "车窗电机"]'),
    ('AUTO_LIGHTING', '汽车车灯', (SELECT id FROM industries WHERE code = 'AUTOMOTIVE'), 4, '["LED大灯", "尾灯", "转向灯"]'),
    ('AUTO_CHARGING', '汽车充电', (SELECT id FROM industries WHERE code = 'AUTOMOTIVE'), 5, '["OBC", "DC-DC", "充电桩"]');

-- 二级行业（新能源）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('BATTERY_PACK', '动力电池', (SELECT id FROM industries WHERE code = 'NEW_ENERGY'), 1, '["电芯", "模组", "PACK"]'),
    ('ENERGY_STORAGE', '储能系统', (SELECT id FROM industries WHERE code = 'NEW_ENERGY'), 2, '["储能电池", "BMS", "PCS"]'),
    ('PV_INVERTER', '光伏逆变', (SELECT id FROM industries WHERE code = 'NEW_ENERGY'), 3, '["逆变器", "优化器", "汇流箱"]'),
    ('CHARGING_PILE', '充电桩', (SELECT id FROM industries WHERE code = 'NEW_ENERGY'), 4, '["直流桩", "交流桩", "充电模块"]');

-- 二级行业（家电）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('WHITE_APPLIANCE', '白色家电', (SELECT id FROM industries WHERE code = 'HOME_APPLIANCE'), 1, '["空调", "冰箱", "洗衣机"]'),
    ('SMALL_APPLIANCE', '小家电', (SELECT id FROM industries WHERE code = 'HOME_APPLIANCE'), 2, '["电饭煲", "吸尘器", "破壁机"]'),
    ('KITCHEN_APPLIANCE', '厨房电器', (SELECT id FROM industries WHERE code = 'HOME_APPLIANCE'), 3, '["油烟机", "燃气灶", "消毒柜"]');

-- 二级行业（医疗器械）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('MEDICAL_MONITOR', '监护设备', (SELECT id FROM industries WHERE code = 'MEDICAL_DEVICE'), 1, '["血压计", "血糖仪", "心电监护"]'),
    ('MEDICAL_IMAGING', '影像设备', (SELECT id FROM industries WHERE code = 'MEDICAL_DEVICE'), 2, '["CT", "MRI", "超声"]'),
    ('IVD', '体外诊断', (SELECT id FROM industries WHERE code = 'MEDICAL_DEVICE'), 3, '["生化分析仪", "免疫分析仪"]');

-- 二级行业（工业控制）
INSERT OR IGNORE INTO industries (code, name, parent_id, sort_order, typical_products) VALUES
    ('PLC_DCS', 'PLC/DCS', (SELECT id FROM industries WHERE code = 'INDUSTRIAL_CONTROL'), 1, '["PLC", "DCS", "PAC"]'),
    ('SERVO_DRIVE', '伺服驱动', (SELECT id FROM industries WHERE code = 'INDUSTRIAL_CONTROL'), 2, '["伺服驱动器", "伺服电机"]'),
    ('FREQUENCY_CONVERTER', '变频器', (SELECT id FROM industries WHERE code = 'INDUSTRIAL_CONTROL'), 3, '["通用变频器", "专用变频器"]');


-- ==================== 7. 插入行业-产品类别映射 ====================

-- 3C电子 -> 白色家电测试设备
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = '3C_ELECTRONICS' AND c.code = 'HOME_APPLIANCE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'MOBILE_PHONE' AND c.code = 'HOME_APPLIANCE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'CHARGER' AND c.code = 'HOME_APPLIANCE';

-- 汽车电子
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'AUTOMOTIVE' AND c.code = 'AUTOMOTIVE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'AUTO_ECU' AND c.code = 'AUTOMOTIVE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 90, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'AUTO_SENSOR' AND c.code = 'AUTOMOTIVE';

-- 新能源
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'NEW_ENERGY' AND c.code = 'NEW_ENERGY';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'BATTERY_PACK' AND c.code = 'NEW_ENERGY';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 95, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'ENERGY_STORAGE' AND c.code = 'NEW_ENERGY';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 90, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'CHARGING_PILE' AND c.code = 'NEW_ENERGY';

-- 家电
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'HOME_APPLIANCE' AND c.code = 'HOME_APPLIANCE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'WHITE_APPLIANCE' AND c.code = 'HOME_APPLIANCE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 95, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'SMALL_APPLIANCE' AND c.code = 'HOME_APPLIANCE';

-- 半导体
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'SEMICONDUCTOR' AND c.code = 'SEMICONDUCTOR';

-- 电动工具
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'POWER_TOOLS' AND c.code = 'POWER_TOOLS';

-- 教育
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 100, 1
FROM industries i, advantage_product_categories c
WHERE i.code = 'EDUCATION' AND c.code = 'EDUCATION';

-- 通用映射：所有行业都可以使用自动化线体和其他设备
INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 60, 0
FROM industries i, advantage_product_categories c
WHERE i.parent_id IS NULL AND c.code = 'AUTOMATION_LINE';

INSERT OR IGNORE INTO industry_category_mappings (industry_id, category_id, match_score, is_primary)
SELECT i.id, c.id, 40, 0
FROM industries i, advantage_product_categories c
WHERE i.parent_id IS NULL AND c.code = 'OTHER_EQUIPMENT';
