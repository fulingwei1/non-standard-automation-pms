-- SLA Management module migration (MySQL)
-- Targets: sla_policies, sla_monitors

START TRANSACTION;

-- SLA Policies Table
CREATE TABLE IF NOT EXISTS sla_policies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL,
    policy_code VARCHAR(50) UNIQUE NOT NULL,
    problem_type VARCHAR(20),
    urgency VARCHAR(20),
    response_time_hours INT NOT NULL,
    resolve_time_hours INT NOT NULL,
    warning_threshold_percent DECIMAL(5, 2) DEFAULT 80,
    priority INT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    remark TEXT,
    created_by INT,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_sla_policy_code (policy_code),
    INDEX idx_sla_policy_type_urgency (problem_type, urgency),
    INDEX idx_sla_policy_active (is_active),
    COMMENT 'SLA策略表'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SLA Monitors Table
CREATE TABLE IF NOT EXISTS sla_monitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    policy_id INT NOT NULL,
    response_deadline DATETIME NOT NULL,
    resolve_deadline DATETIME NOT NULL,
    actual_response_time DATETIME,
    actual_resolve_time DATETIME,
    response_status VARCHAR(20) DEFAULT 'ON_TIME' NOT NULL,
    resolve_status VARCHAR(20) DEFAULT 'ON_TIME' NOT NULL,
    response_time_diff_hours DECIMAL(10, 2),
    resolve_time_diff_hours DECIMAL(10, 2),
    response_warning_sent BOOLEAN DEFAULT FALSE,
    resolve_warning_sent BOOLEAN DEFAULT FALSE,
    response_warning_sent_at DATETIME,
    resolve_warning_sent_at DATETIME,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES service_tickets(id),
    FOREIGN KEY (policy_id) REFERENCES sla_policies(id),
    INDEX idx_sla_monitor_ticket (ticket_id),
    INDEX idx_sla_monitor_policy (policy_id),
    INDEX idx_sla_monitor_response_status (response_status),
    INDEX idx_sla_monitor_resolve_status (resolve_status),
    INDEX idx_sla_monitor_response_deadline (response_deadline),
    INDEX idx_sla_monitor_resolve_deadline (resolve_deadline),
    COMMENT 'SLA监控记录表'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMIT;
