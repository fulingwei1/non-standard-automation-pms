-- 创建公司资质证书表
CREATE TABLE IF NOT EXISTS company_certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cert_name VARCHAR(200) NOT NULL,
    cert_type VARCHAR(100) NOT NULL,
    cert_number VARCHAR(100),
    issuing_authority VARCHAR(200),
    issue_date DATE,
    expiry_date DATE,
    status VARCHAR(50) DEFAULT '有效',
    description TEXT,
    scope TEXT,
    attachment_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_company_certifications_cert_name ON company_certifications(cert_name);
CREATE INDEX IF NOT EXISTS idx_company_certifications_cert_type ON company_certifications(cert_type);
CREATE INDEX IF NOT EXISTS idx_company_certifications_status ON company_certifications(status);

-- 插入示例数据
INSERT INTO company_certifications (cert_name, cert_type, cert_number, issuing_authority, issue_date, expiry_date, status, description, scope) VALUES
('ISO9001质量管理体系认证', '质量管理', 'QMS-2024-001', '中国质量认证中心', '2024-01-15', '2027-01-14', '有效', 'ISO9001:2015质量管理体系认证', '自动化测试设备的研发、生产、销售和服务'),
('高新技术企业证书', '企业资质', 'GR202444200001', '深圳市科技创新委员会', '2024-03-20', '2027-03-19', '有效', '国家高新技术企业认定', '自动化测试技术领域'),
('CE认证', '产品认证', 'CE-2024-AT-001', 'TÜV南德意志集团', '2024-05-10', '2029-05-09', '有效', '欧盟CE产品安全认证', '自动化测试设备出口欧盟'),
('ISO14001环境管理体系认证', '环境管理', 'EMS-2024-001', '中国质量认证中心', '2024-02-28', '2027-02-27', '有效', 'ISO14001:2015环境管理体系认证', '自动化测试设备的研发、生产、销售和服务'),
('专利证书-电池管理系统测试方法', '发明专利', 'ZL202410123456.7', '国家知识产权局', '2024-06-15', NULL, '有效', '电池管理系统测试方法及系统发明专利', 'BMS测试技术领域');
