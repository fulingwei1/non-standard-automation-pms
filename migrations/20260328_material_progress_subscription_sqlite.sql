-- 物料进度通知订阅表
-- 支持项目成员订阅物料齐套率变化、关键物料到货、缺料预警等通知

CREATE TABLE IF NOT EXISTS material_progress_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notify_kitting_change BOOLEAN DEFAULT 1,
    notify_key_material_arrival BOOLEAN DEFAULT 1,
    notify_shortage_alert BOOLEAN DEFAULT 1,
    kitting_change_threshold DECIMAL(5, 2) DEFAULT 5.00,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mps_project_user
    ON material_progress_subscriptions(project_id, user_id);

CREATE INDEX IF NOT EXISTS idx_mps_project
    ON material_progress_subscriptions(project_id);
