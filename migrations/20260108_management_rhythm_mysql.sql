-- ============================================================
-- 管理节律模块 DDL - MySQL 版本
-- 创建日期：2026-01-08
-- ============================================================

-- ==================== 管理节律配置 ====================

-- 管理节律配置表
CREATE TABLE IF NOT EXISTS management_rhythm_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL COMMENT '节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK',
    cycle_type VARCHAR(20) NOT NULL COMMENT '周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY',
    config_name VARCHAR(200) NOT NULL COMMENT '配置名称',
    description TEXT COMMENT '配置描述',
    
    -- 会议模板配置(JSON)
    meeting_template JSON COMMENT '会议模板配置(JSON)',
    
    -- 关键指标清单(JSON)
    key_metrics JSON COMMENT '关键指标清单(JSON)',
    
    -- 输出成果清单(JSON)
    output_artifacts JSON COMMENT '输出成果清单(JSON)',
    
    -- 状态
    is_active VARCHAR(10) DEFAULT 'ACTIVE' COMMENT '是否启用:ACTIVE/INACTIVE',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_rhythm_config_level_cycle (rhythm_level, cycle_type)
) COMMENT '管理节律配置表';

-- ==================== 战略会议 ====================

-- 战略会议表
CREATE TABLE IF NOT EXISTS strategic_meeting (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT COMMENT '项目ID(可为空表示跨项目会议)',
    rhythm_config_id BIGINT COMMENT '节律配置ID',
    
    -- 会议信息
    rhythm_level VARCHAR(20) NOT NULL COMMENT '会议层级:STRATEGIC/OPERATIONAL/OPERATION/TASK',
    cycle_type VARCHAR(20) NOT NULL COMMENT '周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY',
    meeting_name VARCHAR(200) NOT NULL COMMENT '会议名称',
    meeting_type VARCHAR(50) COMMENT '会议类型',
    
    -- 时间地点
    meeting_date DATE NOT NULL COMMENT '会议日期',
    start_time TIME COMMENT '开始时间',
    end_time TIME COMMENT '结束时间',
    location VARCHAR(100) COMMENT '会议地点',
    
    -- 人员
    organizer_id BIGINT COMMENT '组织者ID',
    organizer_name VARCHAR(50) COMMENT '组织者',
    attendees JSON COMMENT '参会人员(JSON)',
    
    -- 内容
    agenda TEXT COMMENT '会议议程',
    minutes TEXT COMMENT '会议纪要',
    decisions TEXT COMMENT '会议决议',
    
    -- 战略相关(JSON)
    strategic_context JSON COMMENT '战略背景(JSON)',
    strategic_structure JSON COMMENT '五层战略结构(JSON):愿景/机会/定位/目标/路径',
    key_decisions JSON COMMENT '关键决策(JSON)',
    resource_allocation JSON COMMENT '资源分配(JSON)',
    
    -- 指标快照(JSON)
    metrics_snapshot JSON COMMENT '指标快照(JSON)',
    
    -- 附件
    attachments JSON COMMENT '会议附件(JSON)',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'SCHEDULED' COMMENT '状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (rhythm_config_id) REFERENCES management_rhythm_config(id),
    FOREIGN KEY (organizer_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    
    INDEX idx_strategic_meeting_level (rhythm_level),
    INDEX idx_strategic_meeting_cycle (cycle_type),
    INDEX idx_strategic_meeting_date (meeting_date),
    INDEX idx_strategic_meeting_project (project_id)
) COMMENT '战略会议表';

-- ==================== 会议行动项 ====================

-- 会议行动项跟踪表
CREATE TABLE IF NOT EXISTS meeting_action_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    meeting_id BIGINT NOT NULL COMMENT '会议ID',
    
    -- 行动项信息
    action_description TEXT NOT NULL COMMENT '行动描述',
    owner_id BIGINT NOT NULL COMMENT '责任人ID',
    owner_name VARCHAR(50) COMMENT '责任人姓名',
    
    -- 时间
    due_date DATE NOT NULL COMMENT '截止日期',
    completed_date DATE COMMENT '完成日期',
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态:PENDING/IN_PROGRESS/COMPLETED/OVERDUE',
    
    -- 完成说明
    completion_notes TEXT COMMENT '完成说明',
    
    -- 优先级
    priority VARCHAR(20) DEFAULT 'NORMAL' COMMENT '优先级:LOW/NORMAL/HIGH/URGENT',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (meeting_id) REFERENCES strategic_meeting(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    
    INDEX idx_action_item_meeting (meeting_id),
    INDEX idx_action_item_owner (owner_id),
    INDEX idx_action_item_status (status),
    INDEX idx_action_item_due_date (due_date)
) COMMENT '会议行动项跟踪表';

-- ==================== 节律仪表盘快照 ====================

-- 节律仪表盘快照表
CREATE TABLE IF NOT EXISTS rhythm_dashboard_snapshot (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL COMMENT '节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK',
    cycle_type VARCHAR(20) NOT NULL COMMENT '周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY',
    current_cycle VARCHAR(50) COMMENT '当前周期',
    
    -- 指标快照(JSON)
    key_metrics_snapshot JSON COMMENT '关键指标快照(JSON)',
    
    -- 健康状态
    health_status VARCHAR(20) DEFAULT 'GREEN' COMMENT '健康状态:GREEN/YELLOW/RED',
    
    -- 会议信息
    last_meeting_date DATE COMMENT '上次会议日期',
    next_meeting_date DATE COMMENT '下次会议日期',
    meetings_count INT DEFAULT 0 COMMENT '本周期会议数量',
    completed_meetings_count INT DEFAULT 0 COMMENT '已完成会议数量',
    
    -- 行动项统计
    total_action_items INT DEFAULT 0 COMMENT '总行动项数',
    completed_action_items INT DEFAULT 0 COMMENT '已完成行动项数',
    overdue_action_items INT DEFAULT 0 COMMENT '逾期行动项数',
    completion_rate VARCHAR(10) COMMENT '完成率(百分比)',
    
    -- 快照时间
    snapshot_date DATE NOT NULL COMMENT '快照日期',
    
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES user(id),
    
    INDEX idx_dashboard_snapshot_level_cycle (rhythm_level, cycle_type),
    INDEX idx_dashboard_snapshot_date (snapshot_date)
) COMMENT '节律仪表盘快照表';
