-- ============================================================
-- 项目负责人灵活配置系统 - SQLite 迁移脚本
-- 创建日期: 2026-01-08
-- 功能: 支持后台灵活配置项目角色类型，每个项目可选择启用的角色
-- ============================================================

-- 1. 项目角色类型字典表
-- 用于定义系统中所有可用的项目角色类型
CREATE TABLE IF NOT EXISTS project_role_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(50) NOT NULL UNIQUE,          -- 角色编码: PM, TECH_LEAD, PROC_LEAD, CS_LEAD
    role_name VARCHAR(100) NOT NULL,                -- 角色名称: 项目经理, 技术负责人
    role_category VARCHAR(50) DEFAULT 'GENERAL',    -- 角色分类: MANAGEMENT, TECHNICAL, SUPPORT
    description TEXT,                               -- 角色职责描述
    can_have_team BOOLEAN DEFAULT 0,                -- 是否可带团队
    is_required BOOLEAN DEFAULT 0,                  -- 是否默认必需（新项目自动启用）
    sort_order INTEGER DEFAULT 0,                   -- 排序顺序
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 项目角色配置表
-- 配置每个项目启用哪些角色
CREATE TABLE IF NOT EXISTS project_role_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_type_id INTEGER NOT NULL,                  -- 角色类型ID
    is_enabled BOOLEAN DEFAULT 1,                   -- 是否启用该角色
    is_required BOOLEAN DEFAULT 0,                  -- 是否必填（必须指定负责人）
    remark TEXT,                                    -- 配置备注
    created_by INTEGER,                             -- 创建人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (role_type_id) REFERENCES project_role_types(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE(project_id, role_type_id)
);

-- 3. 扩展 project_members 表 - 添加新字段
-- 支持角色类型关联、负责人标记、设备级分配、团队层级

-- 3.1 添加 role_type_id 字段（关联角色类型字典）
ALTER TABLE project_members ADD COLUMN role_type_id INTEGER REFERENCES project_role_types(id);

-- 3.2 添加 is_lead 字段（标记是否为该角色的负责人）
ALTER TABLE project_members ADD COLUMN is_lead BOOLEAN DEFAULT 0;

-- 3.3 添加 machine_id 字段（支持设备级成员分配）
ALTER TABLE project_members ADD COLUMN machine_id INTEGER REFERENCES machines(id);

-- 3.4 添加 lead_member_id 字段（团队成员指向其负责人）
ALTER TABLE project_members ADD COLUMN lead_member_id INTEGER REFERENCES project_members(id);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_project_role_types_category ON project_role_types(role_category);
CREATE INDEX IF NOT EXISTS idx_project_role_types_active ON project_role_types(is_active);
CREATE INDEX IF NOT EXISTS idx_project_role_configs_project ON project_role_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_project_role_configs_role ON project_role_configs(role_type_id);
CREATE INDEX IF NOT EXISTS idx_project_members_role_type ON project_members(role_type_id);
CREATE INDEX IF NOT EXISTS idx_project_members_is_lead ON project_members(is_lead);
CREATE INDEX IF NOT EXISTS idx_project_members_machine ON project_members(machine_id);
CREATE INDEX IF NOT EXISTS idx_project_members_lead ON project_members(lead_member_id);

-- 5. 预置角色类型数据
INSERT OR IGNORE INTO project_role_types (role_code, role_name, role_category, description, can_have_team, is_required, sort_order) VALUES
('PM', '项目经理', 'MANAGEMENT', '负责项目整体规划、进度管控、资源协调和客户沟通', 1, 1, 1),
('TECH_LEAD', '技术负责人', 'TECHNICAL', '负责项目整体技术方案设计和技术决策', 1, 0, 2),
('ME_LEAD', '机械负责人', 'TECHNICAL', '负责机械结构设计、工装夹具设计和机械调试', 1, 0, 3),
('EE_LEAD', '电气负责人', 'TECHNICAL', '负责电气系统设计、布线规划和电气调试', 1, 0, 4),
('SW_LEAD', '软件负责人', 'TECHNICAL', '负责控制程序开发、上位机软件和系统集成', 0, 0, 5),
('PROC_LEAD', '采购负责人', 'SUPPORT', '负责物料采购协调、供应商管理和交期跟踪', 0, 0, 6),
('CS_LEAD', '客服负责人', 'SUPPORT', '负责现场安装调试、客户培训和售后服务', 1, 0, 7),
('QA_LEAD', '质量负责人', 'SUPPORT', '负责质量管控、检验标准制定和问题跟踪', 0, 0, 8),
('PMC_LEAD', 'PMC负责人', 'SUPPORT', '负责生产计划排程、物料齐套和进度协调', 0, 0, 9),
('INSTALL_LEAD', '安装负责人', 'TECHNICAL', '负责现场设备安装、调试和验收', 1, 0, 10);

-- 6. 创建触发器更新 updated_at
CREATE TRIGGER IF NOT EXISTS update_project_role_types_timestamp
AFTER UPDATE ON project_role_types
BEGIN
    UPDATE project_role_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_project_role_configs_timestamp
AFTER UPDATE ON project_role_configs
BEGIN
    UPDATE project_role_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
