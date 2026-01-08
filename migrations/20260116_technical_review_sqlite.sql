-- ============================================
-- 技术评审管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-16
-- 说明: 技术评审主表、评审参与人、评审材料、评审检查项记录、评审问题
-- ============================================

-- ============================================
-- 1. 技术评审主表
-- ============================================

CREATE TABLE IF NOT EXISTS technical_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_no           VARCHAR(50) NOT NULL UNIQUE,              -- 评审编号：RV-PDR-202501-0001
    review_type         VARCHAR(20) NOT NULL,                      -- 评审类型：PDR/DDR/PRR/FRR/ARR
    review_name         VARCHAR(200) NOT NULL,                     -- 评审名称
    
    -- 关联项目
    project_id          INTEGER NOT NULL,                          -- 关联项目ID
    project_no          VARCHAR(50) NOT NULL,                      -- 项目编号
    equipment_id        INTEGER,                                   -- 关联设备ID（多设备项目）
    
    -- 评审基本信息
    status              VARCHAR(20) NOT NULL DEFAULT 'DRAFT',     -- 状态：draft/pending/in_progress/completed/cancelled
    scheduled_date      DATETIME NOT NULL,                         -- 计划评审时间
    actual_date         DATETIME,                                  -- 实际评审时间
    location            VARCHAR(200),                               -- 评审地点
    meeting_type        VARCHAR(20) NOT NULL DEFAULT 'ONSITE',     -- 会议形式：onsite/online/hybrid
    
    -- 评审人员
    host_id             INTEGER NOT NULL,                          -- 主持人ID
    presenter_id        INTEGER NOT NULL,                           -- 汇报人ID
    recorder_id         INTEGER NOT NULL,                          -- 记录人ID
    
    -- 评审结论
    conclusion          VARCHAR(30),                              -- 评审结论：pass/pass_with_condition/reject/abort
    conclusion_summary  TEXT,                                      -- 结论说明
    condition_deadline  DATE,                                      -- 有条件通过的整改期限
    next_review_date    DATE,                                      -- 下次复审日期
    
    -- 问题统计
    issue_count_a       INTEGER DEFAULT 0,                         -- A类问题数
    issue_count_b       INTEGER DEFAULT 0,                         -- B类问题数
    issue_count_c       INTEGER DEFAULT 0,                         -- C类问题数
    issue_count_d       INTEGER DEFAULT 0,                          -- D类问题数
    
    -- 创建人
    created_by          INTEGER NOT NULL,                          -- 创建人
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (equipment_id) REFERENCES machines(id),
    FOREIGN KEY (host_id) REFERENCES users(id),
    FOREIGN KEY (presenter_id) REFERENCES users(id),
    FOREIGN KEY (recorder_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_review_no ON technical_reviews(review_no);
CREATE INDEX idx_review_project ON technical_reviews(project_id);
CREATE INDEX idx_review_type ON technical_reviews(review_type);
CREATE INDEX idx_review_status ON technical_reviews(status);
CREATE INDEX idx_review_scheduled_date ON technical_reviews(scheduled_date);

-- ============================================
-- 2. 评审参与人表
-- ============================================

CREATE TABLE IF NOT EXISTS review_participants (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    user_id             INTEGER NOT NULL,                          -- 用户ID
    role                VARCHAR(20) NOT NULL,                      -- 角色：host/expert/presenter/recorder/observer
    is_required         BOOLEAN NOT NULL DEFAULT 1,                -- 是否必须参与
    
    -- 出席信息
    attendance          VARCHAR(20),                              -- 出席状态：pending/confirmed/absent/delegated
    delegate_id         INTEGER,                                   -- 代理人ID（请假时）
    sign_time           DATETIME,                                  -- 签到时间
    signature           VARCHAR(500),                              -- 电子签名
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (delegate_id) REFERENCES users(id)
);

CREATE INDEX idx_participant_review ON review_participants(review_id);
CREATE INDEX idx_participant_user ON review_participants(user_id);
CREATE INDEX idx_participant_role ON review_participants(role);

-- ============================================
-- 3. 评审材料表
-- ============================================

CREATE TABLE IF NOT EXISTS review_materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    material_type       VARCHAR(20) NOT NULL,                      -- 材料类型：drawing/bom/report/document/other
    material_name       VARCHAR(200) NOT NULL,                     -- 材料名称
    file_path           VARCHAR(500) NOT NULL,                     -- 文件路径
    file_size           BIGINT NOT NULL,                           -- 文件大小（字节）
    version             VARCHAR(20),                               -- 版本号
    is_required         BOOLEAN NOT NULL DEFAULT 1,                -- 是否必须材料
    upload_by           INTEGER NOT NULL,                          -- 上传人
    upload_at           DATETIME DEFAULT CURRENT_TIMESTAMP,        -- 上传时间
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_by) REFERENCES users(id)
);

CREATE INDEX idx_material_review ON review_materials(review_id);
CREATE INDEX idx_material_type ON review_materials(material_type);

-- ============================================
-- 4. 评审检查项记录表
-- ============================================

CREATE TABLE IF NOT EXISTS review_checklist_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    checklist_item_id  INTEGER,                                  -- 检查项ID（关联模板，可为空）
    category            VARCHAR(50) NOT NULL,                      -- 检查类别
    check_item          VARCHAR(500) NOT NULL,                     -- 检查项内容
    result              VARCHAR(20) NOT NULL,                      -- 检查结果：pass/fail/na
    
    -- 问题信息（不通过时）
    issue_level         VARCHAR(10),                               -- 问题等级：A/B/C/D（不通过时）
    issue_desc          TEXT,                                      -- 问题描述
    issue_id            INTEGER,                                   -- 关联问题ID（自动创建的问题）
    
    checker_id          INTEGER NOT NULL,                         -- 检查人ID
    remark              VARCHAR(500),                              -- 备注
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (issue_id) REFERENCES review_issues(id),
    FOREIGN KEY (checker_id) REFERENCES users(id)
);

CREATE INDEX idx_checklist_review ON review_checklist_records(review_id);
CREATE INDEX idx_checklist_result ON review_checklist_records(result);

-- ============================================
-- 5. 评审问题表
-- ============================================

CREATE TABLE IF NOT EXISTS review_issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    issue_no            VARCHAR(50) NOT NULL UNIQUE,                -- 问题编号：RV-ISSUE-202501-0001
    issue_level         VARCHAR(10) NOT NULL,                      -- 问题等级：A/B/C/D
    category            VARCHAR(50) NOT NULL,                       -- 问题类别
    description         TEXT NOT NULL,                             -- 问题描述
    suggestion          TEXT,                                      -- 改进建议
    
    -- 责任与期限
    assignee_id         INTEGER NOT NULL,                          -- 责任人ID
    deadline            DATE NOT NULL,                              -- 整改期限
    
    -- 状态与处理
    status              VARCHAR(20) NOT NULL DEFAULT 'OPEN',        -- 状态：open/processing/resolved/verified/closed
    solution            TEXT,                                      -- 解决方案
    
    -- 验证信息
    verify_result       VARCHAR(20),                               -- 验证结果：pass/fail
    verifier_id         INTEGER,                                   -- 验证人
    verify_time         DATETIME,                                  -- 验证时间
    
    -- 关联
    linked_issue_id     INTEGER,                                   -- 关联问题管理系统ID
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (verifier_id) REFERENCES users(id)
);

CREATE INDEX idx_issue_no ON review_issues(issue_no);
CREATE INDEX idx_issue_review ON review_issues(review_id);
CREATE INDEX idx_issue_level ON review_issues(issue_level);
CREATE INDEX idx_issue_status ON review_issues(status);
CREATE INDEX idx_issue_assignee ON review_issues(assignee_id);
CREATE INDEX idx_issue_deadline ON review_issues(deadline);






