-- ============================================
-- 销售模块 - 客户360 & 模板/CPQ 支撑 - SQLite 数据库迁移
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 新增CPQ规则集、报价/合同模板及版本表
-- ============================================

-- 1. CPQ 规则集表
CREATE TABLE IF NOT EXISTS cpq_rule_sets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           TEXT NOT NULL UNIQUE,
    rule_name           TEXT NOT NULL,
    description         TEXT,
    status              TEXT DEFAULT 'ACTIVE',
    base_price          REAL DEFAULT 0,
    currency            TEXT DEFAULT 'CNY',
    config_schema       TEXT,
    pricing_matrix      TEXT,
    approval_threshold  TEXT,
    visibility_scope    TEXT DEFAULT 'ALL',
    is_default          INTEGER DEFAULT 0,
    owner_role          TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cpq_rule_set_status ON cpq_rule_sets(status);
CREATE INDEX IF NOT EXISTS idx_cpq_rule_set_default ON cpq_rule_sets(is_default);

-- 2. 报价模板主表
CREATE TABLE IF NOT EXISTS quote_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       TEXT NOT NULL UNIQUE,
    template_name       TEXT NOT NULL,
    category            TEXT,
    description         TEXT,
    status              TEXT DEFAULT 'DRAFT',
    visibility_scope    TEXT DEFAULT 'TEAM',
    is_default          INTEGER DEFAULT 0,
    current_version_id  INTEGER,
    owner_id            INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_quote_template_status ON quote_templates(status);
CREATE INDEX IF NOT EXISTS idx_quote_template_scope ON quote_templates(visibility_scope);

-- 3. 报价模板版本表
CREATE TABLE IF NOT EXISTS quote_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,
    version_no          TEXT NOT NULL,
    status              TEXT DEFAULT 'DRAFT',
    sections            TEXT,
    pricing_rules       TEXT,
    config_schema       TEXT,
    discount_rules      TEXT,
    release_notes       TEXT,
    rule_set_id         INTEGER,
    created_by          INTEGER,
    published_by        INTEGER,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES quote_templates(id),
    FOREIGN KEY (rule_set_id) REFERENCES cpq_rule_sets(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_quote_template_version_unique ON quote_template_versions(template_id, version_no);
CREATE INDEX IF NOT EXISTS idx_quote_template_version_status ON quote_template_versions(status);

-- 4. 合同模板主表
CREATE TABLE IF NOT EXISTS contract_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       TEXT NOT NULL UNIQUE,
    template_name       TEXT NOT NULL,
    contract_type       TEXT,
    description         TEXT,
    status              TEXT DEFAULT 'DRAFT',
    visibility_scope    TEXT DEFAULT 'TEAM',
    is_default          INTEGER DEFAULT 0,
    current_version_id  INTEGER,
    owner_id            INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_contract_template_status ON contract_templates(status);
CREATE INDEX IF NOT EXISTS idx_contract_template_scope ON contract_templates(visibility_scope);

-- 5. 合同模板版本表
CREATE TABLE IF NOT EXISTS contract_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,
    version_no          TEXT NOT NULL,
    status              TEXT DEFAULT 'DRAFT',
    clause_sections     TEXT,
    clause_library      TEXT,
    attachment_refs     TEXT,
    approval_flow       TEXT,
    release_notes       TEXT,
    created_by          INTEGER,
    published_by        INTEGER,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES contract_templates(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_contract_template_version_unique ON contract_template_versions(template_id, version_no);
CREATE INDEX IF NOT EXISTS idx_contract_template_version_status ON contract_template_versions(status);
