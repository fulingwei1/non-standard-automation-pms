-- 用户账号同步功能 - 数据库迁移
-- 日期: 2026-01-09

-- 1. 员工表添加拼音字段（用于生成用户名）
ALTER TABLE employees ADD COLUMN pinyin_name VARCHAR(100);

-- 2. 创建岗位-角色映射表
CREATE TABLE IF NOT EXISTS position_role_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_keyword VARCHAR(50) NOT NULL,  -- 岗位关键词（模糊匹配）
    role_code VARCHAR(50) NOT NULL,         -- 对应角色编码
    priority INTEGER DEFAULT 0,             -- 优先级，数字越大优先级越高
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 插入默认岗位-角色映射数据
INSERT INTO position_role_mapping (position_keyword, role_code, priority) VALUES
    -- 销售序列
    ('销售总监', 'sales_director', 100),
    ('销售经理', 'sales_manager', 90),
    ('销售工程师', 'sales', 80),
    ('销售助理', 'sales_assistant', 70),

    -- 工程序列
    ('PLC工程师', 'plc_engineer', 80),
    ('测试工程师', 'test_engineer', 80),
    ('机械工程师', 'mechanical_engineer', 80),
    ('结构工程师', 'mechanical_engineer', 80),
    ('电气工程师', 'electrical_engineer', 80),
    ('软件工程师', 'software_engineer', 80),
    ('售前技术', 'presales_engineer', 80),
    ('技术开发', 'rd_engineer', 80),

    -- 生产序列
    ('装配技工', 'assembler', 70),
    ('装配钳工', 'assembler', 70),
    ('装配电工', 'assembler', 70),
    ('品质工程师', 'qa_engineer', 80),
    ('品质', 'qa', 70),
    ('生产部经理', 'production_manager', 90),
    ('制造总监', 'manufacturing_director', 100),

    -- 项目管理序列
    ('项目经理', 'pm', 90),
    ('PMC', 'pmc', 80),
    ('项目部经理', 'project_dept_manager', 95),

    -- 客服序列
    ('客服工程师', 'customer_service', 80),
    ('客服', 'customer_service', 70),

    -- 采购序列
    ('采购工程师', 'procurement_engineer', 80),
    ('采购', 'procurement', 70),

    -- 仓库序列
    ('仓库管理员', 'warehouse', 70),
    ('仓库', 'warehouse', 60),

    -- 财务序列
    ('财务经理', 'finance_manager', 90),
    ('财务', 'finance', 70),
    ('会计', 'accountant', 70),

    -- 人事序列
    ('人事经理', 'hr_manager', 90),
    ('人事', 'hr', 70),

    -- 管理层
    ('总经理', 'gm', 100),
    ('副总经理', 'vp', 95),
    ('董事长', 'chairman', 100),
    ('部门经理', 'dept_manager', 85),
    ('总监', 'director', 90);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_position_role_keyword ON position_role_mapping(position_keyword);
CREATE INDEX IF NOT EXISTS idx_position_role_code ON position_role_mapping(role_code);
