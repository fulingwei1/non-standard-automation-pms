-- ============================================
-- 问题管理扩展模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 问题统计快照表和问题模板表
-- ============================================

-- ============================================
-- 1. 问题统计快照表
-- ============================================

CREATE TABLE IF NOT EXISTS issue_statistics_snapshots (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_date           DATE NOT NULL COMMENT '快照日期',
    
    -- 总体统计
    total_issues            INT DEFAULT 0 COMMENT '问题总数',
    
    -- 状态统计
    open_issues             INT DEFAULT 0 COMMENT '待处理问题数',
    processing_issues       INT DEFAULT 0 COMMENT '处理中问题数',
    resolved_issues          INT DEFAULT 0 COMMENT '已解决问题数',
    closed_issues            INT DEFAULT 0 COMMENT '已关闭问题数',
    cancelled_issues         INT DEFAULT 0 COMMENT '已取消问题数',
    deferred_issues          INT DEFAULT 0 COMMENT '已延期问题数',
    
    -- 严重程度统计
    critical_issues         INT DEFAULT 0 COMMENT '严重问题数',
    major_issues            INT DEFAULT 0 COMMENT '重大问题数',
    minor_issues            INT DEFAULT 0 COMMENT '轻微问题数',
    
    -- 优先级统计
    urgent_issues           INT DEFAULT 0 COMMENT '紧急问题数',
    high_priority_issues     INT DEFAULT 0 COMMENT '高优先级问题数',
    medium_priority_issues  INT DEFAULT 0 COMMENT '中优先级问题数',
    low_priority_issues      INT DEFAULT 0 COMMENT '低优先级问题数',
    
    -- 类型统计
    defect_issues           INT DEFAULT 0 COMMENT '缺陷问题数',
    risk_issues             INT DEFAULT 0 COMMENT '风险问题数',
    blocker_issues          INT DEFAULT 0 COMMENT '阻塞问题数',
    
    -- 特殊统计
    blocking_issues          INT DEFAULT 0 COMMENT '阻塞问题数（is_blocking=True）',
    overdue_issues           INT DEFAULT 0 COMMENT '逾期问题数',
    
    -- 分类统计
    project_issues          INT DEFAULT 0 COMMENT '项目问题数',
    task_issues             INT DEFAULT 0 COMMENT '任务问题数',
    acceptance_issues       INT DEFAULT 0 COMMENT '验收问题数',
    
    -- 处理时间统计（小时）
    avg_response_time        DECIMAL(10, 2) DEFAULT 0 COMMENT '平均响应时间',
    avg_resolve_time         DECIMAL(10, 2) DEFAULT 0 COMMENT '平均解决时间',
    avg_verify_time          DECIMAL(10, 2) DEFAULT 0 COMMENT '平均验证时间',
    
    -- 分布数据（JSON格式）
    status_distribution      JSON COMMENT '状态分布(JSON)',
    severity_distribution    JSON COMMENT '严重程度分布(JSON)',
    priority_distribution    JSON COMMENT '优先级分布(JSON)',
    category_distribution    JSON COMMENT '分类分布(JSON)',
    project_distribution     JSON COMMENT '项目分布(JSON)',
    
    -- 趋势数据
    new_issues_today         INT DEFAULT 0 COMMENT '今日新增问题数',
    resolved_today           INT DEFAULT 0 COMMENT '今日解决问题数',
    closed_today             INT DEFAULT 0 COMMENT '今日关闭问题数',
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_snapshot_date (snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问题统计快照表';

-- ============================================
-- 2. 问题模板表
-- ============================================

CREATE TABLE IF NOT EXISTS issue_templates (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    template_name            VARCHAR(100) NOT NULL COMMENT '模板名称',
    template_code            VARCHAR(50) NOT NULL UNIQUE COMMENT '模板编码',
    
    -- 模板分类
    category                VARCHAR(20) NOT NULL COMMENT '问题分类',
    issue_type              VARCHAR(20) NOT NULL COMMENT '问题类型',
    
    -- 默认值
    default_severity         VARCHAR(20) COMMENT '默认严重程度',
    default_priority         VARCHAR(20) DEFAULT 'MEDIUM' COMMENT '默认优先级',
    default_impact_level     VARCHAR(20) COMMENT '默认影响级别',
    
    -- 模板内容
    title_template          VARCHAR(200) NOT NULL COMMENT '标题模板（支持变量）',
    description_template    TEXT COMMENT '描述模板（支持变量）',
    solution_template       TEXT COMMENT '解决方案模板（支持变量）',
    
    -- 默认字段
    default_tags            JSON COMMENT '默认标签JSON数组',
    default_impact_scope     TEXT COMMENT '默认影响范围',
    default_is_blocking      TINYINT(1) DEFAULT 0 COMMENT '默认是否阻塞',
    
    -- 使用统计
    usage_count             INT DEFAULT 0 COMMENT '使用次数',
    last_used_at            DATETIME COMMENT '最后使用时间',
    
    -- 状态
    is_active               TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    
    -- 备注
    remark                  TEXT COMMENT '备注说明',
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_template_code (template_code),
    INDEX idx_template_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问题模板表';



