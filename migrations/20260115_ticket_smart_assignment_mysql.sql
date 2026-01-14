-- 工单智能分配功能迁移脚本 (MySQL)
-- 创建工单项目关联表和抄送人员表

-- 工单项目关联表（支持多对多）
CREATE TABLE IF NOT EXISTS service_ticket_projects (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ticket_id INT UNSIGNED NOT NULL COMMENT '工单ID',
    project_id INT UNSIGNED NOT NULL COMMENT '项目ID',
    is_primary TINYINT(1) DEFAULT 0 COMMENT '是否主项目',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_ticket_project (ticket_id, project_id),
    KEY idx_ticket_projects_ticket (ticket_id),
    KEY idx_ticket_projects_project (project_id),
    CONSTRAINT fk_ticket_projects_ticket FOREIGN KEY (ticket_id) REFERENCES service_tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_projects_project FOREIGN KEY (project_id) REFERENCES projects(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单项目关联表';

-- 工单抄送人员表
CREATE TABLE IF NOT EXISTS service_ticket_cc_users (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ticket_id INT UNSIGNED NOT NULL COMMENT '工单ID',
    user_id INT UNSIGNED NOT NULL COMMENT '用户ID',
    notified_at DATETIME COMMENT '通知时间',
    read_at DATETIME COMMENT '阅读时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_ticket_cc_user (ticket_id, user_id),
    KEY idx_ticket_cc_ticket (ticket_id),
    KEY idx_ticket_cc_user (user_id),
    CONSTRAINT fk_ticket_cc_ticket FOREIGN KEY (ticket_id) REFERENCES service_tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_cc_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单抄送人员表';

-- 为现有工单创建项目关联记录（将主项目添加到关联表）
INSERT INTO service_ticket_projects (ticket_id, project_id, is_primary, created_at, updated_at)
SELECT id, project_id, 1, created_at, updated_at
FROM service_tickets
WHERE project_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM service_ticket_projects 
    WHERE service_ticket_projects.ticket_id = service_tickets.id
);
