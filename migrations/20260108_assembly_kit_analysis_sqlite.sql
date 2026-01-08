-- ============================================
-- 基于装配工艺路径的智能齐套分析系统 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-08
-- 说明: 实现按装配阶段的分层齐套率计算
-- ============================================

-- ============================================
-- 1. 装配阶段定义表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_assembly_stage (
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

CREATE INDEX IF NOT EXISTS idx_assembly_stage_order ON mes_assembly_stage(stage_order);
CREATE INDEX IF NOT EXISTS idx_assembly_stage_active ON mes_assembly_stage(is_active);

-- 初始化6个装配阶段
INSERT OR IGNORE INTO mes_assembly_stage (stage_code, stage_name, stage_order, description, default_duration, color_code, icon) VALUES
('FRAME', '框架装配', 1, '铝型材框架搭建、钣金底座组装、立柱安装', 24, '#3B82F6', 'Box'),
('MECH', '机械模组', 2, '直线模组、气缸、电机、导轨滑块、夹具安装', 40, '#10B981', 'Cog'),
('ELECTRIC', '电气安装', 3, 'PLC、伺服驱动、传感器、HMI、电源安装接线', 32, '#F59E0B', 'Zap'),
('WIRING', '线路整理', 4, '线槽安装、线缆整理、标签粘贴、端子接线', 16, '#EF4444', 'Cable'),
('DEBUG', '调试准备', 5, '工装治具准备、测试产品准备、程序调试', 24, '#8B5CF6', 'Bug'),
('COSMETIC', '外观完善', 6, '铭牌、盖板、安全防护、亚克力板安装', 8, '#6B7280', 'Sparkles');

-- ============================================
-- 2. 装配工艺模板表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_assembly_template (
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

CREATE INDEX IF NOT EXISTS idx_assembly_template_type ON mes_assembly_template(equipment_type);
CREATE INDEX IF NOT EXISTS idx_assembly_template_active ON mes_assembly_template(is_active);

-- 初始化默认模板
INSERT OR IGNORE INTO mes_assembly_template (template_code, template_name, equipment_type, description, is_default, stage_config) VALUES
('TPL_TEST_STD', '测试设备标准模板', 'TEST', 'ICT/FCT/EOL等测试设备的标准装配流程', 1,
'[{"stage":"FRAME","duration":24,"blocking_categories":["铝型材","钣金件","连接件"]},{"stage":"MECH","duration":40,"blocking_categories":["直线模组","气缸","导轨","电机"]},{"stage":"ELECTRIC","duration":32,"blocking_categories":["PLC","伺服","传感器","电源"]},{"stage":"WIRING","duration":16,"blocking_categories":["主线缆"]},{"stage":"DEBUG","duration":24,"blocking_categories":["工装治具"]},{"stage":"COSMETIC","duration":8,"blocking_categories":[]}]'),
('TPL_ASSEMBLY_LINE', '产线设备模板', 'ASSEMBLY', '自动化组装线体的装配流程', 0,
'[{"stage":"FRAME","duration":56,"blocking_categories":["型材","钣金","输送机框架"]},{"stage":"MECH","duration":80,"blocking_categories":["皮带","滚筒","电机","张紧装置"]},{"stage":"ELECTRIC","duration":56,"blocking_categories":["总控PLC","分站IO","伺服系统"]},{"stage":"WIRING","duration":24,"blocking_categories":["主干线缆"]},{"stage":"DEBUG","duration":40,"blocking_categories":[]},{"stage":"COSMETIC","duration":16,"blocking_categories":[]}]');

-- ============================================
-- 3. 物料分类与装配阶段映射表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_category_stage_mapping (
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

CREATE INDEX IF NOT EXISTS idx_category_stage_category ON mes_category_stage_mapping(category_id);
CREATE INDEX IF NOT EXISTS idx_category_stage_stage ON mes_category_stage_mapping(stage_code);
CREATE INDEX IF NOT EXISTS idx_category_stage_active ON mes_category_stage_mapping(is_active);

-- 初始化物料分类映射(基于关键词)
INSERT OR IGNORE INTO mes_category_stage_mapping (category_code, category_name, stage_code, is_blocking, can_postpone, importance_level, keywords) VALUES
-- 框架阶段物料
('ALU_PROFILE', '铝型材', 'FRAME', 1, 0, 'CRITICAL', '["铝型材","4040","4080","型材","框架"]'),
('SHEET_METAL', '钣金件', 'FRAME', 1, 0, 'CRITICAL', '["钣金","底座","立板","安装板"]'),
('FRAME_CONN', '框架连接件', 'FRAME', 1, 0, 'HIGH', '["角码","连接板","角件"]'),
('CASTER', '脚轮地脚', 'FRAME', 0, 1, 'LOW', '["脚轮","万向轮","调节脚","地脚"]'),
-- 机械模组阶段物料
('LINEAR_MODULE', '直线模组', 'MECH', 1, 0, 'CRITICAL', '["模组","直线模组","THK","上银","滑台"]'),
('CYLINDER', '气缸', 'MECH', 1, 0, 'CRITICAL', '["气缸","SMC","亚德客","CKD"]'),
('MOTOR', '电机', 'MECH', 1, 0, 'CRITICAL', '["电机","步进","减速机"]'),
('GUIDE_RAIL', '导轨滑块', 'MECH', 1, 0, 'CRITICAL', '["导轨","滑块","直线导轨"]'),
('PNEUMATIC', '气动元件', 'MECH', 1, 0, 'HIGH', '["气管","接头","电磁阀","气动"]'),
('FASTENER', '紧固件', 'MECH', 0, 1, 'NORMAL', '["螺丝","螺母","螺栓","垫圈"]'),
-- 电气安装阶段物料
('PLC', 'PLC控制器', 'ELECTRIC', 1, 0, 'CRITICAL', '["PLC","三菱","西门子","欧姆龙","控制器"]'),
('SERVO', '伺服系统', 'ELECTRIC', 1, 0, 'CRITICAL', '["伺服","驱动器","安川","松下","台达"]'),
('SENSOR', '传感器', 'ELECTRIC', 1, 0, 'CRITICAL', '["传感器","光电","接近","基恩士","欧姆龙"]'),
('HMI', '触摸屏', 'ELECTRIC', 1, 0, 'HIGH', '["触摸屏","HMI","威纶通","显示屏"]'),
('POWER', '电源', 'ELECTRIC', 1, 0, 'HIGH', '["电源","开关电源","稳压","明纬"]'),
('RELAY', '继电器', 'ELECTRIC', 0, 1, 'NORMAL', '["继电器","固态继电器","中间继电器"]'),
-- 线路整理阶段物料
('WIRE_DUCT', '线槽', 'WIRING', 0, 1, 'NORMAL', '["线槽","PVC线槽","线槽盖"]'),
('CABLE', '线缆', 'WIRING', 1, 0, 'HIGH', '["电缆","线缆","电线","屏蔽线"]'),
('TERMINAL', '端子', 'WIRING', 0, 1, 'NORMAL', '["端子","接线端子","端子排"]'),
('LABEL', '标签扎带', 'WIRING', 0, 1, 'LOW', '["扎带","标签","号码管","标识"]'),
-- 调试准备阶段物料
('FIXTURE', '工装治具', 'DEBUG', 1, 0, 'HIGH', '["工装","治具","夹具","定位"]'),
('TEST_SAMPLE', '测试样品', 'DEBUG', 0, 1, 'NORMAL', '["样品","测试品","产品"]'),
-- 外观完善阶段物料
('NAMEPLATE', '铭牌标识', 'COSMETIC', 0, 1, 'LOW', '["铭牌","标牌","警示标","标识牌"]'),
('COVER', '盖板防护', 'COSMETIC', 0, 1, 'LOW', '["盖板","亚克力","防护罩","安全门"]');

-- ============================================
-- 4. BOM物料装配属性扩展表
-- ============================================

CREATE TABLE IF NOT EXISTS bom_item_assembly_attrs (
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

CREATE INDEX IF NOT EXISTS idx_bom_assembly_bom ON bom_item_assembly_attrs(bom_id);
CREATE INDEX IF NOT EXISTS idx_bom_assembly_stage ON bom_item_assembly_attrs(assembly_stage);
CREATE INDEX IF NOT EXISTS idx_bom_assembly_blocking ON bom_item_assembly_attrs(is_blocking);
CREATE INDEX IF NOT EXISTS idx_bom_assembly_importance ON bom_item_assembly_attrs(importance_level);

-- ============================================
-- 5. 齐套分析结果表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_material_readiness (
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

CREATE INDEX IF NOT EXISTS idx_readiness_no ON mes_material_readiness(readiness_no);
CREATE INDEX IF NOT EXISTS idx_readiness_project ON mes_material_readiness(project_id);
CREATE INDEX IF NOT EXISTS idx_readiness_machine ON mes_material_readiness(machine_id);
CREATE INDEX IF NOT EXISTS idx_readiness_bom ON mes_material_readiness(bom_id);
CREATE INDEX IF NOT EXISTS idx_readiness_status ON mes_material_readiness(status);
CREATE INDEX IF NOT EXISTS idx_readiness_time ON mes_material_readiness(analysis_time);
CREATE INDEX IF NOT EXISTS idx_readiness_can_start ON mes_material_readiness(can_start);

-- ============================================
-- 6. 缺料明细表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_shortage_detail (
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

CREATE INDEX IF NOT EXISTS idx_shortage_detail_readiness ON mes_shortage_detail(readiness_id);
CREATE INDEX IF NOT EXISTS idx_shortage_detail_material ON mes_shortage_detail(material_code);
CREATE INDEX IF NOT EXISTS idx_shortage_detail_stage ON mes_shortage_detail(assembly_stage);
CREATE INDEX IF NOT EXISTS idx_shortage_detail_blocking ON mes_shortage_detail(is_blocking);
CREATE INDEX IF NOT EXISTS idx_shortage_detail_status ON mes_shortage_detail(shortage_status);
CREATE INDEX IF NOT EXISTS idx_shortage_detail_alert ON mes_shortage_detail(alert_level);

-- ============================================
-- 7. 缺料预警规则配置表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_shortage_alert_rule (
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

CREATE INDEX IF NOT EXISTS idx_alert_rule_level ON mes_shortage_alert_rule(alert_level);
CREATE INDEX IF NOT EXISTS idx_alert_rule_active ON mes_shortage_alert_rule(is_active);
CREATE INDEX IF NOT EXISTS idx_alert_rule_priority ON mes_shortage_alert_rule(priority);

-- 初始化四级预警规则
INSERT OR IGNORE INTO mes_shortage_alert_rule (rule_code, rule_name, alert_level, days_before_required, only_blocking, response_deadline_hours, priority, notify_roles, notify_channels, auto_escalate, escalate_after_hours, escalate_to_level, description) VALUES
('L1_STOPPAGE', '停工预警', 'L1', 0, 1, 2, 10,
 '["procurement_manager","project_manager","production_manager"]',
 '["SYSTEM","WECHAT","SMS"]',
 0, 0, NULL,
 '阻塞性物料缺料导致无法装配，需立即处理，2小时内响应'),
('L2_URGENT', '紧急预警', 'L2', 3, 1, 8, 20,
 '["procurement_engineer","project_manager"]',
 '["SYSTEM","WECHAT"]',
 1, 24, 'L1',
 '阻塞性物料3天内需要但缺料，紧急跟进，8小时内响应，24小时未处理升级'),
('L3_ADVANCE', '提前预警', 'L3', 7, 0, 24, 30,
 '["procurement_engineer"]',
 '["SYSTEM","EMAIL"]',
 1, 48, 'L2',
 '物料7天内需要但缺料，提前准备，24小时内响应，48小时未处理升级'),
('L4_NORMAL', '常规预警', 'L4', 14, 0, 48, 40,
 '["procurement_engineer"]',
 '["SYSTEM"]',
 1, 72, 'L3',
 '物料14天内需要但缺料，常规跟进，48小时内响应，72小时未处理升级');

-- ============================================
-- 8. 排产建议表
-- ============================================

CREATE TABLE IF NOT EXISTS mes_scheduling_suggestion (
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

CREATE INDEX IF NOT EXISTS idx_suggestion_no ON mes_scheduling_suggestion(suggestion_no);
CREATE INDEX IF NOT EXISTS idx_suggestion_project ON mes_scheduling_suggestion(project_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_machine ON mes_scheduling_suggestion(machine_id);
CREATE INDEX IF NOT EXISTS idx_suggestion_status ON mes_scheduling_suggestion(status);
CREATE INDEX IF NOT EXISTS idx_suggestion_priority ON mes_scheduling_suggestion(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_suggestion_type ON mes_scheduling_suggestion(suggestion_type);

-- ============================================
-- 完成
-- ============================================
