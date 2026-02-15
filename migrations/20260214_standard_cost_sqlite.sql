-- 标准成本库管理模块
-- 用于存储和管理标准成本数据，支持成本基准设置、版本管理和历史追踪

-- 标准成本表
CREATE TABLE IF NOT EXISTS standard_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cost_code VARCHAR(50) NOT NULL,
    cost_name VARCHAR(200) NOT NULL,
    
    -- 成本分类
    cost_category VARCHAR(50) NOT NULL,  -- MATERIAL: 物料成本, LABOR: 人工成本, OVERHEAD: 制造费用
    
    -- 成本详情
    specification VARCHAR(500),
    unit VARCHAR(20) NOT NULL,  -- 单位（如：件、kg、人天、小时）
    standard_cost DECIMAL(15, 4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    
    -- 成本来源
    cost_source VARCHAR(50) NOT NULL,  -- HISTORICAL_AVG: 历史平均, INDUSTRY_STANDARD: 行业标准, EXPERT_ESTIMATE: 专家估计, VENDOR_QUOTE: 供应商报价
    source_description TEXT,
    
    -- 生效期
    effective_date DATE NOT NULL,
    expiry_date DATE,  -- 为空表示长期有效
    
    -- 版本管理
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    
    -- 元数据
    parent_id INTEGER,  -- 父成本项ID（用于版本追踪）
    created_by INTEGER,
    updated_by INTEGER,
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES standard_costs(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- 标准成本历史记录表
CREATE TABLE IF NOT EXISTS standard_cost_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    standard_cost_id INTEGER NOT NULL,
    
    -- 变更信息
    change_type VARCHAR(20) NOT NULL,  -- CREATE: 创建, UPDATE: 更新, ACTIVATE: 激活, DEACTIVATE: 停用
    change_date DATE NOT NULL,
    
    -- 变更前后值
    old_cost DECIMAL(15, 4),
    new_cost DECIMAL(15, 4),
    old_effective_date DATE,
    new_effective_date DATE,
    
    -- 变更原因
    change_reason TEXT,
    change_description TEXT,
    
    -- 操作人
    changed_by INTEGER,
    changed_by_name VARCHAR(50),
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (standard_cost_id) REFERENCES standard_costs(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_standard_cost_code ON standard_costs(cost_code);
CREATE INDEX IF NOT EXISTS idx_standard_cost_category ON standard_costs(cost_category);
CREATE INDEX IF NOT EXISTS idx_standard_cost_active ON standard_costs(is_active);
CREATE INDEX IF NOT EXISTS idx_standard_cost_effective_date ON standard_costs(effective_date);
CREATE INDEX IF NOT EXISTS idx_standard_cost_expiry_date ON standard_costs(expiry_date);
CREATE INDEX IF NOT EXISTS idx_standard_cost_code_version ON standard_costs(cost_code, version);

CREATE INDEX IF NOT EXISTS idx_cost_history_cost_id ON standard_cost_history(standard_cost_id);
CREATE INDEX IF NOT EXISTS idx_cost_history_change_date ON standard_cost_history(change_date);
CREATE INDEX IF NOT EXISTS idx_cost_history_change_type ON standard_cost_history(change_type);

-- 插入示例标准成本数据
INSERT OR IGNORE INTO standard_costs (
    cost_code, cost_name, cost_category, specification, unit, 
    standard_cost, currency, cost_source, source_description,
    effective_date, is_active, version, description
) VALUES
-- 物料成本
('MAT-001', '钢板Q235', 'MATERIAL', '8mm厚度', 'kg', 4.50, 'CNY', 'HISTORICAL_AVG', '基于过去6个月平均价格', '2026-01-01', 1, 1, '普通碳素结构钢板'),
('MAT-002', '不锈钢304', 'MATERIAL', '2mm厚度', 'kg', 15.80, 'CNY', 'VENDOR_QUOTE', '供应商报价', '2026-01-01', 1, 1, '304不锈钢板材'),
('MAT-003', '铝合金6061', 'MATERIAL', '5mm厚度', 'kg', 22.50, 'CNY', 'INDUSTRY_STANDARD', '行业标准价格', '2026-01-01', 1, 1, '铝合金板材'),
('MAT-004', 'M8螺栓', 'MATERIAL', '304不锈钢', '个', 0.35, 'CNY', 'HISTORICAL_AVG', '历史平均采购价', '2026-01-01', 1, 1, '不锈钢螺栓'),
('MAT-005', '电焊条', 'MATERIAL', 'J422型', 'kg', 12.00, 'CNY', 'VENDOR_QUOTE', '供应商报价', '2026-01-01', 1, 1, '碳钢焊条'),

-- 人工成本
('LAB-001', '高级工程师', 'LABOR', '5年以上经验', '人天', 1200.00, 'CNY', 'EXPERT_ESTIMATE', '基于市场薪酬水平', '2026-01-01', 1, 1, '高级技术人员日工资标准'),
('LAB-002', '中级工程师', 'LABOR', '2-5年经验', '人天', 800.00, 'CNY', 'EXPERT_ESTIMATE', '基于市场薪酬水平', '2026-01-01', 1, 1, '中级技术人员日工资标准'),
('LAB-003', '初级工程师', 'LABOR', '2年以下经验', '人天', 500.00, 'CNY', 'EXPERT_ESTIMATE', '基于市场薪酬水平', '2026-01-01', 1, 1, '初级技术人员日工资标准'),
('LAB-004', '高级技工', 'LABOR', '3年以上经验', '人天', 600.00, 'CNY', 'HISTORICAL_AVG', '历史平均工资', '2026-01-01', 1, 1, '高级技术工人日工资标准'),
('LAB-005', '普通技工', 'LABOR', '1-3年经验', '人天', 400.00, 'CNY', 'HISTORICAL_AVG', '历史平均工资', '2026-01-01', 1, 1, '普通技术工人日工资标准'),

-- 制造费用
('OVH-001', '设备折旧', 'OVERHEAD', '按台时分摊', '台时', 50.00, 'CNY', 'EXPERT_ESTIMATE', '基于设备原值和折旧年限', '2026-01-01', 1, 1, '机器设备折旧费用'),
('OVH-002', '电费', 'OVERHEAD', '工业用电', '度', 0.65, 'CNY', 'HISTORICAL_AVG', '过去一年平均电价', '2026-01-01', 1, 1, '工业用电成本'),
('OVH-003', '车间管理费', 'OVERHEAD', '按人工成本20%', '%', 20.00, 'CNY', 'INDUSTRY_STANDARD', '行业标准分摊率', '2026-01-01', 1, 1, '车间管理人员及运营成本'),
('OVH-004', '质检成本', 'OVERHEAD', '按产值2%', '%', 2.00, 'CNY', 'EXPERT_ESTIMATE', '专家估计', '2026-01-01', 1, 1, '质量检验相关成本'),
('OVH-005', '工具损耗', 'OVERHEAD', '按人工成本5%', '%', 5.00, 'CNY', 'HISTORICAL_AVG', '历史平均损耗率', '2026-01-01', 1, 1, '工具、刀具等损耗');
