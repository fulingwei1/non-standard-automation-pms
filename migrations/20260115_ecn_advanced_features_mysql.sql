-- ECN高级功能扩展 - MySQL版本
-- 添加BOM影响分析、责任分摊、RCA分析等功能

-- 1. 扩展EcnAffectedMaterial表，添加BOM影响范围和呆滞料相关字段
ALTER TABLE ecn_affected_materials 
ADD COLUMN bom_impact_scope JSON COMMENT 'BOM影响范围，包含受影响的BOM项和设备',
ADD COLUMN is_obsolete_risk BOOLEAN DEFAULT FALSE COMMENT '是否呆滞料风险',
ADD COLUMN obsolete_risk_level VARCHAR(20) COMMENT '呆滞料风险级别：LOW/MEDIUM/HIGH/CRITICAL',
ADD COLUMN obsolete_quantity NUMERIC(10, 4) COMMENT '呆滞料数量',
ADD COLUMN obsolete_cost NUMERIC(14, 2) COMMENT '呆滞料成本',
ADD COLUMN obsolete_analysis TEXT COMMENT '呆滞料分析说明';

-- 2. 扩展Ecn表，添加RCA分析和解决方案字段
ALTER TABLE ecn 
ADD COLUMN root_cause VARCHAR(20) COMMENT '根本原因类型',
ADD COLUMN root_cause_analysis TEXT COMMENT 'RCA分析内容',
ADD COLUMN root_cause_category VARCHAR(50) COMMENT '原因分类',
ADD COLUMN solution TEXT COMMENT '解决方案',
ADD COLUMN solution_template_id INTEGER COMMENT '使用的解决方案模板ID',
ADD COLUMN similar_ecn_ids JSON COMMENT '相似ECN ID列表',
ADD COLUMN solution_source VARCHAR(20) COMMENT '解决方案来源：MANUAL/AUTO_EXTRACT/KNOWLEDGE_BASE';

-- 3. 创建ECN BOM影响分析表
CREATE TABLE IF NOT EXISTS ecn_bom_impacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ecn_id INT NOT NULL COMMENT 'ECN ID',
    bom_version_id INT COMMENT 'BOM版本ID',
    machine_id INT COMMENT '设备ID',
    project_id INT COMMENT '项目ID',
    affected_item_count INT DEFAULT 0 COMMENT '受影响物料项数',
    total_cost_impact NUMERIC(14, 2) DEFAULT 0 COMMENT '总成本影响',
    schedule_impact_days INT DEFAULT 0 COMMENT '交期影响天数',
    impact_analysis JSON COMMENT '影响分析详情',
    analysis_status VARCHAR(20) DEFAULT 'PENDING' COMMENT '分析状态：PENDING/ANALYZING/COMPLETED/FAILED',
    analyzed_at DATETIME COMMENT '分析时间',
    analyzed_by INT COMMENT '分析人ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id) ON DELETE CASCADE,
    FOREIGN KEY (bom_version_id) REFERENCES bom_headers(id) ON DELETE SET NULL,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (analyzed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_bom_impact_ecn (ecn_id),
    INDEX idx_bom_impact_bom (bom_version_id),
    INDEX idx_bom_impact_machine (machine_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ECN BOM影响分析表';

-- 4. 创建ECN责任分摊表
CREATE TABLE IF NOT EXISTS ecn_responsibilities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ecn_id INT NOT NULL COMMENT 'ECN ID',
    dept VARCHAR(50) NOT NULL COMMENT '责任部门',
    responsibility_ratio NUMERIC(5, 2) DEFAULT 0 COMMENT '责任比例(0-100)',
    responsibility_type VARCHAR(20) DEFAULT 'PRIMARY' COMMENT '责任类型：PRIMARY/SECONDARY/SUPPORT',
    cost_allocation NUMERIC(14, 2) DEFAULT 0 COMMENT '成本分摊金额',
    impact_description TEXT COMMENT '影响描述',
    responsibility_scope TEXT COMMENT '责任范围',
    confirmed BOOLEAN DEFAULT FALSE COMMENT '是否已确认',
    confirmed_by INT COMMENT '确认人ID',
    confirmed_at DATETIME COMMENT '确认时间',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_resp_ecn (ecn_id),
    INDEX idx_resp_dept (dept)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ECN责任分摊表';
