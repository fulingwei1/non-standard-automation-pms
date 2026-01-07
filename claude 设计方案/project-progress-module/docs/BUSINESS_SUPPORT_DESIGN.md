# 商务支持专员模块设计文档

## 1. 模块概述

### 1.1 业务背景
商务支持岗位是连接销售业务与公司内部运营的关键枢纽，负责客户建档、标书编制、订单及合同处理、对账开票、回款跟踪等工作。本模块旨在为商务支持人员提供一站式工作平台，提升工作效率和数据准确性。

### 1.2 核心职责范围
根据岗位职责说明书，商务支持专员主要负责：
1. **客户供应商建档** - 协助处理客户供应商建档，入驻客户供应商系统
2. **投标管理** - 协助业务完成项目投标工作，编制标书，完成投递和线上投标竞价
3. **合同管理** - 合同审核、盖章、扫描、邮寄、归档，复核商务条款
4. **订单处理** - 订单和合同系统维护录入，安排项目号，发布项目通知单
5. **对账开票** - 根据客户要求完成对账与开票工作
6. **送货管理** - 送货单打印、回收、归档，出货审批
7. **回款跟踪** - 协助催收预付款、发货款、验收款、质保款
8. **验收管理** - 跟催验收单，督促业务员完成验收报告签章
9. **报表统计** - 销售报表整理及汇总播报
10. **资料归档** - 验收报告、立项报告等相关资料归档管理

### 1.3 工作协作关系
- **内部协调**：销售部、PMC部门、财务部、生产部门
- **外部协调**：客户、供应商

---

## 2. 功能架构

```
商务支持工作台
├── 工作看板（首页）
│   ├── 待办事项提醒
│   ├── 今日任务清单
│   ├── 关键指标统计
│   └── 快捷操作入口
│
├── 客户管理
│   ├── 客户档案管理
│   ├── 供应商入驻管理
│   ├── 客户联系人管理
│   └── 客户资质管理
│
├── 投标管理
│   ├── 投标项目登记
│   ├── 标书编制
│   ├── 投标文件管理
│   ├── 线上投标/竞价
│   └── 投标结果跟踪
│
├── 合同管理
│   ├── 合同起草/模板
│   ├── 合同审批流程
│   ├── 合同条款审核
│   ├── 盖章/邮寄管理
│   └── 合同归档查询
│
├── 订单管理
│   ├── 销售订单录入
│   ├── 项目号分配
│   ├── 项目通知单
│   ├── 订单状态跟踪
│   └── 订单变更管理
│
├── 发货管理
│   ├── 出货审批
│   ├── 送货单管理
│   ├── 发货记录
│   └── 送货单回收
│
├── 对账开票
│   ├── 客户对账单
│   ├── 开票申请
│   ├── 发票管理
│   └── 开票记录查询
│
├── 回款管理
│   ├── 回款计划
│   ├── 回款跟踪
│   ├── 催款提醒
│   ├── 回款记录
│   └── 账龄分析
│
├── 验收管理
│   ├── 验收条件检查
│   ├── 验收单跟踪
│   ├── 验收报告管理
│   └── 质保期管理
│
├── 报表中心
│   ├── 销售日报/周报/月报
│   ├── 回款统计报表
│   ├── 合同执行报表
│   ├── 开票统计报表
│   └── 自定义报表
│
└── 资料归档
    ├── 立项报告归档
    ├── 验收报告归档
    ├── 询证函管理
    └── 其他文档归档
```

---

## 3. 数据模型设计

### 3.1 客户档案表 (t_customer)
```sql
CREATE TABLE t_customer (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_no VARCHAR(50) NOT NULL COMMENT '客户编号',
    customer_name VARCHAR(200) NOT NULL COMMENT '客户名称',
    short_name VARCHAR(50) COMMENT '客户简称',
    customer_type ENUM('enterprise', 'government', 'institution', 'other') COMMENT '客户类型',
    industry VARCHAR(100) COMMENT '所属行业',
    region VARCHAR(100) COMMENT '所属区域',
    
    -- 企业信息
    unified_credit_code VARCHAR(50) COMMENT '统一社会信用代码',
    legal_person VARCHAR(50) COMMENT '法人代表',
    registered_capital VARCHAR(50) COMMENT '注册资本',
    establishment_date DATE COMMENT '成立日期',
    business_scope TEXT COMMENT '经营范围',
    
    -- 联系信息
    address VARCHAR(500) COMMENT '公司地址',
    postal_code VARCHAR(20) COMMENT '邮政编码',
    phone VARCHAR(50) COMMENT '联系电话',
    fax VARCHAR(50) COMMENT '传真',
    website VARCHAR(200) COMMENT '网站',
    
    -- 开票信息
    invoice_title VARCHAR(200) COMMENT '发票抬头',
    tax_no VARCHAR(50) COMMENT '税号',
    bank_name VARCHAR(100) COMMENT '开户银行',
    bank_account VARCHAR(50) COMMENT '银行账号',
    invoice_address VARCHAR(500) COMMENT '开票地址',
    invoice_phone VARCHAR(50) COMMENT '开票电话',
    
    -- 收货信息
    delivery_address VARCHAR(500) COMMENT '收货地址',
    delivery_contact VARCHAR(50) COMMENT '收货联系人',
    delivery_phone VARCHAR(50) COMMENT '收货电话',
    
    -- 商务信息
    payment_terms VARCHAR(200) COMMENT '付款条件',
    credit_limit DECIMAL(15,2) COMMENT '信用额度',
    credit_period INT COMMENT '账期(天)',
    
    -- 负责人
    sales_person_id BIGINT COMMENT '负责业务员ID',
    sales_person_name VARCHAR(50) COMMENT '负责业务员',
    
    -- 供应商入驻
    supplier_portal_status ENUM('not_registered', 'registering', 'registered', 'expired') 
        DEFAULT 'not_registered' COMMENT '供应商平台入驻状态',
    supplier_portal_account VARCHAR(100) COMMENT '供应商平台账号',
    supplier_portal_expiry DATE COMMENT '供应商资质到期日',
    
    -- 状态
    status ENUM('active', 'inactive', 'blacklist') DEFAULT 'active',
    
    -- 审计
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_customer_no (customer_no),
    INDEX idx_customer_name (customer_name),
    INDEX idx_sales_person (sales_person_id)
) COMMENT '客户档案表';
```

### 3.2 客户联系人表 (t_customer_contact)
```sql
CREATE TABLE t_customer_contact (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL COMMENT '客户ID',
    contact_name VARCHAR(50) NOT NULL COMMENT '联系人姓名',
    department VARCHAR(100) COMMENT '部门',
    position VARCHAR(100) COMMENT '职位',
    mobile VARCHAR(20) COMMENT '手机',
    phone VARCHAR(50) COMMENT '座机',
    email VARCHAR(100) COMMENT '邮箱',
    wechat VARCHAR(50) COMMENT '微信',
    
    contact_type ENUM('business', 'technical', 'finance', 'procurement', 'other') 
        COMMENT '联系人类型',
    is_primary TINYINT(1) DEFAULT 0 COMMENT '是否主要联系人',
    
    remark TEXT COMMENT '备注',
    status ENUM('active', 'inactive') DEFAULT 'active',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_customer (customer_id)
) COMMENT '客户联系人表';
```

### 3.3 投标项目表 (t_bidding_project)
```sql
CREATE TABLE t_bidding_project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bidding_no VARCHAR(50) NOT NULL COMMENT '投标编号',
    project_name VARCHAR(500) NOT NULL COMMENT '项目名称',
    customer_id BIGINT COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    
    -- 招标信息
    tender_no VARCHAR(100) COMMENT '招标编号',
    tender_type ENUM('public', 'invited', 'competitive', 'single_source', 'online') 
        COMMENT '招标类型：公开/邀请/竞争性谈判/单一来源/网上竞价',
    tender_platform VARCHAR(200) COMMENT '招标平台',
    tender_url VARCHAR(500) COMMENT '招标链接',
    
    -- 时间节点
    publish_date DATE COMMENT '发布日期',
    deadline_date DATETIME COMMENT '投标截止时间',
    bid_opening_date DATETIME COMMENT '开标时间',
    
    -- 标书信息
    bid_bond DECIMAL(15,2) COMMENT '投标保证金',
    bid_bond_status ENUM('not_required', 'pending', 'paid', 'returned') 
        COMMENT '保证金状态',
    estimated_amount DECIMAL(15,2) COMMENT '预估金额',
    
    -- 投标准备
    bid_document_status ENUM('not_started', 'in_progress', 'completed', 'submitted') 
        DEFAULT 'not_started' COMMENT '标书状态',
    technical_doc_ready TINYINT(1) DEFAULT 0 COMMENT '技术文件就绪',
    commercial_doc_ready TINYINT(1) DEFAULT 0 COMMENT '商务文件就绪',
    qualification_doc_ready TINYINT(1) DEFAULT 0 COMMENT '资质文件就绪',
    
    -- 投标方式
    submission_method ENUM('offline', 'online', 'both') COMMENT '投递方式',
    submission_address VARCHAR(500) COMMENT '投递地址',
    
    -- 负责人
    sales_person_id BIGINT COMMENT '业务员ID',
    sales_person_name VARCHAR(50) COMMENT '业务员',
    support_person_id BIGINT COMMENT '商务支持ID',
    support_person_name VARCHAR(50) COMMENT '商务支持',
    
    -- 投标结果
    bid_result ENUM('pending', 'won', 'lost', 'cancelled', 'invalid') 
        DEFAULT 'pending' COMMENT '投标结果',
    bid_price DECIMAL(15,2) COMMENT '投标价格',
    win_price DECIMAL(15,2) COMMENT '中标价格',
    result_date DATE COMMENT '结果公布日期',
    result_remark TEXT COMMENT '结果说明',
    
    status ENUM('draft', 'preparing', 'submitted', 'closed') DEFAULT 'draft',
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_bidding_no (bidding_no),
    INDEX idx_customer (customer_id),
    INDEX idx_deadline (deadline_date),
    INDEX idx_result (bid_result)
) COMMENT '投标项目表';
```

### 3.4 合同表 (t_sales_contract)
```sql
CREATE TABLE t_sales_contract (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    contract_no VARCHAR(50) NOT NULL COMMENT '合同编号',
    contract_name VARCHAR(500) NOT NULL COMMENT '合同名称',
    contract_type ENUM('sales', 'service', 'maintenance', 'other') COMMENT '合同类型',
    
    -- 关联信息
    customer_id BIGINT NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    bidding_id BIGINT COMMENT '关联投标ID',
    project_id BIGINT COMMENT '关联项目ID',
    
    -- 金额信息
    contract_amount DECIMAL(15,2) NOT NULL COMMENT '合同金额(含税)',
    tax_rate DECIMAL(5,2) DEFAULT 13.00 COMMENT '税率',
    amount_without_tax DECIMAL(15,2) COMMENT '不含税金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    
    -- 付款条款
    payment_terms TEXT COMMENT '付款条款说明',
    prepayment_ratio DECIMAL(5,2) COMMENT '预付款比例%',
    prepayment_amount DECIMAL(15,2) COMMENT '预付款金额',
    delivery_payment_ratio DECIMAL(5,2) COMMENT '发货款比例%',
    delivery_payment_amount DECIMAL(15,2) COMMENT '发货款金额',
    acceptance_payment_ratio DECIMAL(5,2) COMMENT '验收款比例%',
    acceptance_payment_amount DECIMAL(15,2) COMMENT '验收款金额',
    warranty_payment_ratio DECIMAL(5,2) COMMENT '质保款比例%',
    warranty_payment_amount DECIMAL(15,2) COMMENT '质保款金额',
    
    -- 交期信息
    delivery_days INT COMMENT '交货期(天)',
    delivery_date DATE COMMENT '交货日期',
    delivery_address VARCHAR(500) COMMENT '交货地址',
    
    -- 质保信息
    warranty_period INT COMMENT '质保期(月)',
    warranty_start_type ENUM('delivery', 'acceptance', 'custom') 
        COMMENT '质保起算方式',
    
    -- 违约条款
    penalty_clause TEXT COMMENT '违约条款',
    penalty_rate DECIMAL(5,4) COMMENT '违约金比例(日)',
    max_penalty_ratio DECIMAL(5,2) COMMENT '最高违约金比例%',
    
    -- 合同状态
    contract_status ENUM('draft', 'reviewing', 'approved', 'signed', 
        'executing', 'completed', 'terminated', 'cancelled') 
        DEFAULT 'draft' COMMENT '合同状态',
    
    -- 审批信息
    submitted_at DATETIME COMMENT '提交审批时间',
    approved_at DATETIME COMMENT '审批通过时间',
    approved_by BIGINT COMMENT '审批人',
    
    -- 签署信息
    sign_date DATE COMMENT '签订日期',
    effective_date DATE COMMENT '生效日期',
    expiry_date DATE COMMENT '到期日期',
    our_signer VARCHAR(50) COMMENT '我方签署人',
    customer_signer VARCHAR(50) COMMENT '客户签署人',
    
    -- 盖章邮寄
    seal_status ENUM('pending', 'sealed', 'sent', 'received', 'archived') 
        DEFAULT 'pending' COMMENT '盖章状态',
    seal_date DATE COMMENT '盖章日期',
    send_date DATE COMMENT '邮寄日期',
    tracking_no VARCHAR(50) COMMENT '快递单号',
    receive_date DATE COMMENT '回收日期',
    
    -- 商务审核
    business_review_status ENUM('pending', 'passed', 'rejected') COMMENT '商务审核状态',
    business_review_comment TEXT COMMENT '商务审核意见',
    business_reviewer_id BIGINT COMMENT '商务审核人',
    business_review_date DATETIME COMMENT '商务审核时间',
    
    -- 风险提示
    risk_level ENUM('low', 'medium', 'high') COMMENT '风险等级',
    risk_items JSON COMMENT '风险项',
    
    -- 负责人
    sales_person_id BIGINT COMMENT '业务员ID',
    sales_person_name VARCHAR(50) COMMENT '业务员',
    support_person_id BIGINT COMMENT '商务支持ID',
    
    -- 文件
    contract_file_id BIGINT COMMENT '合同文件ID',
    attachment_ids JSON COMMENT '附件ID列表',
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX idx_contract_no (contract_no),
    INDEX idx_customer (customer_id),
    INDEX idx_status (contract_status),
    INDEX idx_sign_date (sign_date)
) COMMENT '销售合同表';
```

### 3.5 销售订单表 (t_sales_order)
```sql
CREATE TABLE t_sales_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(50) NOT NULL COMMENT '订单编号',
    
    -- 关联
    contract_id BIGINT COMMENT '合同ID',
    contract_no VARCHAR(50) COMMENT '合同编号',
    customer_id BIGINT NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    project_id BIGINT COMMENT '项目ID',
    project_no VARCHAR(50) COMMENT '项目号',
    
    -- 订单信息
    order_type ENUM('standard', 'sample', 'repair', 'other') DEFAULT 'standard',
    order_amount DECIMAL(15,2) COMMENT '订单金额',
    currency VARCHAR(10) DEFAULT 'CNY',
    
    -- 交期
    required_date DATE COMMENT '客户要求日期',
    promised_date DATE COMMENT '承诺交期',
    
    -- 状态
    order_status ENUM('draft', 'confirmed', 'in_production', 'ready', 
        'partial_shipped', 'shipped', 'completed', 'cancelled') 
        DEFAULT 'draft' COMMENT '订单状态',
    
    -- 项目号分配
    project_no_assigned TINYINT(1) DEFAULT 0 COMMENT '是否已分配项目号',
    project_no_assigned_date DATETIME COMMENT '项目号分配时间',
    project_notice_sent TINYINT(1) DEFAULT 0 COMMENT '是否已发项目通知单',
    project_notice_date DATETIME COMMENT '通知单发布时间',
    
    -- ERP信息
    erp_order_no VARCHAR(50) COMMENT 'ERP订单号',
    erp_sync_status ENUM('pending', 'synced', 'failed') DEFAULT 'pending',
    erp_sync_time DATETIME,
    
    -- 负责人
    sales_person_id BIGINT,
    sales_person_name VARCHAR(50),
    support_person_id BIGINT,
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX idx_order_no (order_no),
    INDEX idx_contract (contract_id),
    INDEX idx_customer (customer_id),
    INDEX idx_project (project_id),
    INDEX idx_status (order_status)
) COMMENT '销售订单表';
```

### 3.6 发货单表 (t_delivery_order)
```sql
CREATE TABLE t_delivery_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    delivery_no VARCHAR(50) NOT NULL COMMENT '送货单号',
    
    -- 关联
    order_id BIGINT NOT NULL COMMENT '销售订单ID',
    order_no VARCHAR(50) COMMENT '销售订单号',
    contract_id BIGINT COMMENT '合同ID',
    customer_id BIGINT NOT NULL COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    project_id BIGINT COMMENT '项目ID',
    
    -- 发货信息
    delivery_date DATE COMMENT '发货日期',
    delivery_type ENUM('express', 'logistics', 'self_pickup', 'install') 
        COMMENT '发货方式',
    logistics_company VARCHAR(100) COMMENT '物流公司',
    tracking_no VARCHAR(100) COMMENT '物流单号',
    
    -- 收货信息
    receiver_name VARCHAR(50) COMMENT '收货人',
    receiver_phone VARCHAR(20) COMMENT '收货电话',
    receiver_address VARCHAR(500) COMMENT '收货地址',
    
    -- 金额
    delivery_amount DECIMAL(15,2) COMMENT '本次发货金额',
    
    -- 审批
    approval_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    approval_comment TEXT COMMENT '审批意见',
    approved_by BIGINT COMMENT '审批人',
    approved_at DATETIME COMMENT '审批时间',
    
    -- 特殊审批（应收未收情况）
    special_approval TINYINT(1) DEFAULT 0 COMMENT '是否特殊审批',
    special_approver_id BIGINT COMMENT '特殊审批人',
    special_approval_reason TEXT COMMENT '特殊审批原因',
    
    -- 送货单状态
    delivery_status ENUM('draft', 'approved', 'printed', 'shipped', 
        'received', 'returned') DEFAULT 'draft',
    print_date DATETIME COMMENT '打印时间',
    ship_date DATETIME COMMENT '实际发货时间',
    receive_date DATE COMMENT '客户签收日期',
    
    -- 送货单回收
    return_status ENUM('pending', 'received', 'lost') DEFAULT 'pending' 
        COMMENT '送货单回收状态',
    return_date DATE COMMENT '回收日期',
    signed_delivery_file_id BIGINT COMMENT '签收送货单文件ID',
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX idx_delivery_no (delivery_no),
    INDEX idx_order (order_id),
    INDEX idx_customer (customer_id),
    INDEX idx_status (delivery_status),
    INDEX idx_return_status (return_status)
) COMMENT '发货单表';
```

### 3.7 对账单表 (t_reconciliation)
```sql
CREATE TABLE t_reconciliation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reconciliation_no VARCHAR(50) NOT NULL COMMENT '对账单号',
    
    -- 客户
    customer_id BIGINT NOT NULL,
    customer_name VARCHAR(200),
    
    -- 对账期间
    period_start DATE COMMENT '对账开始日期',
    period_end DATE COMMENT '对账结束日期',
    
    -- 金额汇总
    opening_balance DECIMAL(15,2) DEFAULT 0 COMMENT '期初余额',
    period_sales DECIMAL(15,2) DEFAULT 0 COMMENT '本期销售',
    period_receipt DECIMAL(15,2) DEFAULT 0 COMMENT '本期回款',
    closing_balance DECIMAL(15,2) DEFAULT 0 COMMENT '期末余额',
    
    -- 状态
    status ENUM('draft', 'sent', 'confirmed', 'disputed') DEFAULT 'draft',
    sent_date DATE COMMENT '发送日期',
    confirm_date DATE COMMENT '确认日期',
    
    -- 客户确认
    customer_confirmed TINYINT(1) DEFAULT 0,
    customer_confirm_date DATE,
    customer_difference DECIMAL(15,2) COMMENT '客户差异金额',
    difference_reason TEXT COMMENT '差异原因',
    
    -- 文件
    reconciliation_file_id BIGINT COMMENT '对账单文件',
    confirmed_file_id BIGINT COMMENT '确认回执文件',
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_customer (customer_id),
    INDEX idx_period (period_start, period_end)
) COMMENT '对账单表';
```

### 3.8 开票申请表 (t_invoice_request)
```sql
CREATE TABLE t_invoice_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_no VARCHAR(50) NOT NULL COMMENT '申请单号',
    
    -- 客户
    customer_id BIGINT NOT NULL,
    customer_name VARCHAR(200),
    
    -- 关联
    contract_id BIGINT COMMENT '合同ID',
    contract_no VARCHAR(50),
    order_id BIGINT COMMENT '订单ID',
    delivery_id BIGINT COMMENT '发货单ID',
    
    -- 开票信息
    invoice_type ENUM('special', 'normal', 'electronic') COMMENT '发票类型',
    invoice_amount DECIMAL(15,2) NOT NULL COMMENT '开票金额',
    tax_rate DECIMAL(5,2) DEFAULT 13.00,
    amount_without_tax DECIMAL(15,2),
    tax_amount DECIMAL(15,2) COMMENT '税额',
    
    -- 开票内容
    invoice_content TEXT COMMENT '开票内容/明细',
    invoice_title VARCHAR(200) COMMENT '发票抬头',
    tax_no VARCHAR(50) COMMENT '税号',
    bank_info VARCHAR(200) COMMENT '开户银行及账号',
    address_phone VARCHAR(300) COMMENT '地址电话',
    
    -- 收票信息
    receiver_name VARCHAR(50) COMMENT '收票人',
    receiver_phone VARCHAR(20),
    receiver_address VARCHAR(500) COMMENT '收票地址',
    
    -- 申请状态
    request_status ENUM('draft', 'submitted', 'approved', 'invoiced', 
        'sent', 'received', 'rejected') DEFAULT 'draft',
    
    -- 审批
    submitted_at DATETIME,
    approved_at DATETIME,
    approved_by BIGINT,
    reject_reason TEXT,
    
    -- 开票结果
    invoice_no VARCHAR(50) COMMENT '发票号码',
    invoice_code VARCHAR(50) COMMENT '发票代码',
    invoice_date DATE COMMENT '开票日期',
    invoiced_by BIGINT COMMENT '开票人',
    
    -- 邮寄
    send_method ENUM('mail', 'email', 'self_pickup') COMMENT '发送方式',
    send_date DATE,
    tracking_no VARCHAR(50),
    receive_date DATE COMMENT '客户收到日期',
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_customer (customer_id),
    INDEX idx_contract (contract_id),
    INDEX idx_status (request_status)
) COMMENT '开票申请表';
```

### 3.9 回款计划表 (t_payment_plan)
```sql
CREATE TABLE t_payment_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联
    contract_id BIGINT NOT NULL COMMENT '合同ID',
    contract_no VARCHAR(50),
    customer_id BIGINT NOT NULL,
    customer_name VARCHAR(200),
    
    -- 款项信息
    payment_type ENUM('prepayment', 'delivery', 'acceptance', 'warranty', 'other') 
        NOT NULL COMMENT '款项类型',
    payment_name VARCHAR(100) COMMENT '款项名称',
    plan_amount DECIMAL(15,2) NOT NULL COMMENT '计划金额',
    plan_date DATE COMMENT '计划回款日期',
    
    -- 触发条件
    trigger_condition TEXT COMMENT '回款触发条件',
    trigger_status ENUM('not_met', 'met', 'waived') DEFAULT 'not_met' 
        COMMENT '条件状态',
    trigger_date DATE COMMENT '条件满足日期',
    
    -- 回款状态
    payment_status ENUM('pending', 'partial', 'completed', 'overdue') 
        DEFAULT 'pending',
    received_amount DECIMAL(15,2) DEFAULT 0 COMMENT '已收金额',
    remaining_amount DECIMAL(15,2) COMMENT '剩余金额',
    
    -- 开票关联
    invoice_request_id BIGINT COMMENT '开票申请ID',
    invoiced TINYINT(1) DEFAULT 0 COMMENT '是否已开票',
    invoiced_amount DECIMAL(15,2) DEFAULT 0 COMMENT '已开票金额',
    
    -- 催款
    last_reminder_date DATE COMMENT '最后催款日期',
    reminder_count INT DEFAULT 0 COMMENT '催款次数',
    next_reminder_date DATE COMMENT '下次催款日期',
    
    -- 负责人
    sales_person_id BIGINT,
    sales_person_name VARCHAR(50),
    
    remark TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract (contract_id),
    INDEX idx_customer (customer_id),
    INDEX idx_plan_date (plan_date),
    INDEX idx_status (payment_status)
) COMMENT '回款计划表';
```

### 3.10 回款记录表 (t_payment_record)
```sql
CREATE TABLE t_payment_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联
    payment_plan_id BIGINT COMMENT '回款计划ID',
    contract_id BIGINT NOT NULL,
    contract_no VARCHAR(50),
    customer_id BIGINT NOT NULL,
    customer_name VARCHAR(200),
    
    -- 回款信息
    payment_date DATE NOT NULL COMMENT '回款日期',
    payment_amount DECIMAL(15,2) NOT NULL COMMENT '回款金额',
    payment_method ENUM('bank', 'check', 'cash', 'bill', 'other') 
        COMMENT '付款方式',
    
    -- 银行信息
    bank_name VARCHAR(100) COMMENT '付款银行',
    bank_account VARCHAR(50) COMMENT '付款账号',
    transaction_no VARCHAR(100) COMMENT '交易流水号',
    
    -- 核销
    write_off_status ENUM('pending', 'partial', 'completed') DEFAULT 'pending',
    
    -- 确认
    confirmed TINYINT(1) DEFAULT 0,
    confirmed_by BIGINT,
    confirmed_at DATETIME,
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract (contract_id),
    INDEX idx_customer (customer_id),
    INDEX idx_payment_date (payment_date)
) COMMENT '回款记录表';
```

### 3.11 验收管理表 (t_acceptance)
```sql
CREATE TABLE t_acceptance (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    acceptance_no VARCHAR(50) NOT NULL COMMENT '验收单号',
    
    -- 关联
    contract_id BIGINT NOT NULL,
    contract_no VARCHAR(50),
    order_id BIGINT,
    project_id BIGINT,
    customer_id BIGINT NOT NULL,
    customer_name VARCHAR(200),
    
    -- 验收信息
    acceptance_type ENUM('partial', 'final') DEFAULT 'final' COMMENT '验收类型',
    acceptance_amount DECIMAL(15,2) COMMENT '验收金额',
    
    -- 验收条件
    condition_check JSON COMMENT '验收条件检查项',
    conditions_met TINYINT(1) DEFAULT 0 COMMENT '条件是否满足',
    conditions_met_date DATE COMMENT '条件满足日期',
    
    -- 验收进度
    acceptance_status ENUM('not_ready', 'ready', 'submitted', 'customer_review', 
        'signed', 'completed') DEFAULT 'not_ready',
    
    -- 提交验收
    submit_date DATE COMMENT '提交验收日期',
    
    -- 客户签署
    customer_sign_date DATE COMMENT '客户签署日期',
    customer_signer VARCHAR(50) COMMENT '客户签署人',
    signed_file_id BIGINT COMMENT '签署验收单文件ID',
    
    -- 验收单跟踪
    tracking_status ENUM('pending', 'reminded', 'received') DEFAULT 'pending',
    reminder_count INT DEFAULT 0 COMMENT '催签次数',
    last_reminder_date DATE COMMENT '最后催签日期',
    received_date DATE COMMENT '收到原件日期',
    
    -- 质保期
    warranty_start_date DATE COMMENT '质保开始日期',
    warranty_end_date DATE COMMENT '质保结束日期',
    warranty_status ENUM('not_started', 'active', 'expiring', 'expired') 
        DEFAULT 'not_started',
    warranty_expiry_reminded TINYINT(1) DEFAULT 0 COMMENT '是否已提醒质保到期',
    
    -- 负责人
    sales_person_id BIGINT,
    sales_person_name VARCHAR(50),
    
    remark TEXT,
    
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract (contract_id),
    INDEX idx_customer (customer_id),
    INDEX idx_status (acceptance_status),
    INDEX idx_warranty (warranty_end_date)
) COMMENT '验收管理表';
```

### 3.12 催款记录表 (t_collection_record)
```sql
CREATE TABLE t_collection_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- 关联
    payment_plan_id BIGINT COMMENT '回款计划ID',
    contract_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    
    -- 催款信息
    collection_date DATE NOT NULL COMMENT '催款日期',
    collection_method ENUM('phone', 'email', 'wechat', 'visit', 'letter') 
        COMMENT '催款方式',
    contact_person VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    
    -- 催款内容
    collection_amount DECIMAL(15,2) COMMENT '催款金额',
    collection_content TEXT COMMENT '催款内容',
    
    -- 客户反馈
    customer_response TEXT COMMENT '客户反馈',
    promised_date DATE COMMENT '客户承诺付款日期',
    promised_amount DECIMAL(15,2) COMMENT '客户承诺金额',
    
    -- 跟进
    next_action TEXT COMMENT '下一步行动',
    next_collection_date DATE COMMENT '下次催款日期',
    
    -- 操作人
    collector_id BIGINT COMMENT '催款人',
    collector_name VARCHAR(50),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_payment_plan (payment_plan_id),
    INDEX idx_contract (contract_id),
    INDEX idx_customer (customer_id)
) COMMENT '催款记录表';
```

---

## 4. 核心功能设计

### 4.1 工作看板

#### 4.1.1 待办事项提醒
```javascript
// 待办事项类型及优先级
const todoTypes = {
  // 紧急（红色）
  urgent: [
    { type: 'bid_deadline', name: '投标截止', beforeDays: 1 },
    { type: 'payment_overdue', name: '回款逾期', afterDays: 0 },
    { type: 'contract_unsigned', name: '合同待签', afterDays: 7 },
  ],
  // 重要（橙色）
  important: [
    { type: 'bid_preparing', name: '标书准备', beforeDays: 3 },
    { type: 'invoice_pending', name: '待开票', afterDays: 3 },
    { type: 'delivery_pending', name: '待审批出货', afterDays: 0 },
    { type: 'acceptance_tracking', name: '验收单跟踪', afterDays: 7 },
  ],
  // 普通（黄色）
  normal: [
    { type: 'contract_review', name: '合同审核', afterDays: 0 },
    { type: 'payment_reminder', name: '回款提醒', beforeDays: 7 },
    { type: 'warranty_expiring', name: '质保到期', beforeDays: 30 },
    { type: 'delivery_return', name: '送货单回收', afterDays: 14 },
  ]
};
```

#### 4.1.2 关键指标
```javascript
// 商务支持KPI指标
const kpiMetrics = {
  // 投标指标
  bidding: {
    total: 0,           // 本月投标数
    won: 0,             // 中标数
    winRate: 0,         // 中标率
    pending: 0,         // 待处理投标
  },
  // 合同指标
  contract: {
    newCount: 0,        // 本月新签合同
    newAmount: 0,       // 新签金额
    pendingReview: 0,   // 待审核
    pendingSeal: 0,     // 待盖章
  },
  // 开票指标
  invoice: {
    monthAmount: 0,     // 本月开票金额
    pending: 0,         // 待开票数
    pendingAmount: 0,   // 待开票金额
  },
  // 回款指标
  collection: {
    monthAmount: 0,     // 本月回款
    overdue: 0,         // 逾期款项数
    overdueAmount: 0,   // 逾期金额
    collectionRate: 0,  // 回款率
  },
  // 验收指标
  acceptance: {
    pending: 0,         // 待验收
    tracking: 0,        // 跟踪中
    warrantyExpiring: 0,// 质保即将到期
  }
};
```

### 4.2 合同商务审核

#### 4.2.1 审核要点（根据岗位职责）
```javascript
// 合同商务审核检查项
const contractReviewChecklist = {
  // 付款条款审核
  paymentTerms: {
    name: '付款条款',
    items: [
      { key: 'prepayment', name: '预付款比例', 
        rule: '新客户必须有预付款，比例≥30%', risk: 'high' },
      { key: 'paymentPeriod', name: '账期', 
        rule: '账期不超过90天', risk: 'medium' },
      { key: 'paymentMethod', name: '付款方式', 
        rule: '优先电汇，承兑需审批', risk: 'low' },
    ]
  },
  // 交期条款
  deliveryTerms: {
    name: '交期条款',
    items: [
      { key: 'deliveryDate', name: '交货日期', 
        rule: '交期需与生产确认', risk: 'medium' },
      { key: 'delayPenalty', name: '延期罚款', 
        rule: '日罚款≤0.05%，总额≤5%', risk: 'high' },
    ]
  },
  // 验收条款
  acceptanceTerms: {
    name: '验收条款',
    items: [
      { key: 'acceptancePeriod', name: '验收期限', 
        rule: '必须约定验收时间，≤30天', risk: 'high' },
      { key: 'acceptanceCondition', name: '验收条件', 
        rule: '验收标准需明确', risk: 'medium' },
    ]
  },
  // 质保条款
  warrantyTerms: {
    name: '质保条款',
    items: [
      { key: 'warrantyPeriod', name: '质保期', 
        rule: '质保期≤12个月', risk: 'medium' },
      { key: 'warrantyScope', name: '质保范围', 
        rule: '需排除人为损坏', risk: 'low' },
    ]
  },
  // 违约条款
  penaltyTerms: {
    name: '违约条款',
    items: [
      { key: 'penaltyRate', name: '违约金比例', 
        rule: '违约金比例≤5%', risk: 'high' },
      { key: 'mutualPenalty', name: '双向约束', 
        rule: '违约条款应双向对等', risk: 'medium' },
    ]
  }
};
```

### 4.3 出货审批逻辑

#### 4.3.1 审批规则（根据岗位职责）
```javascript
// 出货审批规则
const deliveryApprovalRules = {
  // 自动通过条件
  autoApprove: {
    conditions: [
      'contract_signed',      // 合同已签
      'prepayment_received',  // 预付款已收
      'no_overdue_payment',   // 无逾期款项
    ]
  },
  
  // 需特殊审批情况
  specialApproval: {
    triggers: [
      {
        condition: 'prepayment_not_received',
        name: '预付款未收',
        approver: 'sales_manager',  // 销售经理审批
        required: true
      },
      {
        condition: 'has_overdue_payment',
        name: '有逾期应收款',
        approver: 'sales_director', // 销售总监审批
        required: true
      },
      {
        condition: 'credit_limit_exceeded',
        name: '超出信用额度',
        approver: 'finance_manager', // 财务经理审批
        required: true
      }
    ]
  },
  
  // 禁止出货情况
  blockDelivery: {
    conditions: [
      'contract_not_signed',  // 合同未签
      'blacklist_customer',   // 黑名单客户
    ]
  }
};
```

### 4.4 回款跟踪流程

#### 4.4.1 回款阶段管理
```javascript
// 回款阶段及催款策略
const collectionStages = {
  // 预付款
  prepayment: {
    name: '预付款',
    triggerEvent: 'contract_signed',
    reminderStrategy: {
      beforeDays: [7, 3, 1],  // 提前提醒
      afterDays: [1, 3, 7],   // 逾期催款
    },
    blockAction: 'block_production' // 未收到阻止生产
  },
  
  // 发货款
  deliveryPayment: {
    name: '发货款',
    triggerEvent: 'ready_to_ship',
    reminderStrategy: {
      beforeDays: [3, 1],
      afterDays: [1, 3, 5],
    },
    blockAction: 'block_shipment' // 未收到阻止发货
  },
  
  // 验收款
  acceptancePayment: {
    name: '验收款',
    triggerEvent: 'acceptance_completed',
    reminderStrategy: {
      afterDays: [7, 14, 21, 30],
    },
    escalation: {
      afterDays: 30,
      to: 'sales_manager'
    }
  },
  
  // 质保款
  warrantyPayment: {
    name: '质保款',
    triggerEvent: 'warranty_expired',
    reminderStrategy: {
      beforeDays: [30, 14, 7],
      afterDays: [7, 14, 30],
    }
  }
};
```

### 4.5 验收管理流程

#### 4.5.1 验收条件检查
```javascript
// 验收条件模板
const acceptanceConditions = {
  // 设备调试完成
  debugCompleted: {
    name: '设备调试完成',
    checkType: 'system',  // 系统自动检查
    source: 'project_progress'
  },
  // 测试报告提交
  testReportSubmitted: {
    name: '测试报告已提交',
    checkType: 'document',
    required: true
  },
  // 操作培训完成
  trainingCompleted: {
    name: '操作培训完成',
    checkType: 'manual',  // 人工确认
    required: false
  },
  // 技术文件移交
  documentHandover: {
    name: '技术文件移交',
    checkType: 'document',
    documents: ['操作手册', '维护手册', '电气图纸', '机械图纸']
  }
};
```

---

## 5. 自动化提醒机制

### 5.1 提醒规则配置
```javascript
// 自动提醒规则
const reminderRules = [
  // 投标提醒
  {
    type: 'bid_deadline',
    name: '投标截止提醒',
    conditions: [
      { field: 'deadline_date', operator: 'before_days', value: 3 },
      { field: 'bid_document_status', operator: 'not_in', value: ['submitted'] }
    ],
    recipients: ['support_person', 'sales_person'],
    channels: ['system', 'wechat'],
    template: '【投标提醒】{project_name} 投标将于 {deadline_date} 截止，请尽快完成标书准备'
  },
  
  // 回款提醒
  {
    type: 'payment_reminder',
    name: '回款到期提醒',
    conditions: [
      { field: 'plan_date', operator: 'before_days', value: 7 },
      { field: 'payment_status', operator: 'in', value: ['pending'] }
    ],
    recipients: ['sales_person'],
    cc: ['support_person'],
    channels: ['system', 'wechat'],
    template: '【回款提醒】{customer_name} {payment_name} {plan_amount}元 将于 {plan_date} 到期'
  },
  
  // 逾期催款
  {
    type: 'payment_overdue',
    name: '回款逾期提醒',
    conditions: [
      { field: 'plan_date', operator: 'after_days', value: 0 },
      { field: 'payment_status', operator: 'in', value: ['pending', 'partial'] }
    ],
    recipients: ['sales_person', 'sales_manager'],
    cc: ['support_person'],
    channels: ['system', 'wechat', 'email'],
    escalation: [
      { afterDays: 7, addRecipients: ['sales_director'] },
      { afterDays: 30, addRecipients: ['gm'] }
    ]
  },
  
  // 质保到期提醒
  {
    type: 'warranty_expiring',
    name: '质保到期提醒',
    conditions: [
      { field: 'warranty_end_date', operator: 'before_days', value: 30 },
      { field: 'warranty_status', operator: 'eq', value: 'active' }
    ],
    recipients: ['sales_person'],
    cc: ['support_person'],
    channels: ['system', 'wechat'],
    template: '【质保提醒】{customer_name} {project_name} 质保将于 {warranty_end_date} 到期，请跟进质保款回收'
  },
  
  // 送货单回收提醒
  {
    type: 'delivery_return',
    name: '送货单回收提醒',
    conditions: [
      { field: 'ship_date', operator: 'after_days', value: 14 },
      { field: 'return_status', operator: 'eq', value: 'pending' }
    ],
    recipients: ['support_person'],
    channels: ['system'],
    template: '【送货单回收】{delivery_no} 已发货超过14天，请跟进送货单回收'
  },
  
  // 验收单跟踪
  {
    type: 'acceptance_tracking',
    name: '验收单跟踪提醒',
    conditions: [
      { field: 'submit_date', operator: 'after_days', value: 7 },
      { field: 'acceptance_status', operator: 'in', value: ['submitted', 'customer_review'] }
    ],
    recipients: ['sales_person'],
    cc: ['support_person'],
    channels: ['system', 'wechat'],
    template: '【验收跟踪】{customer_name} 验收单已提交{days}天，请跟进客户签署'
  }
];
```

---

## 6. 报表设计

### 6.1 销售报表
```javascript
// 销售日报/周报/月报
const salesReportConfig = {
  daily: {
    name: '销售日报',
    metrics: [
      { name: '新增合同', field: 'new_contracts', type: 'count' },
      { name: '新增金额', field: 'new_amount', type: 'sum' },
      { name: '今日回款', field: 'today_receipt', type: 'sum' },
      { name: '今日开票', field: 'today_invoice', type: 'sum' },
      { name: '发货金额', field: 'today_delivery', type: 'sum' },
    ],
    dimensions: ['sales_person', 'customer'],
    schedule: '每日 18:00'
  },
  
  weekly: {
    name: '销售周报',
    metrics: [
      { name: '本周新签', field: 'week_contracts', type: 'count' },
      { name: '本周金额', field: 'week_amount', type: 'sum' },
      { name: '本周回款', field: 'week_receipt', type: 'sum' },
      { name: '本周开票', field: 'week_invoice', type: 'sum' },
      { name: '投标情况', field: 'week_bidding', type: 'detail' },
    ],
    dimensions: ['sales_person', 'customer', 'region'],
    schedule: '每周五 17:00'
  },
  
  monthly: {
    name: '销售月报',
    metrics: [
      { name: '月度签约', field: 'month_contracts', type: 'count_amount' },
      { name: '月度回款', field: 'month_receipt', type: 'sum' },
      { name: '月度开票', field: 'month_invoice', type: 'sum' },
      { name: '应收账款', field: 'receivable', type: 'sum' },
      { name: '逾期账款', field: 'overdue', type: 'sum' },
      { name: '回款率', field: 'collection_rate', type: 'percent' },
    ],
    dimensions: ['sales_person', 'customer', 'region', 'industry'],
    schedule: '每月1日 09:00'
  }
};
```

### 6.2 账龄分析报表
```javascript
// 应收账款账龄分析
const agingAnalysisConfig = {
  agingBuckets: [
    { name: '未到期', range: [-Infinity, 0] },
    { name: '1-30天', range: [1, 30] },
    { name: '31-60天', range: [31, 60] },
    { name: '61-90天', range: [61, 90] },
    { name: '91-180天', range: [91, 180] },
    { name: '180天以上', range: [181, Infinity] },
  ],
  
  groupBy: ['customer', 'sales_person', 'contract'],
  
  metrics: [
    'total_receivable',   // 应收总额
    'aging_amount',       // 各账龄金额
    'aging_percent',      // 各账龄占比
    'weighted_aging',     // 加权账龄天数
  ]
};
```

---

## 7. 权限设计

### 7.1 功能权限
```javascript
// 商务支持岗位权限
const businessSupportPermissions = {
  // 客户管理
  customer: {
    view: true,
    create: true,
    edit: true,
    delete: false,
    export: true,
  },
  
  // 投标管理
  bidding: {
    view: true,
    create: true,
    edit: true,
    submit: true,
    delete: false,
  },
  
  // 合同管理
  contract: {
    view: true,
    create: true,
    edit: true,
    review: true,        // 商务审核
    seal: true,          // 盖章操作
    archive: true,
    delete: false,
  },
  
  // 订单管理
  order: {
    view: true,
    create: true,
    edit: true,
    assignProjectNo: true,  // 分配项目号
    sendNotice: true,       // 发布通知单
  },
  
  // 发货管理
  delivery: {
    view: true,
    create: true,
    approve: true,       // 审批出货
    print: true,         // 打印送货单
    confirm: true,       // 确认回收
  },
  
  // 开票管理
  invoice: {
    view: true,
    request: true,       // 申请开票
    edit: true,
    approve: false,      // 审批由财务
  },
  
  // 回款管理
  collection: {
    view: true,
    track: true,         // 跟踪记录
    remind: true,        // 催款
    record: false,       // 录入由财务
  },
  
  // 验收管理
  acceptance: {
    view: true,
    create: true,
    track: true,
    archive: true,
  },
  
  // 报表
  report: {
    view: true,
    export: true,
    create: false,       // 创建报表模板
  }
};
```

---

## 8. 企业微信集成

### 8.1 消息推送场景
```javascript
// 企业微信推送配置
const wechatNotifications = [
  {
    event: 'bid_deadline_approaching',
    template: {
      title: '投标截止提醒',
      description: '{project_name}\n截止时间: {deadline}\n剩余: {remaining_days}天',
      url: '{system_url}/bidding/{id}'
    }
  },
  {
    event: 'contract_pending_review',
    template: {
      title: '合同待审核',
      description: '{contract_name}\n客户: {customer_name}\n金额: {amount}',
      url: '{system_url}/contract/{id}'
    }
  },
  {
    event: 'payment_overdue',
    template: {
      title: '回款逾期提醒',
      description: '{customer_name}\n逾期金额: {amount}\n逾期天数: {overdue_days}天',
      url: '{system_url}/collection/{id}'
    }
  },
  {
    event: 'delivery_pending_approval',
    template: {
      title: '出货待审批',
      description: '{customer_name}\n订单: {order_no}\n金额: {amount}',
      url: '{system_url}/delivery/{id}'
    }
  }
];
```

---

## 9. 与其他模块集成

### 9.1 集成接口
```
商务支持模块
    │
    ├── → 项目管理模块
    │     ├── 获取项目进度（验收条件判断）
    │     ├── 发送项目通知单
    │     └── 同步合同/订单信息
    │
    ├── → 生产管理模块
    │     ├── 触发生产排程
    │     └── 查询生产进度
    │
    ├── → 财务系统
    │     ├── 开票数据同步
    │     ├── 回款数据同步
    │     └── 应收账款查询
    │
    ├── → ERP系统（金蝶）
    │     ├── 客户档案同步
    │     ├── 销售订单同步
    │     └── 发货单同步
    │
    └── → 文档管理
          ├── 合同文件归档
          ├── 投标文件归档
          └── 验收文件归档
```

---

## 10. 实施建议

### 10.1 阶段规划
1. **第一阶段（基础功能）**：客户管理、合同管理、订单管理
2. **第二阶段（核心流程）**：发货审批、对账开票、回款跟踪
3. **第三阶段（高级功能）**：投标管理、验收管理、报表中心
4. **第四阶段（智能化）**：自动提醒、风险预警、数据分析

### 10.2 关键成功因素
- 与ERP系统的数据打通
- 审批流程的合理设计
- 提醒机制的有效性
- 报表数据的准确性
- 用户操作的便捷性
