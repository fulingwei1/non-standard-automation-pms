-- ==========================================
-- 任职资格体系数据库迁移 - SQLite版本
-- 创建日期: 2026-01-07
-- 说明: 任职资格等级、岗位能力模型、员工任职资格、评估记录
-- ==========================================

-- ========== 1. 任职资格等级表 ==========

CREATE TABLE IF NOT EXISTS qualification_level (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_code VARCHAR(20) UNIQUE NOT NULL,  -- ASSISTANT/JUNIOR/MIDDLE/SENIOR/EXPERT
    level_name VARCHAR(50) NOT NULL,        -- 助理级/初级/中级/高级/专家级
    level_order INTEGER NOT NULL,           -- 排序顺序
    role_type VARCHAR(50),                  -- 适用角色类型
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_qual_level_code ON qualification_level(level_code);
CREATE INDEX IF NOT EXISTS idx_qual_level_order ON qualification_level(level_order);
CREATE INDEX IF NOT EXISTS idx_qual_level_role_type ON qualification_level(role_type);

-- ========== 2. 岗位能力模型表 ==========

CREATE TABLE IF NOT EXISTS position_competency_model (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_type VARCHAR(50) NOT NULL,    -- SALES/ENGINEER/CUSTOMER_SERVICE/WORKER
    position_subtype VARCHAR(50),            -- 子类型 (ME/EE/SW/TE等)
    level_id INTEGER NOT NULL,
    competency_dimensions TEXT NOT NULL,    -- 能力维度要求 (JSON格式)
    is_active BOOLEAN DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (level_id) REFERENCES qualification_level(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_comp_model_position ON position_competency_model(position_type, position_subtype);
CREATE INDEX IF NOT EXISTS idx_comp_model_level ON position_competency_model(level_id);
CREATE INDEX IF NOT EXISTS idx_comp_model_active ON position_competency_model(is_active);

-- ========== 3. 员工任职资格表 ==========

CREATE TABLE IF NOT EXISTS employee_qualification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    position_type VARCHAR(50) NOT NULL,
    current_level_id INTEGER NOT NULL,
    
    -- 认证信息
    certified_date DATE,
    certifier_id INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/APPROVED/EXPIRED/REVOKED
    
    -- 评估详情 (JSON格式)
    assessment_details TEXT,
    
    -- 有效期
    valid_until DATE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (current_level_id) REFERENCES qualification_level(id),
    FOREIGN KEY (certifier_id) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_emp_qual_employee ON employee_qualification(employee_id);
CREATE INDEX IF NOT EXISTS idx_emp_qual_level ON employee_qualification(current_level_id);
CREATE INDEX IF NOT EXISTS idx_emp_qual_status ON employee_qualification(status);
CREATE INDEX IF NOT EXISTS idx_emp_qual_position ON employee_qualification(position_type);

-- ========== 4. 任职资格评估记录表 ==========

CREATE TABLE IF NOT EXISTS qualification_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    qualification_id INTEGER,
    
    -- 评估信息
    assessment_period VARCHAR(20),         -- 2024-Q1
    assessment_type VARCHAR(20) NOT NULL,   -- INITIAL/PROMOTION/ANNUAL/REASSESSMENT
    
    -- 各维度得分 (JSON格式)
    scores TEXT,
    
    total_score DECIMAL(5,2),
    result VARCHAR(20),                     -- PASS/FAIL/PARTIAL
    
    -- 评估人信息
    assessor_id INTEGER,
    comments TEXT,
    assessed_at DATETIME,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (qualification_id) REFERENCES employee_qualification(id),
    FOREIGN KEY (assessor_id) REFERENCES users(id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_assess_employee ON qualification_assessment(employee_id);
CREATE INDEX IF NOT EXISTS idx_assess_qualification ON qualification_assessment(qualification_id);
CREATE INDEX IF NOT EXISTS idx_assess_period ON qualification_assessment(assessment_period);
CREATE INDEX IF NOT EXISTS idx_assess_type ON qualification_assessment(assessment_type);

-- ========== 5. 扩展绩效评价记录表 ==========

-- 在 performance_evaluation_record 表中增加任职资格相关字段
ALTER TABLE performance_evaluation_record 
ADD COLUMN qualification_level_id INTEGER REFERENCES qualification_level(id);

ALTER TABLE performance_evaluation_record 
ADD COLUMN qualification_score TEXT;  -- JSON格式的任职资格维度得分

-- 索引
CREATE INDEX IF NOT EXISTS idx_eval_record_qual_level ON performance_evaluation_record(qualification_level_id);

