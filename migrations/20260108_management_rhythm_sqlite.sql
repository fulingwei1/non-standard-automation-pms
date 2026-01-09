-- ============================================================
-- 管理节律模块 DDL - SQLite 版本
-- 创建日期：2026-01-08
-- ============================================================

-- ==================== 管理节律配置 ====================

-- 管理节律配置表
CREATE TABLE IF NOT EXISTS management_rhythm_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL,                    -- 节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    config_name VARCHAR(200) NOT NULL,                    -- 配置名称
    description TEXT,                                     -- 配置描述
    
    -- 会议模板配置(JSON)
    meeting_template TEXT,                                -- 会议模板配置(JSON)
    
    -- 关键指标清单(JSON)
    key_metrics TEXT,                                     -- 关键指标清单(JSON)
    
    -- 输出成果清单(JSON)
    output_artifacts TEXT,                                -- 输出成果清单(JSON)
    
    -- 状态
    is_active VARCHAR(10) DEFAULT 'ACTIVE',              -- 是否启用:ACTIVE/INACTIVE
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rhythm_config_level_cycle ON management_rhythm_config(rhythm_level, cycle_type);

-- ==================== 战略会议 ====================

-- 战略会议表
CREATE TABLE IF NOT EXISTS strategic_meeting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,                                    -- 项目ID(可为空表示跨项目会议)
    rhythm_config_id INTEGER,                              -- 节律配置ID
    
    -- 会议信息
    rhythm_level VARCHAR(20) NOT NULL,                     -- 会议层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    meeting_name VARCHAR(200) NOT NULL,                    -- 会议名称
    meeting_type VARCHAR(50),                              -- 会议类型
    
    -- 时间地点
    meeting_date DATE NOT NULL,                           -- 会议日期
    start_time TIME,                                      -- 开始时间
    end_time TIME,                                        -- 结束时间
    location VARCHAR(100),                                -- 会议地点
    
    -- 人员
    organizer_id INTEGER,                                  -- 组织者ID
    organizer_name VARCHAR(50),                            -- 组织者
    attendees TEXT,                                       -- 参会人员(JSON)
    
    -- 内容
    agenda TEXT,                                           -- 会议议程
    minutes TEXT,                                          -- 会议纪要
    decisions TEXT,                                        -- 会议决议
    
    -- 战略相关(JSON)
    strategic_context TEXT,                                -- 战略背景(JSON)
    strategic_structure TEXT,                              -- 五层战略结构(JSON):愿景/机会/定位/目标/路径
    key_decisions TEXT,                                    -- 关键决策(JSON)
    resource_allocation TEXT,                              -- 资源分配(JSON)
    
    -- 指标快照(JSON)
    metrics_snapshot TEXT,                                 -- 指标快照(JSON)
    
    -- 附件
    attachments TEXT,                                      -- 会议附件(JSON)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'SCHEDULED',                -- 状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (rhythm_config_id) REFERENCES management_rhythm_config(id),
    FOREIGN KEY (organizer_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_strategic_meeting_level ON strategic_meeting(rhythm_level);
CREATE INDEX IF NOT EXISTS idx_strategic_meeting_cycle ON strategic_meeting(cycle_type);
CREATE INDEX IF NOT EXISTS idx_strategic_meeting_date ON strategic_meeting(meeting_date);
CREATE INDEX IF NOT EXISTS idx_strategic_meeting_project ON strategic_meeting(project_id);

-- ==================== 会议行动项 ====================

-- 会议行动项跟踪表
CREATE TABLE IF NOT EXISTS meeting_action_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,                          -- 会议ID
    
    -- 行动项信息
    action_description TEXT NOT NULL,                      -- 行动描述
    owner_id INTEGER NOT NULL,                             -- 责任人ID
    owner_name VARCHAR(50),                                -- 责任人姓名
    
    -- 时间
    due_date DATE NOT NULL,                                -- 截止日期
    completed_date DATE,                                   -- 完成日期
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',                  -- 状态:PENDING/IN_PROGRESS/COMPLETED/OVERDUE
    
    -- 完成说明
    completion_notes TEXT,                                -- 完成说明
    
    -- 优先级
    priority VARCHAR(20) DEFAULT 'NORMAL',                  -- 优先级:LOW/NORMAL/HIGH/URGENT
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (meeting_id) REFERENCES strategic_meeting(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_action_item_meeting ON meeting_action_item(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_item_owner ON meeting_action_item(owner_id);
CREATE INDEX IF NOT EXISTS idx_action_item_status ON meeting_action_item(status);
CREATE INDEX IF NOT EXISTS idx_action_item_due_date ON meeting_action_item(due_date);

-- ==================== 节律仪表盘快照 ====================

-- 节律仪表盘快照表
CREATE TABLE IF NOT EXISTS rhythm_dashboard_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL,                      -- 节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    current_cycle VARCHAR(50),                              -- 当前周期
    
    -- 指标快照(JSON)
    key_metrics_snapshot TEXT,                            -- 关键指标快照(JSON)
    
    -- 健康状态
    health_status VARCHAR(20) DEFAULT 'GREEN',             -- 健康状态:GREEN/YELLOW/RED
    
    -- 会议信息
    last_meeting_date DATE,                                -- 上次会议日期
    next_meeting_date DATE,                                -- 下次会议日期
    meetings_count INTEGER DEFAULT 0,                     -- 本周期会议数量
    completed_meetings_count INTEGER DEFAULT 0,            -- 已完成会议数量
    
    -- 行动项统计
    total_action_items INTEGER DEFAULT 0,                  -- 总行动项数
    completed_action_items INTEGER DEFAULT 0,               -- 已完成行动项数
    overdue_action_items INTEGER DEFAULT 0,                -- 逾期行动项数
    completion_rate VARCHAR(10),                            -- 完成率(百分比)
    
    -- 快照时间
    snapshot_date DATE NOT NULL,                           -- 快照日期
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_snapshot_level_cycle ON rhythm_dashboard_snapshot(rhythm_level, cycle_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_snapshot_date ON rhythm_dashboard_snapshot(snapshot_date);
