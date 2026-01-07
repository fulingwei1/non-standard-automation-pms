-- ============================================
-- 问题管理扩展模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 问题统计快照表和问题模板表
-- ============================================

-- ============================================
-- 1. 问题统计快照表
-- ============================================

CREATE TABLE IF NOT EXISTS issue_statistics_snapshots (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date           DATE NOT NULL,                      -- 快照日期
    
    -- 总体统计
    total_issues            INTEGER DEFAULT 0,                  -- 问题总数
    
    -- 状态统计
    open_issues             INTEGER DEFAULT 0,                  -- 待处理问题数
    processing_issues       INTEGER DEFAULT 0,                  -- 处理中问题数
    resolved_issues          INTEGER DEFAULT 0,                  -- 已解决问题数
    closed_issues            INTEGER DEFAULT 0,                  -- 已关闭问题数
    cancelled_issues         INTEGER DEFAULT 0,                  -- 已取消问题数
    deferred_issues          INTEGER DEFAULT 0,                  -- 已延期问题数
    
    -- 严重程度统计
    critical_issues         INTEGER DEFAULT 0,                  -- 严重问题数
    major_issues            INTEGER DEFAULT 0,                  -- 重大问题数
    minor_issues            INTEGER DEFAULT 0,                  -- 轻微问题数
    
    -- 优先级统计
    urgent_issues           INTEGER DEFAULT 0,                  -- 紧急问题数
    high_priority_issues     INTEGER DEFAULT 0,                  -- 高优先级问题数
    medium_priority_issues  INTEGER DEFAULT 0,                  -- 中优先级问题数
    low_priority_issues      INTEGER DEFAULT 0,                  -- 低优先级问题数
    
    -- 类型统计
    defect_issues           INTEGER DEFAULT 0,                  -- 缺陷问题数
    risk_issues             INTEGER DEFAULT 0,                  -- 风险问题数
    blocker_issues          INTEGER DEFAULT 0,                  -- 阻塞问题数
    
    -- 特殊统计
    blocking_issues          INTEGER DEFAULT 0,                  -- 阻塞问题数（is_blocking=True）
    overdue_issues           INTEGER DEFAULT 0,                  -- 逾期问题数
    
    -- 分类统计
    project_issues          INTEGER DEFAULT 0,                  -- 项目问题数
    task_issues             INTEGER DEFAULT 0,                  -- 任务问题数
    acceptance_issues       INTEGER DEFAULT 0,                  -- 验收问题数
    
    -- 处理时间统计（小时）
    avg_response_time        NUMERIC(10, 2) DEFAULT 0,          -- 平均响应时间
    avg_resolve_time         NUMERIC(10, 2) DEFAULT 0,          -- 平均解决时间
    avg_verify_time          NUMERIC(10, 2) DEFAULT 0,          -- 平均验证时间
    
    -- 分布数据（JSON格式）
    status_distribution      TEXT,                               -- 状态分布(JSON)
    severity_distribution    TEXT,                               -- 严重程度分布(JSON)
    priority_distribution    TEXT,                               -- 优先级分布(JSON)
    category_distribution    TEXT,                               -- 分类分布(JSON)
    project_distribution     TEXT,                               -- 项目分布(JSON)
    
    -- 趋势数据
    new_issues_today         INTEGER DEFAULT 0,                  -- 今日新增问题数
    resolved_today           INTEGER DEFAULT 0,                  -- 今日解决问题数
    closed_today             INTEGER DEFAULT 0,                  -- 今日关闭问题数
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_snapshot_date ON issue_statistics_snapshots(snapshot_date);

-- ============================================
-- 2. 问题模板表
-- ============================================

CREATE TABLE IF NOT EXISTS issue_templates (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name            VARCHAR(100) NOT NULL,              -- 模板名称
    template_code            VARCHAR(50) NOT NULL UNIQUE,        -- 模板编码
    
    -- 模板分类
    category                VARCHAR(20) NOT NULL,                -- 问题分类
    issue_type              VARCHAR(20) NOT NULL,                -- 问题类型
    
    -- 默认值
    default_severity         VARCHAR(20),                         -- 默认严重程度
    default_priority         VARCHAR(20) DEFAULT 'MEDIUM',       -- 默认优先级
    default_impact_level     VARCHAR(20),                         -- 默认影响级别
    
    -- 模板内容
    title_template          VARCHAR(200) NOT NULL,              -- 标题模板（支持变量）
    description_template    TEXT,                                -- 描述模板（支持变量）
    solution_template       TEXT,                                -- 解决方案模板（支持变量）
    
    -- 默认字段
    default_tags            TEXT,                                -- 默认标签JSON数组
    default_impact_scope     TEXT,                                -- 默认影响范围
    default_is_blocking      BOOLEAN DEFAULT 0,                   -- 默认是否阻塞
    
    -- 使用统计
    usage_count             INTEGER DEFAULT 0,                    -- 使用次数
    last_used_at            DATETIME,                            -- 最后使用时间
    
    -- 状态
    is_active               BOOLEAN DEFAULT 1,                   -- 是否启用
    
    -- 备注
    remark                  TEXT,                                -- 备注说明
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_template_code ON issue_templates(template_code);
CREATE INDEX idx_template_category ON issue_templates(category);



