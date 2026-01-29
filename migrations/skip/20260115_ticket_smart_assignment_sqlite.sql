-- 工单智能分配功能迁移脚本 (SQLite)
-- 创建工单项目关联表和抄送人员表

BEGIN;

-- 工单项目关联表（支持多对多）
CREATE TABLE IF NOT EXISTS service_ticket_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ticket_id) REFERENCES service_tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(ticket_id, project_id)
);

CREATE INDEX IF NOT EXISTS idx_ticket_projects_ticket ON service_ticket_projects(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_projects_project ON service_ticket_projects(project_id);

-- 工单抄送人员表
CREATE TABLE IF NOT EXISTS service_ticket_cc_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notified_at DATETIME,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ticket_id) REFERENCES service_tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(ticket_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ticket_cc_ticket ON service_ticket_cc_users(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_cc_user ON service_ticket_cc_users(user_id);

-- 为现有工单创建项目关联记录（将主项目添加到关联表）
INSERT INTO service_ticket_projects (ticket_id, project_id, is_primary, created_at, updated_at)
SELECT id, project_id, 1, created_at, updated_at
FROM service_tickets
WHERE project_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM service_ticket_projects 
    WHERE service_ticket_projects.ticket_id = service_tickets.id
);

COMMIT;
