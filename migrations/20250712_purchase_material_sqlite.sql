-- ============================================
-- 采购与物料管理模块 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 物料、供应商、BOM、采购单、收货等表
-- ============================================

-- ============================================
-- 1. 物料主数据表
-- ============================================

CREATE TABLE IF NOT EXISTS materials (
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

CREATE INDEX idx_materials_code ON materials(material_code);
CREATE INDEX idx_materials_name ON materials(material_name);
CREATE INDEX idx_materials_category ON materials(category_l1, category_l2);
CREATE INDEX idx_materials_type ON materials(material_type);
CREATE INDEX idx_materials_status ON materials(status);

-- ============================================
-- 2. 供应商表
-- ============================================

CREATE TABLE IF NOT EXISTS suppliers (
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

CREATE INDEX idx_suppliers_code ON suppliers(supplier_code);
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);
CREATE INDEX idx_suppliers_type ON suppliers(supplier_type);
CREATE INDEX idx_suppliers_status ON suppliers(cooperation_status);

-- ============================================
-- 3. 供应商物料报价表
-- ============================================

CREATE TABLE IF NOT EXISTS supplier_quotations (
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

CREATE INDEX idx_supplier_quotations_supplier ON supplier_quotations(supplier_id);
CREATE INDEX idx_supplier_quotations_material ON supplier_quotations(material_id);

-- ============================================
-- 4. BOM版本表
-- ============================================

CREATE TABLE IF NOT EXISTS bom_versions (
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

CREATE INDEX idx_bom_versions_project ON bom_versions(project_id);
CREATE INDEX idx_bom_versions_machine ON bom_versions(machine_id);
CREATE INDEX idx_bom_versions_status ON bom_versions(status);

-- ============================================
-- 5. BOM明细表
-- ============================================

CREATE TABLE IF NOT EXISTS bom_items (
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

CREATE INDEX idx_bom_items_version ON bom_items(bom_version_id);
CREATE INDEX idx_bom_items_material ON bom_items(material_id);
CREATE INDEX idx_bom_items_parent ON bom_items(parent_item_id);
CREATE INDEX idx_bom_items_ready ON bom_items(ready_status);

-- ============================================
-- 6. 采购申请单表
-- ============================================

CREATE TABLE IF NOT EXISTS purchase_requests (
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
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_purchase_requests_no ON purchase_requests(request_no);
CREATE INDEX idx_purchase_requests_project ON purchase_requests(project_id);
CREATE INDEX idx_purchase_requests_status ON purchase_requests(status);

-- ============================================
-- 7. 采购申请明细表
-- ============================================

CREATE TABLE IF NOT EXISTS purchase_request_items (
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

    remark              TEXT,

    FOREIGN KEY (request_id) REFERENCES purchase_requests(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE INDEX idx_pr_items_request ON purchase_request_items(request_id);

-- ============================================
-- 8. 采购订单表
-- ============================================

CREATE TABLE IF NOT EXISTS purchase_orders (
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
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_purchase_orders_no ON purchase_orders(order_no);
CREATE INDEX idx_purchase_orders_project ON purchase_orders(project_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_orders_date ON purchase_orders(order_date);

-- ============================================
-- 9. 采购订单明细表
-- ============================================

CREATE TABLE IF NOT EXISTS purchase_order_items (
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

    remark              TEXT,

    FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (pr_item_id) REFERENCES purchase_request_items(id),
    FOREIGN KEY (bom_item_id) REFERENCES bom_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE INDEX idx_po_items_order ON purchase_order_items(order_id);
CREATE INDEX idx_po_items_material ON purchase_order_items(material_id);

-- ============================================
-- 10. 收货单表
-- ============================================

CREATE TABLE IF NOT EXISTS goods_receipts (
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

CREATE INDEX idx_goods_receipts_no ON goods_receipts(receipt_no);
CREATE INDEX idx_goods_receipts_order ON goods_receipts(order_id);
CREATE INDEX idx_goods_receipts_date ON goods_receipts(receipt_date);

-- ============================================
-- 11. 收货明细表
-- ============================================

CREATE TABLE IF NOT EXISTS goods_receipt_items (
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

    remark              TEXT,

    FOREIGN KEY (receipt_id) REFERENCES goods_receipts(id),
    FOREIGN KEY (po_item_id) REFERENCES purchase_order_items(id),
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE INDEX idx_gr_items_receipt ON goods_receipt_items(receipt_id);

-- ============================================
-- 12. 物料短缺预警表
-- ============================================

CREATE TABLE IF NOT EXISTS shortage_alerts (
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

CREATE INDEX idx_shortage_alerts_project ON shortage_alerts(project_id);
CREATE INDEX idx_shortage_alerts_status ON shortage_alerts(status);
CREATE INDEX idx_shortage_alerts_level ON shortage_alerts(alert_level);

-- ============================================
-- 13. 物料分类表
-- ============================================

CREATE TABLE IF NOT EXISTS material_categories (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code       VARCHAR(50) NOT NULL UNIQUE,          -- 分类编码
    category_name       VARCHAR(100) NOT NULL,                -- 分类名称
    parent_id           INTEGER,                              -- 父分类ID
    level               INTEGER DEFAULT 1,                    -- 层级
    sort_order          INTEGER DEFAULT 0,                    -- 排序

    description         TEXT,
    is_active           BOOLEAN DEFAULT 1,

    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_id) REFERENCES material_categories(id)
);

CREATE INDEX idx_material_categories_parent ON material_categories(parent_id);

-- ============================================
-- 14. 视图定义
-- ============================================

-- BOM齐套率视图
CREATE VIEW IF NOT EXISTS v_bom_ready_rate AS
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

-- 采购订单统计视图
CREATE VIEW IF NOT EXISTS v_po_statistics AS
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

-- ============================================
-- 完成
-- ============================================
