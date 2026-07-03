-- M1: 标准模块库（AI从历史BOM挖出的可复用模块，支撑配置式设计/模块级报价）
CREATE TABLE IF NOT EXISTS ai_standard_modules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module_name VARCHAR(100) NOT NULL,
  category VARCHAR(50),
  description TEXT,
  typical_components JSON,
  ref_cost DECIMAL(14,2),
  source_count INTEGER DEFAULT 1,
  created_by INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_module_name ON ai_standard_modules(module_name);
