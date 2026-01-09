-- 会议报告表
CREATE TABLE IF NOT EXISTS meeting_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_no VARCHAR(50) NOT NULL UNIQUE,
    report_type VARCHAR(20) NOT NULL,
    report_title VARCHAR(200) NOT NULL,
    period_year INTEGER NOT NULL,
    period_month INTEGER,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    rhythm_level VARCHAR(20) NOT NULL,
    report_data TEXT,
    comparison_data TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'GENERATED',
    generated_by INTEGER,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES user(id)
);

CREATE INDEX IF NOT EXISTS idx_meeting_report_type ON meeting_report(report_type);
CREATE INDEX IF NOT EXISTS idx_meeting_report_period ON meeting_report(period_year, period_month);
CREATE INDEX IF NOT EXISTS idx_meeting_report_level ON meeting_report(rhythm_level);
CREATE INDEX IF NOT EXISTS idx_meeting_report_date ON meeting_report(period_start, period_end);
