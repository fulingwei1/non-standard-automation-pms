-- 售前方案协作表（方案迭代版本链 + 状态机）
CREATE TABLE IF NOT EXISTS presale_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    requirement_text TEXT NOT NULL,
    current_solution JSON,
    status VARCHAR(20) DEFAULT 'draft',
    metric_id INTEGER,
    created_by INTEGER,
    created_by_name VARCHAR(100),
    reviewed_by INTEGER,
    reviewed_by_name VARCHAR(100),
    reviewed_at DATETIME,
    review_comment TEXT,
    version_count INTEGER DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_proposal_status ON presale_proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposal_created_by ON presale_proposals(created_by);
CREATE INDEX IF NOT EXISTS idx_proposal_created_at ON presale_proposals(created_at);

CREATE TABLE IF NOT EXISTS presale_proposal_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    change_request TEXT,
    changes_summary TEXT,
    solution JSON,
    operated_by INTEGER,
    operated_by_name VARCHAR(100),
    operation VARCHAR(20),
    created_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_ppv_proposal ON presale_proposal_versions(proposal_id);
