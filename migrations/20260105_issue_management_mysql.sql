-- ============================================
-- 问题管理中心模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 统一的问题管理中心，支持项目问题、任务问题、验收问题等
-- ============================================

-- ============================================
-- 1. 问题表
-- ============================================

CREATE TABLE IF NOT EXISTS issues (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    issue_no            VARCHAR(50) NOT NULL UNIQUE COMMENT '问题编号',
    category            VARCHAR(20) NOT NULL COMMENT '问题分类',
    project_id          BIGINT COMMENT '关联项目ID',
    machine_id          BIGINT COMMENT '关联机台ID',
    task_id             BIGINT COMMENT '关联任务ID',
    acceptance_order_id BIGINT COMMENT '关联验收单ID',
    related_issue_id    BIGINT COMMENT '关联问题ID（父子问题）',
    
    -- 问题基本信息
    issue_type          VARCHAR(20) NOT NULL COMMENT '问题类型',
    severity            VARCHAR(20) NOT NULL COMMENT '严重程度',
    priority            VARCHAR(20) DEFAULT 'MEDIUM' COMMENT '优先级',
    title               VARCHAR(200) NOT NULL COMMENT '问题标题',
    description         TEXT NOT NULL COMMENT '问题描述',
    
    -- 提出人信息
    reporter_id         BIGINT NOT NULL COMMENT '提出人ID',
    reporter_name       VARCHAR(50) COMMENT '提出人姓名',
    report_date         DATETIME NOT NULL COMMENT '提出时间',
    
    -- 处理人信息
    assignee_id         BIGINT COMMENT '处理负责人ID',
    assignee_name       VARCHAR(50) COMMENT '处理负责人姓名',
    due_date            DATE COMMENT '要求完成日期',
    
    -- 状态信息
    status              VARCHAR(20) DEFAULT 'OPEN' NOT NULL COMMENT '问题状态',
    
    -- 解决信息
    solution            TEXT COMMENT '解决方案',
    resolved_at         DATETIME COMMENT '解决时间',
    resolved_by         BIGINT COMMENT '解决人ID',
    resolved_by_name    VARCHAR(50) COMMENT '解决人姓名',
    
    -- 验证信息
    verified_at         DATETIME COMMENT '验证时间',
    verified_by         BIGINT COMMENT '验证人ID',
    verified_by_name    VARCHAR(50) COMMENT '验证人姓名',
    verified_result     VARCHAR(20) COMMENT '验证结果',
    
    -- 影响评估
    impact_scope        TEXT COMMENT '影响范围',
    impact_level        VARCHAR(20) COMMENT '影响级别',
    is_blocking         BOOLEAN DEFAULT FALSE COMMENT '是否阻塞',
    
    -- 附件和标签
    attachments         JSON COMMENT '附件列表',
    tags                JSON COMMENT '标签数组',
    
    -- 统计信息
    follow_up_count     INT DEFAULT 0 COMMENT '跟进次数',
    last_follow_up_at   DATETIME COMMENT '最后跟进时间',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (related_issue_id) REFERENCES issues(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    
    INDEX idx_issue_no (issue_no),
    INDEX idx_issue_category (category),
    INDEX idx_issue_project (project_id),
    INDEX idx_issue_machine (machine_id),
    INDEX idx_issue_task (task_id),
    INDEX idx_issue_status (status),
    INDEX idx_issue_severity (severity),
    INDEX idx_issue_priority (priority),
    INDEX idx_issue_assignee (assignee_id),
    INDEX idx_issue_reporter (reporter_id),
    INDEX idx_issue_blocking (is_blocking),
    INDEX idx_issue_due_date (due_date)
) COMMENT '问题表 - 统一的问题管理中心';

-- ============================================
-- 2. 问题跟进记录表（通用）
-- ============================================

CREATE TABLE IF NOT EXISTS issue_follow_up_records (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    issue_id            BIGINT NOT NULL COMMENT '问题ID',
    follow_up_type      VARCHAR(20) NOT NULL COMMENT '跟进类型',
    content             TEXT NOT NULL COMMENT '跟进内容',
    operator_id         BIGINT NOT NULL COMMENT '操作人ID',
    operator_name       VARCHAR(50) COMMENT '操作人姓名',
    old_status          VARCHAR(20) COMMENT '原状态',
    new_status          VARCHAR(20) COMMENT '新状态',
    attachments         JSON COMMENT '附件列表',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (operator_id) REFERENCES users(id),
    
    INDEX idx_follow_up_issue (issue_id),
    INDEX idx_follow_up_type (follow_up_type),
    INDEX idx_follow_up_operator (operator_id),
    INDEX idx_follow_up_created (created_at)
) COMMENT '问题跟进记录表';

