-- TEN-03（全量铺开第五批，STRICT 子集）：从原第四批被误判为"系统基础设施"
-- 的表里重新审视，把真正属于"某个租户业务活动记录/审计事件"的表（进度
-- 日志、状态变更日志、AI生成任务、登录尝试等）纠正为严格租户过滤，与
-- 前几批业务实体表口径一致：全部存量数据归入默认租户（id=1 金凯博，
-- active），新增行由 before_flush 钩子自动补全。

ALTER TABLE ai_generation_jobs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ai_generation_jobs_tenant ON ai_generation_jobs(tenant_id);
UPDATE ai_generation_jobs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_delegate_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_delegate_logs_tenant ON approval_delegate_logs(tenant_id);
UPDATE approval_delegate_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE approval_action_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_approval_action_logs_tenant ON approval_action_logs(tenant_id);
UPDATE approval_action_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE ecn_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_ecn_logs_tenant ON ecn_logs(tenant_id);
UPDATE ecn_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE knowledge_reuse_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_knowledge_reuse_log_tenant ON knowledge_reuse_log(tenant_id);
UPDATE knowledge_reuse_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE login_attempts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_tenant ON login_attempts(tenant_id);
UPDATE login_attempts SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_audit_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_audit_log_tenant ON presale_ai_audit_log(tenant_id);
UPDATE presale_ai_audit_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_workflow_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_workflow_log_tenant ON presale_ai_workflow_log(tenant_id);
UPDATE presale_ai_workflow_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE presale_ai_generation_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_presale_ai_generation_log_tenant ON presale_ai_generation_log(tenant_id);
UPDATE presale_ai_generation_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE production_progress_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_production_progress_log_tenant ON production_progress_log(tenant_id);
UPDATE production_progress_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE schedule_adjustment_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_schedule_adjustment_log_tenant ON schedule_adjustment_log(tenant_id);
UPDATE schedule_adjustment_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE progress_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_progress_logs_tenant ON progress_logs(tenant_id);
UPDATE progress_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_status_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_status_logs_tenant ON project_status_logs(tenant_id);
UPDATE project_status_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE project_delivery_change_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_project_delivery_change_logs_tenant ON project_delivery_change_logs(tenant_id);
UPDATE project_delivery_change_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE funnel_transition_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_funnel_transition_logs_tenant ON funnel_transition_logs(tenant_id);
UPDATE funnel_transition_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE target_breakdown_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_target_breakdown_logs_tenant ON target_breakdown_logs(tenant_id);
UPDATE target_breakdown_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE user_sessions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_tenant ON user_sessions(tenant_id);
UPDATE user_sessions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE mat_alert_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_mat_alert_log_tenant ON mat_alert_log(tenant_id);
UPDATE mat_alert_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE hr_ai_matching_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_hr_ai_matching_log_tenant ON hr_ai_matching_log(tenant_id);
UPDATE hr_ai_matching_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE state_transition_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_state_transition_logs_tenant ON state_transition_logs(tenant_id);
UPDATE state_transition_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE task_operation_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_task_operation_log_tenant ON task_operation_log(tenant_id);
UPDATE task_operation_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE timesheet_approval_log ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_timesheet_approval_log_tenant ON timesheet_approval_log(tenant_id);
UPDATE timesheet_approval_log SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE user_2fa_backup_codes ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_user_2fa_backup_codes_tenant ON user_2fa_backup_codes(tenant_id);
UPDATE user_2fa_backup_codes SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE work_log_configs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_work_log_configs_tenant ON work_log_configs(tenant_id);
UPDATE work_log_configs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE work_log_mentions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_work_log_mentions_tenant ON work_log_mentions(tenant_id);
UPDATE work_log_mentions SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE work_logs ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_work_logs_tenant ON work_logs(tenant_id);
UPDATE work_logs SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

ALTER TABLE permission_audits ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
CREATE INDEX IF NOT EXISTS idx_permission_audits_tenant ON permission_audits(tenant_id);
UPDATE permission_audits SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active') WHERE tenant_id IS NULL;

