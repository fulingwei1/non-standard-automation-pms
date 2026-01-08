-- =====================================================
-- 工程师进度管理模块 - MySQL 数据库迁移脚本
-- 日期: 2026-01-07
-- 说明: 增强 TaskUnified 模型，新增任务审批和完成证明表
-- =====================================================

-- ==================== 第一部分：扩展 task_unified 表 ====================

-- 任务审批工作流字段
ALTER TABLE task_unified ADD COLUMN approval_required BOOLEAN DEFAULT FALSE COMMENT '是否需要审批';
ALTER TABLE task_unified ADD COLUMN approval_status VARCHAR(20) COMMENT '审批状态：PENDING_APPROVAL/APPROVED/REJECTED';
ALTER TABLE task_unified ADD COLUMN approved_by INT COMMENT '审批人ID';
ALTER TABLE task_unified ADD COLUMN approved_at DATETIME COMMENT '审批时间';
ALTER TABLE task_unified ADD COLUMN approval_note TEXT COMMENT '审批意见';
ALTER TABLE task_unified ADD COLUMN task_importance VARCHAR(20) DEFAULT 'GENERAL' COMMENT '任务重要性：IMPORTANT/GENERAL';

-- 完成证明字段
ALTER TABLE task_unified ADD COLUMN completion_note TEXT COMMENT '完成说明';

-- 延期管理字段
ALTER TABLE task_unified ADD COLUMN is_delayed BOOLEAN DEFAULT FALSE COMMENT '是否延期';
ALTER TABLE task_unified ADD COLUMN delay_reason TEXT COMMENT '延期原因';
ALTER TABLE task_unified ADD COLUMN delay_responsibility VARCHAR(100) COMMENT '延期责任归属';
ALTER TABLE task_unified ADD COLUMN delay_impact_scope VARCHAR(50) COMMENT '延期影响范围：LOCAL/PROJECT/MULTI_PROJECT';
ALTER TABLE task_unified ADD COLUMN new_completion_date DATE COMMENT '新的预计完成日期';
ALTER TABLE task_unified ADD COLUMN delay_reported_at DATETIME COMMENT '延期上报时间';
ALTER TABLE task_unified ADD COLUMN delay_reported_by INT COMMENT '延期上报人ID';

-- 添加外键约束
ALTER TABLE task_unified ADD CONSTRAINT fk_task_approved_by
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE task_unified ADD CONSTRAINT fk_task_delay_reported_by
    FOREIGN KEY (delay_reported_by) REFERENCES users(id) ON DELETE SET NULL;

-- 创建索引
CREATE INDEX idx_task_approval_status ON task_unified(approval_status);
CREATE INDEX idx_task_importance ON task_unified(task_importance);
CREATE INDEX idx_task_is_delayed ON task_unified(is_delayed);


-- ==================== 第二部分：创建任务审批工作流表 ====================

CREATE TABLE IF NOT EXISTS task_approval_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    task_id INT NOT NULL COMMENT '任务ID',
    submitted_by INT NOT NULL COMMENT '提交人ID',
    submitted_at DATETIME NOT NULL COMMENT '提交时间',
    submit_note TEXT COMMENT '提交说明（任务必要性）',

    approver_id INT COMMENT '审批人ID',
    approval_status VARCHAR(20) DEFAULT 'PENDING' COMMENT '审批状态：PENDING/APPROVED/REJECTED',
    approved_at DATETIME COMMENT '审批时间',
    approval_note TEXT COMMENT '审批意见',
    rejection_reason TEXT COMMENT '拒绝原因',

    task_details JSON COMMENT '任务详情快照',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_taw_task_id FOREIGN KEY (task_id) REFERENCES task_unified(id) ON DELETE CASCADE,
    CONSTRAINT fk_taw_submitted_by FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_taw_approver_id FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务审批工作流表';

-- 创建索引
CREATE INDEX idx_taw_task_id ON task_approval_workflows(task_id);
CREATE INDEX idx_taw_approver_id ON task_approval_workflows(approver_id);
CREATE INDEX idx_taw_status ON task_approval_workflows(approval_status);
CREATE INDEX idx_taw_submitted_by ON task_approval_workflows(submitted_by);
CREATE INDEX idx_taw_submitted_at ON task_approval_workflows(submitted_at);


-- ==================== 第三部分：创建任务完成证明表 ====================

CREATE TABLE IF NOT EXISTS task_completion_proofs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    task_id INT NOT NULL COMMENT '任务ID',

    proof_type VARCHAR(50) NOT NULL COMMENT '证明类型：DOCUMENT/PHOTO/VIDEO/TEST_REPORT/DATA',
    file_category VARCHAR(50) COMMENT '文件分类：DRAWING/SPEC/CALCULATION/SITE_PHOTO/TEST_VIDEO等',

    file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
    file_name VARCHAR(200) NOT NULL COMMENT '文件名',
    file_size INT COMMENT '文件大小(字节)',
    file_type VARCHAR(50) COMMENT '文件类型(扩展名)',
    description TEXT COMMENT '文件说明',

    uploaded_by INT NOT NULL COMMENT '上传人ID',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    CONSTRAINT fk_tcp_task_id FOREIGN KEY (task_id) REFERENCES task_unified(id) ON DELETE CASCADE,
    CONSTRAINT fk_tcp_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务完成证明材料表';

-- 创建索引
CREATE INDEX idx_tcp_task_id ON task_completion_proofs(task_id);
CREATE INDEX idx_tcp_proof_type ON task_completion_proofs(proof_type);
CREATE INDEX idx_tcp_uploaded_by ON task_completion_proofs(uploaded_by);
CREATE INDEX idx_tcp_uploaded_at ON task_completion_proofs(uploaded_at);


-- ==================== 迁移完成 ====================
-- 说明：
-- 1. 已扩展 task_unified 表，新增 17 个字段
-- 2. 已创建 task_approval_workflows 表（任务审批工作流）
-- 3. 已创建 task_completion_proofs 表（任务完成证明材料）
-- 4. 已创建相应的索引和外键约束
-- 5. 支持工程师进度管理的完整功能
-- 6. MySQL 支持 ON UPDATE CURRENT_TIMESTAMP 自动更新时间戳
