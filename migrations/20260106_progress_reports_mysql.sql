-- Progress reports table migration (MySQL)
-- Add progress_reports table for daily/weekly progress reports

CREATE TABLE IF NOT EXISTS progress_reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_type VARCHAR(20) NOT NULL COMMENT '报告类型：daily/weekly',
    report_date DATE NOT NULL COMMENT '报告日期',
    
    -- 关联信息（三选一或组合）
    project_id BIGINT COMMENT '项目ID',
    machine_id BIGINT COMMENT '机台ID',
    task_id BIGINT COMMENT '任务ID',
    
    -- 报告内容
    content TEXT NOT NULL COMMENT '报告内容',
    completed_work TEXT COMMENT '已完成工作',
    planned_work TEXT COMMENT '计划工作',
    issues TEXT COMMENT '问题与阻塞',
    next_plan TEXT COMMENT '下一步计划',
    
    -- 创建人
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    
    INDEX idx_progress_reports_project (project_id),
    INDEX idx_progress_reports_machine (machine_id),
    INDEX idx_progress_reports_task (task_id),
    INDEX idx_progress_reports_date (report_date),
    INDEX idx_progress_reports_type (report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='进度报告表';


