-- ============================================
-- 销售模块 - 客户360 & 模板/CPQ 支撑 - MySQL 数据库迁移
-- 版本: 1.0
-- 日期: 2026-01-07
-- 说明: 新增CPQ规则集、报价/合同模板及版本表
-- ============================================

-- ============================================
-- 1. CPQ 规则集表
-- ============================================

CREATE TABLE IF NOT EXISTS cpq_rule_sets (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    rule_code           VARCHAR(50) NOT NULL UNIQUE,
    rule_name           VARCHAR(200) NOT NULL,
    description         TEXT,
    status              VARCHAR(20) DEFAULT 'ACTIVE',
    base_price          DECIMAL(14,2) DEFAULT 0,
    currency            VARCHAR(10) DEFAULT 'CNY',
    config_schema       JSON,
    pricing_matrix      JSON,
    approval_threshold  JSON,
    visibility_scope    VARCHAR(30) DEFAULT 'ALL',
    is_default          TINYINT(1) DEFAULT 0,
    owner_role          VARCHAR(50),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CPQ规则集';

CREATE INDEX idx_cpq_rule_set_status ON cpq_rule_sets(status);
CREATE INDEX idx_cpq_rule_set_default ON cpq_rule_sets(is_default);

-- ============================================
-- 2. 报价模板主表
-- ============================================

CREATE TABLE IF NOT EXISTS quote_templates (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,
    template_name       VARCHAR(200) NOT NULL,
    category            VARCHAR(50),
    description         TEXT,
    status              VARCHAR(20) DEFAULT 'DRAFT',
    visibility_scope    VARCHAR(30) DEFAULT 'TEAM',
    is_default          TINYINT(1) DEFAULT 0,
    current_version_id  BIGINT,
    owner_id            BIGINT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_quote_template_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报价模板主表';

CREATE INDEX idx_quote_template_status ON quote_templates(status);
CREATE INDEX idx_quote_template_scope ON quote_templates(visibility_scope);

-- ============================================
-- 3. 报价模板版本表
-- ============================================

CREATE TABLE IF NOT EXISTS quote_template_versions (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_id         BIGINT NOT NULL,
    version_no          VARCHAR(20) NOT NULL,
    status              VARCHAR(20) DEFAULT 'DRAFT',
    sections            JSON,
    pricing_rules       JSON,
    config_schema       JSON,
    discount_rules      JSON,
    release_notes       TEXT,
    rule_set_id         BIGINT,
    created_by          BIGINT,
    published_by        BIGINT,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_quote_template_version_template FOREIGN KEY (template_id) REFERENCES quote_templates(id),
    CONSTRAINT fk_quote_template_version_ruleset FOREIGN KEY (rule_set_id) REFERENCES cpq_rule_sets(id),
    CONSTRAINT fk_quote_template_version_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT fk_quote_template_version_publisher FOREIGN KEY (published_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报价模板版本表';

CREATE UNIQUE INDEX idx_quote_template_version_unique ON quote_template_versions(template_id, version_no);
CREATE INDEX idx_quote_template_version_status ON quote_template_versions(status);

ALTER TABLE quote_templates
    ADD CONSTRAINT fk_quote_template_current_version
    FOREIGN KEY (current_version_id) REFERENCES quote_template_versions(id);

-- ============================================
-- 4. 合同模板主表
-- ============================================

CREATE TABLE IF NOT EXISTS contract_templates (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,
    template_name       VARCHAR(200) NOT NULL,
    contract_type       VARCHAR(50),
    description         TEXT,
    status              VARCHAR(20) DEFAULT 'DRAFT',
    visibility_scope    VARCHAR(30) DEFAULT 'TEAM',
    is_default          TINYINT(1) DEFAULT 0,
    current_version_id  BIGINT,
    owner_id            BIGINT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_contract_template_owner FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同模板主表';

CREATE INDEX idx_contract_template_status ON contract_templates(status);
CREATE INDEX idx_contract_template_scope ON contract_templates(visibility_scope);

-- ============================================
-- 5. 合同模板版本表
-- ============================================

CREATE TABLE IF NOT EXISTS contract_template_versions (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_id         BIGINT NOT NULL,
    version_no          VARCHAR(20) NOT NULL,
    status              VARCHAR(20) DEFAULT 'DRAFT',
    clause_sections     JSON,
    clause_library      JSON,
    attachment_refs     JSON,
    approval_flow       JSON,
    release_notes       TEXT,
    created_by          BIGINT,
    published_by        BIGINT,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_contract_template_version_template FOREIGN KEY (template_id) REFERENCES contract_templates(id),
    CONSTRAINT fk_contract_template_version_creator FOREIGN KEY (created_by) REFERENCES users(id),
    CONSTRAINT fk_contract_template_version_publisher FOREIGN KEY (published_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同模板版本表';

CREATE UNIQUE INDEX idx_contract_template_version_unique ON contract_template_versions(template_id, version_no);
CREATE INDEX idx_contract_template_version_status ON contract_template_versions(status);

ALTER TABLE contract_templates
    ADD CONSTRAINT fk_contract_template_current_version
    FOREIGN KEY (current_version_id) REFERENCES contract_template_versions(id);
