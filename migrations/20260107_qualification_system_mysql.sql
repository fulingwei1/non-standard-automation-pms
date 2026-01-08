-- ==========================================
-- 任职资格体系数据库迁移 - MySQL版本
-- 创建日期: 2026-01-07
-- 说明: 任职资格等级、岗位能力模型、员工任职资格、评估记录
-- ==========================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ========== 1. 任职资格等级表 ==========

CREATE TABLE IF NOT EXISTS qualification_level (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level_code VARCHAR(20) UNIQUE NOT NULL COMMENT '等级编码 (ASSISTANT/JUNIOR/MIDDLE/SENIOR/EXPERT)',
    level_name VARCHAR(50) NOT NULL COMMENT '等级名称 (助理级/初级/中级/高级/专家级)',
    level_order INT NOT NULL COMMENT '排序顺序',
    role_type VARCHAR(50) COMMENT '适用角色类型',
    description TEXT COMMENT '等级描述',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_qual_level_code (level_code),
    INDEX idx_qual_level_order (level_order),
    INDEX idx_qual_level_role_type (role_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任职资格等级表';

-- ========== 2. 岗位能力模型表 ==========

CREATE TABLE IF NOT EXISTS position_competency_model (
    id INT AUTO_INCREMENT PRIMARY KEY,
    position_type VARCHAR(50) NOT NULL COMMENT '岗位类型',
    position_subtype VARCHAR(50) COMMENT '岗位子类型 (ME/EE/SW/TE等)',
    level_id INT NOT NULL COMMENT '等级ID',
    competency_dimensions JSON NOT NULL COMMENT '能力维度要求 (JSON格式)',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (level_id) REFERENCES qualification_level(id) ON DELETE RESTRICT,
    INDEX idx_comp_model_position (position_type, position_subtype),
    INDEX idx_comp_model_level (level_id),
    INDEX idx_comp_model_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='岗位能力模型表';

-- ========== 3. 员工任职资格表 ==========

CREATE TABLE IF NOT EXISTS employee_qualification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL COMMENT '员工ID',
    position_type VARCHAR(50) NOT NULL COMMENT '岗位类型',
    current_level_id INT NOT NULL COMMENT '当前等级ID',
    
    -- 认证信息
    certified_date DATE COMMENT '认证日期',
    certifier_id INT COMMENT '认证人ID',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '认证状态',
    
    -- 评估详情 (JSON格式)
    assessment_details JSON COMMENT '能力评估详情',
    
    -- 有效期
    valid_until DATE COMMENT '有效期至',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT,
    FOREIGN KEY (current_level_id) REFERENCES qualification_level(id) ON DELETE RESTRICT,
    FOREIGN KEY (certifier_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_emp_qual_employee (employee_id),
    INDEX idx_emp_qual_level (current_level_id),
    INDEX idx_emp_qual_status (status),
    INDEX idx_emp_qual_position (position_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='员工任职资格表';

-- ========== 4. 任职资格评估记录表 ==========

CREATE TABLE IF NOT EXISTS qualification_assessment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL COMMENT '员工ID',
    qualification_id INT COMMENT '任职资格ID',
    
    -- 评估信息
    assessment_period VARCHAR(20) COMMENT '评估周期 (如: 2024-Q1)',
    assessment_type VARCHAR(20) NOT NULL COMMENT '评估类型',
    
    -- 各维度得分 (JSON格式)
    scores JSON COMMENT '各维度得分',
    
    total_score DECIMAL(5,2) COMMENT '综合得分',
    result VARCHAR(20) COMMENT '评估结果',
    
    -- 评估人信息
    assessor_id INT COMMENT '评估人ID',
    comments TEXT COMMENT '评估意见',
    assessed_at DATETIME COMMENT '评估时间',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT,
    FOREIGN KEY (qualification_id) REFERENCES employee_qualification(id) ON DELETE SET NULL,
    FOREIGN KEY (assessor_id) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_assess_employee (employee_id),
    INDEX idx_assess_qualification (qualification_id),
    INDEX idx_assess_period (assessment_period),
    INDEX idx_assess_type (assessment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任职资格评估记录表';

-- ========== 5. 扩展绩效评价记录表 ==========

-- 在 performance_evaluation_record 表中增加任职资格相关字段
ALTER TABLE performance_evaluation_record 
ADD COLUMN qualification_level_id INT COMMENT '任职资格等级ID' AFTER project_weight,
ADD COLUMN qualification_score JSON COMMENT '任职资格维度得分 (JSON格式)' AFTER qualification_level_id,
ADD INDEX idx_eval_record_qual_level (qualification_level_id),
ADD FOREIGN KEY (qualification_level_id) REFERENCES qualification_level(id) ON DELETE SET NULL;

SET FOREIGN_KEY_CHECKS = 1;

