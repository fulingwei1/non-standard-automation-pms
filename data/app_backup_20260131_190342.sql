PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code VARCHAR(10) UNIQUE NOT NULL,     -- E0001
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50),                        -- 机械部/电气部/PMC
    role VARCHAR(50),                              -- 机械工程师/调试工程师
    phone VARCHAR(20),
    wechat_userid VARCHAR(50),                     -- 企业微信UserID
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, id_card VARCHAR(18), pinyin_name VARCHAR(100), employment_status VARCHAR(20) DEFAULT 'active', employment_type VARCHAR(20) DEFAULT 'full_time');
INSERT INTO employees VALUES(1,'E0001','董事长','董事会','董事长',NULL,NULL,1,'2026-01-28 06:48:15','2026-01-28 15:00:32.046404',NULL,NULL,'active','full_time');
INSERT INTO employees VALUES(2,'E0002','总经理','总经理办公室','总经理',NULL,NULL,1,'2026-01-28 15:00:32.050750','2026-01-28 15:00:32.050752',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(3,'E0003','项目经理','技术中心','项目经理',NULL,NULL,1,'2026-01-28 15:00:32.060145','2026-01-28 15:00:32.060145',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(4,'E0005','销售总监','销售部','销售总监',NULL,NULL,1,'2026-01-28 15:00:32.070634','2026-01-28 15:00:32.070636',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(5,'E0006','销售经理','销售部','销售经理',NULL,NULL,1,'2026-01-28 15:00:32.085618','2026-01-28 15:00:32.085620',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(6,'E0004','P&C','计划部','计划管理',NULL,NULL,1,'2026-01-28 15:00:32.100832','2026-01-28 15:00:32.100835',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(7,'E0007','机械部经理','机械部','机械部经理',NULL,NULL,1,'2026-01-28 15:00:32.118094','2026-01-28 15:00:32.118097',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(8,'E1001','郑汝才','高层管理','常务副总',NULL,NULL,1,'2026-01-28 15:01:48.171433','2026-01-28 15:01:48.171437',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(9,'E1002','骆奕兴','高层管理','副总经理',NULL,NULL,1,'2026-01-28 15:01:48.182739','2026-01-28 15:01:48.182741',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(10,'E1003','符凌维','高层管理','副总经理（董秘）',NULL,NULL,1,'2026-01-28 15:01:48.192225','2026-01-28 15:01:48.192226',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(11,'E1004','宋魁','营销中心','营销中心总监',NULL,NULL,1,'2026-01-28 15:01:48.201464','2026-01-28 15:01:48.201464',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(12,'E1005','郑琴','营销中心','销售经理',NULL,NULL,1,'2026-01-28 15:01:48.214327','2026-01-28 15:01:48.214329',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(13,'E1006','姚洪','营销中心','销售工程师',NULL,NULL,1,'2026-01-28 15:01:48.224390','2026-01-28 15:01:48.224392',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(14,'E1007','常雄','生产管理中心','PMC主管',NULL,NULL,1,'2026-01-28 15:01:48.233929','2026-01-28 15:01:48.233931',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(15,'E1008','高勇','生产部','生产部经理',NULL,NULL,1,'2026-01-28 15:01:48.242485','2026-01-28 15:01:48.242486',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(16,'E1009','陈亮','项目管理部','项目管理部总监',NULL,NULL,1,'2026-01-28 15:01:48.251377','2026-01-28 15:01:48.251378',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(17,'E1010','谭章斌','项目管理部','项目经理',NULL,NULL,1,'2026-01-28 15:01:48.259877','2026-01-28 15:01:48.259878',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(18,'E1011','于振华','技术部','经理',NULL,NULL,1,'2026-01-28 15:01:48.268769','2026-01-28 15:01:48.268770',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(19,'E1012','王俊','质量部','经理',NULL,NULL,1,'2026-01-28 15:01:48.277556','2026-01-28 15:01:48.277557',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(20,'E1013','王志红','客服部','客服主管',NULL,NULL,1,'2026-01-28 15:01:48.287277','2026-01-28 15:01:48.287278',NULL,NULL,'active','regular');
INSERT INTO employees VALUES(21,'EMP-PROJECTS','Project.Smoke','Smoke Test Dept','PM',NULL,NULL,1,'2026-01-30 11:42:15.482893','2026-01-30 11:42:15.483002',NULL,NULL,'active','regular');
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_type VARCHAR(20),  -- RECEIVE/PAY
    status VARCHAR(20) DEFAULT 'PENDING',
    payment_date DATE,
    payer_name VARCHAR(100),
    payee_name VARCHAR(100),
    bank_account VARCHAR(100),
    transaction_no VARCHAR(100),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, contract_id INTEGER, milestone_id INTEGER, deliverable_id INTEGER, invoice_id INTEGER, responsible_id INTEGER, due_date DATE);
CREATE TABLE holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    holiday_type VARCHAR(20) NOT NULL,  -- HOLIDAY: 法定节假日, WORKDAY: 调休工作日, COMPANY: 公司假期
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO holidays VALUES(1,'2025-01-01',2025,'HOLIDAY','元旦','新年元旦',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(2,'2025-01-28',2025,'HOLIDAY','春节','除夕',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(3,'2025-01-29',2025,'HOLIDAY','春节','春节第一天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(4,'2025-01-30',2025,'HOLIDAY','春节','春节第二天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(5,'2025-01-31',2025,'HOLIDAY','春节','春节第三天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(6,'2025-02-01',2025,'HOLIDAY','春节','春节第四天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(7,'2025-02-02',2025,'HOLIDAY','春节','春节第五天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(8,'2025-02-03',2025,'HOLIDAY','春节','春节第六天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(9,'2025-02-04',2025,'HOLIDAY','春节','春节第七天',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(10,'2025-01-26',2025,'WORKDAY','春节调休','周日调休上班',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(11,'2025-02-08',2025,'WORKDAY','春节调休','周六调休上班',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(12,'2025-04-04',2025,'HOLIDAY','清明节','清明节',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(13,'2025-04-05',2025,'HOLIDAY','清明节','清明节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(14,'2025-04-06',2025,'HOLIDAY','清明节','清明节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(15,'2025-05-01',2025,'HOLIDAY','劳动节','国际劳动节',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(16,'2025-05-02',2025,'HOLIDAY','劳动节','劳动节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(17,'2025-05-03',2025,'HOLIDAY','劳动节','劳动节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(18,'2025-05-04',2025,'HOLIDAY','劳动节','劳动节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(19,'2025-05-05',2025,'HOLIDAY','劳动节','劳动节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(20,'2025-04-27',2025,'WORKDAY','劳动节调休','周日调休上班',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(21,'2025-05-31',2025,'HOLIDAY','端午节','端午节',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(22,'2025-06-01',2025,'HOLIDAY','端午节','端午节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(23,'2025-06-02',2025,'HOLIDAY','端午节','端午节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(24,'2025-10-06',2025,'HOLIDAY','中秋节','中秋节',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(25,'2025-10-01',2025,'HOLIDAY','国庆节','国庆节',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(26,'2025-10-02',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(27,'2025-10-03',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(28,'2025-10-04',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(29,'2025-10-05',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(30,'2025-10-07',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(31,'2025-10-08',2025,'HOLIDAY','国庆节','国庆节假期',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(32,'2025-09-28',2025,'WORKDAY','国庆节调休','周日调休上班',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
INSERT INTO holidays VALUES(33,'2025-10-11',2025,'WORKDAY','国庆节调休','周六调休上班',1,'2026-01-28 06:47:09','2026-01-28 06:47:09');
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_code VARCHAR(20) UNIQUE NOT NULL,
    source VARCHAR(50),
    customer_name VARCHAR(100),
    industry VARCHAR(50),
    contact_name VARCHAR(50),
    contact_phone VARCHAR(20),
    demand_summary TEXT,
    owner_id INTEGER,
    status VARCHAR(20) DEFAULT 'NEW',
    next_action_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, selected_advantage_products TEXT, product_match_type VARCHAR(20) DEFAULT 'UNKNOWN', is_advantage_product INTEGER DEFAULT 0, priority_score INTEGER, is_key_lead BOOLEAN DEFAULT 0, priority_level VARCHAR(10), importance_level VARCHAR(10), urgency_level VARCHAR(10), health_status VARCHAR(10) DEFAULT 'H1', health_score INT, last_follow_up_at DATETIME, break_risk_level VARCHAR(10), requirement_detail_id INTEGER, assessment_id INTEGER, completeness INTEGER DEFAULT 0, assignee_id INTEGER, assessment_status VARCHAR(20),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opp_code VARCHAR(20) UNIQUE NOT NULL,
    lead_id INTEGER,
    customer_id INTEGER NOT NULL,
    opp_name VARCHAR(200) NOT NULL,
    project_type VARCHAR(20),
    equipment_type VARCHAR(20),
    stage VARCHAR(20) DEFAULT 'DISCOVERY',
    est_amount DECIMAL(12,2),
    est_margin DECIMAL(5,2),
    budget_range VARCHAR(50),
    decision_chain TEXT,
    delivery_window VARCHAR(50),
    acceptance_basis TEXT,
    score INTEGER DEFAULT 0,
    risk_level VARCHAR(10),
    owner_id INTEGER,
    gate_status VARCHAR(20) DEFAULT 'PENDING',
    gate_passed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, priority_score INTEGER, is_key_opportunity BOOLEAN DEFAULT 0, priority_level VARCHAR(10), health_status VARCHAR(10) DEFAULT 'H1', health_score INT, last_progress_at DATETIME, break_risk_level VARCHAR(10), assessment_id INTEGER, requirement_maturity INTEGER, assessment_status VARCHAR(20), probability INTEGER DEFAULT 0, expected_close_date DATE, updated_by INTEGER,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE opportunity_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL,
    product_object VARCHAR(100),
    ct_seconds INTEGER,
    interface_desc TEXT,
    site_constraints TEXT,
    acceptance_criteria TEXT,
    safety_requirement TEXT,
    attachments TEXT,
    extra_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'DRAFT',
    current_version_id INTEGER,
    valid_until DATE,
    owner_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, health_status VARCHAR(10) DEFAULT 'H1', health_score INT, break_risk_level VARCHAR(10),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE quote_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    version_no VARCHAR(10) NOT NULL,
    total_price DECIMAL(12,2),
    cost_total DECIMAL(12,2),
    gross_margin DECIMAL(5,2),
    lead_time_days INTEGER,
    risk_terms TEXT,
    delivery_date DATE,
    created_by INTEGER,
    approved_by INTEGER,
    approved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, cost_template_id INTEGER, cost_breakdown_complete BOOLEAN DEFAULT 0, margin_warning BOOLEAN DEFAULT 0,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_version_id INTEGER NOT NULL,
    item_type VARCHAR(20),
    item_name VARCHAR(200),
    qty DECIMAL(10,2),
    unit_price DECIMAL(12,2),
    cost DECIMAL(12,2),
    lead_time_days INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, cost_category VARCHAR(50), cost_source VARCHAR(50), specification TEXT, unit VARCHAR(20),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id)
);
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_code VARCHAR(20) UNIQUE NOT NULL,
    opportunity_id INTEGER NOT NULL,
    quote_version_id INTEGER,
    customer_id INTEGER NOT NULL,
    project_id INTEGER,
    contract_amount DECIMAL(12,2),
    signed_date DATE,
    status VARCHAR(20) DEFAULT 'DRAFT',
    payment_terms_summary TEXT,
    acceptance_summary TEXT,
    owner_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, health_status VARCHAR(10) DEFAULT 'H1', health_score INT, break_risk_level VARCHAR(10), `customer_contract_no` VARCHAR(100) DEFAULT NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE contract_deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    deliverable_name VARCHAR(100),
    deliverable_type VARCHAR(50),
    required_for_payment BOOLEAN DEFAULT TRUE,
    template_ref VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_code VARCHAR(30) UNIQUE NOT NULL,
    contract_id INTEGER NOT NULL,
    project_id INTEGER,
    payment_id INTEGER,
    invoice_type VARCHAR(20),
    amount DECIMAL(12,2),
    tax_rate DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'DRAFT',
    issue_date DATE,
    buyer_name VARCHAR(100),
    buyer_tax_no VARCHAR(30),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, tax_amount DECIMAL(12,2), total_amount DECIMAL(12,2), payment_status VARCHAR(20), due_date DATE, paid_amount DECIMAL(12,2) DEFAULT 0, paid_date DATE, remark TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);
CREATE TABLE receivable_disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL,
    reason_code VARCHAR(30),
    description TEXT,
    status VARCHAR(20) DEFAULT 'OPEN',
    responsible_dept VARCHAR(50),
    responsible_id INTEGER,
    expect_resolve_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payments(id),
    FOREIGN KEY (responsible_id) REFERENCES users(id)
);
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    auth_type VARCHAR(20) DEFAULT 'password',
    email VARCHAR(100),
    phone VARCHAR(20),
    real_name VARCHAR(50),
    employee_no VARCHAR(50),
    department VARCHAR(100),
    position VARCHAR(100),
    avatar VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login_at DATETIME,
    last_login_ip VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, solution_credits INTEGER DEFAULT 100 NOT NULL, credits_updated_at DATETIME, tenant_id VARCHAR(50) DEFAULT 'default', is_tenant_admin BOOLEAN DEFAULT 0, reporting_to INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
INSERT INTO users VALUES(1,1,'admin','$pbkdf2-sha256$29000$RggBoBTivNc6Zyzl/B9jLA$9O8WfNRaH0YtHkDvBfyj0Kc0NaV6ezEv2XAmVXy060Q','password',NULL,NULL,'系统管理员',NULL,'系统管理','管理员',NULL,1,1,'2026-01-28 17:36:20.636295',NULL,'2026-01-28 06:48:15','2026-01-28 17:36:20.638002',100,NULL,'default',0,NULL);
INSERT INTO users VALUES(2,1,'chairman','$pbkdf2-sha256$29000$uvfeew8BoFRK6b2X8l7rPQ$Uh/FSPtDJxVBVma2jMq5aOBJhbqbsCYG/NmPUmf6RVA','password','chairman@demo.local',NULL,'董事长','E0001','董事会','董事长',NULL,1,1,NULL,NULL,'2026-01-28 15:00:32.047069','2026-01-28 15:00:32.047071',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(3,2,'gm','$pbkdf2-sha256$29000$fq9VSsm517r3HqMUwrhXag$OoVQnz36a/rMJHWbU7C7ZPuYK18O0NGwL/2MqmvRbJg','password','gm@demo.local',NULL,'总经理','E0002','总经理办公室','总经理',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.058663','2026-01-28 15:00:32.058664',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(4,3,'pm','$pbkdf2-sha256$29000$3Pt/TwlhDGFMiZFyDqG0dg$1jsgqFDwX3q4k1CEzJreDfmkUplq65znVFO/TCTykcY','password','pm@demo.local',NULL,'项目经理','E0003','技术中心','项目经理',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.068315','2026-01-28 15:00:32.068318',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(5,4,'sales_director','$pbkdf2-sha256$29000$GgNAqLXWmlOK0dpbi3EuhQ$tLHngRZjjP5D3SuepXRaOFqWX4m..XLAQezSSlNrR1E','password','sales_director@demo.local',NULL,'销售总监','E0005','销售部','销售总监',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.079499','2026-01-28 15:00:32.079503',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(6,5,'sales_manager','$pbkdf2-sha256$29000$H6NUCkHoXcuZU.qdc85Zqw$jB0KvPuG1iOQlw8kBWI90KD/SuORVUDvCIKgkAa27Ug','password','sales_manager@demo.local',NULL,'销售经理','E0006','销售部','销售经理',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.095057','2026-01-28 15:00:32.095060',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(7,6,'pmc','$pbkdf2-sha256$29000$9n4vRWhNCaFUqtXa.3/vPQ$03FO2Zd.46eVIu5vfZ4sb30cN0.Rabfmaw49e2Hju/s','password','pmc@demo.local',NULL,'P&C','E0004','计划部','计划管理',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.111706','2026-01-28 15:00:32.111710',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(8,7,'mech_manager','$pbkdf2-sha256$29000$FEKIMSYkROg9R2jNOcfYmw$v3Ce1CEbHNkun43YyDuLpPzaurakOBnjHNRuXCBO1Xo','password','mech_manager@demo.local',NULL,'机械部经理','E0007','机械部','机械部经理',NULL,1,0,NULL,NULL,'2026-01-28 15:00:32.126262','2026-01-28 15:00:32.126265',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(9,8,'zhengrucai','$pbkdf2-sha256$29000$ZSwlRGgNwRiD8B4DIERI6Q$.Hu3umINJRUsAb7309Zj2NqTnQFHYJEjvxzPN44Mirs','password','zhengrucai@demo.local',NULL,'郑汝才','E1001','高层管理','常务副总',NULL,1,0,'2026-01-31 15:04:32.859336',NULL,'2026-01-28 15:01:48.180114','2026-01-31 15:04:32.969402',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(10,9,'luoyixing','$pbkdf2-sha256$29000$5bz33ltLiXFujfGeU8qZUw$ASpeYx.l2NtI0X28jj75agjkux/4TQqhUpuyU6fUsd4','password','luoyixing@demo.local',NULL,'骆奕兴','E1002','高层管理','副总经理',NULL,1,0,'2026-01-31 15:04:39.959186',NULL,'2026-01-28 15:01:48.190116','2026-01-31 15:04:39.960497',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(11,10,'fulingwei','$pbkdf2-sha256$29000$05oz5hwjZAwhBGDMee.9tw$znTUCKW.Wsiy8yDDbfINyQ3U02N9AvNOuKApNa6AQTo','password','fulingwei@demo.local',NULL,'符凌维','E1003','高层管理','副总经理（董秘）',NULL,1,0,'2026-01-31 19:00:12.546725',NULL,'2026-01-28 15:01:48.199884','2026-01-31 19:00:12.555390',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(12,11,'songkui','$pbkdf2-sha256$29000$TUmptRYC4FyLUerdmzPG2A$SLswf.OrMO6guMa.OBv.ewvE0qt4//Mk.DeHwYi0FOk','password','songkui@demo.local',NULL,'宋魁','E1004','营销中心','营销中心总监',NULL,1,0,'2026-01-28 15:17:14.205368',NULL,'2026-01-28 15:01:48.209164','2026-01-28 15:17:14.206854',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(13,12,'zhengqin','$pbkdf2-sha256$29000$3vs/Z8x5r7X2/n/vvVfKeQ$XB7TUGO1Xc8LFPRMOTlarWEWCea9NFykYza73pK59c4','password','zhengqin@demo.local',NULL,'郑琴','E1005','营销中心','销售经理',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.222514','2026-01-28 15:01:48.222517',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(14,13,'yaohong','$pbkdf2-sha256$29000$33sPYQwhJKRUqjUGoPSekw$ukwYh5TD6qQWpy0L4kA0p7rhgwkeHCtGd4/SG5Ove9E','password','yaohong@demo.local',NULL,'姚洪','E1006','营销中心','销售工程师',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.232197','2026-01-28 15:01:48.232199',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(15,14,'changxiong','$pbkdf2-sha256$29000$MmaM8V5LSck5h/Cek7I2pg$z0tJCoNA1wGqjU9iib8NAi1MqKFchamK9cFaflO.Eig','password','changxiong@demo.local',NULL,'常雄','E1007','生产管理中心','PMC主管',NULL,1,0,'2026-01-28 15:16:35.022305',NULL,'2026-01-28 15:01:48.241232','2026-01-28 15:16:35.023599',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(16,15,'gaoyong','$pbkdf2-sha256$29000$qhXivLcWYmzNmTOm1ForhQ$g8/TyMWDAc.okaAPeaBImDbLsHDNvhL5UkbnKR8mV/E','password','gaoyong@demo.local',NULL,'高勇','E1008','生产部','生产部经理',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.249939','2026-01-28 15:01:48.249940',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(17,16,'chenliang','$pbkdf2-sha256$29000$LOXce8/Ze0.p9b73HuO8tw$uRQ2I7/TaSQ6vV41kiOslVFeKFldbBWnZcMhqrXNsoU','password','chenliang@demo.local',NULL,'陈亮','E1009','项目管理部','项目管理部总监',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.258530','2026-01-28 15:01:48.258530',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(18,17,'tanzhangbin','$pbkdf2-sha256$29000$ZYzRurfWOuf8H6N0TgmhVA$OsMzl8L0t.9xJxygPCOYXsaBTi4gGjU6bbTus/Jn7kQ','password','tanzhangbin@demo.local',NULL,'谭章斌','E1010','项目管理部','项目经理',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.267372','2026-01-28 15:01:48.267373',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(19,18,'yuzhenhua','$pbkdf2-sha256$29000$khICYKxVyrnXGqOUcq7VOg$D8R7aCOyVB0cb73YSYMSm0mf8RAv92uPqDKI2416tjA','password','yuzhenhua@demo.local',NULL,'于振华','E1011','技术部','经理',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.276115','2026-01-28 15:01:48.276116',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(20,19,'wangjun','$pbkdf2-sha256$29000$SkkpRQhByBnjnDOG8N5bCw$iV1apo1jLB5eF2Eml3oDrHwqv1mYL/Jp9GP.k9iiWh8','password','wangjun@demo.local',NULL,'王俊','E1012','质量部','经理',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.285324','2026-01-28 15:01:48.285326',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(21,20,'wangzhihong','$pbkdf2-sha256$29000$SWlN6X1vTYmx9t7739vbGw$tfCylqM73G9GWVYd0RyS6QWrVL.H6PoPCGnZ9NxzrMU','password','wangzhihong@demo.local',NULL,'王志红','E1013','客服部','客服主管',NULL,1,0,NULL,NULL,'2026-01-28 15:01:48.295985','2026-01-28 15:01:48.295987',100,NULL,NULL,0,NULL);
INSERT INTO users VALUES(22,21,'project.smoke','$pbkdf2-sha256$29000$/x9jrJXyfs9ZS0lJSakVAg$bOTXr7LrcC3irMLjRFED/CQYw1y/AZUxgLYpBWAxWZc','password',NULL,NULL,'Project.Smoke',NULL,'Smoke Test Dept',NULL,NULL,1,1,NULL,NULL,'2026-01-30 11:42:15.488225','2026-01-30 11:42:15.488331',100,NULL,NULL,0,NULL);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(30) UNIQUE NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    data_scope VARCHAR(20) DEFAULT 'PROJECT',
    is_system BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
, role_type VARCHAR(20) DEFAULT 'BUSINESS', scope_type VARCHAR(20) DEFAULT 'GLOBAL', parent_role_id INTEGER REFERENCES roles(id), level INTEGER DEFAULT 2, inherit_permissions BOOLEAN DEFAULT FALSE, status VARCHAR(20) DEFAULT 'ACTIVE', description TEXT, updated_at DATETIME, role_category VARCHAR(50), tenant_id INTEGER, source_template_id INTEGER, parent_id INTEGER, is_active BOOLEAN DEFAULT 1, sort_order INTEGER DEFAULT 0, nav_groups TEXT, ui_config TEXT);
INSERT INTO roles VALUES(5,'ENGINEER','Engineer','PROJECT',1,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE',NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(7,'PURCHASER','Purchaser','DEPT',1,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE',NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(8,'FINANCE','Finance','ALL',1,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE',NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(9,'SALES','Sales','OWN',1,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE',NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(21,'ADMIN','系统管理员','ALL',1,'2026-01-28 06:47:09','SYSTEM','GLOBAL',NULL,0,0,'ACTIVE','系统最高权限，可管理所有功能和数据',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(22,'GM','总经理','ALL',1,'2026-01-28 06:47:09','SYSTEM','GLOBAL',NULL,1,0,'ACTIVE','全局数据只读，关键审批权限',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(23,'CFO','财务总监','ALL',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,1,0,'ACTIVE','财务相关全局权限，成本与回款管理',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(24,'CTO','技术总监','ALL',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,1,0,'ACTIVE','技术相关全局权限，研发管理',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(25,'SALES_DIR','销售总监','DEPT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,1,0,'ACTIVE','销售部门全局权限，商机与合同管理',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(26,'PM','项目经理','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',24,2,0,'ACTIVE','项目全权管理，进度/变更/验收/成本',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(27,'PMC','计划管理','DEPT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE','生产计划、物料齐套、进度协调',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(28,'QA_MGR','质量主管','DEPT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE','质量管理、验收审批、问题闭环',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(29,'PU_MGR','采购主管','DEPT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE','采购管理、供应商管理、成本控制',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(30,'ME','机械工程师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',26,3,0,'ACTIVE','机械设计任务执行、交付物提交',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(31,'EE','电气工程师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',26,3,0,'ACTIVE','电气设计任务执行、交付物提交',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(32,'SW','软件工程师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',26,3,0,'ACTIVE','软件开发任务执行、交付物提交',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(33,'QA','质量工程师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',28,3,0,'ACTIVE','质量检验、验收执行、问题记录',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(34,'PU','采购专员','DEPT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',29,3,0,'ACTIVE','采购执行、到货跟踪、外协管理',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(35,'FI','财务专员','ALL',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',23,3,0,'ACTIVE','开票、收款登记、成本核算',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(36,'SA','销售专员','OWN',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',25,3,0,'ACTIVE','商机跟进、报价、合同、回款跟踪',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(37,'ASSEMBLER','装配技师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',NULL,3,0,'ACTIVE','装配任务执行、工时记录',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(38,'DEBUG','调试工程师','PROJECT',0,'2026-01-28 06:47:09','BUSINESS','GLOBAL',26,3,0,'ACTIVE','设备调试、问题记录、调试报告',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(39,'CUSTOMER','客户','CUSTOMER',1,'2026-01-28 06:47:09','SYSTEM','GLOBAL',NULL,4,0,'ACTIVE','客户门户，仅查看自身项目进度与验收',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(40,'SUPPLIER','供应商','OWN',1,'2026-01-28 06:47:09','SYSTEM','GLOBAL',NULL,4,0,'ACTIVE','供应商门户，查看订单与交货要求',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
INSERT INTO roles VALUES(61,'DEPT_MGR','部门经理','PROJECT',0,'2026-01-28 07:00:06','BUSINESS','GLOBAL',NULL,2,0,'ACTIVE','部门经理角色',NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL);
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    perm_code VARCHAR(100) UNIQUE NOT NULL,
    perm_name VARCHAR(100),
    module VARCHAR(50),
    action VARCHAR(50)
, resource VARCHAR(50), description TEXT, is_active BOOLEAN DEFAULT 1, created_at DATETIME, updated_at DATETIME, permission_type VARCHAR(20) DEFAULT 'API', group_id INTEGER REFERENCES permission_groups(id));
INSERT INTO permissions VALUES(1,'system:user:read','User Read','system','read','user',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(2,'system:user:manage','User Manage','system','manage','user',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(3,'system:role:read','Role Read','system','read','role',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(4,'system:role:manage','Role Manage','system','manage','role',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(5,'system:permission:read','Permission Read','system','read','permission',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(6,'project:project:read','Project Read','project','read','project',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(7,'project:project:manage','Project Manage','project','manage','project',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(8,'project:milestone:read','Milestone Read','project','read','milestone',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(9,'project:milestone:manage','Milestone Manage','project','manage','milestone',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(10,'project:task:read','Task Read','project','read','task',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(11,'project:task:manage','Task Manage','project','manage','task',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(12,'project:wbs:read','WBS Read','project','read','wbs',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(13,'project:wbs:manage','WBS Manage','project','manage','wbs',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(14,'project:deliverable:read','Deliverable Read','project','read','deliverable',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(15,'project:deliverable:submit','Deliverable Submit','project','submit','deliverable',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(16,'project:deliverable:approve','Deliverable Approve','project','approve','deliverable',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(17,'project:acceptance:read','Acceptance Read','project','read','acceptance',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(18,'project:acceptance:submit','Acceptance Submit','project','submit','acceptance',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(19,'project:acceptance:approve','Acceptance Approve','project','approve','acceptance',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(20,'project:ecn:read','ECN Read','project','read','ecn',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(21,'project:ecn:submit','ECN Submit','project','submit','ecn',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(22,'project:ecn:approve','ECN Approve','project','approve','ecn',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(23,'supply:purchase:read','Purchase Read','supply','read','purchase',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(24,'supply:purchase:manage','Purchase Manage','supply','manage','purchase',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(25,'supply:outsourcing:read','Outsourcing Read','supply','read','outsourcing',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(26,'supply:outsourcing:manage','Outsourcing Manage','supply','manage','outsourcing',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(27,'finance:payment:read','Payment Read','finance','read','payment',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(28,'finance:payment:approve','Payment Approve','finance','approve','payment',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(29,'finance:invoice:read','Invoice Read','finance','read','invoice',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(30,'finance:invoice:issue','Invoice Issue','finance','issue','invoice',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(31,'crm:lead:read','Lead Read','crm','read','lead',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(32,'crm:lead:manage','Lead Manage','crm','manage','lead',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(33,'crm:opportunity:read','Opportunity Read','crm','read','opportunity',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(34,'crm:opportunity:manage','Opportunity Manage','crm','manage','opportunity',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(35,'crm:quote:read','Quote Read','crm','read','quote',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(36,'crm:quote:manage','Quote Manage','crm','manage','quote',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(37,'crm:quote:approve','Quote Approve','crm','approve','quote',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(38,'crm:contract:read','Contract Read','crm','read','contract',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(39,'crm:contract:manage','Contract Manage','crm','manage','contract',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(40,'crm:contract:approve','Contract Approve','crm','approve','contract',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09','API',NULL);
INSERT INTO permissions VALUES(82,'system:user:create','用户创建','system','create','user',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(83,'system:user:update','用户更新','system','update','user',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(84,'system:user:delete','用户删除','system','delete','user',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(85,'system:audit:read','审计查看','system','read','audit',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(87,'project:project:create','项目创建','project','create','project',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(88,'project:project:update','项目更新','project','update','project',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(89,'project:project:delete','项目删除','project','delete','project',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(90,'project:machine:read','设备查看','project','read','machine',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(91,'project:machine:manage','设备管理','project','manage','machine',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(92,'project:member:read','成员查看','project','read','member',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(93,'project:member:manage','成员管理','project','manage','member',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(94,'project:stage:read','阶段查看','project','read','stage',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(95,'project:stage:manage','阶段管理','project','manage','stage',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(96,'project:cost:read','成本查看','project','read','cost',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(97,'project:cost:manage','成本管理','project','manage','cost',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(98,'project:document:read','文档查看','project','read','document',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(99,'project:document:manage','文档管理','project','manage','document',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(100,'customer:customer:read','客户查看','customer','read','customer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(101,'customer:customer:create','客户创建','customer','create','customer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(102,'customer:customer:update','客户更新','customer','update','customer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(103,'customer:customer:delete','客户删除','customer','delete','customer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(104,'supplier:supplier:read','供应商查看','supplier','read','supplier',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(105,'supplier:supplier:create','供应商创建','supplier','create','supplier',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(106,'supplier:supplier:update','供应商更新','supplier','update','supplier',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(107,'supplier:supplier:delete','供应商删除','supplier','delete','supplier',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(108,'material:material:read','物料查看','material','read','material',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(109,'material:material:create','物料创建','material','create','material',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(110,'material:material:update','物料更新','material','update','material',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(111,'material:material:delete','物料删除','material','delete','material',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(112,'material:shortage:read','缺料查看','material','read','shortage',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(113,'material:shortage:manage','缺料管理','material','manage','shortage',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(114,'issue:issue:read','问题查看','issue','read','issue',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(115,'issue:issue:create','问题创建','issue','create','issue',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(116,'issue:issue:update','问题更新','issue','update','issue',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(117,'issue:issue:delete','问题删除','issue','delete','issue',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(118,'issue:issue:resolve','问题解决','issue','resolve','issue',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(119,'finance:budget:read','预算查看','finance','read','budget',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(120,'finance:budget:create','预算创建','finance','create','budget',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(121,'finance:budget:update','预算更新','finance','update','budget',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(122,'finance:budget:approve','预算审批','finance','approve','budget',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(123,'finance:cost:read','成本查看','finance','read','cost',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(124,'finance:cost:manage','成本管理','finance','manage','cost',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(125,'finance:bonus:read','奖金查看','finance','read','bonus',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(126,'finance:bonus:manage','奖金管理','finance','manage','bonus',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(127,'service:service:read','服务查看','service','read','service',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(128,'service:service:create','服务创建','service','create','service',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(129,'service:service:update','服务更新','service','update','service',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(130,'service:ticket:read','工单查看','service','read','ticket',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(131,'service:ticket:manage','工单管理','service','manage','ticket',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(132,'business_support:order:read','业务订单查看','business_support','read','order',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(133,'business_support:order:create','业务订单创建','business_support','create','order',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(134,'business_support:order:update','业务订单更新','business_support','update','order',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(135,'business_support:order:approve','业务订单审批','business_support','approve','order',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(136,'organization:org:read','组织查看','organization','read','org',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(137,'organization:org:manage','组织管理','organization','manage','org',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(138,'organization:employee:read','员工查看','organization','read','employee',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(139,'organization:employee:manage','员工管理','organization','manage','employee',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(140,'task_center:task:read','任务查看','task_center','read','task',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(141,'task_center:task:create','任务创建','task_center','create','task',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(142,'task_center:task:update','任务更新','task_center','update','task',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(143,'task_center:task:complete','任务完成','task_center','complete','task',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(144,'timesheet:timesheet:read','工时查看','timesheet','read','timesheet',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(145,'timesheet:timesheet:create','工时创建','timesheet','create','timesheet',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(146,'timesheet:timesheet:update','工时更新','timesheet','update','timesheet',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(147,'timesheet:timesheet:approve','工时审批','timesheet','approve','timesheet',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(148,'report:report:read','报表查看','report','read','report',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(149,'report:report:export','报表导出','report','export','report',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(150,'report:report:manage','报表管理','report','manage','report',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(151,'notification:notification:read','通知查看','notification','read','notification',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(152,'notification:notification:manage','通知管理','notification','manage','notification',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(153,'document:document:read','文档查看','document','read','document',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(154,'document:document:manage','文档管理','document','manage','document',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(155,'technical_spec:spec:read','技术规格查看','technical_spec','read','spec',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(156,'technical_spec:spec:manage','技术规格管理','technical_spec','manage','spec',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(157,'engineer:engineer:read','工程师查看','engineer','read','engineer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(158,'engineer:engineer:manage','工程师管理','engineer','manage','engineer',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(159,'qualification:qualification:read','任职资格查看','qualification','read','qualification',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(160,'qualification:qualification:manage','任职资格管理','qualification','manage','qualification',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(161,'assembly_kit:kit:read','装配齐套查看','assembly_kit','read','kit',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(162,'assembly_kit:kit:manage','装配齐套管理','assembly_kit','manage','kit',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(163,'staff_matching:matching:read','人员匹配查看','staff_matching','read','matching',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(164,'staff_matching:matching:manage','人员匹配管理','staff_matching','manage','matching',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(165,'project_evaluation:evaluation:read','项目评价查看','project_evaluation','read','evaluation',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(166,'project_evaluation:evaluation:manage','项目评价管理','project_evaluation','manage','evaluation',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(167,'installation_dispatch:dispatch:read','安装派工查看','installation_dispatch','read','dispatch',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(168,'installation_dispatch:dispatch:manage','安装派工管理','installation_dispatch','manage','dispatch',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(169,'scheduler:scheduler:read','调度器查看','scheduler','read','scheduler',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(170,'scheduler:scheduler:manage','调度器管理','scheduler','manage','scheduler',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(171,'hr_management:hr:read','HR管理查看','hr_management','read','hr',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(172,'hr_management:hr:manage','HR管理','hr_management','manage','hr',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(173,'presales_integration:presales:read','售前集成查看','presales_integration','read','presales',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(174,'presales_integration:presales:manage','售前集成管理','presales_integration','manage','presales',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(175,'advantage_products:product:read','优势产品查看','advantage_products','read','product',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(176,'advantage_products:product:manage','优势产品管理','advantage_products','manage','product',NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(177,'purchase:order:read','采购订单查看','purchase','read','order','可以查看采购订单列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(178,'purchase:order:create','采购订单创建','purchase','create','order','可以创建采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(179,'purchase:order:update','采购订单更新','purchase','update','order','可以更新采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(180,'purchase:order:delete','采购订单删除','purchase','delete','order','可以删除采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(181,'purchase:order:submit','采购订单提交','purchase','submit','order','可以提交采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(182,'purchase:order:approve','采购订单审批','purchase','approve','order','可以审批采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(183,'purchase:order:receive','采购订单收货','purchase','receive','order','可以处理采购订单收货',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(184,'purchase:receipt:read','收货单查看','purchase','read','receipt','可以查看收货单列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(185,'purchase:receipt:create','收货单创建','purchase','create','receipt','可以创建收货单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(186,'purchase:receipt:update','收货单更新','purchase','update','receipt','可以更新收货单状态',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(187,'purchase:receipt:inspect','收货单质检','purchase','inspect','receipt','可以对收货单进行质检',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(188,'purchase:request:read','采购申请查看','purchase','read','request','可以查看采购申请列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(189,'purchase:request:create','采购申请创建','purchase','create','request','可以创建采购申请',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(190,'purchase:request:update','采购申请更新','purchase','update','request','可以更新采购申请',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(191,'purchase:request:delete','采购申请删除','purchase','delete','request','可以删除采购申请',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(192,'purchase:request:submit','采购申请提交','purchase','submit','request','可以提交采购申请',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(193,'purchase:request:approve','采购申请审批','purchase','approve','request','可以审批采购申请',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(194,'purchase:request:generate','采购申请生成订单','purchase','generate','request','可以根据采购申请生成采购订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(195,'purchase:bom:generate','从BOM生成采购','purchase','generate','bom','可以从BOM生成采购申请或订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(196,'ecn:ecn:read','ECN查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(197,'ecn:ecn:create','ECN创建','ecn','create',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(198,'ecn:ecn:update','ECN修改','ecn','update',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(199,'ecn:ecn:submit','ECN提交','ecn','submit',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(200,'ecn:ecn:cancel','ECN取消','ecn','cancel',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(201,'ecn:ecn:delete','ECN删除','ecn','delete',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(202,'ecn:evaluation:read','评估查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(203,'ecn:evaluation:create','评估创建','ecn','create',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(204,'ecn:evaluation:submit','评估提交','ecn','submit',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(205,'ecn:approval:read','审批查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(206,'ecn:approval:approve','审批通过','ecn','approve',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(207,'ecn:approval:reject','审批驳回','ecn','reject',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(208,'ecn:task:read','任务查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(209,'ecn:task:create','任务创建','ecn','create',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(210,'ecn:task:update','任务更新','ecn','update',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(211,'ecn:task:complete','任务完成','ecn','complete',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(212,'ecn:affected:read','影响分析查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(213,'ecn:affected:manage','影响分析管理','ecn','manage',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(214,'ecn:sync:bom','BOM同步','ecn','bom',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(215,'ecn:sync:project','项目同步','ecn','project',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(216,'ecn:sync:purchase','采购同步','ecn','purchase',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(217,'ecn:type:read','类型配置查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(218,'ecn:type:manage','类型配置管理','ecn','manage',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(219,'ecn:matrix:read','审批矩阵查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(220,'ecn:matrix:manage','审批矩阵管理','ecn','manage',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(221,'ecn:statistics:read','统计查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(222,'ecn:alert:read','超时提醒查看','ecn','read',NULL,NULL,1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(223,'advantage_product:read','优势产品查看','advantage_product','read','advantage_product','可以查看优势产品列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(224,'advantage_product:create','优势产品创建','advantage_product','create','advantage_product','可以创建新的优势产品',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(225,'advantage_product:update','优势产品更新','advantage_product','update','advantage_product','可以更新优势产品信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(226,'advantage_product:delete','优势产品删除','advantage_product','delete','advantage_product','可以删除优势产品',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(227,'assembly_kit:read','装配套件查看','assembly_kit','read','assembly_kit','可以查看装配套件列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(228,'assembly_kit:create','装配套件创建','assembly_kit','create','assembly_kit','可以创建装配套件',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(229,'assembly_kit:update','装配套件更新','assembly_kit','update','assembly_kit','可以更新装配套件信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(230,'assembly_kit:delete','装配套件删除','assembly_kit','delete','assembly_kit','可以删除装配套件',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(231,'assembly_kit:manage','装配套件管理','assembly_kit','manage','assembly_kit','可以管理装配套件的完整生命周期',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(232,'budget:read','预算查看','budget','read','budget','可以查看项目预算列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(233,'budget:create','预算创建','budget','create','budget','可以创建项目预算',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(234,'budget:update','预算更新','budget','update','budget','可以更新项目预算信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(235,'budget:approve','预算审批','budget','approve','budget','可以审批项目预算',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(236,'budget:delete','预算删除','budget','delete','budget','可以删除项目预算',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(237,'business_support:read','业务支持查看','business_support','read','business_support','可以查看业务支持订单和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(238,'business_support:create','业务支持创建','business_support','create','business_support','可以创建业务支持订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(239,'business_support:update','业务支持更新','business_support','update','business_support','可以更新业务支持订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(240,'business_support:approve','业务支持审批','business_support','approve','business_support','可以审批业务支持订单',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(241,'business_support:manage','业务支持管理','business_support','manage','business_support','可以管理业务支持的完整流程',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(242,'cost:read','成本查看','cost','read','cost','可以查看项目成本列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(243,'cost:create','成本创建','cost','create','cost','可以创建成本记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(244,'cost:update','成本更新','cost','update','cost','可以更新成本信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(245,'cost:delete','成本删除','cost','delete','cost','可以删除成本记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(246,'cost:manage','成本管理','cost','manage','cost','可以管理成本的完整生命周期',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(247,'customer:read','客户查看','customer','read','customer','可以查看客户列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(248,'customer:create','客户创建','customer','create','customer','可以创建新客户',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(249,'customer:update','客户更新','customer','update','customer','可以更新客户信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(250,'customer:delete','客户删除','customer','delete','customer','可以删除客户',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(251,'data_import:import','数据导入','data_import','import','data_import','可以导入数据到系统',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(252,'data_export:export','数据导出','data_export','export','data_export','可以导出系统数据',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(253,'data_import_export:manage','数据导入导出管理','data_import_export','manage','data_import_export','可以管理数据导入导出功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(254,'document:read','文档查看','document','read','document','可以查看文档列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(255,'document:create','文档创建','document','create','document','可以上传和创建文档',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(256,'document:update','文档更新','document','update','document','可以更新文档信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(257,'document:delete','文档删除','document','delete','document','可以删除文档',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(258,'document:download','文档下载','document','download','document','可以下载文档',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(259,'engineer:read','工程师查看','engineer','read','engineer','可以查看工程师列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(260,'engineer:create','工程师创建','engineer','create','engineer','可以创建工程师信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(261,'engineer:update','工程师更新','engineer','update','engineer','可以更新工程师信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(262,'engineer:manage','工程师管理','engineer','manage','engineer','可以管理工程师的完整信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(263,'hourly_rate:read','小时费率查看','hourly_rate','read','hourly_rate','可以查看小时费率配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(264,'hourly_rate:create','小时费率创建','hourly_rate','create','hourly_rate','可以创建小时费率配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(265,'hourly_rate:update','小时费率更新','hourly_rate','update','hourly_rate','可以更新小时费率配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(266,'hourly_rate:delete','小时费率删除','hourly_rate','delete','hourly_rate','可以删除小时费率配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(267,'hr:read','HR管理查看','hr','read','hr','可以查看HR管理相关数据',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(268,'hr:create','HR管理创建','hr','create','hr','可以创建HR管理记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(269,'hr:update','HR管理更新','hr','update','hr','可以更新HR管理信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(270,'hr:manage','HR管理','hr','manage','hr','可以管理HR的完整功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(271,'installation_dispatch:read','安装调度查看','installation_dispatch','read','installation_dispatch','可以查看安装调度列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(272,'installation_dispatch:create','安装调度创建','installation_dispatch','create','installation_dispatch','可以创建安装调度任务',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(273,'installation_dispatch:update','安装调度更新','installation_dispatch','update','installation_dispatch','可以更新安装调度信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(274,'installation_dispatch:manage','安装调度管理','installation_dispatch','manage','installation_dispatch','可以管理安装调度的完整流程',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(275,'issue:read','问题查看','issue','read','issue','可以查看问题列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(276,'issue:create','问题创建','issue','create','issue','可以创建问题记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(277,'issue:update','问题更新','issue','update','issue','可以更新问题信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(278,'issue:resolve','问题解决','issue','resolve','issue','可以解决和关闭问题',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(279,'issue:assign','问题分配','issue','assign','issue','可以分配问题给处理人',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(280,'issue:delete','问题删除','issue','delete','issue','可以删除问题记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(281,'machine:read','设备查看','machine','read','machine','可以查看设备列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(282,'machine:create','设备创建','machine','create','machine','可以创建设备信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(283,'machine:update','设备更新','machine','update','machine','可以更新设备信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(284,'machine:delete','设备删除','machine','delete','machine','可以删除设备',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(285,'material:read','物料查看','material','read','material','可以查看物料列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(286,'material:create','物料创建','material','create','material','可以创建物料信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(287,'material:update','物料更新','material','update','material','可以更新物料信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(288,'material:delete','物料删除','material','delete','material','可以删除物料',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(289,'milestone:read','里程碑查看','milestone','read','milestone','可以查看里程碑列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(290,'milestone:create','里程碑创建','milestone','create','milestone','可以创建里程碑',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(291,'milestone:update','里程碑更新','milestone','update','milestone','可以更新里程碑信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(292,'milestone:delete','里程碑删除','milestone','delete','milestone','可以删除里程碑',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(293,'notification:read','通知查看','notification','read','notification','可以查看通知列表',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(294,'notification:create','通知创建','notification','create','notification','可以创建和发送通知',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(295,'notification:update','通知更新','notification','update','notification','可以更新通知状态',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(296,'notification:delete','通知删除','notification','delete','notification','可以删除通知',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(297,'presales_integration:read','售前集成查看','presales_integration','read','presales_integration','可以查看售前集成数据',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(298,'presales_integration:create','售前集成创建','presales_integration','create','presales_integration','可以创建售前集成记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(299,'presales_integration:update','售前集成更新','presales_integration','update','presales_integration','可以更新售前集成信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(300,'presales_integration:manage','售前集成管理','presales_integration','manage','presales_integration','可以管理售前集成的完整功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(301,'project_evaluation:read','项目评估查看','project_evaluation','read','project_evaluation','可以查看项目评估列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(302,'project_evaluation:create','项目评估创建','project_evaluation','create','project_evaluation','可以创建项目评估',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(303,'project_evaluation:update','项目评估更新','project_evaluation','update','project_evaluation','可以更新项目评估信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(304,'project_evaluation:manage','项目评估管理','project_evaluation','manage','project_evaluation','可以管理项目评估的完整流程',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(305,'project_role:read','项目角色查看','project_role','read','project_role','可以查看项目角色列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(306,'project_role:create','项目角色创建','project_role','create','project_role','可以创建项目角色',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(307,'project_role:update','项目角色更新','project_role','update','project_role','可以更新项目角色信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(308,'project_role:delete','项目角色删除','project_role','delete','project_role','可以删除项目角色',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(309,'project_role:assign','项目角色分配','project_role','assign','project_role','可以分配项目角色给用户',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(310,'qualification:read','资质查看','qualification','read','qualification','可以查看资质列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(311,'qualification:create','资质创建','qualification','create','qualification','可以创建资质记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(312,'qualification:update','资质更新','qualification','update','qualification','可以更新资质信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(313,'qualification:delete','资质删除','qualification','delete','qualification','可以删除资质记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(314,'qualification:manage','资质管理','qualification','manage','qualification','可以管理资质的完整生命周期',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(315,'report:read','报表查看','report','read','report','可以查看报表列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(316,'report:create','报表创建','report','create','report','可以创建和生成报表',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(317,'report:export','报表导出','report','export','report','可以导出报表',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(318,'report:manage','报表管理','report','manage','report','可以管理报表的完整功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(319,'shortage_alert:read','短缺预警查看','shortage_alert','read','shortage_alert','可以查看短缺预警列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(320,'shortage_alert:create','短缺预警创建','shortage_alert','create','shortage_alert','可以创建短缺预警',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(321,'shortage_alert:update','短缺预警更新','shortage_alert','update','shortage_alert','可以更新短缺预警信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(322,'shortage_alert:resolve','短缺预警处理','shortage_alert','resolve','shortage_alert','可以处理和解决短缺预警',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(323,'shortage_alert:manage','短缺预警管理','shortage_alert','manage','shortage_alert','可以管理短缺预警的完整流程',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(324,'staff_matching:read','人员匹配查看','staff_matching','read','staff_matching','可以查看人员匹配列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(325,'staff_matching:create','人员匹配创建','staff_matching','create','staff_matching','可以创建人员匹配记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(326,'staff_matching:update','人员匹配更新','staff_matching','update','staff_matching','可以更新人员匹配信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(327,'staff_matching:manage','人员匹配管理','staff_matching','manage','staff_matching','可以管理人员匹配的完整功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(328,'stage:read','阶段查看','stage','read','stage','可以查看项目阶段列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(329,'stage:create','阶段创建','stage','create','stage','可以创建项目阶段',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(330,'stage:update','阶段更新','stage','update','stage','可以更新项目阶段信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(331,'stage:delete','阶段删除','stage','delete','stage','可以删除项目阶段',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(332,'stage:manage','阶段管理','stage','manage','stage','可以管理项目阶段的完整生命周期',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(333,'supplier:read','供应商查看','supplier','read','supplier','可以查看供应商列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(334,'supplier:create','供应商创建','supplier','create','supplier','可以创建供应商信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(335,'supplier:update','供应商更新','supplier','update','supplier','可以更新供应商信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(336,'supplier:delete','供应商删除','supplier','delete','supplier','可以删除供应商',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(337,'task_center:read','任务中心查看','task_center','read','task_center','可以查看任务列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(338,'task_center:create','任务中心创建','task_center','create','task_center','可以创建任务',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(339,'task_center:update','任务中心更新','task_center','update','task_center','可以更新任务信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(340,'task_center:assign','任务中心分配','task_center','assign','task_center','可以分配任务给执行人',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(341,'task_center:manage','任务中心管理','task_center','manage','task_center','可以管理任务的完整生命周期',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(342,'technical_spec:read','技术规格查看','technical_spec','read','technical_spec','可以查看技术规格列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(343,'technical_spec:create','技术规格创建','technical_spec','create','technical_spec','可以创建技术规格',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(344,'technical_spec:update','技术规格更新','technical_spec','update','technical_spec','可以更新技术规格信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(345,'technical_spec:delete','技术规格删除','technical_spec','delete','technical_spec','可以删除技术规格',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(346,'timesheet:read','工时表查看','timesheet','read','timesheet','可以查看工时表列表和详情',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(347,'timesheet:create','工时表创建','timesheet','create','timesheet','可以创建和填报工时',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(348,'timesheet:update','工时表更新','timesheet','update','timesheet','可以更新工时记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(349,'timesheet:approve','工时表审批','timesheet','approve','timesheet','可以审批工时表',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(350,'timesheet:delete','工时表删除','timesheet','delete','timesheet','可以删除工时记录',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(351,'timesheet:manage','工时表管理','timesheet','manage','timesheet','可以管理工时表的完整功能',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(356,'system:role:create','角色创建','system','create','role','创建新角色',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(357,'system:role:update','角色更新','system','update','role','更新角色信息',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(359,'performance:manage','绩效管理','performance','manage','performance','绩效管理权限（包含所有操作）',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(360,'performance:evaluation:read','绩效评估查看','performance','read','evaluation','查看绩效评估',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(361,'performance:evaluation:create','绩效评估创建','performance','create','evaluation','创建绩效评估',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(362,'performance:evaluation:update','绩效评估更新','performance','update','evaluation','更新绩效评估',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(363,'performance:summary:read','工作汇总查看','performance','read','summary','查看工作汇总',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(364,'performance:summary:create','工作汇总创建','performance','create','summary','创建工作汇总',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(365,'performance:summary:update','工作汇总更新','performance','update','summary','更新工作汇总',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(366,'project:erp:sync','ERP同步','project','sync','erp','同步项目数据到ERP系统',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(367,'project:erp:update','ERP更新','project','update','erp','更新ERP系统中的项目数据',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(368,'work_log:config:read','工作日志配置查看','work_log','read','config','查看工作日志配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(369,'work_log:config:create','工作日志配置创建','work_log','create','config','创建工作日志配置',1,NULL,NULL,'API',NULL);
INSERT INTO permissions VALUES(370,'work_log:config:update','工作日志配置更新','work_log','update','config','更新工作日志配置',1,NULL,NULL,'API',NULL);
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
INSERT INTO user_roles VALUES(1,2,21,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(2,3,22,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(3,4,26,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(4,5,25,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(5,6,36,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(6,7,27,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(7,8,61,'2026-01-28 07:00:32','2026-01-28 07:00:32');
INSERT INTO user_roles VALUES(8,9,22,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(9,10,22,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(11,12,25,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(12,13,36,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(13,14,36,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(14,15,27,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(15,16,61,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(16,17,26,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(17,18,26,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(18,19,61,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(19,20,28,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(20,21,61,'2026-01-28 07:01:48','2026-01-28 07:01:48');
INSERT INTO user_roles VALUES(21,11,21,'2026-01-28 07:18:53','2026-01-28 07:18:53');
INSERT INTO user_roles VALUES(22,1,21,'2026-01-28 09:35:36','2026-01-28 09:35:36');
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);
INSERT INTO role_permissions VALUES(1,1,40,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(2,1,39,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(3,1,38,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(4,1,32,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(5,1,31,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(6,1,34,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(7,1,33,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(8,1,37,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(9,1,36,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(10,1,35,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(11,1,30,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(12,1,29,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(13,1,28,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(14,1,27,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(15,1,19,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(16,1,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(17,1,18,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(18,1,16,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(19,1,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(20,1,15,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(21,1,22,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(22,1,20,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(23,1,21,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(24,1,9,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(25,1,8,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(26,1,7,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(27,1,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(28,1,11,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(29,1,10,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(30,1,13,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(31,1,12,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(32,1,26,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(33,1,25,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(34,1,24,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(35,1,23,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(36,1,5,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(37,1,4,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(38,1,3,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(39,1,2,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(40,1,1,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(41,2,1,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(42,2,3,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(43,2,5,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(44,2,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(45,2,8,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(46,2,10,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(47,2,12,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(48,2,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(49,2,16,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(50,2,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(51,2,19,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(52,2,20,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(53,2,22,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(54,2,23,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(55,2,25,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(56,2,27,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(57,2,28,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(58,2,29,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(59,2,31,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(60,2,33,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(61,2,35,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(62,2,37,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(63,2,38,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(64,2,40,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(65,3,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(66,3,18,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(67,3,16,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(68,3,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(69,3,15,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(70,3,22,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(71,3,20,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(72,3,21,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(73,3,9,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(74,3,8,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(75,3,7,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(76,3,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(77,3,11,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(78,3,10,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(79,3,13,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(80,3,12,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(81,3,25,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(82,3,23,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(83,4,9,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(84,4,8,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(85,4,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(86,4,10,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(87,4,12,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(88,4,26,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(89,4,25,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(90,4,24,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(91,4,23,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(92,5,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(93,5,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(94,5,15,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(95,5,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(96,5,11,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(97,5,10,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(98,6,19,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(99,6,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(100,6,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(101,6,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(102,7,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(103,7,26,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(104,7,25,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(105,7,24,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(106,7,23,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(107,8,38,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(108,8,30,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(109,8,29,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(110,8,28,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(111,8,27,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(112,8,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(113,9,39,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(114,9,38,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(115,9,32,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(116,9,31,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(117,9,34,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(118,9,33,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(119,9,36,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(120,9,35,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(121,10,17,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(122,10,14,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(123,10,8,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(124,10,6,'2026-01-28 06:47:09');
INSERT INTO role_permissions VALUES(249,21,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(250,21,197,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(251,21,198,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(252,21,199,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(253,21,200,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(254,21,201,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(255,21,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(256,21,203,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(257,21,204,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(258,21,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(259,21,206,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(260,21,207,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(261,21,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(262,21,209,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(263,21,210,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(264,21,211,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(265,21,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(266,21,213,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(267,21,214,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(268,21,215,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(269,21,216,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(270,21,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(271,21,218,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(272,21,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(273,21,220,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(274,21,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(275,21,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(276,22,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(277,22,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(278,22,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(279,22,206,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(280,22,207,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(281,22,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(282,22,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(283,22,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(284,22,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(285,22,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(286,22,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(287,26,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(288,26,197,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(289,26,198,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(290,26,199,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(291,26,200,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(292,26,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(293,26,203,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(294,26,204,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(295,26,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(296,26,206,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(297,26,207,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(298,26,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(299,26,209,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(300,26,210,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(301,26,211,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(302,26,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(303,26,213,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(304,26,214,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(305,26,215,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(306,26,216,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(307,26,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(308,26,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(309,26,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(310,26,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(311,27,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(312,27,197,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(313,27,198,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(314,27,199,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(315,27,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(316,27,203,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(317,27,204,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(318,27,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(319,27,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(320,27,209,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(321,27,210,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(322,27,211,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(323,27,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(324,27,214,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(325,27,215,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(326,27,216,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(327,27,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(328,27,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(329,27,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(330,27,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(331,33,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(332,33,197,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(333,33,199,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(334,33,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(335,33,203,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(336,33,204,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(337,33,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(338,33,206,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(339,33,207,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(340,33,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(341,33,209,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(342,33,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(343,33,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(344,33,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(345,33,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(346,33,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(347,34,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(348,34,197,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(349,34,199,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(350,34,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(351,34,203,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(352,34,204,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(353,34,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(354,34,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(355,34,209,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(356,34,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(357,34,213,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(358,34,216,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(359,34,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(360,34,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(361,34,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(362,34,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(363,35,196,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(364,35,202,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(365,35,205,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(366,35,206,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(367,35,207,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(368,35,208,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(369,35,212,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(370,35,217,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(371,35,219,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(372,35,221,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(373,35,222,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(374,21,361,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(375,21,360,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(376,21,362,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(377,21,359,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(378,21,364,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(379,21,363,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(380,21,365,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(381,21,366,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(382,21,367,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(383,21,85,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(384,21,356,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(385,21,357,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(386,21,82,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(387,21,84,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(388,21,1,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(389,21,83,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(390,21,369,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(391,21,368,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(392,21,370,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(393,22,360,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(394,22,363,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(395,22,85,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(396,22,3,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(397,22,1,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(398,26,360,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(399,26,364,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(400,26,363,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(401,26,366,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(402,26,368,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(403,21,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(404,22,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(405,23,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(406,24,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(407,25,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(408,5,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(409,7,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(410,8,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(411,9,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(412,26,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(413,27,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(414,28,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(415,29,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(416,30,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(417,31,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(418,32,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(419,33,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(420,34,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(421,35,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(422,36,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(423,37,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(424,38,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(425,39,293,'2026-01-28 06:47:10');
INSERT INTO role_permissions VALUES(426,40,293,'2026-01-28 06:47:10');
CREATE TABLE permission_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER NOT NULL,
    action VARCHAR(50),
    target_type VARCHAR(20),
    target_id INTEGER NOT NULL,
    detail TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);
CREATE TABLE wbs_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(20) UNIQUE NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    project_type VARCHAR(20),
    equipment_type VARCHAR(20),
    version_no VARCHAR(10) DEFAULT 'V1',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE wbs_template_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    task_name VARCHAR(200),
    stage VARCHAR(20),
    default_owner_role VARCHAR(50),
    plan_days INTEGER,
    weight DECIMAL(5,2) DEFAULT 1,
    depends_on_template_task_id INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES wbs_templates(id),
    FOREIGN KEY (depends_on_template_task_id) REFERENCES wbs_template_tasks(id)
);
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    milestone_id INTEGER,
    task_name VARCHAR(200) NOT NULL,
    stage VARCHAR(20),
    status VARCHAR(20) DEFAULT 'TODO',
    owner_id INTEGER,
    plan_start DATE,
    plan_end DATE,
    actual_start DATE,
    actual_end DATE,
    progress_percent INTEGER DEFAULT 0,
    weight DECIMAL(5,2) DEFAULT 1,
    block_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (milestone_id) REFERENCES milestones(id),
    FOREIGN KEY (owner_id) REFERENCES employees(id)
);
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    dependency_type VARCHAR(10) DEFAULT 'FS',
    lag_days INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
);
CREATE TABLE progress_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    progress_percent INTEGER,
    update_note TEXT,
    updated_by INTEGER,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (updated_by) REFERENCES employees(id)
);
CREATE TABLE schedule_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    baseline_no VARCHAR(10) DEFAULT 'V1',
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);
CREATE TABLE baseline_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    plan_start DATE,
    plan_end DATE,
    weight DECIMAL(5,2), created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (baseline_id) REFERENCES schedule_baselines(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
CREATE TABLE projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code        VARCHAR(50) NOT NULL UNIQUE,          -- 项目编码
    project_name        VARCHAR(200) NOT NULL,                -- 项目名称
    short_name          VARCHAR(50),                          -- 项目简称

    -- 客户信息
    customer_id         INTEGER,                              -- 客户ID
    customer_name       VARCHAR(200),                         -- 客户名称（冗余）
    customer_contact    VARCHAR(100),                         -- 客户联系人
    customer_phone      VARCHAR(50),                          -- 联系电话

    -- 合同信息
    contract_no         VARCHAR(100),                         -- 合同编号
    contract_amount     DECIMAL(14,2),                        -- 合同金额
    contract_date       DATE,                                 -- 合同签订日期

    -- 项目类型与分类
    project_type        VARCHAR(50) DEFAULT 'STANDARD',       -- 项目类型：STANDARD/UPGRADE/MAINTENANCE
    product_category    VARCHAR(50),                          -- 产品类别：ASSEMBLY_LINE/INSPECTION/PACKAGING等
    industry            VARCHAR(50),                          -- 行业：3C/AUTO/MEDICAL/FOOD等

    -- 三维状态
    stage               VARCHAR(20) DEFAULT 'S1',             -- 阶段：S1-S9
    status              VARCHAR(20) DEFAULT 'ST01',           -- 状态：每阶段细分状态
    health              VARCHAR(10) DEFAULT 'H1',             -- 健康度：H1-H4

    -- 时间计划
    planned_start_date  DATE,                                 -- 计划开始日期
    planned_end_date    DATE,                                 -- 计划结束日期
    actual_start_date   DATE,                                 -- 实际开始日期
    actual_end_date     DATE,                                 -- 实际结束日期

    -- 进度信息
    progress_pct        DECIMAL(5,2) DEFAULT 0,               -- 整体进度百分比

    -- 预算与成本
    budget_amount       DECIMAL(14,2),                        -- 预算金额
    actual_cost         DECIMAL(14,2) DEFAULT 0,              -- 实际成本

    -- 项目团队
    pm_id               INTEGER,                              -- 项目经理ID
    pm_name             VARCHAR(50),                          -- 项目经理姓名（冗余）
    dept_id             INTEGER,                              -- 所属部门

    -- 优先级与标签
    priority            VARCHAR(20) DEFAULT 'NORMAL',         -- 优先级：LOW/NORMAL/HIGH/URGENT
    tags                TEXT,                                 -- 标签JSON数组

    -- 描述
    description         TEXT,                                 -- 项目描述
    requirements        TEXT,                                 -- 项目需求摘要

    -- 附件
    attachments         TEXT,                                 -- 附件列表JSON

    -- 状态
    is_active           BOOLEAN DEFAULT 1,                    -- 是否激活
    is_archived         BOOLEAN DEFAULT 0,                    -- 是否归档

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, source_lead_id VARCHAR(50), evaluation_score DECIMAL(5,2), predicted_win_rate DECIMAL(5,4), outcome VARCHAR(20), loss_reason VARCHAR(50), loss_reason_detail TEXT, salesperson_id INTEGER REFERENCES users(id), `customer_contract_no` VARCHAR(100) DEFAULT NULL, `lead_id` INTEGER DEFAULT NULL, approval_status VARCHAR(20) DEFAULT 'NONE', approval_record_id INTEGER REFERENCES approval_records(id), project_category VARCHAR(20), opportunity_id INTEGER, contract_id INTEGER, erp_synced BOOLEAN DEFAULT 0, erp_sync_time DATETIME, erp_order_no VARCHAR(50), erp_sync_status VARCHAR(20) DEFAULT 'PENDING', invoice_issued BOOLEAN DEFAULT 0, final_payment_completed BOOLEAN DEFAULT 0, final_payment_date DATE, warranty_period_months INTEGER, warranty_start_date DATE, warranty_end_date DATE, implementation_address VARCHAR(500), test_encryption VARCHAR(100), initiation_id INTEGER, stage_template_id INTEGER REFERENCES stage_templates(id), current_stage_instance_id INTEGER, current_node_instance_id INTEGER, template_id INTEGER, template_version_id INTEGER,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (pm_id) REFERENCES users(id),
    FOREIGN KEY (dept_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
INSERT INTO projects VALUES(1,'PRJAPP-854D5B','PRJAPP Smoke Project','PRJAPP-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S1','ST01','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:42:15.490943','2026-01-30 15:42:39.466405',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'NONE',NULL,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO projects VALUES(2,'PRJAPP-E65328','PRJAPP Smoke Project','PRJAPP-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S1','ST01','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:42:47.698148','2026-01-30 15:49:04.494286',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'NONE',NULL,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO projects VALUES(3,'PRJAPP-BA4231','PRJAPP Smoke Project','PRJAPP-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S1','ST01','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:44:11.487025','2026-01-30 15:49:04.501462',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'NONE',NULL,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO projects VALUES(4,'PRJAPP-FDED8B','PRJAPP Smoke Project','PRJAPP-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S1','ST01','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:44:46.206753','2026-01-30 15:49:04.503544',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'NONE',NULL,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO projects VALUES(5,'PRJAPP-8DA55A','PRJAPP Smoke Project','PRJAPP-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S2','ST02','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:44:59.979056','2026-01-30 15:49:04.505491',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'APPROVED',1,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO projects VALUES(6,'PRJWD-B3F216','PRJWD Smoke Project','PRJWD-SMK',NULL,'Smoke Customer',NULL,NULL,NULL,100000,NULL,NULL,NULL,NULL,'S1','ST01','H2','2026-01-30','2026-01-30',NULL,NULL,0,85000,0,22,'Project.Smoke',23,'NORMAL',NULL,NULL,NULL,NULL,1,0,22,'2026-01-30 11:45:00.000285','2026-01-30 15:49:04.507431',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'CANCELLED',NULL,NULL,NULL,NULL,0,NULL,NULL,'PENDING',0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE machines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 所属项目
    machine_code        VARCHAR(50) NOT NULL,                 -- 设备编码
    machine_name        VARCHAR(200) NOT NULL,                -- 设备名称
    machine_no          INTEGER DEFAULT 1,                    -- 设备序号（项目内）

    -- 设备类型
    machine_type        VARCHAR(50),                          -- 设备类型
    specification       TEXT,                                 -- 规格描述

    -- 状态
    stage               VARCHAR(20) DEFAULT 'S1',             -- 设备阶段
    status              VARCHAR(20) DEFAULT 'ST01',           -- 设备状态
    health              VARCHAR(10) DEFAULT 'H1',             -- 健康度

    -- 进度
    progress_pct        DECIMAL(5,2) DEFAULT 0,               -- 设备进度

    -- 时间
    planned_start_date  DATE,                                 -- 计划开始
    planned_end_date    DATE,                                 -- 计划结束
    actual_start_date   DATE,                                 -- 实际开始
    actual_end_date     DATE,                                 -- 实际结束

    -- FAT/SAT信息
    fat_date            DATE,                                 -- FAT日期
    fat_result          VARCHAR(20),                          -- FAT结果
    sat_date            DATE,                                 -- SAT日期
    sat_result          VARCHAR(20),                          -- SAT结果

    -- 发货信息
    ship_date           DATE,                                 -- 发货日期
    ship_address        VARCHAR(500),                         -- 发货地址
    tracking_no         VARCHAR(100),                         -- 物流单号

    -- 备注
    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, machine_code)
);
CREATE TABLE project_stages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 所属项目
    stage_code          VARCHAR(20) NOT NULL,                 -- 阶段编码：S1-S9
    stage_name          VARCHAR(50) NOT NULL,                 -- 阶段名称
    stage_order         INTEGER NOT NULL,                     -- 阶段顺序
    description         TEXT,                                 -- 阶段描述

    -- 计划与实际
    planned_start_date  DATE,
    planned_end_date    DATE,
    actual_start_date   DATE,
    actual_end_date     DATE,

    -- 进度
    progress_pct        INTEGER DEFAULT 0,
    status              VARCHAR(20) DEFAULT 'PENDING',

    -- 门控条件
    gate_conditions     TEXT,                                 -- 进入条件JSON
    required_deliverables TEXT,                               -- 必需交付物JSON

    -- 默认时长
    default_duration_days INTEGER,                            -- 默认工期（天）

    -- 颜色配置
    color               VARCHAR(20),                          -- 显示颜色
    icon                VARCHAR(50),                          -- 图标

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, stage_code)
);
CREATE TABLE project_statuses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id            INTEGER NOT NULL,                     -- 所属阶段ID
    status_code         VARCHAR(20) NOT NULL,                 -- 状态编码
    status_name         VARCHAR(50) NOT NULL,                 -- 状态名称
    status_order        INTEGER NOT NULL,                     -- 状态顺序
    description         TEXT,                                 -- 状态描述

    -- 状态类型
    status_type         VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/MILESTONE/GATE

    -- 自动流转
    auto_next_status    VARCHAR(20),                          -- 自动下一状态

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (stage_id) REFERENCES project_stages(id),
    UNIQUE(stage_id, status_code)
);
CREATE TABLE project_status_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    -- 变更前状态
    old_stage           VARCHAR(20),
    old_status          VARCHAR(20),
    old_health          VARCHAR(10),

    -- 变更后状态
    new_stage           VARCHAR(20),
    new_status          VARCHAR(20),
    new_health          VARCHAR(10),

    -- 变更信息
    change_type         VARCHAR(20) NOT NULL,                 -- STAGE_CHANGE/STATUS_CHANGE/HEALTH_CHANGE
    change_reason       TEXT,                                 -- 变更原因
    change_note         TEXT,                                 -- 变更备注

    -- 操作信息
    changed_by          INTEGER,
    changed_at          DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);
INSERT INTO project_status_logs VALUES(1,1,NULL,'S1','ST01','H1','S1','ST01','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:42:39.465184','2026-01-30 07:42:39','2026-01-30 07:42:39');
INSERT INTO project_status_logs VALUES(2,2,NULL,'S1','ST01','H1','S1','ST01','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:49:04.492931','2026-01-30 07:49:04','2026-01-30 07:49:04');
INSERT INTO project_status_logs VALUES(3,3,NULL,'S1','ST01','H1','S1','ST01','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:49:04.500995','2026-01-30 07:49:04','2026-01-30 07:49:04');
INSERT INTO project_status_logs VALUES(4,4,NULL,'S1','ST01','H1','S1','ST01','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:49:04.503132','2026-01-30 07:49:04','2026-01-30 07:49:04');
INSERT INTO project_status_logs VALUES(5,5,NULL,'S2','ST02','H1','S2','ST02','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:49:04.505088','2026-01-30 07:49:04','2026-01-30 07:49:04');
INSERT INTO project_status_logs VALUES(6,6,NULL,'S1','ST01','H1','S1','ST01','H2','HEALTH_AUTO_CALCULATED',NULL,'系统自动计算健康度：H1 -> H2',NULL,'2026-01-30 15:49:04.507021','2026-01-30 07:49:04','2026-01-30 07:49:04');
CREATE TABLE project_members (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    user_id             INTEGER NOT NULL,                     -- 用户ID
    role_code           VARCHAR(50) NOT NULL,                 -- 角色编码

    -- 分配信息
    allocation_pct      DECIMAL(5,2) DEFAULT 100,             -- 分配比例
    start_date          DATE,                                 -- 开始日期
    end_date            DATE,                                 -- 结束日期

    -- 状态
    is_active           BOOLEAN DEFAULT 1,

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, role_type_id INTEGER REFERENCES project_role_types(id), is_lead BOOLEAN DEFAULT 0, machine_id INTEGER REFERENCES machines(id), lead_member_id INTEGER REFERENCES project_members(id), commitment_level VARCHAR(20), reporting_to_pm BOOLEAN DEFAULT 1, dept_manager_notified BOOLEAN DEFAULT 0,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_code) REFERENCES roles(role_code),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE(project_id, user_id, role_code)
);
CREATE TABLE project_milestones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    milestone_code      VARCHAR(50) NOT NULL,                 -- 里程碑编码
    milestone_name      VARCHAR(200) NOT NULL,                -- 里程碑名称
    milestone_type      VARCHAR(20) DEFAULT 'CUSTOM',         -- GATE/DELIVERY/PAYMENT/CUSTOM

    -- 时间
    planned_date        DATE NOT NULL,                        -- 计划日期
    actual_date         DATE,                                 -- 实际完成日期

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/IN_PROGRESS/COMPLETED/DELAYED

    -- 关联阶段
    stage_code          VARCHAR(20),                          -- 关联阶段

    -- 交付物
    deliverables        TEXT,                                 -- 交付物JSON

    -- 责任人
    owner_id            INTEGER,

    -- 备注
    description         TEXT,
    completion_note     TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, reminder_days INTEGER DEFAULT 7, is_key BOOLEAN DEFAULT 0, remark TEXT,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE project_payment_plans (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID

    payment_no          INTEGER NOT NULL,                     -- 期次
    payment_name        VARCHAR(100) NOT NULL,                -- 款项名称（如：预付款、发货款）
    payment_type        VARCHAR(20) NOT NULL,                 -- ADVANCE/DELIVERY/ACCEPTANCE/WARRANTY

    -- 金额
    payment_ratio       DECIMAL(5,2),                         -- 比例(%)
    planned_amount      DECIMAL(14,2) NOT NULL,               -- 计划金额
    actual_amount       DECIMAL(14,2) DEFAULT 0,              -- 实际收款

    -- 时间
    planned_date        DATE,                                 -- 计划收款日期
    actual_date         DATE,                                 -- 实际收款日期

    -- 触发条件
    trigger_milestone   VARCHAR(50),                          -- 触发里程碑
    trigger_condition   TEXT,                                 -- 触发条件描述

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/INVOICED/PARTIAL/COMPLETED

    -- 发票信息
    invoice_no          VARCHAR(100),                         -- 发票号
    invoice_date        DATE,                                 -- 开票日期
    invoice_amount      DECIMAL(14,2),                        -- 开票金额

    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, contract_id INTEGER REFERENCES contracts(id), milestone_id INTEGER REFERENCES project_milestones(id), invoice_id INTEGER,

    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE project_costs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    cost_type           VARCHAR(50) NOT NULL,                 -- 成本类型
    cost_category       VARCHAR(50) NOT NULL,                 -- 成本分类

    -- 来源
    source_module       VARCHAR(50),                          -- 来源模块
    source_type         VARCHAR(50),                          -- 来源类型
    source_id           INTEGER,                              -- 来源ID
    source_no           VARCHAR(100),                         -- 来源单号

    -- 金额
    amount              DECIMAL(14,2) NOT NULL,               -- 金额
    tax_amount          DECIMAL(12,2) DEFAULT 0,              -- 税额

    -- 描述
    description         TEXT,                                 -- 描述

    -- 时间
    cost_date           DATE NOT NULL,                        -- 成本日期

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE project_documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    doc_type            VARCHAR(50) NOT NULL,                 -- 文档类型
    doc_category        VARCHAR(50),                          -- 文档分类
    doc_name            VARCHAR(200) NOT NULL,                -- 文档名称
    doc_no              VARCHAR(100),                         -- 文档编号
    version             VARCHAR(20) DEFAULT '1.0',            -- 版本号

    -- 文件信息
    file_path           VARCHAR(500) NOT NULL,                -- 文件路径
    file_name           VARCHAR(200) NOT NULL,                -- 原始文件名
    file_size           INTEGER,                              -- 文件大小
    file_type           VARCHAR(50),                          -- 文件类型

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/REVIEW/APPROVED/RELEASED

    -- 审批
    approved_by         INTEGER,
    approved_at         DATETIME,

    -- 描述
    description         TEXT,

    uploaded_by         INTEGER,
    uploaded_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, rd_project_id INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE customers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code       VARCHAR(50) NOT NULL UNIQUE,          -- 客户编码
    customer_name       VARCHAR(200) NOT NULL,                -- 客户名称
    short_name          VARCHAR(50),                          -- 简称

    -- 基本信息
    customer_type       VARCHAR(20) DEFAULT 'ENTERPRISE',     -- ENTERPRISE/INDIVIDUAL
    industry            VARCHAR(50),                          -- 行业
    scale               VARCHAR(20),                          -- 规模

    -- 联系信息
    contact_person      VARCHAR(50),                          -- 联系人
    contact_phone       VARCHAR(50),                          -- 联系电话
    contact_email       VARCHAR(100),                         -- 邮箱
    address             VARCHAR(500),                         -- 地址

    -- 公司信息
    legal_person        VARCHAR(50),                          -- 法人
    tax_no              VARCHAR(50),                          -- 税号
    bank_name           VARCHAR(100),                         -- 开户银行
    bank_account        VARCHAR(50),                          -- 银行账号

    -- 信用信息
    credit_level        VARCHAR(20),                          -- 信用等级
    credit_limit        DECIMAL(14,2),                        -- 信用额度
    payment_terms       VARCHAR(50),                          -- 付款条款

    -- 客户门户
    portal_enabled      BOOLEAN DEFAULT 0,                    -- 是否启用门户
    portal_username     VARCHAR(100),                         -- 门户账号

    -- 状态
    status              VARCHAR(20) DEFAULT 'ACTIVE',         -- ACTIVE/INACTIVE

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code       VARCHAR(50) NOT NULL UNIQUE,          -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500),                         -- 规格型号

    -- 分类
    category_l1         VARCHAR(50),                          -- 一级分类
    category_l2         VARCHAR(50),                          -- 二级分类
    category_l3         VARCHAR(50),                          -- 三级分类
    material_type       VARCHAR(20) DEFAULT 'PURCHASE',       -- PURCHASE/OUTSOURCE/SELF_MADE

    -- 基本属性
    unit                VARCHAR(20) DEFAULT '件',             -- 基本单位
    brand               VARCHAR(100),                         -- 品牌
    model               VARCHAR(100),                         -- 型号

    -- 采购属性
    default_supplier_id INTEGER,                              -- 默认供应商
    lead_time_days      INTEGER DEFAULT 7,                    -- 采购周期(天)
    min_order_qty       DECIMAL(10,2) DEFAULT 1,              -- 最小起订量
    price_unit          DECIMAL(12,4),                        -- 参考单价

    -- 库存属性
    safety_stock        DECIMAL(10,2) DEFAULT 0,              -- 安全库存
    reorder_point       DECIMAL(10,2) DEFAULT 0,              -- 再订货点

    -- 质量属性
    inspection_required BOOLEAN DEFAULT 0,                    -- 是否需要检验
    shelf_life_days     INTEGER,                              -- 保质期(天)

    -- 图纸信息
    drawing_no          VARCHAR(100),                         -- 图号
    drawing_version     VARCHAR(20),                          -- 图纸版本
    drawing_file        VARCHAR(500),                         -- 图纸文件路径

    -- 状态
    status              VARCHAR(20) DEFAULT 'ACTIVE',         -- ACTIVE/INACTIVE/OBSOLETE

    -- 描述
    description         TEXT,
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (default_supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE suppliers (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_code       VARCHAR(50) NOT NULL UNIQUE,          -- 供应商编码
    supplier_name       VARCHAR(200) NOT NULL,                -- 供应商名称
    short_name          VARCHAR(50),                          -- 简称

    -- 分类
    supplier_type       VARCHAR(20) DEFAULT 'MATERIAL',       -- MATERIAL/OUTSOURCE/BOTH
    category            VARCHAR(50),                          -- 供应商分类

    -- 联系信息
    contact_person      VARCHAR(50),                          -- 联系人
    contact_phone       VARCHAR(50),                          -- 联系电话
    contact_email       VARCHAR(100),                         -- 邮箱
    contact_fax         VARCHAR(50),                          -- 传真
    address             VARCHAR(500),                         -- 地址

    -- 公司信息
    legal_person        VARCHAR(50),                          -- 法人
    tax_no              VARCHAR(50),                          -- 税号
    bank_name           VARCHAR(100),                         -- 开户银行
    bank_account        VARCHAR(50),                          -- 银行账号

    -- 合作信息
    cooperation_status  VARCHAR(20) DEFAULT 'ACTIVE',         -- ACTIVE/SUSPENDED/BLACKLIST
    cooperation_level   VARCHAR(20) DEFAULT 'NORMAL',         -- STRATEGIC/IMPORTANT/NORMAL
    contract_start      DATE,                                 -- 合同开始
    contract_end        DATE,                                 -- 合同结束

    -- 付款信息
    payment_terms       VARCHAR(50),                          -- 付款条款
    payment_days        INTEGER DEFAULT 30,                   -- 账期(天)
    currency            VARCHAR(10) DEFAULT 'CNY',            -- 币种
    tax_rate            DECIMAL(5,2) DEFAULT 13,              -- 税率

    -- 评价信息
    quality_rating      DECIMAL(3,2) DEFAULT 0,               -- 质量评分
    delivery_rating     DECIMAL(3,2) DEFAULT 0,               -- 交期评分
    service_rating      DECIMAL(3,2) DEFAULT 0,               -- 服务评分
    overall_rating      DECIMAL(3,2) DEFAULT 0,               -- 综合评分

    -- 资质信息
    certifications      TEXT,                                 -- 资质证书JSON

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE supplier_quotations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id         INTEGER NOT NULL,                     -- 供应商ID
    material_id         INTEGER NOT NULL,                     -- 物料ID

    -- 报价信息
    unit_price          DECIMAL(12,4) NOT NULL,               -- 单价
    currency            VARCHAR(10) DEFAULT 'CNY',            -- 币种
    min_qty             DECIMAL(10,2) DEFAULT 1,              -- 最小数量
    price_break_qty     DECIMAL(10,2),                        -- 阶梯数量
    price_break_price   DECIMAL(12,4),                        -- 阶梯价格

    -- 交期
    lead_time_days      INTEGER,                              -- 交期(天)

    -- 有效期
    valid_from          DATE,                                 -- 有效开始
    valid_to            DATE,                                 -- 有效结束

    -- 状态
    is_preferred        BOOLEAN DEFAULT 0,                    -- 是否首选
    is_active           BOOLEAN DEFAULT 1,                    -- 是否有效

    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE bom_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID（可选）

    version_no          VARCHAR(20) NOT NULL,                 -- 版本号
    version_name        VARCHAR(100),                         -- 版本名称

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/REVIEW/APPROVED/RELEASED
    is_current          BOOLEAN DEFAULT 0,                    -- 是否当前版本

    -- 来源
    source_version_id   INTEGER,                              -- 来源版本（升版时）

    -- 统计
    total_items         INTEGER DEFAULT 0,                    -- 物料总数
    total_amount        DECIMAL(14,2) DEFAULT 0,              -- 预估总金额

    -- 审批
    approved_by         INTEGER,
    approved_at         DATETIME,

    -- 备注
    change_note         TEXT,                                 -- 变更说明

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (source_version_id) REFERENCES bom_versions(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE bom_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_version_id      INTEGER NOT NULL,                     -- BOM版本ID
    material_id         INTEGER,                              -- 物料ID（标准件）

    -- 层级
    parent_item_id      INTEGER,                              -- 父级物料行ID
    level               INTEGER DEFAULT 1,                    -- 层级
    item_no             VARCHAR(20),                          -- 项号

    -- 物料信息（允许非标准物料）
    material_code       VARCHAR(50) NOT NULL,                 -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500),                         -- 规格
    unit                VARCHAR(20) DEFAULT '件',             -- 单位

    -- 数量
    quantity            DECIMAL(10,4) NOT NULL,               -- 数量
    unit_price          DECIMAL(12,4),                        -- 预估单价
    amount              DECIMAL(14,2),                        -- 金额

    -- 采购属性
    source_type         VARCHAR(20) DEFAULT 'PURCHASE',       -- PURCHASE/OUTSOURCE/SELF_MADE/STOCK
    supplier_id         INTEGER,                              -- 指定供应商
    lead_time_days      INTEGER,                              -- 交期

    -- 需求时间
    required_date       DATE,                                 -- 需求日期

    -- 图纸
    drawing_no          VARCHAR(100),                         -- 图号
    drawing_version     VARCHAR(20),                          -- 图纸版本

    -- 齐套状态
    ordered_qty         DECIMAL(10,4) DEFAULT 0,              -- 已订购数量
    received_qty        DECIMAL(10,4) DEFAULT 0,              -- 已到货数量
    ready_status        VARCHAR(20) DEFAULT 'NOT_READY',      -- NOT_READY/PARTIAL/READY

    -- 备注
    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bom_version_id) REFERENCES bom_versions(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (parent_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);
CREATE TABLE purchase_requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_no          VARCHAR(50) NOT NULL UNIQUE,          -- 申请单号
    project_id          INTEGER,                              -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 申请信息
    request_type        VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/URGENT
    request_reason      TEXT,                                 -- 申请原因
    required_date       DATE,                                 -- 需求日期

    -- 金额
    total_amount        DECIMAL(14,2) DEFAULT 0,              -- 总金额

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/SUBMITTED/APPROVED/REJECTED/CLOSED

    -- 审批
    approved_by         INTEGER,
    approved_at         DATETIME,
    approval_note       TEXT,

    -- 申请人
    requested_by        INTEGER,
    requested_at        DATETIME,

    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, supplier_id INTEGER, source_type VARCHAR(20) DEFAULT 'MANUAL', source_id INTEGER, auto_po_created BOOLEAN DEFAULT 0, auto_po_created_at DATETIME, auto_po_created_by INTEGER,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE purchase_request_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id          INTEGER NOT NULL,                     -- 申请单ID
    bom_item_id         INTEGER,                              -- BOM行ID
    material_id         INTEGER,                              -- 物料ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,
    specification       VARCHAR(500),
    unit                VARCHAR(20) DEFAULT '件',

    -- 数量
    quantity            DECIMAL(10,4) NOT NULL,               -- 申请数量
    unit_price          DECIMAL(12,4),                        -- 预估单价
    amount              DECIMAL(14,2),                        -- 金额

    -- 需求日期
    required_date       DATE,

    -- 已采购数量
    ordered_qty         DECIMAL(10,4) DEFAULT 0,

    remark              TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (request_id) REFERENCES purchase_requests(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE purchase_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no            VARCHAR(50) NOT NULL UNIQUE,          -- 订单号
    project_id          INTEGER,                              -- 项目ID
    supplier_id         INTEGER NOT NULL,                     -- 供应商ID

    -- 订单信息
    order_type          VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/URGENT/FRAMEWORK
    order_date          DATE NOT NULL,                        -- 订单日期

    -- 时间
    required_date       DATE,                                 -- 要求交期
    confirmed_date      DATE,                                 -- 确认交期

    -- 金额
    total_quantity      DECIMAL(12,2) DEFAULT 0,              -- 总数量
    subtotal            DECIMAL(14,2) DEFAULT 0,              -- 小计
    tax_rate            DECIMAL(5,2) DEFAULT 13,              -- 税率
    tax_amount          DECIMAL(12,2) DEFAULT 0,              -- 税额
    total_amount        DECIMAL(14,2) DEFAULT 0,              -- 价税合计

    -- 付款
    payment_terms       VARCHAR(50),                          -- 付款条款
    currency            VARCHAR(10) DEFAULT 'CNY',            -- 币种

    -- 收货地址
    delivery_address    VARCHAR(500),                         -- 收货地址
    receiver            VARCHAR(50),                          -- 收货人
    receiver_phone      VARCHAR(50),                          -- 联系电话

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/SUBMITTED/CONFIRMED/PARTIAL/COMPLETED/CLOSED

    -- 审批
    approved_by         INTEGER,
    approved_at         DATETIME,

    -- 收货统计
    received_amount     DECIMAL(14,2) DEFAULT 0,              -- 已收货金额

    remark              TEXT,
    internal_note       TEXT,                                 -- 内部备注

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, source_request_id INTEGER, order_title VARCHAR(200), amount_with_tax DECIMAL(14,2) DEFAULT 0, promised_date DATE, payment_status VARCHAR(20) DEFAULT 'UNPAID', paid_amount DECIMAL(14,2) DEFAULT 0, submitted_at DATETIME, approval_note TEXT, contract_no VARCHAR(100),

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE purchase_order_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 订单ID
    pr_item_id          INTEGER,                              -- 采购申请行ID
    bom_item_id         INTEGER,                              -- BOM行ID
    material_id         INTEGER,                              -- 物料ID

    item_no             INTEGER NOT NULL,                     -- 行号

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,
    specification       VARCHAR(500),
    unit                VARCHAR(20) DEFAULT '件',

    -- 数量价格
    quantity            DECIMAL(10,4) NOT NULL,               -- 数量
    unit_price          DECIMAL(12,4) NOT NULL,               -- 单价
    amount              DECIMAL(14,2) NOT NULL,               -- 金额

    -- 交期
    required_date       DATE,                                 -- 要求交期

    -- 收货
    received_qty        DECIMAL(10,4) DEFAULT 0,              -- 已收数量
    qualified_qty       DECIMAL(10,4) DEFAULT 0,              -- 合格数量
    rejected_qty        DECIMAL(10,4) DEFAULT 0,              -- 不合格数量

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PARTIAL/COMPLETED

    remark              TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (pr_item_id) REFERENCES purchase_request_items(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE goods_receipts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no          VARCHAR(50) NOT NULL UNIQUE,          -- 收货单号
    order_id            INTEGER NOT NULL,                     -- 采购订单ID
    supplier_id         INTEGER NOT NULL,                     -- 供应商ID

    -- 收货信息
    receipt_date        DATE NOT NULL,                        -- 收货日期
    receipt_type        VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/RETURN

    -- 物流信息
    tracking_no         VARCHAR(100),                         -- 物流单号
    carrier             VARCHAR(100),                         -- 承运商

    -- 总数量
    total_quantity      DECIMAL(12,2) DEFAULT 0,

    -- 检验状态
    inspection_status   VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PASSED/REJECTED/PARTIAL

    -- 入库
    warehouse_in_status VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PARTIAL/COMPLETED

    received_by         INTEGER,                              -- 收货人

    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (received_by) REFERENCES users(id)
);
CREATE TABLE goods_receipt_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id          INTEGER NOT NULL,                     -- 收货单ID
    po_item_id          INTEGER NOT NULL,                     -- 采购订单行ID
    material_id         INTEGER,                              -- 物料ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,

    -- 数量
    received_qty        DECIMAL(10,4) NOT NULL,               -- 收货数量
    qualified_qty       DECIMAL(10,4) DEFAULT 0,              -- 合格数量
    rejected_qty        DECIMAL(10,4) DEFAULT 0,              -- 不合格数量

    -- 批次
    batch_no            VARCHAR(50),                          -- 批次号

    -- 检验
    inspection_result   VARCHAR(20),                          -- PASSED/REJECTED/CONDITIONAL
    inspection_note     TEXT,                                 -- 检验备注

    -- 入库
    warehouse_in_qty    DECIMAL(10,4) DEFAULT 0,              -- 入库数量

    remark              TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (receipt_id) REFERENCES goods_receipts(id),
    FOREIGN KEY (po_item_id) REFERENCES purchase_order_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE shortage_alerts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID
    bom_item_id         INTEGER,                              -- BOM行ID
    material_id         INTEGER,                              -- 物料ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,

    -- 需求
    required_qty        DECIMAL(10,4) NOT NULL,               -- 需求数量
    required_date       DATE,                                 -- 需求日期

    -- 当前状态
    ordered_qty         DECIMAL(10,4) DEFAULT 0,              -- 已订购
    received_qty        DECIMAL(10,4) DEFAULT 0,              -- 已到货
    shortage_qty        DECIMAL(10,4) NOT NULL,               -- 短缺数量

    -- 预警级别
    alert_level         VARCHAR(20) DEFAULT 'WARNING',        -- WARNING/CRITICAL/URGENT

    -- 处理状态
    status              VARCHAR(20) DEFAULT 'OPEN',           -- OPEN/PROCESSING/RESOLVED/CLOSED

    -- 处理信息
    handled_by          INTEGER,
    handled_at          DATETIME,
    handle_note         TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (handled_by) REFERENCES users(id)
);
CREATE TABLE material_categories (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code       VARCHAR(50) NOT NULL UNIQUE,          -- 分类编码
    category_name       VARCHAR(100) NOT NULL,                -- 分类名称
    parent_id           INTEGER,                              -- 父分类ID
    level               INTEGER DEFAULT 1,                    -- 层级
    sort_order          INTEGER DEFAULT 0,                    -- 排序

    description         TEXT,
    is_active           BOOLEAN DEFAULT 1,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES material_categories(id)
);
CREATE TABLE role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(30) UNIQUE NOT NULL,
    template_name VARCHAR(50) NOT NULL,
    role_type VARCHAR(20) NOT NULL DEFAULT 'BUSINESS',
    scope_type VARCHAR(20) DEFAULT 'GLOBAL',
    data_scope VARCHAR(20) DEFAULT 'PROJECT',
    level INTEGER DEFAULT 2,
    description TEXT,
    permission_snapshot TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO role_templates VALUES(9,'TPL_PM','项目经理模板','BUSINESS','GLOBAL','PROJECT',2,'标准项目经理权限模板，包含项目管理全套权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(10,'TPL_ENGINEER','工程师模板','BUSINESS','GLOBAL','PROJECT',3,'标准工程师权限模板，包含任务执行与交付物权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(11,'TPL_PMC','PMC模板','BUSINESS','GLOBAL','DEPT',2,'计划管理权限模板，包含计划与物料管理权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(12,'TPL_SALES','销售模板','BUSINESS','GLOBAL','OWN',3,'销售专员权限模板，包含商机与合同权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(13,'TPL_FINANCE','财务模板','BUSINESS','GLOBAL','ALL',3,'财务专员权限模板，包含开票与收款权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(14,'TPL_QA','质量模板','BUSINESS','GLOBAL','PROJECT',3,'质量工程师权限模板，包含验收与问题管理权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(15,'TPL_PURCHASE','采购模板','BUSINESS','GLOBAL','DEPT',3,'采购专员权限模板，包含采购与外协权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO role_templates VALUES(16,'TPL_VIEWER','只读模板','CUSTOM','GLOBAL','ALL',4,'只读权限模板，仅包含查看权限',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE role_template_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (template_id) REFERENCES role_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);
CREATE TABLE user_role_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    scope_type VARCHAR(20) DEFAULT 'GLOBAL',
    scope_id INTEGER,
    assigned_by INTEGER NOT NULL,
    approved_by INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',
    effective_from DATETIME,
    effective_until DATETIME,
    assignment_reason TEXT,
    revoke_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE role_assignment_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    approver_id INTEGER NOT NULL,
    decision VARCHAR(20) NOT NULL,
    comment TEXT,
    decided_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assignment_id) REFERENCES user_role_assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code VARCHAR(20) UNIQUE NOT NULL,
    dept_name VARCHAR(50) NOT NULL,
    parent_id INTEGER,
    manager_id INTEGER,
    level INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES departments(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);
INSERT INTO departments VALUES(12,'ROOT','公司',NULL,NULL,0,0,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(13,'TECH','技术中心',12,NULL,1,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(14,'SALES','销售部',12,NULL,1,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(15,'FINANCE','财务部',12,NULL,1,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(16,'PURCHASE','采购部',12,NULL,1,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(17,'QA','质量部',12,NULL,1,5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(18,'PMC','计划部',12,NULL,1,6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(19,'MECH','机械部',13,NULL,2,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(20,'ELEC','电气部',13,NULL,2,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(21,'SOFT','软件部',13,NULL,2,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(22,'DEBUG','调试部',13,NULL,2,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO departments VALUES(23,'SMOKE','Smoke Test Dept',NULL,NULL,1,0,1,'2026-01-30 11:42:15.480327','2026-01-30 11:42:15.480497');
CREATE TABLE department_default_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);
INSERT INTO department_default_roles VALUES(1,8,30,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(2,9,31,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(3,10,32,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(4,11,38,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(5,5,34,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(6,4,35,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(7,3,36,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(8,6,33,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(9,7,27,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(10,19,30,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(11,20,31,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(12,21,32,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(13,22,38,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(14,16,34,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(15,15,35,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(16,14,36,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(17,17,33,1,'2026-01-28 06:47:10');
INSERT INTO department_default_roles VALUES(18,18,27,1,'2026-01-28 06:47:10');
CREATE TABLE department_role_admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    can_assign_roles TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE role_exclusions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id_a INTEGER NOT NULL,
    role_id_b INTEGER NOT NULL,
    exclusion_type VARCHAR(20) DEFAULT 'MUTUAL',
    reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id_a) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id_b) REFERENCES roles(id) ON DELETE CASCADE
);
INSERT INTO role_exclusions VALUES(1,34,35,'MUTUAL','职责分离：采购与财务不得兼任，防止舞弊风险',1,'2026-01-28 06:47:09');
INSERT INTO role_exclusions VALUES(2,29,35,'MUTUAL','职责分离：采购主管与财务专员不得兼任',1,'2026-01-28 06:47:09');
INSERT INTO role_exclusions VALUES(3,34,23,'MUTUAL','职责分离：采购专员与财务总监不得兼任',1,'2026-01-28 06:47:09');
INSERT INTO role_exclusions VALUES(4,28,26,'MUTUAL','验收独立性：同一项目内质量主管与项目经理不得兼任（项目维度）',1,'2026-01-28 06:47:09');
INSERT INTO role_exclusions VALUES(5,34,35,'MUTUAL','职责分离：采购与财务不得兼任，防止舞弊风险',1,'2026-01-28 06:47:10');
INSERT INTO role_exclusions VALUES(6,29,35,'MUTUAL','职责分离：采购主管与财务专员不得兼任',1,'2026-01-28 06:47:10');
INSERT INTO role_exclusions VALUES(7,34,23,'MUTUAL','职责分离：采购专员与财务总监不得兼任',1,'2026-01-28 06:47:10');
INSERT INTO role_exclusions VALUES(8,28,26,'MUTUAL','验收独立性：同一项目内质量主管与项目经理不得兼任（项目维度）',1,'2026-01-28 06:47:10');
CREATE TABLE role_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(50) NOT NULL,
    operator_id INTEGER NOT NULL,
    target_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (operator_id) REFERENCES users(id)
);
CREATE TABLE quote_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE contract_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE invoice_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_role VARCHAR(50) NOT NULL,
    approver_id INTEGER,
    approver_name VARCHAR(50),
    approval_result VARCHAR(20),
    approval_opinion TEXT,
    status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    due_date DATETIME,
    is_overdue BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE acceptance_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,          -- 模板编码
    template_name       VARCHAR(200) NOT NULL,                -- 模板名称
    acceptance_type     VARCHAR(20) NOT NULL,                 -- FAT/SAT/FINAL
    equipment_type      VARCHAR(50),                          -- 设备类型
    version             VARCHAR(20) DEFAULT '1.0',            -- 版本号
    description         TEXT,                                 -- 模板说明
    is_system           BOOLEAN DEFAULT 0,                    -- 是否系统预置
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用
    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE template_categories (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,                     -- 所属模板
    category_code       VARCHAR(20) NOT NULL,                 -- 分类编码
    category_name       VARCHAR(100) NOT NULL,                -- 分类名称
    weight              DECIMAL(5,2) DEFAULT 0,               -- 权重百分比
    sort_order          INTEGER DEFAULT 0,                    -- 排序
    is_required         BOOLEAN DEFAULT 1,                    -- 是否必检分类
    description         TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                                 -- 分类说明

    FOREIGN KEY (template_id) REFERENCES acceptance_templates(id),
    UNIQUE(template_id, category_code)
);
CREATE TABLE template_check_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id         INTEGER NOT NULL,                     -- 所属分类
    item_code           VARCHAR(50) NOT NULL,                 -- 检查项编码
    item_name           VARCHAR(200) NOT NULL,                -- 检查项名称
    check_method        TEXT,                                 -- 检查方法
    acceptance_criteria TEXT,                                 -- 验收标准
    standard_value      VARCHAR(100),                         -- 标准值
    tolerance_min       VARCHAR(50),                          -- 下限
    tolerance_max       VARCHAR(50),                          -- 上限
    unit                VARCHAR(20),                          -- 单位
    is_required         BOOLEAN DEFAULT 1,                    -- 是否必检项
    is_key_item         BOOLEAN DEFAULT 0,                    -- 是否关键项
    sort_order          INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                    -- 排序

    FOREIGN KEY (category_id) REFERENCES template_categories(id)
);
CREATE TABLE acceptance_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no            VARCHAR(50) NOT NULL UNIQUE,          -- 验收单号
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID
    acceptance_type     VARCHAR(20) NOT NULL,                 -- FAT/SAT/FINAL
    template_id         INTEGER,                              -- 使用的模板

    -- 验收信息
    planned_date        DATE,                                 -- 计划验收日期
    actual_start_date   DATETIME,                             -- 实际开始时间
    actual_end_date     DATETIME,                             -- 实际结束时间
    location            VARCHAR(200),                         -- 验收地点

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 验收状态

    -- 统计
    total_items         INTEGER DEFAULT 0,                    -- 检查项总数
    passed_items        INTEGER DEFAULT 0,                    -- 通过项数
    failed_items        INTEGER DEFAULT 0,                    -- 不通过项数
    na_items            INTEGER DEFAULT 0,                    -- 不适用项数
    pass_rate           DECIMAL(5,2) DEFAULT 0,               -- 通过率

    -- 结论
    overall_result      VARCHAR(20),                          -- PASSED/FAILED/CONDITIONAL
    conclusion          TEXT,                                 -- 验收结论
    conditions          TEXT,                                 -- 有条件通过的条件说明

    -- 签字确认
    qa_signer_id        INTEGER,                              -- QA签字人
    qa_signed_at        DATETIME,                             -- QA签字时间
    customer_signer     VARCHAR(100),                         -- 客户签字人
    customer_signed_at  DATETIME,                             -- 客户签字时间
    customer_signature  TEXT,                                 -- 客户电子签名

    -- 附件
    report_file_path    VARCHAR(500),                         -- 验收报告文件路径

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, customer_signed_file_path VARCHAR(500) DEFAULT NULL, is_officially_completed BOOLEAN DEFAULT 0, officially_completed_at DATETIME DEFAULT NULL,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (template_id) REFERENCES acceptance_templates(id),
    FOREIGN KEY (qa_signer_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE acceptance_order_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    template_item_id    INTEGER,                              -- 模板检查项ID

    -- 检查项信息
    category_code       VARCHAR(20) NOT NULL,
    category_name       VARCHAR(100) NOT NULL,
    item_code           VARCHAR(50) NOT NULL,
    item_name           VARCHAR(200) NOT NULL,
    check_method        TEXT,
    acceptance_criteria TEXT,
    standard_value      VARCHAR(100),
    tolerance_min       VARCHAR(50),
    tolerance_max       VARCHAR(50),
    unit                VARCHAR(20),
    is_required         BOOLEAN DEFAULT 1,
    is_key_item         BOOLEAN DEFAULT 0,
    sort_order          INTEGER DEFAULT 0,

    -- 检查结果
    result_status       VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PASSED/FAILED/NA/CONDITIONAL
    actual_value        VARCHAR(100),                         -- 实际值
    deviation           VARCHAR(100),                         -- 偏差
    remark              TEXT,                                 -- 备注

    -- 检查记录
    checked_by          INTEGER,                              -- 检查人
    checked_at          DATETIME,                             -- 检查时间

    -- 复验信息
    retry_count         INTEGER DEFAULT 0,                    -- 复验次数
    last_retry_at       DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                             -- 最后复验时间

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (template_item_id) REFERENCES template_check_items(id),
    FOREIGN KEY (checked_by) REFERENCES users(id)
);
CREATE TABLE acceptance_issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_no            VARCHAR(50) NOT NULL UNIQUE,          -- 问题编号
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    order_item_id       INTEGER,                              -- 关联检查项

    -- 问题信息
    issue_type          VARCHAR(20) NOT NULL,                 -- DEFECT/DEVIATION/SUGGESTION
    severity            VARCHAR(20) NOT NULL,                 -- CRITICAL/MAJOR/MINOR
    title               VARCHAR(200) NOT NULL,                -- 问题标题
    description         TEXT NOT NULL,                        -- 问题描述
    found_at            DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 发现时间
    found_by            INTEGER,                              -- 发现人

    -- 处理信息
    status              VARCHAR(20) DEFAULT 'OPEN',           -- OPEN/PROCESSING/RESOLVED/CLOSED/DEFERRED
    assigned_to         INTEGER,                              -- 处理负责人
    due_date            DATE,                                 -- 要求完成日期

    -- 解决信息
    solution            TEXT,                                 -- 解决方案
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人

    -- 验证信息
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人
    verified_result     VARCHAR(20),                          -- VERIFIED/REJECTED

    -- 是否阻塞验收
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞验收通过

    -- 附件
    attachments         TEXT,                                 -- 附件列表JSON

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (order_item_id) REFERENCES acceptance_order_items(id),
    FOREIGN KEY (found_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);
CREATE TABLE issue_follow_ups (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id            INTEGER NOT NULL,                     -- 问题ID
    action_type         VARCHAR(20) NOT NULL,                 -- COMMENT/STATUS_CHANGE/ASSIGN/RESOLVE/VERIFY
    action_content      TEXT NOT NULL,                        -- 操作内容
    old_value           VARCHAR(100),                         -- 原值
    new_value           VARCHAR(100),                         -- 新值
    attachments         TEXT,                                 -- 附件JSON
    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (issue_id) REFERENCES acceptance_issues(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE acceptance_signatures (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    signer_type         VARCHAR(20) NOT NULL,                 -- QA/PM/CUSTOMER/WITNESS
    signer_role         VARCHAR(50),                          -- 签字人角色
    signer_name         VARCHAR(100) NOT NULL,                -- 签字人姓名
    signer_user_id      INTEGER,                              -- 系统用户ID
    signer_company      VARCHAR(200),                         -- 签字人公司
    signature_data      TEXT,                                 -- 电子签名数据
    signed_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address          VARCHAR(50),                          -- 签字IP
    device_info         VARCHAR(200), created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                         -- 设备信息

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (signer_user_id) REFERENCES users(id)
);
CREATE TABLE acceptance_reports (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 验收单ID
    report_no           VARCHAR(50) NOT NULL UNIQUE,          -- 报告编号
    report_type         VARCHAR(20) NOT NULL,                 -- DRAFT/OFFICIAL
    version             INTEGER DEFAULT 1,                    -- 版本号

    -- 报告内容
    report_content      TEXT,                                 -- 报告正文

    -- 文件信息
    file_path           VARCHAR(500),                         -- PDF文件路径
    file_size           INTEGER,                              -- 文件大小
    file_hash           VARCHAR(64),                          -- 文件哈希

    generated_at        DATETIME,                             -- 生成时间
    generated_by        INTEGER,                              -- 生成人

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (generated_by) REFERENCES users(id)
);
CREATE TABLE alert_rules (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           VARCHAR(50) NOT NULL UNIQUE,          -- 规则编码
    rule_name           VARCHAR(200) NOT NULL,                -- 规则名称
    rule_type           VARCHAR(30) NOT NULL,                 -- 规则类型

    -- 监控对象
    target_type         VARCHAR(30) NOT NULL,                 -- PROJECT/MACHINE/PURCHASE/OUTSOURCING/MATERIAL/ACCEPTANCE
    target_field        VARCHAR(100),                         -- 监控字段

    -- 触发条件
    condition_type      VARCHAR(20) NOT NULL,                 -- THRESHOLD/DEVIATION/OVERDUE/CUSTOM
    condition_operator  VARCHAR(10),                          -- GT/LT/EQ/GTE/LTE/BETWEEN
    threshold_value     VARCHAR(100),                         -- 阈值
    threshold_min       VARCHAR(50),                          -- 阈值下限
    threshold_max       VARCHAR(50),                          -- 阈值上限
    condition_expr      TEXT,                                 -- 自定义条件表达式

    -- 预警级别
    alert_level         VARCHAR(20) DEFAULT 'WARNING',        -- INFO/WARNING/CRITICAL/URGENT

    -- 提前预警
    advance_days        INTEGER DEFAULT 0,                    -- 提前预警天数

    -- 通知配置
    notify_channels     TEXT,                                 -- 通知渠道JSON: ["EMAIL","SMS","SYSTEM"]
    notify_roles        TEXT,                                 -- 通知角色JSON
    notify_users        TEXT,                                 -- 指定通知用户JSON

    -- 执行配置
    check_frequency     VARCHAR(20) DEFAULT 'DAILY',          -- REALTIME/HOURLY/DAILY/WEEKLY
    is_enabled          BOOLEAN DEFAULT 1,                    -- 是否启用
    is_system           BOOLEAN DEFAULT 0,                    -- 是否系统预置

    -- 描述
    description         TEXT,                                 -- 规则说明
    solution_guide      TEXT,                                 -- 处理指南

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
INSERT INTO alert_rules VALUES(1,'WORK_REPORT_TIMEOUT','报工超时提醒','SCHEDULE_DELAY','WORK_ORDER',NULL,'THRESHOLD','GT','24',NULL,NULL,NULL,'WARNING',0,NULL,NULL,NULL,'DAILY',1,1,'当工单超过24小时未报工时触发预警',NULL,NULL,'2026-01-28 15:00:00.025242','2026-01-28 15:00:00.025245');
INSERT INTO alert_rules VALUES(2,'OVERDUE_RECEIVABLE','逾期应收预警','FINANCIAL','INVOICE',NULL,'THRESHOLD','GT','0',NULL,NULL,NULL,'WARNING',0,NULL,NULL,NULL,'DAILY',1,1,'当发票已逾期且未完全收款时触发预警',NULL,NULL,'2026-01-29 10:30:00.107850','2026-01-29 10:30:00.107853');
INSERT INTO alert_rules VALUES(3,'PRODUCTION_PLAN','生产计划预警','SCHEDULE_DELAY','PRODUCTION_PLAN',NULL,'THRESHOLD','LT','80',NULL,NULL,NULL,'WARNING',0,NULL,NULL,NULL,'DAILY',1,1,'当生产计划进度低于80%或计划日期临近时触发预警',NULL,NULL,'2026-01-29 11:00:00.068973','2026-01-29 11:00:00.068977');
INSERT INTO alert_rules VALUES(4,'MILESTONE_WARNING','里程碑即将到期预警','MILESTONE_DUE','MILESTONE',NULL,'THRESHOLD','LT','3',NULL,NULL,NULL,'WARNING',0,NULL,NULL,NULL,'DAILY',1,1,'当里程碑将在3天内到期时触发预警',NULL,NULL,'2026-01-30 15:30:34.014717','2026-01-30 15:30:34.014719');
INSERT INTO alert_rules VALUES(5,'MILESTONE_OVERDUE','里程碑逾期预警','MILESTONE_DUE','MILESTONE',NULL,'THRESHOLD','LT','0',NULL,NULL,NULL,'CRITICAL',0,NULL,NULL,NULL,'DAILY',1,1,'当里程碑已逾期时触发预警',NULL,NULL,'2026-01-30 15:30:34.015550','2026-01-30 15:30:34.015551');
CREATE TABLE alert_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_no            VARCHAR(50) NOT NULL UNIQUE,          -- 预警编号
    rule_id             INTEGER NOT NULL,                     -- 触发的规则ID

    -- 预警对象
    target_type         VARCHAR(30) NOT NULL,                 -- 对象类型
    target_id           INTEGER NOT NULL,                     -- 对象ID
    target_no           VARCHAR(100),                         -- 对象编号
    target_name         VARCHAR(200),                         -- 对象名称

    -- 关联项目
    project_id          INTEGER,                              -- 关联项目ID
    machine_id          INTEGER,                              -- 关联设备ID

    -- 预警信息
    alert_level         VARCHAR(20) NOT NULL,                 -- INFO/WARNING/CRITICAL/URGENT
    alert_title         VARCHAR(200) NOT NULL,                -- 预警标题
    alert_content       TEXT NOT NULL,                        -- 预警内容
    alert_data          TEXT,                                 -- 预警数据JSON

    -- 触发信息
    triggered_at        DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 触发时间
    trigger_value       VARCHAR(100),                         -- 触发时的值
    threshold_value     VARCHAR(100),                         -- 阈值

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/ACKNOWLEDGED/PROCESSING/RESOLVED/IGNORED/EXPIRED

    -- 确认信息
    acknowledged_by     INTEGER,                              -- 确认人
    acknowledged_at     DATETIME,                             -- 确认时间

    -- 处理信息
    handler_id          INTEGER,                              -- 处理人
    handle_start_at     DATETIME,                             -- 开始处理时间
    handle_end_at       DATETIME,                             -- 处理完成时间
    handle_result       TEXT,                                 -- 处理结果
    handle_note         TEXT,                                 -- 处理说明

    -- 是否升级
    is_escalated        BOOLEAN DEFAULT 0,                    -- 是否升级
    escalated_at        DATETIME,                             -- 升级时间
    escalated_to        INTEGER,                              -- 升级给谁

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (acknowledged_by) REFERENCES users(id),
    FOREIGN KEY (handler_id) REFERENCES users(id),
    FOREIGN KEY (escalated_to) REFERENCES users(id)
);
INSERT INTO alert_records VALUES(1,'ALT-DL-1-20260130160600',1,'project',1,'PRJAPP-854D5B','PRJAPP Smoke Project',1,NULL,'CRITICAL','项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.814501',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816268','2026-01-30 16:06:00.816269');
INSERT INTO alert_records VALUES(2,'ALT-DL-2-20260130160600',1,'project',2,'PRJAPP-E65328','PRJAPP Smoke Project',2,NULL,'CRITICAL','项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.814896',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816269','2026-01-30 16:06:00.816269');
INSERT INTO alert_records VALUES(3,'ALT-DL-3-20260130160600',1,'project',3,'PRJAPP-BA4231','PRJAPP Smoke Project',3,NULL,'CRITICAL','项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.815081',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816270','2026-01-30 16:06:00.816270');
INSERT INTO alert_records VALUES(4,'ALT-DL-4-20260130160600',1,'project',4,'PRJAPP-FDED8B','PRJAPP Smoke Project',4,NULL,'CRITICAL','项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.815265',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816270','2026-01-30 16:06:00.816271');
INSERT INTO alert_records VALUES(5,'ALT-DL-5-20260130160600',1,'project',5,'PRJAPP-8DA55A','PRJAPP Smoke Project',5,NULL,'CRITICAL','项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.815456',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816271','2026-01-30 16:06:00.816271');
INSERT INTO alert_records VALUES(6,'ALT-DL-6-20260130160600',1,'project',6,'PRJWD-B3F216','PRJWD Smoke Project',6,NULL,'CRITICAL','项目截止日期预警','项目 "PRJWD Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。',NULL,'2026-01-30 16:06:00.815644',NULL,NULL,'PENDING',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,'2026-01-30 16:06:00.816271','2026-01-30 16:06:00.816272');
CREATE TABLE alert_notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id            INTEGER NOT NULL,                     -- 预警记录ID

    -- 通知信息
    notify_channel      VARCHAR(20) NOT NULL,                 -- EMAIL/SMS/SYSTEM/WECHAT
    notify_target       VARCHAR(200) NOT NULL,                -- 通知目标(邮箱/手机/用户ID)
    notify_user_id      INTEGER,                              -- 通知用户ID

    -- 通知内容
    notify_title        VARCHAR(200),                         -- 通知标题
    notify_content      TEXT,                                 -- 通知内容

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/SENT/FAILED/READ
    sent_at             DATETIME,                             -- 发送时间
    read_at             DATETIME,                             -- 阅读时间
    error_message       TEXT,                                 -- 错误信息

    -- 重试
    retry_count         INTEGER DEFAULT 0,                    -- 重试次数
    next_retry_at       DATETIME,                             -- 下次重试时间

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (alert_id) REFERENCES alert_records(id),
    FOREIGN KEY (notify_user_id) REFERENCES users(id)
);
INSERT INTO alert_notifications VALUES(1,6,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJWD Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.126146','2026-01-30 16:06:00.876306','2026-01-31 18:15:00.134272');
INSERT INTO alert_notifications VALUES(2,5,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.127076','2026-01-30 16:06:00.876307','2026-01-31 18:15:00.134274');
INSERT INTO alert_notifications VALUES(3,4,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.127442','2026-01-30 16:06:00.876308','2026-01-31 18:15:00.134274');
INSERT INTO alert_notifications VALUES(4,3,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.127778','2026-01-30 16:06:00.876308','2026-01-31 18:15:00.134275');
INSERT INTO alert_notifications VALUES(5,2,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.129918','2026-01-30 16:06:00.876309','2026-01-31 18:15:00.134275');
INSERT INTO alert_notifications VALUES(6,1,'SYSTEM','22',22,'项目截止日期预警','项目 "PRJAPP Smoke Project" 将在 0 天后截止（2026-01-30），当前进度 0%。','FAILED',NULL,NULL,'''NotificationRequest'' object has no attribute ''force_send''',4,'2026-01-31 19:15:00.130288','2026-01-30 16:06:00.876310','2026-01-31 18:15:00.134275');
CREATE TABLE exception_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_no            VARCHAR(50) NOT NULL UNIQUE,          -- 异常编号

    -- 异常来源
    source_type         VARCHAR(30) NOT NULL,                 -- ALERT/MANUAL/ACCEPTANCE/OUTSOURCING/OTHER
    source_id           INTEGER,                              -- 来源ID
    alert_id            INTEGER,                              -- 关联预警ID

    -- 关联对象
    project_id          INTEGER,                              -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 异常信息
    event_type          VARCHAR(30) NOT NULL,                 -- SCHEDULE/QUALITY/COST/RESOURCE/SAFETY/OTHER
    severity            VARCHAR(20) NOT NULL,                 -- MINOR/MAJOR/CRITICAL/BLOCKER
    event_title         VARCHAR(200) NOT NULL,                -- 异常标题
    event_description   TEXT NOT NULL,                        -- 异常描述

    -- 发现信息
    discovered_at       DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 发现时间
    discovered_by       INTEGER,                              -- 发现人
    discovery_location  VARCHAR(200),                         -- 发现地点

    -- 影响评估
    impact_scope        VARCHAR(20),                          -- LOCAL/MODULE/PROJECT/MULTI_PROJECT
    impact_description  TEXT,                                 -- 影响描述
    schedule_impact     INTEGER DEFAULT 0,                    -- 工期影响(天)
    cost_impact         DECIMAL(14,2) DEFAULT 0,              -- 成本影响

    -- 状态
    status              VARCHAR(20) DEFAULT 'OPEN',           -- OPEN/ANALYZING/RESOLVING/RESOLVED/CLOSED/DEFERRED

    -- 责任人
    responsible_dept    VARCHAR(50),                          -- 责任部门
    responsible_user_id INTEGER,                              -- 责任人

    -- 处理期限
    due_date            DATE,                                 -- 要求完成日期
    is_overdue          BOOLEAN DEFAULT 0,                    -- 是否超期

    -- 根本原因
    root_cause          TEXT,                                 -- 根本原因分析
    cause_category      VARCHAR(50),                          -- 原因分类

    -- 解决方案
    solution            TEXT,                                 -- 解决方案
    preventive_measures TEXT,                                 -- 预防措施

    -- 处理结果
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人
    resolution_note     TEXT,                                 -- 解决说明

    -- 验证
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人
    verification_result VARCHAR(20),                          -- VERIFIED/REJECTED

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (alert_id) REFERENCES alert_records(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (discovered_by) REFERENCES users(id),
    FOREIGN KEY (responsible_user_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE exception_actions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL,                     -- 异常事件ID

    -- 操作信息
    action_type         VARCHAR(30) NOT NULL,                 -- COMMENT/STATUS_CHANGE/ASSIGN/ANALYZE/RESOLVE/VERIFY/ESCALATE
    action_content      TEXT NOT NULL,                        -- 操作内容

    -- 状态变更
    old_status          VARCHAR(20),                          -- 原状态
    new_status          VARCHAR(20),                          -- 新状态

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id) REFERENCES exception_events(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE exception_escalations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            INTEGER NOT NULL,                     -- 异常事件ID
    escalation_level    INTEGER NOT NULL,                     -- 升级层级

    -- 升级信息
    escalated_from      INTEGER,                              -- 升级发起人
    escalated_to        INTEGER NOT NULL,                     -- 升级接收人
    escalated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 升级时间
    escalation_reason   TEXT,                                 -- 升级原因

    -- 响应
    response_status     VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/ACCEPTED/DELEGATED
    responded_at        DATETIME,                             -- 响应时间
    response_note       TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                                 -- 响应说明

    FOREIGN KEY (event_id) REFERENCES exception_events(id),
    FOREIGN KEY (escalated_from) REFERENCES users(id),
    FOREIGN KEY (escalated_to) REFERENCES users(id)
);
CREATE TABLE alert_statistics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date           DATE NOT NULL,                        -- 统计日期
    stat_type           VARCHAR(20) NOT NULL,                 -- DAILY/WEEKLY/MONTHLY

    -- 预警统计
    total_alerts        INTEGER DEFAULT 0,                    -- 预警总数
    info_alerts         INTEGER DEFAULT 0,                    -- 提示级别
    warning_alerts      INTEGER DEFAULT 0,                    -- 警告级别
    critical_alerts     INTEGER DEFAULT 0,                    -- 严重级别
    urgent_alerts       INTEGER DEFAULT 0,                    -- 紧急级别

    -- 处理统计
    pending_alerts      INTEGER DEFAULT 0,                    -- 待处理
    processing_alerts   INTEGER DEFAULT 0,                    -- 处理中
    resolved_alerts     INTEGER DEFAULT 0,                    -- 已解决
    ignored_alerts      INTEGER DEFAULT 0,                    -- 已忽略

    -- 异常统计
    total_exceptions    INTEGER DEFAULT 0,                    -- 异常总数
    open_exceptions     INTEGER DEFAULT 0,                    -- 未关闭异常
    overdue_exceptions  INTEGER DEFAULT 0,                    -- 超期异常

    -- 响应时间(小时)
    avg_response_time   DECIMAL(10,2) DEFAULT 0,              -- 平均响应时间
    avg_resolve_time    DECIMAL(10,2) DEFAULT 0,              -- 平均解决时间

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stat_date, stat_type)
);
CREATE TABLE project_health_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    snapshot_date       DATE NOT NULL,                        -- 快照日期

    -- 健康指标
    overall_health      VARCHAR(10) NOT NULL,                 -- H1/H2/H3/H4
    schedule_health     VARCHAR(10),                          -- 进度健康度
    cost_health         VARCHAR(10),                          -- 成本健康度
    quality_health      VARCHAR(10),                          -- 质量健康度
    resource_health     VARCHAR(10),                          -- 资源健康度

    -- 健康评分(0-100)
    health_score        INTEGER DEFAULT 0,                    -- 综合评分

    -- 风险指标
    open_alerts         INTEGER DEFAULT 0,                    -- 未处理预警数
    open_exceptions     INTEGER DEFAULT 0,                    -- 未关闭异常数
    blocking_issues     INTEGER DEFAULT 0,                    -- 阻塞问题数

    -- 进度指标
    schedule_variance   DECIMAL(5,2) DEFAULT 0,               -- 进度偏差(%)
    milestone_on_track  INTEGER DEFAULT 0,                    -- 按期里程碑数
    milestone_delayed   INTEGER DEFAULT 0,                    -- 延期里程碑数

    -- 成本指标
    cost_variance       DECIMAL(5,2) DEFAULT 0,               -- 成本偏差(%)
    budget_used_pct     DECIMAL(5,2) DEFAULT 0,               -- 预算使用率(%)

    -- 主要风险
    top_risks           TEXT,                                 -- 主要风险JSON

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    UNIQUE(project_id, snapshot_date)
);
INSERT INTO project_health_snapshots VALUES(1,1,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.494996','2026-01-30 15:49:04.494996');
INSERT INTO project_health_snapshots VALUES(2,2,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.501619','2026-01-30 15:49:04.501620');
INSERT INTO project_health_snapshots VALUES(3,3,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.503673','2026-01-30 15:49:04.503674');
INSERT INTO project_health_snapshots VALUES(4,4,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.505622','2026-01-30 15:49:04.505622');
INSERT INTO project_health_snapshots VALUES(5,5,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.507565','2026-01-30 15:49:04.507566');
INSERT INTO project_health_snapshots VALUES(6,6,'2026-01-30','H2','H2','H2','H2','H2',70,0,0,0,0,0,0,0,0,NULL,'2026-01-30 15:49:04.508321','2026-01-30 15:49:04.508321');
CREATE TABLE alert_rule_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,          -- 模板编码
    template_name       VARCHAR(200) NOT NULL,                -- 模板名称
    template_category   VARCHAR(30) NOT NULL,                 -- 模板分类

    -- 规则配置
    rule_config         TEXT NOT NULL,                        -- 规则配置JSON

    -- 说明
    description         TEXT,                                 -- 模板说明
    usage_guide         TEXT,                                 -- 使用指南

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE ecn (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_no              VARCHAR(50) NOT NULL UNIQUE,          -- ECN编号
    ecn_title           VARCHAR(200) NOT NULL,                -- ECN标题
    ecn_type            VARCHAR(20) NOT NULL,                 -- 变更类型

    -- 来源
    source_type         VARCHAR(20) NOT NULL,                 -- 来源类型
    source_no           VARCHAR(100),                         -- 来源单号
    source_id           INTEGER,                              -- 来源ID

    -- 关联
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 变更内容
    change_reason       TEXT NOT NULL,                        -- 变更原因
    change_description  TEXT NOT NULL,                        -- 变更内容描述
    change_scope        VARCHAR(20) DEFAULT 'PARTIAL',        -- 变更范围

    -- 优先级
    priority            VARCHAR(20) DEFAULT 'NORMAL',         -- 优先级
    urgency             VARCHAR(20) DEFAULT 'NORMAL',         -- 紧急程度

    -- 影响评估
    cost_impact         DECIMAL(14,2) DEFAULT 0,              -- 成本影响
    schedule_impact_days INTEGER DEFAULT 0,                   -- 工期影响(天)
    quality_impact      VARCHAR(20),                          -- 质量影响

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 状态
    current_step        VARCHAR(50),                          -- 当前步骤

    -- 申请人
    applicant_id        INTEGER,                              -- 申请人
    applicant_dept      VARCHAR(100),                         -- 申请部门
    applied_at          DATETIME,                             -- 申请时间

    -- 审批结果
    approval_result     VARCHAR(20),                          -- 审批结果
    approval_note       TEXT,                                 -- 审批意见
    approved_at         DATETIME,                             -- 审批时间

    -- 执行
    execution_start     DATETIME,                             -- 执行开始
    execution_end       DATETIME,                             -- 执行结束
    execution_note      TEXT,                                 -- 执行说明

    -- 关闭
    closed_at           DATETIME,                             -- 关闭时间
    closed_by           INTEGER,                              -- 关闭人

    -- 附件
    attachments         TEXT,                                 -- 附件JSON

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, root_cause VARCHAR(20), root_cause_analysis TEXT, root_cause_category VARCHAR(50), solution TEXT, solution_template_id INTEGER, similar_ecn_ids TEXT, solution_source VARCHAR(20),

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (applicant_id) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE ecn_evaluations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    eval_dept           VARCHAR(50) NOT NULL,                 -- 评估部门

    -- 评估人
    evaluator_id        INTEGER,                              -- 评估人
    evaluator_name      VARCHAR(50),                          -- 评估人姓名

    -- 评估内容
    impact_analysis     TEXT,                                 -- 影响分析
    cost_estimate       DECIMAL(14,2) DEFAULT 0,              -- 成本估算
    schedule_estimate   INTEGER DEFAULT 0,                    -- 工期估算(天)
    resource_requirement TEXT,                                -- 资源需求
    risk_assessment     TEXT,                                 -- 风险评估

    -- 评估结论
    eval_result         VARCHAR(20),                          -- APPROVE/REJECT/CONDITIONAL
    eval_opinion        TEXT,                                 -- 评估意见
    conditions          TEXT,                                 -- 附加条件

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/COMPLETED/SKIPPED
    evaluated_at        DATETIME,                             -- 评估时间

    -- 附件
    attachments         TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE ecn_approvals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    approval_level      INTEGER NOT NULL,                     -- 审批层级
    approval_role       VARCHAR(50) NOT NULL,                 -- 审批角色

    -- 审批人
    approver_id         INTEGER,                              -- 审批人ID
    approver_name       VARCHAR(50),                          -- 审批人姓名

    -- 审批结果
    approval_result     VARCHAR(20),                          -- APPROVED/REJECTED/RETURNED
    approval_opinion    TEXT,                                 -- 审批意见

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/COMPLETED
    approved_at         DATETIME,                             -- 审批时间

    -- 超时
    due_date            DATETIME,                             -- 审批期限
    is_overdue          BOOLEAN DEFAULT 0,                    -- 是否超期

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE ecn_tasks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    task_no             INTEGER NOT NULL,                     -- 任务序号
    task_name           VARCHAR(200) NOT NULL,                -- 任务名称
    task_type           VARCHAR(50),                          -- 任务类型
    task_dept           VARCHAR(50),                          -- 责任部门

    -- 任务内容
    task_description    TEXT,                                 -- 任务描述
    deliverables        TEXT,                                 -- 交付物要求

    -- 负责人
    assignee_id         INTEGER,                              -- 负责人
    assignee_name       VARCHAR(50),                          -- 负责人姓名

    -- 时间
    planned_start       DATE,                                 -- 计划开始
    planned_end         DATE,                                 -- 计划结束
    actual_start        DATE,                                 -- 实际开始
    actual_end          DATE,                                 -- 实际结束

    -- 进度
    progress_pct        INTEGER DEFAULT 0,                    -- 进度百分比

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/IN_PROGRESS/COMPLETED/CANCELLED

    -- 完成信息
    completion_note     TEXT,                                 -- 完成说明
    attachments         TEXT,                                 -- 附件

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);
CREATE TABLE ecn_affected_materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    material_id         INTEGER,                              -- 物料ID
    bom_item_id         INTEGER,                              -- BOM行ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,
    specification       VARCHAR(500),

    -- 变更类型
    change_type         VARCHAR(20) NOT NULL,                 -- ADD/DELETE/MODIFY/REPLACE

    -- 变更前
    old_quantity        DECIMAL(10,4),
    old_specification   VARCHAR(500),
    old_supplier_id     INTEGER,

    -- 变更后
    new_quantity        DECIMAL(10,4),
    new_specification   VARCHAR(500),
    new_supplier_id     INTEGER,

    -- 影响
    cost_impact         DECIMAL(12,2) DEFAULT 0,              -- 成本影响

    -- 处理状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PROCESSED
    processed_at        DATETIME,

    remark              TEXT, bom_impact_scope TEXT, is_obsolete_risk BOOLEAN DEFAULT 0, obsolete_risk_level VARCHAR(20), obsolete_quantity NUMERIC(10, 4), obsolete_cost NUMERIC(14, 2), obsolete_analysis TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id)
);
CREATE TABLE ecn_affected_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    order_type          VARCHAR(20) NOT NULL,                 -- PURCHASE/OUTSOURCE
    order_id            INTEGER NOT NULL,                     -- 订单ID
    order_no            VARCHAR(50) NOT NULL,                 -- 订单号

    -- 影响描述
    impact_description  TEXT,                                 -- 影响描述

    -- 处理方式
    action_type         VARCHAR(20),                          -- CANCEL/MODIFY/KEEP
    action_description  TEXT,                                 -- 处理说明

    -- 处理状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PROCESSED
    processed_by        INTEGER,
    processed_at        DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (processed_by) REFERENCES users(id)
);
CREATE TABLE ecn_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id              INTEGER NOT NULL,                     -- ECN ID
    log_type            VARCHAR(20) NOT NULL,                 -- 日志类型
    log_action          VARCHAR(50) NOT NULL,                 -- 操作动作

    -- 状态变更
    old_status          VARCHAR(20),
    new_status          VARCHAR(20),

    -- 内容
    log_content         TEXT,                                 -- 日志内容
    attachments         TEXT,                                 -- 附件

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE ecn_types (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code           VARCHAR(20) NOT NULL UNIQUE,          -- 类型编码
    type_name           VARCHAR(50) NOT NULL,                 -- 类型名称
    description         TEXT,                                 -- 描述

    -- 评估配置
    required_depts      TEXT,                                 -- 必需评估部门JSON
    optional_depts      TEXT,                                 -- 可选评估部门JSON

    -- 审批配置
    approval_matrix     TEXT,                                 -- 审批矩阵JSON

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE ecn_approval_matrix (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_type            VARCHAR(20),                          -- ECN类型
    condition_type      VARCHAR(20) NOT NULL,                 -- 条件类型：COST/SCHEDULE
    condition_min       DECIMAL(14,2),                        -- 条件下限
    condition_max       DECIMAL(14,2),                        -- 条件上限

    approval_level      INTEGER NOT NULL,                     -- 审批层级
    approval_role       VARCHAR(50) NOT NULL,                 -- 审批角色

    is_active           BOOLEAN DEFAULT 1,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE outsourcing_vendors (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_code         VARCHAR(50) NOT NULL UNIQUE,          -- 外协商编码
    vendor_name         VARCHAR(200) NOT NULL,                -- 外协商名称
    vendor_short_name   VARCHAR(50),                          -- 简称
    vendor_type         VARCHAR(20) NOT NULL,                 -- MACHINING/ASSEMBLY/SURFACE/ELECTRICAL/OTHER

    -- 联系信息
    contact_person      VARCHAR(50),                          -- 联系人
    contact_phone       VARCHAR(30),                          -- 联系电话
    contact_email       VARCHAR(100),                         -- 邮箱
    address             VARCHAR(500),                         -- 地址

    -- 资质信息
    business_license    VARCHAR(100),                         -- 营业执照号
    qualification       TEXT,                                 -- 资质认证JSON
    capabilities        TEXT,                                 -- 加工能力JSON

    -- 评价
    quality_rating      DECIMAL(3,2) DEFAULT 0,               -- 质量评分(0-5)
    delivery_rating     DECIMAL(3,2) DEFAULT 0,               -- 交期评分(0-5)
    service_rating      DECIMAL(3,2) DEFAULT 0,               -- 服务评分(0-5)
    overall_rating      DECIMAL(3,2) DEFAULT 0,               -- 综合评分

    -- 状态
    status              VARCHAR(20) DEFAULT 'ACTIVE',         -- ACTIVE/INACTIVE/BLACKLIST
    cooperation_start   DATE,                                 -- 合作开始日期
    last_order_date     DATE,                                 -- 最后订单日期

    -- 银行信息
    bank_name           VARCHAR(100),                         -- 开户行
    bank_account        VARCHAR(50),                          -- 银行账号
    tax_number          VARCHAR(50),                          -- 税号

    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE outsourcing_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no            VARCHAR(50) NOT NULL UNIQUE,          -- 外协订单号
    vendor_id           INTEGER NOT NULL,                     -- 外协商ID
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 设备ID

    -- 订单信息
    order_type          VARCHAR(20) NOT NULL,                 -- MACHINING/ASSEMBLY/SURFACE/OTHER
    order_title         VARCHAR(200) NOT NULL,                -- 订单标题
    order_description   TEXT,                                 -- 订单说明

    -- 金额
    total_amount        DECIMAL(14,2) DEFAULT 0,              -- 总金额
    tax_rate            DECIMAL(5,2) DEFAULT 13,              -- 税率
    tax_amount          DECIMAL(14,2) DEFAULT 0,              -- 税额
    amount_with_tax     DECIMAL(14,2) DEFAULT 0,              -- 含税金额

    -- 时间要求
    required_date       DATE,                                 -- 要求交期
    estimated_date      DATE,                                 -- 预计交期
    actual_date         DATE,                                 -- 实际交期

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/CONFIRMED/IN_PROGRESS/DELIVERED/INSPECTED/COMPLETED/CANCELLED

    -- 付款状态
    payment_status      VARCHAR(20) DEFAULT 'UNPAID',         -- UNPAID/PARTIAL/PAID
    paid_amount         DECIMAL(14,2) DEFAULT 0,              -- 已付金额

    -- 签约
    contract_no         VARCHAR(100),                         -- 合同编号
    contract_file       VARCHAR(500),                         -- 合同文件路径

    -- 备注
    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE outsourcing_order_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 外协订单ID
    item_no             INTEGER NOT NULL,                     -- 行号

    -- 物料信息
    material_id         INTEGER,                              -- 物料ID
    material_code       VARCHAR(50) NOT NULL,                 -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500),                         -- 规格型号
    drawing_no          VARCHAR(100),                         -- 图号

    -- 加工信息
    process_type        VARCHAR(50),                          -- 加工类型
    process_content     TEXT,                                 -- 加工内容
    process_requirements TEXT,                                -- 工艺要求

    -- 数量与单价
    unit                VARCHAR(20) DEFAULT '件',             -- 单位
    quantity            DECIMAL(10,4) NOT NULL,               -- 数量
    unit_price          DECIMAL(12,4) DEFAULT 0,              -- 单价
    amount              DECIMAL(14,2) DEFAULT 0,              -- 金额

    -- 来料信息(若需要来料加工)
    material_provided   BOOLEAN DEFAULT 0,                    -- 是否来料加工
    provided_quantity   DECIMAL(10,4) DEFAULT 0,              -- 来料数量
    provided_date       DATE,                                 -- 来料日期

    -- 交付信息
    delivered_quantity  DECIMAL(10,4) DEFAULT 0,              -- 已交付数量
    qualified_quantity  DECIMAL(10,4) DEFAULT 0,              -- 合格数量
    rejected_quantity   DECIMAL(10,4) DEFAULT 0,              -- 不合格数量

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/PROCESSING/DELIVERED/INSPECTED/COMPLETED

    remark              TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE outsourcing_deliveries (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_no         VARCHAR(50) NOT NULL UNIQUE,          -- 交付单号
    order_id            INTEGER NOT NULL,                     -- 外协订单ID
    vendor_id           INTEGER NOT NULL,                     -- 外协商ID

    -- 交付信息
    delivery_date       DATE NOT NULL,                        -- 交付日期
    delivery_type       VARCHAR(20) DEFAULT 'NORMAL',         -- NORMAL/PARTIAL/FINAL
    delivery_person     VARCHAR(50),                          -- 送货人
    receiver            VARCHAR(50),                          -- 收货人

    -- 物流信息
    logistics_company   VARCHAR(100),                         -- 物流公司
    tracking_no         VARCHAR(100),                         -- 运单号

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/RECEIVED/INSPECTING/COMPLETED
    received_at         DATETIME,                             -- 收货时间
    received_by         INTEGER,                              -- 收货人ID

    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (received_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE outsourcing_delivery_items (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id         INTEGER NOT NULL,                     -- 交付单ID
    order_item_id       INTEGER NOT NULL,                     -- 订单明细ID

    -- 物料信息
    material_code       VARCHAR(50) NOT NULL,
    material_name       VARCHAR(200) NOT NULL,

    -- 数量
    delivery_quantity   DECIMAL(10,4) NOT NULL,               -- 交付数量
    received_quantity   DECIMAL(10,4) DEFAULT 0,              -- 实收数量

    -- 质检结果
    inspect_status      VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/INSPECTING/PASSED/REJECTED/PARTIAL
    qualified_quantity  DECIMAL(10,4) DEFAULT 0,              -- 合格数量
    rejected_quantity   DECIMAL(10,4) DEFAULT 0,              -- 不合格数量

    remark              TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (delivery_id) REFERENCES outsourcing_deliveries(id),
    FOREIGN KEY (order_item_id) REFERENCES outsourcing_order_items(id)
);
CREATE TABLE outsourcing_inspections (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_no       VARCHAR(50) NOT NULL UNIQUE,          -- 质检单号
    delivery_id         INTEGER NOT NULL,                     -- 交付单ID
    delivery_item_id    INTEGER NOT NULL,                     -- 交付明细ID

    -- 质检信息
    inspect_type        VARCHAR(20) DEFAULT 'INCOMING',       -- INCOMING/PROCESS/FINAL
    inspect_date        DATE NOT NULL,                        -- 质检日期
    inspector_id        INTEGER,                              -- 质检员
    inspector_name      VARCHAR(50),                          -- 质检员姓名

    -- 检验数量
    inspect_quantity    DECIMAL(10,4) NOT NULL,               -- 送检数量
    sample_quantity     DECIMAL(10,4) DEFAULT 0,              -- 抽检数量
    qualified_quantity  DECIMAL(10,4) DEFAULT 0,              -- 合格数量
    rejected_quantity   DECIMAL(10,4) DEFAULT 0,              -- 不合格数量

    -- 结果
    inspect_result      VARCHAR(20),                          -- PASSED/REJECTED/CONDITIONAL
    pass_rate           DECIMAL(5,2) DEFAULT 0,               -- 合格率

    -- 不良信息
    defect_description  TEXT,                                 -- 不良描述
    defect_type         VARCHAR(50),                          -- 不良类型
    defect_images       TEXT,                                 -- 不良图片JSON

    -- 处理
    disposition         VARCHAR(20),                          -- ACCEPT/REWORK/RETURN/SCRAP
    disposition_note    TEXT,                                 -- 处理说明

    remark              TEXT,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (delivery_id) REFERENCES outsourcing_deliveries(id),
    FOREIGN KEY (delivery_item_id) REFERENCES outsourcing_delivery_items(id),
    FOREIGN KEY (inspector_id) REFERENCES users(id)
);
CREATE TABLE outsourcing_payments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no          VARCHAR(50) NOT NULL UNIQUE,          -- 付款单号
    vendor_id           INTEGER NOT NULL,                     -- 外协商ID
    order_id            INTEGER,                              -- 外协订单ID(可为空,对账付款)

    -- 付款信息
    payment_type        VARCHAR(20) NOT NULL,                 -- ADVANCE/PROGRESS/FINAL/SETTLEMENT
    payment_amount      DECIMAL(14,2) NOT NULL,               -- 付款金额
    payment_date        DATE,                                 -- 付款日期
    payment_method      VARCHAR(20),                          -- BANK/CASH/CHECK

    -- 发票信息
    invoice_no          VARCHAR(100),                         -- 发票号
    invoice_amount      DECIMAL(14,2),                        -- 发票金额
    invoice_date        DATE,                                 -- 发票日期

    -- 审批
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- DRAFT/PENDING/APPROVED/PAID/REJECTED
    approved_by         INTEGER,                              -- 审批人
    approved_at         DATETIME,                             -- 审批时间

    remark              TEXT,

    created_by          INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE outsourcing_evaluations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id           INTEGER NOT NULL,                     -- 外协商ID
    order_id            INTEGER,                              -- 关联订单(可选)
    eval_period         VARCHAR(20),                          -- 评价周期(如: 2026-Q1)

    -- 评分(1-5分)
    quality_score       DECIMAL(3,2) DEFAULT 0,               -- 质量评分
    delivery_score      DECIMAL(3,2) DEFAULT 0,               -- 交期评分
    price_score         DECIMAL(3,2) DEFAULT 0,               -- 价格评分
    service_score       DECIMAL(3,2) DEFAULT 0,               -- 服务评分
    overall_score       DECIMAL(3,2) DEFAULT 0,               -- 综合评分

    -- 评价内容
    advantages          TEXT,                                 -- 优点
    disadvantages       TEXT,                                 -- 不足
    improvement         TEXT,                                 -- 改进建议

    -- 评价人
    evaluator_id        INTEGER,
    evaluated_at        DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE outsourcing_progress (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,                     -- 外协订单ID
    order_item_id       INTEGER,                              -- 订单明细ID(可选)

    -- 进度信息
    report_date         DATE NOT NULL,                        -- 报告日期
    progress_pct        INTEGER DEFAULT 0,                    -- 进度百分比
    completed_quantity  DECIMAL(10,4) DEFAULT 0,              -- 完成数量

    -- 状态
    current_process     VARCHAR(100),                         -- 当前工序
    next_process        VARCHAR(100),                         -- 下一工序
    estimated_complete  DATE,                                 -- 预计完成日期

    -- 问题
    issues              TEXT,                                 -- 问题说明
    risk_level          VARCHAR(20),                          -- LOW/MEDIUM/HIGH

    -- 图片/附件
    attachments         TEXT,                                 -- 附件JSON

    reported_by         INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (order_item_id) REFERENCES outsourcing_order_items(id),
    FOREIGN KEY (reported_by) REFERENCES users(id)
);
CREATE TABLE performance_period (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_code VARCHAR(20) NOT NULL UNIQUE,                 -- 周期编码
    period_name VARCHAR(100) NOT NULL,                       -- 周期名称
    period_type VARCHAR(20) NOT NULL,                        -- 周期类型
    start_date DATE NOT NULL,                                -- 开始日期
    end_date DATE NOT NULL,                                  -- 结束日期
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    is_active INTEGER DEFAULT 1,                             -- 是否当前周期
    calculate_date DATE,                                     -- 计算日期
    review_deadline DATE,                                    -- 评审截止日期
    finalize_date DATE,                                      -- 定稿日期
    remarks TEXT,                                            -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE performance_indicator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code VARCHAR(50) NOT NULL UNIQUE,              -- 指标编码
    indicator_name VARCHAR(100) NOT NULL,                    -- 指标名称
    indicator_type VARCHAR(20) NOT NULL,                     -- 指标类型
    calculation_formula TEXT,                                -- 计算公式说明
    data_source VARCHAR(100),                                -- 数据来源
    weight DECIMAL(5,2) DEFAULT 0,                          -- 权重(%)
    scoring_rules TEXT,                                      -- 评分规则(JSON)
    max_score INTEGER DEFAULT 100,                           -- 最高分
    min_score INTEGER DEFAULT 0,                             -- 最低分
    apply_to_roles TEXT,                                     -- 适用角色列表(JSON)
    apply_to_depts TEXT,                                     -- 适用部门列表(JSON)
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    sort_order INTEGER DEFAULT 0,                            -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO performance_indicator VALUES(1,'WORKLOAD_HOURS','工时饱和度','WORKLOAD',NULL,NULL,20,NULL,100,0,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(2,'WORKLOAD_OVERTIME','加班贡献','WORKLOAD',NULL,NULL,5,NULL,100,0,NULL,NULL,1,2,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(3,'TASK_COMPLETION','任务完成率','TASK',NULL,NULL,25,NULL,100,0,NULL,NULL,1,3,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(4,'TASK_ONTIME','按时完成率','TASK',NULL,NULL,15,NULL,100,0,NULL,NULL,1,4,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(5,'QUALITY_DEFECT','缺陷率','QUALITY',NULL,NULL,15,NULL,100,0,NULL,NULL,1,5,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(6,'QUALITY_REWORK','返工率','QUALITY',NULL,NULL,10,NULL,100,0,NULL,NULL,1,6,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(7,'COLLAB_ASSIST','协作支持','COLLABORATION',NULL,NULL,5,NULL,100,0,NULL,NULL,1,7,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO performance_indicator VALUES(8,'COLLAB_RESPONSE','响应及时性','COLLABORATION',NULL,NULL,5,NULL,100,0,NULL,NULL,1,8,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE performance_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    department_name VARCHAR(100),                            -- 部门名称
    total_score DECIMAL(5,2),                               -- 综合得分
    level VARCHAR(20),                                       -- 绩效等级
    workload_score DECIMAL(5,2),                            -- 工作量得分
    task_score DECIMAL(5,2),                                -- 任务得分
    quality_score DECIMAL(5,2),                             -- 质量得分
    collaboration_score DECIMAL(5,2),                       -- 协作得分
    growth_score DECIMAL(5,2),                              -- 成长得分
    indicator_scores TEXT,                                   -- 各指标详细得分(JSON)
    dept_rank INTEGER,                                       -- 部门排名
    company_rank INTEGER,                                    -- 公司排名
    score_change DECIMAL(5,2),                              -- 得分变化
    rank_change INTEGER,                                     -- 排名变化
    highlights TEXT,                                         -- 亮点(JSON)
    improvements TEXT,                                       -- 待改进(JSON)
    status VARCHAR(20) DEFAULT 'CALCULATED',                 -- 状态
    calculated_at DATETIME,                                  -- 计算时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, job_type VARCHAR(20), job_level VARCHAR(20), dimension_details TEXT, original_total_score DECIMAL(5,2), adjusted_total_score DECIMAL(5,2), original_dept_rank INTEGER, adjusted_dept_rank INTEGER, original_company_rank INTEGER, adjusted_company_rank INTEGER, adjustment_reason TEXT, adjusted_by INTEGER, adjusted_at DATETIME, is_adjusted BOOLEAN DEFAULT 0,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);
CREATE TABLE performance_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,                              -- 绩效结果ID
    evaluator_id INTEGER NOT NULL,                           -- 评价人ID
    evaluator_name VARCHAR(50),                              -- 评价人姓名
    evaluator_role VARCHAR(50),                              -- 评价人角色
    overall_comment TEXT,                                    -- 总体评价
    strength_comment TEXT,                                   -- 优点评价
    improvement_comment TEXT,                                -- 改进建议
    adjusted_level VARCHAR(20),                              -- 调整后等级
    adjustment_reason TEXT,                                  -- 调整原因
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 评价时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id)
);
CREATE TABLE performance_appeal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,                              -- 绩效结果ID
    appellant_id INTEGER NOT NULL,                           -- 申诉人ID
    appellant_name VARCHAR(50),                              -- 申诉人姓名
    appeal_reason TEXT NOT NULL,                             -- 申诉理由
    expected_score DECIMAL(5,2),                            -- 期望得分
    supporting_evidence TEXT,                                -- 支撑证据
    attachments TEXT,                                        -- 附件(JSON)
    appeal_time DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 申诉时间
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    handler_id INTEGER,                                      -- 处理人ID
    handler_name VARCHAR(50),                                -- 处理人
    handle_time DATETIME,                                    -- 处理时间
    handle_result TEXT,                                      -- 处理结果
    new_score DECIMAL(5,2),                                 -- 调整后得分
    new_level VARCHAR(20),                                   -- 调整后等级
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id)
);
CREATE TABLE project_contribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    project_id INTEGER NOT NULL,                             -- 项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    task_count INTEGER DEFAULT 0,                            -- 任务数
    completed_tasks INTEGER DEFAULT 0,                       -- 完成任务数
    on_time_tasks INTEGER DEFAULT 0,                         -- 按时完成数
    hours_spent DECIMAL(10,2) DEFAULT 0,                    -- 投入工时
    hours_percentage DECIMAL(5,2),                          -- 工时占比(%)
    contribution_level VARCHAR(20),                          -- 贡献等级
    role_in_project VARCHAR(50),                             -- 项目中角色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);
CREATE TABLE performance_ranking_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,                              -- 考核周期ID
    scope_type VARCHAR(20) NOT NULL,                         -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    scope_name VARCHAR(100),                                 -- 范围名称
    total_members INTEGER,                                   -- 总人数
    avg_score DECIMAL(5,2),                                 -- 平均分
    max_score DECIMAL(5,2),                                 -- 最高分
    min_score DECIMAL(5,2),                                 -- 最低分
    median_score DECIMAL(5,2),                              -- 中位数
    level_distribution TEXT,                                 -- 等级分布(JSON)
    ranking_data TEXT,                                       -- 排名数据(JSON)
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,        -- 快照时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (period_id) REFERENCES performance_period(id)
);
CREATE TABLE timesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_no VARCHAR(50),                                -- 工时单号
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    department_name VARCHAR(100),                            -- 部门名称
    project_id INTEGER NOT NULL,                             -- 项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    task_id INTEGER,                                         -- 任务ID
    task_name VARCHAR(200),                                  -- 任务名称
    assign_id INTEGER,                                       -- 任务分配ID
    work_date DATE NOT NULL,                                 -- 工作日期
    hours DECIMAL(5,2) NOT NULL,                            -- 工时(小时)
    overtime_type VARCHAR(20) DEFAULT 'NORMAL',              -- 加班类型
    work_content TEXT,                                       -- 工作内容
    work_result TEXT,                                        -- 工作成果
    progress_before INTEGER,                                 -- 更新前进度(%)
    progress_after INTEGER,                                  -- 更新后进度(%)
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    submit_time DATETIME,                                    -- 提交时间
    approver_id INTEGER,                                     -- 审核人ID
    approver_name VARCHAR(50),                               -- 审核人
    approve_time DATETIME,                                   -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, rd_project_id INTEGER);
CREATE TABLE timesheet_batch (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_no VARCHAR(50) NOT NULL UNIQUE,                    -- 批次编号
    user_id INTEGER NOT NULL,                                -- 用户ID
    user_name VARCHAR(50),                                   -- 用户姓名
    department_id INTEGER,                                   -- 部门ID
    week_start DATE NOT NULL,                                -- 周开始日期
    week_end DATE NOT NULL,                                  -- 周结束日期
    year INTEGER,                                            -- 年份
    week_number INTEGER,                                     -- 周数
    total_hours DECIMAL(6,2) DEFAULT 0,                     -- 总工时
    normal_hours DECIMAL(6,2) DEFAULT 0,                    -- 正常工时
    overtime_hours DECIMAL(6,2) DEFAULT 0,                  -- 加班工时
    entries_count INTEGER DEFAULT 0,                         -- 记录条数
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    submit_time DATETIME,                                    -- 提交时间
    approver_id INTEGER,                                     -- 审核人ID
    approver_name VARCHAR(50),                               -- 审核人
    approve_time DATETIME,                                   -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE timesheet_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_type VARCHAR(20) NOT NULL,                       -- 汇总类型
    user_id INTEGER,                                         -- 用户ID
    project_id INTEGER,                                      -- 项目ID
    department_id INTEGER,                                   -- 部门ID
    year INTEGER NOT NULL,                                   -- 年份
    month INTEGER NOT NULL,                                  -- 月份
    total_hours DECIMAL(8,2) DEFAULT 0,                     -- 总工时
    normal_hours DECIMAL(8,2) DEFAULT 0,                    -- 正常工时
    overtime_hours DECIMAL(8,2) DEFAULT 0,                  -- 加班工时
    weekend_hours DECIMAL(8,2) DEFAULT 0,                   -- 周末工时
    holiday_hours DECIMAL(8,2) DEFAULT 0,                   -- 节假日工时
    standard_hours DECIMAL(8,2),                            -- 标准工时
    work_days INTEGER,                                       -- 工作日数
    entries_count INTEGER DEFAULT 0,                         -- 记录条数
    projects_count INTEGER DEFAULT 0,                        -- 参与项目数
    project_breakdown TEXT,                                  -- 项目分布(JSON)
    daily_breakdown TEXT,                                    -- 每日分布(JSON)
    task_breakdown TEXT,                                     -- 任务分布(JSON)
    status_breakdown TEXT,                                   -- 状态分布(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO timesheet_summary VALUES(1,'GLOBAL_MONTH',NULL,NULL,NULL,2026,1,0,0,0,0,0,NULL,NULL,0,0,'{}','{}','{}',NULL,'2026-01-29 01:00:00.248835','2026-01-29 01:00:00.248844');
INSERT INTO timesheet_summary VALUES(2,'GLOBAL_MONTH',NULL,NULL,NULL,2025,12,0,0,0,0,0,NULL,NULL,0,0,'{}','{}','{}',NULL,'2026-01-30 15:37:59.916164','2026-01-30 15:37:59.916164');
CREATE TABLE overtime_application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no VARCHAR(50) NOT NULL UNIQUE,              -- 申请编号
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    department_id INTEGER,                                   -- 部门ID
    overtime_type VARCHAR(20) NOT NULL,                      -- 加班类型
    overtime_date DATE NOT NULL,                             -- 加班日期
    start_time DATETIME,                                     -- 开始时间
    end_time DATETIME,                                       -- 结束时间
    planned_hours DECIMAL(5,2) NOT NULL,                    -- 计划加班时长
    project_id INTEGER,                                      -- 项目ID
    project_name VARCHAR(200),                               -- 项目名称
    reason TEXT NOT NULL,                                    -- 加班原因
    work_content TEXT,                                       -- 加班内容
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    approver_id INTEGER,                                     -- 审批人ID
    approver_name VARCHAR(50),                               -- 审批人
    approve_time DATETIME,                                   -- 审批时间
    approve_comment TEXT,                                    -- 审批意见
    actual_hours DECIMAL(5,2),                              -- 实际加班时长
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE timesheet_approval_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timesheet_id INTEGER,                                    -- 工时记录ID
    batch_id INTEGER,                                        -- 工时批次ID
    approver_id INTEGER NOT NULL,                            -- 审批人ID
    approver_name VARCHAR(50),                               -- 审批人
    action VARCHAR(20) NOT NULL,                             -- 审批动作
    comment TEXT,                                            -- 审批意见
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 审批时间
    FOREIGN KEY (timesheet_id) REFERENCES timesheet(id),
    FOREIGN KEY (batch_id) REFERENCES timesheet_batch(id)
);
CREATE TABLE timesheet_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) NOT NULL UNIQUE,                   -- 规则编码
    rule_name VARCHAR(100) NOT NULL,                         -- 规则名称
    apply_to_depts TEXT,                                     -- 适用部门(JSON)
    apply_to_roles TEXT,                                     -- 适用角色(JSON)
    standard_daily_hours DECIMAL(4,2) DEFAULT 8,            -- 标准日工时
    max_daily_hours DECIMAL(4,2) DEFAULT 12,                -- 每日最大工时
    min_entry_hours DECIMAL(4,2) DEFAULT 0.5,               -- 最小记录单位
    submit_deadline_day INTEGER DEFAULT 1,                   -- 提交截止日
    allow_backfill_days INTEGER DEFAULT 7,                   -- 允许补录天数
    require_approval INTEGER DEFAULT 1,                      -- 是否需要审批
    remind_unfilled INTEGER DEFAULT 1,                       -- 未填报提醒
    remind_time VARCHAR(10) DEFAULT '09:00',                 -- 提醒时间
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO timesheet_rule VALUES(1,'DEFAULT_RULE','默认填报规则',NULL,NULL,8,12,0.5,1,7,1,1,'09:00',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE report_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,               -- 模板编码
    template_name VARCHAR(100) NOT NULL,                     -- 模板名称
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    description TEXT,                                        -- 模板描述
    sections TEXT,                                           -- 模块配置(JSON)
    metrics_config TEXT,                                     -- 指标配置(JSON)
    charts_config TEXT,                                      -- 图表配置(JSON)
    filters_config TEXT,                                     -- 筛选器配置(JSON)
    style_config TEXT,                                       -- 样式配置(JSON)
    default_for_roles TEXT,                                  -- 默认适用角色(JSON)
    use_count INTEGER DEFAULT 0,                             -- 使用次数
    is_system INTEGER DEFAULT 0,                             -- 是否系统内置
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO report_template VALUES(1,'TPL_PROJECT_WEEKLY_STD','标准项目周报','PROJECT_WEEKLY','包含进度、任务、风险、下周计划',NULL,NULL,NULL,NULL,NULL,NULL,0,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO report_template VALUES(2,'TPL_PROJECT_WEEKLY_EXEC','项目周报-管理层版','PROJECT_WEEKLY','精简版，聚焦关键指标和风险',NULL,NULL,NULL,NULL,NULL,NULL,0,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO report_template VALUES(3,'TPL_DEPT_MONTHLY','部门月报','DEPT_MONTHLY','部门月度工作汇总',NULL,NULL,NULL,NULL,NULL,NULL,0,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO report_template VALUES(4,'TPL_COST_ANALYSIS','成本分析报表','COST_ANALYSIS','项目成本明细分析',NULL,NULL,NULL,NULL,NULL,NULL,0,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO report_template VALUES(5,'TPL_WORKLOAD','负荷分析报表','WORKLOAD_ANALYSIS','人员工作负荷分析',NULL,NULL,NULL,NULL,NULL,NULL,0,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE report_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code VARCHAR(50) NOT NULL UNIQUE,                 -- 报表编码
    report_name VARCHAR(100) NOT NULL,                       -- 报表名称
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    period_type VARCHAR(20) DEFAULT 'MONTHLY',               -- 周期类型
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_ids TEXT,                                          -- 范围ID列表(JSON)
    filters TEXT,                                            -- 过滤条件(JSON)
    sections TEXT,                                           -- 模块配置(JSON)
    metrics TEXT,                                            -- 指标配置(JSON)
    owner_id INTEGER NOT NULL,                               -- 所有者ID
    owner_name VARCHAR(50),                                  -- 所有者
    is_shared INTEGER DEFAULT 0,                             -- 是否共享
    shared_to TEXT,                                          -- 共享给(JSON)
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);
CREATE TABLE report_generation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_definition_id INTEGER,                            -- 报表定义ID
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    report_title VARCHAR(200),                               -- 报表标题
    period_type VARCHAR(20),                                 -- 周期类型
    period_start DATE,                                       -- 周期开始
    period_end DATE,                                         -- 周期结束
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    viewer_role VARCHAR(50),                                 -- 查看角色
    report_data TEXT,                                        -- 报表数据(JSON)
    status VARCHAR(20) DEFAULT 'GENERATED',                  -- 状态
    generated_by INTEGER,                                    -- 生成人ID
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 生成时间
    export_format VARCHAR(10),                               -- 导出格式
    export_path VARCHAR(500),                                -- 导出路径
    exported_at DATETIME,                                    -- 导出时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_definition_id) REFERENCES report_definition(id),
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);
CREATE TABLE report_subscription (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER NOT NULL,                          -- 订阅人ID
    subscriber_name VARCHAR(50),                             -- 订阅人
    report_definition_id INTEGER,                            -- 报表定义ID
    template_id INTEGER,                                     -- 模板ID
    report_type VARCHAR(30) NOT NULL,                        -- 报表类型
    scope_type VARCHAR(20),                                  -- 范围类型
    scope_id INTEGER,                                        -- 范围ID
    frequency VARCHAR(20) NOT NULL,                          -- 频率
    send_day INTEGER,                                        -- 发送日
    send_time VARCHAR(10) DEFAULT '09:00',                   -- 发送时间
    channels TEXT,                                           -- 发送渠道(JSON)
    email VARCHAR(100),                                      -- 邮箱
    export_format VARCHAR(10) DEFAULT 'PDF',                 -- 导出格式
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    last_sent_at DATETIME,                                   -- 上次发送时间
    next_send_at DATETIME,                                   -- 下次发送时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_definition_id) REFERENCES report_definition(id),
    FOREIGN KEY (template_id) REFERENCES report_template(id)
);
CREATE TABLE data_import_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_no VARCHAR(50) NOT NULL UNIQUE,                     -- 任务编号
    import_type VARCHAR(50) NOT NULL,                        -- 导入类型
    target_table VARCHAR(100),                               -- 目标表
    file_name VARCHAR(200) NOT NULL,                         -- 文件名
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    total_rows INTEGER DEFAULT 0,                            -- 总行数
    success_rows INTEGER DEFAULT 0,                          -- 成功行数
    failed_rows INTEGER DEFAULT 0,                           -- 失败行数
    skipped_rows INTEGER DEFAULT 0,                          -- 跳过行数
    validation_errors TEXT,                                  -- 校验错误(JSON)
    imported_by INTEGER NOT NULL,                            -- 导入人ID
    started_at DATETIME,                                     -- 开始时间
    completed_at DATETIME,                                   -- 完成时间
    error_message TEXT,                                      -- 错误信息
    error_log_path VARCHAR(500),                             -- 错误日志路径
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE data_export_task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_no VARCHAR(50) NOT NULL UNIQUE,                     -- 任务编号
    export_type VARCHAR(50) NOT NULL,                        -- 导出类型
    export_format VARCHAR(10) DEFAULT 'XLSX',                -- 导出格式
    query_params TEXT,                                       -- 查询参数(JSON)
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    file_name VARCHAR(200),                                  -- 文件名
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小
    total_rows INTEGER DEFAULT 0,                            -- 总行数
    exported_by INTEGER NOT NULL,                            -- 导出人ID
    started_at DATETIME,                                     -- 开始时间
    completed_at DATETIME,                                   -- 完成时间
    expires_at DATETIME,                                     -- 过期时间
    download_count INTEGER DEFAULT 0,                        -- 下载次数
    last_download_at DATETIME,                               -- 最后下载时间
    error_message TEXT,                                      -- 错误信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE import_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,               -- 模板编码
    template_name VARCHAR(100) NOT NULL,                     -- 模板名称
    import_type VARCHAR(50) NOT NULL,                        -- 导入类型
    template_file_path VARCHAR(500),                         -- 模板文件路径
    field_mappings TEXT NOT NULL,                            -- 字段映射(JSON)
    validation_rules TEXT,                                   -- 校验规则(JSON)
    description TEXT,                                        -- 说明
    instructions TEXT,                                       -- 填写说明
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_project_initiation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_no VARCHAR(50) NOT NULL UNIQUE,              -- 申请编号
    project_id INTEGER,                                      -- 项目ID(审批通过后关联)
    project_name VARCHAR(200) NOT NULL,                      -- 项目名称
    project_type VARCHAR(20) DEFAULT 'NEW',                  -- 项目类型:NEW/UPGRADE/MAINTAIN
    project_level VARCHAR(5),                                -- 建议级别:A/B/C
    customer_name VARCHAR(100) NOT NULL,                     -- 客户名称
    contract_no VARCHAR(50),                                 -- 合同编号
    contract_amount DECIMAL(14,2),                          -- 合同金额
    required_start_date DATE,                                -- 要求开始日期
    required_end_date DATE,                                  -- 要求交付日期
    technical_solution_id INTEGER,                           -- 关联技术方案ID
    requirement_summary TEXT,                                -- 需求概述
    technical_difficulty VARCHAR(20),                        -- 技术难度:LOW/MEDIUM/HIGH
    estimated_hours INTEGER,                                 -- 预估工时
    resource_requirements TEXT,                              -- 资源需求说明
    risk_assessment TEXT,                                    -- 初步风险评估
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 申请时间
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态:DRAFT/SUBMITTED/REVIEWING/APPROVED/REJECTED
    review_result TEXT,                                      -- 评审结论
    approved_pm_id INTEGER,                                  -- 指定项目经理ID
    approved_level VARCHAR(5),                               -- 评定级别
    approved_at DATETIME,                                    -- 审批时间
    approved_by INTEGER,                                     -- 审批人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_project_phase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    phase_code VARCHAR(20) NOT NULL,                         -- 阶段编码
    phase_name VARCHAR(50) NOT NULL,                         -- 阶段名称
    phase_order INTEGER DEFAULT 0,                           -- 阶段顺序
    plan_start_date DATE,                                    -- 计划开始
    plan_end_date DATE,                                      -- 计划结束
    actual_start_date DATE,                                  -- 实际开始
    actual_end_date DATE,                                    -- 实际结束
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态:PENDING/IN_PROGRESS/COMPLETED/SKIPPED
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    entry_criteria TEXT,                                     -- 入口条件
    exit_criteria TEXT,                                      -- 出口条件
    entry_check_result TEXT,                                 -- 入口检查结果
    exit_check_result TEXT,                                  -- 出口检查结果
    review_required INTEGER DEFAULT 1,                       -- 是否需要评审
    review_date DATE,                                        -- 评审日期
    review_result VARCHAR(20),                               -- 评审结果:PASSED/CONDITIONAL/FAILED
    review_notes TEXT,                                       -- 评审记录
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_change_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    change_no VARCHAR(50) NOT NULL UNIQUE,                   -- 变更编号
    change_type VARCHAR(20) NOT NULL,                        -- 变更类型:SCOPE/SCHEDULE/COST/RESOURCE/REQUIREMENT/OTHER
    change_level VARCHAR(20) DEFAULT 'MINOR',                -- 变更级别:MINOR/MAJOR/CRITICAL
    title VARCHAR(200) NOT NULL,                             -- 变更标题
    description TEXT NOT NULL,                               -- 变更描述
    reason TEXT,                                             -- 变更原因
    schedule_impact TEXT,                                    -- 进度影响
    cost_impact DECIMAL(12,2),                              -- 成本影响
    quality_impact TEXT,                                     -- 质量影响
    resource_impact TEXT,                                    -- 资源影响
    requestor_id INTEGER NOT NULL,                           -- 申请人ID
    requestor_name VARCHAR(50),                              -- 申请人
    request_time DATETIME DEFAULT CURRENT_TIMESTAMP,         -- 申请时间
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    pm_approval INTEGER,                                     -- 项目经理审批
    pm_approval_time DATETIME,                               -- 项目经理审批时间
    manager_approval INTEGER,                                -- 部门经理审批
    manager_approval_time DATETIME,                          -- 部门经理审批时间
    customer_approval INTEGER,                               -- 客户确认
    customer_approval_time DATETIME,                         -- 客户确认时间
    execution_status VARCHAR(20),                            -- 执行状态
    execution_notes TEXT,                                    -- 执行说明
    completed_time DATETIME,                                 -- 完成时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_project_risk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    risk_no VARCHAR(50) NOT NULL UNIQUE,                     -- 风险编号
    risk_category VARCHAR(20) NOT NULL,                      -- 风险类别
    risk_name VARCHAR(200) NOT NULL,                         -- 风险名称
    description TEXT,                                        -- 风险描述
    probability VARCHAR(20),                                 -- 发生概率:LOW/MEDIUM/HIGH
    impact VARCHAR(20),                                      -- 影响程度
    risk_level VARCHAR(20),                                  -- 风险等级
    response_strategy VARCHAR(20),                           -- 应对策略:AVOID/MITIGATE/TRANSFER/ACCEPT
    response_plan TEXT,                                      -- 应对措施
    owner_id INTEGER,                                        -- 责任人ID
    owner_name VARCHAR(50),                                  -- 责任人
    status VARCHAR(20) DEFAULT 'IDENTIFIED',                 -- 状态
    follow_up_date DATE,                                     -- 跟踪日期
    last_update TEXT,                                        -- 最新进展
    trigger_condition TEXT,                                  -- 触发条件
    is_triggered INTEGER DEFAULT 0,                          -- 是否已触发
    triggered_date DATE,                                     -- 触发日期
    closed_date DATE,                                        -- 关闭日期
    closed_reason TEXT,                                      -- 关闭原因
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_project_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    cost_category VARCHAR(50) NOT NULL,                      -- 成本类别
    cost_item VARCHAR(100) NOT NULL,                         -- 成本项
    budget_amount DECIMAL(12,2) DEFAULT 0,                  -- 预算金额
    actual_amount DECIMAL(12,2) DEFAULT 0,                  -- 实际金额
    cost_month VARCHAR(7),                                   -- 成本月份(YYYY-MM)
    record_date DATE,                                        -- 记录日期
    source_type VARCHAR(50),                                 -- 来源类型
    source_id INTEGER,                                       -- 来源ID
    source_no VARCHAR(50),                                   -- 来源单号
    remarks TEXT,                                            -- 备注
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_meeting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,                                      -- 项目ID
    meeting_type VARCHAR(20) NOT NULL,                       -- 会议类型
    meeting_name VARCHAR(200) NOT NULL,                      -- 会议名称
    meeting_date DATE NOT NULL,                              -- 会议日期
    start_time TIME,                                         -- 开始时间
    end_time TIME,                                           -- 结束时间
    location VARCHAR(100),                                   -- 会议地点
    organizer_id INTEGER,                                    -- 组织者ID
    organizer_name VARCHAR(50),                              -- 组织者
    attendees TEXT,                                          -- 参会人员(JSON)
    agenda TEXT,                                             -- 会议议程
    minutes TEXT,                                            -- 会议纪要
    decisions TEXT,                                          -- 会议决议
    action_items TEXT,                                       -- 待办事项(JSON)
    attachments TEXT,                                        -- 会议附件(JSON)
    status VARCHAR(20) DEFAULT 'SCHEDULED',                  -- 状态
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_resource_allocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                             -- 项目ID
    task_id INTEGER,                                         -- 任务ID
    resource_id INTEGER NOT NULL,                            -- 资源ID(人员ID)
    resource_name VARCHAR(50),                               -- 资源名称
    resource_dept VARCHAR(50),                               -- 所属部门
    resource_role VARCHAR(50),                               -- 项目角色
    allocation_percent INTEGER DEFAULT 100,                  -- 分配比例(%)
    start_date DATE,                                         -- 开始日期
    end_date DATE,                                           -- 结束日期
    planned_hours INTEGER,                                   -- 计划工时
    actual_hours INTEGER DEFAULT 0,                          -- 实际工时
    status VARCHAR(20) DEFAULT 'PLANNED',                    -- 状态
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pmo_project_closure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL UNIQUE,                      -- 项目ID
    acceptance_date DATE,                                    -- 验收日期
    acceptance_result VARCHAR(20),                           -- 验收结果
    acceptance_notes TEXT,                                   -- 验收说明
    project_summary TEXT,                                    -- 项目总结
    achievement TEXT,                                        -- 项目成果
    lessons_learned TEXT,                                    -- 经验教训
    improvement_suggestions TEXT,                            -- 改进建议
    final_budget DECIMAL(14,2),                             -- 最终预算
    final_cost DECIMAL(14,2),                               -- 最终成本
    cost_variance DECIMAL(14,2),                            -- 成本偏差
    final_planned_hours INTEGER,                             -- 最终计划工时
    final_actual_hours INTEGER,                              -- 最终实际工时
    hours_variance INTEGER,                                  -- 工时偏差
    plan_duration INTEGER,                                   -- 计划周期(天)
    actual_duration INTEGER,                                 -- 实际周期(天)
    schedule_variance INTEGER,                               -- 进度偏差(天)
    quality_score INTEGER,                                   -- 质量评分
    customer_satisfaction INTEGER,                           -- 客户满意度
    archive_status VARCHAR(20),                              -- 归档状态
    archive_path VARCHAR(500),                               -- 归档路径
    closure_date DATE,                                       -- 结项日期
    reviewed_by INTEGER,                                     -- 评审人
    review_date DATE,                                        -- 评审日期
    review_result VARCHAR(20),                               -- 评审结果
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE task_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_code VARCHAR(50) NOT NULL UNIQUE,                   -- 任务编号
    title VARCHAR(200) NOT NULL,                             -- 任务标题
    description TEXT,                                        -- 任务描述
    task_type VARCHAR(20) NOT NULL,                          -- 任务类型
    source_type VARCHAR(50),                                 -- 来源类型
    source_id INTEGER,                                       -- 来源ID
    source_name VARCHAR(200),                                -- 来源名称
    parent_task_id INTEGER,                                  -- 父任务ID
    project_id INTEGER,                                      -- 关联项目ID
    project_code VARCHAR(50),                                -- 项目编号
    project_name VARCHAR(200),                               -- 项目名称
    wbs_code VARCHAR(50),                                    -- WBS编码
    assignee_id INTEGER NOT NULL,                            -- 执行人ID
    assignee_name VARCHAR(50),                               -- 执行人姓名
    assigner_id INTEGER,                                     -- 指派人ID
    assigner_name VARCHAR(50),                               -- 指派人姓名
    plan_start_date DATE,                                    -- 计划开始日期
    plan_end_date DATE,                                      -- 计划结束日期
    actual_start_date DATE,                                  -- 实际开始日期
    actual_end_date DATE,                                    -- 实际完成日期
    deadline DATETIME,                                       -- 截止时间
    estimated_hours DECIMAL(10,2),                          -- 预估工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    progress INTEGER DEFAULT 0,                              -- 进度百分比
    priority VARCHAR(20) DEFAULT 'MEDIUM',                   -- 优先级
    is_urgent INTEGER DEFAULT 0,                             -- 是否紧急
    is_recurring INTEGER DEFAULT 0,                          -- 是否周期性
    recurrence_rule VARCHAR(200),                            -- 周期规则
    recurrence_end_date DATE,                                -- 周期结束日期
    is_transferred INTEGER DEFAULT 0,                        -- 是否转办
    transfer_from_id INTEGER,                                -- 转办来源人ID
    transfer_from_name VARCHAR(50),                          -- 转办来源人
    transfer_reason TEXT,                                    -- 转办原因
    transfer_time DATETIME,                                  -- 转办时间
    deliverables TEXT,                                       -- 交付物清单(JSON)
    attachments TEXT,                                        -- 附件列表(JSON)
    tags TEXT,                                               -- 标签(JSON)
    category VARCHAR(50),                                    -- 分类
    reminder_enabled INTEGER DEFAULT 1,                      -- 是否开启提醒
    reminder_before_hours INTEGER DEFAULT 24,                -- 提前提醒小时数
    created_by INTEGER,                                      -- 创建人ID
    updated_by INTEGER,                                      -- 更新人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, approval_required BOOLEAN DEFAULT 0, approval_status VARCHAR(20), approved_by INTEGER, approved_at DATETIME, approval_note TEXT, task_importance VARCHAR(20) DEFAULT 'GENERAL', completion_note TEXT, is_delayed BOOLEAN DEFAULT 0, delay_reason TEXT, delay_responsibility VARCHAR(100), delay_impact_scope VARCHAR(50), new_completion_date DATE, delay_reported_at DATETIME, delay_reported_by INTEGER, is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (parent_task_id) REFERENCES task_unified(id)
);
CREATE TABLE job_duty_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,                            -- 岗位ID
    position_name VARCHAR(100),                              -- 岗位名称
    department_id INTEGER,                                   -- 部门ID
    duty_name VARCHAR(200) NOT NULL,                         -- 职责名称
    duty_description TEXT,                                   -- 职责描述
    frequency VARCHAR(20) NOT NULL,                          -- 频率
    day_of_week INTEGER,                                     -- 周几(1-7)
    day_of_month INTEGER,                                    -- 几号(1-31)
    month_of_year INTEGER,                                   -- 几月(1-12)
    auto_generate INTEGER DEFAULT 1,                         -- 自动生成任务
    generate_before_days INTEGER DEFAULT 3,                  -- 提前几天生成
    deadline_offset_days INTEGER DEFAULT 0,                  -- 截止日期偏移
    default_priority VARCHAR(20) DEFAULT 'MEDIUM',           -- 默认优先级
    estimated_hours DECIMAL(10,2),                          -- 预估工时
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE task_operation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    operation_type VARCHAR(50) NOT NULL,                     -- 操作类型
    operation_desc TEXT,                                     -- 操作描述
    old_value TEXT,                                          -- 变更前值(JSON)
    new_value TEXT,                                          -- 变更后值(JSON)
    operator_id INTEGER,                                     -- 操作人ID
    operator_name VARCHAR(50),                               -- 操作人
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,       -- 操作时间
    FOREIGN KEY (task_id) REFERENCES task_unified(id)
);
CREATE TABLE task_comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    content TEXT NOT NULL,                                   -- 评论内容
    comment_type VARCHAR(20) DEFAULT 'COMMENT',              -- 评论类型
    parent_id INTEGER,                                       -- 回复的评论ID
    commenter_id INTEGER,                                    -- 评论人ID
    commenter_name VARCHAR(50),                              -- 评论人
    mentioned_users TEXT,                                    -- @的用户(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (parent_id) REFERENCES task_comment(id)
);
CREATE TABLE task_reminder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,                                -- 任务ID
    user_id INTEGER NOT NULL,                                -- 用户ID
    reminder_type VARCHAR(20) NOT NULL,                      -- 提醒类型
    remind_at DATETIME NOT NULL,                             -- 提醒时间
    is_sent INTEGER DEFAULT 0,                               -- 是否已发送
    sent_at DATETIME,                                        -- 发送时间
    channel VARCHAR(20) DEFAULT 'SYSTEM',                    -- 通知渠道
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task_unified(id)
);
CREATE TABLE presale_support_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no VARCHAR(50) NOT NULL UNIQUE,                   -- 工单编号
    title VARCHAR(200) NOT NULL,                             -- 工单标题
    ticket_type VARCHAR(20) NOT NULL,                        -- 工单类型
    urgency VARCHAR(20) DEFAULT 'NORMAL',                    -- 紧急程度
    description TEXT,                                        -- 详细描述
    customer_id INTEGER,                                     -- 客户ID
    customer_name VARCHAR(100),                              -- 客户名称
    opportunity_id INTEGER,                                  -- 关联商机ID
    project_id INTEGER,                                      -- 关联项目ID
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    applicant_name VARCHAR(50),                              -- 申请人姓名
    applicant_dept VARCHAR(100),                             -- 申请人部门
    apply_time DATETIME DEFAULT CURRENT_TIMESTAMP,           -- 申请时间
    assignee_id INTEGER,                                     -- 指派处理人ID
    assignee_name VARCHAR(50),                               -- 处理人姓名
    accept_time DATETIME,                                    -- 接单时间
    expected_date DATE,                                      -- 期望完成日期
    deadline DATETIME,                                       -- 截止时间
    status VARCHAR(20) DEFAULT 'PENDING',                    -- 状态
    complete_time DATETIME,                                  -- 完成时间
    actual_hours DECIMAL(10,2),                             -- 实际工时
    satisfaction_score INTEGER,                              -- 满意度评分(1-5)
    feedback TEXT,                                           -- 反馈意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE presale_ticket_deliverable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,                              -- 工单ID
    name VARCHAR(200) NOT NULL,                              -- 文件名称
    file_type VARCHAR(50),                                   -- 文件类型
    file_path VARCHAR(500),                                  -- 文件路径
    file_size INTEGER,                                       -- 文件大小(bytes)
    version VARCHAR(20) DEFAULT 'V1.0',                      -- 版本号
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    reviewer_id INTEGER,                                     -- 审核人ID
    review_time DATETIME,                                    -- 审核时间
    review_comment TEXT,                                     -- 审核意见
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);
CREATE TABLE presale_ticket_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,                              -- 工单ID
    progress_type VARCHAR(20) NOT NULL,                      -- 进度类型
    content TEXT,                                            -- 进度内容
    progress_percent INTEGER,                                -- 进度百分比
    operator_id INTEGER NOT NULL,                            -- 操作人ID
    operator_name VARCHAR(50),                               -- 操作人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);
CREATE TABLE presale_solution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_no VARCHAR(50) NOT NULL UNIQUE,                 -- 方案编号
    name VARCHAR(200) NOT NULL,                              -- 方案名称
    solution_type VARCHAR(20) DEFAULT 'CUSTOM',              -- 方案类型
    industry VARCHAR(50),                                    -- 所属行业
    test_type VARCHAR(100),                                  -- 测试类型
    ticket_id INTEGER,                                       -- 关联工单ID
    customer_id INTEGER,                                     -- 客户ID
    opportunity_id INTEGER,                                  -- 商机ID
    requirement_summary TEXT,                                -- 需求概述
    solution_overview TEXT,                                  -- 方案概述
    technical_spec TEXT,                                     -- 技术规格
    estimated_cost DECIMAL(12,2),                           -- 预估成本
    suggested_price DECIMAL(12,2),                          -- 建议报价
    cost_breakdown TEXT,                                     -- 成本明细(JSON)
    estimated_hours INTEGER,                                 -- 预估工时
    estimated_duration INTEGER,                              -- 预估周期
    status VARCHAR(20) DEFAULT 'DRAFT',                      -- 状态
    version VARCHAR(20) DEFAULT 'V1.0',                      -- 版本
    parent_id INTEGER,                                       -- 父版本ID
    reviewer_id INTEGER,                                     -- 审核人
    review_time DATETIME,                                    -- 审核时间
    review_status VARCHAR(20),                               -- 审核状态
    review_comment TEXT,                                     -- 审核意见
    author_id INTEGER NOT NULL,                              -- 编制人ID
    author_name VARCHAR(50),                                 -- 编制人姓名
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id),
    FOREIGN KEY (parent_id) REFERENCES presale_solution(id)
);
CREATE TABLE presale_solution_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solution_id INTEGER NOT NULL,                            -- 方案ID
    category VARCHAR(50) NOT NULL,                           -- 成本类别
    item_name VARCHAR(200) NOT NULL,                         -- 项目名称
    specification VARCHAR(200),                              -- 规格型号
    unit VARCHAR(20),                                        -- 单位
    quantity DECIMAL(10,2),                                 -- 数量
    unit_price DECIMAL(12,2),                               -- 单价
    amount DECIMAL(12,2),                                   -- 金额
    remark VARCHAR(500),                                     -- 备注
    sort_order INTEGER DEFAULT 0,                            -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (solution_id) REFERENCES presale_solution(id)
);
CREATE TABLE presale_solution_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_no VARCHAR(50) NOT NULL UNIQUE,                 -- 模板编号
    name VARCHAR(200) NOT NULL,                              -- 模板名称
    industry VARCHAR(50),                                    -- 适用行业
    test_type VARCHAR(100),                                  -- 测试类型
    description TEXT,                                        -- 模板描述
    content_template TEXT,                                   -- 内容模板
    cost_template TEXT,                                      -- 成本模板(JSON)
    attachments TEXT,                                        -- 附件列表(JSON)
    use_count INTEGER DEFAULT 0,                             -- 使用次数
    is_active INTEGER DEFAULT 1,                             -- 是否启用
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE presale_workload (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                                -- 人员ID
    stat_date DATE NOT NULL,                                 -- 统计日期
    pending_tickets INTEGER DEFAULT 0,                       -- 待处理工单数
    processing_tickets INTEGER DEFAULT 0,                    -- 进行中工单数
    completed_tickets INTEGER DEFAULT 0,                     -- 已完成工单数
    planned_hours DECIMAL(10,2) DEFAULT 0,                  -- 计划工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    solutions_count INTEGER DEFAULT 0,                       -- 方案数量
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, stat_date)
);
CREATE TABLE presale_customer_tech_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL UNIQUE,                     -- 客户ID
    industry VARCHAR(50),                                    -- 所属行业
    business_scope TEXT,                                     -- 业务范围
    common_test_types VARCHAR(500),                          -- 常见测试类型
    technical_requirements TEXT,                             -- 技术要求特点
    quality_standards VARCHAR(500),                          -- 质量标准要求
    existing_equipment TEXT,                                 -- 现有设备情况
    it_infrastructure TEXT,                                  -- IT基础设施
    mes_system VARCHAR(100),                                 -- MES系统类型
    cooperation_history TEXT,                                -- 合作历史
    success_cases TEXT,                                      -- 成功案例
    technical_contacts TEXT,                                 -- 技术联系人(JSON)
    notes TEXT,                                              -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE presale_tender_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,                                       -- 关联工单ID
    opportunity_id INTEGER,                                  -- 关联商机ID
    tender_no VARCHAR(50),                                   -- 招标编号
    tender_name VARCHAR(200) NOT NULL,                       -- 项目名称
    customer_name VARCHAR(100),                              -- 招标单位
    publish_date DATE,                                       -- 发布日期
    deadline DATETIME,                                       -- 投标截止时间
    bid_opening_date DATE,                                   -- 开标日期
    budget_amount DECIMAL(14,2),                            -- 预算金额
    qualification_requirements TEXT,                         -- 资质要求
    technical_requirements TEXT,                             -- 技术要求
    our_bid_amount DECIMAL(14,2),                           -- 我方报价
    technical_score DECIMAL(5,2),                           -- 技术得分
    commercial_score DECIMAL(5,2),                          -- 商务得分
    total_score DECIMAL(5,2),                               -- 总得分
    competitors TEXT,                                        -- 竞争对手信息(JSON)
    result VARCHAR(20) DEFAULT 'PENDING',                    -- 结果
    result_reason TEXT,                                      -- 中标/落标原因分析
    leader_id INTEGER,                                       -- 投标负责人
    team_members TEXT,                                       -- 投标团队(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES presale_support_ticket(id)
);
CREATE TABLE workshop (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workshop_code VARCHAR(50) NOT NULL UNIQUE,               -- 车间编码
    workshop_name VARCHAR(100) NOT NULL,                     -- 车间名称
    workshop_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',      -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/WAREHOUSE/OTHER
    manager_id INTEGER,                                      -- 车间主管ID
    location VARCHAR(200),                                   -- 车间位置
    capacity_hours DECIMAL(10,2),                           -- 日产能(工时)
    description TEXT,                                        -- 描述
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    -- FOREIGN KEY (manager_id) REFERENCES user(id) -- Deferred: user table created by ORM
);
INSERT INTO workshop VALUES(1,'WS-MACH','机加车间','MACHINING',NULL,NULL,120,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO workshop VALUES(2,'WS-ASSY','装配车间','ASSEMBLY',NULL,NULL,160,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO workshop VALUES(3,'WS-DBUG','调试车间','DEBUGGING',NULL,NULL,80,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO workshop VALUES(4,'WS-WELD','焊接车间','WELDING',NULL,NULL,60,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE workstation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workstation_code VARCHAR(50) NOT NULL UNIQUE,            -- 工位编码
    workstation_name VARCHAR(100) NOT NULL,                  -- 工位名称
    workshop_id INTEGER NOT NULL,                            -- 所属车间ID
    equipment_id INTEGER,                                    -- 关联设备ID
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',              -- 状态:IDLE/WORKING/MAINTENANCE/DISABLED
    current_worker_id INTEGER,                               -- 当前操作工ID
    current_work_order_id INTEGER,                           -- 当前工单ID
    description TEXT,                                        -- 描述
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);
CREATE TABLE worker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_no VARCHAR(50) NOT NULL UNIQUE,                   -- 工号
    user_id INTEGER,                                         -- 关联用户ID
    worker_name VARCHAR(50) NOT NULL,                        -- 姓名
    workshop_id INTEGER,                                     -- 所属车间ID
    position VARCHAR(50),                                    -- 岗位
    skill_level VARCHAR(20) DEFAULT 'JUNIOR',                -- 技能等级:JUNIOR/INTERMEDIATE/SENIOR/EXPERT
    phone VARCHAR(20),                                       -- 联系电话
    entry_date DATE,                                         -- 入职日期
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',            -- 状态:ACTIVE/LEAVE/RESIGNED
    hourly_rate DECIMAL(10,2),                              -- 时薪(元)
    remark TEXT,                                             -- 备注
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否在职
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
    -- FOREIGN KEY (user_id) REFERENCES user(id) -- Deferred: user table created by ORM
);
CREATE TABLE worker_skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER NOT NULL,                              -- 工人ID
    process_id INTEGER NOT NULL,                             -- 工序ID
    skill_level VARCHAR(20) NOT NULL DEFAULT 'JUNIOR',       -- 技能等级
    certified_date DATE,                                     -- 认证日期
    expiry_date DATE,                                        -- 有效期
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES worker(id),
    FOREIGN KEY (process_id) REFERENCES process_dict(id)
);
CREATE TABLE process_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_code VARCHAR(50) NOT NULL UNIQUE,                -- 工序编码
    process_name VARCHAR(100) NOT NULL,                      -- 工序名称
    process_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',       -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/SURFACE/INSPECTION/OTHER
    standard_hours DECIMAL(10,2),                           -- 标准工时(小时)
    description TEXT,                                        -- 描述
    work_instruction TEXT,                                   -- 作业指导
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO process_dict VALUES(1,'CNC-MILL','CNC铣削','MACHINING',4,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(2,'CNC-TURN','CNC车削','MACHINING',3,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(3,'CNC-DRILL','钻孔加工','MACHINING',2,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(4,'GRIND','磨削加工','MACHINING',3,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(5,'WELD-ARC','弧焊','WELDING',4,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(6,'WELD-SPOT','点焊','WELDING',2,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(7,'MECH-ASM','机械装配','ASSEMBLY',6,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(8,'ELEC-ASM','电气装配','ASSEMBLY',8,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(9,'PIPE-ASM','管路装配','ASSEMBLY',4,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(10,'ELEC-DBG','电气调试','DEBUGGING',8,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(11,'SOFT-DBG','软件调试','DEBUGGING',16,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(12,'FINAL-DBG','整机调试','DEBUGGING',24,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO process_dict VALUES(13,'QC-INSP','质量检验','INSPECTION',2,NULL,NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_code VARCHAR(50) NOT NULL UNIQUE,              -- 设备编码
    equipment_name VARCHAR(100) NOT NULL,                    -- 设备名称
    model VARCHAR(100),                                      -- 型号规格
    manufacturer VARCHAR(100),                               -- 生产厂家
    workshop_id INTEGER,                                     -- 所属车间ID
    purchase_date DATE,                                      -- 购置日期
    status VARCHAR(20) NOT NULL DEFAULT 'IDLE',              -- 状态:IDLE/RUNNING/MAINTENANCE/REPAIR/DISABLED
    last_maintenance_date DATE,                              -- 上次保养日期
    next_maintenance_date DATE,                              -- 下次保养日期
    asset_no VARCHAR(50),                                    -- 固定资产编号
    remark TEXT,                                             -- 备注
    is_active INTEGER NOT NULL DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
);
CREATE TABLE equipment_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,                           -- 设备ID
    maintenance_type VARCHAR(20) NOT NULL,                   -- 类型:maintenance/repair
    maintenance_date DATE NOT NULL,                          -- 保养/维修日期
    content TEXT,                                            -- 保养/维修内容
    cost DECIMAL(14,2),                                     -- 费用
    performed_by VARCHAR(50),                                -- 执行人
    next_maintenance_date DATE,                              -- 下次保养日期
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);
CREATE TABLE production_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_no VARCHAR(50) NOT NULL UNIQUE,                     -- 计划编号
    plan_name VARCHAR(200) NOT NULL,                         -- 计划名称
    plan_type VARCHAR(20) NOT NULL DEFAULT 'MASTER',         -- 类型:MASTER(主计划)/WORKSHOP(车间计划)
    project_id INTEGER,                                      -- 关联项目ID
    workshop_id INTEGER,                                     -- 车间ID(车间计划用)
    plan_start_date DATE NOT NULL,                           -- 计划开始日期
    plan_end_date DATE NOT NULL,                             -- 计划结束日期
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',             -- 状态:DRAFT/SUBMITTED/APPROVED/PUBLISHED/EXECUTING/COMPLETED/CANCELLED
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    description TEXT,                                        -- 计划说明
    created_by INTEGER,                                      -- 创建人ID
    approved_by INTEGER,                                     -- 审批人ID
    approved_at DATETIME,                                    -- 审批时间
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workshop_id) REFERENCES workshop(id)
    -- Note: FKs to project/user tables deferred (created by ORM or other migrations)
);
CREATE TABLE work_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_no VARCHAR(50) NOT NULL UNIQUE,               -- 工单编号
    task_name VARCHAR(200) NOT NULL,                         -- 任务名称
    task_type VARCHAR(20) NOT NULL DEFAULT 'OTHER',          -- 类型:MACHINING/ASSEMBLY/DEBUGGING/WELDING/INSPECTION/OTHER
    project_id INTEGER,                                      -- 项目ID
    machine_id INTEGER,                                      -- 机台ID
    production_plan_id INTEGER,                              -- 生产计划ID
    process_id INTEGER,                                      -- 工序ID
    workshop_id INTEGER,                                     -- 车间ID
    workstation_id INTEGER,                                  -- 工位ID
    
    -- 物料相关
    material_id INTEGER,                                     -- 物料ID
    material_name VARCHAR(200),                              -- 物料名称
    specification VARCHAR(200),                              -- 规格型号
    drawing_no VARCHAR(100),                                 -- 图纸编号
    
    -- 计划信息
    plan_qty INTEGER DEFAULT 1,                              -- 计划数量
    completed_qty INTEGER DEFAULT 0,                         -- 完成数量
    qualified_qty INTEGER DEFAULT 0,                         -- 合格数量
    defect_qty INTEGER DEFAULT 0,                            -- 不良数量
    standard_hours DECIMAL(10,2),                           -- 标准工时(小时)
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时(小时)
    
    -- 时间安排
    plan_start_date DATE,                                    -- 计划开始日期
    plan_end_date DATE,                                      -- 计划结束日期
    actual_start_time DATETIME,                              -- 实际开始时间
    actual_end_time DATETIME,                                -- 实际结束时间
    
    -- 派工信息
    assigned_to INTEGER,                                     -- 指派给(工人ID)
    assigned_at DATETIME,                                    -- 派工时间
    assigned_by INTEGER,                                     -- 派工人ID
    
    -- 状态信息
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',           -- 状态:PENDING/ASSIGNED/STARTED/PAUSED/COMPLETED/APPROVED/CANCELLED
    priority VARCHAR(20) NOT NULL DEFAULT 'NORMAL',          -- 优先级:LOW/NORMAL/HIGH/URGENT
    progress INTEGER DEFAULT 0,                              -- 进度(%)
    
    -- 其他
    work_content TEXT,                                       -- 工作内容
    remark TEXT,                                             -- 备注
    pause_reason TEXT,                                       -- 暂停原因
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (production_plan_id) REFERENCES production_plan(id),
    FOREIGN KEY (process_id) REFERENCES process_dict(id),
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (workstation_id) REFERENCES workstation(id),
    FOREIGN KEY (assigned_to) REFERENCES worker(id)
    -- Note: FKs to project/machine/material/user tables deferred
);
CREATE TABLE work_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_no VARCHAR(50) NOT NULL UNIQUE,                   -- 报工单号
    work_order_id INTEGER NOT NULL,                          -- 工单ID
    worker_id INTEGER NOT NULL,                              -- 工人ID
    report_type VARCHAR(20) NOT NULL,                        -- 类型:START/PROGRESS/PAUSE/RESUME/COMPLETE
    report_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 报工时间
    
    -- 进度信息
    progress_percent INTEGER,                                -- 进度百分比
    work_hours DECIMAL(10,2),                               -- 本次工时(小时)
    
    -- 完工信息
    completed_qty INTEGER,                                   -- 完成数量
    qualified_qty INTEGER,                                   -- 合格数量
    defect_qty INTEGER,                                      -- 不良数量
    
    -- 审核信息
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',           -- 状态:PENDING/APPROVED/REJECTED
    approved_by INTEGER,                                     -- 审核人ID
    approved_at DATETIME,                                    -- 审核时间
    approve_comment TEXT,                                    -- 审核意见
    
    -- 其他
    description TEXT,                                        -- 工作描述
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (worker_id) REFERENCES worker(id)
    -- Note: FK to user table deferred
);
CREATE TABLE production_exception (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exception_no VARCHAR(50) NOT NULL UNIQUE,                -- 异常编号
    exception_type VARCHAR(20) NOT NULL,                     -- 类型:MATERIAL/EQUIPMENT/QUALITY/PROCESS/SAFETY/OTHER
    exception_level VARCHAR(20) NOT NULL DEFAULT 'MINOR',    -- 级别:MINOR/MAJOR/CRITICAL
    title VARCHAR(200) NOT NULL,                             -- 异常标题
    description TEXT,                                        -- 异常描述
    
    -- 关联信息
    work_order_id INTEGER,                                   -- 关联工单ID
    project_id INTEGER,                                      -- 关联项目ID
    workshop_id INTEGER,                                     -- 车间ID
    equipment_id INTEGER,                                    -- 设备ID
    
    -- 上报信息
    reporter_id INTEGER NOT NULL,                            -- 上报人ID
    report_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 上报时间
    
    -- 处理信息
    status VARCHAR(20) NOT NULL DEFAULT 'REPORTED',          -- 状态:REPORTED/HANDLING/RESOLVED/CLOSED
    handler_id INTEGER,                                      -- 处理人ID
    handle_plan TEXT,                                        -- 处理方案
    handle_result TEXT,                                      -- 处理结果
    handle_time DATETIME,                                    -- 处理时间
    resolved_at DATETIME,                                    -- 解决时间
    
    -- 影响评估
    impact_hours DECIMAL(10,2),                             -- 影响工时(小时)
    impact_cost DECIMAL(14,2),                              -- 影响成本(元)
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
    -- Note: FKs to project/user tables deferred
);
CREATE TABLE material_requisition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requisition_no VARCHAR(50) NOT NULL UNIQUE,              -- 领料单号
    work_order_id INTEGER,                                   -- 关联工单ID
    project_id INTEGER,                                      -- 项目ID
    
    -- 申请信息
    applicant_id INTEGER NOT NULL,                           -- 申请人ID
    apply_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 申请时间
    apply_reason TEXT,                                       -- 申请原因
    
    -- 审批信息
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',             -- 状态:DRAFT/SUBMITTED/APPROVED/REJECTED/ISSUED/COMPLETED/CANCELLED
    approved_by INTEGER,                                     -- 审批人ID
    approved_at DATETIME,                                    -- 审批时间
    approve_comment TEXT,                                    -- 审批意见
    
    -- 发料信息
    issued_by INTEGER,                                       -- 发料人ID
    issued_at DATETIME,                                      -- 发料时间
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id)
    -- Note: FKs to project/user tables deferred
);
CREATE TABLE material_requisition_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requisition_id INTEGER NOT NULL,                         -- 领料单ID
    material_id INTEGER NOT NULL,                            -- 物料ID
    
    request_qty DECIMAL(14,4) NOT NULL,                     -- 申请数量
    approved_qty DECIMAL(14,4),                             -- 批准数量
    issued_qty DECIMAL(14,4),                               -- 发放数量
    unit VARCHAR(20),                                        -- 单位
    
    remark TEXT,                                             -- 备注
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (requisition_id) REFERENCES material_requisition(id)
    -- Note: FK to material table deferred
);
CREATE TABLE production_daily_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE NOT NULL,                               -- 报告日期
    workshop_id INTEGER,                                     -- 车间ID(空表示全厂)
    
    -- 生产统计
    plan_qty INTEGER DEFAULT 0,                              -- 计划数量
    completed_qty INTEGER DEFAULT 0,                         -- 完成数量
    completion_rate DECIMAL(5,2) DEFAULT 0,                 -- 完成率(%)
    
    -- 工时统计
    plan_hours DECIMAL(10,2) DEFAULT 0,                     -- 计划工时
    actual_hours DECIMAL(10,2) DEFAULT 0,                   -- 实际工时
    overtime_hours DECIMAL(10,2) DEFAULT 0,                 -- 加班工时
    efficiency DECIMAL(5,2) DEFAULT 0,                      -- 效率(%)
    
    -- 出勤统计
    should_attend INTEGER DEFAULT 0,                         -- 应出勤人数
    actual_attend INTEGER DEFAULT 0,                         -- 实际出勤
    leave_count INTEGER DEFAULT 0,                           -- 请假人数
    
    -- 质量统计
    total_qty INTEGER DEFAULT 0,                             -- 生产总数
    qualified_qty INTEGER DEFAULT 0,                         -- 合格数量
    pass_rate DECIMAL(5,2) DEFAULT 0,                       -- 合格率(%)
    
    -- 异常统计
    new_exception_count INTEGER DEFAULT 0,                   -- 新增异常数
    resolved_exception_count INTEGER DEFAULT 0,              -- 解决异常数
    
    summary TEXT,                                            -- 日报总结
    created_by INTEGER,                                      -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (workshop_id) REFERENCES workshop(id),
    UNIQUE(report_date, workshop_id)
    -- Note: FK to user table deferred
);
INSERT INTO production_daily_report VALUES(1,'2026-01-29',NULL,0,0,0,0,0,0,0,0,0,0,0,0,100,0,0,NULL,NULL,'2026-01-30 16:01:47.189663','2026-01-30 16:01:47.189664');
CREATE TABLE issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_no            VARCHAR(50) NOT NULL UNIQUE,          -- 问题编号
    category            VARCHAR(20) NOT NULL,                 -- 问题分类
    project_id          INTEGER,                              -- 关联项目ID
    machine_id          INTEGER,                              -- 关联机台ID
    task_id             INTEGER,                              -- 关联任务ID
    acceptance_order_id INTEGER,                              -- 关联验收单ID
    related_issue_id    INTEGER,                              -- 关联问题ID（父子问题）
    
    -- 问题基本信息
    issue_type          VARCHAR(20) NOT NULL,                 -- 问题类型
    severity            VARCHAR(20) NOT NULL,                 -- 严重程度
    priority            VARCHAR(20) DEFAULT 'MEDIUM',          -- 优先级
    title               VARCHAR(200) NOT NULL,                -- 问题标题
    description         TEXT NOT NULL,                        -- 问题描述
    
    -- 提出人信息
    reporter_id         INTEGER NOT NULL,                     -- 提出人ID
    reporter_name       VARCHAR(50),                          -- 提出人姓名
    report_date         DATETIME NOT NULL,                    -- 提出时间
    
    -- 处理人信息
    assignee_id         INTEGER,                              -- 处理负责人ID
    assignee_name       VARCHAR(50),                          -- 处理负责人姓名
    due_date            DATE,                                 -- 要求完成日期
    
    -- 状态信息
    status              VARCHAR(20) DEFAULT 'OPEN' NOT NULL, -- 问题状态
    
    -- 解决信息
    solution            TEXT,                                 -- 解决方案
    resolved_at         DATETIME,                             -- 解决时间
    resolved_by         INTEGER,                              -- 解决人ID
    resolved_by_name    VARCHAR(50),                          -- 解决人姓名
    
    -- 验证信息
    verified_at         DATETIME,                             -- 验证时间
    verified_by         INTEGER,                              -- 验证人ID
    verified_by_name     VARCHAR(50),                          -- 验证人姓名
    verified_result      VARCHAR(20),                          -- 验证结果
    
    -- 影响评估
    impact_scope        TEXT,                                 -- 影响范围
    impact_level        VARCHAR(20),                          -- 影响级别
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞
    
    -- 附件和标签
    attachments         TEXT,                                 -- 附件列表JSON
    tags                TEXT,                                 -- 标签JSON数组
    
    -- 统计信息
    follow_up_count     INTEGER DEFAULT 0,                    -- 跟进次数
    last_follow_up_at   DATETIME,                             -- 最后跟进时间
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, root_cause VARCHAR(20) DEFAULT NULL, responsible_engineer_id INTEGER DEFAULT NULL, responsible_engineer_name VARCHAR(50) DEFAULT NULL, estimated_inventory_loss DECIMAL(14, 2) DEFAULT NULL, estimated_extra_hours DECIMAL(10, 2) DEFAULT NULL, service_ticket_id INTEGER,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (related_issue_id) REFERENCES issues(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);
CREATE TABLE issue_follow_up_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_id            INTEGER NOT NULL,                     -- 问题ID
    follow_up_type      VARCHAR(20) NOT NULL,                 -- 跟进类型
    content             TEXT NOT NULL,                        -- 跟进内容
    operator_id         INTEGER NOT NULL,                     -- 操作人ID
    operator_name       VARCHAR(50),                          -- 操作人姓名
    old_status          VARCHAR(20),                          -- 原状态
    new_status          VARCHAR(20),                          -- 新状态
    attachments         TEXT,                                 -- 附件列表JSON
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (issue_id) REFERENCES issues(id),
    FOREIGN KEY (operator_id) REFERENCES users(id)
);
CREATE TABLE rd_project_category (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code       VARCHAR(20) NOT NULL UNIQUE,              -- 分类编码
    category_name       VARCHAR(50) NOT NULL,                    -- 分类名称
    category_type       VARCHAR(20) NOT NULL,                    -- 分类类型：SELF/ENTRUST/COOPERATION
    description         TEXT,                                     -- 分类说明
    sort_order          INTEGER DEFAULT 0,                       -- 排序
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rd_project (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_no          VARCHAR(50) NOT NULL UNIQUE,              -- 研发项目编号
    project_name        VARCHAR(200) NOT NULL,                   -- 研发项目名称
    
    -- 分类信息
    category_id         INTEGER,                                  -- 项目分类ID
    category_type       VARCHAR(20) NOT NULL,                    -- 项目类型：SELF/ENTRUST/COOPERATION
    
    -- 立项信息
    initiation_date     DATE NOT NULL,                           -- 立项日期
    planned_start_date  DATE,                                    -- 计划开始日期
    planned_end_date    DATE,                                    -- 计划结束日期
    actual_start_date   DATE,                                    -- 实际开始日期
    actual_end_date     DATE,                                    -- 实际结束日期
    
    -- 项目负责人
    project_manager_id  INTEGER,                                 -- 项目负责人ID
    project_manager_name VARCHAR(50),                           -- 项目负责人姓名
    
    -- 立项信息
    initiation_reason   TEXT,                                    -- 立项原因
    research_goal       TEXT,                                    -- 研发目标
    research_content    TEXT,                                    -- 研发内容
    expected_result     TEXT,                                    -- 预期成果
    budget_amount       DECIMAL(12,2) DEFAULT 0,                -- 预算金额
    
    -- 关联非标项目
    linked_project_id   INTEGER,                                 -- 关联的非标项目ID
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',            -- 状态：DRAFT/PENDING/APPROVED/IN_PROGRESS/COMPLETED/CANCELLED
    approval_status     VARCHAR(20) DEFAULT 'PENDING',          -- 审批状态：PENDING/APPROVED/REJECTED
    approved_by         INTEGER,                                 -- 审批人ID
    approved_at         DATETIME,                                -- 审批时间
    approval_remark     TEXT,                                    -- 审批意见
    
    -- 结项信息
    close_date          DATE,                                    -- 结项日期
    close_reason        TEXT,                                    -- 结项原因
    close_result        TEXT,                                    -- 结项成果
    closed_by           INTEGER,                                 -- 结项人ID
    
    -- 统计信息
    total_cost          DECIMAL(12,2) DEFAULT 0,                 -- 总费用
    total_hours         DECIMAL(10,2) DEFAULT 0,                -- 总工时
    participant_count   INTEGER DEFAULT 0,                      -- 参与人数
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES rd_project_category(id),
    FOREIGN KEY (project_manager_id) REFERENCES users(id),
    FOREIGN KEY (linked_project_id) REFERENCES projects(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id)
);
CREATE TABLE rd_cost_type (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type_code           VARCHAR(20) NOT NULL UNIQUE,              -- 费用类型编码
    type_name           VARCHAR(50) NOT NULL,                    -- 费用类型名称
    category            VARCHAR(20) NOT NULL,                    -- 费用大类：LABOR/MATERIAL/DEPRECIATION/OTHER
    description         TEXT,                                     -- 类型说明
    sort_order          INTEGER DEFAULT 0,                       -- 排序
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    
    -- 加计扣除相关
    is_deductible       BOOLEAN DEFAULT 1,                       -- 是否可加计扣除
    deduction_rate      DECIMAL(5,2) DEFAULT 100.00,             -- 加计扣除比例(%)
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rd_cost_allocation_rule (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name           VARCHAR(100) NOT NULL,                   -- 规则名称
    rule_type           VARCHAR(20) NOT NULL,                    -- 分摊类型：PROPORTION/MANUAL
    
    -- 分摊依据
    allocation_basis    VARCHAR(20) NOT NULL,                   -- 分摊依据：HOURS/REVENUE/HEADCOUNT
    allocation_formula  TEXT,                                     -- 分摊公式（JSON格式）
    
    -- 适用范围
    cost_type_ids       TEXT,                                     -- 适用费用类型ID列表（JSON）
    project_ids         TEXT,                                     -- 适用项目ID列表（JSON，空表示全部）
    
    -- 状态
    is_active           BOOLEAN DEFAULT 1,                       -- 是否启用
    effective_date      DATE,                                    -- 生效日期
    expiry_date         DATE,                                    -- 失效日期
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE rd_cost (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cost_no             VARCHAR(50) NOT NULL UNIQUE,              -- 费用编号
    
    -- 关联信息
    rd_project_id       INTEGER NOT NULL,                        -- 研发项目ID
    cost_type_id        INTEGER NOT NULL,                        -- 费用类型ID
    
    -- 费用信息
    cost_date           DATE NOT NULL,                           -- 费用发生日期
    cost_amount         DECIMAL(12,2) NOT NULL,                  -- 费用金额
    cost_description    TEXT,                                    -- 费用说明
    
    -- 人工费用相关（如果费用类型是人工）
    user_id             INTEGER,                                 -- 人员ID（人工费用）
    hours               DECIMAL(10,2),                           -- 工时（人工费用）
    hourly_rate         DECIMAL(10,2),                           -- 时薪（人工费用）
    
    -- 材料费用相关（如果费用类型是材料）
    material_id         INTEGER,                                 -- 物料ID（材料费用）
    material_qty        DECIMAL(10,4),                           -- 物料数量（材料费用）
    material_price       DECIMAL(10,2),                          -- 物料单价（材料费用）
    
    -- 折旧费用相关（如果费用类型是折旧）
    equipment_id        INTEGER,                                 -- 设备ID（折旧费用）
    depreciation_period VARCHAR(20),                             -- 折旧期间（折旧费用）
    
    -- 来源信息
    source_type         VARCHAR(20),                             -- 来源类型：MANUAL/CALCULATED/ALLOCATED
    source_id           INTEGER,                                 -- 来源ID（如关联的项目成本ID）
    
    -- 分摊信息
    is_allocated        BOOLEAN DEFAULT 0,                       -- 是否分摊费用
    allocation_rule_id  INTEGER,                                 -- 分摊规则ID
    allocation_rate     DECIMAL(5,2),                            -- 分摊比例(%)
    
    -- 加计扣除
    deductible_amount   DECIMAL(12,2),                           -- 可加计扣除金额
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',            -- 状态：DRAFT/APPROVED/CANCELLED
    approved_by         INTEGER,                                 -- 审批人ID
    approved_at         DATETIME,                                -- 审批时间
    
    -- 备注
    remark              TEXT,                                    -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rd_project_id) REFERENCES rd_project(id),
    FOREIGN KEY (cost_type_id) REFERENCES rd_cost_type(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (allocation_rule_id) REFERENCES rd_cost_allocation_rule(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE rd_report_record (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    report_no           VARCHAR(50) NOT NULL UNIQUE,             -- 报表编号
    report_type         VARCHAR(50) NOT NULL,                   -- 报表类型：AUXILIARY_LEDGER/DEDUCTION_DETAIL/HIGH_TECH等
    report_name         VARCHAR(200) NOT NULL,                  -- 报表名称
    
    -- 报表参数
    report_params       TEXT,                                    -- 报表参数（JSON格式）
    start_date          DATE,                                    -- 开始日期
    end_date            DATE,                                    -- 结束日期
    project_ids         TEXT,                                    -- 项目ID列表（JSON）
    
    -- 生成信息
    generated_by        INTEGER NOT NULL,                        -- 生成人ID
    generated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 生成时间
    file_path           VARCHAR(500),                           -- 文件路径
    file_size           INTEGER,                                 -- 文件大小（字节）
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'GENERATED',        -- 状态：GENERATED/DOWNLOADED/ARCHIVED
    
    -- 备注
    remark              TEXT,                                   -- 备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (generated_by) REFERENCES users(id)
);
CREATE TABLE technical_spec_requirements (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    document_id         INTEGER,                              -- 关联技术规格书文档

    -- 物料信息
    material_code       VARCHAR(50),                          -- 物料编码（可选）
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500) NOT NULL,                -- 规格型号要求
    brand               VARCHAR(100),                         -- 品牌要求
    model               VARCHAR(100),                         -- 型号要求

    -- 关键参数（JSON格式，用于智能匹配）
    key_parameters      TEXT,                                -- 关键参数：电压、电流、精度、温度范围等

    -- 要求级别
    requirement_level   VARCHAR(20) DEFAULT 'REQUIRED',       -- 要求级别：REQUIRED/OPTIONAL/STRICT

    -- 备注
    remark              TEXT,                                 -- 备注说明
    extracted_by        INTEGER,                              -- 提取人

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (extracted_by) REFERENCES users(id)
);
CREATE TABLE spec_match_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL,                     -- 项目ID
    spec_requirement_id INTEGER,                              -- 规格要求ID

    -- 匹配对象
    match_type          VARCHAR(20) NOT NULL,                  -- 匹配类型：BOM/PURCHASE_ORDER
    match_target_id     INTEGER NOT NULL,                     -- 匹配对象ID（BOM行ID或采购订单行ID）

    -- 匹配结果
    match_status        VARCHAR(20) NOT NULL,                  -- 匹配状态：MATCHED/MISMATCHED/UNKNOWN
    match_score         DECIMAL(5,2),                         -- 匹配度（0-100）

    -- 差异详情（JSON）
    differences         TEXT,                                -- 差异详情

    -- 预警
    alert_id            INTEGER,                              -- 关联预警ID

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (spec_requirement_id) REFERENCES technical_spec_requirements(id),
    FOREIGN KEY (alert_id) REFERENCES alert_records(id)
);
CREATE TABLE issue_statistics_snapshots (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date           DATE NOT NULL,                      -- 快照日期
    
    -- 总体统计
    total_issues            INTEGER DEFAULT 0,                  -- 问题总数
    
    -- 状态统计
    open_issues             INTEGER DEFAULT 0,                  -- 待处理问题数
    processing_issues       INTEGER DEFAULT 0,                  -- 处理中问题数
    resolved_issues          INTEGER DEFAULT 0,                  -- 已解决问题数
    closed_issues            INTEGER DEFAULT 0,                  -- 已关闭问题数
    cancelled_issues         INTEGER DEFAULT 0,                  -- 已取消问题数
    deferred_issues          INTEGER DEFAULT 0,                  -- 已延期问题数
    
    -- 严重程度统计
    critical_issues         INTEGER DEFAULT 0,                  -- 严重问题数
    major_issues            INTEGER DEFAULT 0,                  -- 重大问题数
    minor_issues            INTEGER DEFAULT 0,                  -- 轻微问题数
    
    -- 优先级统计
    urgent_issues           INTEGER DEFAULT 0,                  -- 紧急问题数
    high_priority_issues     INTEGER DEFAULT 0,                  -- 高优先级问题数
    medium_priority_issues  INTEGER DEFAULT 0,                  -- 中优先级问题数
    low_priority_issues      INTEGER DEFAULT 0,                  -- 低优先级问题数
    
    -- 类型统计
    defect_issues           INTEGER DEFAULT 0,                  -- 缺陷问题数
    risk_issues             INTEGER DEFAULT 0,                  -- 风险问题数
    blocker_issues          INTEGER DEFAULT 0,                  -- 阻塞问题数
    
    -- 特殊统计
    blocking_issues          INTEGER DEFAULT 0,                  -- 阻塞问题数（is_blocking=True）
    overdue_issues           INTEGER DEFAULT 0,                  -- 逾期问题数
    
    -- 分类统计
    project_issues          INTEGER DEFAULT 0,                  -- 项目问题数
    task_issues             INTEGER DEFAULT 0,                  -- 任务问题数
    acceptance_issues       INTEGER DEFAULT 0,                  -- 验收问题数
    
    -- 处理时间统计（小时）
    avg_response_time        NUMERIC(10, 2) DEFAULT 0,          -- 平均响应时间
    avg_resolve_time         NUMERIC(10, 2) DEFAULT 0,          -- 平均解决时间
    avg_verify_time          NUMERIC(10, 2) DEFAULT 0,          -- 平均验证时间
    
    -- 分布数据（JSON格式）
    status_distribution      TEXT,                               -- 状态分布(JSON)
    severity_distribution    TEXT,                               -- 严重程度分布(JSON)
    priority_distribution    TEXT,                               -- 优先级分布(JSON)
    category_distribution    TEXT,                               -- 分类分布(JSON)
    project_distribution     TEXT,                               -- 项目分布(JSON)
    
    -- 趋势数据
    new_issues_today         INTEGER DEFAULT 0,                  -- 今日新增问题数
    resolved_today           INTEGER DEFAULT 0,                  -- 今日解决问题数
    closed_today             INTEGER DEFAULT 0,                  -- 今日关闭问题数
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO issue_statistics_snapshots VALUES(1,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:42:39.570550','2026-01-30 15:42:39.570550');
INSERT INTO issue_statistics_snapshots VALUES(2,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:45:07.428966','2026-01-30 15:45:07.428967');
INSERT INTO issue_statistics_snapshots VALUES(3,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:47:37.935278','2026-01-30 15:47:37.935279');
INSERT INTO issue_statistics_snapshots VALUES(4,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:49:04.607781','2026-01-30 15:49:04.607781');
INSERT INTO issue_statistics_snapshots VALUES(5,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:49:15.118755','2026-01-30 15:49:15.118756');
INSERT INTO issue_statistics_snapshots VALUES(6,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:50:08.577825','2026-01-30 15:50:08.577826');
INSERT INTO issue_statistics_snapshots VALUES(7,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:51:05.779344','2026-01-30 15:51:05.779345');
INSERT INTO issue_statistics_snapshots VALUES(8,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:53:29.737764','2026-01-30 15:53:29.737765');
INSERT INTO issue_statistics_snapshots VALUES(9,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:54:11.575732','2026-01-30 15:54:11.575733');
INSERT INTO issue_statistics_snapshots VALUES(10,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:55:13.340750','2026-01-30 15:55:13.340751');
INSERT INTO issue_statistics_snapshots VALUES(11,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 15:58:26.520748','2026-01-30 15:58:26.520749');
INSERT INTO issue_statistics_snapshots VALUES(12,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:01:47.155517','2026-01-30 16:01:47.155518');
INSERT INTO issue_statistics_snapshots VALUES(13,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:01:56.794944','2026-01-30 16:01:56.794945');
INSERT INTO issue_statistics_snapshots VALUES(14,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:06:00.827193','2026-01-30 16:06:00.827193');
INSERT INTO issue_statistics_snapshots VALUES(15,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:09:16.986406','2026-01-30 16:09:16.986406');
INSERT INTO issue_statistics_snapshots VALUES(16,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:09:27.401825','2026-01-30 16:09:27.401825');
INSERT INTO issue_statistics_snapshots VALUES(17,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:10:13.912105','2026-01-30 16:10:13.912105');
INSERT INTO issue_statistics_snapshots VALUES(18,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 16:10:34.124384','2026-01-30 16:10:34.124385');
INSERT INTO issue_statistics_snapshots VALUES(19,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 19:43:02.160463','2026-01-30 19:43:02.160464');
INSERT INTO issue_statistics_snapshots VALUES(20,'2026-01-30',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'{}',NULL,NULL,NULL,NULL,0,0,0,'2026-01-30 19:53:49.444401','2026-01-30 19:53:49.444402');
CREATE TABLE issue_templates (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name            VARCHAR(100) NOT NULL,              -- 模板名称
    template_code            VARCHAR(50) NOT NULL UNIQUE,        -- 模板编码
    
    -- 模板分类
    category                VARCHAR(20) NOT NULL,                -- 问题分类
    issue_type              VARCHAR(20) NOT NULL,                -- 问题类型
    
    -- 默认值
    default_severity         VARCHAR(20),                         -- 默认严重程度
    default_priority         VARCHAR(20) DEFAULT 'MEDIUM',       -- 默认优先级
    default_impact_level     VARCHAR(20),                         -- 默认影响级别
    
    -- 模板内容
    title_template          VARCHAR(200) NOT NULL,              -- 标题模板（支持变量）
    description_template    TEXT,                                -- 描述模板（支持变量）
    solution_template       TEXT,                                -- 解决方案模板（支持变量）
    
    -- 默认字段
    default_tags            TEXT,                                -- 默认标签JSON数组
    default_impact_scope     TEXT,                                -- 默认影响范围
    default_is_blocking      BOOLEAN DEFAULT 0,                   -- 默认是否阻塞
    
    -- 使用统计
    usage_count             INTEGER DEFAULT 0,                    -- 使用次数
    last_used_at            DATETIME,                            -- 最后使用时间
    
    -- 状态
    is_active               BOOLEAN DEFAULT 1,                   -- 是否启用
    
    -- 备注
    remark                  TEXT,                                -- 备注说明
    
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE progress_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type VARCHAR(20) NOT NULL,
    report_date DATE NOT NULL,
    
    -- 关联信息（三选一或组合）
    project_id INTEGER,
    machine_id INTEGER,
    task_id INTEGER,
    
    -- 报告内容
    content TEXT NOT NULL,
    completed_work TEXT,
    planned_work TEXT,
    issues TEXT,
    next_plan TEXT,
    
    -- 创建人
    created_by INTEGER NOT NULL,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE project_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_no           VARCHAR(50) NOT NULL UNIQUE,              -- 复盘编号
    project_id          INTEGER NOT NULL,                         -- 项目ID
    project_code        VARCHAR(50) NOT NULL,                      -- 项目编号
    
    -- 复盘信息
    review_date         DATE NOT NULL,                             -- 复盘日期
    review_type         VARCHAR(20) DEFAULT 'POST_MORTEM',        -- 复盘类型：POST_MORTEM/MID_TERM/QUARTERLY
    
    -- 项目周期对比
    plan_duration       INTEGER,                                   -- 计划工期(天)
    actual_duration     INTEGER,                                   -- 实际工期(天)
    schedule_variance   INTEGER,                                   -- 进度偏差(天)
    
    -- 成本对比
    budget_amount       DECIMAL(12,2),                             -- 预算金额
    actual_cost         DECIMAL(12,2),                             -- 实际成本
    cost_variance       DECIMAL(12,2),                             -- 成本偏差
    
    -- 质量指标
    quality_issues      INTEGER DEFAULT 0,                         -- 质量问题数
    change_count        INTEGER DEFAULT 0,                         -- 变更次数
    customer_satisfaction INTEGER,                                  -- 客户满意度1-5
    
    -- 复盘内容
    success_factors     TEXT,                                       -- 成功因素
    problems            TEXT,                                       -- 问题与教训
    improvements        TEXT,                                       -- 改进建议
    best_practices      TEXT,                                       -- 最佳实践
    conclusion          TEXT,                                       -- 复盘结论
    
    -- 参与人
    reviewer_id         INTEGER NOT NULL,                          -- 复盘负责人ID
    reviewer_name       VARCHAR(50) NOT NULL,                       -- 复盘负责人
    participants        TEXT,                                       -- 参与人ID列表（JSON）
    participant_names   VARCHAR(500),                               -- 参与人姓名（逗号分隔）
    
    -- 附件
    attachment_ids      TEXT,                                       -- 附件ID列表（JSON）
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',              -- 状态：DRAFT/PUBLISHED/ARCHIVED
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE project_lessons (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 复盘报告ID
    project_id          INTEGER NOT NULL,                          -- 项目ID
    
    -- 经验教训信息
    lesson_type         VARCHAR(20) NOT NULL,                      -- 类型：SUCCESS/FAILURE
    title               VARCHAR(200) NOT NULL,                      -- 标题
    description         TEXT NOT NULL,                             -- 问题/经验描述
    
    -- 根因分析
    root_cause          TEXT,                                       -- 根本原因
    impact              TEXT,                                       -- 影响范围
    
    -- 改进措施
    improvement_action  TEXT,                                       -- 改进措施
    responsible_person  VARCHAR(50),                                -- 责任人
    due_date            DATE,                                       -- 完成日期
    
    -- 分类标签
    category            VARCHAR(50),                                -- 分类：进度/成本/质量/沟通/技术/管理
    tags                TEXT,                                       -- 标签列表（JSON）
    
    -- 优先级
    priority            VARCHAR(10) DEFAULT 'MEDIUM',             -- 优先级：LOW/MEDIUM/HIGH
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'OPEN',                -- 状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED
    resolved_date       DATE,                                       -- 解决日期
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE project_best_practices (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id                   INTEGER NOT NULL,                  -- 复盘报告ID
    project_id                  INTEGER NOT NULL,                  -- 项目ID
    
    -- 最佳实践信息
    title                       VARCHAR(200) NOT NULL,              -- 标题
    description                 TEXT NOT NULL,                      -- 实践描述
    context                     TEXT,                                -- 适用场景
    implementation              TEXT,                                -- 实施方法
    benefits                    TEXT,                                -- 带来的收益
    
    -- 分类标签
    category                    VARCHAR(50),                         -- 分类：流程/工具/技术/管理/沟通
    tags                        TEXT,                                -- 标签列表（JSON）
    
    -- 可复用性
    is_reusable                 BOOLEAN DEFAULT 1,                  -- 是否可复用
    applicable_project_types    TEXT,                                -- 适用项目类型列表（JSON）
    applicable_stages           TEXT,                                -- 适用阶段列表（JSON，S1-S9）
    
    -- 验证信息
    validation_status           VARCHAR(20) DEFAULT 'PENDING',     -- 验证状态：PENDING/VALIDATED/REJECTED
    validation_date             DATE,                               -- 验证日期
    validated_by                INTEGER,                             -- 验证人ID
    
    -- 复用统计
    reuse_count                 INTEGER DEFAULT 0,                  -- 复用次数
    last_reused_at              DATETIME,                           -- 最后复用时间
    
    -- 状态
    status                      VARCHAR(20) DEFAULT 'ACTIVE',       -- 状态：ACTIVE/ARCHIVED
    
    created_at                  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at                  DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES project_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (validated_by) REFERENCES users(id)
);
CREATE TABLE customer_communications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    communication_no VARCHAR(50) UNIQUE NOT NULL,
    communication_type VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_contact VARCHAR(50),
    customer_phone VARCHAR(20),
    customer_email VARCHAR(100),
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    communication_date DATE NOT NULL,
    communication_time VARCHAR(10),
    duration INTEGER,
    location VARCHAR(200),
    topic VARCHAR(50) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    follow_up_required BOOLEAN DEFAULT 0,
    follow_up_task TEXT,
    follow_up_due_date DATE,
    follow_up_status VARCHAR(20),
    tags TEXT,  -- JSON format
    importance VARCHAR(10) DEFAULT '中',
    created_by INTEGER NOT NULL,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE customer_satisfactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_no VARCHAR(50) UNIQUE NOT NULL,
    survey_type VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_contact VARCHAR(50),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(20),
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    survey_date DATE NOT NULL,
    send_date DATE,
    send_method VARCHAR(20),
    deadline DATE,
    status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
    response_date DATE,
    overall_score NUMERIC(3, 1),
    scores TEXT,  -- JSON format
    feedback TEXT,
    suggestions TEXT,
    created_by INTEGER NOT NULL,
    created_by_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_no VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,  -- JSON format
    is_faq BOOLEAN DEFAULT 0,
    is_featured BOOLEAN DEFAULT 0,
    status VARCHAR(20) DEFAULT 'DRAFT',
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    author_id INTEGER NOT NULL,
    author_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, file_path VARCHAR(500), file_name VARCHAR(200), file_size INTEGER, file_type VARCHAR(100), download_count INTEGER DEFAULT 0, allow_download BOOLEAN DEFAULT 1, adopt_count INTEGER DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES users(id)
);
CREATE TABLE mat_work_order_bom (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id       INTEGER NOT NULL,                     -- 工单ID
    work_order_no       VARCHAR(32),                          -- 工单号
    project_id          INTEGER,                              -- 项目ID
    
    -- 物料信息
    material_id         INTEGER,                              -- 物料ID
    material_code       VARCHAR(50) NOT NULL,                 -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(200),                         -- 规格型号
    unit                VARCHAR(20) DEFAULT '件',            -- 单位
    
    -- 数量信息
    bom_qty             DECIMAL(12,4) NOT NULL,               -- BOM用量
    required_qty        DECIMAL(12,4) NOT NULL,               -- 需求数量
    required_date       DATE NOT NULL,                        -- 需求日期
    
    -- 物料类型
    material_type       VARCHAR(20) DEFAULT 'purchase',      -- purchase/make/outsource
    lead_time           INTEGER DEFAULT 0,                    -- 采购提前期(天)
    is_key_material     BOOLEAN DEFAULT 0,                    -- 是否关键物料
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE mat_material_requirement (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_no      VARCHAR(32) NOT NULL UNIQUE,          -- 需求编号
    
    -- 来源信息
    source_type         VARCHAR(20) NOT NULL,                 -- work_order/project/manual
    work_order_id       INTEGER,                              -- 工单ID
    project_id          INTEGER,                              -- 项目ID
    
    -- 物料信息
    material_id         INTEGER,                              -- 物料ID
    material_code       VARCHAR(50) NOT NULL,                 -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(200),                         -- 规格型号
    unit                VARCHAR(20),                          -- 单位
    
    -- 数量信息
    required_qty        DECIMAL(12,4) NOT NULL,               -- 需求数量
    stock_qty           DECIMAL(12,4) DEFAULT 0,              -- 库存可用
    allocated_qty       DECIMAL(12,4) DEFAULT 0,              -- 已分配
    in_transit_qty      DECIMAL(12,4) DEFAULT 0,              -- 在途数量
    shortage_qty        DECIMAL(12,4) DEFAULT 0,              -- 缺料数量
    required_date       DATE NOT NULL,                        -- 需求日期
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'pending',        -- pending/partial/fulfilled/cancelled
    fulfill_method      VARCHAR(20),                          -- stock/purchase/substitute/transfer
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);
CREATE TABLE mat_kit_check (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    check_no            VARCHAR(32) NOT NULL UNIQUE,          -- 检查编号
    
    -- 检查对象
    check_type          VARCHAR(20) NOT NULL,                 -- work_order/project/batch
    work_order_id       INTEGER,                              -- 工单ID
    project_id          INTEGER,                              -- 项目ID
    
    -- 检查结果
    total_items         INTEGER DEFAULT 0,                    -- 物料总项
    fulfilled_items     INTEGER DEFAULT 0,                    -- 已齐套项
    shortage_items      INTEGER DEFAULT 0,                    -- 缺料项
    in_transit_items    INTEGER DEFAULT 0,                    -- 在途项
    kit_rate            DECIMAL(5,2) DEFAULT 0,               -- 齐套率(%)
    kit_status          VARCHAR(20) DEFAULT 'shortage',       -- complete/partial/shortage
    shortage_summary    TEXT,                                 -- 缺料汇总JSON
    
    -- 检查信息
    check_time          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 检查时间
    check_method        VARCHAR(20) DEFAULT 'auto',            -- auto/manual
    checked_by          INTEGER,                              -- 检查人ID
    
    -- 开工确认
    can_start           BOOLEAN DEFAULT 0,                   -- 是否可开工
    start_confirmed     BOOLEAN DEFAULT 0,                    -- 已确认开工
    confirm_time        DATETIME,                              -- 确认时间
    confirmed_by        INTEGER,                              -- 确认人ID
    confirm_remark      TEXT,                                  -- 确认备注
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (checked_by) REFERENCES users(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id)
);
CREATE TABLE mat_alert_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id            INTEGER NOT NULL,                     -- 预警ID
    
    -- 操作信息
    action_type         VARCHAR(20) NOT NULL,                 -- create/handle/update/escalate/resolve/close
    action_description  TEXT,                                 -- 操作描述
    
    -- 操作人
    operator_id         INTEGER,                              -- 操作人ID
    operator_name       VARCHAR(50),                          -- 操作人姓名
    action_time         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- 操作时间
    
    -- 操作前后状态
    before_status       VARCHAR(20),                          -- 操作前状态
    after_status        VARCHAR(20),                           -- 操作后状态
    before_level        VARCHAR(20),                           -- 操作前级别
    after_level         VARCHAR(20),                           -- 操作后级别
    
    -- 扩展数据
    extra_data          TEXT,                                 -- 扩展数据JSON
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (operator_id) REFERENCES users(id)
);
CREATE TABLE mat_shortage_daily_report (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date         DATE NOT NULL UNIQUE,                 -- 报告日期
    
    -- 预警统计
    new_alerts          INTEGER DEFAULT 0,                    -- 新增预警数
    resolved_alerts     INTEGER DEFAULT 0,                    -- 已解决预警数
    pending_alerts      INTEGER DEFAULT 0,                    -- 待处理预警数
    overdue_alerts      INTEGER DEFAULT 0,                    -- 逾期预警数
    level1_count        INTEGER DEFAULT 0,                    -- 一级预警数
    level2_count        INTEGER DEFAULT 0,                    -- 二级预警数
    level3_count        INTEGER DEFAULT 0,                    -- 三级预警数
    level4_count        INTEGER DEFAULT 0,                    -- 四级预警数
    
    -- 上报统计
    new_reports         INTEGER DEFAULT 0,                    -- 新增上报数
    resolved_reports    INTEGER DEFAULT 0,                    -- 已解决上报数
    
    -- 工单统计
    total_work_orders   INTEGER DEFAULT 0,                    -- 总工单数
    kit_complete_count  INTEGER DEFAULT 0,                    -- 齐套完成工单数
    kit_rate            DECIMAL(5,2) DEFAULT 0,               -- 平均齐套率
    
    -- 到货统计
    expected_arrivals   INTEGER DEFAULT 0,                    -- 预期到货数
    actual_arrivals     INTEGER DEFAULT 0,                    -- 实际到货数
    delayed_arrivals    INTEGER DEFAULT 0,                    -- 延迟到货数
    on_time_rate        DECIMAL(5,2) DEFAULT 0,              -- 准时到货率
    
    -- 响应时效
    avg_response_minutes INTEGER DEFAULT 0,                   -- 平均响应时间(分钟)
    avg_resolve_hours   DECIMAL(5,2) DEFAULT 0,              -- 平均解决时间(小时)
    
    -- 停工统计
    stoppage_count      INTEGER DEFAULT 0,                    -- 停工次数
    stoppage_hours      DECIMAL(8,2) DEFAULT 0,              -- 停工时长(小时)
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE mat_shortage_alert (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_no            VARCHAR(32) NOT NULL UNIQUE,               -- 预警编号
    work_order_id       INTEGER,                                  -- 工单ID
    work_order_no       VARCHAR(32),                               -- 工单号
    project_id          INTEGER,                                  -- 项目ID
    project_name        VARCHAR(200),                              -- 项目名称
    
    -- 物料信息
    material_id         INTEGER,                                  -- 物料ID
    material_code        VARCHAR(50) NOT NULL,                     -- 物料编码
    material_name        VARCHAR(200) NOT NULL,                     -- 物料名称
    specification        VARCHAR(200),                              -- 规格型号
    shortage_qty         DECIMAL(12,4) NOT NULL,                   -- 缺料数量
    shortage_value       DECIMAL(12,2),                            -- 缺料金额
    required_date        DATE NOT NULL,                            -- 需求日期
    days_to_required     INTEGER,                                  -- 距离需求日期天数
    
    -- 预警级别: level1=提醒, level2=警告, level3=紧急, level4=严重
    alert_level          VARCHAR(20) DEFAULT 'level1',              -- 预警级别
    
    -- 影响评估
    impact_type          VARCHAR(20) DEFAULT 'none',               -- 影响类型：none/delay/stop/delivery
    impact_description   TEXT,                                     -- 影响描述
    affected_process     VARCHAR(100),                              -- 受影响工序
    estimated_delay_days INTEGER DEFAULT 0,                        -- 预计延迟天数
    
    -- 通知信息
    notify_time          DATETIME,                                 -- 通知时间
    notify_count         INTEGER DEFAULT 0,                        -- 通知次数
    notified_users       TEXT,                                     -- 已通知用户列表（JSON）
    response_deadline    DATETIME,                                 -- 响应时限
    is_overdue           BOOLEAN DEFAULT 0,                        -- 是否逾期
    
    -- 处理状态
    status               VARCHAR(20) DEFAULT 'pending',            -- 状态：pending/handling/resolved/escalated/closed
    
    -- 处理人信息
    handler_id           INTEGER,                                  -- 处理人ID
    handler_name         VARCHAR(50),                               -- 处理人姓名
    handle_start_time    DATETIME,                                 -- 开始处理时间
    handle_plan          TEXT,                                     -- 处理方案
    handle_method        VARCHAR(20),                               -- 处理方式
    expected_resolve_time DATETIME,                                -- 预计解决时间
    
    -- 解决信息
    resolve_time         DATETIME,                                 -- 实际解决时间
    resolve_method       VARCHAR(50),                               -- 解决方式
    resolve_description  TEXT,                                     -- 解决说明
    actual_delay_days    INTEGER DEFAULT 0,                         -- 实际延迟天数
    
    -- 升级信息
    escalated            BOOLEAN DEFAULT 0,                        -- 是否已升级
    escalate_time        DATETIME,                                 -- 升级时间
    escalate_to          INTEGER,                                  -- 升级给谁（用户ID）
    escalate_reason      TEXT,                                     -- 升级原因
    
    -- 关联单据
    related_po_no        VARCHAR(50),                               -- 关联采购订单号
    related_transfer_no   VARCHAR(50),                               -- 关联调拨单号
    related_substitute_no VARCHAR(50),                              -- 关联替代单号
    
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_order_id) REFERENCES work_order(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (handler_id) REFERENCES users(id),
    FOREIGN KEY (escalate_to) REFERENCES users(id)
);
CREATE TABLE invoice_requests (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    request_no          VARCHAR(50) NOT NULL UNIQUE,
    contract_id         INTEGER NOT NULL,
    project_id          INTEGER,
    project_name        VARCHAR(200),
    customer_id         INTEGER NOT NULL,
    customer_name       VARCHAR(200),
    payment_plan_id     INTEGER,
    invoice_type        VARCHAR(20),
    invoice_title       VARCHAR(200),
    tax_rate            NUMERIC(5, 2),
    amount              NUMERIC(14, 2) NOT NULL,
    tax_amount          NUMERIC(14, 2),
    total_amount        NUMERIC(14, 2),
    currency            VARCHAR(10) DEFAULT 'CNY',
    expected_issue_date DATE,
    expected_payment_date DATE,
    reason              TEXT,
    attachments         TEXT,
    remark              TEXT,
    status              VARCHAR(20) DEFAULT 'PENDING',
    approval_comment    TEXT,
    requested_by        INTEGER NOT NULL,
    requested_by_name   VARCHAR(50),
    approved_by         INTEGER,
    approved_at         DATETIME,
    invoice_id          INTEGER,
    receipt_status      VARCHAR(20) DEFAULT 'UNPAID',
    receipt_updated_at  DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (payment_plan_id) REFERENCES project_payment_plans(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);
CREATE TABLE customer_supplier_registrations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_no     VARCHAR(100) NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL,
    customer_name       VARCHAR(200),
    platform_name       VARCHAR(100) NOT NULL,
    platform_url        VARCHAR(500),
    registration_status VARCHAR(20) DEFAULT 'PENDING',
    application_date    DATE,
    approved_date       DATE,
    expire_date         DATE,
    contact_person      VARCHAR(50),
    contact_phone       VARCHAR(30),
    contact_email       VARCHAR(100),
    required_docs       TEXT,
    reviewer_id         INTEGER,
    review_comment      TEXT,
    external_sync_status VARCHAR(20) DEFAULT 'pending',
    last_sync_at        DATETIME,
    sync_message        TEXT,
    remark              TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE task_approval_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    submitted_by INTEGER NOT NULL,
    submitted_at DATETIME NOT NULL,
    submit_note TEXT,

    approver_id INTEGER,
    approval_status VARCHAR(20) DEFAULT 'PENDING',
    approved_at DATETIME,
    approval_note TEXT,
    rejection_reason TEXT,

    task_details JSON,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);
CREATE TABLE task_completion_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,

    proof_type VARCHAR(50) NOT NULL,
    file_category VARCHAR(50),

    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    description TEXT,

    uploaded_by INTEGER NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES task_unified(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
CREATE TABLE monthly_work_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    period VARCHAR(7) NOT NULL, -- 格式: YYYY-MM

    -- 工作总结内容（必填）
    work_content TEXT NOT NULL,
    self_evaluation TEXT NOT NULL,

    -- 工作总结内容（选填）
    highlights TEXT,
    problems TEXT,
    next_month_plan TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT/SUBMITTED/EVALUATING/COMPLETED

    -- 提交时间
    submit_date DATETIME,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES users(id),

    -- 唯一约束
    UNIQUE (employee_id, period)
);
CREATE TABLE performance_evaluation_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_id INTEGER NOT NULL,
    evaluator_id INTEGER NOT NULL,
    evaluator_type VARCHAR(20) NOT NULL, -- DEPT_MANAGER/PROJECT_MANAGER

    -- 项目信息（仅项目经理评价时使用）
    project_id INTEGER,
    project_weight INTEGER, -- 项目权重 (多项目时使用)

    -- 评价内容
    score INTEGER NOT NULL CHECK (score >= 60 AND score <= 100),
    comment TEXT NOT NULL,

    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING/COMPLETED
    evaluated_at DATETIME,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, qualification_level_id INTEGER REFERENCES qualification_level(id), qualification_score TEXT,

    -- 外键约束
    FOREIGN KEY (summary_id) REFERENCES monthly_work_summary(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE evaluation_weight_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_manager_weight INTEGER NOT NULL DEFAULT 50 CHECK (dept_manager_weight >= 0 AND dept_manager_weight <= 100),
    project_manager_weight INTEGER NOT NULL DEFAULT 50 CHECK (project_manager_weight >= 0 AND project_manager_weight <= 100),
    effective_date DATE NOT NULL,
    operator_id INTEGER NOT NULL,
    reason TEXT,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束
    FOREIGN KEY (operator_id) REFERENCES users(id),

    -- 权重总和必须为100（由应用层验证）
    CHECK (dept_manager_weight + project_manager_weight = 100)
);
INSERT INTO evaluation_weight_config VALUES(1,50,50,'2026-01-28',1,'系统初始化默认配置','2026-01-28 06:47:10');
CREATE TABLE qualification_level (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_code VARCHAR(20) UNIQUE NOT NULL,  -- ASSISTANT/JUNIOR/MIDDLE/SENIOR/EXPERT
    level_name VARCHAR(50) NOT NULL,        -- 助理级/初级/中级/高级/专家级
    level_order INTEGER NOT NULL,           -- 排序顺序
    role_type VARCHAR(50),                  -- 适用角色类型
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE position_competency_model (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_type VARCHAR(50) NOT NULL,    -- SALES/ENGINEER/CUSTOMER_SERVICE/WORKER
    position_subtype VARCHAR(50),            -- 子类型 (ME/EE/SW/TE等)
    level_id INTEGER NOT NULL,
    competency_dimensions TEXT NOT NULL,    -- 能力维度要求 (JSON格式)
    is_active BOOLEAN DEFAULT 1,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (level_id) REFERENCES qualification_level(id)
);
CREATE TABLE employee_qualification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    position_type VARCHAR(50) NOT NULL,
    current_level_id INTEGER NOT NULL,
    
    -- 认证信息
    certified_date DATE,
    certifier_id INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/APPROVED/EXPIRED/REVOKED
    
    -- 评估详情 (JSON格式)
    assessment_details TEXT,
    
    -- 有效期
    valid_until DATE,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (current_level_id) REFERENCES qualification_level(id),
    FOREIGN KEY (certifier_id) REFERENCES users(id)
);
CREATE TABLE qualification_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    qualification_id INTEGER,
    
    -- 评估信息
    assessment_period VARCHAR(20),         -- 2024-Q1
    assessment_type VARCHAR(20) NOT NULL,   -- INITIAL/PROMOTION/ANNUAL/REASSESSMENT
    
    -- 各维度得分 (JSON格式)
    scores TEXT,
    
    total_score DECIMAL(5,2),
    result VARCHAR(20),                     -- PASS/FAIL/PARTIAL
    
    -- 评估人信息
    assessor_id INTEGER,
    comments TEXT,
    assessed_at DATETIME,
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (qualification_id) REFERENCES employee_qualification(id),
    FOREIGN KEY (assessor_id) REFERENCES users(id)
);
CREATE TABLE cpq_rule_sets (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           TEXT NOT NULL UNIQUE,
    rule_name           TEXT NOT NULL,
    description         TEXT,
    status              TEXT DEFAULT 'ACTIVE',
    base_price          REAL DEFAULT 0,
    currency            TEXT DEFAULT 'CNY',
    config_schema       TEXT,
    pricing_matrix      TEXT,
    approval_threshold  TEXT,
    visibility_scope    TEXT DEFAULT 'ALL',
    is_default          INTEGER DEFAULT 0,
    owner_role          TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE quote_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       TEXT NOT NULL UNIQUE,
    template_name       TEXT NOT NULL,
    category            TEXT,
    description         TEXT,
    status              TEXT DEFAULT 'DRAFT',
    visibility_scope    TEXT DEFAULT 'TEAM',
    is_default          INTEGER DEFAULT 0,
    current_version_id  INTEGER,
    owner_id            INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE quote_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,
    version_no          TEXT NOT NULL,
    status              TEXT DEFAULT 'DRAFT',
    sections            TEXT,
    pricing_rules       TEXT,
    config_schema       TEXT,
    discount_rules      TEXT,
    release_notes       TEXT,
    rule_set_id         INTEGER,
    created_by          INTEGER,
    published_by        INTEGER,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES quote_templates(id),
    FOREIGN KEY (rule_set_id) REFERENCES cpq_rule_sets(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);
CREATE TABLE contract_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       TEXT NOT NULL UNIQUE,
    template_name       TEXT NOT NULL,
    contract_type       TEXT,
    description         TEXT,
    status              TEXT DEFAULT 'DRAFT',
    visibility_scope    TEXT DEFAULT 'TEAM',
    is_default          INTEGER DEFAULT 0,
    current_version_id  INTEGER,
    owner_id            INTEGER,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
CREATE TABLE contract_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,
    version_no          TEXT NOT NULL,
    status              TEXT DEFAULT 'DRAFT',
    clause_sections     TEXT,
    clause_library      TEXT,
    attachment_refs     TEXT,
    approval_flow       TEXT,
    release_notes       TEXT,
    created_by          INTEGER,
    published_by        INTEGER,
    published_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES contract_templates(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);
CREATE TABLE project_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,              -- 模板编号
    template_name       VARCHAR(200) NOT NULL,                    -- 模板名称
    template_type       VARCHAR(20) DEFAULT 'STANDARD',           -- 模板类型：STANDARD/CUSTOM
    description         TEXT,                                     -- 模板描述
    stages_config       TEXT,                                     -- 阶段配置JSON
    milestones_config   TEXT,                                     -- 里程碑配置JSON
    default_members     TEXT,                                     -- 默认成员配置JSON
    is_active           INTEGER DEFAULT 1,                        -- 是否启用
    created_by          INTEGER,                                  -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP, current_version_id INTEGER,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE alert_subscriptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,                     -- 用户ID
    alert_type          VARCHAR(50),                          -- 预警类型（空表示全部）
    project_id          INTEGER,                              -- 项目ID（空表示全部）
    
    -- 订阅配置
    min_level           VARCHAR(20) DEFAULT 'WARNING',       -- 最低接收级别
    notify_channels     TEXT,                                 -- 通知渠道JSON: ["SYSTEM","EMAIL","WECHAT"]
    
    -- 免打扰时段
    quiet_start         VARCHAR(10),                         -- 免打扰开始时间（HH:mm格式）
    quiet_end           VARCHAR(10),                          -- 免打扰结束时间（HH:mm格式）
    
    -- 状态
    is_active           BOOLEAN DEFAULT 1,                   -- 是否启用
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE mes_assembly_stage (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_code          VARCHAR(20) NOT NULL UNIQUE,          -- 阶段编码: FRAME/MECH/ELECTRIC/WIRING/DEBUG/COSMETIC
    stage_name          VARCHAR(50) NOT NULL,                 -- 阶段名称
    stage_order         INTEGER NOT NULL,                     -- 阶段顺序(1-6)
    description         TEXT,                                 -- 阶段描述
    default_duration    INTEGER DEFAULT 0,                    -- 默认工期(小时)
    color_code          VARCHAR(20),                          -- 显示颜色
    icon                VARCHAR(50),                          -- 图标
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO mes_assembly_stage VALUES(1,'FRAME','框架装配',1,'铝型材框架搭建、钣金底座组装、立柱安装',24,'#3B82F6','Box',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_stage VALUES(2,'MECH','机械模组',2,'直线模组、气缸、电机、导轨滑块、夹具安装',40,'#10B981','Cog',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_stage VALUES(3,'ELECTRIC','电气安装',3,'PLC、伺服驱动、传感器、HMI、电源安装接线',32,'#F59E0B','Zap',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_stage VALUES(4,'WIRING','线路整理',4,'线槽安装、线缆整理、标签粘贴、端子接线',16,'#EF4444','Cable',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_stage VALUES(5,'DEBUG','调试准备',5,'工装治具准备、测试产品准备、程序调试',24,'#8B5CF6','Bug',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_stage VALUES(6,'COSMETIC','外观完善',6,'铭牌、盖板、安全防护、亚克力板安装',8,'#6B7280','Sparkles',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE mes_assembly_template (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code       VARCHAR(50) NOT NULL UNIQUE,          -- 模板编码
    template_name       VARCHAR(200) NOT NULL,                -- 模板名称
    equipment_type      VARCHAR(50) NOT NULL,                 -- 设备类型: ICT/FCT/EOL/AGING/VISION/ASSEMBLY
    description         TEXT,                                 -- 模板描述
    stage_config        TEXT,                                 -- 阶段配置JSON
    is_default          BOOLEAN DEFAULT 0,                    -- 是否默认模板
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用
    created_by          INTEGER,                              -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
INSERT INTO mes_assembly_template VALUES(1,'TPL_TEST_STD','测试设备标准模板','TEST','ICT/FCT/EOL等测试设备的标准装配流程','[{"stage":"FRAME","duration":24,"blocking_categories":["铝型材","钣金件","连接件"]},{"stage":"MECH","duration":40,"blocking_categories":["直线模组","气缸","导轨","电机"]},{"stage":"ELECTRIC","duration":32,"blocking_categories":["PLC","伺服","传感器","电源"]},{"stage":"WIRING","duration":16,"blocking_categories":["主线缆"]},{"stage":"DEBUG","duration":24,"blocking_categories":["工装治具"]},{"stage":"COSMETIC","duration":8,"blocking_categories":[]}]',1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_assembly_template VALUES(2,'TPL_ASSEMBLY_LINE','产线设备模板','ASSEMBLY','自动化组装线体的装配流程','[{"stage":"FRAME","duration":56,"blocking_categories":["型材","钣金","输送机框架"]},{"stage":"MECH","duration":80,"blocking_categories":["皮带","滚筒","电机","张紧装置"]},{"stage":"ELECTRIC","duration":56,"blocking_categories":["总控PLC","分站IO","伺服系统"]},{"stage":"WIRING","duration":24,"blocking_categories":["主干线缆"]},{"stage":"DEBUG","duration":40,"blocking_categories":[]},{"stage":"COSMETIC","duration":16,"blocking_categories":[]}]',0,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE mes_category_stage_mapping (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id         INTEGER,                              -- 物料分类ID(可选)
    category_code       VARCHAR(50) NOT NULL,                 -- 物料分类编码/关键词
    category_name       VARCHAR(100),                         -- 分类名称
    stage_code          VARCHAR(20) NOT NULL,                 -- 默认装配阶段
    priority            INTEGER DEFAULT 50,                   -- 优先级(1-100, 越高越优先匹配)
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞性物料
    can_postpone        BOOLEAN DEFAULT 1,                    -- 是否可后补
    importance_level    VARCHAR(20) DEFAULT 'NORMAL',         -- 重要程度: CRITICAL/HIGH/NORMAL/LOW
    lead_time_buffer    INTEGER DEFAULT 0,                    -- 提前期缓冲(天)
    keywords            TEXT,                                 -- 匹配关键词(JSON数组)
    remark              TEXT,                                 -- 备注
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用
    created_by          INTEGER,                              -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES material_categories(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
INSERT INTO mes_category_stage_mapping VALUES(1,NULL,'ALU_PROFILE','铝型材','FRAME',50,1,0,'CRITICAL',0,'["铝型材","4040","4080","型材","框架"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(2,NULL,'SHEET_METAL','钣金件','FRAME',50,1,0,'CRITICAL',0,'["钣金","底座","立板","安装板"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(3,NULL,'FRAME_CONN','框架连接件','FRAME',50,1,0,'HIGH',0,'["角码","连接板","角件"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(4,NULL,'CASTER','脚轮地脚','FRAME',50,0,1,'LOW',0,'["脚轮","万向轮","调节脚","地脚"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(5,NULL,'LINEAR_MODULE','直线模组','MECH',50,1,0,'CRITICAL',0,'["模组","直线模组","THK","上银","滑台"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(6,NULL,'CYLINDER','气缸','MECH',50,1,0,'CRITICAL',0,'["气缸","SMC","亚德客","CKD"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(7,NULL,'MOTOR','电机','MECH',50,1,0,'CRITICAL',0,'["电机","步进","减速机"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(8,NULL,'GUIDE_RAIL','导轨滑块','MECH',50,1,0,'CRITICAL',0,'["导轨","滑块","直线导轨"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(9,NULL,'PNEUMATIC','气动元件','MECH',50,1,0,'HIGH',0,'["气管","接头","电磁阀","气动"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(10,NULL,'FASTENER','紧固件','MECH',50,0,1,'NORMAL',0,'["螺丝","螺母","螺栓","垫圈"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(11,NULL,'PLC','PLC控制器','ELECTRIC',50,1,0,'CRITICAL',0,'["PLC","三菱","西门子","欧姆龙","控制器"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(12,NULL,'SERVO','伺服系统','ELECTRIC',50,1,0,'CRITICAL',0,'["伺服","驱动器","安川","松下","台达"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(13,NULL,'SENSOR','传感器','ELECTRIC',50,1,0,'CRITICAL',0,'["传感器","光电","接近","基恩士","欧姆龙"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(14,NULL,'HMI','触摸屏','ELECTRIC',50,1,0,'HIGH',0,'["触摸屏","HMI","威纶通","显示屏"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(15,NULL,'POWER','电源','ELECTRIC',50,1,0,'HIGH',0,'["电源","开关电源","稳压","明纬"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(16,NULL,'RELAY','继电器','ELECTRIC',50,0,1,'NORMAL',0,'["继电器","固态继电器","中间继电器"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(17,NULL,'WIRE_DUCT','线槽','WIRING',50,0,1,'NORMAL',0,'["线槽","PVC线槽","线槽盖"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(18,NULL,'CABLE','线缆','WIRING',50,1,0,'HIGH',0,'["电缆","线缆","电线","屏蔽线"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(19,NULL,'TERMINAL','端子','WIRING',50,0,1,'NORMAL',0,'["端子","接线端子","端子排"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(20,NULL,'LABEL','标签扎带','WIRING',50,0,1,'LOW',0,'["扎带","标签","号码管","标识"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(21,NULL,'FIXTURE','工装治具','DEBUG',50,1,0,'HIGH',0,'["工装","治具","夹具","定位"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(22,NULL,'TEST_SAMPLE','测试样品','DEBUG',50,0,1,'NORMAL',0,'["样品","测试品","产品"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(23,NULL,'NAMEPLATE','铭牌标识','COSMETIC',50,0,1,'LOW',0,'["铭牌","标牌","警示标","标识牌"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_category_stage_mapping VALUES(24,NULL,'COVER','盖板防护','COSMETIC',50,0,1,'LOW',0,'["盖板","亚克力","防护罩","安全门"]',NULL,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE bom_item_assembly_attrs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_item_id         INTEGER NOT NULL UNIQUE,              -- BOM明细ID
    bom_id              INTEGER NOT NULL,                     -- BOM表头ID

    -- 装配阶段
    assembly_stage      VARCHAR(20) NOT NULL,                 -- 装配阶段: FRAME/MECH/ELECTRIC/WIRING/DEBUG/COSMETIC
    stage_order         INTEGER DEFAULT 0,                    -- 阶段内排序

    -- 重要程度
    importance_level    VARCHAR(20) DEFAULT 'NORMAL',         -- 重要程度: CRITICAL/HIGH/NORMAL/LOW
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞性(缺料会阻塞当前阶段)
    can_postpone        BOOLEAN DEFAULT 1,                    -- 是否可后补(允许阶段开始后到货)

    -- 时间要求
    required_before_stage BOOLEAN DEFAULT 1,                  -- 是否需要在阶段开始前到货
    lead_time_days      INTEGER DEFAULT 0,                    -- 提前期要求(天)

    -- 替代信息
    has_substitute      BOOLEAN DEFAULT 0,                    -- 是否有替代料
    substitute_material_ids TEXT,                             -- 替代物料ID列表(JSON)

    -- 备注
    assembly_remark     TEXT,                                 -- 装配备注

    -- 设置来源
    setting_source      VARCHAR(20) DEFAULT 'AUTO',           -- 设置来源: AUTO/MANUAL/TEMPLATE

    -- 审核
    confirmed           BOOLEAN DEFAULT 0,                    -- 是否已确认
    confirmed_by        INTEGER,                              -- 确认人ID
    confirmed_at        DATETIME,                             -- 确认时间

    created_by          INTEGER,                              -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id) ON DELETE CASCADE,
    FOREIGN KEY (bom_id) REFERENCES bom_headers(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE mes_material_readiness (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    readiness_no        VARCHAR(50) NOT NULL UNIQUE,          -- 分析单号: KIT + YYMMDD + 序号

    -- 分析对象
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 机台ID(可选,不填则分析整个项目)
    bom_id              INTEGER,                              -- BOM ID

    -- 计划信息
    planned_start_date  DATE,                                 -- 计划开工日期
    target_stage        VARCHAR(20),                          -- 目标分析阶段(可选,不填则分析全部)

    -- 整体齐套率
    overall_kit_rate    DECIMAL(5,2) DEFAULT 0,               -- 整体齐套率(%)
    blocking_kit_rate   DECIMAL(5,2) DEFAULT 0,               -- 阻塞性齐套率(%)

    -- 分阶段齐套率(JSON格式)
    stage_kit_rates     TEXT,                                 -- 各阶段齐套率JSON

    -- 统计数据
    total_items         INTEGER DEFAULT 0,                    -- 物料总项数
    fulfilled_items     INTEGER DEFAULT 0,                    -- 已齐套项数
    shortage_items      INTEGER DEFAULT 0,                    -- 缺料项数
    in_transit_items    INTEGER DEFAULT 0,                    -- 在途项数

    blocking_total      INTEGER DEFAULT 0,                    -- 阻塞性物料总数
    blocking_fulfilled  INTEGER DEFAULT 0,                    -- 阻塞性已齐套数

    -- 金额统计
    total_amount        DECIMAL(14,2) DEFAULT 0,              -- 物料总金额
    shortage_amount     DECIMAL(14,2) DEFAULT 0,              -- 缺料金额

    -- 分析结果
    can_start           BOOLEAN DEFAULT 0,                    -- 是否可开工(框架阶段100%齐套)
    current_workable_stage VARCHAR(20),                       -- 当前可进行到的阶段
    first_blocked_stage VARCHAR(20),                          -- 首个阻塞阶段
    estimated_ready_date DATE,                                -- 预计完全齐套日期

    -- 分析信息
    analysis_time       DATETIME NOT NULL,                    -- 分析时间
    analysis_type       VARCHAR(20) DEFAULT 'AUTO',           -- 分析类型: AUTO/MANUAL/SCHEDULED
    analyzed_by         INTEGER,                              -- 分析人ID

    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 状态: DRAFT/CONFIRMED/EXPIRED
    confirmed_by        INTEGER,                              -- 确认人ID
    confirmed_at        DATETIME,                             -- 确认时间
    expired_at          DATETIME,                             -- 过期时间

    remark              TEXT,                                 -- 备注
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (bom_id) REFERENCES bom_headers(id),
    FOREIGN KEY (analyzed_by) REFERENCES users(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id)
);
CREATE TABLE mes_shortage_detail (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    readiness_id        INTEGER NOT NULL,                     -- 齐套分析ID

    -- BOM信息
    bom_item_id         INTEGER NOT NULL,                     -- BOM明细ID

    -- 物料信息
    material_id         INTEGER,                              -- 物料ID
    material_code       VARCHAR(50) NOT NULL,                 -- 物料编码
    material_name       VARCHAR(200) NOT NULL,                -- 物料名称
    specification       VARCHAR(500),                         -- 规格型号
    unit                VARCHAR(20),                          -- 单位

    -- 装配阶段属性
    assembly_stage      VARCHAR(20) NOT NULL,                 -- 所属装配阶段
    is_blocking         BOOLEAN DEFAULT 0,                    -- 是否阻塞性
    can_postpone        BOOLEAN DEFAULT 1,                    -- 是否可后补
    importance_level    VARCHAR(20) DEFAULT 'NORMAL',         -- 重要程度

    -- 数量信息
    required_qty        DECIMAL(12,4) NOT NULL,               -- 需求数量
    stock_qty           DECIMAL(12,4) DEFAULT 0,              -- 库存数量
    allocated_qty       DECIMAL(12,4) DEFAULT 0,              -- 已分配(其他项目)
    in_transit_qty      DECIMAL(12,4) DEFAULT 0,              -- 在途数量(已采购未到)
    available_qty       DECIMAL(12,4) DEFAULT 0,              -- 可用数量=库存-已分配+在途
    shortage_qty        DECIMAL(12,4) DEFAULT 0,              -- 缺料数量=需求-可用

    -- 金额
    unit_price          DECIMAL(12,4) DEFAULT 0,              -- 单价
    shortage_amount     DECIMAL(14,2) DEFAULT 0,              -- 缺料金额

    -- 时间
    required_date       DATE,                                 -- 需求日期(计划开工日期)
    expected_arrival    DATE,                                 -- 预计到货日期
    delay_days          INTEGER DEFAULT 0,                    -- 预计延误天数

    -- 采购信息
    purchase_order_id   INTEGER,                              -- 关联采购订单ID
    purchase_order_no   VARCHAR(50),                          -- 关联采购订单号
    supplier_id         INTEGER,                              -- 供应商ID
    supplier_name       VARCHAR(200),                         -- 供应商名称

    -- 状态
    shortage_status     VARCHAR(20) DEFAULT 'OPEN',           -- 缺料状态: OPEN/ORDERING/IN_TRANSIT/RESOLVED/CANCELLED

    -- 预警
    alert_level         VARCHAR(20),                          -- 预警级别: L1/L2/L3/L4
    alert_time          DATETIME,                             -- 预警时间

    -- 处理
    handler_id          INTEGER,                              -- 处理人ID
    handle_note         TEXT,                                 -- 处理说明
    handled_at          DATETIME,                             -- 处理时间

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (readiness_id) REFERENCES mes_material_readiness(id) ON DELETE CASCADE,
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (handler_id) REFERENCES users(id)
);
CREATE TABLE mes_shortage_alert_rule (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code           VARCHAR(50) NOT NULL UNIQUE,          -- 规则编码
    rule_name           VARCHAR(200) NOT NULL,                -- 规则名称

    -- 预警级别
    alert_level         VARCHAR(10) NOT NULL,                 -- L1停工/L2紧急/L3提前/L4常规

    -- 触发条件
    days_before_required INTEGER NOT NULL,                    -- 距需求日期天数(<=此值触发)
    only_blocking       BOOLEAN DEFAULT 0,                    -- 仅阻塞性物料
    importance_levels   TEXT,                                 -- 适用重要程度(JSON数组)
    min_shortage_amount DECIMAL(14,2) DEFAULT 0,              -- 最小缺料金额(可选)

    -- 预警动作
    notify_roles        TEXT,                                 -- 通知角色(JSON数组)
    notify_channels     TEXT,                                 -- 通知渠道: SYSTEM/EMAIL/WECHAT/SMS
    auto_escalate       BOOLEAN DEFAULT 0,                    -- 是否自动升级
    escalate_after_hours INTEGER DEFAULT 0,                   -- 超时后自动升级(小时)
    escalate_to_level   VARCHAR(10),                          -- 升级到的级别

    -- 响应要求
    response_deadline_hours INTEGER DEFAULT 24,               -- 响应时限(小时)

    -- 排序和启用
    priority            INTEGER DEFAULT 50,                   -- 优先级(数值越小优先级越高)
    is_active           BOOLEAN DEFAULT 1,                    -- 是否启用

    description         TEXT,                                 -- 规则描述
    created_by          INTEGER,                              -- 创建人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(id)
);
INSERT INTO mes_shortage_alert_rule VALUES(1,'L1_STOPPAGE','停工预警','L1',0,1,NULL,0,'["procurement_manager","project_manager","production_manager"]','["SYSTEM","WECHAT","SMS"]',0,0,NULL,2,10,1,'阻塞性物料缺料导致无法装配，需立即处理，2小时内响应',NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_shortage_alert_rule VALUES(2,'L2_URGENT','紧急预警','L2',3,1,NULL,0,'["procurement_engineer","project_manager"]','["SYSTEM","WECHAT"]',1,24,'L1',8,20,1,'阻塞性物料3天内需要但缺料，紧急跟进，8小时内响应，24小时未处理升级',NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_shortage_alert_rule VALUES(3,'L3_ADVANCE','提前预警','L3',7,0,NULL,0,'["procurement_engineer"]','["SYSTEM","EMAIL"]',1,48,'L2',24,30,1,'物料7天内需要但缺料，提前准备，24小时内响应，48小时未处理升级',NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO mes_shortage_alert_rule VALUES(4,'L4_NORMAL','常规预警','L4',14,0,NULL,0,'["procurement_engineer"]','["SYSTEM"]',1,72,'L3',48,40,1,'物料14天内需要但缺料，常规跟进，48小时内响应，72小时未处理升级',NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE mes_scheduling_suggestion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_no       VARCHAR(50) NOT NULL UNIQUE,          -- 建议单号: SUG + YYMMDD + 序号

    -- 关联
    readiness_id        INTEGER,                              -- 关联齐套分析ID
    project_id          INTEGER NOT NULL,                     -- 项目ID
    machine_id          INTEGER,                              -- 机台ID

    -- 建议类型
    suggestion_type     VARCHAR(20) NOT NULL,                 -- 类型: START/DELAY/EXPEDITE/SUBSTITUTE/PARTIAL

    -- 建议内容
    suggestion_title    VARCHAR(200) NOT NULL,                -- 建议标题
    suggestion_content  TEXT NOT NULL,                        -- 建议详情

    -- 优先级评分(基于多因素计算)
    priority_score      DECIMAL(5,2) DEFAULT 0,               -- 优先级得分(0-100)

    -- 评分因素(JSON)
    factors             TEXT,                                 -- 影响因素JSON

    -- 时间建议
    suggested_start_date DATE,                                -- 建议开工日期
    original_start_date DATE,                                 -- 原计划开工日期
    delay_days          INTEGER DEFAULT 0,                    -- 建议延期天数

    -- 影响评估
    impact_description  TEXT,                                 -- 影响描述
    risk_level          VARCHAR(20),                          -- 风险级别: HIGH/MEDIUM/LOW

    -- 状态
    status              VARCHAR(20) DEFAULT 'PENDING',        -- PENDING/ACCEPTED/REJECTED/EXPIRED
    accepted_by         INTEGER,                              -- 接受人ID
    accepted_at         DATETIME,                             -- 接受时间
    reject_reason       TEXT,                                 -- 拒绝原因

    -- 生成信息
    generated_at        DATETIME NOT NULL,                    -- 生成时间
    valid_until         DATETIME,                             -- 有效期至

    remark              TEXT,                                 -- 备注
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (readiness_id) REFERENCES mes_material_readiness(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (accepted_by) REFERENCES users(id)
);
CREATE TABLE bonus_allocation_sheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_code VARCHAR(50) NOT NULL UNIQUE,          -- 明细表编号
    sheet_name VARCHAR(200) NOT NULL,                -- 明细表名称
    
    -- 文件信息
    file_path VARCHAR(500) NOT NULL,                  -- 文件路径
    file_name VARCHAR(200),                          -- 原始文件名
    file_size INTEGER,                               -- 文件大小（字节）
    
    -- 关联信息
    project_id INTEGER,                              -- 项目ID（可选）
    period_id INTEGER,                                -- 考核周期ID（可选）
    
    -- 统计信息
    total_rows INTEGER DEFAULT 0,                    -- 总行数
    valid_rows INTEGER DEFAULT 0,                    -- 有效行数
    invalid_rows INTEGER DEFAULT 0,                   -- 无效行数
    
    -- 状态
    status VARCHAR(20) DEFAULT 'UPLOADED',           -- 状态：UPLOADED/PARSED/DISTRIBUTED
    
    -- 解析结果
    parse_result TEXT,                               -- 解析结果(JSON)
    parse_errors TEXT,                               -- 解析错误(JSON)
    
    -- 线下确认标记
    finance_confirmed BOOLEAN DEFAULT 0,            -- 财务部确认
    hr_confirmed BOOLEAN DEFAULT 0,                  -- 人力资源部确认
    manager_confirmed BOOLEAN DEFAULT 0,             -- 总经理确认
    confirmed_at DATETIME,                           -- 确认完成时间
    
    -- 发放信息
    distributed_at DATETIME,                         -- 发放时间
    distributed_by INTEGER,                           -- 发放人
    distribution_count INTEGER DEFAULT 0,             -- 发放记录数
    
    uploaded_by INTEGER NOT NULL,                     -- 上传人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (distributed_by) REFERENCES users(id)
);
CREATE TABLE bidding_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bidding_no VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(500) NOT NULL,
    customer_id INTEGER,
    customer_name VARCHAR(200),
    
    -- 招标信息
    tender_no VARCHAR(100),
    tender_type VARCHAR(20),
    tender_platform VARCHAR(200),
    tender_url VARCHAR(500),
    
    -- 时间节点
    publish_date DATE,
    deadline_date DATETIME,
    bid_opening_date DATETIME,
    
    -- 标书信息
    bid_bond DECIMAL(15, 2),
    bid_bond_status VARCHAR(20) DEFAULT 'not_required',
    estimated_amount DECIMAL(15, 2),
    
    -- 投标准备
    bid_document_status VARCHAR(20) DEFAULT 'not_started',
    technical_doc_ready BOOLEAN DEFAULT 0,
    commercial_doc_ready BOOLEAN DEFAULT 0,
    qualification_doc_ready BOOLEAN DEFAULT 0,
    
    -- 投标方式
    submission_method VARCHAR(20),
    submission_address VARCHAR(500),
    
    -- 负责人
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    support_person_name VARCHAR(50),
    
    -- 投标结果
    bid_result VARCHAR(20) DEFAULT 'pending',
    bid_price DECIMAL(15, 2),
    win_price DECIMAL(15, 2),
    result_date DATE,
    result_remark TEXT,
    
    status VARCHAR(20) DEFAULT 'draft',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);
CREATE TABLE bidding_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bidding_project_id INTEGER NOT NULL,
    document_type VARCHAR(50),
    document_name VARCHAR(200),
    file_path VARCHAR(500),
    file_size INTEGER,
    version VARCHAR(20),
    status VARCHAR(20) DEFAULT 'draft',
    reviewed_by INTEGER,
    reviewed_at DATETIME,
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (bidding_project_id) REFERENCES bidding_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);
CREATE TABLE contract_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    review_type VARCHAR(20),
    review_status VARCHAR(20) DEFAULT 'pending',
    reviewer_id INTEGER,
    review_comment TEXT,
    reviewed_at DATETIME,
    risk_items TEXT,  -- JSON格式
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE contract_seal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    seal_status VARCHAR(20) DEFAULT 'pending',
    seal_date DATE,
    seal_operator_id INTEGER,
    send_date DATE,
    tracking_no VARCHAR(50),
    courier_company VARCHAR(50),
    receive_date DATE,
    archive_date DATE,
    archive_location VARCHAR(200),
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (seal_operator_id) REFERENCES users(id)
);
CREATE TABLE payment_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    project_id INTEGER,
    payment_node VARCHAR(50),
    payment_amount DECIMAL(15, 2),
    plan_date DATE,
    reminder_type VARCHAR(20),
    reminder_content TEXT,
    reminder_date DATE,
    reminder_person_id INTEGER,
    customer_response TEXT,
    next_reminder_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reminder_person_id) REFERENCES users(id)
);
CREATE TABLE document_archives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archive_no VARCHAR(50) NOT NULL UNIQUE,
    document_type VARCHAR(50),
    related_type VARCHAR(50),
    related_id INTEGER,
    document_name VARCHAR(200),
    file_path VARCHAR(500),
    file_size INTEGER,
    archive_location VARCHAR(200),
    archive_date DATE,
    archiver_id INTEGER,
    status VARCHAR(20) DEFAULT 'archived',
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (archiver_id) REFERENCES users(id)
);
CREATE TABLE sales_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(50) NOT NULL UNIQUE,
    contract_id INTEGER,
    contract_no VARCHAR(50),
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    project_id INTEGER,
    project_no VARCHAR(50),
    order_type VARCHAR(20) DEFAULT 'standard',
    order_amount DECIMAL(15, 2),
    currency VARCHAR(10) DEFAULT 'CNY',
    required_date DATE,
    promised_date DATE,
    order_status VARCHAR(20) DEFAULT 'draft',
    project_no_assigned BOOLEAN DEFAULT 0,
    project_no_assigned_date DATETIME,
    project_notice_sent BOOLEAN DEFAULT 0,
    project_notice_date DATETIME,
    erp_order_no VARCHAR(50),
    erp_sync_status VARCHAR(20) DEFAULT 'pending',
    erp_sync_time DATETIME,
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);
CREATE TABLE sales_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_order_id INTEGER NOT NULL,
    item_name VARCHAR(200),
    item_spec VARCHAR(200),
    qty DECIMAL(10, 2),
    unit VARCHAR(20),
    unit_price DECIMAL(12, 2),
    amount DECIMAL(12, 2),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE
);
CREATE TABLE delivery_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_no VARCHAR(50) NOT NULL UNIQUE,
    order_id INTEGER NOT NULL,
    order_no VARCHAR(50),
    contract_id INTEGER,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    project_id INTEGER,
    delivery_date DATE,
    delivery_type VARCHAR(20),
    logistics_company VARCHAR(100),
    tracking_no VARCHAR(100),
    receiver_name VARCHAR(50),
    receiver_phone VARCHAR(20),
    receiver_address VARCHAR(500),
    delivery_amount DECIMAL(15, 2),
    approval_status VARCHAR(20) DEFAULT 'pending',
    approval_comment TEXT,
    approved_by INTEGER,
    approved_at DATETIME,
    special_approval BOOLEAN DEFAULT 0,
    special_approver_id INTEGER,
    special_approval_reason TEXT,
    delivery_status VARCHAR(20) DEFAULT 'draft',
    print_date DATETIME,
    ship_date DATETIME,
    receive_date DATE,
    return_status VARCHAR(20) DEFAULT 'pending',
    return_date DATE,
    signed_delivery_file_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (special_approver_id) REFERENCES users(id)
);
CREATE TABLE acceptance_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acceptance_order_id INTEGER NOT NULL,
    acceptance_order_no VARCHAR(50),
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    condition_check_status VARCHAR(20) DEFAULT 'pending',
    condition_check_result TEXT,
    condition_check_date DATETIME,
    condition_checker_id INTEGER,
    tracking_status VARCHAR(20) DEFAULT 'pending',
    reminder_count INTEGER DEFAULT 0,
    last_reminder_date DATETIME,
    last_reminder_by INTEGER,
    received_date DATE,
    signed_file_id INTEGER,
    report_status VARCHAR(20) DEFAULT 'pending',
    report_generated_date DATETIME,
    report_signed_date DATETIME,
    report_archived_date DATETIME,
    warranty_start_date DATE,
    warranty_end_date DATE,
    warranty_status VARCHAR(20) DEFAULT 'not_started',
    warranty_expiry_reminded BOOLEAN DEFAULT 0,
    contract_id INTEGER,
    contract_no VARCHAR(50),
    sales_person_id INTEGER,
    sales_person_name VARCHAR(50),
    support_person_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (condition_checker_id) REFERENCES users(id),
    FOREIGN KEY (last_reminder_by) REFERENCES users(id),
    FOREIGN KEY (sales_person_id) REFERENCES users(id),
    FOREIGN KEY (support_person_id) REFERENCES users(id)
);
CREATE TABLE acceptance_tracking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_id INTEGER NOT NULL,
    record_type VARCHAR(20) NOT NULL,
    record_content TEXT,
    record_date DATETIME NOT NULL,
    operator_id INTEGER NOT NULL,
    operator_name VARCHAR(50),
    result VARCHAR(20),
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracking_id) REFERENCES acceptance_tracking(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);
CREATE TABLE reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_no VARCHAR(50) NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    customer_name VARCHAR(200),
    period_start DATE,
    period_end DATE,
    opening_balance DECIMAL(15, 2) DEFAULT 0,
    period_sales DECIMAL(15, 2) DEFAULT 0,
    period_receipt DECIMAL(15, 2) DEFAULT 0,
    closing_balance DECIMAL(15, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    sent_date DATE,
    confirm_date DATE,
    customer_confirmed BOOLEAN DEFAULT 0,
    customer_confirm_date DATE,
    customer_difference DECIMAL(15, 2),
    difference_reason TEXT,
    reconciliation_file_id INTEGER,
    confirmed_file_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
CREATE TABLE culture_wall_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 内容类型
    content_type VARCHAR(30) NOT NULL,                    -- 内容类型:STRATEGY/CULTURE/IMPORTANT/NOTICE/REWARD
    
    -- 内容信息
    title VARCHAR(200) NOT NULL,                          -- 标题
    content TEXT,                                         -- 内容
    summary VARCHAR(500),                                 -- 摘要
    
    -- 媒体资源
    images TEXT,                                          -- 图片列表(JSON)
    videos TEXT,                                          -- 视频列表(JSON)
    attachments TEXT,                                     -- 附件列表(JSON)
    
    -- 显示设置
    is_published INTEGER DEFAULT 0,                       -- 是否发布
    publish_date DATE,                                    -- 发布日期
    expire_date DATE,                                     -- 过期日期
    priority INTEGER DEFAULT 0,                           -- 优先级
    display_order INTEGER DEFAULT 0,                      -- 显示顺序
    
    -- 阅读统计
    view_count INTEGER DEFAULT 0,                        -- 浏览次数
    
    -- 关联信息
    related_project_id INTEGER,                           -- 关联项目ID
    related_department_id INTEGER,                        -- 关联部门ID
    
    -- 发布人
    published_by INTEGER,                                 -- 发布人ID
    published_by_name VARCHAR(50),                        -- 发布人姓名
    
    created_by INTEGER,                                   -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (related_project_id) REFERENCES project(id),
    FOREIGN KEY (related_department_id) REFERENCES organization(id),
    FOREIGN KEY (published_by) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE personal_goal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,                             -- 用户ID
    
    -- 目标信息
    goal_type VARCHAR(20) NOT NULL,                      -- 目标类型:MONTHLY/QUARTERLY/YEARLY
    period VARCHAR(20) NOT NULL,                          -- 目标周期
    title VARCHAR(200) NOT NULL,                          -- 目标标题
    description TEXT,                                     -- 目标描述
    
    -- 目标指标
    target_value VARCHAR(50),                             -- 目标值
    current_value VARCHAR(50),                            -- 当前值
    unit VARCHAR(20),                                    -- 单位
    
    -- 进度
    progress INTEGER DEFAULT 0,                          -- 进度百分比(0-100)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'IN_PROGRESS',            -- 状态:IN_PROGRESS/COMPLETED/OVERDUE/CANCELLED
    
    -- 时间
    start_date DATE,                                      -- 开始日期
    end_date DATE,                                       -- 结束日期
    completed_date DATE,                                  -- 完成日期
    
    -- 备注
    notes TEXT,                                           -- 备注
    
    created_by INTEGER,                                   -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE culture_wall_read_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,                          -- 内容ID
    user_id INTEGER NOT NULL,                             -- 用户ID
    
    -- 阅读时间
    read_at DATETIME NOT NULL,                            -- 阅读时间
    
    -- 阅读时长(秒)
    read_duration INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,                      -- 阅读时长(秒)
    
    FOREIGN KEY (content_id) REFERENCES culture_wall_content(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id),
    UNIQUE(content_id, user_id)
);
CREATE TABLE installation_dispatch_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(50) UNIQUE NOT NULL,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    customer_id INTEGER NOT NULL,
    task_type VARCHAR(20) NOT NULL,
    task_title VARCHAR(200) NOT NULL,
    task_description TEXT,
    location VARCHAR(200),
    scheduled_date DATE NOT NULL,
    estimated_hours NUMERIC(5, 2),
    assigned_to_id INTEGER,
    assigned_to_name VARCHAR(50),
    assigned_by_id INTEGER,
    assigned_by_name VARCHAR(50),
    assigned_time DATETIME,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    actual_hours NUMERIC(5, 2),
    progress INTEGER DEFAULT 0,
    customer_contact VARCHAR(50),
    customer_phone VARCHAR(20),
    customer_address VARCHAR(500),
    execution_notes TEXT,
    issues_found TEXT,
    solution_provided TEXT,
    photos TEXT,  -- JSON format
    service_record_id INTEGER,
    acceptance_order_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (assigned_to_id) REFERENCES users(id),
    FOREIGN KEY (assigned_by_id) REFERENCES users(id),
    FOREIGN KEY (service_record_id) REFERENCES service_records(id),
    FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id)
);
CREATE TABLE management_rhythm_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL,                    -- 节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    config_name VARCHAR(200) NOT NULL,                    -- 配置名称
    description TEXT,                                     -- 配置描述
    
    -- 会议模板配置(JSON)
    meeting_template TEXT,                                -- 会议模板配置(JSON)
    
    -- 关键指标清单(JSON)
    key_metrics TEXT,                                     -- 关键指标清单(JSON)
    
    -- 输出成果清单(JSON)
    output_artifacts TEXT,                                -- 输出成果清单(JSON)
    
    -- 状态
    is_active VARCHAR(10) DEFAULT 'ACTIVE',              -- 是否启用:ACTIVE/INACTIVE
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE strategic_meeting (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,                                    -- 项目ID(可为空表示跨项目会议)
    rhythm_config_id INTEGER,                              -- 节律配置ID
    
    -- 会议信息
    rhythm_level VARCHAR(20) NOT NULL,                     -- 会议层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    meeting_name VARCHAR(200) NOT NULL,                    -- 会议名称
    meeting_type VARCHAR(50),                              -- 会议类型
    
    -- 时间地点
    meeting_date DATE NOT NULL,                           -- 会议日期
    start_time TIME,                                      -- 开始时间
    end_time TIME,                                        -- 结束时间
    location VARCHAR(100),                                -- 会议地点
    
    -- 人员
    organizer_id INTEGER,                                  -- 组织者ID
    organizer_name VARCHAR(50),                            -- 组织者
    attendees TEXT,                                       -- 参会人员(JSON)
    
    -- 内容
    agenda TEXT,                                           -- 会议议程
    minutes TEXT,                                          -- 会议纪要
    decisions TEXT,                                        -- 会议决议
    
    -- 战略相关(JSON)
    strategic_context TEXT,                                -- 战略背景(JSON)
    strategic_structure TEXT,                              -- 五层战略结构(JSON):愿景/机会/定位/目标/路径
    key_decisions TEXT,                                    -- 关键决策(JSON)
    resource_allocation TEXT,                              -- 资源分配(JSON)
    
    -- 指标快照(JSON)
    metrics_snapshot TEXT,                                 -- 指标快照(JSON)
    
    -- 附件
    attachments TEXT,                                      -- 会议附件(JSON)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'SCHEDULED',                -- 状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, related_project_ids TEXT,
    
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (rhythm_config_id) REFERENCES management_rhythm_config(id),
    FOREIGN KEY (organizer_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE meeting_action_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL,                          -- 会议ID
    
    -- 行动项信息
    action_description TEXT NOT NULL,                      -- 行动描述
    owner_id INTEGER NOT NULL,                             -- 责任人ID
    owner_name VARCHAR(50),                                -- 责任人姓名
    
    -- 时间
    due_date DATE NOT NULL,                                -- 截止日期
    completed_date DATE,                                   -- 完成日期
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PENDING',                  -- 状态:PENDING/IN_PROGRESS/COMPLETED/OVERDUE
    
    -- 完成说明
    completion_notes TEXT,                                -- 完成说明
    
    -- 优先级
    priority VARCHAR(20) DEFAULT 'NORMAL',                  -- 优先级:LOW/NORMAL/HIGH/URGENT
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (meeting_id) REFERENCES strategic_meeting(id) ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE rhythm_dashboard_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 节律信息
    rhythm_level VARCHAR(20) NOT NULL,                      -- 节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK
    cycle_type VARCHAR(20) NOT NULL,                      -- 周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY
    current_cycle VARCHAR(50),                              -- 当前周期
    
    -- 指标快照(JSON)
    key_metrics_snapshot TEXT,                            -- 关键指标快照(JSON)
    
    -- 健康状态
    health_status VARCHAR(20) DEFAULT 'GREEN',             -- 健康状态:GREEN/YELLOW/RED
    
    -- 会议信息
    last_meeting_date DATE,                                -- 上次会议日期
    next_meeting_date DATE,                                -- 下次会议日期
    meetings_count INTEGER DEFAULT 0,                     -- 本周期会议数量
    completed_meetings_count INTEGER DEFAULT 0,            -- 已完成会议数量
    
    -- 行动项统计
    total_action_items INTEGER DEFAULT 0,                  -- 总行动项数
    completed_action_items INTEGER DEFAULT 0,               -- 已完成行动项数
    overdue_action_items INTEGER DEFAULT 0,                -- 逾期行动项数
    completion_rate VARCHAR(10),                            -- 完成率(百分比)
    
    -- 快照时间
    snapshot_date DATE NOT NULL,                           -- 快照日期
    
    created_by INTEGER,                                    -- 创建人ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE project_role_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(50) NOT NULL UNIQUE,          -- 角色编码: PM, TECH_LEAD, PROC_LEAD, CS_LEAD
    role_name VARCHAR(100) NOT NULL,                -- 角色名称: 项目经理, 技术负责人
    role_category VARCHAR(50) DEFAULT 'GENERAL',    -- 角色分类: MANAGEMENT, TECHNICAL, SUPPORT
    description TEXT,                               -- 角色职责描述
    can_have_team BOOLEAN DEFAULT 0,                -- 是否可带团队
    is_required BOOLEAN DEFAULT 0,                  -- 是否默认必需（新项目自动启用）
    sort_order INTEGER DEFAULT 0,                   -- 排序顺序
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO project_role_types VALUES(1,'PM','项目经理','MANAGEMENT','负责项目整体规划、进度管控、资源协调和客户沟通',1,1,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(2,'TECH_LEAD','技术负责人','TECHNICAL','负责项目整体技术方案设计和技术决策',1,0,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(3,'ME_LEAD','机械负责人','TECHNICAL','负责机械结构设计、工装夹具设计和机械调试',1,0,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(4,'EE_LEAD','电气负责人','TECHNICAL','负责电气系统设计、布线规划和电气调试',1,0,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(5,'SW_LEAD','软件负责人','TECHNICAL','负责控制程序开发、上位机软件和系统集成',0,0,5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(6,'PROC_LEAD','采购负责人','SUPPORT','负责物料采购协调、供应商管理和交期跟踪',0,0,6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(7,'CS_LEAD','客服负责人','SUPPORT','负责现场安装调试、客户培训和售后服务',1,0,7,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(8,'QA_LEAD','质量负责人','SUPPORT','负责质量管控、检验标准制定和问题跟踪',0,0,8,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(9,'PMC_LEAD','PMC负责人','SUPPORT','负责生产计划排程、物料齐套和进度协调',0,0,9,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_role_types VALUES(10,'INSTALL_LEAD','安装负责人','TECHNICAL','负责现场设备安装、调试和验收',1,0,10,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE project_role_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_type_id INTEGER NOT NULL,                  -- 角色类型ID
    is_enabled BOOLEAN DEFAULT 1,                   -- 是否启用该角色
    is_required BOOLEAN DEFAULT 0,                  -- 是否必填（必须指定负责人）
    remark TEXT,                                    -- 配置备注
    created_by INTEGER,                             -- 创建人
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (role_type_id) REFERENCES project_role_types(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE(project_id, role_type_id)
);
CREATE TABLE project_template_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id         INTEGER NOT NULL,                     -- 模板ID
    version_no          VARCHAR(20) NOT NULL,                 -- 版本号
    status              VARCHAR(20) DEFAULT 'DRAFT',          -- 状态：DRAFT/ACTIVE/ARCHIVED
    template_config     TEXT,                                 -- 模板配置JSON
    release_notes       TEXT,                                 -- 版本说明
    created_by          INTEGER,                              -- 创建人ID
    published_by        INTEGER,                              -- 发布人ID
    published_at        DATETIME,                              -- 发布时间
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (published_by) REFERENCES users(id)
);
CREATE TABLE hr_tag_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_code VARCHAR(50) UNIQUE NOT NULL,           -- 标签编码
    tag_name VARCHAR(100) NOT NULL,                 -- 标签名称
    tag_type VARCHAR(20) NOT NULL,                  -- SKILL/DOMAIN/ATTITUDE/CHARACTER/SPECIAL
    parent_id INTEGER,                              -- 父标签ID（支持层级）
    weight DECIMAL(5,2) DEFAULT 1.0,                -- 权重
    is_required BOOLEAN DEFAULT 0,                  -- 是否必需标签
    description TEXT,                               -- 标签描述
    sort_order INTEGER DEFAULT 0,                   -- 排序
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES hr_tag_dict(id)
);
INSERT INTO hr_tag_dict VALUES(1,'SKILL_ME_DESIGN','机械设计','SKILL',NULL,1,0,'机械结构设计能力',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(2,'SKILL_ME_3D','3D建模','SKILL',NULL,1,0,'SolidWorks/UG等3D建模',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(3,'SKILL_ME_2D','工程制图','SKILL',NULL,0.8000000000000000444,0,'AutoCAD工程图纸',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(4,'SKILL_EE_SCHEMATIC','电气原理图','SKILL',NULL,1,0,'电气原理图设计',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(5,'SKILL_EE_PLC','PLC编程','SKILL',NULL,1.199999999999999956,0,'PLC程序编写调试',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(6,'SKILL_EE_HMI','HMI开发','SKILL',NULL,0.9000000000000000222,0,'触摸屏界面开发',6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(7,'SKILL_SW_MOTION','运动控制','SKILL',NULL,1.199999999999999956,0,'运动控制系统开发',7,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(8,'SKILL_SW_VISION','视觉系统','SKILL',NULL,1.300000000000000044,0,'视觉检测系统开发',8,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(9,'SKILL_TE_ICT','ICT测试','SKILL',NULL,1,0,'ICT测试设备调试',9,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(10,'SKILL_TE_FCT','FCT测试','SKILL',NULL,1,0,'FCT功能测试',10,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(11,'SKILL_ASSEMBLY','装配调试','SKILL',NULL,1,0,'设备装配调试能力',11,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(12,'SKILL_DEBUG','故障排除','SKILL',NULL,1.100000000000000089,0,'设备故障诊断排除',12,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(13,'DOMAIN_3C','3C电子','DOMAIN',NULL,1,0,'3C电子行业经验',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(14,'DOMAIN_AUTO','汽车电子','DOMAIN',NULL,1.199999999999999956,0,'汽车电子行业经验',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(15,'DOMAIN_MEDICAL','医疗器械','DOMAIN',NULL,1.300000000000000044,0,'医疗器械行业经验',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(16,'DOMAIN_SEMICONDUCTOR','半导体','DOMAIN',NULL,1.399999999999999912,0,'半导体行业经验',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(17,'DOMAIN_NEW_ENERGY','新能源','DOMAIN',NULL,1.199999999999999956,0,'新能源行业经验',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(18,'DOMAIN_PCBA','PCBA测试','DOMAIN',NULL,1,0,'PCBA测试经验',6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(19,'ATT_RESPONSIBLE','责任心','ATTITUDE',NULL,1.199999999999999956,0,'工作责任心强',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(20,'ATT_PROACTIVE','主动性','ATTITUDE',NULL,1.100000000000000089,0,'工作主动积极',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(21,'ATT_TEAMWORK','团队协作','ATTITUDE',NULL,1,0,'善于团队协作',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(22,'ATT_LEARNING','学习能力','ATTITUDE',NULL,1,0,'快速学习能力',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(23,'ATT_PRESSURE','抗压能力','ATTITUDE',NULL,1.100000000000000089,0,'能承受工作压力',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(24,'ATT_COMMUNICATION','沟通能力','ATTITUDE',NULL,1,0,'有效沟通能力',6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(25,'CHAR_DETAIL','细致严谨','CHARACTER',NULL,1,0,'工作细致严谨',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(26,'CHAR_CREATIVE','创新思维','CHARACTER',NULL,0.9000000000000000222,0,'具有创新思维',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(27,'CHAR_STABLE','稳重可靠','CHARACTER',NULL,1,0,'性格稳重可靠',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(28,'CHAR_FLEXIBLE','灵活应变','CHARACTER',NULL,0.8000000000000000444,0,'灵活应变能力',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(29,'SPEC_ONSITE','现场经验','SPECIAL',NULL,1.5,0,'客户现场服务经验',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(30,'SPEC_TRAINING','培训能力','SPECIAL',NULL,1.199999999999999956,0,'能进行技术培训',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(31,'SPEC_CUSTOMER','客户关系','SPECIAL',NULL,1.300000000000000044,0,'良好客户关系维护',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(32,'SPEC_LEADER','项目带队','SPECIAL',NULL,1.399999999999999912,0,'能带领项目团队',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO hr_tag_dict VALUES(33,'SPEC_OVERSEAS','出国经验','SPECIAL',NULL,1.5,0,'有海外项目经验',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE hr_employee_tag_evaluation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                   -- 员工ID
    tag_id INTEGER NOT NULL,                        -- 标签ID
    score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),  -- 评分1-5
    evidence TEXT,                                  -- 评分依据/证据
    evaluator_id INTEGER NOT NULL,                  -- 评估人ID
    evaluate_date DATE NOT NULL,                    -- 评估日期
    is_valid BOOLEAN DEFAULT 1,                     -- 是否有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (tag_id) REFERENCES hr_tag_dict(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE hr_employee_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER UNIQUE NOT NULL,            -- 员工ID
    skill_tags TEXT,                                -- 技能标签JSON [{tag_id, score, tag_name}]
    domain_tags TEXT,                               -- 领域标签JSON
    attitude_tags TEXT,                             -- 态度标签JSON
    character_tags TEXT,                            -- 性格标签JSON
    special_tags TEXT,                              -- 特殊能力JSON
    attitude_score DECIMAL(5,2),                    -- 态度得分（聚合）
    quality_score DECIMAL(5,2),                     -- 质量得分（聚合）
    current_workload_pct DECIMAL(5,2) DEFAULT 0,   -- 当前工作负载百分比
    available_hours DECIMAL(10,2) DEFAULT 0,        -- 可用工时
    total_projects INTEGER DEFAULT 0,               -- 参与项目总数
    avg_performance_score DECIMAL(5,2),             -- 平均绩效得分
    profile_updated_at TIMESTAMP,                   -- 档案更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
CREATE TABLE hr_project_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                   -- 员工ID
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_code VARCHAR(50) NOT NULL,                 -- 角色编码
    role_name VARCHAR(100),                         -- 角色名称
    performance_score DECIMAL(5,2),                 -- 绩效得分
    quality_score DECIMAL(5,2),                     -- 质量得分
    collaboration_score DECIMAL(5,2),               -- 协作得分
    on_time_rate DECIMAL(5,2),                      -- 按时完成率
    contribution_level VARCHAR(20),                 -- CORE/MAJOR/NORMAL/MINOR
    hours_spent DECIMAL(10,2),                      -- 投入工时
    evaluation_date DATE,                           -- 评估日期
    evaluator_id INTEGER,                           -- 评估人ID
    comments TEXT,                                  -- 评价意见
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE mes_project_staffing_need (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                    -- 项目ID
    role_code VARCHAR(50) NOT NULL,                 -- 角色编码
    role_name VARCHAR(100),                         -- 角色名称
    headcount INTEGER DEFAULT 1,                    -- 需求人数
    required_skills TEXT NOT NULL,                  -- 必需技能JSON [{tag_id, min_score}]
    preferred_skills TEXT,                          -- 优选技能JSON
    required_domains TEXT,                          -- 必需领域JSON
    required_attitudes TEXT,                        -- 必需态度JSON
    min_level VARCHAR(20),                          -- 最低等级
    priority VARCHAR(10) DEFAULT 'P3',              -- P1-P5
    start_date DATE,                                -- 开始日期
    end_date DATE,                                  -- 结束日期
    allocation_pct DECIMAL(5,2) DEFAULT 100,        -- 分配比例
    status VARCHAR(20) DEFAULT 'OPEN',              -- OPEN/MATCHING/FILLED/CANCELLED
    requester_id INTEGER,                           -- 申请人ID
    filled_count INTEGER DEFAULT 0,                 -- 已填充人数
    remark TEXT,                                    -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (requester_id) REFERENCES users(id)
);
CREATE TABLE hr_ai_matching_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id VARCHAR(50) NOT NULL,                -- 匹配请求ID
    project_id INTEGER NOT NULL,                    -- 项目ID
    staffing_need_id INTEGER NOT NULL,              -- 人员需求ID
    candidate_employee_id INTEGER NOT NULL,         -- 候选员工ID
    total_score DECIMAL(5,2) NOT NULL,              -- 综合得分
    dimension_scores TEXT NOT NULL,                 -- 各维度得分JSON
    rank INTEGER NOT NULL,                          -- 排名
    recommendation_type VARCHAR(20),                -- STRONG/RECOMMENDED/ACCEPTABLE/WEAK
    is_accepted BOOLEAN,                            -- 是否被采纳
    accept_time TIMESTAMP,                          -- 采纳时间
    acceptor_id INTEGER,                            -- 采纳人ID
    reject_reason TEXT,                             -- 拒绝原因
    matching_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 匹配时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (staffing_need_id) REFERENCES mes_project_staffing_need(id),
    FOREIGN KEY (candidate_employee_id) REFERENCES employees(id),
    FOREIGN KEY (acceptor_id) REFERENCES users(id)
);
CREATE TABLE meeting_report_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name VARCHAR(200) NOT NULL,
    report_type VARCHAR(20) NOT NULL,
    description TEXT,
    enabled_metrics TEXT,
    comparison_config TEXT,
    display_config TEXT,
    is_default BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE report_metric_definition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_code VARCHAR(50) NOT NULL UNIQUE,
    metric_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    data_source VARCHAR(50) NOT NULL,
    data_field VARCHAR(100),
    filter_conditions TEXT,
    calculation_type VARCHAR(20) NOT NULL,
    calculation_formula TEXT,
    support_mom BOOLEAN DEFAULT 1,
    support_yoy BOOLEAN DEFAULT 1,
    unit VARCHAR(20),
    format_type VARCHAR(20) DEFAULT 'NUMBER',
    decimal_places INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT 1,
    is_system BOOLEAN DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE meeting_report (
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
CREATE TABLE scheduler_task_configs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id             VARCHAR(100) NOT NULL UNIQUE,            -- 任务ID（对应scheduler_config.py中的id）
    
    -- 任务基本信息（从scheduler_config.py同步，用于显示）
    task_name           VARCHAR(200) NOT NULL,                    -- 任务名称
    module              VARCHAR(200) NOT NULL,                    -- 模块路径
    callable_name       VARCHAR(100) NOT NULL,                    -- 函数名
    owner               VARCHAR(100),                             -- 负责人
    category            VARCHAR(100),                             -- 分类
    description         TEXT,                                      -- 描述
    
    -- 配置信息（可修改）
    is_enabled          BOOLEAN DEFAULT 1 NOT NULL,               -- 是否启用
    cron_config         TEXT NOT NULL,                            -- Cron配置（JSON格式，存储为TEXT）
    
    -- 元数据（从scheduler_config.py同步，只读）
    dependencies_tables TEXT,                                     -- 依赖的数据库表列表（JSON格式，存储为TEXT）
    risk_level          VARCHAR(20),                              -- 风险级别：LOW/MEDIUM/HIGH/CRITICAL
    sla_config          TEXT,                                     -- SLA配置（JSON格式，存储为TEXT）
    
    -- 操作信息
    updated_by          INTEGER,                                  -- 最后更新人ID
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 创建时间
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,      -- 更新时间
    
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
CREATE TABLE position_role_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_keyword VARCHAR(50) NOT NULL,  -- 岗位关键词（模糊匹配）
    role_code VARCHAR(50) NOT NULL,         -- 对应角色编码
    priority INTEGER DEFAULT 0,             -- 优先级，数字越大优先级越高
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO position_role_mapping VALUES(1,'销售总监','sales_director',100,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(2,'销售经理','sales_manager',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(3,'销售工程师','sales',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(4,'销售助理','sales_assistant',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(5,'PLC工程师','plc_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(6,'测试工程师','test_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(7,'机械工程师','mechanical_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(8,'结构工程师','mechanical_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(9,'电气工程师','electrical_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(10,'软件工程师','software_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(11,'售前技术','presales_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(12,'技术开发','rd_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(13,'装配技工','assembler',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(14,'装配钳工','assembler',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(15,'装配电工','assembler',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(16,'品质工程师','qa_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(17,'品质','qa',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(18,'生产部经理','production_manager',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(19,'制造总监','manufacturing_director',100,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(20,'项目经理','pm',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(21,'PMC','pmc',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(22,'项目部经理','project_dept_manager',95,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(23,'客服工程师','customer_service',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(24,'客服','customer_service',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(25,'采购工程师','procurement_engineer',80,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(26,'采购','procurement',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(27,'仓库管理员','warehouse',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(28,'仓库','warehouse',60,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(29,'财务经理','finance_manager',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(30,'财务','finance',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(31,'会计','accountant',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(32,'人事经理','hr_manager',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(33,'人事','hr',70,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(34,'总经理','gm',100,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(35,'副总经理','vp',95,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(36,'董事长','chairman',100,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(37,'部门经理','dept_manager',85,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO position_role_mapping VALUES(38,'总监','director',90,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 人员信息
    user_id INTEGER NOT NULL,                    -- 提交人ID
    user_name VARCHAR(50),                       -- 提交人姓名（冗余字段）
    
    -- 工作信息
    work_date DATE NOT NULL,                     -- 工作日期
    content TEXT NOT NULL,                       -- 工作内容（限制300字）
    
    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT',          -- 状态：DRAFT/SUBMITTED
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE work_log_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 适用范围
    user_id INTEGER,                             -- 用户ID（NULL表示全员）
    department_id INTEGER,                       -- 部门ID（可选）
    
    -- 配置项
    is_required INTEGER DEFAULT 1,               -- 是否必须提交
    is_active INTEGER DEFAULT 1,                 -- 是否启用
    remind_time VARCHAR(10) DEFAULT '18:00',     -- 提醒时间（HH:mm格式）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE work_log_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联工作日志
    work_log_id INTEGER NOT NULL,                -- 工作日志ID
    
    -- 提及信息
    mention_type VARCHAR(20) NOT NULL,           -- 提及类型：PROJECT/MACHINE/USER
    mention_id INTEGER NOT NULL,                  -- 被提及对象ID
    mention_name VARCHAR(200),                   -- 被提及对象名称（冗余字段）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (work_log_id) REFERENCES work_logs(id) ON DELETE CASCADE
);
CREATE TABLE advantage_product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,           -- 类别编码（如 HOME_APPLIANCE）
    name VARCHAR(100) NOT NULL,                 -- 类别名称（如 白色家电）
    description TEXT,                           -- 类别描述
    sort_order INTEGER DEFAULT 0,               -- 排序序号
    is_active INTEGER DEFAULT 1,                -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, test_types TEXT, typical_ct_range VARCHAR(50), automation_levels TEXT);
INSERT INTO advantage_product_categories VALUES(1,'HOME_APPLIANCE','白色家电',NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(2,'AUTOMOTIVE','汽车电子',NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(3,'NEW_ENERGY','新能源',NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(4,'SEMICONDUCTOR','半导体',NULL,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(5,'POWER_TOOLS','电动工具',NULL,5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(6,'AUTOMATION_LINE','自动化线体',NULL,6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(7,'OTHER_EQUIPMENT','其他设备',NULL,7,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
INSERT INTO advantage_product_categories VALUES(8,'EDUCATION','教育实训',NULL,8,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL);
CREATE TABLE advantage_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code VARCHAR(50) NOT NULL UNIQUE,   -- 产品编码（如 KC2701）
    product_name VARCHAR(200) NOT NULL,         -- 产品名称（如 离线双工位FCT）
    category_id INTEGER,                        -- 所属类别ID
    series_code VARCHAR(50),                    -- 产品系列编码（如 KC2700）
    description TEXT,                           -- 产品描述
    is_active INTEGER DEFAULT 1,                -- 是否启用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, test_types TEXT, typical_ct_seconds INTEGER, max_throughput_uph INTEGER, automation_level VARCHAR(50), rail_type VARCHAR(50), workstation_count INTEGER, applicable_products TEXT, applicable_interfaces TEXT, special_features TEXT, reference_price_min NUMERIC(14, 2), reference_price_max NUMERIC(14, 2), typical_lead_time_days INTEGER, match_keywords TEXT, priority_score INTEGER DEFAULT 50,
    FOREIGN KEY (category_id) REFERENCES advantage_product_categories(id)
);
INSERT INTO advantage_products VALUES(1,'KC2701','离线双工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(2,'KC2702','离线显示双工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(3,'KC2703','离线双工位FCT+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(4,'KC2704','离线双轨双工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(5,'KC2705','离线双轨双工位FCT+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(6,'KC2706','在线式双轨双工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(7,'KC2707','在线式双轨双工位FCT+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(8,'KC2708','离线显示双轨双工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(9,'KC2709','在线式双轨双工位FCT+显示',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(10,'KC2710','在线式双轨双工位FCT+显示+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(11,'KC2711','离线双轨多工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(12,'KC2712','离线双轨多工位FCT+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(13,'KC2713','在线式双轨多工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(14,'KC2714','在线式双轨多工位FCT+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(15,'KC2715','离线双轨多工位FCT+显示',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(16,'KC2716','在线式双轨多工位FCT+显示',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(17,'KC2717','在线式双轨多工位FCT+显示+3D SPI',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(18,'KC2718','离线多轨多工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(19,'KC2719','在线式多轨多工位FCT',1,'KC2700',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(20,'KC2101','域控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(21,'KC2102','车载导航整机测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(22,'KC2103','中控屏整机测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(23,'KC2104','T-BOX测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(24,'KC2105','车载网关测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(25,'KC2106','电机控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(26,'KC2107','OBC车载充电机测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(27,'KC2108','DC-DC测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(28,'KC2109','PDU配电盒测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(29,'KC2110','BCM车身控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(30,'KC2111','仪表测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(31,'KC2112','组合开关测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(32,'KC2113','座椅控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(33,'KC2114','车窗控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(34,'KC2115','车灯控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(35,'KC2116','雨刮控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(36,'KC2117','后视镜控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(37,'KC2118','ADAS控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(38,'KC2119','摄像头模组测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(39,'KC2120','毫米波雷达测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(40,'KC2121','激光雷达测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(41,'KC2122','EPB电子手刹测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(42,'KC2123','ABS/ESP测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(43,'KC2124','EPS电动助力转向测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(44,'KC2125','电池包控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(45,'KC2126','线束测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(46,'KC2127','传感器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(47,'KC2128','执行器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(48,'KC2129','汽车音响测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(49,'KC2130','HUD抬头显示测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(50,'KC2131','空调控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(51,'KC2132','天窗控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(52,'KC2133','无线充电控制器测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(53,'KC2134','智能钥匙测试系统',2,'KC2100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(54,'KC2901','PACK/模组EOL测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(55,'KC2902','动力电池模组EOL测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(56,'KC2903','储能电池模组EOL测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(57,'KC2904','电芯化成分容测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(58,'KC2905','电芯分选测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(59,'KC2906','电池包化成测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(60,'KC2907','电池包EOL测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(61,'KC2908','充电桩测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(62,'KC2909','BMS测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(63,'KC2910','电池模拟器',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(64,'KC2911','充电桩模拟器',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(65,'KC2912','车辆模拟器',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(66,'KC2913','电池包老化测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(67,'KC2914','电芯性能测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(68,'KC2915','电池安全测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(69,'KC2916','换电站测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(70,'KC2917','储能系统测试平台',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(71,'KC2918','光伏逆变器测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(72,'KC2919','风电变流器测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(73,'KC2920','电池热管理测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(74,'KC2921','电池均衡测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(75,'KC2922','充放电循环测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(76,'KC2923','电池内阻测试系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(77,'KC2924','动力电池下线检测系统',3,'KC2900',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(78,'KC3101','IC测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(79,'KC3102','芯片老化测试设备',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(80,'KC3103','晶圆测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(81,'KC3104','封装测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(82,'KC3105','功率器件老化测试设备',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(83,'KC3106','IGBT测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(84,'KC3107','功率器件ATE测试设备',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(85,'KC3108','LED测试分选系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(86,'KC3109','光电器件测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(87,'KC3110','传感器芯片测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(88,'KC3111','MCU测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(89,'KC3112','存储芯片测试系统',4,'KC3100',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(90,'KC2601','电动工具整机性能测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(91,'KC2602','电动工具电池包测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(92,'KC2603','电动工具充电器测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(93,'KC2604','电动工具控制器测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(94,'KC2605','电动工具电机测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(95,'KC2606','园林工具测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(96,'KC2607','手持电动工具寿命测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(97,'KC2608','电动工具安全测试系统',5,'KC2600',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(98,'KC3001','PCBA自动化测试线',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(99,'KC3002','电池PACK自动化生产线',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(100,'KC3003','充电桩自动化测试线',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(101,'KC3004','SMT上下料自动化系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(102,'KC3005','自动化检测分选线',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(103,'KC3006','自动化包装系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(104,'KC3007','MES生产执行系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(105,'KC3008','WMS仓储管理系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(106,'KC3009','产线数字孪生系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(107,'KC3010','工业机器人集成应用',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(108,'KC3011','AGV智能物流系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(109,'KC3012','视觉检测自动化系统',6,'KC3000',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(110,'KC3201','通用ICT测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(111,'KC3202','通用FCT测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(112,'KC3203','电源测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(113,'KC3204','变频器测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(114,'KC3205','伺服驱动器测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(115,'KC3206','PLC测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(116,'KC3207','工控机测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(117,'KC3208','触摸屏测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(118,'KC3209','显示屏测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(119,'KC3210','摄像头模组测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(120,'KC3211','智能家居测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(121,'KC3212','医疗器械测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(122,'KC3213','通信模块测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(123,'KC3214','无线充电测试系统',7,'KC3200',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(124,'KC3301','汽车电子技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(125,'KC3302','新能源汽车技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(126,'KC3303','工业机器人实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(127,'KC3304','PLC控制技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(128,'KC3305','电工电子技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(129,'KC3306','单片机技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(130,'KC3307','传感器技术实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(131,'KC3308','自动化生产线实训系统',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(132,'KC3309','智能制造实训系统',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
INSERT INTO advantage_products VALUES(133,'KC3310','工业互联网实训平台',8,'KC3300',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,50);
CREATE TABLE engineer_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,

    -- 岗位信息
    job_type VARCHAR(20) NOT NULL,
    job_level VARCHAR(20) DEFAULT 'junior',

    -- 技能标签
    skills TEXT,
    certifications TEXT,

    -- 时间信息
    job_start_date DATE,
    level_start_date DATE,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE engineer_dimension_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 配置维度（只能按岗位+级别配置，不能针对个人）
    job_type VARCHAR(20) NOT NULL,
    job_level VARCHAR(20),

    -- 五维权重（百分比，总和100）
    technical_weight INTEGER DEFAULT 30,
    execution_weight INTEGER DEFAULT 25,
    cost_quality_weight INTEGER DEFAULT 20,
    knowledge_weight INTEGER DEFAULT 15,
    collaboration_weight INTEGER DEFAULT 10,

    -- 生效时间
    effective_date DATE NOT NULL,
    expired_date DATE,

    -- 配置信息
    config_name VARCHAR(100),
    description TEXT,
    operator_id INTEGER,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (operator_id) REFERENCES users(id)
);
INSERT INTO engineer_dimension_config VALUES(1,'mechanical',NULL,30,25,20,15,10,'2026-01-01',NULL,'机械工程师默认配置',NULL,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO engineer_dimension_config VALUES(2,'test',NULL,30,25,20,15,10,'2026-01-01',NULL,'测试工程师默认配置',NULL,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO engineer_dimension_config VALUES(3,'electrical',NULL,30,25,20,15,10,'2026-01-01',NULL,'电气工程师默认配置',NULL,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE collaboration_rating (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_id INTEGER NOT NULL,

    -- 评价双方
    rater_id INTEGER NOT NULL,
    ratee_id INTEGER NOT NULL,
    rater_job_type VARCHAR(20),
    ratee_job_type VARCHAR(20),

    -- 四维评分（1-5分）
    communication_score INTEGER,
    response_score INTEGER,
    delivery_score INTEGER,
    interface_score INTEGER,

    -- 总分（自动计算）
    total_score DECIMAL(4,2),

    -- 评价备注
    comment TEXT,

    -- 项目关联（可选）
    project_id INTEGER,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (rater_id) REFERENCES users(id),
    FOREIGN KEY (ratee_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE knowledge_contribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 贡献类型
    contribution_type VARCHAR(30) NOT NULL,
    job_type VARCHAR(20),

    -- 贡献内容
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    tags TEXT,

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 审核状态
    status VARCHAR(20) DEFAULT 'draft',
    approved_by INTEGER,
    approved_at DATETIME,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE knowledge_reuse_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    project_id INTEGER,

    -- 复用信息
    reuse_type VARCHAR(30),
    rating INTEGER,
    feedback TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contribution_id) REFERENCES knowledge_contribution(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE design_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 设计信息
    design_name VARCHAR(200) NOT NULL,
    design_type VARCHAR(50),
    design_code VARCHAR(50),
    version VARCHAR(20),

    -- 评审信息
    review_date DATE,
    reviewer_id INTEGER,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    review_comments TEXT,

    -- 附件
    attachments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE mechanical_debug_issue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    responsible_id INTEGER NOT NULL,
    reporter_id INTEGER,

    -- 问题信息
    issue_code VARCHAR(50),
    issue_description TEXT NOT NULL,
    severity VARCHAR(20),
    root_cause VARCHAR(50),
    affected_part VARCHAR(200),

    -- 处理状态
    status VARCHAR(20) DEFAULT 'open',
    found_date DATE,
    resolved_date DATE,
    resolution TEXT,

    -- 影响评估
    cost_impact DECIMAL(12,2),
    time_impact_hours DECIMAL(6,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (responsible_id) REFERENCES users(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);
CREATE TABLE design_reuse_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 复用信息
    source_design_id INTEGER,
    source_design_name VARCHAR(200),
    source_project_id INTEGER,

    -- 复用程度
    reuse_type VARCHAR(30),
    reuse_percentage DECIMAL(5,2),

    -- 节省评估
    saved_hours DECIMAL(6,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (source_project_id) REFERENCES projects(id)
);
CREATE TABLE test_bug_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    reporter_id INTEGER,
    assignee_id INTEGER NOT NULL,

    -- Bug信息
    bug_code VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    severity VARCHAR(20),
    bug_type VARCHAR(30),
    found_stage VARCHAR(30),

    -- 处理信息
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'normal',
    found_time DATETIME,
    resolved_time DATETIME,
    fix_duration_hours DECIMAL(6,2),
    resolution TEXT,

    -- 附件
    attachments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id)
);
CREATE TABLE code_review_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    author_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,

    -- 评审信息
    review_title VARCHAR(200),
    code_module VARCHAR(100),
    language VARCHAR(30),
    lines_changed INTEGER,

    -- 评审结果
    review_date DATE,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    comments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE code_module (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_code VARCHAR(50),
    category VARCHAR(50),
    language VARCHAR(30),
    description TEXT,

    -- 版本信息
    version VARCHAR(20),
    repository_url VARCHAR(500),

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    projects_used TEXT,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id)
);
CREATE TABLE electrical_drawing_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    designer_id INTEGER NOT NULL,

    -- 图纸信息
    drawing_name VARCHAR(200) NOT NULL,
    drawing_code VARCHAR(50),
    drawing_type VARCHAR(50),
    version VARCHAR(20),

    -- 评审结果
    review_date DATE,
    reviewer_id INTEGER,
    result VARCHAR(20),
    is_first_pass BOOLEAN,
    issues_found INTEGER DEFAULT 0,
    review_comments TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (designer_id) REFERENCES users(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);
CREATE TABLE plc_program_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    programmer_id INTEGER NOT NULL,

    -- 程序信息
    program_name VARCHAR(200) NOT NULL,
    program_code VARCHAR(50),
    plc_brand VARCHAR(30),
    plc_model VARCHAR(50),
    version VARCHAR(20),

    -- 调试结果
    first_debug_date DATE,
    is_first_pass BOOLEAN,
    debug_issues INTEGER DEFAULT 0,
    debug_hours DECIMAL(6,2),

    -- 备注
    remarks TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (programmer_id) REFERENCES users(id)
);
CREATE TABLE plc_module_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contributor_id INTEGER NOT NULL,

    -- 模块信息
    module_name VARCHAR(100) NOT NULL,
    module_code VARCHAR(50),
    category VARCHAR(50),
    plc_brand VARCHAR(30),
    description TEXT,

    -- 版本信息
    version VARCHAR(20),
    file_path VARCHAR(500),

    -- 复用统计
    reuse_count INTEGER DEFAULT 0,
    projects_used TEXT,
    rating_score DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (contributor_id) REFERENCES users(id)
);
CREATE TABLE component_selection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    engineer_id INTEGER NOT NULL,

    -- 选型信息
    component_name VARCHAR(200) NOT NULL,
    component_type VARCHAR(50),
    specification VARCHAR(200),
    manufacturer VARCHAR(100),

    -- 选型结果
    is_standard BOOLEAN DEFAULT FALSE,
    is_from_stock BOOLEAN DEFAULT FALSE,
    selection_result VARCHAR(20),
    replacement_reason TEXT,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (engineer_id) REFERENCES users(id)
);
CREATE TABLE electrical_fault_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    responsible_id INTEGER NOT NULL,
    reporter_id INTEGER,

    -- 故障信息
    fault_code VARCHAR(50),
    fault_description TEXT NOT NULL,
    fault_type VARCHAR(50),
    severity VARCHAR(20),

    -- 处理状态
    status VARCHAR(20) DEFAULT 'open',
    found_date DATE,
    resolved_date DATE,
    resolution TEXT,
    root_cause TEXT,

    -- 影响评估
    downtime_hours DECIMAL(6,2),
    cost_impact DECIMAL(12,2),

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (responsible_id) REFERENCES users(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);
CREATE TABLE industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES industries(id),
    description TEXT,
    typical_products TEXT,
    typical_tests TEXT,
    market_size VARCHAR(50),
    growth_potential VARCHAR(50),
    company_experience VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO industries VALUES(1,'3C_ELECTRONICS','3C电子',NULL,NULL,NULL,NULL,'LARGE','MEDIUM','EXPERT',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(2,'AUTOMOTIVE','汽车电子',NULL,NULL,NULL,NULL,'LARGE','HIGH','EXPERT',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(3,'NEW_ENERGY','新能源',NULL,NULL,NULL,NULL,'LARGE','HIGH','EXPERIENCED',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(4,'HOME_APPLIANCE','家电',NULL,NULL,NULL,NULL,'LARGE','LOW','EXPERT',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(5,'MEDICAL_DEVICE','医疗器械',NULL,NULL,NULL,NULL,'MEDIUM','HIGH','LEARNING',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(6,'INDUSTRIAL_CONTROL','工业控制',NULL,NULL,NULL,NULL,'MEDIUM','MEDIUM','EXPERIENCED',6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(7,'SEMICONDUCTOR','半导体',NULL,NULL,NULL,NULL,'LARGE','HIGH','EXPERIENCED',7,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(8,'COMMUNICATION','通信设备',NULL,NULL,NULL,NULL,'LARGE','MEDIUM','EXPERIENCED',8,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(9,'POWER_TOOLS','电动工具',NULL,NULL,NULL,NULL,'MEDIUM','MEDIUM','EXPERT',9,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(10,'LIGHTING','照明',NULL,NULL,NULL,NULL,'MEDIUM','LOW','EXPERIENCED',10,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(11,'AEROSPACE','航空航天',NULL,NULL,NULL,NULL,'MEDIUM','HIGH','LEARNING',11,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(12,'MILITARY','军工',NULL,NULL,NULL,NULL,'MEDIUM','MEDIUM','LEARNING',12,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(13,'EDUCATION','教育科研',NULL,NULL,NULL,NULL,'SMALL','MEDIUM','EXPERIENCED',13,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(14,'OTHER','其他行业',NULL,NULL,NULL,NULL,'SMALL','LOW','LEARNING',99,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(15,'MOBILE_PHONE','手机',1,NULL,'["手机主板", "摄像头模组", "触摸屏", "电池"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(16,'TABLET','平板电脑',1,NULL,'["主板", "显示屏", "电池包"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(17,'LAPTOP','笔记本电脑',1,NULL,'["主板", "键盘", "电源适配器"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(18,'WEARABLE','可穿戴设备',1,NULL,'["智能手表", "TWS耳机", "手环"]',NULL,NULL,NULL,NULL,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(19,'CHARGER','充电器/适配器',1,NULL,'["充电器", "适配器", "充电宝"]',NULL,NULL,NULL,NULL,5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(20,'AUTO_ECU','ECU/控制器',2,NULL,'["域控制器", "BMS", "MCU", "VCU"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(21,'AUTO_SENSOR','汽车传感器',2,NULL,'["毫米波雷达", "激光雷达", "摄像头"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(22,'AUTO_MOTOR','汽车电机',2,NULL,'["驱动电机", "转向电机", "车窗电机"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(23,'AUTO_LIGHTING','汽车车灯',2,NULL,'["LED大灯", "尾灯", "转向灯"]',NULL,NULL,NULL,NULL,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(24,'AUTO_CHARGING','汽车充电',2,NULL,'["OBC", "DC-DC", "充电桩"]',NULL,NULL,NULL,NULL,5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(25,'BATTERY_PACK','动力电池',3,NULL,'["电芯", "模组", "PACK"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(26,'ENERGY_STORAGE','储能系统',3,NULL,'["储能电池", "BMS", "PCS"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(27,'PV_INVERTER','光伏逆变',3,NULL,'["逆变器", "优化器", "汇流箱"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(28,'CHARGING_PILE','充电桩',3,NULL,'["直流桩", "交流桩", "充电模块"]',NULL,NULL,NULL,NULL,4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(29,'WHITE_APPLIANCE','白色家电',4,NULL,'["空调", "冰箱", "洗衣机"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(30,'SMALL_APPLIANCE','小家电',4,NULL,'["电饭煲", "吸尘器", "破壁机"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(31,'KITCHEN_APPLIANCE','厨房电器',4,NULL,'["油烟机", "燃气灶", "消毒柜"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(32,'MEDICAL_MONITOR','监护设备',5,NULL,'["血压计", "血糖仪", "心电监护"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(33,'MEDICAL_IMAGING','影像设备',5,NULL,'["CT", "MRI", "超声"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(34,'IVD','体外诊断',5,NULL,'["生化分析仪", "免疫分析仪"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(35,'PLC_DCS','PLC/DCS',6,NULL,'["PLC", "DCS", "PAC"]',NULL,NULL,NULL,NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(36,'SERVO_DRIVE','伺服驱动',6,NULL,'["伺服驱动器", "伺服电机"]',NULL,NULL,NULL,NULL,2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industries VALUES(37,'FREQUENCY_CONVERTER','变频器',6,NULL,'["通用变频器", "专用变频器"]',NULL,NULL,NULL,NULL,3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE industry_category_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_id INTEGER NOT NULL REFERENCES industries(id),
    category_id INTEGER NOT NULL REFERENCES advantage_product_categories(id),
    match_score INTEGER DEFAULT 100,
    is_primary BOOLEAN DEFAULT 0,
    typical_scenarios TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO industry_category_mappings VALUES(1,1,1,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(2,15,1,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(3,19,1,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(4,2,2,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(5,20,2,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(6,21,2,90,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(7,3,3,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(8,25,3,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(9,26,3,95,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(10,28,3,90,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(11,4,1,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(12,29,1,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(13,30,1,95,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(14,7,4,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(15,9,5,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(16,13,8,100,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(17,1,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(18,2,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(19,3,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(20,4,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(21,5,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(22,6,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(23,7,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(24,8,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(25,9,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(26,10,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(27,11,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(28,12,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(29,13,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(30,14,6,60,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(31,1,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(32,2,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(33,3,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(34,4,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(35,5,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(36,6,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(37,7,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(38,8,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(39,9,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(40,10,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(41,11,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(42,12,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(43,13,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO industry_category_mappings VALUES(44,14,7,40,0,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE new_product_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    product_name VARCHAR(200) NOT NULL,
    product_type VARCHAR(100),
    industry_id INTEGER REFERENCES industries(id),
    category_id INTEGER REFERENCES advantage_product_categories(id),
    test_requirements TEXT,
    capacity_requirements TEXT,
    special_requirements TEXT,
    market_potential VARCHAR(50),
    similar_customers TEXT,
    estimated_annual_demand INTEGER,
    review_status VARCHAR(20) DEFAULT 'PENDING',
    reviewer_id INTEGER REFERENCES users(id),
    reviewed_at DATETIME,
    review_comment TEXT,
    converted_product_id INTEGER REFERENCES advantage_products(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE presale_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    lead_id INTEGER,
    opportunity_id INTEGER,
    expense_type VARCHAR(20) NOT NULL,
    expense_category VARCHAR(50) NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    labor_hours NUMERIC(10, 2),
    hourly_rate NUMERIC(10, 2),
    user_id INTEGER,
    user_name VARCHAR(50),
    department_id INTEGER,
    department_name VARCHAR(100),
    salesperson_id INTEGER,
    salesperson_name VARCHAR(50),
    expense_date DATE NOT NULL,
    description TEXT,
    loss_reason VARCHAR(50),
    loss_reason_detail TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (salesperson_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE solution_credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),

    -- 交易类型
    transaction_type VARCHAR(30) NOT NULL,
    -- INIT: 初始化积分
    -- GENERATE: 生成方案扣除
    -- ADMIN_ADD: 管理员充值
    -- ADMIN_DEDUCT: 管理员扣除
    -- SYSTEM_REWARD: 系统奖励
    -- REFUND: 退还（生成失败时）

    -- 积分变动
    amount INTEGER NOT NULL,              -- 变动数量（正数为增加，负数为减少）
    balance_before INTEGER NOT NULL,      -- 变动前余额
    balance_after INTEGER NOT NULL,       -- 变动后余额

    -- 关联信息
    related_type VARCHAR(50),             -- 关联对象类型（如 lead, solution 等）
    related_id INTEGER,                   -- 关联对象ID

    -- 操作信息
    operator_id INTEGER REFERENCES users(id),  -- 操作人ID（管理员充值时记录）
    remark TEXT,                          -- 备注说明

    -- 元数据
    ip_address VARCHAR(50),               -- 操作IP
    user_agent VARCHAR(500),              -- 用户代理

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE solution_credit_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO solution_credit_configs VALUES(1,'INITIAL_CREDITS','100','新用户初始积分',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO solution_credit_configs VALUES(2,'GENERATE_COST','10','每次生成方案消耗积分',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO solution_credit_configs VALUES(3,'MIN_CREDITS_TO_GENERATE','10','生成方案所需最低积分',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO solution_credit_configs VALUES(4,'DAILY_FREE_GENERATIONS','0','每日免费生成次数（0表示无免费）',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO solution_credit_configs VALUES(5,'MAX_CREDITS','9999','用户积分上限',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE approval_workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_type VARCHAR(20) NOT NULL,
    workflow_name VARCHAR(100) NOT NULL,
    description TEXT,
    routing_rules TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO approval_workflows VALUES(1,'PROJECT','项目审批工作流','项目创建或变更时的多级审批流程',NULL,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE approval_workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    approver_role VARCHAR(50),
    approver_id INTEGER,
    is_required BOOLEAN DEFAULT 1,
    can_delegate BOOLEAN DEFAULT 1,
    can_withdraw BOOLEAN DEFAULT 1,
    due_hours INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
);
INSERT INTO approval_workflow_steps VALUES(1,1,1,'部门经理审批','DEPT_MANAGER',NULL,1,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO approval_workflow_steps VALUES(2,1,2,'PMO审批','PMO_MANAGER',NULL,1,1,1,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE approval_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(20) NOT NULL,
    entity_id INTEGER NOT NULL,
    workflow_id INTEGER NOT NULL,
    current_step INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'PENDING',
    initiator_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE RESTRICT,
    FOREIGN KEY (initiator_id) REFERENCES users(id) ON DELETE RESTRICT
);
CREATE TABLE approval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_record_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    approver_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    comment TEXT,
    delegate_to_id INTEGER,
    action_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approval_record_id) REFERENCES approval_records(id) ON DELETE CASCADE,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (delegate_to_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE culture_wall_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    is_enabled BOOLEAN DEFAULT 1,
    is_default BOOLEAN DEFAULT 0,
    content_types TEXT,  -- JSON格式
    visible_roles TEXT,  -- JSON格式
    play_settings TEXT,  -- JSON格式
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES user(id)
);
CREATE TABLE ecn_bom_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id INTEGER NOT NULL,
    bom_version_id INTEGER,
    machine_id INTEGER,
    project_id INTEGER,
    affected_item_count INTEGER DEFAULT 0,
    total_cost_impact NUMERIC(14, 2) DEFAULT 0,
    schedule_impact_days INTEGER DEFAULT 0,
    impact_analysis TEXT,
    analysis_status VARCHAR(20) DEFAULT 'PENDING',
    analyzed_at DATETIME,
    analyzed_by INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (bom_version_id) REFERENCES bom_headers(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (analyzed_by) REFERENCES users(id)
);
CREATE TABLE ecn_responsibilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id INTEGER NOT NULL,
    dept VARCHAR(50) NOT NULL,
    responsibility_ratio NUMERIC(5, 2) DEFAULT 0,
    responsibility_type VARCHAR(20) DEFAULT 'PRIMARY',
    cost_allocation NUMERIC(14, 2) DEFAULT 0,
    impact_description TEXT,
    responsibility_scope TEXT,
    confirmed BOOLEAN DEFAULT 0,
    confirmed_by INTEGER,
    confirmed_at DATETIME,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id)
);
CREATE TABLE ecn_solution_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    template_category VARCHAR(50),
    ecn_type VARCHAR(20),
    root_cause_category VARCHAR(50),
    keywords TEXT,
    solution_description TEXT NOT NULL,
    solution_steps TEXT,
    required_resources TEXT,
    estimated_cost NUMERIC(14, 2),
    estimated_days INTEGER,
    success_rate NUMERIC(5, 2) DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    avg_cost_saving NUMERIC(14, 2),
    avg_time_saving INTEGER,
    source_ecn_id INTEGER,
    created_from VARCHAR(20) DEFAULT 'MANUAL',
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    verified_by INTEGER,
    verified_at DATETIME,
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_ecn_id) REFERENCES ecn(id),
    FOREIGN KEY (verified_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE performance_adjustment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,                              -- 绩效结果ID
    original_total_score DECIMAL(5,2),                       -- 原始综合得分
    original_dept_rank INTEGER,                                -- 原始部门排名
    original_company_rank INTEGER,                            -- 原始公司排名
    original_level VARCHAR(20),                              -- 原始等级
    adjusted_total_score DECIMAL(5,2),                       -- 调整后综合得分
    adjusted_dept_rank INTEGER,                               -- 调整后部门排名
    adjusted_company_rank INTEGER,                           -- 调整后公司排名
    adjusted_level VARCHAR(20),                               -- 调整后等级
    adjustment_reason TEXT NOT NULL,                         -- 调整理由（必填）
    adjusted_by INTEGER NOT NULL,                            -- 调整人ID
    adjusted_by_name VARCHAR(50),                            -- 调整人姓名
    adjusted_at DATETIME DEFAULT CURRENT_TIMESTAMP,          -- 调整时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES performance_result(id),
    FOREIGN KEY (adjusted_by) REFERENCES users(id)
);
CREATE TABLE financial_project_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    project_code VARCHAR(50),
    project_name VARCHAR(200),
    machine_id INTEGER,
    cost_type VARCHAR(50) NOT NULL,
    cost_category VARCHAR(50) NOT NULL,
    cost_item VARCHAR(200),
    amount DECIMAL(14, 2) NOT NULL,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'CNY',
    cost_date DATE NOT NULL,
    cost_month VARCHAR(7),
    description TEXT,
    location VARCHAR(200),
    participants VARCHAR(500),
    purpose VARCHAR(500),
    user_id INTEGER,
    user_name VARCHAR(50),
    hours DECIMAL(10, 2),
    hourly_rate DECIMAL(10, 2),
    source_type VARCHAR(50) DEFAULT 'FINANCIAL_UPLOAD',
    source_no VARCHAR(100),
    invoice_no VARCHAR(100),
    upload_batch_no VARCHAR(50),
    uploaded_by INTEGER NOT NULL,
    is_verified BOOLEAN DEFAULT 0,
    verified_by INTEGER,
    verified_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id),
    FOREIGN KEY (verified_by) REFERENCES users(id)
);
CREATE TABLE organization_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_code VARCHAR(50) UNIQUE NOT NULL,           -- 组织编码
    unit_name VARCHAR(100) NOT NULL,                 -- 组织名称
    unit_type VARCHAR(20) NOT NULL,                  -- 类型: COMPANY/BUSINESS_UNIT/DEPARTMENT/TEAM
    parent_id INTEGER,                               -- 上级组织ID
    manager_id INTEGER,                              -- 负责人ID (employee_id)
    level INTEGER DEFAULT 1,                         -- 层级深度
    path VARCHAR(500),                               -- 路径 (如: /1/3/5/)
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES organization_units(id)
);
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_code VARCHAR(50) UNIQUE NOT NULL,       -- 岗位编码
    position_name VARCHAR(100) NOT NULL,             -- 岗位名称
    position_category VARCHAR(20) NOT NULL,          -- 类别: MANAGEMENT/TECHNICAL/SUPPORT/SALES/PRODUCTION
    org_unit_id INTEGER,                             -- 所属组织单元ID
    description TEXT,                                -- 岗位描述
    responsibilities TEXT,                           -- 岗位职责 (JSON)
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    sort_order INTEGER DEFAULT 0,                    -- 排序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id)
);
CREATE TABLE job_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_code VARCHAR(20) UNIQUE NOT NULL,          -- 职级编码 (如 P1-P10, M1-M5)
    level_name VARCHAR(50) NOT NULL,                 -- 职级名称
    level_category VARCHAR(10) NOT NULL,             -- 序列: P(专业)/M(管理)/T(技术)
    level_rank INTEGER NOT NULL,                     -- 职级数值 (用于比较)
    description TEXT,                                -- 职级描述
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    sort_order INTEGER DEFAULT 0,                    -- 排序
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO job_levels VALUES(1,'P1','助理','P',1,'入门级专业人员',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(2,'P2','初级专员','P',2,'初级专业人员',1,2,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(3,'P3','专员','P',3,'独立工作的专业人员',1,3,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(4,'P4','高级专员','P',4,'高级专业人员',1,4,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(5,'P5','资深专员','P',5,'资深专业人员',1,5,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(6,'P6','专家','P',6,'领域专家',1,6,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(7,'P7','高级专家','P',7,'高级领域专家',1,7,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(8,'P8','资深专家','P',8,'资深领域专家',1,8,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(9,'P9','首席专家','P',9,'首席专家',1,9,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(10,'P10','科学家/Fellow','P',10,'顶级专家',1,10,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(11,'M1','主管','M',11,'基层管理者',1,11,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(12,'M2','经理','M',12,'部门经理',1,12,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(13,'M3','高级经理','M',13,'高级经理',1,13,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(14,'M4','总监','M',14,'部门总监',1,14,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(15,'M5','副总裁/VP','M',15,'副总裁级别',1,15,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(16,'M6','高级副总裁/SVP','M',16,'高级副总裁',1,16,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(17,'T1','技术员','T',1,'初级技术人员',1,21,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(18,'T2','助理工程师','T',2,'助理工程师',1,22,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(19,'T3','工程师','T',3,'工程师',1,23,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(20,'T4','高级工程师','T',4,'高级工程师',1,24,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(21,'T5','资深工程师','T',5,'资深工程师',1,25,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(22,'T6','技术专家','T',6,'技术专家',1,26,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(23,'T7','高级技术专家','T',7,'高级技术专家',1,27,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO job_levels VALUES(24,'T8','首席技术专家','T',8,'首席技术专家',1,28,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE employee_org_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,                    -- 员工ID
    org_unit_id INTEGER NOT NULL,                    -- 组织单元ID
    position_id INTEGER,                             -- 岗位ID
    job_level_id INTEGER,                            -- 职级ID
    is_primary BOOLEAN DEFAULT 1,                    -- 是否主要归属
    assignment_type VARCHAR(20) DEFAULT 'PERMANENT', -- 分配类型: PERMANENT/TEMPORARY/PROJECT
    start_date DATE,                                 -- 开始日期
    end_date DATE,                                   -- 结束日期
    is_active BOOLEAN DEFAULT 1,                     -- 是否有效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (org_unit_id) REFERENCES organization_units(id),
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (job_level_id) REFERENCES job_levels(id)
);
CREATE TABLE position_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,                    -- 岗位ID
    role_id INTEGER NOT NULL,                        -- 角色ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
CREATE TABLE data_scope_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) UNIQUE NOT NULL,           -- 规则编码
    rule_name VARCHAR(100) NOT NULL,                 -- 规则名称
    scope_type VARCHAR(20) NOT NULL,                 -- 范围类型: ALL/BUSINESS_UNIT/DEPARTMENT/TEAM/PROJECT/OWN/CUSTOM
    scope_config TEXT,                               -- 范围配置 (JSON, 自定义规则时使用)
    description TEXT,                                -- 规则描述
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO data_scope_rules VALUES(1,'ALL','全部数据','ALL',NULL,'可访问所有数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO data_scope_rules VALUES(2,'BUSINESS_UNIT','本事业部数据','BUSINESS_UNIT',NULL,'可访问本事业部及下属组织的数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO data_scope_rules VALUES(3,'DEPARTMENT','本部门数据','DEPARTMENT',NULL,'可访问本部门及下属团队的数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO data_scope_rules VALUES(4,'TEAM','本团队数据','TEAM',NULL,'可访问本团队的数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO data_scope_rules VALUES(5,'PROJECT','参与项目数据','PROJECT',NULL,'可访问参与的项目相关数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO data_scope_rules VALUES(6,'OWN','仅个人数据','OWN',NULL,'仅可访问自己创建或负责的数据',1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE role_data_scopes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,                        -- 角色ID
    resource_type VARCHAR(50) NOT NULL,              -- 资源类型 (project/customer/employee等)
    scope_rule_id INTEGER NOT NULL,                  -- 数据权限规则ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (scope_rule_id) REFERENCES data_scope_rules(id)
);
CREATE TABLE permission_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_code VARCHAR(50) UNIQUE NOT NULL,          -- 分组编码
    group_name VARCHAR(100) NOT NULL,                -- 分组名称
    parent_id INTEGER,                               -- 父分组ID
    description TEXT,                                -- 分组描述
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES permission_groups(id)
);
INSERT INTO permission_groups VALUES(1,'system','系统管理',NULL,'系统管理相关权限',1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(2,'org','组织管理',NULL,'组织架构、岗位、职级管理',2,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(3,'project','项目管理',NULL,'项目相关权限',3,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(4,'sales','销售管理',NULL,'销售相关权限',4,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(5,'procurement','采购管理',NULL,'采购相关权限',5,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(6,'production','生产管理',NULL,'生产制造相关权限',6,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(7,'finance','财务管理',NULL,'财务相关权限',7,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(8,'hr','人力资源',NULL,'人力资源相关权限',8,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO permission_groups VALUES(9,'service','售后服务',NULL,'售后服务相关权限',9,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE menu_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_code VARCHAR(50) UNIQUE NOT NULL,           -- 菜单编码
    menu_name VARCHAR(100) NOT NULL,                 -- 菜单名称
    menu_path VARCHAR(200),                          -- 前端路由路径
    menu_icon VARCHAR(50),                           -- 菜单图标
    parent_id INTEGER,                               -- 父菜单ID
    menu_type VARCHAR(20) NOT NULL,                  -- 类型: DIRECTORY/MENU/BUTTON
    permission_id INTEGER,                           -- 关联的API权限ID (可选)
    sort_order INTEGER DEFAULT 0,                    -- 排序
    is_visible BOOLEAN DEFAULT 1,                    -- 是否可见
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES menu_permissions(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);
CREATE TABLE role_menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,                        -- 角色ID
    menu_id INTEGER NOT NULL,                        -- 菜单ID
    is_active BOOLEAN DEFAULT 1,                     -- 是否启用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (menu_id) REFERENCES menu_permissions(id)
);
CREATE TABLE material_cost_update_reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reminder_type VARCHAR(50) DEFAULT 'PERIODIC',
    reminder_interval_days INTEGER DEFAULT 30,
    last_reminder_date DATE,
    next_reminder_date DATE,
    is_enabled BOOLEAN DEFAULT 1,
    material_type_filter VARCHAR(50),
    include_standard BOOLEAN DEFAULT 1,
    include_non_standard BOOLEAN DEFAULT 1,
    notify_roles TEXT,
    notify_users TEXT,
    reminder_count INTEGER DEFAULT 0,
    last_updated_by INTEGER,
    last_updated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (last_updated_by) REFERENCES users(id)
);
INSERT INTO material_cost_update_reminders VALUES(1,'PERIODIC',30,NULL,'2026-02-27',1,NULL,1,1,'["procurement", "procurement_manager", "采购工程师", "采购专员", "采购部经理"]',NULL,0,NULL,NULL,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE pipeline_break_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    break_stage VARCHAR(20) NOT NULL,
    break_reason VARCHAR(100),
    break_date DATE NOT NULL,
    responsible_person_id INTEGER,
    responsible_department VARCHAR(50),
    cost_impact DECIMAL(14,2),
    opportunity_cost DECIMAL(14,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);
CREATE TABLE pipeline_health_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    health_status VARCHAR(10) NOT NULL,
    health_score INT,
    risk_factors TEXT,
    snapshot_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE accountability_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id VARCHAR(50) NOT NULL,
    pipeline_type VARCHAR(20) NOT NULL,
    issue_type VARCHAR(50) NOT NULL,
    responsible_person_id INTEGER NOT NULL,
    responsible_department VARCHAR(50),
    responsibility_ratio DECIMAL(5,2),
    cost_impact DECIMAL(14,2),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);
CREATE TABLE purchase_material_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code VARCHAR(50),
    material_name VARCHAR(200) NOT NULL,
    specification VARCHAR(500),
    brand VARCHAR(100),
    unit VARCHAR(20) DEFAULT '件',
    material_type VARCHAR(50),
    is_standard_part BOOLEAN DEFAULT 1,
    unit_cost DECIMAL(12, 4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    supplier_id INTEGER,
    supplier_name VARCHAR(200),
    purchase_date DATE,
    purchase_order_no VARCHAR(50),
    purchase_quantity DECIMAL(10, 4),
    lead_time_days INTEGER,
    is_active BOOLEAN DEFAULT 1,
    match_priority INTEGER DEFAULT 0,
    match_keywords TEXT,
    usage_count INTEGER DEFAULT 0,
    last_used_at DATETIME,
    remark TEXT,
    submitted_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (submitted_by) REFERENCES users(id)
);
CREATE TABLE quote_cost_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50),
    equipment_type VARCHAR(50),
    industry VARCHAR(50),
    cost_structure TEXT,  -- JSON格式
    total_cost DECIMAL(12, 2),
    cost_categories TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE quote_cost_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    quote_version_id INTEGER NOT NULL,
    approval_status VARCHAR(20) DEFAULT 'PENDING',
    approval_level INTEGER DEFAULT 1,
    current_approver_id INTEGER,
    total_price DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    gross_margin DECIMAL(5, 2),
    margin_threshold DECIMAL(5, 2) DEFAULT 20.00,
    margin_status VARCHAR(20),
    cost_complete BOOLEAN DEFAULT 0,
    delivery_check BOOLEAN DEFAULT 0,
    risk_terms_check BOOLEAN DEFAULT 0,
    approval_comment TEXT,
    approved_by INTEGER,
    approved_at DATETIME,
    rejected_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (current_approver_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE quote_cost_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL,
    quote_version_id INTEGER NOT NULL,
    total_price DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    gross_margin DECIMAL(5, 2),
    cost_breakdown TEXT,  -- JSON格式
    change_type VARCHAR(50),
    change_reason TEXT,
    changed_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quote_id) REFERENCES quotes(id),
    FOREIGN KEY (quote_version_id) REFERENCES quote_versions(id),
    FOREIGN KEY (changed_by) REFERENCES users(id)
);
CREATE TABLE technical_reviews (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_no           VARCHAR(50) NOT NULL UNIQUE,              -- 评审编号：RV-PDR-202501-0001
    review_type         VARCHAR(20) NOT NULL,                      -- 评审类型：PDR/DDR/PRR/FRR/ARR
    review_name         VARCHAR(200) NOT NULL,                     -- 评审名称
    
    -- 关联项目
    project_id          INTEGER NOT NULL,                          -- 关联项目ID
    project_no          VARCHAR(50) NOT NULL,                      -- 项目编号
    equipment_id        INTEGER,                                   -- 关联设备ID（多设备项目）
    
    -- 评审基本信息
    status              VARCHAR(20) NOT NULL DEFAULT 'DRAFT',     -- 状态：draft/pending/in_progress/completed/cancelled
    scheduled_date      DATETIME NOT NULL,                         -- 计划评审时间
    actual_date         DATETIME,                                  -- 实际评审时间
    location            VARCHAR(200),                               -- 评审地点
    meeting_type        VARCHAR(20) NOT NULL DEFAULT 'ONSITE',     -- 会议形式：onsite/online/hybrid
    
    -- 评审人员
    host_id             INTEGER NOT NULL,                          -- 主持人ID
    presenter_id        INTEGER NOT NULL,                           -- 汇报人ID
    recorder_id         INTEGER NOT NULL,                          -- 记录人ID
    
    -- 评审结论
    conclusion          VARCHAR(30),                              -- 评审结论：pass/pass_with_condition/reject/abort
    conclusion_summary  TEXT,                                      -- 结论说明
    condition_deadline  DATE,                                      -- 有条件通过的整改期限
    next_review_date    DATE,                                      -- 下次复审日期
    
    -- 问题统计
    issue_count_a       INTEGER DEFAULT 0,                         -- A类问题数
    issue_count_b       INTEGER DEFAULT 0,                         -- B类问题数
    issue_count_c       INTEGER DEFAULT 0,                         -- C类问题数
    issue_count_d       INTEGER DEFAULT 0,                          -- D类问题数
    
    -- 创建人
    created_by          INTEGER NOT NULL,                          -- 创建人
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (equipment_id) REFERENCES machines(id),
    FOREIGN KEY (host_id) REFERENCES users(id),
    FOREIGN KEY (presenter_id) REFERENCES users(id),
    FOREIGN KEY (recorder_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE review_participants (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    user_id             INTEGER NOT NULL,                          -- 用户ID
    role                VARCHAR(20) NOT NULL,                      -- 角色：host/expert/presenter/recorder/observer
    is_required         BOOLEAN NOT NULL DEFAULT 1,                -- 是否必须参与
    
    -- 出席信息
    attendance          VARCHAR(20),                              -- 出席状态：pending/confirmed/absent/delegated
    delegate_id         INTEGER,                                   -- 代理人ID（请假时）
    sign_time           DATETIME,                                  -- 签到时间
    signature           VARCHAR(500),                              -- 电子签名
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (delegate_id) REFERENCES users(id)
);
CREATE TABLE review_materials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    material_type       VARCHAR(20) NOT NULL,                      -- 材料类型：drawing/bom/report/document/other
    material_name       VARCHAR(200) NOT NULL,                     -- 材料名称
    file_path           VARCHAR(500) NOT NULL,                     -- 文件路径
    file_size           BIGINT NOT NULL,                           -- 文件大小（字节）
    version             VARCHAR(20),                               -- 版本号
    is_required         BOOLEAN NOT NULL DEFAULT 1,                -- 是否必须材料
    upload_by           INTEGER NOT NULL,                          -- 上传人
    upload_at           DATETIME DEFAULT CURRENT_TIMESTAMP,        -- 上传时间
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_by) REFERENCES users(id)
);
CREATE TABLE review_checklist_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    checklist_item_id  INTEGER,                                  -- 检查项ID（关联模板，可为空）
    category            VARCHAR(50) NOT NULL,                      -- 检查类别
    check_item          VARCHAR(500) NOT NULL,                     -- 检查项内容
    result              VARCHAR(20) NOT NULL,                      -- 检查结果：pass/fail/na
    
    -- 问题信息（不通过时）
    issue_level         VARCHAR(10),                               -- 问题等级：A/B/C/D（不通过时）
    issue_desc          TEXT,                                      -- 问题描述
    issue_id            INTEGER,                                   -- 关联问题ID（自动创建的问题）
    
    checker_id          INTEGER NOT NULL,                         -- 检查人ID
    remark              VARCHAR(500),                              -- 备注
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (issue_id) REFERENCES review_issues(id),
    FOREIGN KEY (checker_id) REFERENCES users(id)
);
CREATE TABLE review_issues (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id           INTEGER NOT NULL,                          -- 评审ID
    issue_no            VARCHAR(50) NOT NULL UNIQUE,                -- 问题编号：RV-ISSUE-202501-0001
    issue_level         VARCHAR(10) NOT NULL,                      -- 问题等级：A/B/C/D
    category            VARCHAR(50) NOT NULL,                       -- 问题类别
    description         TEXT NOT NULL,                             -- 问题描述
    suggestion          TEXT,                                      -- 改进建议
    
    -- 责任与期限
    assignee_id         INTEGER NOT NULL,                          -- 责任人ID
    deadline            DATE NOT NULL,                              -- 整改期限
    
    -- 状态与处理
    status              VARCHAR(20) NOT NULL DEFAULT 'OPEN',        -- 状态：open/processing/resolved/verified/closed
    solution            TEXT,                                      -- 解决方案
    
    -- 验证信息
    verify_result       VARCHAR(20),                               -- 验证结果：pass/fail
    verifier_id         INTEGER,                                   -- 验证人
    verify_time         DATETIME,                                  -- 验证时间
    
    -- 关联
    linked_issue_id     INTEGER,                                   -- 关联问题管理系统ID
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (review_id) REFERENCES technical_reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (verifier_id) REFERENCES users(id)
);
CREATE TABLE technical_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    evaluator_id INTEGER,
    status VARCHAR(20) DEFAULT 'PENDING',
    total_score INTEGER,
    dimension_scores TEXT,
    veto_triggered BOOLEAN DEFAULT 0,
    veto_rules TEXT,
    decision VARCHAR(30),
    risks TEXT,
    similar_cases TEXT,
    ai_analysis TEXT,
    conditions TEXT,
    evaluated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE scoring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version VARCHAR(20) UNIQUE NOT NULL,
    rules_json TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 0,
    description TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE failure_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    industry VARCHAR(50) NOT NULL,
    product_types TEXT,
    processes TEXT,
    takt_time_s INTEGER,
    annual_volume INTEGER,
    budget_status VARCHAR(50),
    customer_project_status VARCHAR(50),
    spec_status VARCHAR(50),
    price_sensitivity VARCHAR(50),
    delivery_months INTEGER,
    failure_tags TEXT NOT NULL,
    core_failure_reason TEXT NOT NULL,
    early_warning_signals TEXT NOT NULL,
    final_result VARCHAR(100),
    lesson_learned TEXT NOT NULL,
    keywords TEXT NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE lead_requirement_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    customer_factory_location VARCHAR(200),
    target_object_type VARCHAR(100),
    application_scenario VARCHAR(100),
    delivery_mode VARCHAR(100),
    expected_delivery_date DATETIME,
    requirement_source VARCHAR(100),
    participant_ids TEXT,
    requirement_maturity INTEGER,
    has_sow BOOLEAN,
    has_interface_doc BOOLEAN,
    has_drawing_doc BOOLEAN,
    sample_availability TEXT,
    customer_support_resources TEXT,
    key_risk_factors TEXT,
    veto_triggered BOOLEAN DEFAULT 0,
    veto_reason TEXT,
    target_capacity_uph DECIMAL(10,2),
    target_capacity_daily DECIMAL(10,2),
    target_capacity_shift DECIMAL(10,2),
    cycle_time_seconds DECIMAL(10,2),
    workstation_count INTEGER,
    changeover_method VARCHAR(100),
    yield_target DECIMAL(5,2),
    retest_allowed BOOLEAN,
    retest_max_count INTEGER,
    traceability_type VARCHAR(50),
    data_retention_period INTEGER,
    data_format VARCHAR(100),
    test_scope TEXT,
    key_metrics_spec TEXT,
    coverage_boundary TEXT,
    exception_handling TEXT,
    acceptance_method VARCHAR(100),
    acceptance_basis TEXT,
    delivery_checklist TEXT,
    interface_types TEXT,
    io_point_estimate TEXT,
    communication_protocols TEXT,
    upper_system_integration TEXT,
    data_field_list TEXT,
    it_security_restrictions TEXT,
    power_supply TEXT,
    air_supply TEXT,
    environment TEXT,
    safety_requirements TEXT,
    space_and_logistics TEXT,
    customer_site_standards TEXT,
    customer_supplied_materials TEXT,
    restricted_brands TEXT,
    specified_brands TEXT,
    long_lead_items TEXT,
    spare_parts_requirement TEXT,
    after_sales_support TEXT,
    requirement_version VARCHAR(50),
    is_frozen BOOLEAN DEFAULT 0,
    frozen_at DATETIME,
    frozen_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (frozen_by) REFERENCES users(id)
);
CREATE TABLE requirement_freezes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    freeze_type VARCHAR(50) NOT NULL,
    freeze_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    frozen_by INTEGER NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    requires_ecr BOOLEAN DEFAULT 1,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (frozen_by) REFERENCES users(id)
);
CREATE TABLE open_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    responsible_party VARCHAR(50) NOT NULL,
    responsible_person_id INTEGER,
    due_date DATETIME,
    status VARCHAR(20) DEFAULT 'PENDING',
    close_evidence TEXT,
    blocks_quotation BOOLEAN DEFAULT 0,
    closed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);
CREATE TABLE ai_clarifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(20) NOT NULL,
    source_id INTEGER NOT NULL,
    round INTEGER NOT NULL,
    questions TEXT NOT NULL,
    answers TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE bonus_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code VARCHAR(50) UNIQUE NOT NULL,           -- 规则编码
    rule_name VARCHAR(200) NOT NULL,                 -- 规则名称
    bonus_type VARCHAR(20) NOT NULL,                 -- 奖金类型
    calculation_formula TEXT,                        -- 计算公式说明
    base_amount DECIMAL(14, 2),                      -- 基础金额
    coefficient DECIMAL(5, 2),                       -- 系数
    trigger_condition TEXT,                         -- 触发条件(JSON)
    apply_to_roles TEXT,                             -- 适用角色列表(JSON)
    apply_to_depts TEXT,                             -- 适用部门列表(JSON)
    apply_to_projects TEXT,                          -- 适用项目类型列表(JSON)
    effective_start_date DATE,                       -- 生效开始日期
    effective_end_date DATE,                         -- 生效结束日期
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    priority INTEGER DEFAULT 0,                      -- 优先级
    require_approval BOOLEAN DEFAULT 1,               -- 是否需要审批
    approval_workflow TEXT,                          -- 审批流程(JSON)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE bonus_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_code VARCHAR(50) UNIQUE NOT NULL,    -- 计算单号
    rule_id INTEGER NOT NULL,                        -- 规则ID
    period_id INTEGER,                                -- 考核周期ID（绩效奖金）
    project_id INTEGER,                              -- 项目ID（项目奖金）
    milestone_id INTEGER,                            -- 里程碑ID（里程碑奖金）
    user_id INTEGER NOT NULL,                        -- 受益人ID
    performance_result_id INTEGER,                   -- 绩效结果ID
    project_contribution_id INTEGER,                 -- 项目贡献ID
    calculation_basis TEXT,                           -- 计算依据详情(JSON)
    calculated_amount DECIMAL(14, 2) NOT NULL,       -- 计算金额
    calculation_detail TEXT,                          -- 计算明细(JSON)
    status VARCHAR(20) DEFAULT 'CALCULATED',         -- 状态
    approved_by INTEGER,                              -- 审批人
    approved_at DATETIME,                             -- 审批时间
    approval_comment TEXT,                            -- 审批意见
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 计算时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES bonus_rules(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (milestone_id) REFERENCES project_milestones(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (performance_result_id) REFERENCES performance_result(id),
    FOREIGN KEY (project_contribution_id) REFERENCES project_contribution(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE bonus_distributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    distribution_code VARCHAR(50) UNIQUE NOT NULL,   -- 发放单号
    calculation_id INTEGER NOT NULL,                 -- 计算记录ID
    user_id INTEGER NOT NULL,                        -- 受益人ID
    distributed_amount DECIMAL(14, 2) NOT NULL,      -- 发放金额
    distribution_date DATE NOT NULL,                  -- 发放日期
    payment_method VARCHAR(20),                       -- 发放方式
    status VARCHAR(20) DEFAULT 'PENDING',            -- 状态
    voucher_no VARCHAR(50),                           -- 凭证号
    payment_account VARCHAR(100),                     -- 付款账户
    payment_remark TEXT,                              -- 付款备注
    paid_by INTEGER,                                  -- 发放人
    paid_at DATETIME,                                 -- 发放时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calculation_id) REFERENCES bonus_calculations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (paid_by) REFERENCES users(id)
);
CREATE TABLE team_bonus_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                      -- 项目ID
    period_id INTEGER,                                 -- 周期ID
    total_bonus_amount DECIMAL(14, 2) NOT NULL,       -- 团队总奖金
    allocation_method VARCHAR(20),                     -- 分配方式
    allocation_detail TEXT,                            -- 分配明细(JSON)
    status VARCHAR(20) DEFAULT 'PENDING',             -- 状态
    approved_by INTEGER,                               -- 审批人
    approved_at DATETIME,                              -- 审批时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (period_id) REFERENCES performance_period(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);
CREATE TABLE project_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_code VARCHAR(50) UNIQUE NOT NULL,    -- 评价编号
    project_id INTEGER NOT NULL,                    -- 项目ID
    
    -- 评价维度得分（1-10分）
    novelty_score DECIMAL(3, 1),                    -- 项目新旧得分
    new_tech_score DECIMAL(3, 1),                   -- 新技术得分
    difficulty_score DECIMAL(3, 1),                 -- 项目难度得分
    workload_score DECIMAL(3, 1),                   -- 项目工作量得分
    amount_score DECIMAL(3, 1),                     -- 项目金额得分
    
    -- 综合评价
    total_score DECIMAL(5, 2),                      -- 综合得分
    evaluation_level VARCHAR(20),                   -- 评价等级：S/A/B/C/D
    
    -- 评价详情
    evaluation_detail TEXT,                         -- 评价详情(JSON)
    weights TEXT,                                    -- 权重配置(JSON)
    
    -- 评价人
    evaluator_id INTEGER NOT NULL,                  -- 评价人ID
    evaluator_name VARCHAR(50),                     -- 评价人姓名
    evaluation_date DATE NOT NULL,                  -- 评价日期
    
    -- 评价说明
    evaluation_note TEXT,                            -- 评价说明
    
    -- 状态
    status VARCHAR(20) DEFAULT 'DRAFT',             -- 状态
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);
CREATE TABLE project_evaluation_dimensions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dimension_code VARCHAR(50) UNIQUE NOT NULL,     -- 维度编码
    dimension_name VARCHAR(100) NOT NULL,            -- 维度名称
    dimension_type VARCHAR(20) NOT NULL,              -- 维度类型
    scoring_rules TEXT,                              -- 评分规则(JSON)
    default_weight DECIMAL(5, 2),                    -- 默认权重(%)
    calculation_method VARCHAR(20) DEFAULT 'MANUAL', -- 计算方式
    auto_calculation_rule TEXT,                      -- 自动计算规则(JSON)
    is_active BOOLEAN DEFAULT 1,                      -- 是否启用
    sort_order INTEGER DEFAULT 0,                     -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO project_evaluation_dimensions VALUES(1,'NOVELTY','项目新旧','NOVELTY','{"ranges": [{"min": 1, "max": 3, "label": "全新项目", "description": "从未做过类似项目"}, {"min": 4, "max": 6, "label": "类似项目", "description": "做过类似项目"}, {"min": 7, "max": 9, "label": "标准项目", "description": "做过多次"}, {"min": 10, "max": 10, "label": "完全标准", "description": "完全标准项目"}]}',15,'HYBRID',NULL,1,1,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_evaluation_dimensions VALUES(2,'NEW_TECH','新技术','NEW_TECH','{"ranges": [{"min": 1, "max": 3, "label": "大量新技术", "description": "技术风险高"}, {"min": 4, "max": 6, "label": "部分新技术", "description": "有一定风险"}, {"min": 7, "max": 9, "label": "少量新技术", "description": "风险可控"}, {"min": 10, "max": 10, "label": "无新技术", "description": "成熟技术"}]}',20,'MANUAL',NULL,1,2,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_evaluation_dimensions VALUES(3,'DIFFICULTY','项目难度','DIFFICULTY','{"ranges": [{"min": 1, "max": 3, "label": "极高难度", "description": "技术挑战极大"}, {"min": 4, "max": 6, "label": "高难度", "description": "技术挑战大"}, {"min": 7, "max": 8, "label": "中等难度", "description": "技术挑战一般"}, {"min": 9, "max": 10, "label": "低难度", "description": "技术挑战小"}]}',30,'MANUAL',NULL,1,3,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_evaluation_dimensions VALUES(4,'WORKLOAD','项目工作量','WORKLOAD','{"ranges": [{"min": 1, "max": 3, "label": "工作量极大", "description": ">1000人天"}, {"min": 4, "max": 6, "label": "工作量大", "description": "500-1000人天"}, {"min": 7, "max": 8, "label": "工作量中等", "description": "200-500人天"}, {"min": 9, "max": 10, "label": "工作量小", "description": "<200人天"}]}',20,'MANUAL',NULL,1,4,'2026-01-28 06:47:10','2026-01-28 06:47:10');
INSERT INTO project_evaluation_dimensions VALUES(5,'AMOUNT','项目金额','AMOUNT','{"ranges": [{"min": 1, "max": 3, "label": "超大项目", "description": ">500万"}, {"min": 4, "max": 6, "label": "大项目", "description": "200-500万"}, {"min": 7, "max": 8, "label": "中等项目", "description": "50-200万"}, {"min": 9, "max": 10, "label": "小项目", "description": "<50万"}]}',15,'AUTO',NULL,1,5,'2026-01-28 06:47:10','2026-01-28 06:47:10');
CREATE TABLE investors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_code VARCHAR(50) NOT NULL UNIQUE,
    investor_name VARCHAR(200) NOT NULL,
    investor_type VARCHAR(20) NOT NULL,
    
    -- 基本信息
    legal_name VARCHAR(200),
    registration_no VARCHAR(100),
    country VARCHAR(50) DEFAULT '中国',
    region VARCHAR(50),
    address VARCHAR(500),
    
    -- 联系信息
    contact_person VARCHAR(50),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    website VARCHAR(200),
    
    -- 投资信息
    investment_focus TEXT,
    investment_stage VARCHAR(100),
    typical_ticket_size DECIMAL(15, 2),
    portfolio_companies TEXT,
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,
    is_lead_investor BOOLEAN DEFAULT 0,
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE funding_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_code VARCHAR(50) NOT NULL UNIQUE,
    round_name VARCHAR(100) NOT NULL,
    round_type VARCHAR(20) NOT NULL,
    round_order INTEGER NOT NULL,
    
    -- 融资信息
    target_amount DECIMAL(15, 2) NOT NULL,
    actual_amount DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'CNY',
    valuation_pre DECIMAL(15, 2),
    valuation_post DECIMAL(15, 2),
    
    -- 时间信息
    launch_date DATE,
    closing_date DATE,
    expected_closing_date DATE,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNING',
    
    -- 负责人
    lead_investor_id INTEGER,
    lead_investor_name VARCHAR(200),
    responsible_person_id INTEGER,
    responsible_person_name VARCHAR(50),
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (lead_investor_id) REFERENCES investors(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);
CREATE TABLE funding_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_code VARCHAR(50) NOT NULL UNIQUE,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    investor_id INTEGER NOT NULL,
    
    -- 投资信息
    investment_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    share_percentage DECIMAL(8, 4),
    share_count DECIMAL(15, 2),
    price_per_share DECIMAL(10, 4),
    
    -- 时间信息
    commitment_date DATE,
    payment_date DATE,
    actual_payment_date DATE,
    
    -- 付款信息
    payment_method VARCHAR(20),
    payment_status VARCHAR(20) DEFAULT 'PENDING',
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    remaining_amount DECIMAL(15, 2),
    
    -- 合同信息
    contract_no VARCHAR(100),
    contract_date DATE,
    contract_file VARCHAR(500),
    
    -- 状态
    status VARCHAR(20) DEFAULT 'COMMITTED',
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);
CREATE TABLE equity_structures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    investor_id INTEGER,
    
    -- 股东信息
    shareholder_name VARCHAR(200) NOT NULL,
    shareholder_type VARCHAR(20) NOT NULL,
    
    -- 股权信息
    share_percentage DECIMAL(8, 4) NOT NULL,
    share_count DECIMAL(15, 2),
    share_class VARCHAR(20),
    
    -- 时间信息
    effective_date DATE NOT NULL,
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);
CREATE TABLE funding_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    funding_round_id INTEGER NOT NULL,
    
    -- 用途信息
    usage_category VARCHAR(50) NOT NULL,
    usage_item VARCHAR(200) NOT NULL,
    planned_amount DECIMAL(15, 2) NOT NULL,
    actual_amount DECIMAL(15, 2) DEFAULT 0,
    percentage DECIMAL(5, 2),
    
    -- 时间信息
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- 状态
    status VARCHAR(20) DEFAULT 'PLANNED',
    
    -- 负责人
    responsible_person_id INTEGER,
    responsible_person_name VARCHAR(50),
    
    -- 备注
    description TEXT,
    notes TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funding_round_id) REFERENCES funding_rounds(id),
    FOREIGN KEY (responsible_person_id) REFERENCES users(id)
);
CREATE TABLE mes_kit_rate_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 快照对象
    project_id INTEGER NOT NULL REFERENCES projects(id),
    machine_id INTEGER REFERENCES machines(id),

    -- 快照时间
    snapshot_date DATE NOT NULL,
    snapshot_time DATETIME NOT NULL,

    -- 快照来源
    snapshot_type VARCHAR(20) NOT NULL DEFAULT 'DAILY',  -- DAILY/STAGE_CHANGE/MANUAL
    trigger_event VARCHAR(100),

    -- 齐套率数据
    kit_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    kit_status VARCHAR(20) NOT NULL DEFAULT 'shortage',  -- complete/partial/shortage

    -- 物料统计
    total_items INTEGER DEFAULT 0,
    fulfilled_items INTEGER DEFAULT 0,
    shortage_items INTEGER DEFAULT 0,
    in_transit_items INTEGER DEFAULT 0,

    -- 阻塞性物料统计
    blocking_total INTEGER DEFAULT 0,
    blocking_fulfilled INTEGER DEFAULT 0,
    blocking_kit_rate DECIMAL(5,2) DEFAULT 0,

    -- 金额统计
    total_amount DECIMAL(14,2) DEFAULT 0,
    shortage_amount DECIMAL(14,2) DEFAULT 0,

    -- 项目阶段信息
    project_stage VARCHAR(20),
    project_health VARCHAR(10),

    -- 分阶段齐套率
    stage_kit_rates TEXT
, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
INSERT INTO mes_kit_rate_snapshot VALUES(1,1,NULL,'2026-01-30','2026-01-30 16:10:13.959677','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S1','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
INSERT INTO mes_kit_rate_snapshot VALUES(2,2,NULL,'2026-01-30','2026-01-30 16:10:13.961037','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S1','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
INSERT INTO mes_kit_rate_snapshot VALUES(3,3,NULL,'2026-01-30','2026-01-30 16:10:13.961638','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S1','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
INSERT INTO mes_kit_rate_snapshot VALUES(4,4,NULL,'2026-01-30','2026-01-30 16:10:13.962202','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S1','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
INSERT INTO mes_kit_rate_snapshot VALUES(5,5,NULL,'2026-01-30','2026-01-30 16:10:13.962751','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S2','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
INSERT INTO mes_kit_rate_snapshot VALUES(6,6,NULL,'2026-01-30','2026-01-30 16:10:13.963301','DAILY',NULL,0,'shortage',0,0,0,0,0,0,0,0,0,'S1','H2',NULL,'2026-01-30 08:10:13','2026-01-30 08:10:13');
CREATE TABLE project_member_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,                     -- 项目ID
    user_id INTEGER NOT NULL,                         -- 用户ID
    period VARCHAR(7) NOT NULL,                      -- 统计周期 YYYY-MM
    
    -- 工作量指标
    task_count INTEGER DEFAULT 0,                    -- 完成任务数
    task_hours DECIMAL(10,2) DEFAULT 0,              -- 任务工时
    actual_hours DECIMAL(10,2) DEFAULT 0,            -- 实际投入工时
    
    -- 质量指标
    deliverable_count INTEGER DEFAULT 0,              -- 交付物数量
    issue_count INTEGER DEFAULT 0,                   -- 问题数
    issue_resolved INTEGER DEFAULT 0,                 -- 解决问题数
    
    -- 贡献度评分
    contribution_score DECIMAL(5,2),                 -- 贡献度评分
    pm_rating INTEGER,                               -- 项目经理评分 1-5
    
    -- 奖金关联
    bonus_amount DECIMAL(14,2) DEFAULT 0,           -- 项目奖金金额
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(project_id, user_id, period)
);
CREATE TABLE solution_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name VARCHAR(200) NOT NULL,             -- 模板名称
    template_code VARCHAR(50) UNIQUE,                -- 模板编码
    
    -- 关联信息
    issue_type VARCHAR(20),                          -- 问题类型
    category VARCHAR(20),                            -- 问题分类
    severity VARCHAR(20),                            -- 严重程度
    
    -- 解决方案内容
    solution TEXT NOT NULL,                          -- 解决方案模板
    solution_steps TEXT,                             -- 解决步骤（JSON数组）
    
    -- 适用场景
    applicable_scenarios TEXT,                      -- 适用场景描述
    prerequisites TEXT,                             -- 前置条件
    precautions TEXT,                                -- 注意事项
    
    -- 标签和分类
    tags TEXT,                                       -- 标签（JSON数组）
    keywords TEXT,                                   -- 关键词（JSON数组，用于搜索）
    
    -- 统计信息
    usage_count INTEGER DEFAULT 0,                   -- 使用次数
    success_rate DECIMAL(5,2),                      -- 成功率（%）
    avg_resolution_time DECIMAL(10,2),               -- 平均解决时间（小时）
    
    -- 来源信息
    source_issue_id INTEGER,                         -- 来源问题ID
    created_by INTEGER,                              -- 创建人ID
    created_by_name VARCHAR(50),                     -- 创建人姓名
    
    -- 状态
    is_active BOOLEAN DEFAULT 1,                    -- 是否启用
    is_public BOOLEAN DEFAULT 1,                    -- 是否公开（所有项目可用）
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_issue_id) REFERENCES issues(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE sales_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_scope VARCHAR(20) NOT NULL,
    user_id INTEGER,
    department_id INTEGER,
    team_id INTEGER,
    target_type VARCHAR(20) NOT NULL,
    target_period VARCHAR(20) NOT NULL,
    period_value VARCHAR(20) NOT NULL,
    target_value NUMERIC(14, 2) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
CREATE TABLE sales_teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_code VARCHAR(20) UNIQUE NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    description TEXT,
    team_type VARCHAR(20) DEFAULT 'REGION',
    department_id INTEGER REFERENCES departments(id),
    leader_id INTEGER REFERENCES users(id),
    parent_team_id INTEGER REFERENCES sales_teams(id),
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sales_team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES sales_teams(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'MEMBER',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    remark VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, user_id)
);
CREATE TABLE team_performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES sales_teams(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL,
    period_value VARCHAR(20) NOT NULL,
    snapshot_date DATETIME NOT NULL,
    lead_count INTEGER DEFAULT 0,
    opportunity_count INTEGER DEFAULT 0,
    opportunity_amount DECIMAL(14,2) DEFAULT 0,
    contract_count INTEGER DEFAULT 0,
    contract_amount DECIMAL(14,2) DEFAULT 0,
    collection_amount DECIMAL(14,2) DEFAULT 0,
    target_amount DECIMAL(14,2) DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,
    rank_in_department INTEGER,
    rank_overall INTEGER,
    member_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, period_type, period_value)
);
CREATE TABLE team_pk_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pk_name VARCHAR(100) NOT NULL,
    pk_type VARCHAR(20) NOT NULL,
    team_ids TEXT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    target_value DECIMAL(14,2),
    status VARCHAR(20) DEFAULT 'ONGOING',
    winner_team_id INTEGER REFERENCES sales_teams(id),
    result_summary TEXT,
    reward_description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE stage_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_code VARCHAR(50) NOT NULL UNIQUE,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    project_type VARCHAR(20) DEFAULT 'CUSTOM',
    is_default INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE stage_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES stage_templates(id) ON DELETE CASCADE,
    stage_code VARCHAR(20) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 0,
    estimated_days INTEGER,
    description TEXT,
    is_required INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, category VARCHAR(50));
CREATE TABLE node_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_definition_id INTEGER NOT NULL REFERENCES stage_definitions(id) ON DELETE CASCADE,
    node_code VARCHAR(20) NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK',
    sequence INTEGER NOT NULL DEFAULT 0,
    estimated_days INTEGER,
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    dependency_node_ids TEXT,  -- JSON array
    is_required INTEGER DEFAULT 1,
    required_attachments INTEGER DEFAULT 0,
    approval_role_ids TEXT,  -- JSON array
    auto_condition TEXT,  -- JSON
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE project_stage_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    stage_definition_id INTEGER REFERENCES stage_definitions(id) ON DELETE SET NULL,
    stage_code VARCHAR(20) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    is_modified INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE project_node_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    stage_instance_id INTEGER NOT NULL REFERENCES project_stage_instances(id) ON DELETE CASCADE,
    node_definition_id INTEGER REFERENCES node_definitions(id) ON DELETE SET NULL,
    node_code VARCHAR(20) NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    node_type VARCHAR(20) NOT NULL DEFAULT 'TASK',
    sequence INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    completion_method VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    dependency_node_instance_ids TEXT,  -- JSON array
    is_required INTEGER DEFAULT 1,
    planned_date DATE,
    actual_date DATE,
    completed_by INTEGER REFERENCES users(id),
    completed_at DATETIME,
    attachments TEXT,  -- JSON array
    approval_record_id INTEGER,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,          -- 战略编码，如 STR-2026
    name VARCHAR(200) NOT NULL,                -- 战略名称
    vision TEXT,                               -- 愿景描述
    mission TEXT,                              -- 使命描述
    slogan VARCHAR(200),                       -- 战略口号

    year INTEGER NOT NULL,                     -- 战略年度
    start_date DATE,                           -- 战略周期开始
    end_date DATE,                             -- 战略周期结束

    status VARCHAR(20) DEFAULT 'DRAFT',        -- 状态：DRAFT/ACTIVE/ARCHIVED

    created_by INTEGER REFERENCES users(id),   -- 创建人
    approved_by INTEGER REFERENCES users(id),  -- 审批人
    approved_at DATETIME,                      -- 审批时间
    published_at DATETIME,                     -- 发布时间

    is_active BOOLEAN DEFAULT 1,               -- 是否激活
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE csfs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    dimension VARCHAR(20) NOT NULL,            -- BSC维度：FINANCIAL/CUSTOMER/INTERNAL/LEARNING
    code VARCHAR(50) NOT NULL,                 -- CSF 编码，如 CSF-F-001
    name VARCHAR(200) NOT NULL,                -- 要素名称
    description TEXT,                          -- 详细描述

    derivation_method VARCHAR(50),             -- 导出方法
    weight DECIMAL(5,2) DEFAULT 0,             -- 权重占比
    sort_order INTEGER DEFAULT 0,              -- 排序

    owner_dept_id INTEGER REFERENCES departments(id),
    owner_user_id INTEGER REFERENCES users(id),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csf_id INTEGER NOT NULL REFERENCES csfs(id),

    code VARCHAR(50) NOT NULL,                 -- KPI 编码
    name VARCHAR(200) NOT NULL,                -- 指标名称
    description TEXT,                          -- 指标描述

    ipooc_type VARCHAR(20) NOT NULL,           -- IPOOC类型
    unit VARCHAR(20),                          -- 单位
    direction VARCHAR(10) DEFAULT 'UP',        -- 方向：UP/DOWN

    target_value DECIMAL(14,2),                -- 目标值
    baseline_value DECIMAL(14,2),              -- 基线值
    current_value DECIMAL(14,2),               -- 当前值

    excellent_threshold DECIMAL(14,2),         -- 优秀阈值
    good_threshold DECIMAL(14,2),              -- 良好阈值
    warning_threshold DECIMAL(14,2),           -- 警告阈值

    data_source_type VARCHAR(20) DEFAULT 'MANUAL',
    data_source_config TEXT,                   -- JSON

    frequency VARCHAR(20) DEFAULT 'MONTHLY',
    last_collected_at DATETIME,

    weight DECIMAL(5,2) DEFAULT 0,
    owner_user_id INTEGER REFERENCES users(id),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE kpi_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER NOT NULL REFERENCES kpis(id),

    snapshot_date DATE NOT NULL,               -- 快照日期
    snapshot_period VARCHAR(20),               -- 快照周期

    value DECIMAL(14,2),                       -- KPI 值
    target_value DECIMAL(14,2),                -- 目标值
    completion_rate DECIMAL(5,2),              -- 完成率
    health_level VARCHAR(20),                  -- 健康等级

    source_type VARCHAR(20),                   -- 来源类型
    source_detail TEXT,                        -- 来源详情
    remark TEXT,                               -- 备注

    recorded_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE kpi_data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER NOT NULL REFERENCES kpis(id),

    source_type VARCHAR(20) NOT NULL,          -- 类型：AUTO/FORMULA

    source_module VARCHAR(50),                 -- 来源模块
    query_type VARCHAR(20),                    -- 查询类型
    metric VARCHAR(100),                       -- 度量字段
    filters TEXT,                              -- 过滤条件（JSON）
    aggregation VARCHAR(20),                   -- 聚合方式

    formula TEXT,                              -- 计算公式
    formula_params TEXT,                       -- 公式参数（JSON）

    is_primary BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,

    last_executed_at DATETIME,
    last_result DECIMAL(14,2),
    last_error TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE annual_key_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csf_id INTEGER NOT NULL REFERENCES csfs(id),

    code VARCHAR(50) NOT NULL,                 -- 工作编码
    name VARCHAR(200) NOT NULL,                -- 工作名称
    description TEXT,                          -- 工作描述

    voc_source VARCHAR(20),                    -- 声音来源
    pain_point TEXT,                           -- 痛点/短板
    solution TEXT,                             -- 解决方案
    target TEXT,                               -- 目标描述

    year INTEGER NOT NULL,                     -- 年度
    start_date DATE,                           -- 计划开始
    end_date DATE,                             -- 计划结束
    actual_start_date DATE,                    -- 实际开始
    actual_end_date DATE,                      -- 实际结束

    owner_dept_id INTEGER REFERENCES departments(id),
    owner_user_id INTEGER REFERENCES users(id),

    status VARCHAR(20) DEFAULT 'NOT_STARTED',
    progress_percent INTEGER DEFAULT 0,
    priority VARCHAR(20) DEFAULT 'MEDIUM',

    budget DECIMAL(14,2),
    actual_cost DECIMAL(14,2),

    risk_description TEXT,
    remark TEXT,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE annual_key_work_project_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annual_work_id INTEGER NOT NULL REFERENCES annual_key_works(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    link_type VARCHAR(20) DEFAULT 'SUPPORT',   -- MAIN/SUPPORT/RELATED
    contribution_weight DECIMAL(5,2) DEFAULT 100,
    remark TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(annual_work_id, project_id)
);
CREATE TABLE department_objectives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),

    year INTEGER NOT NULL,
    quarter INTEGER,

    objectives TEXT,                           -- 部门级目标（JSON）
    key_results TEXT,                          -- 关键成果（JSON）
    kpis_config TEXT,                          -- 部门级 KPI（JSON）

    status VARCHAR(20) DEFAULT 'DRAFT',

    owner_user_id INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at VARCHAR(50),

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(strategy_id, department_id, year, quarter)
);
CREATE TABLE personal_kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES users(id),

    year INTEGER NOT NULL,
    quarter INTEGER,

    source_type VARCHAR(20) NOT NULL,          -- CSF_KPI/DEPT_OBJECTIVE/ANNUAL_WORK
    source_id INTEGER,
    department_objective_id INTEGER REFERENCES department_objectives(id),

    kpi_name VARCHAR(200) NOT NULL,
    kpi_description TEXT,
    unit VARCHAR(20),

    target_value DECIMAL(14,2),
    actual_value DECIMAL(14,2),
    completion_rate DECIMAL(5,2),

    weight DECIMAL(5,2) DEFAULT 0,

    self_rating INTEGER,
    self_comment TEXT,
    manager_rating INTEGER,
    manager_comment TEXT,

    status VARCHAR(20) DEFAULT 'PENDING',

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE strategy_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    review_type VARCHAR(20) NOT NULL,          -- ANNUAL/QUARTERLY/MONTHLY/SPECIAL
    review_date DATE NOT NULL,
    review_period VARCHAR(20),

    reviewer_id INTEGER REFERENCES users(id),

    health_score INTEGER,                      -- 总体健康度（0-100）
    financial_score INTEGER,
    customer_score INTEGER,
    internal_score INTEGER,
    learning_score INTEGER,

    findings TEXT,                             -- JSON
    achievements TEXT,                         -- JSON
    recommendations TEXT,                      -- JSON
    decisions TEXT,                            -- JSON
    action_items TEXT,                         -- JSON

    meeting_minutes TEXT,
    attendees TEXT,                            -- JSON
    meeting_duration INTEGER,

    next_review_date DATE,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE strategy_calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id),

    event_type VARCHAR(30) NOT NULL,           -- 事件类型
    name VARCHAR(200) NOT NULL,
    description TEXT,

    year INTEGER NOT NULL,
    month INTEGER,
    quarter INTEGER,
    scheduled_date DATE,
    actual_date DATE,
    deadline DATE,

    is_recurring BOOLEAN DEFAULT 0,
    recurrence_rule VARCHAR(50),

    owner_user_id INTEGER REFERENCES users(id),
    participants TEXT,                         -- JSON

    status VARCHAR(20) DEFAULT 'PLANNED',

    review_id INTEGER REFERENCES strategy_reviews(id),

    reminder_days INTEGER DEFAULT 7,
    reminder_sent BOOLEAN DEFAULT 0,

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE strategy_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    current_strategy_id INTEGER NOT NULL REFERENCES strategies(id),
    previous_strategy_id INTEGER REFERENCES strategies(id),
    current_year INTEGER NOT NULL,
    previous_year INTEGER,

    generated_date DATE NOT NULL,
    generated_by INTEGER REFERENCES users(id),

    current_health_score INTEGER,
    previous_health_score INTEGER,
    health_change INTEGER,

    current_financial_score INTEGER,
    previous_financial_score INTEGER,
    financial_change INTEGER,

    current_customer_score INTEGER,
    previous_customer_score INTEGER,
    customer_change INTEGER,

    current_internal_score INTEGER,
    previous_internal_score INTEGER,
    internal_change INTEGER,

    current_learning_score INTEGER,
    previous_learning_score INTEGER,
    learning_change INTEGER,

    kpi_completion_rate DECIMAL(5,2),
    previous_kpi_completion_rate DECIMAL(5,2),
    kpi_completion_change DECIMAL(5,2),

    work_completion_rate DECIMAL(5,2),
    previous_work_completion_rate DECIMAL(5,2),
    work_completion_change DECIMAL(5,2),

    csf_comparison TEXT,                       -- JSON
    kpi_comparison TEXT,                       -- JSON
    work_comparison TEXT,                      -- JSON

    summary TEXT,
    highlights TEXT,                           -- JSON
    improvements TEXT,                         -- JSON
    recommendations TEXT,                      -- JSON

    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pitfalls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_no VARCHAR(50) UNIQUE NOT NULL,

    -- 必填字段
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    solution TEXT,

    -- 多维度分类
    stage VARCHAR(20),
    equipment_type VARCHAR(50),
    problem_type VARCHAR(50),
    tags JSON,

    -- 选填字段
    root_cause TEXT,
    impact TEXT,
    prevention TEXT,
    cost_impact DECIMAL(12,2),
    schedule_impact INTEGER,

    -- 来源追溯
    source_type VARCHAR(20),
    source_project_id INTEGER REFERENCES projects(id),
    source_ecn_id INTEGER,
    source_issue_id INTEGER,

    -- 权限与状态
    is_sensitive BOOLEAN DEFAULT FALSE,
    sensitive_reason VARCHAR(50),
    visible_to JSON,
    status VARCHAR(20) DEFAULT 'DRAFT',
    verified BOOLEAN DEFAULT FALSE,
    verify_count INTEGER DEFAULT 0,

    -- 创建人
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pitfall_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    trigger_type VARCHAR(20) NOT NULL,
    trigger_context JSON,

    is_helpful BOOLEAN,
    feedback TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pitfall_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),

    read_at DATETIME,
    is_marked BOOLEAN DEFAULT FALSE,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, pitfall_id)
);
CREATE TABLE project_stage_resource_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    stage_code VARCHAR(10) NOT NULL,
    staffing_need_id INTEGER REFERENCES mes_project_staffing_need(id),
    role_code VARCHAR(50) NOT NULL,
    role_name VARCHAR(100),
    headcount INTEGER DEFAULT 1,
    allocation_pct DECIMAL(5,2) DEFAULT 100,
    assigned_employee_id INTEGER REFERENCES users(id),
    assignment_status VARCHAR(20) DEFAULT 'PENDING',
    planned_start DATE,
    planned_end DATE,
    remark TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE resource_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES users(id),
    plan_a_id INTEGER NOT NULL REFERENCES project_stage_resource_plan(id),
    plan_b_id INTEGER NOT NULL REFERENCES project_stage_resource_plan(id),
    overlap_start DATE NOT NULL,
    overlap_end DATE NOT NULL,
    total_allocation DECIMAL(5,2),
    over_allocation DECIMAL(5,2),
    severity VARCHAR(10) DEFAULT 'LOW',
    is_resolved INTEGER DEFAULT 0,
    resolved_by INTEGER REFERENCES users(id),
    resolved_at DATE,
    resolution_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sales_ranking_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics TEXT NOT NULL,
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);
INSERT INTO sales_ranking_configs VALUES(1,'[{"key": "contract_amount", "label": "\u5408\u540c\u91d1\u989d", "weight": 0.4, "data_source": "contract_amount", "description": "\u7edf\u8ba1\u5468\u671f\u5185\u7b7e\u8ba2\u5408\u540c\u91d1\u989d", "is_primary": true}, {"key": "acceptance_amount", "label": "\u9a8c\u6536\u91d1\u989d", "weight": 0.2, "data_source": "acceptance_amount", "description": "\u5df2\u5ba1\u6279/\u5df2\u5f00\u7968\u91d1\u989d\uff0c\u4ee3\u8868\u9a8c\u6536\u8fdb\u5ea6", "is_primary": true}, {"key": "collection_amount", "label": "\u56de\u6b3e\u91d1\u989d", "weight": 0.2, "data_source": "collection_amount", "description": "\u5468\u671f\u5185\u5df2\u56de\u6b3e\u91d1\u989d", "is_primary": true}, {"key": "opportunity_count", "label": "\u5546\u673a\u6570\u91cf", "weight": 0.05, "data_source": "opportunity_count", "description": "\u521b\u5efa\u5e76\u63a8\u8fdb\u7684\u5546\u673a\u6570\u91cf", "is_primary": false}, {"key": "lead_conversion_rate", "label": "\u7ebf\u7d22\u6210\u529f\u7387", "weight": 0.05, "data_source": "lead_conversion_rate", "description": "\u7ebf\u7d22\u8f6c\u5546\u673a\u7684\u8f6c\u5316\u7387", "is_primary": false}, {"key": "follow_up_total", "label": "\u8ddf\u8fdb\u884c\u4e3a\u6b21\u6570", "weight": 0.05, "data_source": "follow_up_total", "description": "\u7535\u8bdd\u3001\u62dc\u8bbf\u3001\u4f1a\u8bae\u7b49\u603b\u8ddf\u8fdb\u6b21\u6570", "is_primary": false}, {"key": "avg_est_margin", "label": "\u5e73\u5747\u9884\u4f30\u6bdb\u5229\u7387", "weight": 0.05, "data_source": "avg_est_margin", "description": "\u5546\u673a\u7684\u5e73\u5747\u9884\u4f30\u6bdb\u5229\u7387", "is_primary": false}]',NULL,NULL,'2026-01-28 15:20:14.497705','2026-01-28 15:20:14.497706');
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_code VARCHAR(50) UNIQUE NOT NULL,
    tenant_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    plan_type VARCHAR(20) DEFAULT 'FREE',
    max_users INTEGER DEFAULT 5,
    max_roles INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 1,
    settings JSON,
    contact_name VARCHAR(100),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),
    expired_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO tenants VALUES(1,'DEFAULT','默认租户','ACTIVE','ENTERPRISE',-1,-1,100,NULL,NULL,NULL,NULL,NULL,'2026-01-28 06:49:08','2026-01-28 06:49:08');
CREATE TABLE api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER REFERENCES tenants(id),
    perm_code VARCHAR(100) NOT NULL,
    perm_name VARCHAR(100),
    module VARCHAR(50),
    resource VARCHAR(50),
    action VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
, page_code VARCHAR(50), permission_type VARCHAR(20) DEFAULT 'API', group_id INTEGER, is_system BOOLEAN DEFAULT 0);
INSERT INTO api_permissions VALUES(1,NULL,'system:user:read','User Read','system','user','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(2,NULL,'system:user:manage','User Manage','system','user','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(3,NULL,'system:role:read','Role Read','system','role','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(4,NULL,'system:role:manage','Role Manage','system','role','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(5,NULL,'system:permission:read','Permission Read','system','permission','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(6,NULL,'project:project:read','Project Read','project','project','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(7,NULL,'project:project:manage','Project Manage','project','project','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(8,NULL,'project:milestone:read','Milestone Read','project','milestone','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(9,NULL,'project:milestone:manage','Milestone Manage','project','milestone','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(10,NULL,'project:task:read','Task Read','project','task','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(11,NULL,'project:task:manage','Task Manage','project','task','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(12,NULL,'project:wbs:read','WBS Read','project','wbs','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(13,NULL,'project:wbs:manage','WBS Manage','project','wbs','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(14,NULL,'project:deliverable:read','Deliverable Read','project','deliverable','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(15,NULL,'project:deliverable:submit','Deliverable Submit','project','deliverable','submit',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(16,NULL,'project:deliverable:approve','Deliverable Approve','project','deliverable','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(17,NULL,'project:acceptance:read','Acceptance Read','project','acceptance','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(18,NULL,'project:acceptance:submit','Acceptance Submit','project','acceptance','submit',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(19,NULL,'project:acceptance:approve','Acceptance Approve','project','acceptance','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(20,NULL,'project:ecn:read','ECN Read','project','ecn','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(21,NULL,'project:ecn:submit','ECN Submit','project','ecn','submit',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(22,NULL,'project:ecn:approve','ECN Approve','project','ecn','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(23,NULL,'supply:purchase:read','Purchase Read','supply','purchase','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(24,NULL,'supply:purchase:manage','Purchase Manage','supply','purchase','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(25,NULL,'supply:outsourcing:read','Outsourcing Read','supply','outsourcing','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(26,NULL,'supply:outsourcing:manage','Outsourcing Manage','supply','outsourcing','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(27,NULL,'finance:payment:read','Payment Read','finance','payment','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(28,NULL,'finance:payment:approve','Payment Approve','finance','payment','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(29,NULL,'finance:invoice:read','Invoice Read','finance','invoice','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(30,NULL,'finance:invoice:issue','Invoice Issue','finance','invoice','issue',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(31,NULL,'crm:lead:read','Lead Read','crm','lead','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(32,NULL,'crm:lead:manage','Lead Manage','crm','lead','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(33,NULL,'crm:opportunity:read','Opportunity Read','crm','opportunity','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(34,NULL,'crm:opportunity:manage','Opportunity Manage','crm','opportunity','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(35,NULL,'crm:quote:read','Quote Read','crm','quote','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(36,NULL,'crm:quote:manage','Quote Manage','crm','quote','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(37,NULL,'crm:quote:approve','Quote Approve','crm','quote','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(38,NULL,'crm:contract:read','Contract Read','crm','contract','read',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(39,NULL,'crm:contract:manage','Contract Manage','crm','contract','manage',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(40,NULL,'crm:contract:approve','Contract Approve','crm','contract','approve',NULL,1,'2026-01-28 06:47:09','2026-01-28 06:47:09',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(41,NULL,'system:user:create','用户创建','system','user','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(42,NULL,'system:user:update','用户更新','system','user','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(43,NULL,'system:user:delete','用户删除','system','user','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(44,NULL,'system:audit:read','审计查看','system','audit','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(45,NULL,'project:project:create','项目创建','project','project','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(46,NULL,'project:project:update','项目更新','project','project','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(47,NULL,'project:project:delete','项目删除','project','project','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(48,NULL,'project:machine:read','设备查看','project','machine','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(49,NULL,'project:machine:manage','设备管理','project','machine','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(50,NULL,'project:member:read','成员查看','project','member','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(51,NULL,'project:member:manage','成员管理','project','member','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(52,NULL,'project:stage:read','阶段查看','project','stage','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(53,NULL,'project:stage:manage','阶段管理','project','stage','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(54,NULL,'project:cost:read','成本查看','project','cost','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(55,NULL,'project:cost:manage','成本管理','project','cost','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(56,NULL,'project:document:read','文档查看','project','document','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(57,NULL,'project:document:manage','文档管理','project','document','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(58,NULL,'customer:customer:read','客户查看','customer','customer','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(59,NULL,'customer:customer:create','客户创建','customer','customer','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(60,NULL,'customer:customer:update','客户更新','customer','customer','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(61,NULL,'customer:customer:delete','客户删除','customer','customer','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(62,NULL,'supplier:supplier:read','供应商查看','supplier','supplier','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(63,NULL,'supplier:supplier:create','供应商创建','supplier','supplier','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(64,NULL,'supplier:supplier:update','供应商更新','supplier','supplier','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(65,NULL,'supplier:supplier:delete','供应商删除','supplier','supplier','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(66,NULL,'material:material:read','物料查看','material','material','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(67,NULL,'material:material:create','物料创建','material','material','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(68,NULL,'material:material:update','物料更新','material','material','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(69,NULL,'material:material:delete','物料删除','material','material','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(70,NULL,'material:shortage:read','缺料查看','material','shortage','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(71,NULL,'material:shortage:manage','缺料管理','material','shortage','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(72,NULL,'issue:issue:read','问题查看','issue','issue','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(73,NULL,'issue:issue:create','问题创建','issue','issue','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(74,NULL,'issue:issue:update','问题更新','issue','issue','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(75,NULL,'issue:issue:delete','问题删除','issue','issue','delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(76,NULL,'issue:issue:resolve','问题解决','issue','issue','resolve',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(77,NULL,'finance:budget:read','预算查看','finance','budget','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(78,NULL,'finance:budget:create','预算创建','finance','budget','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(79,NULL,'finance:budget:update','预算更新','finance','budget','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(80,NULL,'finance:budget:approve','预算审批','finance','budget','approve',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(81,NULL,'finance:cost:read','成本查看','finance','cost','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(82,NULL,'finance:cost:manage','成本管理','finance','cost','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(83,NULL,'finance:bonus:read','奖金查看','finance','bonus','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(84,NULL,'finance:bonus:manage','奖金管理','finance','bonus','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(85,NULL,'service:service:read','服务查看','service','service','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(86,NULL,'service:service:create','服务创建','service','service','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(87,NULL,'service:service:update','服务更新','service','service','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(88,NULL,'service:ticket:read','工单查看','service','ticket','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(89,NULL,'service:ticket:manage','工单管理','service','ticket','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(90,NULL,'business_support:order:read','业务订单查看','business_support','order','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(91,NULL,'business_support:order:create','业务订单创建','business_support','order','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(92,NULL,'business_support:order:update','业务订单更新','business_support','order','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(93,NULL,'business_support:order:approve','业务订单审批','business_support','order','approve',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(94,NULL,'organization:org:read','组织查看','organization','org','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(95,NULL,'organization:org:manage','组织管理','organization','org','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(96,NULL,'organization:employee:read','员工查看','organization','employee','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(97,NULL,'organization:employee:manage','员工管理','organization','employee','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(98,NULL,'task_center:task:read','任务查看','task_center','task','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(99,NULL,'task_center:task:create','任务创建','task_center','task','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(100,NULL,'task_center:task:update','任务更新','task_center','task','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(101,NULL,'task_center:task:complete','任务完成','task_center','task','complete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(102,NULL,'timesheet:timesheet:read','工时查看','timesheet','timesheet','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(103,NULL,'timesheet:timesheet:create','工时创建','timesheet','timesheet','create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(104,NULL,'timesheet:timesheet:update','工时更新','timesheet','timesheet','update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(105,NULL,'timesheet:timesheet:approve','工时审批','timesheet','timesheet','approve',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(106,NULL,'report:report:read','报表查看','report','report','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(107,NULL,'report:report:export','报表导出','report','report','export',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(108,NULL,'report:report:manage','报表管理','report','report','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(109,NULL,'notification:notification:read','通知查看','notification','notification','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(110,NULL,'notification:notification:manage','通知管理','notification','notification','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(111,NULL,'document:document:read','文档查看','document','document','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(112,NULL,'document:document:manage','文档管理','document','document','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(113,NULL,'technical_spec:spec:read','技术规格查看','technical_spec','spec','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(114,NULL,'technical_spec:spec:manage','技术规格管理','technical_spec','spec','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(115,NULL,'engineer:engineer:read','工程师查看','engineer','engineer','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(116,NULL,'engineer:engineer:manage','工程师管理','engineer','engineer','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(117,NULL,'qualification:qualification:read','任职资格查看','qualification','qualification','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(118,NULL,'qualification:qualification:manage','任职资格管理','qualification','qualification','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(119,NULL,'assembly_kit:kit:read','装配齐套查看','assembly_kit','kit','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(120,NULL,'assembly_kit:kit:manage','装配齐套管理','assembly_kit','kit','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(121,NULL,'staff_matching:matching:read','人员匹配查看','staff_matching','matching','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(122,NULL,'staff_matching:matching:manage','人员匹配管理','staff_matching','matching','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(123,NULL,'project_evaluation:evaluation:read','项目评价查看','project_evaluation','evaluation','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(124,NULL,'project_evaluation:evaluation:manage','项目评价管理','project_evaluation','evaluation','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(125,NULL,'installation_dispatch:dispatch:read','安装派工查看','installation_dispatch','dispatch','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(126,NULL,'installation_dispatch:dispatch:manage','安装派工管理','installation_dispatch','dispatch','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(127,NULL,'scheduler:scheduler:read','调度器查看','scheduler','scheduler','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(128,NULL,'scheduler:scheduler:manage','调度器管理','scheduler','scheduler','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(129,NULL,'hr_management:hr:read','HR管理查看','hr_management','hr','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(130,NULL,'hr_management:hr:manage','HR管理','hr_management','hr','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(131,NULL,'presales_integration:presales:read','售前集成查看','presales_integration','presales','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(132,NULL,'presales_integration:presales:manage','售前集成管理','presales_integration','presales','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(133,NULL,'advantage_products:product:read','优势产品查看','advantage_products','product','read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(134,NULL,'advantage_products:product:manage','优势产品管理','advantage_products','product','manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(135,NULL,'purchase:order:read','采购订单查看','purchase','order','read','可以查看采购订单列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(136,NULL,'purchase:order:create','采购订单创建','purchase','order','create','可以创建采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(137,NULL,'purchase:order:update','采购订单更新','purchase','order','update','可以更新采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(138,NULL,'purchase:order:delete','采购订单删除','purchase','order','delete','可以删除采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(139,NULL,'purchase:order:submit','采购订单提交','purchase','order','submit','可以提交采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(140,NULL,'purchase:order:approve','采购订单审批','purchase','order','approve','可以审批采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(141,NULL,'purchase:order:receive','采购订单收货','purchase','order','receive','可以处理采购订单收货',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(142,NULL,'purchase:receipt:read','收货单查看','purchase','receipt','read','可以查看收货单列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(143,NULL,'purchase:receipt:create','收货单创建','purchase','receipt','create','可以创建收货单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(144,NULL,'purchase:receipt:update','收货单更新','purchase','receipt','update','可以更新收货单状态',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(145,NULL,'purchase:receipt:inspect','收货单质检','purchase','receipt','inspect','可以对收货单进行质检',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(146,NULL,'purchase:request:read','采购申请查看','purchase','request','read','可以查看采购申请列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(147,NULL,'purchase:request:create','采购申请创建','purchase','request','create','可以创建采购申请',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(148,NULL,'purchase:request:update','采购申请更新','purchase','request','update','可以更新采购申请',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(149,NULL,'purchase:request:delete','采购申请删除','purchase','request','delete','可以删除采购申请',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(150,NULL,'purchase:request:submit','采购申请提交','purchase','request','submit','可以提交采购申请',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(151,NULL,'purchase:request:approve','采购申请审批','purchase','request','approve','可以审批采购申请',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(152,NULL,'purchase:request:generate','采购申请生成订单','purchase','request','generate','可以根据采购申请生成采购订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(153,NULL,'purchase:bom:generate','从BOM生成采购','purchase','bom','generate','可以从BOM生成采购申请或订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(154,NULL,'ecn:ecn:read','ECN查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(155,NULL,'ecn:ecn:create','ECN创建','ecn',NULL,'create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(156,NULL,'ecn:ecn:update','ECN修改','ecn',NULL,'update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(157,NULL,'ecn:ecn:submit','ECN提交','ecn',NULL,'submit',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(158,NULL,'ecn:ecn:cancel','ECN取消','ecn',NULL,'cancel',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(159,NULL,'ecn:ecn:delete','ECN删除','ecn',NULL,'delete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(160,NULL,'ecn:evaluation:read','评估查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(161,NULL,'ecn:evaluation:create','评估创建','ecn',NULL,'create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(162,NULL,'ecn:evaluation:submit','评估提交','ecn',NULL,'submit',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(163,NULL,'ecn:approval:read','审批查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(164,NULL,'ecn:approval:approve','审批通过','ecn',NULL,'approve',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(165,NULL,'ecn:approval:reject','审批驳回','ecn',NULL,'reject',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(166,NULL,'ecn:task:read','任务查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(167,NULL,'ecn:task:create','任务创建','ecn',NULL,'create',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(168,NULL,'ecn:task:update','任务更新','ecn',NULL,'update',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(169,NULL,'ecn:task:complete','任务完成','ecn',NULL,'complete',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(170,NULL,'ecn:affected:read','影响分析查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(171,NULL,'ecn:affected:manage','影响分析管理','ecn',NULL,'manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(172,NULL,'ecn:sync:bom','BOM同步','ecn',NULL,'bom',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(173,NULL,'ecn:sync:project','项目同步','ecn',NULL,'project',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(174,NULL,'ecn:sync:purchase','采购同步','ecn',NULL,'purchase',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(175,NULL,'ecn:type:read','类型配置查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(176,NULL,'ecn:type:manage','类型配置管理','ecn',NULL,'manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(177,NULL,'ecn:matrix:read','审批矩阵查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(178,NULL,'ecn:matrix:manage','审批矩阵管理','ecn',NULL,'manage',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(179,NULL,'ecn:statistics:read','统计查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(180,NULL,'ecn:alert:read','超时提醒查看','ecn',NULL,'read',NULL,1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(181,NULL,'advantage_product:read','优势产品查看','advantage_product','advantage_product','read','可以查看优势产品列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(182,NULL,'advantage_product:create','优势产品创建','advantage_product','advantage_product','create','可以创建新的优势产品',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(183,NULL,'advantage_product:update','优势产品更新','advantage_product','advantage_product','update','可以更新优势产品信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(184,NULL,'advantage_product:delete','优势产品删除','advantage_product','advantage_product','delete','可以删除优势产品',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(185,NULL,'assembly_kit:read','装配套件查看','assembly_kit','assembly_kit','read','可以查看装配套件列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(186,NULL,'assembly_kit:create','装配套件创建','assembly_kit','assembly_kit','create','可以创建装配套件',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(187,NULL,'assembly_kit:update','装配套件更新','assembly_kit','assembly_kit','update','可以更新装配套件信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(188,NULL,'assembly_kit:delete','装配套件删除','assembly_kit','assembly_kit','delete','可以删除装配套件',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(189,NULL,'assembly_kit:manage','装配套件管理','assembly_kit','assembly_kit','manage','可以管理装配套件的完整生命周期',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(190,NULL,'budget:read','预算查看','budget','budget','read','可以查看项目预算列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(191,NULL,'budget:create','预算创建','budget','budget','create','可以创建项目预算',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(192,NULL,'budget:update','预算更新','budget','budget','update','可以更新项目预算信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(193,NULL,'budget:approve','预算审批','budget','budget','approve','可以审批项目预算',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(194,NULL,'budget:delete','预算删除','budget','budget','delete','可以删除项目预算',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(195,NULL,'business_support:read','业务支持查看','business_support','business_support','read','可以查看业务支持订单和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(196,NULL,'business_support:create','业务支持创建','business_support','business_support','create','可以创建业务支持订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(197,NULL,'business_support:update','业务支持更新','business_support','business_support','update','可以更新业务支持订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(198,NULL,'business_support:approve','业务支持审批','business_support','business_support','approve','可以审批业务支持订单',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(199,NULL,'business_support:manage','业务支持管理','business_support','business_support','manage','可以管理业务支持的完整流程',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(200,NULL,'cost:read','成本查看','cost','cost','read','可以查看项目成本列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(201,NULL,'cost:create','成本创建','cost','cost','create','可以创建成本记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(202,NULL,'cost:update','成本更新','cost','cost','update','可以更新成本信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(203,NULL,'cost:delete','成本删除','cost','cost','delete','可以删除成本记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(204,NULL,'cost:manage','成本管理','cost','cost','manage','可以管理成本的完整生命周期',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(205,NULL,'customer:read','客户查看','customer','customer','read','可以查看客户列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(206,NULL,'customer:create','客户创建','customer','customer','create','可以创建新客户',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(207,NULL,'customer:update','客户更新','customer','customer','update','可以更新客户信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(208,NULL,'customer:delete','客户删除','customer','customer','delete','可以删除客户',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(209,NULL,'data_import:import','数据导入','data_import','data_import','import','可以导入数据到系统',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(210,NULL,'data_export:export','数据导出','data_export','data_export','export','可以导出系统数据',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(211,NULL,'data_import_export:manage','数据导入导出管理','data_import_export','data_import_export','manage','可以管理数据导入导出功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(212,NULL,'document:read','文档查看','document','document','read','可以查看文档列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(213,NULL,'document:create','文档创建','document','document','create','可以上传和创建文档',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(214,NULL,'document:update','文档更新','document','document','update','可以更新文档信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(215,NULL,'document:delete','文档删除','document','document','delete','可以删除文档',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(216,NULL,'document:download','文档下载','document','document','download','可以下载文档',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(217,NULL,'engineer:read','工程师查看','engineer','engineer','read','可以查看工程师列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(218,NULL,'engineer:create','工程师创建','engineer','engineer','create','可以创建工程师信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(219,NULL,'engineer:update','工程师更新','engineer','engineer','update','可以更新工程师信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(220,NULL,'engineer:manage','工程师管理','engineer','engineer','manage','可以管理工程师的完整信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(221,NULL,'hourly_rate:read','小时费率查看','hourly_rate','hourly_rate','read','可以查看小时费率配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(222,NULL,'hourly_rate:create','小时费率创建','hourly_rate','hourly_rate','create','可以创建小时费率配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(223,NULL,'hourly_rate:update','小时费率更新','hourly_rate','hourly_rate','update','可以更新小时费率配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(224,NULL,'hourly_rate:delete','小时费率删除','hourly_rate','hourly_rate','delete','可以删除小时费率配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(225,NULL,'hr:read','HR管理查看','hr','hr','read','可以查看HR管理相关数据',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(226,NULL,'hr:create','HR管理创建','hr','hr','create','可以创建HR管理记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(227,NULL,'hr:update','HR管理更新','hr','hr','update','可以更新HR管理信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(228,NULL,'hr:manage','HR管理','hr','hr','manage','可以管理HR的完整功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(229,NULL,'installation_dispatch:read','安装调度查看','installation_dispatch','installation_dispatch','read','可以查看安装调度列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(230,NULL,'installation_dispatch:create','安装调度创建','installation_dispatch','installation_dispatch','create','可以创建安装调度任务',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(231,NULL,'installation_dispatch:update','安装调度更新','installation_dispatch','installation_dispatch','update','可以更新安装调度信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(232,NULL,'installation_dispatch:manage','安装调度管理','installation_dispatch','installation_dispatch','manage','可以管理安装调度的完整流程',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(233,NULL,'issue:read','问题查看','issue','issue','read','可以查看问题列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(234,NULL,'issue:create','问题创建','issue','issue','create','可以创建问题记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(235,NULL,'issue:update','问题更新','issue','issue','update','可以更新问题信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(236,NULL,'issue:resolve','问题解决','issue','issue','resolve','可以解决和关闭问题',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(237,NULL,'issue:assign','问题分配','issue','issue','assign','可以分配问题给处理人',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(238,NULL,'issue:delete','问题删除','issue','issue','delete','可以删除问题记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(239,NULL,'machine:read','设备查看','machine','machine','read','可以查看设备列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(240,NULL,'machine:create','设备创建','machine','machine','create','可以创建设备信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(241,NULL,'machine:update','设备更新','machine','machine','update','可以更新设备信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(242,NULL,'machine:delete','设备删除','machine','machine','delete','可以删除设备',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(243,NULL,'material:read','物料查看','material','material','read','可以查看物料列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(244,NULL,'material:create','物料创建','material','material','create','可以创建物料信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(245,NULL,'material:update','物料更新','material','material','update','可以更新物料信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(246,NULL,'material:delete','物料删除','material','material','delete','可以删除物料',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(247,NULL,'milestone:read','里程碑查看','milestone','milestone','read','可以查看里程碑列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(248,NULL,'milestone:create','里程碑创建','milestone','milestone','create','可以创建里程碑',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(249,NULL,'milestone:update','里程碑更新','milestone','milestone','update','可以更新里程碑信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(250,NULL,'milestone:delete','里程碑删除','milestone','milestone','delete','可以删除里程碑',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(251,NULL,'notification:read','通知查看','notification','notification','read','可以查看通知列表',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(252,NULL,'notification:create','通知创建','notification','notification','create','可以创建和发送通知',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(253,NULL,'notification:update','通知更新','notification','notification','update','可以更新通知状态',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(254,NULL,'notification:delete','通知删除','notification','notification','delete','可以删除通知',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(255,NULL,'presales_integration:read','售前集成查看','presales_integration','presales_integration','read','可以查看售前集成数据',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(256,NULL,'presales_integration:create','售前集成创建','presales_integration','presales_integration','create','可以创建售前集成记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(257,NULL,'presales_integration:update','售前集成更新','presales_integration','presales_integration','update','可以更新售前集成信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(258,NULL,'presales_integration:manage','售前集成管理','presales_integration','presales_integration','manage','可以管理售前集成的完整功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(259,NULL,'project_evaluation:read','项目评估查看','project_evaluation','project_evaluation','read','可以查看项目评估列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(260,NULL,'project_evaluation:create','项目评估创建','project_evaluation','project_evaluation','create','可以创建项目评估',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(261,NULL,'project_evaluation:update','项目评估更新','project_evaluation','project_evaluation','update','可以更新项目评估信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(262,NULL,'project_evaluation:manage','项目评估管理','project_evaluation','project_evaluation','manage','可以管理项目评估的完整流程',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(263,NULL,'project_role:read','项目角色查看','project_role','project_role','read','可以查看项目角色列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(264,NULL,'project_role:create','项目角色创建','project_role','project_role','create','可以创建项目角色',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(265,NULL,'project_role:update','项目角色更新','project_role','project_role','update','可以更新项目角色信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(266,NULL,'project_role:delete','项目角色删除','project_role','project_role','delete','可以删除项目角色',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(267,NULL,'project_role:assign','项目角色分配','project_role','project_role','assign','可以分配项目角色给用户',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(268,NULL,'qualification:read','资质查看','qualification','qualification','read','可以查看资质列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(269,NULL,'qualification:create','资质创建','qualification','qualification','create','可以创建资质记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(270,NULL,'qualification:update','资质更新','qualification','qualification','update','可以更新资质信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(271,NULL,'qualification:delete','资质删除','qualification','qualification','delete','可以删除资质记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(272,NULL,'qualification:manage','资质管理','qualification','qualification','manage','可以管理资质的完整生命周期',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(273,NULL,'report:read','报表查看','report','report','read','可以查看报表列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(274,NULL,'report:create','报表创建','report','report','create','可以创建和生成报表',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(275,NULL,'report:export','报表导出','report','report','export','可以导出报表',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(276,NULL,'report:manage','报表管理','report','report','manage','可以管理报表的完整功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(277,NULL,'shortage_alert:read','短缺预警查看','shortage_alert','shortage_alert','read','可以查看短缺预警列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(278,NULL,'shortage_alert:create','短缺预警创建','shortage_alert','shortage_alert','create','可以创建短缺预警',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(279,NULL,'shortage_alert:update','短缺预警更新','shortage_alert','shortage_alert','update','可以更新短缺预警信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(280,NULL,'shortage_alert:resolve','短缺预警处理','shortage_alert','shortage_alert','resolve','可以处理和解决短缺预警',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(281,NULL,'shortage_alert:manage','短缺预警管理','shortage_alert','shortage_alert','manage','可以管理短缺预警的完整流程',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(282,NULL,'staff_matching:read','人员匹配查看','staff_matching','staff_matching','read','可以查看人员匹配列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(283,NULL,'staff_matching:create','人员匹配创建','staff_matching','staff_matching','create','可以创建人员匹配记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(284,NULL,'staff_matching:update','人员匹配更新','staff_matching','staff_matching','update','可以更新人员匹配信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(285,NULL,'staff_matching:manage','人员匹配管理','staff_matching','staff_matching','manage','可以管理人员匹配的完整功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(286,NULL,'stage:read','阶段查看','stage','stage','read','可以查看项目阶段列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(287,NULL,'stage:create','阶段创建','stage','stage','create','可以创建项目阶段',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(288,NULL,'stage:update','阶段更新','stage','stage','update','可以更新项目阶段信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(289,NULL,'stage:delete','阶段删除','stage','stage','delete','可以删除项目阶段',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(290,NULL,'stage:manage','阶段管理','stage','stage','manage','可以管理项目阶段的完整生命周期',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(291,NULL,'supplier:read','供应商查看','supplier','supplier','read','可以查看供应商列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(292,NULL,'supplier:create','供应商创建','supplier','supplier','create','可以创建供应商信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(293,NULL,'supplier:update','供应商更新','supplier','supplier','update','可以更新供应商信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(294,NULL,'supplier:delete','供应商删除','supplier','supplier','delete','可以删除供应商',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(295,NULL,'task_center:read','任务中心查看','task_center','task_center','read','可以查看任务列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(296,NULL,'task_center:create','任务中心创建','task_center','task_center','create','可以创建任务',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(297,NULL,'task_center:update','任务中心更新','task_center','task_center','update','可以更新任务信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(298,NULL,'task_center:assign','任务中心分配','task_center','task_center','assign','可以分配任务给执行人',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(299,NULL,'task_center:manage','任务中心管理','task_center','task_center','manage','可以管理任务的完整生命周期',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(300,NULL,'technical_spec:read','技术规格查看','technical_spec','technical_spec','read','可以查看技术规格列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(301,NULL,'technical_spec:create','技术规格创建','technical_spec','technical_spec','create','可以创建技术规格',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(302,NULL,'technical_spec:update','技术规格更新','technical_spec','technical_spec','update','可以更新技术规格信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(303,NULL,'technical_spec:delete','技术规格删除','technical_spec','technical_spec','delete','可以删除技术规格',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(304,NULL,'timesheet:read','工时表查看','timesheet','timesheet','read','可以查看工时表列表和详情',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(305,NULL,'timesheet:create','工时表创建','timesheet','timesheet','create','可以创建和填报工时',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(306,NULL,'timesheet:update','工时表更新','timesheet','timesheet','update','可以更新工时记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(307,NULL,'timesheet:approve','工时表审批','timesheet','timesheet','approve','可以审批工时表',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(308,NULL,'timesheet:delete','工时表删除','timesheet','timesheet','delete','可以删除工时记录',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(309,NULL,'timesheet:manage','工时表管理','timesheet','timesheet','manage','可以管理工时表的完整功能',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(310,NULL,'system:role:create','角色创建','system','role','create','创建新角色',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(311,NULL,'system:role:update','角色更新','system','role','update','更新角色信息',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(312,NULL,'performance:manage','绩效管理','performance','performance','manage','绩效管理权限（包含所有操作）',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(313,NULL,'performance:evaluation:read','绩效评估查看','performance','evaluation','read','查看绩效评估',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(314,NULL,'performance:evaluation:create','绩效评估创建','performance','evaluation','create','创建绩效评估',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(315,NULL,'performance:evaluation:update','绩效评估更新','performance','evaluation','update','更新绩效评估',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(316,NULL,'performance:summary:read','工作汇总查看','performance','summary','read','查看工作汇总',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(317,NULL,'performance:summary:create','工作汇总创建','performance','summary','create','创建工作汇总',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(318,NULL,'performance:summary:update','工作汇总更新','performance','summary','update','更新工作汇总',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(319,NULL,'project:erp:sync','ERP同步','project','erp','sync','同步项目数据到ERP系统',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(320,NULL,'project:erp:update','ERP更新','project','erp','update','更新ERP系统中的项目数据',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(321,NULL,'work_log:config:read','工作日志配置查看','work_log','config','read','查看工作日志配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(322,NULL,'work_log:config:create','工作日志配置创建','work_log','config','create','创建工作日志配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(323,NULL,'work_log:config:update','工作日志配置更新','work_log','config','update','更新工作日志配置',1,NULL,NULL,NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(324,NULL,'USER_VIEW','View Users','system','user','view','查看用户列表',1,'2026-01-31 09:47:20','2026-01-31 09:47:20',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(325,NULL,'USER_CREATE','Create User','system','user','create','创建用户',1,'2026-01-31 09:47:20','2026-01-31 09:47:20',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(326,NULL,'USER_UPDATE','Update User','system','user','update','更新用户',1,'2026-01-31 09:47:20','2026-01-31 09:47:20',NULL,'API',NULL,0);
INSERT INTO api_permissions VALUES(327,NULL,'USER_DELETE','Delete User','system','user','delete','删除用户',1,'2026-01-31 09:47:20','2026-01-31 09:47:20',NULL,'API',NULL,0);
CREATE TABLE role_api_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    permission_id INTEGER NOT NULL REFERENCES api_permissions(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_id, permission_id)
);
INSERT INTO role_api_permissions VALUES(1,1,1,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(2,2,1,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(3,21,1,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(4,22,1,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(5,1,2,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(6,1,3,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(7,2,3,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(8,22,3,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(9,1,4,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(10,1,5,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(11,2,5,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(12,1,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(13,2,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(14,3,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(15,4,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(16,5,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(17,6,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(18,7,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(19,8,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(20,10,6,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(21,1,7,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(22,3,7,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(23,1,8,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(24,2,8,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(25,3,8,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(26,4,8,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(27,10,8,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(28,1,9,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(29,3,9,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(30,4,9,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(31,1,10,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(32,2,10,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(33,3,10,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(34,4,10,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(35,5,10,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(36,1,11,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(37,3,11,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(38,5,11,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(39,1,12,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(40,2,12,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(41,3,12,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(42,4,12,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(43,1,13,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(44,3,13,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(45,1,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(46,2,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(47,3,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(48,5,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(49,6,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(50,10,14,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(51,1,15,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(52,3,15,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(53,5,15,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(54,1,16,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(55,2,16,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(56,3,16,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(57,1,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(58,2,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(59,3,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(60,5,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(61,6,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(62,10,17,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(63,1,18,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(64,3,18,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(65,1,19,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(66,2,19,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(67,6,19,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(68,1,20,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(69,2,20,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(70,3,20,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(71,1,21,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(72,3,21,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(73,1,22,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(74,2,22,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(75,3,22,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(76,1,23,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(77,2,23,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(78,3,23,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(79,4,23,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(80,7,23,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(81,1,24,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(82,4,24,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(83,7,24,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(84,1,25,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(85,2,25,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(86,3,25,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(87,4,25,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(88,7,25,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(89,1,26,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(90,4,26,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(91,7,26,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(92,1,27,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(93,2,27,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(94,8,27,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(95,1,28,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(96,2,28,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(97,8,28,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(98,1,29,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(99,2,29,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(100,8,29,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(101,1,30,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(102,8,30,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(103,1,31,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(104,2,31,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(105,9,31,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(106,1,32,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(107,9,32,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(108,1,33,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(109,2,33,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(110,9,33,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(111,1,34,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(112,9,34,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(113,1,35,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(114,2,35,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(115,9,35,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(116,1,36,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(117,9,36,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(118,1,37,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(119,2,37,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(120,1,38,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(121,2,38,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(122,8,38,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(123,9,38,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(124,1,39,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(125,9,39,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(126,1,40,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(127,2,40,'2026-01-28 06:47:09','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(128,21,41,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(129,21,42,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(130,21,43,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(131,21,44,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(132,22,44,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(133,21,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(134,22,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(135,26,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(136,27,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(137,33,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(138,34,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(139,35,154,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(140,21,155,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(141,26,155,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(142,27,155,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(143,33,155,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(144,34,155,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(145,21,156,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(146,26,156,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(147,27,156,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(148,21,157,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(149,26,157,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(150,27,157,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(151,33,157,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(152,34,157,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(153,21,158,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(154,26,158,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(155,21,159,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(156,21,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(157,22,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(158,26,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(159,27,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(160,33,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(161,34,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(162,35,160,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(163,21,161,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(164,26,161,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(165,27,161,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(166,33,161,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(167,34,161,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(168,21,162,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(169,26,162,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(170,27,162,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(171,33,162,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(172,34,162,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(173,21,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(174,22,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(175,26,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(176,27,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(177,33,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(178,34,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(179,35,163,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(180,21,164,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(181,22,164,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(182,26,164,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(183,33,164,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(184,35,164,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(185,21,165,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(186,22,165,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(187,26,165,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(188,33,165,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(189,35,165,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(190,21,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(191,22,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(192,26,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(193,27,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(194,33,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(195,34,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(196,35,166,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(197,21,167,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(198,26,167,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(199,27,167,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(200,33,167,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(201,34,167,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(202,21,168,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(203,26,168,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(204,27,168,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(205,21,169,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(206,26,169,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(207,27,169,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(208,21,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(209,22,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(210,26,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(211,27,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(212,33,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(213,34,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(214,35,170,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(215,21,171,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(216,26,171,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(217,34,171,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(218,21,172,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(219,26,172,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(220,27,172,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(221,21,173,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(222,26,173,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(223,27,173,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(224,21,174,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(225,26,174,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(226,27,174,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(227,34,174,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(228,21,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(229,22,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(230,26,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(231,27,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(232,33,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(233,34,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(234,35,175,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(235,21,176,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(236,21,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(237,22,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(238,26,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(239,27,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(240,33,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(241,34,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(242,35,177,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(243,21,178,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(244,21,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(245,22,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(246,26,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(247,27,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(248,33,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(249,34,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(250,35,179,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(251,21,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(252,22,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(253,26,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(254,27,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(255,33,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(256,34,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(257,35,180,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(258,21,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(259,22,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(260,23,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(261,24,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(262,25,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(263,5,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(264,7,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(265,8,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(266,9,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(267,26,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(268,27,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(269,28,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(270,29,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(271,30,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(272,31,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(273,32,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(274,33,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(275,34,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(276,35,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(277,36,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(278,37,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(279,38,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(280,39,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(281,40,251,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(282,21,310,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(283,21,311,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(284,21,312,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(285,21,313,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(286,22,313,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(287,26,313,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(288,21,314,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(289,21,315,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(290,21,316,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(291,22,316,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(292,26,316,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(293,21,317,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(294,26,317,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(295,21,318,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(296,21,319,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(297,26,319,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(298,21,320,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(299,21,321,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(300,26,321,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(301,21,322,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(302,21,323,'2026-01-28 06:47:10','2026-01-28 07:09:55');
INSERT INTO role_api_permissions VALUES(303,21,324,'2026-01-31 09:47:40','2026-01-31 09:47:40');
INSERT INTO role_api_permissions VALUES(304,21,325,'2026-01-31 09:47:40','2026-01-31 09:47:40');
INSERT INTO role_api_permissions VALUES(305,21,326,'2026-01-31 09:47:40','2026-01-31 09:47:40');
INSERT INTO role_api_permissions VALUES(306,21,327,'2026-01-31 09:47:40','2026-01-31 09:47:40');
CREATE TABLE approval_delegates (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	delegate_id INTEGER NOT NULL, 
	scope VARCHAR(20), 
	template_ids JSON, 
	categories JSON, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	is_active BOOLEAN, 
	reason VARCHAR(200), 
	notify_original BOOLEAN, 
	notify_delegate BOOLEAN, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(delegate_id) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE approval_templates (
	id INTEGER NOT NULL, 
	template_code VARCHAR(50) NOT NULL, 
	template_name VARCHAR(100) NOT NULL, 
	category VARCHAR(20), 
	description TEXT, 
	icon VARCHAR(50), 
	entity_type VARCHAR(50), 
	form_schema JSON, 
	version INTEGER, 
	is_published BOOLEAN, 
	published_at DATETIME, 
	published_by INTEGER, 
	visible_scope JSON, 
	is_active BOOLEAN, 
	created_by INTEGER, 
	updated_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (template_code), 
	FOREIGN KEY(published_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);
INSERT INTO approval_templates VALUES(1,'PROJECT_TEMPLATE','项目审批模板','PROJECT','默认项目审批流程',NULL,'PROJECT',NULL,1,1,NULL,NULL,NULL,1,NULL,NULL,'2026-01-30 11:39:10.267300','2026-01-30 11:39:10.267475');
CREATE TABLE state_transition_logs (
	id INTEGER NOT NULL, 
	entity_type VARCHAR(50) NOT NULL, 
	entity_id INTEGER NOT NULL, 
	from_state VARCHAR(50) NOT NULL, 
	to_state VARCHAR(50) NOT NULL, 
	operator_id INTEGER, 
	operator_name VARCHAR(100), 
	action_type VARCHAR(50), 
	comment TEXT, 
	extra_data JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(operator_id) REFERENCES users (id)
);
CREATE TABLE vendors (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
	supplier_code VARCHAR(50) NOT NULL, 
	supplier_name VARCHAR(200) NOT NULL, 
	vendor_type VARCHAR(20) DEFAULT 'MATERIAL' NOT NULL, 
	business_license VARCHAR(100), 
	qualification TEXT, 
	capabilities JSON, 
	supplier_level VARCHAR(1), 
	payment_terms VARCHAR(50), 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	supplier_short_name VARCHAR(50), 
	supplier_type VARCHAR(20), 
	contact_person VARCHAR(50), 
	contact_phone VARCHAR(30), 
	contact_email VARCHAR(100), 
	address VARCHAR(500), 
	bank_name VARCHAR(100), 
	bank_account VARCHAR(50), 
	tax_number VARCHAR(50), 
	quality_rating NUMERIC(3, 2), 
	delivery_rating NUMERIC(3, 2), 
	service_rating NUMERIC(3, 2), 
	overall_rating NUMERIC(3, 2), 
	status VARCHAR(20), 
	cooperation_start DATETIME, 
	last_order_date DATETIME, 
	UNIQUE (supplier_code), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE bom_headers (
	id INTEGER NOT NULL, 
	bom_no VARCHAR(50) NOT NULL, 
	bom_name VARCHAR(200) NOT NULL, 
	project_id INTEGER NOT NULL, 
	machine_id INTEGER, 
	version VARCHAR(20), 
	is_latest BOOLEAN, 
	status VARCHAR(20), 
	total_items INTEGER, 
	total_amount NUMERIC(14, 2), 
	approved_by INTEGER, 
	approved_at DATETIME, 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (bom_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(machine_id) REFERENCES machines (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE material_shortages (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	bom_item_id INTEGER, 
	material_id INTEGER NOT NULL, 
	material_code VARCHAR(50) NOT NULL, 
	material_name VARCHAR(200) NOT NULL, 
	required_qty NUMERIC(10, 4) NOT NULL, 
	available_qty NUMERIC(10, 4), 
	shortage_qty NUMERIC(10, 4) NOT NULL, 
	required_date DATE, 
	status VARCHAR(20), 
	alert_level VARCHAR(20), 
	solution TEXT, 
	handler_id INTEGER, 
	resolved_at DATETIME, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(bom_item_id) REFERENCES bom_items (id), 
	FOREIGN KEY(material_id) REFERENCES materials (id), 
	FOREIGN KEY(handler_id) REFERENCES users (id)
);
CREATE TABLE shortage_reports (
	id INTEGER NOT NULL, 
	report_no VARCHAR(50) NOT NULL, 
	project_id INTEGER NOT NULL, 
	machine_id INTEGER, 
	work_order_id INTEGER, 
	reporter_id INTEGER NOT NULL, 
	report_time DATETIME NOT NULL, 
	report_location VARCHAR(200), 
	material_id INTEGER NOT NULL, 
	material_code VARCHAR(50) NOT NULL, 
	material_name VARCHAR(200) NOT NULL, 
	required_qty NUMERIC(10, 4) NOT NULL, 
	shortage_qty NUMERIC(10, 4) NOT NULL, 
	urgent_level VARCHAR(20), 
	status VARCHAR(20), 
	confirmed_by INTEGER, 
	confirmed_at DATETIME, 
	handler_id INTEGER, 
	resolved_at DATETIME, 
	solution_type VARCHAR(20), 
	solution_note TEXT, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (report_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(machine_id) REFERENCES machines (id), 
	FOREIGN KEY(work_order_id) REFERENCES work_order (id), 
	FOREIGN KEY(reporter_id) REFERENCES users (id), 
	FOREIGN KEY(material_id) REFERENCES materials (id), 
	FOREIGN KEY(confirmed_by) REFERENCES users (id), 
	FOREIGN KEY(handler_id) REFERENCES users (id)
);
CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	notification_type VARCHAR(30) NOT NULL, 
	source_type VARCHAR(30), 
	source_id INTEGER, 
	title VARCHAR(200) NOT NULL, 
	content TEXT, 
	link_url VARCHAR(500), 
	link_params JSON, 
	is_read BOOLEAN, 
	read_at DATETIME, 
	priority VARCHAR(10), 
	extra_data JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE notification_settings (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	email_enabled BOOLEAN, 
	sms_enabled BOOLEAN, 
	wechat_enabled BOOLEAN, 
	system_enabled BOOLEAN, 
	task_notifications BOOLEAN, 
	approval_notifications BOOLEAN, 
	alert_notifications BOOLEAN, 
	issue_notifications BOOLEAN, 
	project_notifications BOOLEAN, 
	quiet_hours_start VARCHAR(5), 
	quiet_hours_end VARCHAR(5), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE satisfaction_survey_templates (
	id INTEGER NOT NULL, 
	template_name VARCHAR(100) NOT NULL, 
	template_code VARCHAR(50) NOT NULL, 
	survey_type VARCHAR(20) NOT NULL, 
	questions JSON NOT NULL, 
	default_send_method VARCHAR(20), 
	default_deadline_days INTEGER, 
	usage_count INTEGER, 
	last_used_at DATETIME, 
	is_active BOOLEAN, 
	created_by INTEGER NOT NULL, 
	created_by_name VARCHAR(50), 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (template_code), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE service_records (
	id INTEGER NOT NULL, 
	record_no VARCHAR(50) NOT NULL, 
	service_type VARCHAR(20) NOT NULL, 
	project_id INTEGER NOT NULL, 
	machine_no VARCHAR(50), 
	customer_id INTEGER NOT NULL, 
	location VARCHAR(200), 
	service_date DATE NOT NULL, 
	start_time VARCHAR(10), 
	end_time VARCHAR(10), 
	duration_hours NUMERIC(5, 2), 
	service_engineer_id INTEGER NOT NULL, 
	service_engineer_name VARCHAR(50), 
	customer_contact VARCHAR(50), 
	customer_phone VARCHAR(20), 
	service_content TEXT NOT NULL, 
	service_result TEXT, 
	issues_found TEXT, 
	solution_provided TEXT, 
	photos JSON, 
	customer_satisfaction INTEGER, 
	customer_feedback TEXT, 
	customer_signed BOOLEAN, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (record_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(service_engineer_id) REFERENCES users (id)
);
CREATE TABLE service_tickets (
	id INTEGER NOT NULL, 
	ticket_no VARCHAR(50) NOT NULL, 
	project_id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	problem_type VARCHAR(20) NOT NULL, 
	problem_desc TEXT NOT NULL, 
	urgency VARCHAR(20) NOT NULL, 
	reported_by VARCHAR(50) NOT NULL, 
	reported_time DATETIME NOT NULL, 
	assigned_to_id INTEGER, 
	assigned_to_name VARCHAR(50), 
	assigned_time DATETIME, 
	status VARCHAR(20) NOT NULL, 
	response_time DATETIME, 
	resolved_time DATETIME, 
	solution TEXT, 
	root_cause TEXT, 
	preventive_action TEXT, 
	satisfaction INTEGER, 
	feedback TEXT, 
	timeline JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (ticket_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id), 
	FOREIGN KEY(assigned_to_id) REFERENCES users (id)
);
CREATE TABLE sla_policies (
	id INTEGER NOT NULL, 
	policy_name VARCHAR(100) NOT NULL, 
	policy_code VARCHAR(50) NOT NULL, 
	problem_type VARCHAR(20), 
	urgency VARCHAR(20), 
	response_time_hours INTEGER NOT NULL, 
	resolve_time_hours INTEGER NOT NULL, 
	warning_threshold_percent NUMERIC(5, 2), 
	priority INTEGER, 
	is_active BOOLEAN, 
	description TEXT, 
	remark TEXT, 
	created_by INTEGER, 
	created_by_name VARCHAR(50), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (policy_code), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE employee_hr_profiles (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	dept_level1 VARCHAR(50), 
	dept_level2 VARCHAR(50), 
	dept_level3 VARCHAR(50), 
	direct_supervisor VARCHAR(50), 
	position VARCHAR(100), 
	job_level VARCHAR(50), 
	hire_date DATE, 
	probation_end_date DATE, 
	is_confirmed BOOLEAN, 
	contract_sign_date DATE, 
	contract_end_date DATE, 
	gender VARCHAR(10), 
	birth_date DATE, 
	age INTEGER, 
	ethnicity VARCHAR(20), 
	political_status VARCHAR(20), 
	marital_status VARCHAR(20), 
	height_cm NUMERIC(5, 1), 
	weight_kg NUMERIC(5, 1), 
	native_place VARCHAR(50), 
	home_address VARCHAR(200), 
	current_address VARCHAR(200), 
	emergency_contact VARCHAR(50), 
	emergency_phone VARCHAR(20), 
	graduate_school VARCHAR(100), 
	graduate_date VARCHAR(20), 
	major VARCHAR(100), 
	education_level VARCHAR(20), 
	foreign_language VARCHAR(50), 
	hobbies VARCHAR(200), 
	bank_account VARCHAR(50), 
	insurance_base NUMERIC(10, 2), 
	social_security_no VARCHAR(50), 
	housing_fund_no VARCHAR(50), 
	resignation_date DATE, 
	old_department VARCHAR(100), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (employee_id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);
CREATE TABLE hr_transactions (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	transaction_type VARCHAR(20) NOT NULL, 
	transaction_date DATE NOT NULL, 
	status VARCHAR(20), 
	onboard_date DATE, 
	probation_months INTEGER, 
	initial_position VARCHAR(100), 
	initial_department VARCHAR(100), 
	initial_salary NUMERIC(12, 2), 
	resignation_date DATE, 
	last_working_date DATE, 
	resignation_reason VARCHAR(50), 
	resignation_remark TEXT, 
	handover_status VARCHAR(20), 
	handover_to INTEGER, 
	confirmation_date DATE, 
	probation_evaluation VARCHAR(20), 
	confirmation_salary NUMERIC(12, 2), 
	from_department VARCHAR(100), 
	to_department VARCHAR(100), 
	from_position VARCHAR(100), 
	to_position VARCHAR(100), 
	transfer_reason TEXT, 
	from_level VARCHAR(50), 
	to_level VARCHAR(50), 
	from_salary NUMERIC(12, 2), 
	to_salary NUMERIC(12, 2), 
	salary_change_ratio NUMERIC(5, 2), 
	promotion_reason TEXT, 
	applicant_id INTEGER, 
	approver_id INTEGER, 
	approved_at DATETIME, 
	approval_remark TEXT, 
	remark TEXT, 
	attachments TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(handover_to) REFERENCES employees (id), 
	FOREIGN KEY(applicant_id) REFERENCES users (id), 
	FOREIGN KEY(approver_id) REFERENCES users (id)
);
CREATE TABLE employee_contracts (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	contract_no VARCHAR(50), 
	contract_type VARCHAR(20) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE, 
	duration_months INTEGER, 
	position VARCHAR(100), 
	department VARCHAR(100), 
	work_location VARCHAR(200), 
	base_salary NUMERIC(12, 2), 
	probation_salary NUMERIC(12, 2), 
	probation_months INTEGER, 
	status VARCHAR(20), 
	sign_date DATE, 
	termination_date DATE, 
	termination_reason TEXT, 
	is_renewed BOOLEAN, 
	renewed_contract_id INTEGER, 
	renewal_count INTEGER, 
	reminder_sent BOOLEAN, 
	reminder_sent_at DATETIME, 
	contract_file VARCHAR(500), 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(renewed_contract_id) REFERENCES employee_contracts (id)
);
CREATE TABLE hourly_rate_configs (
	id INTEGER NOT NULL, 
	config_type VARCHAR(20) NOT NULL, 
	user_id INTEGER, 
	role_id INTEGER, 
	dept_id INTEGER, 
	hourly_rate NUMERIC(10, 2) NOT NULL, 
	effective_date DATE, 
	expiry_date DATE, 
	is_active BOOLEAN, 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(dept_id) REFERENCES departments (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE project_financials (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	contract_amount NUMERIC(14, 2), 
	budget_amount NUMERIC(14, 2), 
	actual_cost NUMERIC(14, 2), 
	invoice_issued BOOLEAN, 
	final_payment_completed BOOLEAN, 
	final_payment_date DATE, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE project_erp (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	erp_synced BOOLEAN, 
	erp_sync_time DATETIME, 
	erp_order_no VARCHAR(50), 
	erp_sync_status VARCHAR(20), 
	erp_sync_error TEXT, 
	erp_last_sync_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE project_warranties (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	warranty_period_months INTEGER, 
	warranty_start_date DATE, 
	warranty_end_date DATE, 
	warranty_status VARCHAR(20), 
	warranty_notes TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE project_implementations (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	implementation_address VARCHAR(500), 
	test_encryption VARCHAR(100), 
	site_contact_name VARCHAR(50), 
	site_contact_phone VARCHAR(30), 
	site_contact_email VARCHAR(100), 
	site_conditions TEXT, 
	installation_requirements TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE project_presales (
	id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	source_lead_id VARCHAR(50), 
	evaluation_score NUMERIC(5, 2), 
	predicted_win_rate NUMERIC(5, 4), 
	outcome VARCHAR(20), 
	loss_reason VARCHAR(50), 
	loss_reason_detail TEXT, 
	competitor_info TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE node_tasks (
	id INTEGER NOT NULL, 
	node_instance_id INTEGER NOT NULL, 
	task_code VARCHAR(30) NOT NULL, 
	task_name VARCHAR(200) NOT NULL, 
	description TEXT, 
	sequence INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	estimated_hours INTEGER, 
	actual_hours INTEGER, 
	planned_start_date DATE, 
	planned_end_date DATE, 
	actual_start_date DATE, 
	actual_end_date DATE, 
	assignee_id INTEGER, 
	completed_by INTEGER, 
	completed_at DATETIME, 
	priority VARCHAR(20), 
	tags VARCHAR(200), 
	attachments TEXT, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(node_instance_id) REFERENCES project_node_instances (id) ON DELETE CASCADE, 
	FOREIGN KEY(assignee_id) REFERENCES users (id), 
	FOREIGN KEY(completed_by) REFERENCES users (id)
);
CREATE TABLE project_budgets (
	id INTEGER NOT NULL, 
	budget_no VARCHAR(50) NOT NULL, 
	project_id INTEGER NOT NULL, 
	budget_name VARCHAR(200) NOT NULL, 
	budget_type VARCHAR(20), 
	version VARCHAR(20), 
	total_amount NUMERIC(14, 2) NOT NULL, 
	budget_breakdown JSON, 
	status VARCHAR(20), 
	submitted_at DATETIME, 
	submitted_by INTEGER, 
	approved_by INTEGER, 
	approved_at DATETIME, 
	approval_note TEXT, 
	effective_date DATE, 
	expiry_date DATE, 
	is_active BOOLEAN, 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (budget_no), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(submitted_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE project_cost_allocation_rules (
	id INTEGER NOT NULL, 
	rule_name VARCHAR(100) NOT NULL, 
	rule_type VARCHAR(20) NOT NULL, 
	allocation_basis VARCHAR(20) NOT NULL, 
	allocation_formula TEXT, 
	cost_type VARCHAR(50), 
	cost_category VARCHAR(50), 
	project_ids JSON, 
	is_active BOOLEAN, 
	effective_date DATE, 
	expiry_date DATE, 
	remark TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE contract_amendments (
	id INTEGER NOT NULL, 
	contract_id INTEGER NOT NULL, 
	amendment_no VARCHAR(50) NOT NULL, 
	amendment_type VARCHAR(20) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	reason TEXT, 
	old_value TEXT, 
	new_value TEXT, 
	amount_change NUMERIC(12, 2), 
	schedule_impact TEXT, 
	other_impact TEXT, 
	requestor_id INTEGER NOT NULL, 
	request_date DATE NOT NULL, 
	status VARCHAR(20), 
	approver_id INTEGER, 
	approval_date DATE, 
	approval_comment TEXT, 
	attachments TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(contract_id) REFERENCES contracts (id), 
	UNIQUE (amendment_no), 
	FOREIGN KEY(requestor_id) REFERENCES users (id), 
	FOREIGN KEY(approver_id) REFERENCES users (id)
);
CREATE TABLE lead_follow_ups (
	id INTEGER NOT NULL, 
	lead_id INTEGER NOT NULL, 
	follow_up_type VARCHAR(20) NOT NULL, 
	content TEXT NOT NULL, 
	next_action TEXT, 
	next_action_at DATETIME, 
	created_by INTEGER NOT NULL, 
	attachments TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lead_id) REFERENCES leads (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE approval_flow_definitions (
	id INTEGER NOT NULL, 
	template_id INTEGER NOT NULL, 
	flow_name VARCHAR(100) NOT NULL, 
	description TEXT, 
	is_default BOOLEAN, 
	version INTEGER, 
	is_active BOOLEAN, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(template_id) REFERENCES approval_templates (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
INSERT INTO approval_flow_definitions VALUES(1,1,'项目审批默认流程','项目经理审批',1,1,1,NULL,'2026-01-30 11:39:10.268366','2026-01-30 11:39:10.268472');
CREATE TABLE approval_template_versions (
	id INTEGER NOT NULL, 
	template_id INTEGER NOT NULL, 
	version INTEGER NOT NULL, 
	template_name VARCHAR(100), 
	form_schema JSON, 
	flow_snapshot JSON, 
	change_log TEXT, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(template_id) REFERENCES approval_templates (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE material_suppliers (
	id INTEGER NOT NULL, 
	material_id INTEGER NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	supplier_material_code VARCHAR(100), 
	price NUMERIC(12, 4), 
	currency VARCHAR(10), 
	lead_time_days INTEGER, 
	min_order_qty NUMERIC(10, 4), 
	is_preferred BOOLEAN, 
	is_active BOOLEAN, 
	valid_from DATE, 
	valid_to DATE, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(material_id) REFERENCES materials (id), 
	FOREIGN KEY(supplier_id) REFERENCES vendors (id)
);
CREATE TABLE material_arrivals (
	id INTEGER NOT NULL, 
	arrival_no VARCHAR(50) NOT NULL, 
	shortage_report_id INTEGER, 
	purchase_order_id INTEGER, 
	purchase_order_item_id INTEGER, 
	material_id INTEGER NOT NULL, 
	material_code VARCHAR(50) NOT NULL, 
	material_name VARCHAR(200) NOT NULL, 
	expected_qty NUMERIC(10, 4) NOT NULL, 
	supplier_id INTEGER, 
	supplier_name VARCHAR(200), 
	expected_date DATE NOT NULL, 
	actual_date DATE, 
	is_delayed BOOLEAN, 
	delay_days INTEGER, 
	status VARCHAR(20), 
	received_qty NUMERIC(10, 4), 
	received_by INTEGER, 
	received_at DATETIME, 
	follow_up_count INTEGER, 
	last_follow_up_at DATETIME, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (arrival_no), 
	FOREIGN KEY(shortage_report_id) REFERENCES shortage_reports (id), 
	FOREIGN KEY(purchase_order_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(purchase_order_item_id) REFERENCES purchase_order_items (id), 
	FOREIGN KEY(material_id) REFERENCES materials (id), 
	FOREIGN KEY(supplier_id) REFERENCES vendors (id), 
	FOREIGN KEY(received_by) REFERENCES users (id)
);
CREATE TABLE material_substitutions (
	id INTEGER NOT NULL, 
	substitution_no VARCHAR(50) NOT NULL, 
	shortage_report_id INTEGER, 
	project_id INTEGER NOT NULL, 
	bom_item_id INTEGER, 
	original_material_id INTEGER NOT NULL, 
	original_material_code VARCHAR(50) NOT NULL, 
	original_material_name VARCHAR(200) NOT NULL, 
	original_qty NUMERIC(10, 4) NOT NULL, 
	substitute_material_id INTEGER NOT NULL, 
	substitute_material_code VARCHAR(50) NOT NULL, 
	substitute_material_name VARCHAR(200) NOT NULL, 
	substitute_qty NUMERIC(10, 4) NOT NULL, 
	substitution_reason TEXT NOT NULL, 
	technical_impact TEXT, 
	cost_impact NUMERIC(14, 2), 
	status VARCHAR(20), 
	tech_approver_id INTEGER, 
	tech_approved_at DATETIME, 
	tech_approval_note TEXT, 
	prod_approver_id INTEGER, 
	prod_approved_at DATETIME, 
	prod_approval_note TEXT, 
	executed_at DATETIME, 
	executed_by INTEGER, 
	execution_note TEXT, 
	remark TEXT, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (substitution_no), 
	FOREIGN KEY(shortage_report_id) REFERENCES shortage_reports (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(bom_item_id) REFERENCES bom_items (id), 
	FOREIGN KEY(original_material_id) REFERENCES materials (id), 
	FOREIGN KEY(substitute_material_id) REFERENCES materials (id), 
	FOREIGN KEY(tech_approver_id) REFERENCES users (id), 
	FOREIGN KEY(prod_approver_id) REFERENCES users (id), 
	FOREIGN KEY(executed_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE material_transfers (
	id INTEGER NOT NULL, 
	transfer_no VARCHAR(50) NOT NULL, 
	shortage_report_id INTEGER, 
	from_project_id INTEGER, 
	from_location VARCHAR(200), 
	to_project_id INTEGER NOT NULL, 
	to_location VARCHAR(200), 
	material_id INTEGER NOT NULL, 
	material_code VARCHAR(50) NOT NULL, 
	material_name VARCHAR(200) NOT NULL, 
	transfer_qty NUMERIC(10, 4) NOT NULL, 
	available_qty NUMERIC(10, 4), 
	transfer_reason TEXT NOT NULL, 
	urgent_level VARCHAR(20), 
	status VARCHAR(20), 
	approver_id INTEGER, 
	approved_at DATETIME, 
	approval_note TEXT, 
	executed_at DATETIME, 
	executed_by INTEGER, 
	actual_qty NUMERIC(10, 4), 
	execution_note TEXT, 
	remark TEXT, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (transfer_no), 
	FOREIGN KEY(shortage_report_id) REFERENCES shortage_reports (id), 
	FOREIGN KEY(from_project_id) REFERENCES projects (id), 
	FOREIGN KEY(to_project_id) REFERENCES projects (id), 
	FOREIGN KEY(material_id) REFERENCES materials (id), 
	FOREIGN KEY(approver_id) REFERENCES users (id), 
	FOREIGN KEY(executed_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE service_ticket_projects (
	id INTEGER NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	project_id INTEGER NOT NULL, 
	is_primary BOOLEAN, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES service_tickets (id) ON DELETE CASCADE, 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE service_ticket_cc_users (
	id INTEGER NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	notified_at DATETIME, 
	read_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES service_tickets (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE sla_monitors (
	id INTEGER NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	policy_id INTEGER NOT NULL, 
	response_deadline DATETIME NOT NULL, 
	resolve_deadline DATETIME NOT NULL, 
	actual_response_time DATETIME, 
	actual_resolve_time DATETIME, 
	response_status VARCHAR(20) NOT NULL, 
	resolve_status VARCHAR(20) NOT NULL, 
	response_time_diff_hours NUMERIC(10, 2), 
	resolve_time_diff_hours NUMERIC(10, 2), 
	response_warning_sent BOOLEAN, 
	resolve_warning_sent BOOLEAN, 
	response_warning_sent_at DATETIME, 
	resolve_warning_sent_at DATETIME, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES service_tickets (id), 
	FOREIGN KEY(policy_id) REFERENCES sla_policies (id)
);
CREATE TABLE contract_reminders (
	id INTEGER NOT NULL, 
	contract_id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	reminder_type VARCHAR(20) NOT NULL, 
	reminder_date DATE NOT NULL, 
	contract_end_date DATE NOT NULL, 
	days_until_expiry INTEGER, 
	status VARCHAR(20), 
	handled_at DATETIME, 
	handled_by INTEGER, 
	handle_action VARCHAR(20), 
	handle_remark TEXT, 
	notified_at DATETIME, 
	notification_method VARCHAR(50), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(contract_id) REFERENCES employee_contracts (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(handled_by) REFERENCES users (id)
);
CREATE TABLE salary_records (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	effective_date DATE NOT NULL, 
	base_salary NUMERIC(12, 2) NOT NULL, 
	position_allowance NUMERIC(10, 2), 
	skill_allowance NUMERIC(10, 2), 
	performance_bonus NUMERIC(10, 2), 
	other_allowance NUMERIC(10, 2), 
	total_salary NUMERIC(12, 2), 
	change_type VARCHAR(20), 
	change_reason TEXT, 
	previous_salary NUMERIC(12, 2), 
	change_amount NUMERIC(12, 2), 
	change_ratio NUMERIC(5, 2), 
	transaction_id INTEGER, 
	is_current BOOLEAN, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(transaction_id) REFERENCES hr_transactions (id)
);
CREATE TABLE project_budget_items (
	id INTEGER NOT NULL, 
	budget_id INTEGER NOT NULL, 
	item_no INTEGER NOT NULL, 
	cost_category VARCHAR(50) NOT NULL, 
	cost_item VARCHAR(200) NOT NULL, 
	description TEXT, 
	budget_amount NUMERIC(14, 2) NOT NULL, 
	machine_id INTEGER, 
	remark TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(budget_id) REFERENCES project_budgets (id), 
	FOREIGN KEY(machine_id) REFERENCES machines (id)
);
CREATE TABLE approval_node_definitions (
	id INTEGER NOT NULL, 
	flow_id INTEGER NOT NULL, 
	node_code VARCHAR(50), 
	node_name VARCHAR(100) NOT NULL, 
	node_order INTEGER NOT NULL, 
	node_type VARCHAR(20) NOT NULL, 
	approval_mode VARCHAR(20), 
	approver_type VARCHAR(30), 
	approver_config JSON, 
	condition_expression TEXT, 
	branches JSON, 
	can_add_approver BOOLEAN, 
	can_transfer BOOLEAN, 
	can_delegate BOOLEAN, 
	can_reject_to VARCHAR(20), 
	timeout_hours INTEGER, 
	timeout_action VARCHAR(20), 
	timeout_remind_hours INTEGER, 
	notify_config JSON, 
	eval_form_schema JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, is_active BOOLEAN DEFAULT 1, 
	PRIMARY KEY (id), 
	FOREIGN KEY(flow_id) REFERENCES approval_flow_definitions (id)
);
INSERT INTO approval_node_definitions VALUES(1,1,'PM_APPROVAL','项目经理审批',1,'APPROVAL','SINGLE','FORM_FIELD','{"field_name": "pm_id"}',NULL,NULL,0,1,1,'START',NULL,NULL,NULL,NULL,NULL,'2026-01-30 11:39:10.269180','2026-01-30 11:39:10.269278',1);
CREATE TABLE approval_routing_rules (
	id INTEGER NOT NULL, 
	template_id INTEGER NOT NULL, 
	flow_id INTEGER NOT NULL, 
	rule_name VARCHAR(100) NOT NULL, 
	rule_order INTEGER NOT NULL, 
	description TEXT, 
	conditions JSON NOT NULL, 
	is_active BOOLEAN, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(template_id) REFERENCES approval_templates (id), 
	FOREIGN KEY(flow_id) REFERENCES approval_flow_definitions (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE arrival_follow_ups (
	id INTEGER NOT NULL, 
	arrival_id INTEGER NOT NULL, 
	follow_up_type VARCHAR(20), 
	follow_up_note TEXT NOT NULL, 
	followed_by INTEGER NOT NULL, 
	followed_at DATETIME NOT NULL, 
	supplier_response TEXT, 
	next_follow_up_date DATE, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(arrival_id) REFERENCES material_arrivals (id), 
	FOREIGN KEY(followed_by) REFERENCES users (id)
);
CREATE TABLE approval_instances (
	id INTEGER NOT NULL, 
	instance_no VARCHAR(50) NOT NULL, 
	template_id INTEGER NOT NULL, 
	flow_id INTEGER NOT NULL, 
	entity_type VARCHAR(50), 
	entity_id INTEGER, 
	initiator_id INTEGER NOT NULL, 
	initiator_dept_id INTEGER, 
	form_data JSON, 
	status VARCHAR(20) NOT NULL, 
	current_node_id INTEGER, 
	current_node_order INTEGER, 
	urgency VARCHAR(10), 
	title VARCHAR(200), 
	summary TEXT, 
	submitted_at DATETIME, 
	completed_at DATETIME, 
	final_comment TEXT, 
	final_approver_id INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, initiator_name VARCHAR(100), 
	PRIMARY KEY (id), 
	UNIQUE (instance_no), 
	FOREIGN KEY(template_id) REFERENCES approval_templates (id), 
	FOREIGN KEY(flow_id) REFERENCES approval_flow_definitions (id), 
	FOREIGN KEY(initiator_id) REFERENCES users (id), 
	FOREIGN KEY(initiator_dept_id) REFERENCES departments (id), 
	FOREIGN KEY(current_node_id) REFERENCES approval_node_definitions (id), 
	FOREIGN KEY(final_approver_id) REFERENCES users (id)
);
INSERT INTO approval_instances VALUES(1,'AP2601300001',1,1,'PROJECT',5,22,NULL,'{"pm_id": 22, "pm_name": "Project.Smoke", "project_name": "PRJAPP Smoke Project", "contract_amount": 100000.0, "budget_amount": 85000.0}','APPROVED',1,NULL,'NORMAL','审批 PRJAPP-8DA55A','','2026-01-30 11:44:59.987379','2026-01-30 11:44:59.996912',NULL,NULL,'2026-01-30 11:44:59.987879','2026-01-30 11:44:59.997754','Project.Smoke');
INSERT INTO approval_instances VALUES(2,'AP2601300002',1,1,'PROJECT',6,22,NULL,'{"pm_id": 22, "pm_name": "Project.Smoke", "project_name": "PRJAPP Smoke Project", "contract_amount": 100000.0, "budget_amount": 85000.0}','CANCELLED',1,NULL,'NORMAL','审批 PRJWD-B3F216','','2026-01-30 11:45:00.002454','2026-01-30 11:45:00.007245',NULL,NULL,'2026-01-30 11:45:00.002665','2026-01-30 11:45:00.007835','Project.Smoke');
CREATE TABLE approval_comments (
	id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	user_name VARCHAR(50), 
	content TEXT NOT NULL, 
	attachments JSON, 
	parent_id INTEGER, 
	reply_to_user_id INTEGER, 
	mentioned_user_ids JSON, 
	is_deleted BOOLEAN, 
	deleted_at DATETIME, 
	deleted_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(parent_id) REFERENCES approval_comments (id), 
	FOREIGN KEY(reply_to_user_id) REFERENCES users (id), 
	FOREIGN KEY(deleted_by) REFERENCES users (id)
);
CREATE TABLE approval_tasks (
	id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	node_id INTEGER NOT NULL, 
	task_type VARCHAR(20), 
	task_order INTEGER, 
	assignee_id INTEGER NOT NULL, 
	assignee_name VARCHAR(50), 
	assignee_dept_id INTEGER, 
	assignee_type VARCHAR(20), 
	original_assignee_id INTEGER, 
	status VARCHAR(20), 
	action VARCHAR(20), 
	comment TEXT, 
	attachments JSON, 
	eval_data JSON, 
	return_to_node_id INTEGER, 
	due_at DATETIME, 
	reminded_at DATETIME, 
	remind_count INTEGER, 
	completed_at DATETIME, 
	is_countersign BOOLEAN, 
	countersign_weight INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(node_id) REFERENCES approval_node_definitions (id), 
	FOREIGN KEY(assignee_id) REFERENCES users (id), 
	FOREIGN KEY(assignee_dept_id) REFERENCES departments (id), 
	FOREIGN KEY(original_assignee_id) REFERENCES users (id), 
	FOREIGN KEY(return_to_node_id) REFERENCES approval_node_definitions (id)
);
INSERT INTO approval_tasks VALUES(1,1,1,'APPROVAL',1,22,NULL,NULL,'NORMAL',NULL,'COMPLETED','APPROVE','Auto approve in smoke test',NULL,NULL,NULL,NULL,NULL,0,'2026-01-30 11:44:59.995900',0,1,'2026-01-30 11:44:59.992629','2026-01-30 11:44:59.998622');
INSERT INTO approval_tasks VALUES(2,2,1,'APPROVAL',1,22,NULL,NULL,'NORMAL',NULL,'CANCELLED',NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,0,1,'2026-01-30 11:45:00.004610','2026-01-30 11:45:00.007027');
CREATE TABLE approval_carbon_copies (
	id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	node_id INTEGER, 
	cc_user_id INTEGER NOT NULL, 
	cc_user_name VARCHAR(50), 
	cc_source VARCHAR(20), 
	added_by INTEGER, 
	is_read BOOLEAN, 
	read_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(cc_user_id) REFERENCES users (id), 
	FOREIGN KEY(added_by) REFERENCES users (id)
);
CREATE TABLE approval_countersign_results (
	id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	node_id INTEGER NOT NULL, 
	total_count INTEGER, 
	approved_count INTEGER, 
	rejected_count INTEGER, 
	pending_count INTEGER, 
	final_result VARCHAR(20), 
	result_reason TEXT, 
	summary_data JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(node_id) REFERENCES approval_node_definitions (id)
);
CREATE TABLE approval_delegate_logs (
	id INTEGER NOT NULL, 
	delegate_config_id INTEGER NOT NULL, 
	task_id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	original_user_id INTEGER NOT NULL, 
	delegate_user_id INTEGER NOT NULL, 
	action VARCHAR(20), 
	action_at DATETIME, 
	original_notified BOOLEAN, 
	original_notified_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(delegate_config_id) REFERENCES approval_delegates (id), 
	FOREIGN KEY(task_id) REFERENCES approval_tasks (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(original_user_id) REFERENCES users (id), 
	FOREIGN KEY(delegate_user_id) REFERENCES users (id)
);
CREATE TABLE approval_action_logs (
	id INTEGER NOT NULL, 
	instance_id INTEGER NOT NULL, 
	task_id INTEGER, 
	node_id INTEGER, 
	operator_id INTEGER NOT NULL, 
	operator_name VARCHAR(50), 
	action VARCHAR(30) NOT NULL, 
	action_detail JSON, 
	comment TEXT, 
	attachments JSON, 
	before_status VARCHAR(20), 
	after_status VARCHAR(20), 
	before_node_id INTEGER, 
	after_node_id INTEGER, 
	action_at DATETIME NOT NULL, 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(500), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instance_id) REFERENCES approval_instances (id), 
	FOREIGN KEY(task_id) REFERENCES approval_tasks (id), 
	FOREIGN KEY(node_id) REFERENCES approval_node_definitions (id), 
	FOREIGN KEY(operator_id) REFERENCES users (id)
);
INSERT INTO approval_action_logs VALUES(1,1,NULL,NULL,22,'Project.Smoke','SUBMIT','null',NULL,'null',NULL,NULL,NULL,NULL,'2026-01-30 11:44:59.989483',NULL,NULL,'2026-01-30 11:44:59.991895','2026-01-30 11:44:59.991995');
INSERT INTO approval_action_logs VALUES(2,1,1,1,22,'Project.Smoke','APPROVE','null','Auto approve in smoke test','null','PENDING',NULL,NULL,NULL,'2026-01-30 11:44:59.996425',NULL,NULL,'2026-01-30 11:44:59.998256','2026-01-30 11:44:59.998354');
INSERT INTO approval_action_logs VALUES(3,2,NULL,NULL,22,'Project.Smoke','SUBMIT','null',NULL,'null',NULL,NULL,NULL,NULL,'2026-01-30 11:45:00.003613',NULL,NULL,'2026-01-30 11:45:00.004337','2026-01-30 11:45:00.004430');
INSERT INTO approval_action_logs VALUES(4,2,NULL,NULL,22,'Project.Smoke','WITHDRAW','null','Smoke test withdraw','null','PENDING','CANCELLED',NULL,NULL,'2026-01-30 11:45:00.008143',NULL,NULL,'2026-01-30 11:45:00.008313','2026-01-30 11:45:00.008408');
CREATE TABLE project_risk_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- 风险等级变化
    old_risk_level VARCHAR(20),  -- 原风险等级: LOW/MEDIUM/HIGH/CRITICAL
    new_risk_level VARCHAR(20),  -- 新风险等级: LOW/MEDIUM/HIGH/CRITICAL

    -- 风险因子（JSON格式存储详细数据）
    risk_factors JSON,  -- 风险因子详情

    -- 触发信息
    triggered_by VARCHAR(50) DEFAULT 'SYSTEM',  -- 触发者：SYSTEM/MANUAL/用户ID
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 触发时间

    -- 备注
    remarks TEXT,  -- 备注说明

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO project_risk_history VALUES(1,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.580582"}','SYSTEM','2026-01-30 15:24:37.581167',NULL,'2026-01-30 15:24:37.581573','2026-01-30 15:24:37.581574');
INSERT INTO project_risk_history VALUES(2,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.584153"}','SYSTEM','2026-01-30 15:24:37.584293',NULL,'2026-01-30 15:24:37.584380','2026-01-30 15:24:37.584380');
INSERT INTO project_risk_history VALUES(3,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.585620"}','SYSTEM','2026-01-30 15:24:37.585749',NULL,'2026-01-30 15:24:37.585827','2026-01-30 15:24:37.585828');
INSERT INTO project_risk_history VALUES(4,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.586930"}','SYSTEM','2026-01-30 15:24:37.587058',NULL,'2026-01-30 15:24:37.587128','2026-01-30 15:24:37.587129');
INSERT INTO project_risk_history VALUES(5,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.588196"}','SYSTEM','2026-01-30 15:24:37.588317',NULL,'2026-01-30 15:24:37.588385','2026-01-30 15:24:37.588385');
INSERT INTO project_risk_history VALUES(6,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.589463"}','SYSTEM','2026-01-30 15:24:37.589582',NULL,'2026-01-30 15:24:37.589647','2026-01-30 15:24:37.589648');
INSERT INTO project_risk_history VALUES(7,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.377682"}','SYSTEM','2026-01-30 15:35:17.378493',NULL,'2026-01-30 15:35:17.378948','2026-01-30 15:35:17.378949');
INSERT INTO project_risk_history VALUES(8,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.381277"}','SYSTEM','2026-01-30 15:35:17.381429',NULL,'2026-01-30 15:35:17.381529','2026-01-30 15:35:17.381530');
INSERT INTO project_risk_history VALUES(9,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.382845"}','SYSTEM','2026-01-30 15:35:17.383003',NULL,'2026-01-30 15:35:17.383086','2026-01-30 15:35:17.383087');
INSERT INTO project_risk_history VALUES(10,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.384287"}','SYSTEM','2026-01-30 15:35:17.384428',NULL,'2026-01-30 15:35:17.384503','2026-01-30 15:35:17.384504');
INSERT INTO project_risk_history VALUES(11,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.385811"}','SYSTEM','2026-01-30 15:35:17.385971',NULL,'2026-01-30 15:35:17.386057','2026-01-30 15:35:17.386058');
INSERT INTO project_risk_history VALUES(12,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:35:17.387292"}','SYSTEM','2026-01-30 15:35:17.387428',NULL,'2026-01-30 15:35:17.387500','2026-01-30 15:35:17.387500');
INSERT INTO project_risk_history VALUES(13,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.947252"}','SYSTEM','2026-01-30 15:37:59.947878',NULL,'2026-01-30 15:37:59.948177','2026-01-30 15:37:59.948177');
INSERT INTO project_risk_history VALUES(14,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.950217"}','SYSTEM','2026-01-30 15:37:59.950398',NULL,'2026-01-30 15:37:59.950492','2026-01-30 15:37:59.950493');
INSERT INTO project_risk_history VALUES(15,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.951774"}','SYSTEM','2026-01-30 15:37:59.951915',NULL,'2026-01-30 15:37:59.951991','2026-01-30 15:37:59.951991');
INSERT INTO project_risk_history VALUES(16,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.953097"}','SYSTEM','2026-01-30 15:37:59.953233',NULL,'2026-01-30 15:37:59.953303','2026-01-30 15:37:59.953304');
INSERT INTO project_risk_history VALUES(17,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.954394"}','SYSTEM','2026-01-30 15:37:59.954527',NULL,'2026-01-30 15:37:59.954598','2026-01-30 15:37:59.954599');
INSERT INTO project_risk_history VALUES(18,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.955653"}','SYSTEM','2026-01-30 15:37:59.955784',NULL,'2026-01-30 15:37:59.955854','2026-01-30 15:37:59.955855');
INSERT INTO project_risk_history VALUES(19,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.543616"}','SYSTEM','2026-01-30 15:42:39.544255',NULL,'2026-01-30 15:42:39.544570','2026-01-30 15:42:39.544571');
INSERT INTO project_risk_history VALUES(20,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.547033"}','SYSTEM','2026-01-30 15:42:39.547200',NULL,'2026-01-30 15:42:39.547294','2026-01-30 15:42:39.547294');
INSERT INTO project_risk_history VALUES(21,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.548574"}','SYSTEM','2026-01-30 15:42:39.548721',NULL,'2026-01-30 15:42:39.548803','2026-01-30 15:42:39.548804');
INSERT INTO project_risk_history VALUES(22,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.549977"}','SYSTEM','2026-01-30 15:42:39.550124',NULL,'2026-01-30 15:42:39.550199','2026-01-30 15:42:39.550200');
INSERT INTO project_risk_history VALUES(23,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.551278"}','SYSTEM','2026-01-30 15:42:39.551416',NULL,'2026-01-30 15:42:39.551488','2026-01-30 15:42:39.551488');
INSERT INTO project_risk_history VALUES(24,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.552576"}','SYSTEM','2026-01-30 15:42:39.552711',NULL,'2026-01-30 15:42:39.552781','2026-01-30 15:42:39.552781');
INSERT INTO project_risk_history VALUES(25,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.346682"}','SYSTEM','2026-01-30 15:45:07.347256',NULL,'2026-01-30 15:45:07.347662','2026-01-30 15:45:07.347662');
INSERT INTO project_risk_history VALUES(26,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.350120"}','SYSTEM','2026-01-30 15:45:07.350281',NULL,'2026-01-30 15:45:07.350374','2026-01-30 15:45:07.350375');
INSERT INTO project_risk_history VALUES(27,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.351595"}','SYSTEM','2026-01-30 15:45:07.351740',NULL,'2026-01-30 15:45:07.351820','2026-01-30 15:45:07.351820');
INSERT INTO project_risk_history VALUES(28,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.353021"}','SYSTEM','2026-01-30 15:45:07.353181',NULL,'2026-01-30 15:45:07.353278','2026-01-30 15:45:07.353279');
INSERT INTO project_risk_history VALUES(29,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.354405"}','SYSTEM','2026-01-30 15:45:07.354542',NULL,'2026-01-30 15:45:07.354616','2026-01-30 15:45:07.354617');
INSERT INTO project_risk_history VALUES(30,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.355714"}','SYSTEM','2026-01-30 15:45:07.355848',NULL,'2026-01-30 15:45:07.355918','2026-01-30 15:45:07.355919');
INSERT INTO project_risk_history VALUES(31,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.852532"}','SYSTEM','2026-01-30 15:47:37.853165',NULL,'2026-01-30 15:47:37.853593','2026-01-30 15:47:37.853594');
INSERT INTO project_risk_history VALUES(32,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.855981"}','SYSTEM','2026-01-30 15:47:37.856135',NULL,'2026-01-30 15:47:37.856221','2026-01-30 15:47:37.856222');
INSERT INTO project_risk_history VALUES(33,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.857460"}','SYSTEM','2026-01-30 15:47:37.857607',NULL,'2026-01-30 15:47:37.857683','2026-01-30 15:47:37.857684');
INSERT INTO project_risk_history VALUES(34,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.858922"}','SYSTEM','2026-01-30 15:47:37.859074',NULL,'2026-01-30 15:47:37.859157','2026-01-30 15:47:37.859157');
INSERT INTO project_risk_history VALUES(35,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.860338"}','SYSTEM','2026-01-30 15:47:37.860482',NULL,'2026-01-30 15:47:37.860556','2026-01-30 15:47:37.860557');
INSERT INTO project_risk_history VALUES(36,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.861679"}','SYSTEM','2026-01-30 15:47:37.861817',NULL,'2026-01-30 15:47:37.861888','2026-01-30 15:47:37.861888');
INSERT INTO project_risk_history VALUES(37,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.582441"}','SYSTEM','2026-01-30 15:49:04.583054',NULL,'2026-01-30 15:49:04.583370','2026-01-30 15:49:04.583371');
INSERT INTO project_risk_history VALUES(38,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.584961"}','SYSTEM','2026-01-30 15:49:04.585121',NULL,'2026-01-30 15:49:04.585208','2026-01-30 15:49:04.585209');
INSERT INTO project_risk_history VALUES(39,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.586362"}','SYSTEM','2026-01-30 15:49:04.586509',NULL,'2026-01-30 15:49:04.586585','2026-01-30 15:49:04.586585');
INSERT INTO project_risk_history VALUES(40,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.587722"}','SYSTEM','2026-01-30 15:49:04.587863',NULL,'2026-01-30 15:49:04.587935','2026-01-30 15:49:04.587935');
INSERT INTO project_risk_history VALUES(41,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.588987"}','SYSTEM','2026-01-30 15:49:04.589124',NULL,'2026-01-30 15:49:04.589193','2026-01-30 15:49:04.589193');
INSERT INTO project_risk_history VALUES(42,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.590462"}','SYSTEM','2026-01-30 15:49:04.590622',NULL,'2026-01-30 15:49:04.590706','2026-01-30 15:49:04.590707');
INSERT INTO project_risk_history VALUES(43,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.038211"}','SYSTEM','2026-01-30 15:49:15.038804',NULL,'2026-01-30 15:49:15.039093','2026-01-30 15:49:15.039094');
INSERT INTO project_risk_history VALUES(44,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.041311"}','SYSTEM','2026-01-30 15:49:15.041463',NULL,'2026-01-30 15:49:15.041557','2026-01-30 15:49:15.041562');
INSERT INTO project_risk_history VALUES(45,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.042762"}','SYSTEM','2026-01-30 15:49:15.042906',NULL,'2026-01-30 15:49:15.042981','2026-01-30 15:49:15.042982');
INSERT INTO project_risk_history VALUES(46,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.044346"}','SYSTEM','2026-01-30 15:49:15.044525',NULL,'2026-01-30 15:49:15.044615','2026-01-30 15:49:15.044615');
INSERT INTO project_risk_history VALUES(47,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.045770"}','SYSTEM','2026-01-30 15:49:15.045907',NULL,'2026-01-30 15:49:15.045979','2026-01-30 15:49:15.045979');
INSERT INTO project_risk_history VALUES(48,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.047075"}','SYSTEM','2026-01-30 15:49:15.047209',NULL,'2026-01-30 15:49:15.047277','2026-01-30 15:49:15.047278');
INSERT INTO project_risk_history VALUES(49,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.492275"}','SYSTEM','2026-01-30 15:50:08.492888',NULL,'2026-01-30 15:50:08.493230','2026-01-30 15:50:08.493231');
INSERT INTO project_risk_history VALUES(50,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.495665"}','SYSTEM','2026-01-30 15:50:08.495830',NULL,'2026-01-30 15:50:08.495922','2026-01-30 15:50:08.495923');
INSERT INTO project_risk_history VALUES(51,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.497166"}','SYSTEM','2026-01-30 15:50:08.497315',NULL,'2026-01-30 15:50:08.497398','2026-01-30 15:50:08.497398');
INSERT INTO project_risk_history VALUES(52,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.498800"}','SYSTEM','2026-01-30 15:50:08.498988',NULL,'2026-01-30 15:50:08.499097','2026-01-30 15:50:08.499098');
INSERT INTO project_risk_history VALUES(53,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.500503"}','SYSTEM','2026-01-30 15:50:08.500676',NULL,'2026-01-30 15:50:08.500761','2026-01-30 15:50:08.500762');
INSERT INTO project_risk_history VALUES(54,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.502149"}','SYSTEM','2026-01-30 15:50:08.502312',NULL,'2026-01-30 15:50:08.502423','2026-01-30 15:50:08.502423');
INSERT INTO project_risk_history VALUES(55,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.697771"}','SYSTEM','2026-01-30 15:51:05.698365',NULL,'2026-01-30 15:51:05.698662','2026-01-30 15:51:05.698663');
INSERT INTO project_risk_history VALUES(56,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.701087"}','SYSTEM','2026-01-30 15:51:05.701252',NULL,'2026-01-30 15:51:05.701343','2026-01-30 15:51:05.701344');
INSERT INTO project_risk_history VALUES(57,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.702592"}','SYSTEM','2026-01-30 15:51:05.702749',NULL,'2026-01-30 15:51:05.702827','2026-01-30 15:51:05.702827');
INSERT INTO project_risk_history VALUES(58,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.703942"}','SYSTEM','2026-01-30 15:51:05.704097',NULL,'2026-01-30 15:51:05.704171','2026-01-30 15:51:05.704172');
INSERT INTO project_risk_history VALUES(59,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.705485"}','SYSTEM','2026-01-30 15:51:05.705639',NULL,'2026-01-30 15:51:05.705724','2026-01-30 15:51:05.705725');
INSERT INTO project_risk_history VALUES(60,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.706863"}','SYSTEM','2026-01-30 15:51:05.706997',NULL,'2026-01-30 15:51:05.707066','2026-01-30 15:51:05.707067');
INSERT INTO project_risk_history VALUES(61,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.656649"}','SYSTEM','2026-01-30 15:53:29.657437',NULL,'2026-01-30 15:53:29.657736','2026-01-30 15:53:29.657737');
INSERT INTO project_risk_history VALUES(62,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.659918"}','SYSTEM','2026-01-30 15:53:29.660077',NULL,'2026-01-30 15:53:29.660166','2026-01-30 15:53:29.660166');
INSERT INTO project_risk_history VALUES(63,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.661463"}','SYSTEM','2026-01-30 15:53:29.661622',NULL,'2026-01-30 15:53:29.661702','2026-01-30 15:53:29.661703');
INSERT INTO project_risk_history VALUES(64,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.662839"}','SYSTEM','2026-01-30 15:53:29.662979',NULL,'2026-01-30 15:53:29.663056','2026-01-30 15:53:29.663057');
INSERT INTO project_risk_history VALUES(65,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.664153"}','SYSTEM','2026-01-30 15:53:29.664298',NULL,'2026-01-30 15:53:29.664375','2026-01-30 15:53:29.664376');
INSERT INTO project_risk_history VALUES(66,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.665486"}','SYSTEM','2026-01-30 15:53:29.665622',NULL,'2026-01-30 15:53:29.665692','2026-01-30 15:53:29.665692');
INSERT INTO project_risk_history VALUES(67,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.495298"}','SYSTEM','2026-01-30 15:54:11.495896',NULL,'2026-01-30 15:54:11.496188','2026-01-30 15:54:11.496189');
INSERT INTO project_risk_history VALUES(68,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.498525"}','SYSTEM','2026-01-30 15:54:11.498678',NULL,'2026-01-30 15:54:11.498766','2026-01-30 15:54:11.498767');
INSERT INTO project_risk_history VALUES(69,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.500023"}','SYSTEM','2026-01-30 15:54:11.500179',NULL,'2026-01-30 15:54:11.500265','2026-01-30 15:54:11.500265');
INSERT INTO project_risk_history VALUES(70,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.501447"}','SYSTEM','2026-01-30 15:54:11.501591',NULL,'2026-01-30 15:54:11.501665','2026-01-30 15:54:11.501665');
INSERT INTO project_risk_history VALUES(71,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.502746"}','SYSTEM','2026-01-30 15:54:11.502885',NULL,'2026-01-30 15:54:11.502954','2026-01-30 15:54:11.502955');
INSERT INTO project_risk_history VALUES(72,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.504032"}','SYSTEM','2026-01-30 15:54:11.504169',NULL,'2026-01-30 15:54:11.504237','2026-01-30 15:54:11.504238');
INSERT INTO project_risk_history VALUES(73,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.258972"}','SYSTEM','2026-01-30 15:55:13.259790',NULL,'2026-01-30 15:55:13.260121','2026-01-30 15:55:13.260122');
INSERT INTO project_risk_history VALUES(74,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.262358"}','SYSTEM','2026-01-30 15:55:13.262516',NULL,'2026-01-30 15:55:13.262605','2026-01-30 15:55:13.262606');
INSERT INTO project_risk_history VALUES(75,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.263902"}','SYSTEM','2026-01-30 15:55:13.264057',NULL,'2026-01-30 15:55:13.264139','2026-01-30 15:55:13.264139');
INSERT INTO project_risk_history VALUES(76,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.265279"}','SYSTEM','2026-01-30 15:55:13.265424',NULL,'2026-01-30 15:55:13.265502','2026-01-30 15:55:13.265502');
INSERT INTO project_risk_history VALUES(77,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.266635"}','SYSTEM','2026-01-30 15:55:13.266778',NULL,'2026-01-30 15:55:13.266851','2026-01-30 15:55:13.266852');
INSERT INTO project_risk_history VALUES(78,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.267956"}','SYSTEM','2026-01-30 15:55:13.268094',NULL,'2026-01-30 15:55:13.268166','2026-01-30 15:55:13.268166');
INSERT INTO project_risk_history VALUES(79,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.588479"}','SYSTEM','2026-01-30 15:58:26.589535',NULL,'2026-01-30 15:58:26.589852','2026-01-30 15:58:26.589852');
INSERT INTO project_risk_history VALUES(80,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.592000"}','SYSTEM','2026-01-30 15:58:26.592155',NULL,'2026-01-30 15:58:26.592246','2026-01-30 15:58:26.592247');
INSERT INTO project_risk_history VALUES(81,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.593576"}','SYSTEM','2026-01-30 15:58:26.593718',NULL,'2026-01-30 15:58:26.593796','2026-01-30 15:58:26.593797');
INSERT INTO project_risk_history VALUES(82,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.594980"}','SYSTEM','2026-01-30 15:58:26.595126',NULL,'2026-01-30 15:58:26.595204','2026-01-30 15:58:26.595204');
INSERT INTO project_risk_history VALUES(83,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.596405"}','SYSTEM','2026-01-30 15:58:26.596556',NULL,'2026-01-30 15:58:26.596637','2026-01-30 15:58:26.596638');
INSERT INTO project_risk_history VALUES(84,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.597821"}','SYSTEM','2026-01-30 15:58:26.597968',NULL,'2026-01-30 15:58:26.598042','2026-01-30 15:58:26.598042');
INSERT INTO project_risk_history VALUES(85,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.219342"}','SYSTEM','2026-01-30 16:01:47.220316',NULL,'2026-01-30 16:01:47.220629','2026-01-30 16:01:47.220630');
INSERT INTO project_risk_history VALUES(86,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.222727"}','SYSTEM','2026-01-30 16:01:47.222873',NULL,'2026-01-30 16:01:47.222954','2026-01-30 16:01:47.222954');
INSERT INTO project_risk_history VALUES(87,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.224070"}','SYSTEM','2026-01-30 16:01:47.224215',NULL,'2026-01-30 16:01:47.224287','2026-01-30 16:01:47.224288');
INSERT INTO project_risk_history VALUES(88,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.225362"}','SYSTEM','2026-01-30 16:01:47.225506',NULL,'2026-01-30 16:01:47.225579','2026-01-30 16:01:47.225580');
INSERT INTO project_risk_history VALUES(89,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.226650"}','SYSTEM','2026-01-30 16:01:47.226783',NULL,'2026-01-30 16:01:47.226850','2026-01-30 16:01:47.226851');
INSERT INTO project_risk_history VALUES(90,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.227943"}','SYSTEM','2026-01-30 16:01:47.228087',NULL,'2026-01-30 16:01:47.228155','2026-01-30 16:01:47.228155');
INSERT INTO project_risk_history VALUES(91,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.857473"}','SYSTEM','2026-01-30 16:01:56.858662',NULL,'2026-01-30 16:01:56.859113','2026-01-30 16:01:56.859114');
INSERT INTO project_risk_history VALUES(92,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.861658"}','SYSTEM','2026-01-30 16:01:56.861856',NULL,'2026-01-30 16:01:56.861984','2026-01-30 16:01:56.861985');
INSERT INTO project_risk_history VALUES(93,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.863507"}','SYSTEM','2026-01-30 16:01:56.863684',NULL,'2026-01-30 16:01:56.863786','2026-01-30 16:01:56.863787');
INSERT INTO project_risk_history VALUES(94,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.865202"}','SYSTEM','2026-01-30 16:01:56.865374',NULL,'2026-01-30 16:01:56.865474','2026-01-30 16:01:56.865475');
INSERT INTO project_risk_history VALUES(95,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.866852"}','SYSTEM','2026-01-30 16:01:56.867020',NULL,'2026-01-30 16:01:56.867122','2026-01-30 16:01:56.867122');
INSERT INTO project_risk_history VALUES(96,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.868498"}','SYSTEM','2026-01-30 16:01:56.868671',NULL,'2026-01-30 16:01:56.868770','2026-01-30 16:01:56.868770');
INSERT INTO project_risk_history VALUES(97,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.970749"}','SYSTEM','2026-01-30 16:06:00.971883',NULL,'2026-01-30 16:06:00.972201','2026-01-30 16:06:00.972202');
INSERT INTO project_risk_history VALUES(98,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.974264"}','SYSTEM','2026-01-30 16:06:00.974418',NULL,'2026-01-30 16:06:00.974506','2026-01-30 16:06:00.974507');
INSERT INTO project_risk_history VALUES(99,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.975961"}','SYSTEM','2026-01-30 16:06:00.976111',NULL,'2026-01-30 16:06:00.976191','2026-01-30 16:06:00.976192');
INSERT INTO project_risk_history VALUES(100,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.977538"}','SYSTEM','2026-01-30 16:06:00.977688',NULL,'2026-01-30 16:06:00.977766','2026-01-30 16:06:00.977766');
INSERT INTO project_risk_history VALUES(101,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.978883"}','SYSTEM','2026-01-30 16:06:00.979027',NULL,'2026-01-30 16:06:00.979102','2026-01-30 16:06:00.979103');
INSERT INTO project_risk_history VALUES(102,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.980376"}','SYSTEM','2026-01-30 16:06:00.980526',NULL,'2026-01-30 16:06:00.980611','2026-01-30 16:06:00.980612');
INSERT INTO project_risk_history VALUES(103,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.122814"}','SYSTEM','2026-01-30 16:09:17.123943',NULL,'2026-01-30 16:09:17.124290','2026-01-30 16:09:17.124291');
INSERT INTO project_risk_history VALUES(104,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.126318"}','SYSTEM','2026-01-30 16:09:17.126472',NULL,'2026-01-30 16:09:17.126556','2026-01-30 16:09:17.126556');
INSERT INTO project_risk_history VALUES(105,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.127703"}','SYSTEM','2026-01-30 16:09:17.127843',NULL,'2026-01-30 16:09:17.127917','2026-01-30 16:09:17.127917');
INSERT INTO project_risk_history VALUES(106,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.129036"}','SYSTEM','2026-01-30 16:09:17.129182',NULL,'2026-01-30 16:09:17.129251','2026-01-30 16:09:17.129251');
INSERT INTO project_risk_history VALUES(107,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.130354"}','SYSTEM','2026-01-30 16:09:17.130502',NULL,'2026-01-30 16:09:17.130574','2026-01-30 16:09:17.130575');
INSERT INTO project_risk_history VALUES(108,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.131680"}','SYSTEM','2026-01-30 16:09:17.131827',NULL,'2026-01-30 16:09:17.131899','2026-01-30 16:09:17.131899');
INSERT INTO project_risk_history VALUES(109,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.554270"}','SYSTEM','2026-01-30 16:09:27.555424',NULL,'2026-01-30 16:09:27.555786','2026-01-30 16:09:27.555787');
INSERT INTO project_risk_history VALUES(110,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.557917"}','SYSTEM','2026-01-30 16:09:27.558127',NULL,'2026-01-30 16:09:27.558223','2026-01-30 16:09:27.558224');
INSERT INTO project_risk_history VALUES(111,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.559537"}','SYSTEM','2026-01-30 16:09:27.559691',NULL,'2026-01-30 16:09:27.559771','2026-01-30 16:09:27.559771');
INSERT INTO project_risk_history VALUES(112,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.561120"}','SYSTEM','2026-01-30 16:09:27.561292',NULL,'2026-01-30 16:09:27.561377','2026-01-30 16:09:27.561377');
INSERT INTO project_risk_history VALUES(113,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.562570"}','SYSTEM','2026-01-30 16:09:27.562717',NULL,'2026-01-30 16:09:27.562794','2026-01-30 16:09:27.562794');
INSERT INTO project_risk_history VALUES(114,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.563945"}','SYSTEM','2026-01-30 16:09:27.564099',NULL,'2026-01-30 16:09:27.564178','2026-01-30 16:09:27.564178');
INSERT INTO project_risk_history VALUES(115,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.041986"}','SYSTEM','2026-01-30 16:10:14.043151',NULL,'2026-01-30 16:10:14.043457','2026-01-30 16:10:14.043457');
INSERT INTO project_risk_history VALUES(116,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.045676"}','SYSTEM','2026-01-30 16:10:14.045837',NULL,'2026-01-30 16:10:14.045931','2026-01-30 16:10:14.045931');
INSERT INTO project_risk_history VALUES(117,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.047103"}','SYSTEM','2026-01-30 16:10:14.047249',NULL,'2026-01-30 16:10:14.047329','2026-01-30 16:10:14.047330');
INSERT INTO project_risk_history VALUES(118,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.048439"}','SYSTEM','2026-01-30 16:10:14.048582',NULL,'2026-01-30 16:10:14.048658','2026-01-30 16:10:14.048659');
INSERT INTO project_risk_history VALUES(119,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.049926"}','SYSTEM','2026-01-30 16:10:14.050081',NULL,'2026-01-30 16:10:14.050166','2026-01-30 16:10:14.050167');
INSERT INTO project_risk_history VALUES(120,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.051342"}','SYSTEM','2026-01-30 16:10:14.051489',NULL,'2026-01-30 16:10:14.051567','2026-01-30 16:10:14.051568');
INSERT INTO project_risk_history VALUES(121,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.253505"}','SYSTEM','2026-01-30 16:10:34.254756',NULL,'2026-01-30 16:10:34.255076','2026-01-30 16:10:34.255076');
INSERT INTO project_risk_history VALUES(122,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.259503"}','SYSTEM','2026-01-30 16:10:34.259695',NULL,'2026-01-30 16:10:34.259786','2026-01-30 16:10:34.259787');
INSERT INTO project_risk_history VALUES(123,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.261072"}','SYSTEM','2026-01-30 16:10:34.261223',NULL,'2026-01-30 16:10:34.261307','2026-01-30 16:10:34.261308');
INSERT INTO project_risk_history VALUES(124,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.262464"}','SYSTEM','2026-01-30 16:10:34.262607',NULL,'2026-01-30 16:10:34.262682','2026-01-30 16:10:34.262682');
INSERT INTO project_risk_history VALUES(125,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.263804"}','SYSTEM','2026-01-30 16:10:34.263947',NULL,'2026-01-30 16:10:34.264023','2026-01-30 16:10:34.264023');
INSERT INTO project_risk_history VALUES(126,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.265134"}','SYSTEM','2026-01-30 16:10:34.265270',NULL,'2026-01-30 16:10:34.265340','2026-01-30 16:10:34.265340');
INSERT INTO project_risk_history VALUES(127,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.336920"}','SYSTEM','2026-01-30 19:43:02.338431',NULL,'2026-01-30 19:43:02.338804','2026-01-30 19:43:02.338805');
INSERT INTO project_risk_history VALUES(128,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.341597"}','SYSTEM','2026-01-30 19:43:02.341805',NULL,'2026-01-30 19:43:02.341944','2026-01-30 19:43:02.341944');
INSERT INTO project_risk_history VALUES(129,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.343433"}','SYSTEM','2026-01-30 19:43:02.343601',NULL,'2026-01-30 19:43:02.343698','2026-01-30 19:43:02.343699');
INSERT INTO project_risk_history VALUES(130,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.345209"}','SYSTEM','2026-01-30 19:43:02.345402',NULL,'2026-01-30 19:43:02.345512','2026-01-30 19:43:02.345512');
INSERT INTO project_risk_history VALUES(131,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.346954"}','SYSTEM','2026-01-30 19:43:02.347136',NULL,'2026-01-30 19:43:02.347245','2026-01-30 19:43:02.347245');
INSERT INTO project_risk_history VALUES(132,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.348725"}','SYSTEM','2026-01-30 19:43:02.348905',NULL,'2026-01-30 19:43:02.349006','2026-01-30 19:43:02.349007');
INSERT INTO project_risk_history VALUES(133,1,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.050264"}','SYSTEM','2026-01-30 19:53:50.053248',NULL,'2026-01-30 19:53:50.053610','2026-01-30 19:53:50.053611');
INSERT INTO project_risk_history VALUES(134,2,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.225586"}','SYSTEM','2026-01-30 19:53:50.226009',NULL,'2026-01-30 19:53:50.226277','2026-01-30 19:53:50.226279');
INSERT INTO project_risk_history VALUES(135,3,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.229596"}','SYSTEM','2026-01-30 19:53:50.229959',NULL,'2026-01-30 19:53:50.230166','2026-01-30 19:53:50.230168');
INSERT INTO project_risk_history VALUES(136,4,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.232687"}','SYSTEM','2026-01-30 19:53:50.233001',NULL,'2026-01-30 19:53:50.233172','2026-01-30 19:53:50.233173');
INSERT INTO project_risk_history VALUES(137,5,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.235602"}','SYSTEM','2026-01-30 19:53:50.235900',NULL,'2026-01-30 19:53:50.236064','2026-01-30 19:53:50.236066');
INSERT INTO project_risk_history VALUES(138,6,'LOW','LOW','{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.238339"}','SYSTEM','2026-01-30 19:53:50.238611',NULL,'2026-01-30 19:53:50.238754','2026-01-30 19:53:50.238755');
CREATE TABLE project_risk_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),

    -- 快照时间
    snapshot_date TIMESTAMP NOT NULL,  -- 快照日期

    -- 风险等级
    risk_level VARCHAR(20),  -- 风险等级

    -- 风险指标
    overdue_milestones_count INTEGER DEFAULT 0,  -- 逾期里程碑数
    total_milestones_count INTEGER DEFAULT 0,  -- 总里程碑数
    overdue_tasks_count INTEGER DEFAULT 0,  -- 逾期任务数
    open_risks_count INTEGER DEFAULT 0,  -- 未关闭风险数
    high_risks_count INTEGER DEFAULT 0,  -- 高风险数

    -- 详细数据
    risk_factors JSON,  -- 风险因子详情

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO project_risk_snapshot VALUES(1,1,'2026-01-30 15:24:37.591416','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.591414"}','2026-01-30 15:24:37.591734','2026-01-30 15:24:37.591734');
INSERT INTO project_risk_snapshot VALUES(2,2,'2026-01-30 15:24:37.592921','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.592919"}','2026-01-30 15:24:37.592995','2026-01-30 15:24:37.592995');
INSERT INTO project_risk_snapshot VALUES(3,3,'2026-01-30 15:24:37.594277','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.594274"}','2026-01-30 15:24:37.594363','2026-01-30 15:24:37.594364');
INSERT INTO project_risk_snapshot VALUES(4,4,'2026-01-30 15:24:37.595526','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.595524"}','2026-01-30 15:24:37.595604','2026-01-30 15:24:37.595605');
INSERT INTO project_risk_snapshot VALUES(5,5,'2026-01-30 15:24:37.596696','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.596694"}','2026-01-30 15:24:37.596770','2026-01-30 15:24:37.596770');
INSERT INTO project_risk_snapshot VALUES(6,6,'2026-01-30 15:24:37.597830','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:24:37.597828"}','2026-01-30 15:24:37.597901','2026-01-30 15:24:37.597902');
INSERT INTO project_risk_snapshot VALUES(7,1,'2026-01-30 15:37:59.957060','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.957058"}','2026-01-30 15:37:59.957379','2026-01-30 15:37:59.957380');
INSERT INTO project_risk_snapshot VALUES(8,2,'2026-01-30 15:37:59.958709','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.958707"}','2026-01-30 15:37:59.958799','2026-01-30 15:37:59.958800');
INSERT INTO project_risk_snapshot VALUES(9,3,'2026-01-30 15:37:59.959978','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.959976"}','2026-01-30 15:37:59.960058','2026-01-30 15:37:59.960058');
INSERT INTO project_risk_snapshot VALUES(10,4,'2026-01-30 15:37:59.961146','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.961144"}','2026-01-30 15:37:59.961220','2026-01-30 15:37:59.961220');
INSERT INTO project_risk_snapshot VALUES(11,5,'2026-01-30 15:37:59.962446','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.962444"}','2026-01-30 15:37:59.962532','2026-01-30 15:37:59.962532');
INSERT INTO project_risk_snapshot VALUES(12,6,'2026-01-30 15:37:59.963667','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:37:59.963665"}','2026-01-30 15:37:59.963745','2026-01-30 15:37:59.963745');
INSERT INTO project_risk_snapshot VALUES(13,1,'2026-01-30 15:42:39.554612','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.554610"}','2026-01-30 15:42:39.554946','2026-01-30 15:42:39.554947');
INSERT INTO project_risk_snapshot VALUES(14,2,'2026-01-30 15:42:39.556145','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.556143"}','2026-01-30 15:42:39.556226','2026-01-30 15:42:39.556227');
INSERT INTO project_risk_snapshot VALUES(15,3,'2026-01-30 15:42:39.557445','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.557443"}','2026-01-30 15:42:39.557528','2026-01-30 15:42:39.557528');
INSERT INTO project_risk_snapshot VALUES(16,4,'2026-01-30 15:42:39.558848','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.558845"}','2026-01-30 15:42:39.558945','2026-01-30 15:42:39.558945');
INSERT INTO project_risk_snapshot VALUES(17,5,'2026-01-30 15:42:39.560156','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.560153"}','2026-01-30 15:42:39.560246','2026-01-30 15:42:39.560247');
INSERT INTO project_risk_snapshot VALUES(18,6,'2026-01-30 15:42:39.561386','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:42:39.561384"}','2026-01-30 15:42:39.561463','2026-01-30 15:42:39.561464');
INSERT INTO project_risk_snapshot VALUES(19,1,'2026-01-30 15:45:07.357708','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.357706"}','2026-01-30 15:45:07.358033','2026-01-30 15:45:07.358034');
INSERT INTO project_risk_snapshot VALUES(20,2,'2026-01-30 15:45:07.359272','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.359270"}','2026-01-30 15:45:07.359351','2026-01-30 15:45:07.359351');
INSERT INTO project_risk_snapshot VALUES(21,3,'2026-01-30 15:45:07.360426','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.360424"}','2026-01-30 15:45:07.360500','2026-01-30 15:45:07.360501');
INSERT INTO project_risk_snapshot VALUES(22,4,'2026-01-30 15:45:07.361795','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.361792"}','2026-01-30 15:45:07.361883','2026-01-30 15:45:07.361884');
INSERT INTO project_risk_snapshot VALUES(23,5,'2026-01-30 15:45:07.363051','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.363049"}','2026-01-30 15:45:07.363124','2026-01-30 15:45:07.363124');
INSERT INTO project_risk_snapshot VALUES(24,6,'2026-01-30 15:45:07.364214','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:45:07.364212"}','2026-01-30 15:45:07.364284','2026-01-30 15:45:07.364284');
INSERT INTO project_risk_snapshot VALUES(25,1,'2026-01-30 15:47:37.863944','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.863941"}','2026-01-30 15:47:37.864296','2026-01-30 15:47:37.864296');
INSERT INTO project_risk_snapshot VALUES(26,2,'2026-01-30 15:47:37.865666','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.865663"}','2026-01-30 15:47:37.865759','2026-01-30 15:47:37.865760');
INSERT INTO project_risk_snapshot VALUES(27,3,'2026-01-30 15:47:37.866947','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.866945"}','2026-01-30 15:47:37.867022','2026-01-30 15:47:37.867023');
INSERT INTO project_risk_snapshot VALUES(28,4,'2026-01-30 15:47:37.868298','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.868295"}','2026-01-30 15:47:37.868383','2026-01-30 15:47:37.868383');
INSERT INTO project_risk_snapshot VALUES(29,5,'2026-01-30 15:47:37.869500','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.869498"}','2026-01-30 15:47:37.869572','2026-01-30 15:47:37.869573');
INSERT INTO project_risk_snapshot VALUES(30,6,'2026-01-30 15:47:37.870843','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:47:37.870840"}','2026-01-30 15:47:37.870931','2026-01-30 15:47:37.870932');
INSERT INTO project_risk_snapshot VALUES(31,1,'2026-01-30 15:49:04.592569','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.592567"}','2026-01-30 15:49:04.592895','2026-01-30 15:49:04.592895');
INSERT INTO project_risk_snapshot VALUES(32,2,'2026-01-30 15:49:04.594103','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.594101"}','2026-01-30 15:49:04.594182','2026-01-30 15:49:04.594182');
INSERT INTO project_risk_snapshot VALUES(33,3,'2026-01-30 15:49:04.595248','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.595247"}','2026-01-30 15:49:04.595321','2026-01-30 15:49:04.595321');
INSERT INTO project_risk_snapshot VALUES(34,4,'2026-01-30 15:49:04.596358','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.596357"}','2026-01-30 15:49:04.596428','2026-01-30 15:49:04.596428');
INSERT INTO project_risk_snapshot VALUES(35,5,'2026-01-30 15:49:04.597686','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.597683"}','2026-01-30 15:49:04.597775','2026-01-30 15:49:04.597775');
INSERT INTO project_risk_snapshot VALUES(36,6,'2026-01-30 15:49:04.598941','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:04.598938"}','2026-01-30 15:49:04.599022','2026-01-30 15:49:04.599022');
INSERT INTO project_risk_snapshot VALUES(37,1,'2026-01-30 15:49:15.049058','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.049056"}','2026-01-30 15:49:15.049390','2026-01-30 15:49:15.049390');
INSERT INTO project_risk_snapshot VALUES(38,2,'2026-01-30 15:49:15.050545','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.050543"}','2026-01-30 15:49:15.050620','2026-01-30 15:49:15.050620');
INSERT INTO project_risk_snapshot VALUES(39,3,'2026-01-30 15:49:15.051696','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.051695"}','2026-01-30 15:49:15.051766','2026-01-30 15:49:15.051767');
INSERT INTO project_risk_snapshot VALUES(40,4,'2026-01-30 15:49:15.052803','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.052801"}','2026-01-30 15:49:15.052871','2026-01-30 15:49:15.052872');
INSERT INTO project_risk_snapshot VALUES(41,5,'2026-01-30 15:49:15.053972','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.053970"}','2026-01-30 15:49:15.054041','2026-01-30 15:49:15.054041');
INSERT INTO project_risk_snapshot VALUES(42,6,'2026-01-30 15:49:15.055090','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:49:15.055089"}','2026-01-30 15:49:15.055163','2026-01-30 15:49:15.055163');
INSERT INTO project_risk_snapshot VALUES(43,1,'2026-01-30 15:50:08.504554','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.504552"}','2026-01-30 15:50:08.504946','2026-01-30 15:50:08.504947');
INSERT INTO project_risk_snapshot VALUES(44,2,'2026-01-30 15:50:08.506223','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.506221"}','2026-01-30 15:50:08.506300','2026-01-30 15:50:08.506301');
INSERT INTO project_risk_snapshot VALUES(45,3,'2026-01-30 15:50:08.507646','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.507643"}','2026-01-30 15:50:08.507739','2026-01-30 15:50:08.507740');
INSERT INTO project_risk_snapshot VALUES(46,4,'2026-01-30 15:50:08.509071','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.509069"}','2026-01-30 15:50:08.509165','2026-01-30 15:50:08.509165');
INSERT INTO project_risk_snapshot VALUES(47,5,'2026-01-30 15:50:08.510472','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.510470"}','2026-01-30 15:50:08.510565','2026-01-30 15:50:08.510565');
INSERT INTO project_risk_snapshot VALUES(48,6,'2026-01-30 15:50:08.511829','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:50:08.511827"}','2026-01-30 15:50:08.511912','2026-01-30 15:50:08.511912');
INSERT INTO project_risk_snapshot VALUES(49,1,'2026-01-30 15:51:05.708882','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.708880"}','2026-01-30 15:51:05.709204','2026-01-30 15:51:05.709205');
INSERT INTO project_risk_snapshot VALUES(50,2,'2026-01-30 15:51:05.710403','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.710401"}','2026-01-30 15:51:05.710477','2026-01-30 15:51:05.710478');
INSERT INTO project_risk_snapshot VALUES(51,3,'2026-01-30 15:51:05.711507','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.711505"}','2026-01-30 15:51:05.711578','2026-01-30 15:51:05.711578');
INSERT INTO project_risk_snapshot VALUES(52,4,'2026-01-30 15:51:05.712619','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.712617"}','2026-01-30 15:51:05.712688','2026-01-30 15:51:05.712689');
INSERT INTO project_risk_snapshot VALUES(53,5,'2026-01-30 15:51:05.713925','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.713922"}','2026-01-30 15:51:05.714009','2026-01-30 15:51:05.714009');
INSERT INTO project_risk_snapshot VALUES(54,6,'2026-01-30 15:51:05.715144','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:51:05.715142"}','2026-01-30 15:51:05.715215','2026-01-30 15:51:05.715215');
INSERT INTO project_risk_snapshot VALUES(55,1,'2026-01-30 15:53:29.667519','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.667517"}','2026-01-30 15:53:29.667835','2026-01-30 15:53:29.667836');
INSERT INTO project_risk_snapshot VALUES(56,2,'2026-01-30 15:53:29.669047','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.669045"}','2026-01-30 15:53:29.669126','2026-01-30 15:53:29.669126');
INSERT INTO project_risk_snapshot VALUES(57,3,'2026-01-30 15:53:29.670213','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.670211"}','2026-01-30 15:53:29.670286','2026-01-30 15:53:29.670287');
INSERT INTO project_risk_snapshot VALUES(58,4,'2026-01-30 15:53:29.671328','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.671326"}','2026-01-30 15:53:29.671399','2026-01-30 15:53:29.671400');
INSERT INTO project_risk_snapshot VALUES(59,5,'2026-01-30 15:53:29.672721','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.672719"}','2026-01-30 15:53:29.672806','2026-01-30 15:53:29.672807');
INSERT INTO project_risk_snapshot VALUES(60,6,'2026-01-30 15:53:29.674142','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:53:29.674139"}','2026-01-30 15:53:29.674231','2026-01-30 15:53:29.674232');
INSERT INTO project_risk_snapshot VALUES(61,1,'2026-01-30 15:54:11.506058','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.506056"}','2026-01-30 15:54:11.506374','2026-01-30 15:54:11.506375');
INSERT INTO project_risk_snapshot VALUES(62,2,'2026-01-30 15:54:11.507567','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.507565"}','2026-01-30 15:54:11.507647','2026-01-30 15:54:11.507647');
INSERT INTO project_risk_snapshot VALUES(63,3,'2026-01-30 15:54:11.509005','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.509002"}','2026-01-30 15:54:11.509092','2026-01-30 15:54:11.509093');
INSERT INTO project_risk_snapshot VALUES(64,4,'2026-01-30 15:54:11.510269','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.510267"}','2026-01-30 15:54:11.510347','2026-01-30 15:54:11.510348');
INSERT INTO project_risk_snapshot VALUES(65,5,'2026-01-30 15:54:11.511493','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.511491"}','2026-01-30 15:54:11.511567','2026-01-30 15:54:11.511567');
INSERT INTO project_risk_snapshot VALUES(66,6,'2026-01-30 15:54:11.512622','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:54:11.512620"}','2026-01-30 15:54:11.512693','2026-01-30 15:54:11.512694');
INSERT INTO project_risk_snapshot VALUES(67,1,'2026-01-30 15:55:13.270010','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.270008"}','2026-01-30 15:55:13.270347','2026-01-30 15:55:13.270347');
INSERT INTO project_risk_snapshot VALUES(68,2,'2026-01-30 15:55:13.271553','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.271551"}','2026-01-30 15:55:13.271631','2026-01-30 15:55:13.271631');
INSERT INTO project_risk_snapshot VALUES(69,3,'2026-01-30 15:55:13.272731','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.272730"}','2026-01-30 15:55:13.272806','2026-01-30 15:55:13.272806');
INSERT INTO project_risk_snapshot VALUES(70,4,'2026-01-30 15:55:13.273894','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.273892"}','2026-01-30 15:55:13.273964','2026-01-30 15:55:13.273965');
INSERT INTO project_risk_snapshot VALUES(71,5,'2026-01-30 15:55:13.275102','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.275101"}','2026-01-30 15:55:13.275175','2026-01-30 15:55:13.275175');
INSERT INTO project_risk_snapshot VALUES(72,6,'2026-01-30 15:55:13.276260','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:55:13.276258"}','2026-01-30 15:55:13.276333','2026-01-30 15:55:13.276334');
INSERT INTO project_risk_snapshot VALUES(73,1,'2026-01-30 15:58:26.599242','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.599240"}','2026-01-30 15:58:26.599552','2026-01-30 15:58:26.599553');
INSERT INTO project_risk_snapshot VALUES(74,2,'2026-01-30 15:58:26.600864','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.600862"}','2026-01-30 15:58:26.600940','2026-01-30 15:58:26.600941');
INSERT INTO project_risk_snapshot VALUES(75,3,'2026-01-30 15:58:26.602068','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.602066"}','2026-01-30 15:58:26.602145','2026-01-30 15:58:26.602146');
INSERT INTO project_risk_snapshot VALUES(76,4,'2026-01-30 15:58:26.603211','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.603210"}','2026-01-30 15:58:26.603283','2026-01-30 15:58:26.603283');
INSERT INTO project_risk_snapshot VALUES(77,5,'2026-01-30 15:58:26.604335','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.604333"}','2026-01-30 15:58:26.604405','2026-01-30 15:58:26.604406');
INSERT INTO project_risk_snapshot VALUES(78,6,'2026-01-30 15:58:26.605481','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T15:58:26.605479"}','2026-01-30 15:58:26.605554','2026-01-30 15:58:26.605554');
INSERT INTO project_risk_snapshot VALUES(79,1,'2026-01-30 16:01:47.229291','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.229289"}','2026-01-30 16:01:47.229654','2026-01-30 16:01:47.229655');
INSERT INTO project_risk_snapshot VALUES(80,2,'2026-01-30 16:01:47.231086','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.231083"}','2026-01-30 16:01:47.231167','2026-01-30 16:01:47.231167');
INSERT INTO project_risk_snapshot VALUES(81,3,'2026-01-30 16:01:47.232383','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.232381"}','2026-01-30 16:01:47.232465','2026-01-30 16:01:47.232465');
INSERT INTO project_risk_snapshot VALUES(82,4,'2026-01-30 16:01:47.233616','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.233614"}','2026-01-30 16:01:47.233692','2026-01-30 16:01:47.233693');
INSERT INTO project_risk_snapshot VALUES(83,5,'2026-01-30 16:01:47.234786','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.234785"}','2026-01-30 16:01:47.234855','2026-01-30 16:01:47.234856');
INSERT INTO project_risk_snapshot VALUES(84,6,'2026-01-30 16:01:47.235868','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:47.235866"}','2026-01-30 16:01:47.235935','2026-01-30 16:01:47.235935');
INSERT INTO project_risk_snapshot VALUES(85,1,'2026-01-30 16:01:56.870333','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.870330"}','2026-01-30 16:01:56.870828','2026-01-30 16:01:56.870828');
INSERT INTO project_risk_snapshot VALUES(86,2,'2026-01-30 16:01:56.872264','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.872262"}','2026-01-30 16:01:56.872357','2026-01-30 16:01:56.872357');
INSERT INTO project_risk_snapshot VALUES(87,3,'2026-01-30 16:01:56.873496','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.873494"}','2026-01-30 16:01:56.873575','2026-01-30 16:01:56.873576');
INSERT INTO project_risk_snapshot VALUES(88,4,'2026-01-30 16:01:56.874682','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.874680"}','2026-01-30 16:01:56.874759','2026-01-30 16:01:56.874759');
INSERT INTO project_risk_snapshot VALUES(89,5,'2026-01-30 16:01:56.875978','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.875976"}','2026-01-30 16:01:56.876063','2026-01-30 16:01:56.876063');
INSERT INTO project_risk_snapshot VALUES(90,6,'2026-01-30 16:01:56.877201','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:01:56.877199"}','2026-01-30 16:01:56.877277','2026-01-30 16:01:56.877277');
INSERT INTO project_risk_snapshot VALUES(91,1,'2026-01-30 16:06:00.981842','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.981840"}','2026-01-30 16:06:00.982169','2026-01-30 16:06:00.982169');
INSERT INTO project_risk_snapshot VALUES(92,2,'2026-01-30 16:06:00.983519','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.983517"}','2026-01-30 16:06:00.983602','2026-01-30 16:06:00.983603');
INSERT INTO project_risk_snapshot VALUES(93,3,'2026-01-30 16:06:00.984724','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.984723"}','2026-01-30 16:06:00.984800','2026-01-30 16:06:00.984800');
INSERT INTO project_risk_snapshot VALUES(94,4,'2026-01-30 16:06:00.986015','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.986013"}','2026-01-30 16:06:00.986103','2026-01-30 16:06:00.986103');
INSERT INTO project_risk_snapshot VALUES(95,5,'2026-01-30 16:06:00.987225','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.987223"}','2026-01-30 16:06:00.987311','2026-01-30 16:06:00.987311');
INSERT INTO project_risk_snapshot VALUES(96,6,'2026-01-30 16:06:00.988381','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:06:00.988379"}','2026-01-30 16:06:00.988455','2026-01-30 16:06:00.988456');
INSERT INTO project_risk_snapshot VALUES(97,1,'2026-01-30 16:09:17.133079','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.133077"}','2026-01-30 16:09:17.133406','2026-01-30 16:09:17.133406');
INSERT INTO project_risk_snapshot VALUES(98,2,'2026-01-30 16:09:17.134802','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.134800"}','2026-01-30 16:09:17.134880','2026-01-30 16:09:17.134880');
INSERT INTO project_risk_snapshot VALUES(99,3,'2026-01-30 16:09:17.136027','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.136026"}','2026-01-30 16:09:17.136103','2026-01-30 16:09:17.136104');
INSERT INTO project_risk_snapshot VALUES(100,4,'2026-01-30 16:09:17.137186','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.137184"}','2026-01-30 16:09:17.137258','2026-01-30 16:09:17.137258');
INSERT INTO project_risk_snapshot VALUES(101,5,'2026-01-30 16:09:17.138322','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.138320"}','2026-01-30 16:09:17.138394','2026-01-30 16:09:17.138395');
INSERT INTO project_risk_snapshot VALUES(102,6,'2026-01-30 16:09:17.139450','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:17.139448"}','2026-01-30 16:09:17.139523','2026-01-30 16:09:17.139523');
INSERT INTO project_risk_snapshot VALUES(103,1,'2026-01-30 16:09:27.565399','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.565397"}','2026-01-30 16:09:27.565741','2026-01-30 16:09:27.565741');
INSERT INTO project_risk_snapshot VALUES(104,2,'2026-01-30 16:09:27.567040','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.567038"}','2026-01-30 16:09:27.567123','2026-01-30 16:09:27.567124');
INSERT INTO project_risk_snapshot VALUES(105,3,'2026-01-30 16:09:27.568471','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.568468"}','2026-01-30 16:09:27.568562','2026-01-30 16:09:27.568563');
INSERT INTO project_risk_snapshot VALUES(106,4,'2026-01-30 16:09:27.569871','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.569868"}','2026-01-30 16:09:27.569955','2026-01-30 16:09:27.569956');
INSERT INTO project_risk_snapshot VALUES(107,5,'2026-01-30 16:09:27.571141','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.571139"}','2026-01-30 16:09:27.571216','2026-01-30 16:09:27.571217');
INSERT INTO project_risk_snapshot VALUES(108,6,'2026-01-30 16:09:27.572436','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:09:27.572434"}','2026-01-30 16:09:27.572519','2026-01-30 16:09:27.572520');
INSERT INTO project_risk_snapshot VALUES(109,1,'2026-01-30 16:10:14.052786','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.052784"}','2026-01-30 16:10:14.053165','2026-01-30 16:10:14.053165');
INSERT INTO project_risk_snapshot VALUES(110,2,'2026-01-30 16:10:14.054617','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.054615"}','2026-01-30 16:10:14.054696','2026-01-30 16:10:14.054696');
INSERT INTO project_risk_snapshot VALUES(111,3,'2026-01-30 16:10:14.055784','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.055782"}','2026-01-30 16:10:14.055862','2026-01-30 16:10:14.055862');
INSERT INTO project_risk_snapshot VALUES(112,4,'2026-01-30 16:10:14.056946','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.056944"}','2026-01-30 16:10:14.057016','2026-01-30 16:10:14.057017');
INSERT INTO project_risk_snapshot VALUES(113,5,'2026-01-30 16:10:14.058067','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.058065"}','2026-01-30 16:10:14.058139','2026-01-30 16:10:14.058140');
INSERT INTO project_risk_snapshot VALUES(114,6,'2026-01-30 16:10:14.059216','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:14.059214"}','2026-01-30 16:10:14.059291','2026-01-30 16:10:14.059291');
INSERT INTO project_risk_snapshot VALUES(115,1,'2026-01-30 16:10:34.266604','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.266602"}','2026-01-30 16:10:34.266931','2026-01-30 16:10:34.266932');
INSERT INTO project_risk_snapshot VALUES(116,2,'2026-01-30 16:10:34.269104','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.269102"}','2026-01-30 16:10:34.269186','2026-01-30 16:10:34.269187');
INSERT INTO project_risk_snapshot VALUES(117,3,'2026-01-30 16:10:34.270328','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.270326"}','2026-01-30 16:10:34.270410','2026-01-30 16:10:34.270410');
INSERT INTO project_risk_snapshot VALUES(118,4,'2026-01-30 16:10:34.271516','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.271515"}','2026-01-30 16:10:34.271591','2026-01-30 16:10:34.271591');
INSERT INTO project_risk_snapshot VALUES(119,5,'2026-01-30 16:10:34.272701','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.272699"}','2026-01-30 16:10:34.272776','2026-01-30 16:10:34.272777');
INSERT INTO project_risk_snapshot VALUES(120,6,'2026-01-30 16:10:34.273835','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T16:10:34.273833"}','2026-01-30 16:10:34.273906','2026-01-30 16:10:34.273907');
INSERT INTO project_risk_snapshot VALUES(121,1,'2026-01-30 19:43:02.350504','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.350501"}','2026-01-30 19:43:02.350994','2026-01-30 19:43:02.350994');
INSERT INTO project_risk_snapshot VALUES(122,2,'2026-01-30 19:43:02.352772','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.352770"}','2026-01-30 19:43:02.352876','2026-01-30 19:43:02.352877');
INSERT INTO project_risk_snapshot VALUES(123,3,'2026-01-30 19:43:02.354322','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.354319"}','2026-01-30 19:43:02.354431','2026-01-30 19:43:02.354432');
INSERT INTO project_risk_snapshot VALUES(124,4,'2026-01-30 19:43:02.355749','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.355746"}','2026-01-30 19:43:02.355845','2026-01-30 19:43:02.355845');
INSERT INTO project_risk_snapshot VALUES(125,5,'2026-01-30 19:43:02.357179','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.357177"}','2026-01-30 19:43:02.357269','2026-01-30 19:43:02.357269');
INSERT INTO project_risk_snapshot VALUES(126,6,'2026-01-30 19:43:02.358458','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:43:02.358456"}','2026-01-30 19:43:02.358541','2026-01-30 19:43:02.358542');
INSERT INTO project_risk_snapshot VALUES(127,1,'2026-01-30 19:53:50.241288','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.241284"}','2026-01-30 19:53:50.241955','2026-01-30 19:53:50.241956');
INSERT INTO project_risk_snapshot VALUES(128,2,'2026-01-30 19:53:50.247520','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.247516"}','2026-01-30 19:53:50.247663','2026-01-30 19:53:50.247664');
INSERT INTO project_risk_snapshot VALUES(129,3,'2026-01-30 19:53:50.249545','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.249541"}','2026-01-30 19:53:50.249673','2026-01-30 19:53:50.249674');
INSERT INTO project_risk_snapshot VALUES(130,4,'2026-01-30 19:53:50.251377','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.251374"}','2026-01-30 19:53:50.251488','2026-01-30 19:53:50.251489');
INSERT INTO project_risk_snapshot VALUES(131,5,'2026-01-30 19:53:50.253141','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.253138"}','2026-01-30 19:53:50.253253','2026-01-30 19:53:50.253254');
INSERT INTO project_risk_snapshot VALUES(132,6,'2026-01-30 19:53:50.254862','LOW',0,0,0,0,0,'{"total_milestones_count": 0, "overdue_milestones_count": 0, "overdue_milestone_ratio": 0, "max_overdue_days": 0, "open_risks_count": 0, "high_risks_count": 0, "critical_risks_count": 0, "progress_pct": 0.0, "schedule_variance": 0, "calculated_at": "2026-01-30T19:53:50.254860"}','2026-01-30 19:53:50.254962','2026-01-30 19:53:50.254962');
INSERT INTO sqlite_sequence VALUES('holidays',33);
INSERT INTO sqlite_sequence VALUES('roles',61);
INSERT INTO sqlite_sequence VALUES('permissions',371);
INSERT INTO sqlite_sequence VALUES('role_permissions',426);
INSERT INTO sqlite_sequence VALUES('role_templates',16);
INSERT INTO sqlite_sequence VALUES('role_exclusions',8);
INSERT INTO sqlite_sequence VALUES('departments',23);
INSERT INTO sqlite_sequence VALUES('department_default_roles',18);
INSERT INTO sqlite_sequence VALUES('performance_indicator',8);
INSERT INTO sqlite_sequence VALUES('timesheet_rule',1);
INSERT INTO sqlite_sequence VALUES('report_template',5);
INSERT INTO sqlite_sequence VALUES('workshop',4);
INSERT INTO sqlite_sequence VALUES('process_dict',13);
INSERT INTO sqlite_sequence VALUES('evaluation_weight_config',1);
INSERT INTO sqlite_sequence VALUES('mes_assembly_stage',6);
INSERT INTO sqlite_sequence VALUES('mes_assembly_template',2);
INSERT INTO sqlite_sequence VALUES('mes_category_stage_mapping',24);
INSERT INTO sqlite_sequence VALUES('mes_shortage_alert_rule',4);
INSERT INTO sqlite_sequence VALUES('project_role_types',10);
INSERT INTO sqlite_sequence VALUES('hr_tag_dict',33);
INSERT INTO sqlite_sequence VALUES('position_role_mapping',38);
INSERT INTO sqlite_sequence VALUES('advantage_product_categories',8);
INSERT INTO sqlite_sequence VALUES('engineer_dimension_config',3);
INSERT INTO sqlite_sequence VALUES('advantage_products',133);
INSERT INTO sqlite_sequence VALUES('industries',37);
INSERT INTO sqlite_sequence VALUES('industry_category_mappings',44);
INSERT INTO sqlite_sequence VALUES('solution_credit_configs',5);
INSERT INTO sqlite_sequence VALUES('job_levels',24);
INSERT INTO sqlite_sequence VALUES('data_scope_rules',6);
INSERT INTO sqlite_sequence VALUES('permission_groups',9);
INSERT INTO sqlite_sequence VALUES('material_cost_update_reminders',1);
INSERT INTO sqlite_sequence VALUES('project_evaluation_dimensions',5);
INSERT INTO sqlite_sequence VALUES('approval_workflows',1);
INSERT INTO sqlite_sequence VALUES('approval_workflow_steps',2);
INSERT INTO sqlite_sequence VALUES('employees',21);
INSERT INTO sqlite_sequence VALUES('users',22);
INSERT INTO sqlite_sequence VALUES('tenants',1);
INSERT INTO sqlite_sequence VALUES('alert_rules',5);
INSERT INTO sqlite_sequence VALUES('user_roles',22);
INSERT INTO sqlite_sequence VALUES('api_permissions',327);
INSERT INTO sqlite_sequence VALUES('role_api_permissions',306);
INSERT INTO sqlite_sequence VALUES('sales_ranking_configs',1);
INSERT INTO sqlite_sequence VALUES('timesheet_summary',2);
INSERT INTO sqlite_sequence VALUES('projects',6);
INSERT INTO sqlite_sequence VALUES('project_risk_history',138);
INSERT INTO sqlite_sequence VALUES('project_risk_snapshot',132);
INSERT INTO sqlite_sequence VALUES('project_status_logs',6);
INSERT INTO sqlite_sequence VALUES('issue_statistics_snapshots',20);
INSERT INTO sqlite_sequence VALUES('project_health_snapshots',6);
INSERT INTO sqlite_sequence VALUES('production_daily_report',1);
INSERT INTO sqlite_sequence VALUES('alert_records',6);
INSERT INTO sqlite_sequence VALUES('alert_notifications',6);
INSERT INTO sqlite_sequence VALUES('mes_kit_rate_snapshot',6);
CREATE VIEW v_project_overview AS
SELECT
    p.id,
    p.project_code,
    p.project_name,
    p.customer_name,
    p.contract_amount,
    p.stage,
    ps.stage_name,
    p.status,
    pst.status_name,
    p.health,
    p.progress_pct,
    p.planned_start_date,
    p.planned_end_date,
    p.actual_start_date,
    p.pm_name,
    p.priority,
    p.budget_amount,
    p.actual_cost,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id) as machine_count,
    (SELECT COUNT(*) FROM project_members pm WHERE pm.project_id = p.id AND pm.is_active = 1) as member_count
FROM projects p
LEFT JOIN project_stages ps ON p.stage = ps.stage_code
LEFT JOIN project_statuses pst ON p.status = pst.status_code
WHERE p.is_active = 1;
CREATE VIEW v_project_progress AS
SELECT
    p.id as project_id,
    p.project_code,
    p.project_name,
    p.stage,
    p.progress_pct as overall_progress,
    (SELECT AVG(m.progress_pct) FROM machines m WHERE m.project_id = p.id) as avg_machine_progress,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id AND m.stage = 'S8') as completed_machines,
    (SELECT COUNT(*) FROM machines m WHERE m.project_id = p.id) as total_machines,
    p.planned_end_date,
    p.actual_end_date,
    CASE
        WHEN p.actual_end_date IS NOT NULL THEN julianday(p.actual_end_date) - julianday(p.planned_end_date)
        ELSE julianday('now') - julianday(p.planned_end_date)
    END as delay_days
FROM projects p
WHERE p.is_active = 1;
CREATE VIEW v_bom_ready_rate AS
SELECT
    bv.id as bom_version_id,
    bv.project_id,
    bv.machine_id,
    bv.version_no,
    COUNT(bi.id) as total_items,
    SUM(CASE WHEN bi.ready_status = 'READY' THEN 1 ELSE 0 END) as ready_items,
    ROUND(SUM(CASE WHEN bi.ready_status = 'READY' THEN 1 ELSE 0 END) * 100.0 / COUNT(bi.id), 2) as ready_rate_count,
    SUM(bi.amount) as total_amount,
    SUM(CASE WHEN bi.ready_status = 'READY' THEN bi.amount ELSE 0 END) as ready_amount,
    ROUND(SUM(CASE WHEN bi.ready_status = 'READY' THEN bi.amount ELSE 0 END) * 100.0 / NULLIF(SUM(bi.amount), 0), 2) as ready_rate_amount
FROM bom_versions bv
LEFT JOIN bom_items bi ON bv.id = bi.bom_version_id
WHERE bv.is_current = 1
GROUP BY bv.id;
CREATE VIEW v_po_statistics AS
SELECT
    po.id,
    po.order_no,
    po.supplier_id,
    s.supplier_name,
    po.project_id,
    po.order_date,
    po.required_date,
    po.total_amount,
    po.status,
    SUM(poi.received_qty) as total_received_qty,
    SUM(poi.quantity) as total_order_qty,
    ROUND(SUM(poi.received_qty) * 100.0 / NULLIF(SUM(poi.quantity), 0), 2) as receive_rate
FROM purchase_orders po
LEFT JOIN suppliers s ON po.supplier_id = s.id
LEFT JOIN purchase_order_items poi ON po.id = poi.order_id
GROUP BY po.id;
CREATE VIEW v_user_active_roles AS
SELECT
    ura.id AS assignment_id,
    ura.user_id,
    u.username,
    e.name AS employee_name,
    ura.role_id,
    r.role_code,
    r.role_name,
    r.role_type,
    r.data_scope,
    r.level AS role_level,
    ura.scope_type,
    ura.scope_id,
    ura.effective_from,
    ura.effective_until
FROM user_role_assignments ura
JOIN users u ON ura.user_id = u.id
JOIN employees e ON u.employee_id = e.id
JOIN roles r ON ura.role_id = r.id
WHERE ura.status = 'ACTIVE'
  AND r.status = 'ACTIVE'
  AND (ura.effective_from IS NULL OR ura.effective_from <= CURRENT_TIMESTAMP)
  AND (ura.effective_until IS NULL OR ura.effective_until > CURRENT_TIMESTAMP);
CREATE VIEW v_role_hierarchy AS
WITH RECURSIVE role_tree AS (
    -- 根节点（无父角色）
    SELECT
        id, role_code, role_name, role_type,
        parent_role_id, level, data_scope, status,
        role_code AS path,
        0 AS depth
    FROM roles
    WHERE parent_role_id IS NULL

    UNION ALL

    -- 子节点
    SELECT
        r.id, r.role_code, r.role_name, r.role_type,
        r.parent_role_id, r.level, r.data_scope, r.status,
        rt.path || ' > ' || r.role_code AS path,
        rt.depth + 1 AS depth
    FROM roles r
    JOIN role_tree rt ON r.parent_role_id = rt.id
)
SELECT * FROM role_tree
;
CREATE VIEW v_acceptance_overview AS
SELECT
    ao.id,
    ao.order_no,
    ao.acceptance_type,
    ao.project_id,
    p.project_name,
    ao.machine_id,
    m.machine_name,
    ao.status,
    ao.overall_result,
    ao.planned_date,
    ao.actual_start_date,
    ao.actual_end_date,
    ao.total_items,
    ao.passed_items,
    ao.failed_items,
    ao.pass_rate,
    ao.qa_signer_id,
    ao.customer_signer,
    (SELECT COUNT(*) FROM acceptance_issues ai WHERE ai.order_id = ao.id AND ai.status = 'OPEN') as open_issues,
    (SELECT COUNT(*) FROM acceptance_issues ai WHERE ai.order_id = ao.id AND ai.is_blocking = 1 AND ai.status != 'CLOSED') as blocking_issues
FROM acceptance_orders ao
LEFT JOIN projects p ON ao.project_id = p.id
LEFT JOIN machines m ON ao.machine_id = m.id;
CREATE VIEW v_pending_alerts AS
SELECT
    ar.id,
    ar.alert_no,
    ar.alert_level,
    ar.alert_title,
    ar.target_type,
    ar.target_no,
    ar.target_name,
    ar.project_id,
    p.project_name,
    ar.triggered_at,
    ar.status,
    ar.handler_id,
    u.username as handler_name,
    r.rule_name,
    JULIANDAY('now') - JULIANDAY(ar.triggered_at) as pending_days
FROM alert_records ar
LEFT JOIN projects p ON ar.project_id = p.id
LEFT JOIN users u ON ar.handler_id = u.id
LEFT JOIN alert_rules r ON ar.rule_id = r.id
WHERE ar.status IN ('PENDING', 'ACKNOWLEDGED', 'PROCESSING');
CREATE VIEW v_open_exceptions AS
SELECT
    ee.id,
    ee.event_no,
    ee.event_type,
    ee.severity,
    ee.event_title,
    ee.project_id,
    p.project_name,
    ee.machine_id,
    m.machine_name,
    ee.status,
    ee.discovered_at,
    ee.due_date,
    ee.is_overdue,
    ee.responsible_user_id,
    u.username as responsible_name,
    JULIANDAY('now') - JULIANDAY(ee.discovered_at) as open_days
FROM exception_events ee
LEFT JOIN projects p ON ee.project_id = p.id
LEFT JOIN machines m ON ee.machine_id = m.id
LEFT JOIN users u ON ee.responsible_user_id = u.id
WHERE ee.status NOT IN ('CLOSED', 'DEFERRED');
CREATE VIEW v_ecn_overview AS
SELECT
    e.id,
    e.ecn_no,
    e.ecn_title,
    e.ecn_type,
    e.project_id,
    p.project_name,
    e.status,
    e.priority,
    e.cost_impact,
    e.schedule_impact_days,
    e.applicant_id,
    u.username as applicant_name,
    e.applied_at,
    e.created_at,
    (SELECT COUNT(*) FROM ecn_evaluations ev WHERE ev.ecn_id = e.id AND ev.status = 'COMPLETED') as completed_evals,
    (SELECT COUNT(*) FROM ecn_evaluations ev WHERE ev.ecn_id = e.id) as total_evals,
    (SELECT COUNT(*) FROM ecn_tasks t WHERE t.ecn_id = e.id AND t.status = 'COMPLETED') as completed_tasks,
    (SELECT COUNT(*) FROM ecn_tasks t WHERE t.ecn_id = e.id) as total_tasks
FROM ecn e
LEFT JOIN projects p ON e.project_id = p.id
LEFT JOIN users u ON e.applicant_id = u.id;
CREATE VIEW v_outsourcing_overview AS
SELECT
    oo.id,
    oo.order_no,
    oo.order_type,
    oo.order_title,
    oo.vendor_id,
    ov.vendor_name,
    oo.project_id,
    p.project_name,
    oo.total_amount,
    oo.amount_with_tax,
    oo.required_date,
    oo.estimated_date,
    oo.actual_date,
    oo.status,
    oo.payment_status,
    oo.paid_amount,
    (SELECT COUNT(*) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as item_count,
    (SELECT SUM(delivered_quantity) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as total_delivered,
    (SELECT SUM(quantity) FROM outsourcing_order_items oi WHERE oi.order_id = oo.id) as total_quantity
FROM outsourcing_orders oo
LEFT JOIN outsourcing_vendors ov ON oo.vendor_id = ov.id
LEFT JOIN projects p ON oo.project_id = p.id;
CREATE TRIGGER update_task_approval_workflows_timestamp
AFTER UPDATE ON task_approval_workflows
BEGIN
    UPDATE task_approval_workflows SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
CREATE TRIGGER update_task_completion_proofs_timestamp
AFTER UPDATE ON task_completion_proofs
BEGIN
    UPDATE task_completion_proofs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
CREATE TRIGGER update_project_role_types_timestamp
AFTER UPDATE ON project_role_types
BEGIN
    UPDATE project_role_types SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
CREATE TRIGGER update_project_role_configs_timestamp
AFTER UPDATE ON project_role_configs
BEGIN
    UPDATE project_role_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
CREATE INDEX idx_holiday_date ON holidays(holiday_date);
CREATE INDEX idx_holiday_year ON holidays(year);
CREATE INDEX idx_holiday_type ON holidays(holiday_type);
CREATE INDEX idx_leads_owner ON leads(owner_id);
CREATE INDEX idx_opportunities_customer ON opportunities(customer_id);
CREATE INDEX idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX idx_quotes_opportunity ON quotes(opportunity_id);
CREATE INDEX idx_quote_versions_quote ON quote_versions(quote_id);
CREATE INDEX idx_quote_items_version ON quote_items(quote_version_id);
CREATE INDEX idx_contracts_customer ON contracts(customer_id);
CREATE INDEX idx_contracts_project ON contracts(project_id);
CREATE INDEX idx_invoices_contract ON invoices(contract_id);
CREATE INDEX idx_invoices_payment ON invoices(payment_id);
CREATE INDEX idx_disputes_payment ON receivable_disputes(payment_id);
CREATE INDEX idx_payments_contract ON payments(contract_id);
CREATE INDEX idx_payments_milestone ON payments(milestone_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_responsible ON payments(responsible_id);
CREATE INDEX idx_payments_due_date ON payments(due_date);
CREATE INDEX idx_users_employee ON users(employee_id);
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_perm ON role_permissions(permission_id);
CREATE INDEX idx_permission_audits_operator ON permission_audits(operator_id);
CREATE UNIQUE INDEX idx_user_roles_unique ON user_roles(user_id, role_id);
CREATE UNIQUE INDEX idx_role_permissions_unique ON role_permissions(role_id, permission_id);
CREATE INDEX idx_wbs_template_tasks_template ON wbs_template_tasks(template_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_milestone ON tasks(milestone_id);
CREATE INDEX idx_tasks_owner ON tasks(owner_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_task_deps_task ON task_dependencies(task_id);
CREATE INDEX idx_task_deps_depends ON task_dependencies(depends_on_task_id);
CREATE INDEX idx_progress_logs_task ON progress_logs(task_id);
CREATE INDEX idx_schedule_baselines_project ON schedule_baselines(project_id);
CREATE INDEX idx_baseline_tasks_baseline ON baseline_tasks(baseline_id);
CREATE INDEX idx_projects_code ON projects(project_code);
CREATE INDEX idx_projects_customer ON projects(customer_id);
CREATE INDEX idx_projects_pm ON projects(pm_id);
CREATE INDEX idx_projects_stage ON projects(stage);
CREATE INDEX idx_projects_health ON projects(health);
CREATE INDEX idx_projects_active ON projects(is_active);
CREATE INDEX idx_machines_project ON machines(project_id);
CREATE INDEX idx_machines_stage ON machines(stage);
CREATE INDEX idx_project_statuses_stage ON project_statuses(stage_id);
CREATE INDEX idx_project_status_logs_project ON project_status_logs(project_id);
CREATE INDEX idx_project_status_logs_machine ON project_status_logs(machine_id);
CREATE INDEX idx_project_status_logs_time ON project_status_logs(changed_at);
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
CREATE INDEX idx_project_milestones_project ON project_milestones(project_id);
CREATE INDEX idx_project_milestones_status ON project_milestones(status);
CREATE INDEX idx_project_milestones_date ON project_milestones(planned_date);
CREATE INDEX idx_project_payment_plans_project ON project_payment_plans(project_id);
CREATE INDEX idx_project_payment_plans_status ON project_payment_plans(status);
CREATE INDEX idx_project_costs_project ON project_costs(project_id);
CREATE INDEX idx_project_costs_type ON project_costs(cost_type);
CREATE INDEX idx_project_costs_date ON project_costs(cost_date);
CREATE INDEX idx_project_documents_project ON project_documents(project_id);
CREATE INDEX idx_project_documents_type ON project_documents(doc_type);
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_name ON customers(customer_name);
CREATE INDEX idx_customers_industry ON customers(industry);
CREATE INDEX idx_materials_code ON materials(material_code);
CREATE INDEX idx_materials_name ON materials(material_name);
CREATE INDEX idx_materials_category ON materials(category_l1, category_l2);
CREATE INDEX idx_materials_type ON materials(material_type);
CREATE INDEX idx_materials_status ON materials(status);
CREATE INDEX idx_suppliers_code ON suppliers(supplier_code);
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);
CREATE INDEX idx_suppliers_type ON suppliers(supplier_type);
CREATE INDEX idx_suppliers_status ON suppliers(cooperation_status);
CREATE INDEX idx_supplier_quotations_supplier ON supplier_quotations(supplier_id);
CREATE INDEX idx_supplier_quotations_material ON supplier_quotations(material_id);
CREATE INDEX idx_bom_versions_project ON bom_versions(project_id);
CREATE INDEX idx_bom_versions_machine ON bom_versions(machine_id);
CREATE INDEX idx_bom_versions_status ON bom_versions(status);
CREATE INDEX idx_bom_items_version ON bom_items(bom_version_id);
CREATE INDEX idx_bom_items_material ON bom_items(material_id);
CREATE INDEX idx_bom_items_parent ON bom_items(parent_item_id);
CREATE INDEX idx_bom_items_ready ON bom_items(ready_status);
CREATE INDEX idx_purchase_requests_no ON purchase_requests(request_no);
CREATE INDEX idx_purchase_requests_project ON purchase_requests(project_id);
CREATE INDEX idx_purchase_requests_status ON purchase_requests(status);
CREATE INDEX idx_pr_items_request ON purchase_request_items(request_id);
CREATE INDEX idx_purchase_orders_no ON purchase_orders(order_no);
CREATE INDEX idx_purchase_orders_project ON purchase_orders(project_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_orders_date ON purchase_orders(order_date);
CREATE INDEX idx_po_items_order ON purchase_order_items(order_id);
CREATE INDEX idx_po_items_material ON purchase_order_items(material_id);
CREATE INDEX idx_goods_receipts_no ON goods_receipts(receipt_no);
CREATE INDEX idx_goods_receipts_order ON goods_receipts(order_id);
CREATE INDEX idx_goods_receipts_date ON goods_receipts(receipt_date);
CREATE INDEX idx_gr_items_receipt ON goods_receipt_items(receipt_id);
CREATE INDEX idx_shortage_alerts_project ON shortage_alerts(project_id);
CREATE INDEX idx_shortage_alerts_status ON shortage_alerts(status);
CREATE INDEX idx_shortage_alerts_level ON shortage_alerts(alert_level);
CREATE INDEX idx_material_categories_parent ON material_categories(parent_id);
CREATE INDEX idx_roles_parent ON roles(parent_role_id);
CREATE INDEX idx_roles_level ON roles(level);
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_roles_type ON roles(role_type);
CREATE INDEX idx_role_templates_code ON role_templates(template_code);
CREATE INDEX idx_role_templates_active ON role_templates(is_active);
CREATE INDEX idx_tpl_perms_template ON role_template_permissions(template_id);
CREATE INDEX idx_tpl_perms_perm ON role_template_permissions(permission_id);
CREATE UNIQUE INDEX idx_tpl_perms_unique ON role_template_permissions(template_id, permission_id);
CREATE INDEX idx_assignments_user ON user_role_assignments(user_id);
CREATE INDEX idx_assignments_role ON user_role_assignments(role_id);
CREATE INDEX idx_assignments_status ON user_role_assignments(status);
CREATE INDEX idx_assignments_scope ON user_role_assignments(scope_type, scope_id);
CREATE INDEX idx_assignments_effective ON user_role_assignments(effective_from, effective_until);
CREATE INDEX idx_approvals_assignment ON role_assignment_approvals(assignment_id);
CREATE INDEX idx_approvals_approver ON role_assignment_approvals(approver_id);
CREATE INDEX idx_approvals_decision ON role_assignment_approvals(decision);
CREATE INDEX idx_departments_parent ON departments(parent_id);
CREATE INDEX idx_departments_active ON departments(is_active);
CREATE INDEX idx_dept_roles_dept ON department_default_roles(department_id);
CREATE INDEX idx_dept_roles_role ON department_default_roles(role_id);
CREATE UNIQUE INDEX idx_dept_roles_unique ON department_default_roles(department_id, role_id);
CREATE INDEX idx_dept_admins_dept ON department_role_admins(department_id);
CREATE INDEX idx_dept_admins_user ON department_role_admins(user_id);
CREATE UNIQUE INDEX idx_dept_admins_unique ON department_role_admins(department_id, user_id);
CREATE INDEX idx_exclusions_role_a ON role_exclusions(role_id_a);
CREATE INDEX idx_exclusions_role_b ON role_exclusions(role_id_b);
CREATE INDEX idx_exclusions_active ON role_exclusions(is_active);
CREATE INDEX idx_role_audits_event ON role_audits(event_type);
CREATE INDEX idx_role_audits_target ON role_audits(target_type, target_id);
CREATE INDEX idx_role_audits_operator ON role_audits(operator_id);
CREATE INDEX idx_role_audits_time ON role_audits(created_at);
CREATE INDEX idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_paid_date ON invoices(paid_date);
CREATE INDEX idx_quote_approval_quote ON quote_approvals(quote_id);
CREATE INDEX idx_quote_approval_approver ON quote_approvals(approver_id);
CREATE INDEX idx_quote_approval_status ON quote_approvals(status);
CREATE INDEX idx_contract_approval_contract ON contract_approvals(contract_id);
CREATE INDEX idx_contract_approval_approver ON contract_approvals(approver_id);
CREATE INDEX idx_contract_approval_status ON contract_approvals(status);
CREATE INDEX idx_invoice_approval_invoice ON invoice_approvals(invoice_id);
CREATE INDEX idx_invoice_approval_approver ON invoice_approvals(approver_id);
CREATE INDEX idx_invoice_approval_status ON invoice_approvals(status);
CREATE INDEX idx_templates_type ON acceptance_templates(acceptance_type);
CREATE INDEX idx_templates_equip ON acceptance_templates(equipment_type);
CREATE INDEX idx_check_items_category ON template_check_items(category_id);
CREATE INDEX idx_orders_project ON acceptance_orders(project_id);
CREATE INDEX idx_orders_machine ON acceptance_orders(machine_id);
CREATE INDEX idx_orders_status ON acceptance_orders(status);
CREATE INDEX idx_orders_type ON acceptance_orders(acceptance_type);
CREATE INDEX idx_order_items_order ON acceptance_order_items(order_id);
CREATE INDEX idx_order_items_status ON acceptance_order_items(result_status);
CREATE INDEX idx_issues_order ON acceptance_issues(order_id);
CREATE INDEX idx_issues_status ON acceptance_issues(status);
CREATE INDEX idx_issues_severity ON acceptance_issues(severity);
CREATE INDEX idx_issues_assigned ON acceptance_issues(assigned_to);
CREATE INDEX idx_follow_ups_issue ON issue_follow_ups(issue_id);
CREATE INDEX idx_signatures_order ON acceptance_signatures(order_id);
CREATE INDEX idx_reports_order ON acceptance_reports(order_id);
CREATE INDEX idx_alert_rules_type ON alert_rules(rule_type);
CREATE INDEX idx_alert_rules_target ON alert_rules(target_type);
CREATE INDEX idx_alert_rules_enabled ON alert_rules(is_enabled);
CREATE INDEX idx_alerts_rule ON alert_records(rule_id);
CREATE INDEX idx_alerts_target ON alert_records(target_type, target_id);
CREATE INDEX idx_alerts_project ON alert_records(project_id);
CREATE INDEX idx_alerts_status ON alert_records(status);
CREATE INDEX idx_alerts_level ON alert_records(alert_level);
CREATE INDEX idx_alerts_time ON alert_records(triggered_at);
CREATE INDEX idx_notifications_alert ON alert_notifications(alert_id);
CREATE INDEX idx_notifications_user ON alert_notifications(notify_user_id);
CREATE INDEX idx_notifications_status ON alert_notifications(status);
CREATE INDEX idx_events_project ON exception_events(project_id);
CREATE INDEX idx_events_type ON exception_events(event_type);
CREATE INDEX idx_events_severity ON exception_events(severity);
CREATE INDEX idx_events_status ON exception_events(status);
CREATE INDEX idx_events_responsible ON exception_events(responsible_user_id);
CREATE INDEX idx_actions_event ON exception_actions(event_id);
CREATE INDEX idx_actions_type ON exception_actions(action_type);
CREATE INDEX idx_escalations_event ON exception_escalations(event_id);
CREATE INDEX idx_statistics_date ON alert_statistics(stat_date);
CREATE INDEX idx_statistics_type ON alert_statistics(stat_type);
CREATE INDEX idx_health_project ON project_health_snapshots(project_id);
CREATE INDEX idx_health_date ON project_health_snapshots(snapshot_date);
CREATE INDEX idx_order_officially_completed ON acceptance_orders(is_officially_completed);
CREATE INDEX idx_ecn_no ON ecn(ecn_no);
CREATE INDEX idx_ecn_project ON ecn(project_id);
CREATE INDEX idx_ecn_status ON ecn(status);
CREATE INDEX idx_ecn_type ON ecn(ecn_type);
CREATE INDEX idx_ecn_applicant ON ecn(applicant_id);
CREATE INDEX idx_ecn_evaluations_ecn ON ecn_evaluations(ecn_id);
CREATE INDEX idx_ecn_evaluations_dept ON ecn_evaluations(eval_dept);
CREATE INDEX idx_ecn_evaluations_status ON ecn_evaluations(status);
CREATE INDEX idx_ecn_approvals_ecn ON ecn_approvals(ecn_id);
CREATE INDEX idx_ecn_approvals_approver ON ecn_approvals(approver_id);
CREATE INDEX idx_ecn_approvals_status ON ecn_approvals(status);
CREATE INDEX idx_ecn_tasks_ecn ON ecn_tasks(ecn_id);
CREATE INDEX idx_ecn_tasks_assignee ON ecn_tasks(assignee_id);
CREATE INDEX idx_ecn_tasks_status ON ecn_tasks(status);
CREATE INDEX idx_ecn_materials_ecn ON ecn_affected_materials(ecn_id);
CREATE INDEX idx_ecn_materials_material ON ecn_affected_materials(material_id);
CREATE INDEX idx_ecn_orders_ecn ON ecn_affected_orders(ecn_id);
CREATE INDEX idx_ecn_logs_ecn ON ecn_logs(ecn_id);
CREATE INDEX idx_ecn_logs_time ON ecn_logs(created_at);
CREATE INDEX idx_ecn_matrix_type ON ecn_approval_matrix(ecn_type);
CREATE INDEX idx_vendors_code ON outsourcing_vendors(vendor_code);
CREATE INDEX idx_vendors_type ON outsourcing_vendors(vendor_type);
CREATE INDEX idx_vendors_status ON outsourcing_vendors(status);
CREATE INDEX idx_os_orders_no ON outsourcing_orders(order_no);
CREATE INDEX idx_os_orders_vendor ON outsourcing_orders(vendor_id);
CREATE INDEX idx_os_orders_project ON outsourcing_orders(project_id);
CREATE INDEX idx_os_orders_status ON outsourcing_orders(status);
CREATE INDEX idx_os_items_order ON outsourcing_order_items(order_id);
CREATE INDEX idx_os_items_material ON outsourcing_order_items(material_id);
CREATE INDEX idx_os_deliveries_order ON outsourcing_deliveries(order_id);
CREATE INDEX idx_os_deliveries_vendor ON outsourcing_deliveries(vendor_id);
CREATE INDEX idx_os_deliveries_status ON outsourcing_deliveries(status);
CREATE INDEX idx_os_delivery_items_delivery ON outsourcing_delivery_items(delivery_id);
CREATE INDEX idx_os_inspections_delivery ON outsourcing_inspections(delivery_id);
CREATE INDEX idx_os_inspections_result ON outsourcing_inspections(inspect_result);
CREATE INDEX idx_os_payments_vendor ON outsourcing_payments(vendor_id);
CREATE INDEX idx_os_payments_order ON outsourcing_payments(order_id);
CREATE INDEX idx_os_payments_status ON outsourcing_payments(status);
CREATE INDEX idx_os_evaluations_vendor ON outsourcing_evaluations(vendor_id);
CREATE INDEX idx_os_evaluations_period ON outsourcing_evaluations(eval_period);
CREATE INDEX idx_os_progress_order ON outsourcing_progress(order_id);
CREATE INDEX idx_os_progress_date ON outsourcing_progress(report_date);
CREATE INDEX idx_perf_period_code ON performance_period(period_code);
CREATE INDEX idx_perf_period_dates ON performance_period(start_date, end_date);
CREATE INDEX idx_perf_indicator_code ON performance_indicator(indicator_code);
CREATE INDEX idx_perf_indicator_type ON performance_indicator(indicator_type);
CREATE INDEX idx_perf_result_period ON performance_result(period_id);
CREATE INDEX idx_perf_result_user ON performance_result(user_id);
CREATE INDEX idx_perf_result_dept ON performance_result(department_id);
CREATE INDEX idx_perf_result_score ON performance_result(total_score);
CREATE INDEX idx_perf_eval_result ON performance_evaluation(result_id);
CREATE INDEX idx_perf_eval_evaluator ON performance_evaluation(evaluator_id);
CREATE INDEX idx_appeal_result ON performance_appeal(result_id);
CREATE INDEX idx_appeal_appellant ON performance_appeal(appellant_id);
CREATE INDEX idx_appeal_status ON performance_appeal(status);
CREATE INDEX idx_contrib_period ON project_contribution(period_id);
CREATE INDEX idx_contrib_user ON project_contribution(user_id);
CREATE INDEX idx_contrib_project ON project_contribution(project_id);
CREATE INDEX idx_ranking_period ON performance_ranking_snapshot(period_id);
CREATE INDEX idx_ranking_scope ON performance_ranking_snapshot(scope_type, scope_id);
CREATE INDEX idx_ts_user ON timesheet(user_id);
CREATE INDEX idx_ts_project ON timesheet(project_id);
CREATE INDEX idx_ts_date ON timesheet(work_date);
CREATE INDEX idx_ts_status ON timesheet(status);
CREATE INDEX idx_ts_user_date ON timesheet(user_id, work_date);
CREATE INDEX idx_batch_user ON timesheet_batch(user_id);
CREATE INDEX idx_batch_week ON timesheet_batch(week_start, week_end);
CREATE INDEX idx_batch_status ON timesheet_batch(status);
CREATE UNIQUE INDEX idx_batch_user_week ON timesheet_batch(user_id, week_start);
CREATE INDEX idx_summary_user_month ON timesheet_summary(user_id, year, month);
CREATE INDEX idx_summary_project_month ON timesheet_summary(project_id, year, month);
CREATE INDEX idx_summary_dept_month ON timesheet_summary(department_id, year, month);
CREATE INDEX idx_overtime_applicant ON overtime_application(applicant_id);
CREATE INDEX idx_overtime_date ON overtime_application(overtime_date);
CREATE INDEX idx_overtime_status ON overtime_application(status);
CREATE INDEX idx_approval_timesheet ON timesheet_approval_log(timesheet_id);
CREATE INDEX idx_approval_batch ON timesheet_approval_log(batch_id);
CREATE INDEX idx_approval_approver ON timesheet_approval_log(approver_id);
CREATE INDEX idx_rule_code ON timesheet_rule(rule_code);
CREATE INDEX idx_rpt_tpl_code ON report_template(template_code);
CREATE INDEX idx_rpt_tpl_type ON report_template(report_type);
CREATE INDEX idx_rpt_def_code ON report_definition(report_code);
CREATE INDEX idx_rpt_def_owner ON report_definition(owner_id);
CREATE INDEX idx_rpt_def_type ON report_definition(report_type);
CREATE INDEX idx_rpt_gen_definition ON report_generation(report_definition_id);
CREATE INDEX idx_rpt_gen_type ON report_generation(report_type);
CREATE INDEX idx_rpt_gen_time ON report_generation(generated_at);
CREATE INDEX idx_subscription_user ON report_subscription(subscriber_id);
CREATE INDEX idx_subscription_type ON report_subscription(report_type);
CREATE INDEX idx_import_task_no ON data_import_task(task_no);
CREATE INDEX idx_import_type ON data_import_task(import_type);
CREATE INDEX idx_import_status ON data_import_task(status);
CREATE INDEX idx_import_user ON data_import_task(imported_by);
CREATE INDEX idx_export_task_no ON data_export_task(task_no);
CREATE INDEX idx_export_type ON data_export_task(export_type);
CREATE INDEX idx_export_status ON data_export_task(status);
CREATE INDEX idx_export_user ON data_export_task(exported_by);
CREATE INDEX idx_import_tpl_code ON import_template(template_code);
CREATE INDEX idx_import_tpl_type ON import_template(import_type);
CREATE INDEX idx_pmo_init_no ON pmo_project_initiation(application_no);
CREATE INDEX idx_pmo_init_status ON pmo_project_initiation(status);
CREATE INDEX idx_pmo_init_applicant ON pmo_project_initiation(applicant_id);
CREATE INDEX idx_pmo_phase_project ON pmo_project_phase(project_id);
CREATE INDEX idx_pmo_phase_code ON pmo_project_phase(phase_code);
CREATE INDEX idx_pmo_change_project ON pmo_change_request(project_id);
CREATE INDEX idx_pmo_change_no ON pmo_change_request(change_no);
CREATE INDEX idx_pmo_change_status ON pmo_change_request(status);
CREATE INDEX idx_pmo_risk_project ON pmo_project_risk(project_id);
CREATE INDEX idx_pmo_risk_level ON pmo_project_risk(risk_level);
CREATE INDEX idx_pmo_risk_status ON pmo_project_risk(status);
CREATE INDEX idx_pmo_cost_project ON pmo_project_cost(project_id);
CREATE INDEX idx_pmo_cost_category ON pmo_project_cost(cost_category);
CREATE INDEX idx_pmo_cost_month ON pmo_project_cost(cost_month);
CREATE INDEX idx_pmo_meeting_project ON pmo_meeting(project_id);
CREATE INDEX idx_pmo_meeting_date ON pmo_meeting(meeting_date);
CREATE INDEX idx_pmo_meeting_type ON pmo_meeting(meeting_type);
CREATE INDEX idx_pmo_alloc_project ON pmo_resource_allocation(project_id);
CREATE INDEX idx_pmo_alloc_resource ON pmo_resource_allocation(resource_id);
CREATE INDEX idx_task_code ON task_unified(task_code);
CREATE INDEX idx_task_assignee ON task_unified(assignee_id);
CREATE INDEX idx_task_project ON task_unified(project_id);
CREATE INDEX idx_task_status ON task_unified(status);
CREATE INDEX idx_task_type ON task_unified(task_type);
CREATE INDEX idx_task_deadline ON task_unified(deadline);
CREATE INDEX idx_task_priority ON task_unified(priority);
CREATE INDEX idx_duty_position ON job_duty_template(position_id);
CREATE INDEX idx_duty_frequency ON job_duty_template(frequency);
CREATE INDEX idx_task_log_task ON task_operation_log(task_id);
CREATE INDEX idx_task_log_operator ON task_operation_log(operator_id);
CREATE INDEX idx_task_comment_task ON task_comment(task_id);
CREATE INDEX idx_reminder_task ON task_reminder(task_id);
CREATE INDEX idx_reminder_user ON task_reminder(user_id);
CREATE INDEX idx_reminder_time ON task_reminder(remind_at);
CREATE INDEX idx_presale_ticket_no ON presale_support_ticket(ticket_no);
CREATE INDEX idx_presale_ticket_status ON presale_support_ticket(status);
CREATE INDEX idx_presale_ticket_applicant ON presale_support_ticket(applicant_id);
CREATE INDEX idx_presale_ticket_assignee ON presale_support_ticket(assignee_id);
CREATE INDEX idx_presale_ticket_customer ON presale_support_ticket(customer_id);
CREATE INDEX idx_deliverable_ticket ON presale_ticket_deliverable(ticket_id);
CREATE INDEX idx_progress_ticket ON presale_ticket_progress(ticket_id);
CREATE INDEX idx_solution_no ON presale_solution(solution_no);
CREATE INDEX idx_solution_ticket ON presale_solution(ticket_id);
CREATE INDEX idx_solution_customer ON presale_solution(customer_id);
CREATE INDEX idx_solution_industry ON presale_solution(industry);
CREATE INDEX idx_cost_solution ON presale_solution_cost(solution_id);
CREATE INDEX idx_template_no ON presale_solution_template(template_no);
CREATE INDEX idx_template_industry ON presale_solution_template(industry);
CREATE INDEX idx_workload_date ON presale_workload(stat_date);
CREATE INDEX idx_tender_opportunity ON presale_tender_record(opportunity_id);
CREATE INDEX idx_tender_result ON presale_tender_record(result);
CREATE INDEX idx_workshop_code ON workshop(workshop_code);
CREATE INDEX idx_workshop_type ON workshop(workshop_type);
CREATE INDEX idx_workstation_code ON workstation(workstation_code);
CREATE INDEX idx_workstation_workshop ON workstation(workshop_id);
CREATE INDEX idx_workstation_status ON workstation(status);
CREATE INDEX idx_worker_no ON worker(worker_no);
CREATE INDEX idx_worker_workshop ON worker(workshop_id);
CREATE INDEX idx_worker_status ON worker(status);
CREATE INDEX idx_worker_skill_worker ON worker_skill(worker_id);
CREATE INDEX idx_worker_skill_process ON worker_skill(process_id);
CREATE INDEX idx_process_code ON process_dict(process_code);
CREATE INDEX idx_process_type ON process_dict(process_type);
CREATE INDEX idx_equipment_code ON equipment(equipment_code);
CREATE INDEX idx_equipment_workshop ON equipment(workshop_id);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_equip_maint_equipment ON equipment_maintenance(equipment_id);
CREATE INDEX idx_equip_maint_date ON equipment_maintenance(maintenance_date);
CREATE INDEX idx_prod_plan_no ON production_plan(plan_no);
CREATE INDEX idx_prod_plan_project ON production_plan(project_id);
CREATE INDEX idx_prod_plan_workshop ON production_plan(workshop_id);
CREATE INDEX idx_prod_plan_status ON production_plan(status);
CREATE INDEX idx_prod_plan_dates ON production_plan(plan_start_date, plan_end_date);
CREATE INDEX idx_work_order_no ON work_order(work_order_no);
CREATE INDEX idx_work_order_project ON work_order(project_id);
CREATE INDEX idx_work_order_plan ON work_order(production_plan_id);
CREATE INDEX idx_work_order_workshop ON work_order(workshop_id);
CREATE INDEX idx_work_order_assigned ON work_order(assigned_to);
CREATE INDEX idx_work_order_status ON work_order(status);
CREATE INDEX idx_work_order_priority ON work_order(priority);
CREATE INDEX idx_work_order_dates ON work_order(plan_start_date, plan_end_date);
CREATE INDEX idx_work_report_no ON work_report(report_no);
CREATE INDEX idx_work_report_order ON work_report(work_order_id);
CREATE INDEX idx_work_report_worker ON work_report(worker_id);
CREATE INDEX idx_work_report_type ON work_report(report_type);
CREATE INDEX idx_work_report_status ON work_report(status);
CREATE INDEX idx_work_report_time ON work_report(report_time);
CREATE INDEX idx_prod_exc_no ON production_exception(exception_no);
CREATE INDEX idx_prod_exc_type ON production_exception(exception_type);
CREATE INDEX idx_prod_exc_level ON production_exception(exception_level);
CREATE INDEX idx_prod_exc_status ON production_exception(status);
CREATE INDEX idx_prod_exc_work_order ON production_exception(work_order_id);
CREATE INDEX idx_prod_exc_project ON production_exception(project_id);
CREATE INDEX idx_mat_req_no ON material_requisition(requisition_no);
CREATE INDEX idx_mat_req_work_order ON material_requisition(work_order_id);
CREATE INDEX idx_mat_req_project ON material_requisition(project_id);
CREATE INDEX idx_mat_req_status ON material_requisition(status);
CREATE INDEX idx_mat_req_item_requisition ON material_requisition_item(requisition_id);
CREATE INDEX idx_mat_req_item_material ON material_requisition_item(material_id);
CREATE INDEX idx_prod_daily_date ON production_daily_report(report_date);
CREATE INDEX idx_prod_daily_workshop ON production_daily_report(workshop_id);
CREATE INDEX idx_issue_no ON issues(issue_no);
CREATE INDEX idx_issue_category ON issues(category);
CREATE INDEX idx_issue_project ON issues(project_id);
CREATE INDEX idx_issue_machine ON issues(machine_id);
CREATE INDEX idx_issue_task ON issues(task_id);
CREATE INDEX idx_issue_status ON issues(status);
CREATE INDEX idx_issue_severity ON issues(severity);
CREATE INDEX idx_issue_priority ON issues(priority);
CREATE INDEX idx_issue_assignee ON issues(assignee_id);
CREATE INDEX idx_issue_reporter ON issues(reporter_id);
CREATE INDEX idx_issue_blocking ON issues(is_blocking);
CREATE INDEX idx_issue_due_date ON issues(due_date);
CREATE INDEX idx_follow_up_issue ON issue_follow_up_records(issue_id);
CREATE INDEX idx_follow_up_type ON issue_follow_up_records(follow_up_type);
CREATE INDEX idx_follow_up_operator ON issue_follow_up_records(operator_id);
CREATE INDEX idx_follow_up_created ON issue_follow_up_records(created_at);
CREATE INDEX idx_rd_category_code ON rd_project_category(category_code);
CREATE INDEX idx_rd_category_type ON rd_project_category(category_type);
CREATE INDEX idx_rd_project_no ON rd_project(project_no);
CREATE INDEX idx_rd_project_category ON rd_project(category_id);
CREATE INDEX idx_rd_project_status ON rd_project(status);
CREATE INDEX idx_rd_project_manager ON rd_project(project_manager_id);
CREATE INDEX idx_rd_project_linked ON rd_project(linked_project_id);
CREATE INDEX idx_rd_cost_type_code ON rd_cost_type(type_code);
CREATE INDEX idx_rd_cost_type_category ON rd_cost_type(category);
CREATE INDEX idx_rd_allocation_rule_name ON rd_cost_allocation_rule(rule_name);
CREATE INDEX idx_rd_allocation_rule_type ON rd_cost_allocation_rule(rule_type);
CREATE INDEX idx_rd_cost_no ON rd_cost(cost_no);
CREATE INDEX idx_rd_cost_project ON rd_cost(rd_project_id);
CREATE INDEX idx_rd_cost_type ON rd_cost(cost_type_id);
CREATE INDEX idx_rd_cost_date ON rd_cost(cost_date);
CREATE INDEX idx_rd_cost_status ON rd_cost(status);
CREATE INDEX idx_rd_report_no ON rd_report_record(report_no);
CREATE INDEX idx_rd_report_type ON rd_report_record(report_type);
CREATE INDEX idx_rd_report_date ON rd_report_record(generated_at);
CREATE INDEX idx_spec_req_project ON technical_spec_requirements(project_id);
CREATE INDEX idx_spec_req_document ON technical_spec_requirements(document_id);
CREATE INDEX idx_spec_req_material ON technical_spec_requirements(material_code);
CREATE INDEX idx_match_record_project ON spec_match_records(project_id);
CREATE INDEX idx_match_record_spec ON spec_match_records(spec_requirement_id);
CREATE INDEX idx_match_record_type ON spec_match_records(match_type, match_target_id);
CREATE INDEX idx_match_record_status ON spec_match_records(match_status);
CREATE INDEX idx_match_record_alert ON spec_match_records(alert_id);
CREATE INDEX idx_snapshot_date ON issue_statistics_snapshots(snapshot_date);
CREATE INDEX idx_template_code ON issue_templates(template_code);
CREATE INDEX idx_template_category ON issue_templates(category);
CREATE INDEX idx_progress_reports_project ON progress_reports(project_id);
CREATE INDEX idx_progress_reports_machine ON progress_reports(machine_id);
CREATE INDEX idx_progress_reports_task ON progress_reports(task_id);
CREATE INDEX idx_progress_reports_date ON progress_reports(report_date);
CREATE INDEX idx_progress_reports_type ON progress_reports(report_type);
CREATE INDEX idx_project_review_project ON project_reviews(project_id);
CREATE INDEX idx_project_review_date ON project_reviews(review_date);
CREATE INDEX idx_project_review_status ON project_reviews(status);
CREATE INDEX idx_project_lesson_review ON project_lessons(review_id);
CREATE INDEX idx_project_lesson_project ON project_lessons(project_id);
CREATE INDEX idx_project_lesson_type ON project_lessons(lesson_type);
CREATE INDEX idx_project_lesson_status ON project_lessons(status);
CREATE INDEX idx_project_bp_review ON project_best_practices(review_id);
CREATE INDEX idx_project_bp_project ON project_best_practices(project_id);
CREATE INDEX idx_project_bp_category ON project_best_practices(category);
CREATE INDEX idx_project_bp_reusable ON project_best_practices(is_reusable);
CREATE INDEX idx_project_bp_status ON project_best_practices(status);
CREATE INDEX idx_communication_customer ON customer_communications(customer_name);
CREATE INDEX idx_communication_date ON customer_communications(communication_date);
CREATE INDEX idx_satisfaction_customer ON customer_satisfactions(customer_name);
CREATE INDEX idx_satisfaction_date ON customer_satisfactions(survey_date);
CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_status ON knowledge_base(status);
CREATE INDEX idx_kb_faq ON knowledge_base(is_faq);
CREATE INDEX idx_work_order_bom_wo ON mat_work_order_bom(work_order_id);
CREATE INDEX idx_work_order_bom_material ON mat_work_order_bom(material_code);
CREATE INDEX idx_work_order_bom_date ON mat_work_order_bom(required_date);
CREATE INDEX idx_requirement_no ON mat_material_requirement(requirement_no);
CREATE INDEX idx_requirement_wo ON mat_material_requirement(work_order_id);
CREATE INDEX idx_requirement_material ON mat_material_requirement(material_code);
CREATE INDEX idx_requirement_status ON mat_material_requirement(status);
CREATE INDEX idx_requirement_date ON mat_material_requirement(required_date);
CREATE INDEX idx_kit_check_no ON mat_kit_check(check_no);
CREATE INDEX idx_kit_check_wo ON mat_kit_check(work_order_id);
CREATE INDEX idx_kit_check_project ON mat_kit_check(project_id);
CREATE INDEX idx_kit_check_status ON mat_kit_check(kit_status);
CREATE INDEX idx_kit_check_time ON mat_kit_check(check_time);
CREATE INDEX idx_alert_log_alert ON mat_alert_log(alert_id);
CREATE INDEX idx_alert_log_time ON mat_alert_log(action_time);
CREATE INDEX idx_alert_log_operator ON mat_alert_log(operator_id);
CREATE INDEX idx_daily_report_date ON mat_shortage_daily_report(report_date);
CREATE INDEX idx_alert_no ON mat_shortage_alert(alert_no);
CREATE INDEX idx_alert_work_order ON mat_shortage_alert(work_order_id);
CREATE INDEX idx_alert_material ON mat_shortage_alert(material_code);
CREATE INDEX idx_alert_level ON mat_shortage_alert(alert_level);
CREATE INDEX idx_alert_status ON mat_shortage_alert(status);
CREATE INDEX idx_alert_handler ON mat_shortage_alert(handler_id);
CREATE INDEX idx_alert_required_date ON mat_shortage_alert(required_date);
CREATE INDEX idx_invoice_request_no ON invoice_requests(request_no);
CREATE INDEX idx_invoice_request_contract ON invoice_requests(contract_id);
CREATE INDEX idx_invoice_request_project ON invoice_requests(project_id);
CREATE INDEX idx_invoice_request_customer ON invoice_requests(customer_id);
CREATE INDEX idx_invoice_request_status ON invoice_requests(status);
CREATE INDEX idx_invoice_request_plan ON invoice_requests(payment_plan_id);
CREATE INDEX idx_supplier_reg_customer ON customer_supplier_registrations(customer_id);
CREATE INDEX idx_supplier_reg_platform ON customer_supplier_registrations(platform_name);
CREATE INDEX idx_supplier_reg_status ON customer_supplier_registrations(registration_status);
CREATE INDEX idx_task_approval_status ON task_unified(approval_status);
CREATE INDEX idx_task_importance ON task_unified(task_importance);
CREATE INDEX idx_task_is_delayed ON task_unified(is_delayed);
CREATE INDEX idx_taw_task_id ON task_approval_workflows(task_id);
CREATE INDEX idx_taw_approver_id ON task_approval_workflows(approver_id);
CREATE INDEX idx_taw_status ON task_approval_workflows(approval_status);
CREATE INDEX idx_taw_submitted_by ON task_approval_workflows(submitted_by);
CREATE INDEX idx_taw_submitted_at ON task_approval_workflows(submitted_at);
CREATE INDEX idx_tcp_task_id ON task_completion_proofs(task_id);
CREATE INDEX idx_tcp_proof_type ON task_completion_proofs(proof_type);
CREATE INDEX idx_tcp_uploaded_by ON task_completion_proofs(uploaded_by);
CREATE INDEX idx_tcp_uploaded_at ON task_completion_proofs(uploaded_at);
CREATE INDEX idx_issues_responsible_engineer ON issues(responsible_engineer_id);
CREATE INDEX idx_issues_root_cause ON issues(root_cause);
CREATE INDEX idx_monthly_summary_employee ON monthly_work_summary(employee_id);
CREATE INDEX idx_monthly_summary_period ON monthly_work_summary(period);
CREATE INDEX idx_monthly_summary_status ON monthly_work_summary(status);
CREATE INDEX idx_eval_record_summary ON performance_evaluation_record(summary_id);
CREATE INDEX idx_eval_record_evaluator ON performance_evaluation_record(evaluator_id);
CREATE INDEX idx_eval_record_project ON performance_evaluation_record(project_id);
CREATE INDEX idx_eval_record_status ON performance_evaluation_record(status);
CREATE INDEX idx_weight_config_effective_date ON evaluation_weight_config(effective_date);
CREATE INDEX idx_qual_level_code ON qualification_level(level_code);
CREATE INDEX idx_qual_level_order ON qualification_level(level_order);
CREATE INDEX idx_qual_level_role_type ON qualification_level(role_type);
CREATE INDEX idx_comp_model_position ON position_competency_model(position_type, position_subtype);
CREATE INDEX idx_comp_model_level ON position_competency_model(level_id);
CREATE INDEX idx_comp_model_active ON position_competency_model(is_active);
CREATE INDEX idx_emp_qual_employee ON employee_qualification(employee_id);
CREATE INDEX idx_emp_qual_level ON employee_qualification(current_level_id);
CREATE INDEX idx_emp_qual_status ON employee_qualification(status);
CREATE INDEX idx_emp_qual_position ON employee_qualification(position_type);
CREATE INDEX idx_assess_employee ON qualification_assessment(employee_id);
CREATE INDEX idx_assess_qualification ON qualification_assessment(qualification_id);
CREATE INDEX idx_assess_period ON qualification_assessment(assessment_period);
CREATE INDEX idx_assess_type ON qualification_assessment(assessment_type);
CREATE INDEX idx_eval_record_qual_level ON performance_evaluation_record(qualification_level_id);
CREATE INDEX idx_cpq_rule_set_status ON cpq_rule_sets(status);
CREATE INDEX idx_cpq_rule_set_default ON cpq_rule_sets(is_default);
CREATE INDEX idx_quote_template_status ON quote_templates(status);
CREATE INDEX idx_quote_template_scope ON quote_templates(visibility_scope);
CREATE UNIQUE INDEX idx_quote_template_version_unique ON quote_template_versions(template_id, version_no);
CREATE INDEX idx_quote_template_version_status ON quote_template_versions(status);
CREATE INDEX idx_contract_template_status ON contract_templates(status);
CREATE INDEX idx_contract_template_scope ON contract_templates(visibility_scope);
CREATE UNIQUE INDEX idx_contract_template_version_unique ON contract_template_versions(template_id, version_no);
CREATE INDEX idx_contract_template_version_status ON contract_template_versions(status);
CREATE INDEX idx_project_templates_code ON project_templates(template_code);
CREATE INDEX idx_project_templates_type ON project_templates(template_type);
CREATE INDEX idx_project_templates_active ON project_templates(is_active);
CREATE INDEX idx_alert_subscriptions_user ON alert_subscriptions(user_id);
CREATE INDEX idx_alert_subscriptions_type ON alert_subscriptions(alert_type);
CREATE INDEX idx_alert_subscriptions_project ON alert_subscriptions(project_id);
CREATE INDEX idx_alert_subscriptions_active ON alert_subscriptions(is_active);
CREATE INDEX idx_assembly_stage_order ON mes_assembly_stage(stage_order);
CREATE INDEX idx_assembly_stage_active ON mes_assembly_stage(is_active);
CREATE INDEX idx_assembly_template_type ON mes_assembly_template(equipment_type);
CREATE INDEX idx_assembly_template_active ON mes_assembly_template(is_active);
CREATE INDEX idx_category_stage_category ON mes_category_stage_mapping(category_id);
CREATE INDEX idx_category_stage_stage ON mes_category_stage_mapping(stage_code);
CREATE INDEX idx_category_stage_active ON mes_category_stage_mapping(is_active);
CREATE INDEX idx_bom_assembly_bom ON bom_item_assembly_attrs(bom_id);
CREATE INDEX idx_bom_assembly_stage ON bom_item_assembly_attrs(assembly_stage);
CREATE INDEX idx_bom_assembly_blocking ON bom_item_assembly_attrs(is_blocking);
CREATE INDEX idx_bom_assembly_importance ON bom_item_assembly_attrs(importance_level);
CREATE INDEX idx_readiness_no ON mes_material_readiness(readiness_no);
CREATE INDEX idx_readiness_project ON mes_material_readiness(project_id);
CREATE INDEX idx_readiness_machine ON mes_material_readiness(machine_id);
CREATE INDEX idx_readiness_bom ON mes_material_readiness(bom_id);
CREATE INDEX idx_readiness_status ON mes_material_readiness(status);
CREATE INDEX idx_readiness_time ON mes_material_readiness(analysis_time);
CREATE INDEX idx_readiness_can_start ON mes_material_readiness(can_start);
CREATE INDEX idx_shortage_detail_readiness ON mes_shortage_detail(readiness_id);
CREATE INDEX idx_shortage_detail_material ON mes_shortage_detail(material_code);
CREATE INDEX idx_shortage_detail_stage ON mes_shortage_detail(assembly_stage);
CREATE INDEX idx_shortage_detail_blocking ON mes_shortage_detail(is_blocking);
CREATE INDEX idx_shortage_detail_status ON mes_shortage_detail(shortage_status);
CREATE INDEX idx_shortage_detail_alert ON mes_shortage_detail(alert_level);
CREATE INDEX idx_alert_rule_level ON mes_shortage_alert_rule(alert_level);
CREATE INDEX idx_alert_rule_active ON mes_shortage_alert_rule(is_active);
CREATE INDEX idx_alert_rule_priority ON mes_shortage_alert_rule(priority);
CREATE INDEX idx_suggestion_no ON mes_scheduling_suggestion(suggestion_no);
CREATE INDEX idx_suggestion_project ON mes_scheduling_suggestion(project_id);
CREATE INDEX idx_suggestion_machine ON mes_scheduling_suggestion(machine_id);
CREATE INDEX idx_suggestion_status ON mes_scheduling_suggestion(status);
CREATE INDEX idx_suggestion_priority ON mes_scheduling_suggestion(priority_score DESC);
CREATE INDEX idx_suggestion_type ON mes_scheduling_suggestion(suggestion_type);
CREATE INDEX idx_bonus_sheet_code ON bonus_allocation_sheets(sheet_code);
CREATE INDEX idx_bonus_sheet_status ON bonus_allocation_sheets(status);
CREATE INDEX idx_bonus_sheet_project ON bonus_allocation_sheets(project_id);
CREATE INDEX idx_bonus_sheet_period ON bonus_allocation_sheets(period_id);
CREATE INDEX idx_bidding_no ON bidding_projects(bidding_no);
CREATE INDEX idx_customer ON bidding_projects(customer_id);
CREATE INDEX idx_deadline ON bidding_projects(deadline_date);
CREATE INDEX idx_result ON bidding_projects(bid_result);
CREATE INDEX idx_bidding_project ON bidding_documents(bidding_project_id);
CREATE INDEX idx_document_type ON bidding_documents(document_type);
CREATE INDEX idx_contract ON contract_reviews(contract_id);
CREATE INDEX idx_review_status ON contract_reviews(review_status);
CREATE INDEX idx_contract_seal ON contract_seal_records(contract_id);
CREATE INDEX idx_seal_status ON contract_seal_records(seal_status);
CREATE INDEX idx_contract_reminder ON payment_reminders(contract_id);
CREATE INDEX idx_project_reminder ON payment_reminders(project_id);
CREATE INDEX idx_reminder_date ON payment_reminders(reminder_date);
CREATE INDEX idx_archive_no ON document_archives(archive_no);
CREATE INDEX idx_document_type_archive ON document_archives(document_type);
CREATE INDEX idx_related ON document_archives(related_type, related_id);
CREATE INDEX idx_order_no ON sales_orders(order_no);
CREATE INDEX idx_contract_order ON sales_orders(contract_id);
CREATE INDEX idx_customer_order ON sales_orders(customer_id);
CREATE INDEX idx_project_order ON sales_orders(project_id);
CREATE INDEX idx_status_order ON sales_orders(order_status);
CREATE INDEX idx_sales_order_item ON sales_order_items(sales_order_id);
CREATE INDEX idx_delivery_no ON delivery_orders(delivery_no);
CREATE INDEX idx_order_delivery ON delivery_orders(order_id);
CREATE INDEX idx_customer_delivery ON delivery_orders(customer_id);
CREATE INDEX idx_status_delivery ON delivery_orders(delivery_status);
CREATE INDEX idx_return_status ON delivery_orders(return_status);
CREATE INDEX idx_acceptance_order_tracking ON acceptance_tracking(acceptance_order_id);
CREATE INDEX idx_project_tracking ON acceptance_tracking(project_id);
CREATE INDEX idx_customer_tracking ON acceptance_tracking(customer_id);
CREATE INDEX idx_tracking_status ON acceptance_tracking(tracking_status);
CREATE INDEX idx_condition_status ON acceptance_tracking(condition_check_status);
CREATE INDEX idx_tracking_record ON acceptance_tracking_records(tracking_id);
CREATE INDEX idx_record_type ON acceptance_tracking_records(record_type);
CREATE INDEX idx_record_date ON acceptance_tracking_records(record_date);
CREATE INDEX idx_reconciliation_no ON reconciliations(reconciliation_no);
CREATE INDEX idx_customer_reconciliation ON reconciliations(customer_id);
CREATE INDEX idx_period ON reconciliations(period_start, period_end);
CREATE INDEX idx_status_reconciliation ON reconciliations(status);
CREATE INDEX idx_culture_wall_type ON culture_wall_content(content_type);
CREATE INDEX idx_culture_wall_published ON culture_wall_content(is_published, publish_date);
CREATE INDEX idx_culture_wall_expire ON culture_wall_content(expire_date);
CREATE INDEX idx_personal_goal_user ON personal_goal(user_id);
CREATE INDEX idx_personal_goal_type_period ON personal_goal(goal_type, period);
CREATE INDEX idx_personal_goal_status ON personal_goal(status);
CREATE INDEX idx_read_record_content ON culture_wall_read_record(content_id);
CREATE INDEX idx_read_record_user ON culture_wall_read_record(user_id);
CREATE INDEX idx_install_dispatch_project ON installation_dispatch_orders(project_id);
CREATE INDEX idx_install_dispatch_machine ON installation_dispatch_orders(machine_id);
CREATE INDEX idx_install_dispatch_customer ON installation_dispatch_orders(customer_id);
CREATE INDEX idx_install_dispatch_status ON installation_dispatch_orders(status);
CREATE INDEX idx_install_dispatch_assigned ON installation_dispatch_orders(assigned_to_id);
CREATE INDEX idx_install_dispatch_date ON installation_dispatch_orders(scheduled_date);
CREATE INDEX idx_rhythm_config_level_cycle ON management_rhythm_config(rhythm_level, cycle_type);
CREATE INDEX idx_strategic_meeting_level ON strategic_meeting(rhythm_level);
CREATE INDEX idx_strategic_meeting_cycle ON strategic_meeting(cycle_type);
CREATE INDEX idx_strategic_meeting_date ON strategic_meeting(meeting_date);
CREATE INDEX idx_strategic_meeting_project ON strategic_meeting(project_id);
CREATE INDEX idx_action_item_meeting ON meeting_action_item(meeting_id);
CREATE INDEX idx_action_item_owner ON meeting_action_item(owner_id);
CREATE INDEX idx_action_item_status ON meeting_action_item(status);
CREATE INDEX idx_action_item_due_date ON meeting_action_item(due_date);
CREATE INDEX idx_dashboard_snapshot_level_cycle ON rhythm_dashboard_snapshot(rhythm_level, cycle_type);
CREATE INDEX idx_dashboard_snapshot_date ON rhythm_dashboard_snapshot(snapshot_date);
CREATE INDEX idx_project_role_types_category ON project_role_types(role_category);
CREATE INDEX idx_project_role_types_active ON project_role_types(is_active);
CREATE INDEX idx_project_role_configs_project ON project_role_configs(project_id);
CREATE INDEX idx_project_role_configs_role ON project_role_configs(role_type_id);
CREATE INDEX idx_project_members_role_type ON project_members(role_type_id);
CREATE INDEX idx_project_members_is_lead ON project_members(is_lead);
CREATE INDEX idx_project_members_machine ON project_members(machine_id);
CREATE INDEX idx_project_members_lead ON project_members(lead_member_id);
CREATE UNIQUE INDEX idx_project_template_version_unique ON project_template_versions(template_id, version_no);
CREATE INDEX idx_project_template_version_status ON project_template_versions(status);
CREATE INDEX idx_project_template_version_template ON project_template_versions(template_id);
CREATE INDEX idx_project_template_current_version ON project_templates(current_version_id);
CREATE INDEX idx_ts_rd_project ON timesheet(rd_project_id);
CREATE INDEX idx_project_documents_rd_project ON project_documents(rd_project_id);
CREATE INDEX idx_hr_tag_dict_type ON hr_tag_dict(tag_type);
CREATE INDEX idx_hr_tag_dict_parent ON hr_tag_dict(parent_id);
CREATE INDEX idx_hr_tag_dict_active ON hr_tag_dict(is_active);
CREATE INDEX idx_hr_eval_employee ON hr_employee_tag_evaluation(employee_id);
CREATE INDEX idx_hr_eval_tag ON hr_employee_tag_evaluation(tag_id);
CREATE INDEX idx_hr_eval_evaluator ON hr_employee_tag_evaluation(evaluator_id);
CREATE INDEX idx_hr_eval_date ON hr_employee_tag_evaluation(evaluate_date);
CREATE INDEX idx_hr_eval_valid ON hr_employee_tag_evaluation(is_valid);
CREATE INDEX idx_hr_profile_employee ON hr_employee_profile(employee_id);
CREATE INDEX idx_hr_profile_workload ON hr_employee_profile(current_workload_pct);
CREATE INDEX idx_hr_profile_quality ON hr_employee_profile(quality_score);
CREATE INDEX idx_hr_perf_employee ON hr_project_performance(employee_id);
CREATE INDEX idx_hr_perf_project ON hr_project_performance(project_id);
CREATE INDEX idx_hr_perf_role ON hr_project_performance(role_code);
CREATE INDEX idx_hr_perf_contribution ON hr_project_performance(contribution_level);
CREATE UNIQUE INDEX idx_hr_perf_emp_proj ON hr_project_performance(employee_id, project_id);
CREATE INDEX idx_staffing_project ON mes_project_staffing_need(project_id);
CREATE INDEX idx_staffing_role ON mes_project_staffing_need(role_code);
CREATE INDEX idx_staffing_priority ON mes_project_staffing_need(priority);
CREATE INDEX idx_staffing_status ON mes_project_staffing_need(status);
CREATE INDEX idx_staffing_requester ON mes_project_staffing_need(requester_id);
CREATE INDEX idx_matching_request ON hr_ai_matching_log(request_id);
CREATE INDEX idx_matching_project ON hr_ai_matching_log(project_id);
CREATE INDEX idx_matching_need ON hr_ai_matching_log(staffing_need_id);
CREATE INDEX idx_matching_candidate ON hr_ai_matching_log(candidate_employee_id);
CREATE INDEX idx_matching_accepted ON hr_ai_matching_log(is_accepted);
CREATE INDEX idx_matching_time ON hr_ai_matching_log(matching_time);
CREATE INDEX idx_report_config_type ON meeting_report_config(report_type);
CREATE INDEX idx_report_config_default ON meeting_report_config(is_default);
CREATE INDEX idx_metric_code ON report_metric_definition(metric_code);
CREATE INDEX idx_metric_category ON report_metric_definition(category);
CREATE INDEX idx_metric_source ON report_metric_definition(data_source);
CREATE INDEX idx_meeting_report_type ON meeting_report(report_type);
CREATE INDEX idx_meeting_report_period ON meeting_report(period_year, period_month);
CREATE INDEX idx_meeting_report_level ON meeting_report(rhythm_level);
CREATE INDEX idx_meeting_report_date ON meeting_report(period_start, period_end);
CREATE INDEX idx_scheduler_task_id ON scheduler_task_configs(task_id);
CREATE INDEX idx_scheduler_enabled ON scheduler_task_configs(is_enabled);
CREATE INDEX idx_scheduler_category ON scheduler_task_configs(category);
CREATE INDEX idx_position_role_keyword ON position_role_mapping(position_keyword);
CREATE INDEX idx_position_role_code ON position_role_mapping(role_code);
CREATE INDEX idx_work_log_user ON work_logs(user_id);
CREATE INDEX idx_work_log_date ON work_logs(work_date);
CREATE INDEX idx_work_log_status ON work_logs(status);
CREATE INDEX idx_work_log_user_date ON work_logs(user_id, work_date);
CREATE UNIQUE INDEX uq_work_log_user_date ON work_logs(user_id, work_date);
CREATE INDEX idx_work_log_config_user ON work_log_configs(user_id);
CREATE INDEX idx_work_log_config_dept ON work_log_configs(department_id);
CREATE INDEX idx_work_log_config_active ON work_log_configs(is_active);
CREATE INDEX idx_work_log_mention_log ON work_log_mentions(work_log_id);
CREATE INDEX idx_work_log_mention_type ON work_log_mentions(mention_type);
CREATE INDEX idx_work_log_mention_id ON work_log_mentions(mention_id);
CREATE INDEX idx_work_log_mention_type_id ON work_log_mentions(mention_type, mention_id);
CREATE INDEX idx_advantage_products_category ON advantage_products(category_id);
CREATE INDEX idx_advantage_products_code ON advantage_products(product_code);
CREATE INDEX idx_advantage_products_series ON advantage_products(series_code);
CREATE INDEX idx_advantage_product_categories_code ON advantage_product_categories(code);
CREATE INDEX idx_projects_source_lead ON projects(source_lead_id);
CREATE INDEX idx_projects_outcome ON projects(outcome);
CREATE INDEX idx_projects_salesperson ON projects(salesperson_id);
CREATE INDEX idx_leads_advantage_product ON leads(is_advantage_product);
CREATE INDEX idx_leads_product_match_type ON leads(product_match_type);
CREATE INDEX idx_perf_result_job_type ON performance_result(job_type);
CREATE INDEX idx_perf_result_job_level ON performance_result(job_level);
CREATE INDEX idx_engineer_profile_job_type ON engineer_profile(job_type);
CREATE INDEX idx_engineer_profile_job_level ON engineer_profile(job_level);
CREATE INDEX idx_engineer_profile_user ON engineer_profile(user_id);
CREATE UNIQUE INDEX idx_dimension_config_unique ON engineer_dimension_config(job_type, job_level, effective_date);
CREATE INDEX idx_collab_rating_period ON collaboration_rating(period_id);
CREATE INDEX idx_collab_rating_rater ON collaboration_rating(rater_id);
CREATE INDEX idx_collab_rating_ratee ON collaboration_rating(ratee_id);
CREATE UNIQUE INDEX idx_collab_rating_unique ON collaboration_rating(period_id, rater_id, ratee_id);
CREATE INDEX idx_knowledge_contrib_user ON knowledge_contribution(contributor_id);
CREATE INDEX idx_knowledge_contrib_type ON knowledge_contribution(contribution_type);
CREATE INDEX idx_knowledge_contrib_job_type ON knowledge_contribution(job_type);
CREATE INDEX idx_knowledge_contrib_status ON knowledge_contribution(status);
CREATE INDEX idx_knowledge_reuse_contrib ON knowledge_reuse_log(contribution_id);
CREATE INDEX idx_knowledge_reuse_user ON knowledge_reuse_log(user_id);
CREATE INDEX idx_design_review_project ON design_review(project_id);
CREATE INDEX idx_design_review_designer ON design_review(designer_id);
CREATE INDEX idx_design_review_date ON design_review(review_date);
CREATE INDEX idx_design_review_result ON design_review(result);
CREATE INDEX idx_mech_debug_project ON mechanical_debug_issue(project_id);
CREATE INDEX idx_mech_debug_responsible ON mechanical_debug_issue(responsible_id);
CREATE INDEX idx_mech_debug_severity ON mechanical_debug_issue(severity);
CREATE INDEX idx_mech_debug_status ON mechanical_debug_issue(status);
CREATE INDEX idx_design_reuse_project ON design_reuse_record(project_id);
CREATE INDEX idx_design_reuse_designer ON design_reuse_record(designer_id);
CREATE INDEX idx_test_bug_project ON test_bug_record(project_id);
CREATE INDEX idx_test_bug_assignee ON test_bug_record(assignee_id);
CREATE INDEX idx_test_bug_severity ON test_bug_record(severity);
CREATE INDEX idx_test_bug_status ON test_bug_record(status);
CREATE INDEX idx_test_bug_stage ON test_bug_record(found_stage);
CREATE INDEX idx_code_review_project ON code_review_record(project_id);
CREATE INDEX idx_code_review_author ON code_review_record(author_id);
CREATE INDEX idx_code_review_reviewer ON code_review_record(reviewer_id);
CREATE INDEX idx_code_module_contributor ON code_module(contributor_id);
CREATE INDEX idx_code_module_category ON code_module(category);
CREATE INDEX idx_code_module_language ON code_module(language);
CREATE INDEX idx_elec_drawing_project ON electrical_drawing_version(project_id);
CREATE INDEX idx_elec_drawing_designer ON electrical_drawing_version(designer_id);
CREATE INDEX idx_elec_drawing_type ON electrical_drawing_version(drawing_type);
CREATE INDEX idx_plc_program_project ON plc_program_version(project_id);
CREATE INDEX idx_plc_program_programmer ON plc_program_version(programmer_id);
CREATE INDEX idx_plc_program_brand ON plc_program_version(plc_brand);
CREATE INDEX idx_plc_module_contributor ON plc_module_library(contributor_id);
CREATE INDEX idx_plc_module_category ON plc_module_library(category);
CREATE INDEX idx_plc_module_brand ON plc_module_library(plc_brand);
CREATE INDEX idx_comp_selection_project ON component_selection(project_id);
CREATE INDEX idx_comp_selection_engineer ON component_selection(engineer_id);
CREATE INDEX idx_comp_selection_type ON component_selection(component_type);
CREATE INDEX idx_elec_fault_project ON electrical_fault_record(project_id);
CREATE INDEX idx_elec_fault_responsible ON electrical_fault_record(responsible_id);
CREATE INDEX idx_elec_fault_severity ON electrical_fault_record(severity);
CREATE INDEX idx_elec_fault_status ON electrical_fault_record(status);
CREATE INDEX idx_industry_code ON industries(code);
CREATE INDEX idx_industry_parent ON industries(parent_id);
CREATE INDEX idx_industry_active ON industries(is_active);
CREATE INDEX idx_ind_cat_mapping_industry ON industry_category_mappings(industry_id);
CREATE INDEX idx_ind_cat_mapping_category ON industry_category_mappings(category_id);
CREATE INDEX idx_ind_cat_mapping_primary ON industry_category_mappings(is_primary);
CREATE INDEX idx_new_product_lead ON new_product_requests(lead_id);
CREATE INDEX idx_new_product_status ON new_product_requests(review_status);
CREATE INDEX idx_new_product_industry ON new_product_requests(industry_id);
CREATE INDEX idx_presale_expense_project ON presale_expenses(project_id);
CREATE INDEX idx_presale_expense_lead ON presale_expenses(lead_id);
CREATE INDEX idx_presale_expense_opportunity ON presale_expenses(opportunity_id);
CREATE INDEX idx_presale_expense_type ON presale_expenses(expense_type);
CREATE INDEX idx_presale_expense_category ON presale_expenses(expense_category);
CREATE INDEX idx_presale_expense_date ON presale_expenses(expense_date);
CREATE INDEX idx_presale_expense_user ON presale_expenses(user_id);
CREATE INDEX idx_presale_expense_salesperson ON presale_expenses(salesperson_id);
CREATE INDEX idx_presale_expense_department ON presale_expenses(department_id);
CREATE INDEX idx_leads_priority_score ON leads(priority_score);
CREATE INDEX idx_leads_is_key ON leads(is_key_lead);
CREATE INDEX idx_leads_priority_level ON leads(priority_level);
CREATE INDEX idx_opportunities_priority_score ON opportunities(priority_score);
CREATE INDEX idx_opportunities_is_key ON opportunities(is_key_opportunity);
CREATE INDEX idx_opportunities_priority_level ON opportunities(priority_level);
CREATE INDEX idx_credit_trans_user ON solution_credit_transactions(user_id);
CREATE INDEX idx_credit_trans_type ON solution_credit_transactions(transaction_type);
CREATE INDEX idx_credit_trans_created ON solution_credit_transactions(created_at);
CREATE INDEX idx_credit_trans_operator ON solution_credit_transactions(operator_id);
CREATE INDEX idx_approval_workflow_type ON approval_workflows(workflow_type);
CREATE INDEX idx_approval_workflow_active ON approval_workflows(is_active);
CREATE INDEX idx_approval_workflow_step_workflow ON approval_workflow_steps(workflow_id);
CREATE INDEX idx_approval_workflow_step_order ON approval_workflow_steps(workflow_id, step_order);
CREATE INDEX idx_approval_record_entity ON approval_records(entity_type, entity_id);
CREATE INDEX idx_approval_record_workflow ON approval_records(workflow_id);
CREATE INDEX idx_approval_record_status ON approval_records(status);
CREATE INDEX idx_approval_record_initiator ON approval_records(initiator_id);
CREATE INDEX idx_approval_history_record ON approval_history(approval_record_id);
CREATE INDEX idx_approval_history_step ON approval_history(approval_record_id, step_order);
CREATE INDEX idx_approval_history_approver ON approval_history(approver_id);
CREATE INDEX idx_culture_wall_config_enabled ON culture_wall_config(is_enabled);
CREATE INDEX idx_culture_wall_config_default ON culture_wall_config(is_default);
CREATE INDEX idx_bom_impact_ecn ON ecn_bom_impacts(ecn_id);
CREATE INDEX idx_bom_impact_bom ON ecn_bom_impacts(bom_version_id);
CREATE INDEX idx_bom_impact_machine ON ecn_bom_impacts(machine_id);
CREATE INDEX idx_resp_ecn ON ecn_responsibilities(ecn_id);
CREATE INDEX idx_resp_dept ON ecn_responsibilities(dept);
CREATE INDEX idx_solution_template_type ON ecn_solution_templates(ecn_type);
CREATE INDEX idx_solution_template_category ON ecn_solution_templates(template_category);
CREATE INDEX idx_solution_template_active ON ecn_solution_templates(is_active);
CREATE INDEX idx_perf_result_adjusted ON performance_result(is_adjusted);
CREATE INDEX idx_adj_history_result ON performance_adjustment_history(result_id);
CREATE INDEX idx_adj_history_adjuster ON performance_adjustment_history(adjusted_by);
CREATE INDEX idx_adj_history_time ON performance_adjustment_history(adjusted_at);
CREATE INDEX idx_financial_cost_project ON financial_project_costs(project_id);
CREATE INDEX idx_financial_cost_type ON financial_project_costs(cost_type);
CREATE INDEX idx_financial_cost_category ON financial_project_costs(cost_category);
CREATE INDEX idx_financial_cost_date ON financial_project_costs(cost_date);
CREATE INDEX idx_financial_cost_month ON financial_project_costs(cost_month);
CREATE INDEX idx_financial_cost_upload_batch ON financial_project_costs(upload_batch_no);
CREATE INDEX idx_org_unit_type ON organization_units(unit_type);
CREATE INDEX idx_org_parent_id ON organization_units(parent_id);
CREATE INDEX idx_org_path ON organization_units(path);
CREATE INDEX idx_org_active ON organization_units(is_active);
CREATE INDEX idx_position_category ON positions(position_category);
CREATE INDEX idx_position_org ON positions(org_unit_id);
CREATE INDEX idx_position_active ON positions(is_active);
CREATE INDEX idx_level_rank ON job_levels(level_rank);
CREATE INDEX idx_level_category ON job_levels(level_category);
CREATE INDEX idx_eoa_employee ON employee_org_assignments(employee_id);
CREATE INDEX idx_eoa_org_unit ON employee_org_assignments(org_unit_id);
CREATE INDEX idx_eoa_position ON employee_org_assignments(position_id);
CREATE INDEX idx_eoa_primary ON employee_org_assignments(is_primary);
CREATE INDEX idx_eoa_active ON employee_org_assignments(is_active);
CREATE UNIQUE INDEX uk_eoa_emp_org_primary ON employee_org_assignments(employee_id, org_unit_id, is_primary);
CREATE UNIQUE INDEX uk_position_role ON position_roles(position_id, role_id);
CREATE INDEX idx_pr_position ON position_roles(position_id);
CREATE INDEX idx_pr_role ON position_roles(role_id);
CREATE INDEX idx_dsr_scope_type ON data_scope_rules(scope_type);
CREATE INDEX idx_dsr_active ON data_scope_rules(is_active);
CREATE UNIQUE INDEX uk_role_resource ON role_data_scopes(role_id, resource_type);
CREATE INDEX idx_rds_role ON role_data_scopes(role_id);
CREATE INDEX idx_rds_resource ON role_data_scopes(resource_type);
CREATE INDEX idx_pg_parent ON permission_groups(parent_id);
CREATE INDEX idx_mp_parent ON menu_permissions(parent_id);
CREATE INDEX idx_mp_type ON menu_permissions(menu_type);
CREATE INDEX idx_mp_visible ON menu_permissions(is_visible);
CREATE INDEX idx_mp_active ON menu_permissions(is_active);
CREATE UNIQUE INDEX uk_role_menu ON role_menus(role_id, menu_id);
CREATE INDEX idx_rm_role ON role_menus(role_id);
CREATE INDEX idx_rm_menu ON role_menus(menu_id);
CREATE INDEX idx_reminder_type ON material_cost_update_reminders(reminder_type);
CREATE INDEX idx_next_reminder_date ON material_cost_update_reminders(next_reminder_date);
CREATE INDEX idx_is_enabled ON material_cost_update_reminders(is_enabled);
CREATE INDEX idx_leads_health_status ON leads(health_status);
CREATE INDEX idx_leads_break_risk ON leads(break_risk_level);
CREATE INDEX idx_opportunities_health_status ON opportunities(health_status);
CREATE INDEX idx_opportunities_break_risk ON opportunities(break_risk_level);
CREATE INDEX idx_quotes_health_status ON quotes(health_status);
CREATE INDEX idx_quotes_break_risk ON quotes(break_risk_level);
CREATE INDEX idx_contracts_health_status ON contracts(health_status);
CREATE INDEX idx_contracts_break_risk ON contracts(break_risk_level);
CREATE INDEX idx_pipeline_type ON pipeline_break_records(pipeline_type, break_stage);
CREATE INDEX idx_break_date ON pipeline_break_records(break_date);
CREATE INDEX idx_responsible ON pipeline_break_records(responsible_person_id);
CREATE INDEX idx_pipeline ON pipeline_health_snapshots(pipeline_type, pipeline_id);
CREATE INDEX idx_person ON accountability_records(responsible_person_id);
CREATE INDEX idx_department ON accountability_records(responsible_department);
CREATE INDEX idx_issue_type ON accountability_records(issue_type);
CREATE INDEX idx_material_code ON purchase_material_costs(material_code);
CREATE INDEX idx_material_name ON purchase_material_costs(material_name);
CREATE INDEX idx_material_type ON purchase_material_costs(material_type);
CREATE INDEX idx_is_standard ON purchase_material_costs(is_standard_part);
CREATE INDEX idx_is_active ON purchase_material_costs(is_active);
CREATE INDEX idx_match_priority ON purchase_material_costs(match_priority);
CREATE INDEX idx_template_type ON quote_cost_templates(template_type);
CREATE INDEX idx_equipment_type ON quote_cost_templates(equipment_type);
CREATE INDEX idx_quote_id ON quote_cost_approvals(quote_id);
CREATE INDEX idx_approval_status ON quote_cost_approvals(approval_status);
CREATE INDEX idx_created_at ON quote_cost_histories(created_at);
CREATE INDEX idx_tech_review_no ON technical_reviews(review_no);
CREATE INDEX idx_tech_review_project ON technical_reviews(project_id);
CREATE INDEX idx_tech_review_type ON technical_reviews(review_type);
CREATE INDEX idx_tech_review_status ON technical_reviews(status);
CREATE INDEX idx_tech_review_scheduled_date ON technical_reviews(scheduled_date);
CREATE INDEX idx_review_mat_participant_review ON review_participants(review_id);
CREATE INDEX idx_review_mat_participant_user ON review_participants(user_id);
CREATE INDEX idx_review_mat_participant_role ON review_participants(role);
CREATE INDEX idx_review_mat_material_review ON review_materials(review_id);
CREATE INDEX idx_review_mat_material_type ON review_materials(material_type);
CREATE INDEX idx_review_mat_checklist_review ON review_checklist_records(review_id);
CREATE INDEX idx_review_mat_checklist_result ON review_checklist_records(result);
CREATE INDEX idx_review_mat_issue_no ON review_issues(issue_no);
CREATE INDEX idx_review_mat_issue_review ON review_issues(review_id);
CREATE INDEX idx_review_mat_issue_level ON review_issues(issue_level);
CREATE INDEX idx_review_mat_issue_status ON review_issues(status);
CREATE INDEX idx_review_mat_issue_assignee ON review_issues(assignee_id);
CREATE INDEX idx_review_mat_issue_deadline ON review_issues(deadline);
CREATE INDEX idx_assessment_source ON technical_assessments(source_type, source_id);
CREATE INDEX idx_assessment_status ON technical_assessments(status);
CREATE INDEX idx_assessment_evaluator ON technical_assessments(evaluator_id);
CREATE INDEX idx_assessment_decision ON technical_assessments(decision);
CREATE INDEX idx_scoring_rule_active ON scoring_rules(is_active);
CREATE INDEX idx_scoring_rule_version ON scoring_rules(version);
CREATE INDEX idx_failure_case_industry ON failure_cases(industry);
CREATE INDEX idx_failure_case_code ON failure_cases(case_code);
CREATE INDEX idx_requirement_detail_lead ON lead_requirement_details(lead_id);
CREATE INDEX idx_requirement_detail_frozen ON lead_requirement_details(is_frozen);
CREATE INDEX idx_requirement_freeze_source ON requirement_freezes(source_type, source_id);
CREATE INDEX idx_requirement_freeze_type ON requirement_freezes(freeze_type);
CREATE INDEX idx_requirement_freeze_time ON requirement_freezes(freeze_time);
CREATE INDEX idx_open_item_source ON open_items(source_type, source_id);
CREATE INDEX idx_open_item_status ON open_items(status);
CREATE INDEX idx_open_item_type ON open_items(item_type);
CREATE INDEX idx_open_item_blocks ON open_items(blocks_quotation);
CREATE INDEX idx_open_item_due_date ON open_items(due_date);
CREATE INDEX idx_ai_clarification_source ON ai_clarifications(source_type, source_id);
CREATE INDEX idx_ai_clarification_round ON ai_clarifications(round);
CREATE INDEX idx_lead_assessment ON leads(assessment_id);
CREATE INDEX idx_lead_assignee ON leads(assignee_id);
CREATE INDEX idx_opportunity_assessment ON opportunities(assessment_id);
CREATE INDEX idx_bonus_rule_code ON bonus_rules(rule_code);
CREATE INDEX idx_bonus_rule_type ON bonus_rules(bonus_type);
CREATE INDEX idx_bonus_rule_active ON bonus_rules(is_active);
CREATE INDEX idx_bonus_calc_code ON bonus_calculations(calculation_code);
CREATE INDEX idx_bonus_calc_rule ON bonus_calculations(rule_id);
CREATE INDEX idx_bonus_calc_user ON bonus_calculations(user_id);
CREATE INDEX idx_bonus_calc_project ON bonus_calculations(project_id);
CREATE INDEX idx_bonus_calc_period ON bonus_calculations(period_id);
CREATE INDEX idx_bonus_calc_status ON bonus_calculations(status);
CREATE INDEX idx_bonus_dist_code ON bonus_distributions(distribution_code);
CREATE INDEX idx_bonus_dist_calc ON bonus_distributions(calculation_id);
CREATE INDEX idx_bonus_dist_user ON bonus_distributions(user_id);
CREATE INDEX idx_bonus_dist_status ON bonus_distributions(status);
CREATE INDEX idx_bonus_dist_date ON bonus_distributions(distribution_date);
CREATE INDEX idx_team_bonus_project ON team_bonus_allocations(project_id);
CREATE INDEX idx_team_bonus_period ON team_bonus_allocations(period_id);
CREATE INDEX idx_team_bonus_status ON team_bonus_allocations(status);
CREATE INDEX idx_proj_eval_code ON project_evaluations(evaluation_code);
CREATE INDEX idx_proj_eval_project ON project_evaluations(project_id);
CREATE INDEX idx_proj_eval_date ON project_evaluations(evaluation_date);
CREATE INDEX idx_proj_eval_level ON project_evaluations(evaluation_level);
CREATE INDEX idx_eval_dim_code ON project_evaluation_dimensions(dimension_code);
CREATE INDEX idx_eval_dim_type ON project_evaluation_dimensions(dimension_type);
CREATE INDEX idx_purchase_requests_supplier ON purchase_requests(supplier_id);
CREATE INDEX idx_purchase_requests_source ON purchase_requests(source_type);
CREATE INDEX idx_purchase_orders_source_request ON purchase_orders(source_request_id);
CREATE INDEX `idx_contracts_customer_contract_no` ON `contracts` (`customer_contract_no`);
CREATE INDEX `idx_projects_customer_contract_no` ON `projects` (`customer_contract_no`);
CREATE INDEX `idx_projects_lead` ON `projects` (`lead_id`);
CREATE INDEX idx_investor_code ON investors(investor_code);
CREATE INDEX idx_investor_type ON investors(investor_type);
CREATE INDEX idx_investor_name ON investors(investor_name);
CREATE INDEX idx_funding_round_code ON funding_rounds(round_code);
CREATE INDEX idx_funding_round_type ON funding_rounds(round_type);
CREATE INDEX idx_funding_round_status ON funding_rounds(status);
CREATE INDEX idx_funding_round_order ON funding_rounds(round_order);
CREATE INDEX idx_funding_record_round ON funding_records(funding_round_id);
CREATE INDEX idx_funding_record_investor ON funding_records(investor_id);
CREATE INDEX idx_funding_record_status ON funding_records(status);
CREATE INDEX idx_funding_record_payment ON funding_records(payment_status);
CREATE INDEX idx_equity_round ON equity_structures(funding_round_id);
CREATE INDEX idx_equity_investor ON equity_structures(investor_id);
CREATE INDEX idx_equity_type ON equity_structures(shareholder_type);
CREATE INDEX idx_equity_date ON equity_structures(effective_date);
CREATE INDEX idx_funding_usage_round ON funding_usages(funding_round_id);
CREATE INDEX idx_funding_usage_category ON funding_usages(usage_category);
CREATE INDEX idx_funding_usage_status ON funding_usages(status);
CREATE INDEX idx_issues_service_ticket_id ON issues(service_ticket_id);
CREATE INDEX idx_kit_snapshot_project_date ON mes_kit_rate_snapshot(project_id, snapshot_date);
CREATE INDEX idx_kit_snapshot_machine_date ON mes_kit_rate_snapshot(machine_id, snapshot_date);
CREATE INDEX idx_kit_snapshot_type ON mes_kit_rate_snapshot(snapshot_type);
CREATE INDEX idx_kit_snapshot_date ON mes_kit_rate_snapshot(snapshot_date);
CREATE INDEX idx_kit_snapshot_project_time ON mes_kit_rate_snapshot(project_id, snapshot_time);
CREATE INDEX idx_project_members_commitment ON project_members(commitment_level);
CREATE INDEX idx_project_members_reporting ON project_members(reporting_to_pm);
CREATE INDEX idx_project_member_contrib_project ON project_member_contributions(project_id);
CREATE INDEX idx_project_member_contrib_user ON project_member_contributions(user_id);
CREATE INDEX idx_project_member_contrib_period ON project_member_contributions(period);
CREATE INDEX idx_solution_template_code ON solution_templates(template_code);
CREATE INDEX idx_projects_approval ON projects(approval_status, approval_record_id);
CREATE INDEX idx_projects_opportunity ON projects(opportunity_id);
CREATE INDEX idx_projects_contract ON projects(contract_id);
CREATE INDEX idx_projects_erp_sync ON projects(erp_synced, erp_sync_status);
CREATE INDEX idx_projects_initiation ON projects(initiation_id);
CREATE INDEX idx_projects_category ON projects(project_category);
CREATE INDEX idx_projects_warranty_end ON projects(warranty_end_date);
CREATE INDEX idx_sales_target_scope ON sales_targets(target_scope, user_id, department_id);
CREATE INDEX idx_sales_target_type_period ON sales_targets(target_type, target_period, period_value);
CREATE INDEX idx_sales_target_status ON sales_targets(status);
CREATE INDEX idx_sales_target_user ON sales_targets(user_id);
CREATE INDEX idx_sales_target_department ON sales_targets(department_id);
CREATE INDEX idx_sales_team_code ON sales_teams(team_code);
CREATE INDEX idx_sales_team_type ON sales_teams(team_type);
CREATE INDEX idx_sales_team_department ON sales_teams(department_id);
CREATE INDEX idx_sales_team_leader ON sales_teams(leader_id);
CREATE INDEX idx_sales_team_parent ON sales_teams(parent_team_id);
CREATE INDEX idx_sales_team_active ON sales_teams(is_active);
CREATE INDEX idx_team_member_team ON sales_team_members(team_id);
CREATE INDEX idx_team_member_user ON sales_team_members(user_id);
CREATE INDEX idx_team_member_role ON sales_team_members(role);
CREATE INDEX idx_team_member_primary ON sales_team_members(user_id, is_primary);
CREATE INDEX idx_team_member_active ON sales_team_members(is_active);
CREATE INDEX idx_team_perf_team ON team_performance_snapshots(team_id);
CREATE INDEX idx_team_perf_period ON team_performance_snapshots(period_type, period_value);
CREATE INDEX idx_team_perf_date ON team_performance_snapshots(snapshot_date);
CREATE INDEX idx_team_perf_rank ON team_performance_snapshots(period_type, period_value, rank_overall);
CREATE INDEX idx_team_pk_status ON team_pk_records(status);
CREATE INDEX idx_team_pk_date ON team_pk_records(start_date, end_date);
CREATE INDEX idx_team_pk_winner ON team_pk_records(winner_team_id);
CREATE INDEX idx_sales_target_team ON sales_targets(team_id);
CREATE INDEX idx_stage_definitions_template ON stage_definitions(template_id);
CREATE INDEX idx_node_definitions_stage ON node_definitions(stage_definition_id);
CREATE INDEX idx_project_stage_instances_project ON project_stage_instances(project_id);
CREATE INDEX idx_project_stage_instances_status ON project_stage_instances(status);
CREATE INDEX idx_project_node_instances_project ON project_node_instances(project_id);
CREATE INDEX idx_project_node_instances_stage ON project_node_instances(stage_instance_id);
CREATE INDEX idx_project_node_instances_status ON project_node_instances(status);
CREATE INDEX idx_projects_stage_template ON projects(stage_template_id);
CREATE INDEX idx_strategies_code ON strategies(code);
CREATE INDEX idx_strategies_year ON strategies(year);
CREATE INDEX idx_strategies_status ON strategies(status);
CREATE INDEX idx_strategies_active ON strategies(is_active);
CREATE INDEX idx_csfs_strategy ON csfs(strategy_id);
CREATE INDEX idx_csfs_dimension ON csfs(dimension);
CREATE INDEX idx_csfs_code ON csfs(code);
CREATE INDEX idx_csfs_owner_dept ON csfs(owner_dept_id);
CREATE INDEX idx_csfs_active ON csfs(is_active);
CREATE INDEX idx_kpis_csf ON kpis(csf_id);
CREATE INDEX idx_kpis_code ON kpis(code);
CREATE INDEX idx_kpis_ipooc ON kpis(ipooc_type);
CREATE INDEX idx_kpis_source_type ON kpis(data_source_type);
CREATE INDEX idx_kpis_owner ON kpis(owner_user_id);
CREATE INDEX idx_kpis_active ON kpis(is_active);
CREATE INDEX idx_kpi_history_kpi ON kpi_history(kpi_id);
CREATE INDEX idx_kpi_history_date ON kpi_history(snapshot_date);
CREATE INDEX idx_kpi_history_kpi_date ON kpi_history(kpi_id, snapshot_date);
CREATE INDEX idx_kpi_data_source_kpi ON kpi_data_sources(kpi_id);
CREATE INDEX idx_kpi_data_source_type ON kpi_data_sources(source_type);
CREATE INDEX idx_kpi_data_source_active ON kpi_data_sources(is_active);
CREATE INDEX idx_annual_key_works_csf ON annual_key_works(csf_id);
CREATE INDEX idx_annual_key_works_year ON annual_key_works(year);
CREATE INDEX idx_annual_key_works_code ON annual_key_works(code);
CREATE INDEX idx_annual_key_works_status ON annual_key_works(status);
CREATE INDEX idx_annual_key_works_owner_dept ON annual_key_works(owner_dept_id);
CREATE INDEX idx_annual_key_works_owner ON annual_key_works(owner_user_id);
CREATE INDEX idx_annual_key_works_active ON annual_key_works(is_active);
CREATE INDEX idx_akw_project_links_work ON annual_key_work_project_links(annual_work_id);
CREATE INDEX idx_akw_project_links_project ON annual_key_work_project_links(project_id);
CREATE INDEX idx_dept_objectives_strategy ON department_objectives(strategy_id);
CREATE INDEX idx_dept_objectives_dept ON department_objectives(department_id);
CREATE INDEX idx_dept_objectives_year ON department_objectives(year);
CREATE INDEX idx_dept_objectives_status ON department_objectives(status);
CREATE INDEX idx_personal_kpis_employee ON personal_kpis(employee_id);
CREATE INDEX idx_personal_kpis_year ON personal_kpis(year);
CREATE INDEX idx_personal_kpis_quarter ON personal_kpis(quarter);
CREATE INDEX idx_personal_kpis_source ON personal_kpis(source_type, source_id);
CREATE INDEX idx_personal_kpis_dept_obj ON personal_kpis(department_objective_id);
CREATE INDEX idx_personal_kpis_status ON personal_kpis(status);
CREATE INDEX idx_personal_kpis_active ON personal_kpis(is_active);
CREATE INDEX idx_strategy_reviews_strategy ON strategy_reviews(strategy_id);
CREATE INDEX idx_strategy_reviews_type ON strategy_reviews(review_type);
CREATE INDEX idx_strategy_reviews_date ON strategy_reviews(review_date);
CREATE INDEX idx_strategy_reviews_active ON strategy_reviews(is_active);
CREATE INDEX idx_calendar_events_strategy ON strategy_calendar_events(strategy_id);
CREATE INDEX idx_calendar_events_type ON strategy_calendar_events(event_type);
CREATE INDEX idx_calendar_events_year ON strategy_calendar_events(year);
CREATE INDEX idx_calendar_events_month ON strategy_calendar_events(month);
CREATE INDEX idx_calendar_events_date ON strategy_calendar_events(scheduled_date);
CREATE INDEX idx_calendar_events_status ON strategy_calendar_events(status);
CREATE INDEX idx_calendar_events_active ON strategy_calendar_events(is_active);
CREATE INDEX idx_strategy_comparison_current ON strategy_comparisons(current_strategy_id);
CREATE INDEX idx_strategy_comparison_previous ON strategy_comparisons(previous_strategy_id);
CREATE INDEX idx_strategy_comparison_years ON strategy_comparisons(current_year, previous_year);
CREATE INDEX idx_strategy_comparison_date ON strategy_comparisons(generated_date);
CREATE INDEX idx_strategy_comparison_active ON strategy_comparisons(is_active);
CREATE INDEX idx_pitfall_stage ON pitfalls(stage);
CREATE INDEX idx_pitfall_equipment ON pitfalls(equipment_type);
CREATE INDEX idx_pitfall_problem ON pitfalls(problem_type);
CREATE INDEX idx_pitfall_status ON pitfalls(status);
CREATE INDEX idx_pitfall_project ON pitfalls(source_project_id);
CREATE INDEX idx_pitfall_created_by ON pitfalls(created_by);
CREATE INDEX idx_pitfall_rec_project ON pitfall_recommendations(project_id);
CREATE INDEX idx_pitfall_rec_pitfall ON pitfall_recommendations(pitfall_id);
CREATE INDEX idx_pitfall_learn_user ON pitfall_learning_progress(user_id);
CREATE INDEX idx_pitfall_learn_pitfall ON pitfall_learning_progress(pitfall_id);
CREATE INDEX idx_stage_plan_project ON project_stage_resource_plan(project_id);
CREATE INDEX idx_stage_plan_stage ON project_stage_resource_plan(stage_code);
CREATE INDEX idx_stage_plan_employee ON project_stage_resource_plan(assigned_employee_id);
CREATE INDEX idx_stage_plan_status ON project_stage_resource_plan(assignment_status);
CREATE INDEX idx_stage_plan_dates ON project_stage_resource_plan(planned_start, planned_end);
CREATE INDEX idx_conflict_employee ON resource_conflicts(employee_id);
CREATE INDEX idx_conflict_resolved ON resource_conflicts(is_resolved);
CREATE INDEX idx_conflict_severity ON resource_conflicts(severity);
CREATE INDEX idx_sales_ranking_config_updated_at
    ON sales_ranking_configs (updated_at);
CREATE INDEX idx_rap_role ON role_api_permissions(role_id);
CREATE INDEX idx_rap_perm ON role_api_permissions(permission_id);
CREATE INDEX idx_delegate_user_active ON approval_delegates (user_id, is_active);
CREATE INDEX idx_delegate_user ON approval_delegates (user_id);
CREATE INDEX idx_delegate_delegate ON approval_delegates (delegate_id);
CREATE INDEX idx_delegate_date_range ON approval_delegates (start_date, end_date);
CREATE INDEX idx_delegate_active ON approval_delegates (is_active);
CREATE INDEX idx_approval_template_entity_type ON approval_templates (entity_type);
CREATE INDEX idx_approval_template_active ON approval_templates (is_active);
CREATE INDEX idx_approval_template_code ON approval_templates (template_code);
CREATE INDEX idx_approval_template_published ON approval_templates (is_published);
CREATE INDEX idx_approval_template_category ON approval_templates (category);
CREATE INDEX idx_state_log_entity ON state_transition_logs (entity_type, entity_id);
CREATE INDEX idx_state_log_operator ON state_transition_logs (operator_id);
CREATE INDEX idx_state_log_created ON state_transition_logs (created_at);
CREATE INDEX idx_vendor_level ON vendors (supplier_level);
CREATE INDEX idx_vendor_type ON vendors (vendor_type);
CREATE INDEX idx_vendor_status ON vendors (status);
CREATE INDEX idx_bom_machine ON bom_headers (machine_id);
CREATE INDEX idx_bom_project ON bom_headers (project_id);
CREATE INDEX idx_shortage_project ON material_shortages (project_id);
CREATE INDEX idx_shortage_material ON material_shortages (material_id);
CREATE INDEX idx_shortage_status ON material_shortages (status);
CREATE INDEX idx_shortage_report_no ON shortage_reports (report_no);
CREATE INDEX idx_shortage_report_project ON shortage_reports (project_id);
CREATE INDEX idx_shortage_report_status ON shortage_reports (status);
CREATE INDEX idx_notification_user ON notifications (user_id);
CREATE INDEX idx_notification_type ON notifications (notification_type);
CREATE INDEX idx_notification_read ON notifications (is_read);
CREATE INDEX idx_notification_created ON notifications (created_at);
CREATE INDEX idx_notification_settings_user ON notification_settings (user_id);
CREATE INDEX idx_survey_template_type ON satisfaction_survey_templates (survey_type);
CREATE INDEX idx_survey_template_code ON satisfaction_survey_templates (template_code);
CREATE INDEX idx_service_record_date ON service_records (service_date);
CREATE INDEX idx_service_record_project ON service_records (project_id);
CREATE INDEX idx_service_record_customer ON service_records (customer_id);
CREATE INDEX idx_service_ticket_project ON service_tickets (project_id);
CREATE INDEX idx_service_ticket_customer ON service_tickets (customer_id);
CREATE INDEX idx_service_ticket_status ON service_tickets (status);
CREATE INDEX idx_sla_policy_code ON sla_policies (policy_code);
CREATE INDEX idx_sla_policy_type_urgency ON sla_policies (problem_type, urgency);
CREATE INDEX idx_sla_policy_active ON sla_policies (is_active);
CREATE INDEX idx_hourly_rate_role ON hourly_rate_configs (role_id);
CREATE INDEX idx_hourly_rate_type ON hourly_rate_configs (config_type);
CREATE INDEX idx_hourly_rate_dept ON hourly_rate_configs (dept_id);
CREATE INDEX idx_hourly_rate_user ON hourly_rate_configs (user_id);
CREATE INDEX idx_hourly_rate_active ON hourly_rate_configs (is_active);
CREATE INDEX idx_project_financials_project ON project_financials (project_id);
CREATE INDEX idx_project_erp_project ON project_erp (project_id);
CREATE INDEX idx_project_erp_status ON project_erp (erp_sync_status);
CREATE INDEX idx_project_warranties_project ON project_warranties (project_id);
CREATE INDEX idx_project_warranties_end_date ON project_warranties (warranty_end_date);
CREATE INDEX idx_project_implementations_project ON project_implementations (project_id);
CREATE INDEX idx_project_presales_project ON project_presales (project_id);
CREATE INDEX idx_project_presales_outcome ON project_presales (outcome);
CREATE INDEX ix_node_tasks_node_instance_id ON node_tasks (node_instance_id);
CREATE INDEX idx_budget_status ON project_budgets (status);
CREATE INDEX idx_budget_version ON project_budgets (project_id, version);
CREATE INDEX idx_budget_project ON project_budgets (project_id);
CREATE INDEX idx_allocation_rule_name ON project_cost_allocation_rules (rule_name);
CREATE INDEX idx_allocation_rule_type ON project_cost_allocation_rules (rule_type);
CREATE INDEX idx_contract_amendment_contract ON contract_amendments (contract_id);
CREATE INDEX idx_contract_amendment_status ON contract_amendments (status);
CREATE INDEX idx_contract_amendment_date ON contract_amendments (request_date);
CREATE INDEX idx_lead_follow_up_lead ON lead_follow_ups (lead_id);
CREATE INDEX idx_lead_follow_up_created ON lead_follow_ups (created_at);
CREATE INDEX idx_approval_flow_default ON approval_flow_definitions (template_id, is_default);
CREATE INDEX idx_approval_flow_active ON approval_flow_definitions (is_active);
CREATE INDEX idx_approval_flow_template ON approval_flow_definitions (template_id);
CREATE UNIQUE INDEX idx_template_version_version ON approval_template_versions (template_id, version);
CREATE INDEX idx_template_version_template ON approval_template_versions (template_id);
CREATE INDEX idx_ms_supplier ON material_suppliers (supplier_id);
CREATE INDEX idx_ms_material ON material_suppliers (material_id);
CREATE INDEX idx_arrival_no ON material_arrivals (arrival_no);
CREATE INDEX idx_arrival_status ON material_arrivals (status);
CREATE INDEX idx_arrival_expected_date ON material_arrivals (expected_date);
CREATE INDEX idx_substitution_status ON material_substitutions (status);
CREATE INDEX idx_substitution_no ON material_substitutions (substitution_no);
CREATE INDEX idx_substitution_project ON material_substitutions (project_id);
CREATE INDEX idx_transfer_status ON material_transfers (status);
CREATE INDEX idx_transfer_no ON material_transfers (transfer_no);
CREATE INDEX idx_transfer_from_project ON material_transfers (from_project_id);
CREATE INDEX idx_transfer_to_project ON material_transfers (to_project_id);
CREATE INDEX idx_ticket_projects_project ON service_ticket_projects (project_id);
CREATE INDEX idx_ticket_projects_ticket ON service_ticket_projects (ticket_id);
CREATE INDEX idx_ticket_cc_ticket ON service_ticket_cc_users (ticket_id);
CREATE INDEX idx_ticket_cc_user ON service_ticket_cc_users (user_id);
CREATE INDEX idx_sla_monitor_response_status ON sla_monitors (response_status);
CREATE INDEX idx_sla_monitor_resolve_status ON sla_monitors (resolve_status);
CREATE INDEX idx_sla_monitor_ticket ON sla_monitors (ticket_id);
CREATE INDEX idx_sla_monitor_response_deadline ON sla_monitors (response_deadline);
CREATE INDEX idx_sla_monitor_policy ON sla_monitors (policy_id);
CREATE INDEX idx_sla_monitor_resolve_deadline ON sla_monitors (resolve_deadline);
CREATE INDEX idx_budget_item_category ON project_budget_items (cost_category);
CREATE INDEX idx_budget_item_budget ON project_budget_items (budget_id);
CREATE INDEX idx_approval_node_type ON approval_node_definitions (node_type);
CREATE INDEX idx_approval_node_flow ON approval_node_definitions (flow_id);
CREATE INDEX idx_approval_node_order ON approval_node_definitions (flow_id, node_order);
CREATE INDEX idx_routing_rule_active ON approval_routing_rules (is_active);
CREATE INDEX idx_routing_rule_order ON approval_routing_rules (template_id, rule_order);
CREATE INDEX idx_routing_rule_template ON approval_routing_rules (template_id);
CREATE INDEX idx_follow_up_arrival ON arrival_follow_ups (arrival_id);
CREATE INDEX idx_approval_instance_submitted ON approval_instances (submitted_at);
CREATE INDEX idx_approval_instance_initiator ON approval_instances (initiator_id);
CREATE INDEX idx_approval_instance_template ON approval_instances (template_id);
CREATE INDEX idx_approval_instance_no ON approval_instances (instance_no);
CREATE INDEX idx_approval_instance_current_node ON approval_instances (current_node_id);
CREATE INDEX idx_approval_instance_status ON approval_instances (status);
CREATE INDEX idx_approval_instance_urgency ON approval_instances (urgency);
CREATE INDEX idx_approval_instance_entity ON approval_instances (entity_type, entity_id);
CREATE INDEX idx_comment_instance ON approval_comments (instance_id);
CREATE INDEX idx_comment_user ON approval_comments (user_id);
CREATE INDEX idx_comment_parent ON approval_comments (parent_id);
CREATE INDEX idx_approval_task_assignee ON approval_tasks (assignee_id);
CREATE INDEX idx_approval_task_type ON approval_tasks (task_type);
CREATE INDEX idx_approval_task_status ON approval_tasks (status);
CREATE INDEX idx_approval_task_instance ON approval_tasks (instance_id);
CREATE INDEX idx_approval_task_pending ON approval_tasks (assignee_id, status);
CREATE INDEX idx_approval_task_node ON approval_tasks (node_id);
CREATE INDEX idx_approval_task_due ON approval_tasks (due_at);
CREATE INDEX idx_approval_cc_user ON approval_carbon_copies (cc_user_id);
CREATE INDEX idx_approval_cc_unread ON approval_carbon_copies (cc_user_id, is_read);
CREATE INDEX idx_approval_cc_instance ON approval_carbon_copies (instance_id);
CREATE INDEX idx_countersign_instance ON approval_countersign_results (instance_id);
CREATE INDEX idx_countersign_node ON approval_countersign_results (node_id);
CREATE UNIQUE INDEX idx_countersign_instance_node ON approval_countersign_results (instance_id, node_id);
CREATE INDEX idx_delegate_log_config ON approval_delegate_logs (delegate_config_id);
CREATE INDEX idx_delegate_log_task ON approval_delegate_logs (task_id);
CREATE INDEX idx_delegate_log_original ON approval_delegate_logs (original_user_id);
CREATE INDEX idx_action_log_action ON approval_action_logs (action);
CREATE INDEX idx_action_log_instance ON approval_action_logs (instance_id);
CREATE INDEX idx_action_log_time ON approval_action_logs (action_at);
CREATE INDEX idx_action_log_task ON approval_action_logs (task_id);
CREATE INDEX idx_action_log_instance_time ON approval_action_logs (instance_id, action_at);
CREATE INDEX idx_action_log_operator ON approval_action_logs (operator_id);
CREATE INDEX idx_project_risk_history_project ON project_risk_history(project_id);
CREATE INDEX idx_project_risk_history_triggered_at ON project_risk_history(triggered_at);
CREATE INDEX idx_project_risk_history_level ON project_risk_history(new_risk_level);
CREATE INDEX idx_project_risk_snapshot_project ON project_risk_snapshot(project_id);
CREATE INDEX idx_project_risk_snapshot_date ON project_risk_snapshot(snapshot_date);
CREATE INDEX idx_project_risk_snapshot_level ON project_risk_snapshot(risk_level);
COMMIT;
