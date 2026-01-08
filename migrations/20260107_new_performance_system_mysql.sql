-- ==========================================
-- 新绩效系统数据库迁移 - MySQL版本
-- 创建日期: 2026-01-07
-- 说明: 员工中心化绩效管理系统（月度总结+双评价）
-- ==========================================

-- ========== 1. 月度工作总结表 ==========

CREATE TABLE IF NOT EXISTS monthly_work_summary (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    employee_id INT NOT NULL COMMENT '员工ID',
    period VARCHAR(7) NOT NULL COMMENT '评价周期 (格式: YYYY-MM)',

    -- 工作总结内容（必填）
    work_content TEXT NOT NULL COMMENT '本月工作内容',
    self_evaluation TEXT NOT NULL COMMENT '自我评价',

    -- 工作总结内容（选填）
    highlights TEXT COMMENT '工作亮点',
    problems TEXT COMMENT '遇到的问题',
    next_month_plan TEXT COMMENT '下月计划',

    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态: DRAFT/SUBMITTED/EVALUATING/COMPLETED',

    -- 提交时间
    submit_date DATETIME COMMENT '提交时间',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES users(id),

    -- 唯一约束
    UNIQUE KEY uk_employee_period (employee_id, period),

    -- 索引
    INDEX idx_monthly_summary_employee (employee_id),
    INDEX idx_monthly_summary_period (period),
    INDEX idx_monthly_summary_status (status)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月度工作总结表';

-- ========== 2. 绩效评价记录表 ==========

CREATE TABLE IF NOT EXISTS performance_evaluation_record (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    summary_id INT NOT NULL COMMENT '工作总结ID',
    evaluator_id INT NOT NULL COMMENT '评价人ID',
    evaluator_type VARCHAR(20) NOT NULL COMMENT '评价人类型: DEPT_MANAGER/PROJECT_MANAGER',

    -- 项目信息（仅项目经理评价时使用）
    project_id INT COMMENT '项目ID',
    project_weight INT COMMENT '项目权重 (多项目时使用)',

    -- 评价内容
    score INT NOT NULL COMMENT '评分 (60-100)',
    comment TEXT NOT NULL COMMENT '评价意见',

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态: PENDING/COMPLETED',
    evaluated_at DATETIME COMMENT '评价时间',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 外键约束
    FOREIGN KEY (summary_id) REFERENCES monthly_work_summary(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),

    -- 约束检查
    CONSTRAINT chk_score CHECK (score >= 60 AND score <= 100),

    -- 索引
    INDEX idx_eval_record_summary (summary_id),
    INDEX idx_eval_record_evaluator (evaluator_id),
    INDEX idx_eval_record_project (project_id),
    INDEX idx_eval_record_status (status)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='绩效评价记录表';

-- ========== 3. 评价权重配置表 ==========

CREATE TABLE IF NOT EXISTS evaluation_weight_config (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    dept_manager_weight INT NOT NULL DEFAULT 50 COMMENT '部门经理权重 (%)',
    project_manager_weight INT NOT NULL DEFAULT 50 COMMENT '项目经理权重 (%)',
    effective_date DATE NOT NULL COMMENT '生效日期',
    operator_id INT NOT NULL COMMENT '操作人ID',
    reason TEXT COMMENT '调整原因',

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 外键约束
    FOREIGN KEY (operator_id) REFERENCES users(id),

    -- 约束检查
    CONSTRAINT chk_dept_weight CHECK (dept_manager_weight >= 0 AND dept_manager_weight <= 100),
    CONSTRAINT chk_project_weight CHECK (project_manager_weight >= 0 AND project_manager_weight <= 100),
    CONSTRAINT chk_total_weight CHECK (dept_manager_weight + project_manager_weight = 100),

    -- 索引
    INDEX idx_weight_config_effective_date (effective_date)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评价权重配置表';

-- ========== 初始数据 ==========

-- 插入默认权重配置（如果不存在）
INSERT IGNORE INTO evaluation_weight_config (
    dept_manager_weight,
    project_manager_weight,
    effective_date,
    operator_id,
    reason
) VALUES (
    50,
    50,
    CURDATE(),
    1, -- 假设admin用户ID为1
    '系统初始化默认配置'
);

-- ========== 完成 ==========
-- 迁移完成时间: 2026-01-07
