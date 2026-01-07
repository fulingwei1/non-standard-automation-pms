-- ============================================
-- 技术规格管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 技术规格要求表、规格匹配记录表
-- ============================================

-- ============================================
-- 1. 技术规格要求表
-- ============================================

CREATE TABLE IF NOT EXISTS technical_spec_requirements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    document_id         INTEGER,                              -- 关联技术规格书文档

    -- 物料信息
    material_code       VARCHAR(50),                          -- 物料编码（可选）
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500) NOT NULL,                -- 规格型号要求
    brand               VARCHAR(100),                         -- 品牌要求
    model               VARCHAR(100),                         -- 型号要求

    -- 关键参数（JSON格式，用于智能匹配）
    key_parameters      TEXT,                                -- 关键参数：电压、电流、精度、温度范围等

    -- 要求级别
    requirement_level   VARCHAR(20) DEFAULT 'REQUIRED',       -- 要求级别：REQUIRED/OPTIONAL/STRICT

    -- 备注
    remark              TEXT,                                 -- 备注说明
    extracted_by        INTEGER,                              -- 提取人

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (extracted_by) REFERENCES users(id)
);

CREATE INDEX idx_spec_req_project ON technical_spec_requirements(project_id);
CREATE INDEX idx_spec_req_document ON technical_spec_requirements(document_id);
CREATE INDEX idx_spec_req_material ON technical_spec_requirements(material_code);

-- ============================================
-- 2. 规格匹配记录表
-- ============================================

CREATE TABLE IF NOT EXISTS spec_match_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    spec_requirement_id INTEGER,                              -- 规格要求ID

    -- 匹配对象
    match_type          VARCHAR(20) NOT NULL,                  -- 匹配类型：BOM/PURCHASE_ORDER
    match_target_id     INTEGER NOT NULL,                     -- 匹配对象ID（BOM行ID或采购订单行ID）

    -- 匹配结果
    match_status        VARCHAR(20) NOT NULL,                  -- 匹配状态：MATCHED/MISMATCHED/UNKNOWN
    match_score         DECIMAL(5,2),                         -- 匹配度（0-100）

    -- 差异详情（JSON）
    differences         TEXT,                                -- 差异详情

    -- 预警
    alert_id            INTEGER,                              -- 关联预警ID

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (spec_requirement_id) REFERENCES technical_spec_requirements(id),
    FOREIGN KEY (alert_id) REFERENCES alert_records(id)
);

CREATE INDEX idx_match_record_project ON spec_match_records(project_id);
CREATE INDEX idx_match_record_spec ON spec_match_records(spec_requirement_id);
CREATE INDEX idx_match_record_type ON spec_match_records(match_type, match_target_id);
CREATE INDEX idx_match_record_status ON spec_match_records(match_status);
CREATE INDEX idx_match_record_alert ON spec_match_records(alert_id);




