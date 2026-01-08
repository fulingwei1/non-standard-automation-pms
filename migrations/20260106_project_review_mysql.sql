-- ============================================
-- 项目复盘模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 项目复盘报告、经验教训、最佳实践
-- 适用场景：项目结项后的复盘总结、经验沉淀、知识复用
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 项目复盘报告表
-- ============================================

CREATE TABLE IF NOT EXISTS project_reviews (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    review_no           VARCHAR(50) NOT NULL UNIQUE COMMENT '复盘编号',
    project_id          BIGINT NOT NULL COMMENT '项目ID',
    project_code        VARCHAR(50) NOT NULL COMMENT '项目编号',
    
    -- 复盘信息
    review_date         DATE NOT NULL COMMENT '复盘日期',
    review_type         VARCHAR(20) DEFAULT 'POST_MORTEM' COMMENT '复盘类型：POST_MORTEM/MID_TERM/QUARTERLY（结项复盘/中期复盘/季度复盘）',
    
    -- 项目周期对比
    plan_duration       INT COMMENT '计划工期(天)',
    actual_duration     INT COMMENT '实际工期(天)',
    schedule_variance   INT COMMENT '进度偏差(天)',
    
    -- 成本对比
    budget_amount       DECIMAL(12,2) COMMENT '预算金额',
    actual_cost         DECIMAL(12,2) COMMENT '实际成本',
    cost_variance       DECIMAL(12,2) COMMENT '成本偏差',
    
    -- 质量指标
    quality_issues      INT DEFAULT 0 COMMENT '质量问题数',
    change_count        INT DEFAULT 0 COMMENT '变更次数',
    customer_satisfaction INT COMMENT '客户满意度1-5',
    
    -- 复盘内容
    success_factors     TEXT COMMENT '成功因素',
    problems            TEXT COMMENT '问题与教训',
    improvements        TEXT COMMENT '改进建议',
    best_practices      TEXT COMMENT '最佳实践',
    conclusion          TEXT COMMENT '复盘结论',
    
    -- 参与人
    reviewer_id         BIGINT NOT NULL COMMENT '复盘负责人ID',
    reviewer_name       VARCHAR(50) NOT NULL COMMENT '复盘负责人',
    participants        JSON COMMENT '参与人ID列表',
    participant_names   VARCHAR(500) COMMENT '参与人姓名（逗号分隔）',
    
    -- 附件
    attachment_ids      JSON COMMENT '附件ID列表',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/PUBLISHED/ARCHIVED',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id),
    
    INDEX idx_project_review_project (project_id),
    INDEX idx_project_review_date (review_date),
    INDEX idx_project_review_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目复盘报告表';

-- ============================================
-- 2. 项目经验教训表
-- ============================================

CREATE TABLE IF NOT EXISTS project_lessons (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    review_id           BIGINT NOT NULL COMMENT '复盘报告ID',
    project_id          BIGINT NOT NULL COMMENT '项目ID',
    
    -- 经验教训信息
    lesson_type         VARCHAR(20) NOT NULL COMMENT '类型：SUCCESS/FAILURE（成功经验/失败教训）',
    title               VARCHAR(200) NOT NULL COMMENT '标题',
    description         TEXT NOT NULL COMMENT '问题/经验描述',
    
    -- 根因分析
    root_cause          TEXT COMMENT '根本原因',
    impact              TEXT COMMENT '影响范围',
    
    -- 改进措施
    improvement_action  TEXT COMMENT '改进措施',
    responsible_person  VARCHAR(50) COMMENT '责任人',
    due_date            DATE COMMENT '完成日期',
    
    -- 分类标签
    category            VARCHAR(50) COMMENT '分类：进度/成本/质量/沟通/技术/管理',
    tags                JSON COMMENT '标签列表',
    
    -- 优先级
    priority            VARCHAR(10) DEFAULT 'MEDIUM' COMMENT '优先级：LOW/MEDIUM/HIGH',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'OPEN' COMMENT '状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED',
    resolved_date       DATE COMMENT '解决日期',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    
    INDEX idx_project_lesson_review (review_id),
    INDEX idx_project_lesson_project (project_id),
    INDEX idx_project_lesson_type (lesson_type),
    INDEX idx_project_lesson_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目经验教训表';

-- ============================================
-- 3. 项目最佳实践表
-- ============================================

CREATE TABLE IF NOT EXISTS project_best_practices (
    id                          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    review_id                   BIGINT NOT NULL COMMENT '复盘报告ID',
    project_id                  BIGINT NOT NULL COMMENT '项目ID',
    
    -- 最佳实践信息
    title                       VARCHAR(200) NOT NULL COMMENT '标题',
    description                 TEXT NOT NULL COMMENT '实践描述',
    context                     TEXT COMMENT '适用场景',
    implementation              TEXT COMMENT '实施方法',
    benefits                    TEXT COMMENT '带来的收益',
    
    -- 分类标签
    category                    VARCHAR(50) COMMENT '分类：流程/工具/技术/管理/沟通',
    tags                        JSON COMMENT '标签列表',
    
    -- 可复用性
    is_reusable                 BOOLEAN DEFAULT TRUE COMMENT '是否可复用',
    applicable_project_types    JSON COMMENT '适用项目类型列表',
    applicable_stages           JSON COMMENT '适用阶段列表（S1-S9）',
    
    -- 验证信息
    validation_status           VARCHAR(20) DEFAULT 'PENDING' COMMENT '验证状态：PENDING/VALIDATED/REJECTED',
    validation_date             DATE COMMENT '验证日期',
    validated_by                BIGINT COMMENT '验证人ID',
    
    -- 复用统计
    reuse_count                 INT DEFAULT 0 COMMENT '复用次数',
    last_reused_at              DATETIME COMMENT '最后复用时间',
    
    -- 状态
    status                      VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE/ARCHIVED',
    
    created_at                  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at                  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (validated_by) REFERENCES users(id),
    
    INDEX idx_project_bp_review (review_id),
    INDEX idx_project_bp_project (project_id),
    INDEX idx_project_bp_category (category),
    INDEX idx_project_bp_reusable (is_reusable),
    INDEX idx_project_bp_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目最佳实践表';

SET FOREIGN_KEY_CHECKS = 1;












