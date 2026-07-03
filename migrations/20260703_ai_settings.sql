-- 管理员后台可视化配置 AI 接入（覆盖 env）
CREATE TABLE IF NOT EXISTS ai_settings (
  key VARCHAR(50) PRIMARY KEY,
  value TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_by INTEGER
);
