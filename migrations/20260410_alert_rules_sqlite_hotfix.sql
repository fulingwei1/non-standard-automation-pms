-- ============================================
-- Alert rules SQLite schema hotfix
-- 日期: 2026-04-10
-- 说明: 为历史 SQLite 库补齐 alert_rules.enforcement_mode
-- 备注: is_active 已在多数历史库中存在，运行期补丁也会兜底；本热修复避免手工执行时被 duplicate column 卡住
-- ============================================

ALTER TABLE alert_rules ADD COLUMN enforcement_mode VARCHAR(20) DEFAULT 'WARN';

UPDATE alert_rules SET enforcement_mode = 'WARN' WHERE enforcement_mode IS NULL;
