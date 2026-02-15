-- 客户画像分析表
CREATE TABLE IF NOT EXISTS presale_customer_profile (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    presale_ticket_id INT,
    customer_type ENUM('technical', 'commercial', 'decision_maker', 'mixed') NOT NULL,
    focus_points JSON,
    decision_style ENUM('rational', 'emotional', 'authoritative') NOT NULL,
    communication_notes TEXT,
    ai_analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_presale_ticket_id (presale_ticket_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 话术推荐记录表
CREATE TABLE IF NOT EXISTS presale_ai_sales_script (
    id INT PRIMARY KEY AUTO_INCREMENT,
    presale_ticket_id INT NOT NULL,
    scenario ENUM('first_contact', 'needs_discovery', 'solution_presentation', 'price_negotiation', 'objection_handling', 'closing') NOT NULL,
    customer_profile_id INT,
    recommended_scripts JSON,
    objection_type VARCHAR(100),
    response_strategy TEXT,
    success_case_references JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_presale_ticket_id (presale_ticket_id),
    INDEX idx_scenario (scenario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 话术模板库
CREATE TABLE IF NOT EXISTS sales_script_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scenario ENUM('first_contact', 'needs_discovery', 'solution_presentation', 'price_negotiation', 'objection_handling', 'closing') NOT NULL,
    customer_type VARCHAR(50),
    script_content TEXT NOT NULL,
    tags JSON,
    success_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_scenario (scenario),
    INDEX idx_customer_type (customer_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
