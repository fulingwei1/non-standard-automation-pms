-- =====================================================
-- 工程师进度管理模块 - SQLite 数据库迁移脚本
-- 日期: 2026-01-07
-- 说明: 增强 TaskUnified 模型，新增任务审批和完成证明表
-- =====================================================

-- ==================== 第一部分：扩展 task_unified 表 ====================

-- 任务审批工作流字段
ALTER TABLE task_unified ADD COLUMN approval_required BOOLEAN DEFAULT 0;
ALTER TABLE task_unified ADD COLUMN approval_status VARCHAR(20);
ALTER TABLE task_unified ADD COLUMN approved_by INTEGER;
ALTER TABLE task_unified ADD COLUMN approved_at DATETIME;
ALTER TABLE task_unified ADD COLUMN approval_note TEXT;
ALTER TABLE task_unified ADD COLUMN task_importance VARCHAR(20) DEFAULT 'GENERAL';

-- 完成证明字段
ALTER TABLE task_unified ADD COLUMN completion_note TEXT;

-- 延期管理字段
ALTER TABLE task_unified ADD COLUMN is_delayed BOOLEAN DEFAULT 0;
ALTER TABLE task_unified ADD COLUMN delay_reason TEXT;
ALTER TABLE task_unified ADD COLUMN delay_responsibility VARCHAR(100);
ALTER TABLE task_unified ADD COLUMN delay_impact_scope VARCHAR(50);
ALTER TABLE task_unified ADD COLUMN new_completion_date DATE;
ALTER TABLE task_unified ADD COLUMN delay_reported_at DATETIME;
ALTER TABLE task_unified ADD COLUMN delay_reported_by INTEGER;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_task_approval_status ON task_unified(approval_status);
CREATE INDEX IF NOT EXISTS idx_task_importance ON task_unified(task_importance);
CREATE INDEX IF NOT EXISTS idx_task_is_delayed ON task_unified(is_delayed);


-- ==================== 第二部分：创建任务审批工作流表 ====================

CREATE TABLE IF NOT EXISTS task_approval_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    submitted_by INTEGER NOT NULL,
    submitted_at DATETIME NOT NULL,
    submit_note TEXT,

    approver_id INTEGER,
    approval_status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    approval_note TEXT,
    rejection_reason TEXT,

    task_details JSON,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_taw_task_id ON task_approval_workflows(task_id);
CREATE INDEX idx_taw_approver_id ON task_approval_workflows(approver_id);
CREATE INDEX idx_taw_status ON task_approval_workflows(approval_status);
CREATE INDEX idx_taw_submitted_by ON task_approval_workflows(submitted_by);
CREATE INDEX idx_taw_submitted_at ON task_approval_workflows(submitted_at);

-- 注释（SQLite 通过表格存储元数据）
-- task_approval_workflows: 任务审批工作流表


-- ==================== 第三部分：创建任务完成证明表 ====================

CREATE TABLE IF NOT EXISTS task_completion_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,

    proof_type VARCHAR(50) NOT NULL,
    file_category VARCHAR(50),

    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    description TEXT,

    uploaded_by INTEGER NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_tcp_task_id ON task_completion_proofs(task_id);
CREATE INDEX idx_tcp_proof_type ON task_completion_proofs(proof_type);
CREATE INDEX idx_tcp_uploaded_by ON task_completion_proofs(uploaded_by);
CREATE INDEX idx_tcp_uploaded_at ON task_completion_proofs(uploaded_at);

-- 注释（SQLite 通过表格存储元数据）
-- task_completion_proofs: 任务完成证明材料表


-- ==================== 第四部分：创建触发器（自动更新 updated_at） ====================

-- task_approval_workflows 触发器
CREATE TRIGGER IF NOT EXISTS update_task_approval_workflows_timestamp
AFTER UPDATE ON task_approval_workflows
BEGIN
    UPDATE task_approval_workflows SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- task_completion_proofs 触发器
CREATE TRIGGER IF NOT EXISTS update_task_completion_proofs_timestamp
AFTER UPDATE ON task_completion_proofs
BEGIN
    UPDATE task_completion_proofs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;


-- ==================== 迁移完成 ====================
-- 说明：
-- 1. 已扩展 task_unified 表，新增 17 个字段
-- 2. 已创建 task_approval_workflows 表（任务审批工作流）
-- 3. 已创建 task_completion_proofs 表（任务完成证明材料）
-- 4. 已创建相应的索引和触发器
-- 5. 支持工程师进度管理的完整功能
