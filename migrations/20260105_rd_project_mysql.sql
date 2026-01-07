-- ============================================
-- 研发项目管理模块 - MySQL 数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-05
-- 说明: 研发项目、项目分类、研发费用、费用类型、费用分摊规则、报表记录
-- 适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 研发项目分类表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_project_category (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    category_code       VARCHAR(20) NOT NULL UNIQUE COMMENT '分类编码',
    category_name       VARCHAR(50) NOT NULL COMMENT '分类名称',
    category_type       VARCHAR(20) NOT NULL COMMENT '分类类型：SELF/ENTRUST/COOPERATION（自主/委托/合作）',
    description         TEXT COMMENT '分类说明',
    sort_order          INT DEFAULT 0 COMMENT '排序',
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_rd_category_code (category_code),
    INDEX idx_rd_category_type (category_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发项目分类表';

-- ============================================
-- 2. 研发项目主表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_project (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    project_no          VARCHAR(50) NOT NULL UNIQUE COMMENT '研发项目编号',
    project_name        VARCHAR(200) NOT NULL COMMENT '研发项目名称',
    
    -- 分类信息
    category_id         BIGINT COMMENT '项目分类ID',
    category_type       VARCHAR(20) NOT NULL COMMENT '项目类型：SELF/ENTRUST/COOPERATION',
    
    -- 立项信息
    initiation_date     DATE NOT NULL COMMENT '立项日期',
    planned_start_date  DATE COMMENT '计划开始日期',
    planned_end_date    DATE COMMENT '计划结束日期',
    actual_start_date   DATE COMMENT '实际开始日期',
    actual_end_date     DATE COMMENT '实际结束日期',
    
    -- 项目负责人
    project_manager_id  BIGINT COMMENT '项目负责人ID',
    project_manager_name VARCHAR(50) COMMENT '项目负责人姓名',
    
    -- 立项信息
    initiation_reason   TEXT COMMENT '立项原因',
    research_goal       TEXT COMMENT '研发目标',
    research_content    TEXT COMMENT '研发内容',
    expected_result     TEXT COMMENT '预期成果',
    budget_amount       DECIMAL(12,2) DEFAULT 0 COMMENT '预算金额',
    
    -- 关联非标项目
    linked_project_id   BIGINT COMMENT '关联的非标项目ID',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/PENDING/APPROVED/IN_PROGRESS/COMPLETED/CANCELLED',
    approval_status     VARCHAR(20) DEFAULT 'PENDING' COMMENT '审批状态：PENDING/APPROVED/REJECTED',
    approved_by         BIGINT COMMENT '审批人ID',
    approved_at         DATETIME COMMENT '审批时间',
    approval_remark     TEXT COMMENT '审批意见',
    
    -- 结项信息
    close_date          DATE COMMENT '结项日期',
    close_reason        TEXT COMMENT '结项原因',
    close_result        TEXT COMMENT '结项成果',
    closed_by           BIGINT COMMENT '结项人ID',
    
    -- 统计信息
    total_cost          DECIMAL(12,2) DEFAULT 0 COMMENT '总费用',
    total_hours         DECIMAL(10,2) DEFAULT 0 COMMENT '总工时',
    participant_count   INT DEFAULT 0 COMMENT '参与人数',
    
    -- 备注
    remark              TEXT COMMENT '备注',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (category_id) REFERENCES rd_project_category(id),
    FOREIGN KEY (project_manager_id) REFERENCES users(id),
    FOREIGN KEY (linked_project_id) REFERENCES projects(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (closed_by) REFERENCES users(id),
    
    INDEX idx_rd_project_no (project_no),
    INDEX idx_rd_project_category (category_id),
    INDEX idx_rd_project_status (status),
    INDEX idx_rd_project_manager (project_manager_id),
    INDEX idx_rd_project_linked (linked_project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发项目主表';

-- ============================================
-- 3. 研发费用类型表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost_type (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    type_code           VARCHAR(20) NOT NULL UNIQUE COMMENT '费用类型编码',
    type_name           VARCHAR(50) NOT NULL COMMENT '费用类型名称',
    category            VARCHAR(20) NOT NULL COMMENT '费用大类：LABOR/MATERIAL/DEPRECIATION/OTHER（人工/材料/折旧/其他）',
    description         TEXT COMMENT '类型说明',
    sort_order          INT DEFAULT 0 COMMENT '排序',
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    -- 加计扣除相关
    is_deductible       BOOLEAN DEFAULT TRUE COMMENT '是否可加计扣除',
    deduction_rate      DECIMAL(5,2) DEFAULT 100.00 COMMENT '加计扣除比例(%)',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_rd_cost_type_code (type_code),
    INDEX idx_rd_cost_type_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发费用类型表';

-- ============================================
-- 4. 研发费用分摊规则表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost_allocation_rule (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    rule_name           VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type           VARCHAR(20) NOT NULL COMMENT '分摊类型：PROPORTION/MANUAL（按比例/手工）',
    
    -- 分摊依据
    allocation_basis    VARCHAR(20) NOT NULL COMMENT '分摊依据：HOURS/REVENUE/HEADCOUNT（工时/收入/人数）',
    allocation_formula  JSON COMMENT '分摊公式（JSON格式）',
    
    -- 适用范围
    cost_type_ids       JSON COMMENT '适用费用类型ID列表',
    project_ids         JSON COMMENT '适用项目ID列表（空表示全部）',
    
    -- 状态
    is_active           BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    effective_date      DATE COMMENT '生效日期',
    expiry_date         DATE COMMENT '失效日期',
    
    -- 备注
    remark              TEXT COMMENT '备注',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_rd_allocation_rule_name (rule_name),
    INDEX idx_rd_allocation_rule_type (rule_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发费用分摊规则表';

-- ============================================
-- 5. 研发费用表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_cost (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    cost_no             VARCHAR(50) NOT NULL UNIQUE COMMENT '费用编号',
    
    -- 关联信息
    rd_project_id       BIGINT NOT NULL COMMENT '研发项目ID',
    cost_type_id        BIGINT NOT NULL COMMENT '费用类型ID',
    
    -- 费用信息
    cost_date           DATE NOT NULL COMMENT '费用发生日期',
    cost_amount         DECIMAL(12,2) NOT NULL COMMENT '费用金额',
    cost_description    TEXT COMMENT '费用说明',
    
    -- 人工费用相关（如果费用类型是人工）
    user_id             BIGINT COMMENT '人员ID（人工费用）',
    hours               DECIMAL(10,2) COMMENT '工时（人工费用）',
    hourly_rate         DECIMAL(10,2) COMMENT '时薪（人工费用）',
    
    -- 材料费用相关（如果费用类型是材料）
    material_id         BIGINT COMMENT '物料ID（材料费用）',
    material_qty        DECIMAL(10,4) COMMENT '物料数量（材料费用）',
    material_price       DECIMAL(10,2) COMMENT '物料单价（材料费用）',
    
    -- 折旧费用相关（如果费用类型是折旧）
    equipment_id        BIGINT COMMENT '设备ID（折旧费用）',
    depreciation_period VARCHAR(20) COMMENT '折旧期间（折旧费用）',
    
    -- 来源信息
    source_type         VARCHAR(20) COMMENT '来源类型：MANUAL/CALCULATED/ALLOCATED（手工录入/自动计算/分摊）',
    source_id           BIGINT COMMENT '来源ID（如关联的项目成本ID）',
    
    -- 分摊信息
    is_allocated        BOOLEAN DEFAULT FALSE COMMENT '是否分摊费用',
    allocation_rule_id  BIGINT COMMENT '分摊规则ID',
    allocation_rate     DECIMAL(5,2) COMMENT '分摊比例(%)',
    
    -- 加计扣除
    deductible_amount   DECIMAL(12,2) COMMENT '可加计扣除金额',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/APPROVED/CANCELLED',
    approved_by         BIGINT COMMENT '审批人ID',
    approved_at         DATETIME COMMENT '审批时间',
    
    -- 备注
    remark              TEXT COMMENT '备注',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (rd_project_id) REFERENCES rd_project(id),
    FOREIGN KEY (cost_type_id) REFERENCES rd_cost_type(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (allocation_rule_id) REFERENCES rd_cost_allocation_rule(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    
    INDEX idx_rd_cost_no (cost_no),
    INDEX idx_rd_cost_project (rd_project_id),
    INDEX idx_rd_cost_type (cost_type_id),
    INDEX idx_rd_cost_date (cost_date),
    INDEX idx_rd_cost_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发费用表';

-- ============================================
-- 6. 研发报表记录表
-- ============================================

CREATE TABLE IF NOT EXISTS rd_report_record (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    report_no           VARCHAR(50) NOT NULL UNIQUE COMMENT '报表编号',
    report_type         VARCHAR(50) NOT NULL COMMENT '报表类型：AUXILIARY_LEDGER/DEDUCTION_DETAIL/HIGH_TECH等',
    report_name         VARCHAR(200) NOT NULL COMMENT '报表名称',
    
    -- 报表参数
    report_params       JSON COMMENT '报表参数（JSON格式）',
    start_date          DATE COMMENT '开始日期',
    end_date            DATE COMMENT '结束日期',
    project_ids         JSON COMMENT '项目ID列表',
    
    -- 生成信息
    generated_by        BIGINT NOT NULL COMMENT '生成人ID',
    generated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    file_path           VARCHAR(500) COMMENT '文件路径',
    file_size           INT COMMENT '文件大小（字节）',
    
    -- 状态
    status              VARCHAR(20) DEFAULT 'GENERATED' COMMENT '状态：GENERATED/DOWNLOADED/ARCHIVED',
    
    -- 备注
    remark              TEXT COMMENT '备注',
    
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (generated_by) REFERENCES users(id),
    
    INDEX idx_rd_report_no (report_no),
    INDEX idx_rd_report_type (report_type),
    INDEX idx_rd_report_date (generated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='研发报表记录表';

SET FOREIGN_KEY_CHECKS = 1;



