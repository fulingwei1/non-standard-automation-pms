-- ============================================================
-- 项目负责人灵活配置系统 - MySQL 迁移脚本
-- 创建日期: 2026-01-08
-- 功能: 支持后台灵活配置项目角色类型，每个项目可选择启用的角色
-- ============================================================

-- 1. 项目角色类型字典表
CREATE TABLE IF NOT EXISTS project_role_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_code VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    role_name VARCHAR(100) NOT NULL COMMENT '角色名称',
    role_category VARCHAR(50) DEFAULT 'GENERAL' COMMENT '角色分类: MANAGEMENT, TECHNICAL, SUPPORT',
    description TEXT COMMENT '角色职责描述',
    can_have_team BOOLEAN DEFAULT FALSE COMMENT '是否可带团队',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否默认必需',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (role_category),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目角色类型字典表';

-- 2. 项目角色配置表
CREATE TABLE IF NOT EXISTS project_role_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL COMMENT '项目ID',
    role_type_id INT NOT NULL COMMENT '角色类型ID',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用该角色',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    remark TEXT COMMENT '配置备注',
    created_by INT COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (role_type_id) REFERENCES project_role_types(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY uk_project_role (project_id, role_type_id),
    INDEX idx_project (project_id),
    INDEX idx_role (role_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目角色配置表';

-- 3. 扩展 project_members 表
ALTER TABLE project_members
ADD COLUMN role_type_id INT COMMENT '角色类型ID',
ADD COLUMN is_lead BOOLEAN DEFAULT FALSE COMMENT '是否负责人',
ADD COLUMN machine_id INT COMMENT '设备ID（设备级分配）',
ADD COLUMN lead_member_id INT COMMENT '所属负责人ID',
ADD CONSTRAINT fk_pm_role_type FOREIGN KEY (role_type_id) REFERENCES project_role_types(id),
ADD CONSTRAINT fk_pm_machine FOREIGN KEY (machine_id) REFERENCES machines(id),
ADD CONSTRAINT fk_pm_lead FOREIGN KEY (lead_member_id) REFERENCES project_members(id),
ADD INDEX idx_pm_role_type (role_type_id),
ADD INDEX idx_pm_is_lead (is_lead),
ADD INDEX idx_pm_machine (machine_id),
ADD INDEX idx_pm_lead (lead_member_id);

-- 4. 预置角色类型数据
INSERT INTO project_role_types (role_code, role_name, role_category, description, can_have_team, is_required, sort_order) VALUES
('PM', '项目经理', 'MANAGEMENT', '负责项目整体规划、进度管控、资源协调和客户沟通', TRUE, TRUE, 1),
('TECH_LEAD', '技术负责人', 'TECHNICAL', '负责项目整体技术方案设计和技术决策', TRUE, FALSE, 2),
('ME_LEAD', '机械负责人', 'TECHNICAL', '负责机械结构设计、工装夹具设计和机械调试', TRUE, FALSE, 3),
('EE_LEAD', '电气负责人', 'TECHNICAL', '负责电气系统设计、布线规划和电气调试', TRUE, FALSE, 4),
('SW_LEAD', '软件负责人', 'TECHNICAL', '负责控制程序开发、上位机软件和系统集成', FALSE, FALSE, 5),
('PROC_LEAD', '采购负责人', 'SUPPORT', '负责物料采购协调、供应商管理和交期跟踪', FALSE, FALSE, 6),
('CS_LEAD', '客服负责人', 'SUPPORT', '负责现场安装调试、客户培训和售后服务', TRUE, FALSE, 7),
('QA_LEAD', '质量负责人', 'SUPPORT', '负责质量管控、检验标准制定和问题跟踪', FALSE, FALSE, 8),
('PMC_LEAD', 'PMC负责人', 'SUPPORT', '负责生产计划排程、物料齐套和进度协调', FALSE, FALSE, 9),
('INSTALL_LEAD', '安装负责人', 'TECHNICAL', '负责现场设备安装、调试和验收', TRUE, FALSE, 10)
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);
