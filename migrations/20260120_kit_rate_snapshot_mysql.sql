-- 齐套率历史快照表 (MySQL)
-- 用于记录项目/机台每日的齐套率状态，支持历史趋势分析

CREATE TABLE IF NOT EXISTS mes_kit_rate_snapshot (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- 快照对象
    project_id INT NOT NULL COMMENT '项目ID',
    machine_id INT COMMENT '机台ID（可选，不填则为项目级快照）',

    -- 快照时间
    snapshot_date DATE NOT NULL COMMENT '快照日期',
    snapshot_time DATETIME NOT NULL COMMENT '快照精确时间',

    -- 快照来源
    snapshot_type VARCHAR(20) NOT NULL DEFAULT 'DAILY' COMMENT '快照类型：DAILY/STAGE_CHANGE/MANUAL',
    trigger_event VARCHAR(100) COMMENT '触发事件（如：S3->S4阶段切换）',

    -- 齐套率数据
    kit_rate DECIMAL(5,2) NOT NULL DEFAULT 0 COMMENT '齐套率(%)',
    kit_status VARCHAR(20) NOT NULL DEFAULT 'shortage' COMMENT '齐套状态：complete/partial/shortage',

    -- 物料统计
    total_items INT DEFAULT 0 COMMENT 'BOM物料总项数',
    fulfilled_items INT DEFAULT 0 COMMENT '已齐套项数',
    shortage_items INT DEFAULT 0 COMMENT '缺料项数',
    in_transit_items INT DEFAULT 0 COMMENT '在途项数',

    -- 阻塞性物料统计
    blocking_total INT DEFAULT 0 COMMENT '阻塞性物料总数',
    blocking_fulfilled INT DEFAULT 0 COMMENT '阻塞性已齐套数',
    blocking_kit_rate DECIMAL(5,2) DEFAULT 0 COMMENT '阻塞性齐套率(%)',

    -- 金额统计
    total_amount DECIMAL(14,2) DEFAULT 0 COMMENT '物料总金额',
    shortage_amount DECIMAL(14,2) DEFAULT 0 COMMENT '缺料金额',

    -- 项目阶段信息
    project_stage VARCHAR(20) COMMENT '项目当前阶段',
    project_health VARCHAR(10) COMMENT '项目健康度',

    -- 分阶段齐套率
    stage_kit_rates TEXT COMMENT '各装配阶段齐套率JSON',

    -- 外键
    CONSTRAINT fk_kit_snapshot_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_kit_snapshot_machine FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE SET NULL,

    -- 索引
    INDEX idx_kit_snapshot_project_date (project_id, snapshot_date),
    INDEX idx_kit_snapshot_machine_date (machine_id, snapshot_date),
    INDEX idx_kit_snapshot_type (snapshot_type),
    INDEX idx_kit_snapshot_date (snapshot_date),
    INDEX idx_kit_snapshot_project_time (project_id, snapshot_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='齐套率历史快照表';
