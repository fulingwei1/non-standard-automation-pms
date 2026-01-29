-- SLA Management module migration (SQLite)
-- Targets: sla_policies, sla_monitors

BEGIN;

-- SLA Policies Table
CREATE TABLE IF NOT EXISTS sla_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name VARCHAR(100) NOT NULL,
    policy_code VARCHAR(50) UNIQUE NOT NULL,
    problem_type VARCHAR(20),
    urgency VARCHAR(20),
    response_time_hours INTEGER NOT NULL,
    resolve_time_hours INTEGER NOT NULL,
    warning_threshold_percent NUMERIC(5, 2) DEFAULT 80,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    remark TEXT,
    created_by INTEGER,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_sla_policy_code ON sla_policies(policy_code);
CREATE INDEX IF NOT EXISTS idx_sla_policy_type_urgency ON sla_policies(problem_type, urgency);
CREATE INDEX IF NOT EXISTS idx_sla_policy_active ON sla_policies(is_active);

-- SLA Monitors Table
CREATE TABLE IF NOT EXISTS sla_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    policy_id INTEGER NOT NULL,
    response_deadline DATETIME NOT NULL,
    resolve_deadline DATETIME NOT NULL,
    actual_response_time DATETIME,
    actual_resolve_time DATETIME,
    response_status VARCHAR(20) DEFAULT 'ON_TIME' NOT NULL,
    resolve_status VARCHAR(20) DEFAULT 'ON_TIME' NOT NULL,
    response_time_diff_hours NUMERIC(10, 2),
    resolve_time_diff_hours NUMERIC(10, 2),
    response_warning_sent BOOLEAN DEFAULT 0,
    resolve_warning_sent BOOLEAN DEFAULT 0,
    response_warning_sent_at DATETIME,
    resolve_warning_sent_at DATETIME,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES service_tickets(id),
    FOREIGN KEY (policy_id) REFERENCES sla_policies(id)
);

CREATE INDEX IF NOT EXISTS idx_sla_monitor_ticket ON sla_monitors(ticket_id);
CREATE INDEX IF NOT EXISTS idx_sla_monitor_policy ON sla_monitors(policy_id);
CREATE INDEX IF NOT EXISTS idx_sla_monitor_response_status ON sla_monitors(response_status);
CREATE INDEX IF NOT EXISTS idx_sla_monitor_resolve_status ON sla_monitors(resolve_status);
CREATE INDEX IF NOT EXISTS idx_sla_monitor_response_deadline ON sla_monitors(response_deadline);
CREATE INDEX IF NOT EXISTS idx_sla_monitor_resolve_deadline ON sla_monitors(resolve_deadline);

COMMIT;
