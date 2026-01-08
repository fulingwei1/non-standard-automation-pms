-- ECN知识库功能扩展 - MySQL版本
-- 添加解决方案模板表

-- 创建ECN解决方案模板表
CREATE TABLE IF NOT EXISTS ecn_solution_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_code VARCHAR(50) UNIQUE NOT NULL COMMENT '模板编码',
    template_name VARCHAR(200) NOT NULL COMMENT '模板名称',
    template_category VARCHAR(50) COMMENT '模板分类',
    ecn_type VARCHAR(20) COMMENT '适用的ECN类型',
    root_cause_category VARCHAR(50) COMMENT '适用的根本原因分类',
    keywords JSON COMMENT '关键词列表（用于匹配）',
    solution_description TEXT NOT NULL COMMENT '解决方案描述',
    solution_steps JSON COMMENT '解决步骤（JSON数组）',
    required_resources JSON COMMENT '所需资源（JSON数组）',
    estimated_cost NUMERIC(14, 2) COMMENT '预估成本',
    estimated_days INT COMMENT '预估天数',
    success_rate NUMERIC(5, 2) DEFAULT 0 COMMENT '成功率（0-100）',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    avg_cost_saving NUMERIC(14, 2) COMMENT '平均成本节省',
    avg_time_saving INT COMMENT '平均时间节省（天）',
    source_ecn_id INT COMMENT '来源ECN ID',
    created_from VARCHAR(20) DEFAULT 'MANUAL' COMMENT '创建来源：MANUAL/AUTO_EXTRACT',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已验证',
    verified_by INT COMMENT '验证人ID',
    verified_at DATETIME COMMENT '验证时间',
    remark TEXT COMMENT '备注',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_ecn_id) REFERENCES ecn(id) ON DELETE SET NULL,
    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_solution_template_type (ecn_type),
    INDEX idx_solution_template_category (template_category),
    INDEX idx_solution_template_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ECN解决方案模板表';
