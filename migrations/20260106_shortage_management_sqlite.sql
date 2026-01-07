-- ============================================
-- 缺料管理模块扩展表 - SQLite 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-06
-- 说明: 工单BOM明细、物料需求汇总、齐套检查记录、预警处理日志、缺料统计日报
-- ============================================

-- ============================================
-- 1. 工单BOM明细表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_work_order_bom (
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

CREATE INDEX idx_work_order_bom_wo ON mat_work_order_bom(work_order_id);
CREATE INDEX idx_work_order_bom_material ON mat_work_order_bom(material_code);
CREATE INDEX idx_work_order_bom_date ON mat_work_order_bom(required_date);

-- ============================================
-- 2. 物料需求汇总表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_material_requirement (
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

CREATE INDEX idx_requirement_no ON mat_material_requirement(requirement_no);
CREATE INDEX idx_requirement_wo ON mat_material_requirement(work_order_id);
CREATE INDEX idx_requirement_material ON mat_material_requirement(material_code);
CREATE INDEX idx_requirement_status ON mat_material_requirement(status);
CREATE INDEX idx_requirement_date ON mat_material_requirement(required_date);

-- ============================================
-- 3. 齐套检查记录表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_kit_check (
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

CREATE INDEX idx_kit_check_no ON mat_kit_check(check_no);
CREATE INDEX idx_kit_check_wo ON mat_kit_check(work_order_id);
CREATE INDEX idx_kit_check_project ON mat_kit_check(project_id);
CREATE INDEX idx_kit_check_status ON mat_kit_check(kit_status);
CREATE INDEX idx_kit_check_time ON mat_kit_check(check_time);

-- ============================================
-- 4. 预警处理日志表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_alert_log (
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

CREATE INDEX idx_alert_log_alert ON mat_alert_log(alert_id);
CREATE INDEX idx_alert_log_time ON mat_alert_log(action_time);
CREATE INDEX idx_alert_log_operator ON mat_alert_log(operator_id);

-- ============================================
-- 5. 缺料统计日报表
-- ============================================

CREATE TABLE IF NOT EXISTS mat_shortage_daily_report (
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

CREATE INDEX idx_daily_report_date ON mat_shortage_daily_report(report_date);

-- ============================================
-- 6. 缺料预警表（完整版）
-- ============================================

CREATE TABLE IF NOT EXISTS mat_shortage_alert (
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

CREATE INDEX idx_alert_no ON mat_shortage_alert(alert_no);
CREATE INDEX idx_alert_work_order ON mat_shortage_alert(work_order_id);
CREATE INDEX idx_alert_material ON mat_shortage_alert(material_code);
CREATE INDEX idx_alert_level ON mat_shortage_alert(alert_level);
CREATE INDEX idx_alert_status ON mat_shortage_alert(status);
CREATE INDEX idx_alert_handler ON mat_shortage_alert(handler_id);
CREATE INDEX idx_alert_required_date ON mat_shortage_alert(required_date);

