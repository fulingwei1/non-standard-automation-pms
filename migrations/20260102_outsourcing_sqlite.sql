-- ============================================
-- 外协管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-02
-- 说明: 外协商、外协订单、交付跟踪、质检等
-- ============================================

-- ============================================
-- 1. 外协商表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_vendors (
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

CREATE INDEX idx_vendors_code ON outsourcing_vendors(vendor_code);
CREATE INDEX idx_vendors_type ON outsourcing_vendors(vendor_type);
CREATE INDEX idx_vendors_status ON outsourcing_vendors(status);

-- ============================================
-- 2. 外协订单表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_orders (
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

CREATE INDEX idx_os_orders_no ON outsourcing_orders(order_no);
CREATE INDEX idx_os_orders_vendor ON outsourcing_orders(vendor_id);
CREATE INDEX idx_os_orders_project ON outsourcing_orders(project_id);
CREATE INDEX idx_os_orders_status ON outsourcing_orders(status);

-- ============================================
-- 3. 外协订单明细表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_order_items (
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

    remark              TEXT,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE INDEX idx_os_items_order ON outsourcing_order_items(order_id);
CREATE INDEX idx_os_items_material ON outsourcing_order_items(material_id);

-- ============================================
-- 4. 外协交付记录表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_deliveries (
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
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (received_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_os_deliveries_order ON outsourcing_deliveries(order_id);
CREATE INDEX idx_os_deliveries_vendor ON outsourcing_deliveries(vendor_id);
CREATE INDEX idx_os_deliveries_status ON outsourcing_deliveries(status);

-- ============================================
-- 5. 外协交付明细表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_delivery_items (
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

    remark              TEXT,

    FOREIGN KEY (delivery_id) REFERENCES outsourcing_deliveries(id),
    FOREIGN KEY (order_item_id) REFERENCES outsourcing_order_items(id)
);

CREATE INDEX idx_os_delivery_items_delivery ON outsourcing_delivery_items(delivery_id);

-- ============================================
-- 6. 外协质检记录表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_inspections (
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

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (delivery_id) REFERENCES outsourcing_deliveries(id),
    FOREIGN KEY (delivery_item_id) REFERENCES outsourcing_delivery_items(id),
    FOREIGN KEY (inspector_id) REFERENCES users(id)
);

CREATE INDEX idx_os_inspections_delivery ON outsourcing_inspections(delivery_id);
CREATE INDEX idx_os_inspections_result ON outsourcing_inspections(inspect_result);

-- ============================================
-- 7. 外协付款记录表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_payments (
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
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_os_payments_vendor ON outsourcing_payments(vendor_id);
CREATE INDEX idx_os_payments_order ON outsourcing_payments(order_id);
CREATE INDEX idx_os_payments_status ON outsourcing_payments(status);

-- ============================================
-- 8. 外协商评价表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_evaluations (
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
    evaluated_at        DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vendor_id) REFERENCES outsourcing_vendors(id),
    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (evaluator_id) REFERENCES users(id)
);

CREATE INDEX idx_os_evaluations_vendor ON outsourcing_evaluations(vendor_id);
CREATE INDEX idx_os_evaluations_period ON outsourcing_evaluations(eval_period);

-- ============================================
-- 9. 外协进度跟踪表
-- ============================================

CREATE TABLE IF NOT EXISTS outsourcing_progress (
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
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (order_id) REFERENCES outsourcing_orders(id),
    FOREIGN KEY (order_item_id) REFERENCES outsourcing_order_items(id),
    FOREIGN KEY (reported_by) REFERENCES users(id)
);

CREATE INDEX idx_os_progress_order ON outsourcing_progress(order_id);
CREATE INDEX idx_os_progress_date ON outsourcing_progress(report_date);

-- ============================================
-- 10. 视图定义
-- ============================================

-- 外协订单概览视图
CREATE VIEW IF NOT EXISTS v_outsourcing_overview AS
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

-- ============================================
-- 完成
-- ============================================
