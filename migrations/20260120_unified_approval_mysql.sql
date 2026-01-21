-- 统一审批系统迁移脚本 (MySQL)
-- 创建日期: 2026-01-20
-- 描述: 创建统一审批系统所需的所有表

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. 审批模板表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_templates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `template_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '模板编码',
    `template_name` VARCHAR(100) NOT NULL COMMENT '模板名称',
    `category` VARCHAR(30) COMMENT '分类：HR/FINANCE/PROJECT/BUSINESS/ENGINEERING',
    `description` TEXT COMMENT '模板描述',
    `icon` VARCHAR(100) COMMENT '图标',
    `form_schema` JSON COMMENT '表单结构定义（JSON Schema）',
    `version` INT DEFAULT 1 COMMENT '版本号',
    `is_published` TINYINT(1) DEFAULT 0 COMMENT '是否已发布',
    `visible_scope` JSON COMMENT '可见范围（部门/角色ID列表）',
    `entity_type` VARCHAR(50) COMMENT '关联的业务实体类型',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_template_code` (`template_code`),
    INDEX `idx_template_category` (`category`),
    INDEX `idx_template_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批模板';

-- ============================================================
-- 2. 审批模板版本表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_template_versions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `template_id` INT NOT NULL COMMENT '模板ID',
    `version` INT NOT NULL COMMENT '版本号',
    `form_schema` JSON COMMENT '表单结构',
    `published_by` INT COMMENT '发布人ID',
    `published_at` DATETIME COMMENT '发布时间',
    `change_log` TEXT COMMENT '变更说明',
    `snapshot` JSON COMMENT '完整配置快照',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_template_version_template` (`template_id`),
    UNIQUE INDEX `idx_template_version_unique` (`template_id`, `version`),
    CONSTRAINT `fk_template_version_template` FOREIGN KEY (`template_id`) REFERENCES `approval_templates`(`id`),
    CONSTRAINT `fk_template_version_publisher` FOREIGN KEY (`published_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批模板版本';

-- ============================================================
-- 3. 审批流程定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_flow_definitions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `template_id` INT NOT NULL COMMENT '模板ID',
    `flow_name` VARCHAR(100) NOT NULL COMMENT '流程名称',
    `flow_description` TEXT COMMENT '流程描述',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT '是否默认流程',
    `version` INT DEFAULT 1 COMMENT '版本号',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_flow_template` (`template_id`),
    INDEX `idx_flow_active` (`is_active`),
    INDEX `idx_flow_default` (`template_id`, `is_default`),
    CONSTRAINT `fk_flow_template` FOREIGN KEY (`template_id`) REFERENCES `approval_templates`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批流程定义';

-- ============================================================
-- 4. 审批节点定义表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_node_definitions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `flow_id` INT NOT NULL COMMENT '流程ID',
    `node_code` VARCHAR(50) COMMENT '节点编码',
    `node_name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `node_order` INT DEFAULT 0 COMMENT '节点顺序',
    `node_type` VARCHAR(20) DEFAULT 'APPROVAL' COMMENT '节点类型：APPROVAL/CC/CONDITION/PARALLEL/JOIN',
    `approval_mode` VARCHAR(20) DEFAULT 'SINGLE' COMMENT '审批模式：SINGLE/OR_SIGN/AND_SIGN/SEQUENTIAL',
    `approver_type` VARCHAR(20) COMMENT '审批人类型：FIXED_USER/ROLE/DEPARTMENT_HEAD/DIRECT_MANAGER/FORM_FIELD/MULTI_DEPT/DYNAMIC/INITIATOR',
    `approver_config` JSON COMMENT '审批人配置详情',
    `condition_expression` TEXT COMMENT '条件表达式（CONDITION类型）',
    `can_add_approver` TINYINT(1) DEFAULT 0 COMMENT '允许加签',
    `can_transfer` TINYINT(1) DEFAULT 1 COMMENT '允许转审',
    `can_delegate` TINYINT(1) DEFAULT 1 COMMENT '允许委托',
    `can_reject_to` VARCHAR(20) DEFAULT 'START' COMMENT '驳回目标：START/PREV/SPECIFIC',
    `reject_to_node_id` INT COMMENT '指定驳回节点ID',
    `timeout_hours` INT COMMENT '超时时间（小时）',
    `timeout_action` VARCHAR(20) COMMENT '超时操作：REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE',
    `timeout_notify_config` JSON COMMENT '超时通知配置',
    `notify_config` JSON COMMENT '通知配置',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_node_flow` (`flow_id`),
    INDEX `idx_node_order` (`flow_id`, `node_order`),
    INDEX `idx_node_type` (`node_type`),
    CONSTRAINT `fk_node_flow` FOREIGN KEY (`flow_id`) REFERENCES `approval_flow_definitions`(`id`),
    CONSTRAINT `fk_node_reject_to` FOREIGN KEY (`reject_to_node_id`) REFERENCES `approval_node_definitions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批节点定义';

-- ============================================================
-- 5. 审批路由规则表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_routing_rules` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `template_id` INT NOT NULL COMMENT '模板ID',
    `flow_id` INT NOT NULL COMMENT '流程ID',
    `rule_name` VARCHAR(100) NOT NULL COMMENT '规则名称',
    `rule_order` INT DEFAULT 0 COMMENT '规则优先级',
    `conditions` JSON COMMENT '条件配置JSON',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_routing_template` (`template_id`),
    INDEX `idx_routing_order` (`template_id`, `rule_order`),
    CONSTRAINT `fk_routing_template` FOREIGN KEY (`template_id`) REFERENCES `approval_templates`(`id`),
    CONSTRAINT `fk_routing_flow` FOREIGN KEY (`flow_id`) REFERENCES `approval_flow_definitions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批路由规则';

-- ============================================================
-- 6. 审批实例表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_instances` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '审批单号',
    `template_id` INT NOT NULL COMMENT '模板ID',
    `flow_id` INT COMMENT '流程ID',
    `entity_type` VARCHAR(50) COMMENT '业务实体类型',
    `entity_id` INT COMMENT '业务实体ID',
    `initiator_id` INT NOT NULL COMMENT '发起人ID',
    `initiator_name` VARCHAR(50) COMMENT '发起人姓名',
    `initiator_dept_id` INT COMMENT '发起人部门ID',
    `form_data` JSON COMMENT '表单数据',
    `status` VARCHAR(20) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/PENDING/APPROVED/REJECTED/CANCELLED/TERMINATED',
    `current_node_id` INT COMMENT '当前节点ID',
    `urgency` VARCHAR(10) DEFAULT 'NORMAL' COMMENT '紧急程度：NORMAL/URGENT/CRITICAL',
    `title` VARCHAR(200) COMMENT '审批标题',
    `summary` TEXT COMMENT '审批摘要',
    `submitted_at` DATETIME COMMENT '提交时间',
    `completed_at` DATETIME COMMENT '完成时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_instance_no` (`instance_no`),
    INDEX `idx_instance_template` (`template_id`),
    INDEX `idx_instance_entity` (`entity_type`, `entity_id`),
    INDEX `idx_instance_initiator` (`initiator_id`),
    INDEX `idx_instance_status` (`status`),
    INDEX `idx_instance_submitted` (`submitted_at`),
    INDEX `idx_instance_initiator_status` (`initiator_id`, `status`),
    CONSTRAINT `fk_instance_template` FOREIGN KEY (`template_id`) REFERENCES `approval_templates`(`id`),
    CONSTRAINT `fk_instance_flow` FOREIGN KEY (`flow_id`) REFERENCES `approval_flow_definitions`(`id`),
    CONSTRAINT `fk_instance_initiator` FOREIGN KEY (`initiator_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_instance_dept` FOREIGN KEY (`initiator_dept_id`) REFERENCES `departments`(`id`),
    CONSTRAINT `fk_instance_node` FOREIGN KEY (`current_node_id`) REFERENCES `approval_node_definitions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批实例';

-- ============================================================
-- 7. 审批任务表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_id` INT NOT NULL COMMENT '审批实例ID',
    `node_id` INT NOT NULL COMMENT '节点ID',
    `task_type` VARCHAR(20) DEFAULT 'APPROVAL' COMMENT '任务类型：APPROVAL/CC/EVALUATION',
    `task_order` INT DEFAULT 1 COMMENT '任务序号',
    `assignee_id` INT NOT NULL COMMENT '被分配人ID',
    `assignee_name` VARCHAR(50) COMMENT '被分配人姓名',
    `assignee_dept_id` INT COMMENT '被分配人部门ID',
    `assignee_type` VARCHAR(20) DEFAULT 'NORMAL' COMMENT '分配类型：NORMAL/DELEGATED/TRANSFERRED/ADDED_BEFORE/ADDED_AFTER',
    `original_assignee_id` INT COMMENT '原审批人ID',
    `status` VARCHAR(20) DEFAULT 'PENDING' COMMENT '状态：PENDING/COMPLETED/TRANSFERRED/DELEGATED/SKIPPED/EXPIRED/CANCELLED',
    `action` VARCHAR(20) COMMENT '审批操作：APPROVE/REJECT/RETURN',
    `comment` TEXT COMMENT '审批意见',
    `attachments` JSON COMMENT '附件列表',
    `eval_data` JSON COMMENT '评估数据（ECN等场景）',
    `return_to_node_id` INT COMMENT '退回目标节点ID',
    `due_at` DATETIME COMMENT '截止时间',
    `reminded_at` DATETIME COMMENT '最后提醒时间',
    `remind_count` INT DEFAULT 0 COMMENT '提醒次数',
    `completed_at` DATETIME COMMENT '完成时间',
    `is_countersign` TINYINT(1) DEFAULT 0 COMMENT '是否会签任务',
    `countersign_weight` INT DEFAULT 1 COMMENT '会签权重',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_task_instance` (`instance_id`),
    INDEX `idx_task_node` (`node_id`),
    INDEX `idx_task_assignee` (`assignee_id`),
    INDEX `idx_task_status` (`status`),
    INDEX `idx_task_pending` (`assignee_id`, `status`),
    INDEX `idx_task_due` (`due_at`),
    INDEX `idx_task_type` (`task_type`),
    CONSTRAINT `fk_task_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_task_node` FOREIGN KEY (`node_id`) REFERENCES `approval_node_definitions`(`id`),
    CONSTRAINT `fk_task_assignee` FOREIGN KEY (`assignee_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_task_dept` FOREIGN KEY (`assignee_dept_id`) REFERENCES `departments`(`id`),
    CONSTRAINT `fk_task_original` FOREIGN KEY (`original_assignee_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_task_return_node` FOREIGN KEY (`return_to_node_id`) REFERENCES `approval_node_definitions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批任务';

-- ============================================================
-- 8. 抄送记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_carbon_copies` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_id` INT NOT NULL COMMENT '审批实例ID',
    `node_id` INT COMMENT '触发抄送的节点ID',
    `cc_user_id` INT NOT NULL COMMENT '抄送人ID',
    `cc_user_name` VARCHAR(50) COMMENT '抄送人姓名',
    `cc_source` VARCHAR(20) DEFAULT 'FLOW' COMMENT '抄送来源：FLOW/INITIATOR/APPROVER',
    `added_by` INT COMMENT '添加人ID',
    `is_read` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    `read_at` DATETIME COMMENT '阅读时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_cc_instance` (`instance_id`),
    INDEX `idx_cc_user` (`cc_user_id`),
    INDEX `idx_cc_unread` (`cc_user_id`, `is_read`),
    CONSTRAINT `fk_cc_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_cc_user` FOREIGN KEY (`cc_user_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_cc_adder` FOREIGN KEY (`added_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='抄送记录';

-- ============================================================
-- 9. 会签结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_countersign_results` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_id` INT NOT NULL COMMENT '审批实例ID',
    `node_id` INT NOT NULL COMMENT '节点ID',
    `total_count` INT DEFAULT 0 COMMENT '总任务数',
    `approved_count` INT DEFAULT 0 COMMENT '通过数',
    `rejected_count` INT DEFAULT 0 COMMENT '驳回数',
    `pending_count` INT DEFAULT 0 COMMENT '待处理数',
    `final_result` VARCHAR(20) COMMENT '最终结果：PENDING/PASSED/FAILED',
    `result_reason` TEXT COMMENT '结果说明',
    `summary_data` JSON COMMENT '汇总数据',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_countersign_instance` (`instance_id`),
    INDEX `idx_countersign_node` (`node_id`),
    UNIQUE INDEX `idx_countersign_instance_node` (`instance_id`, `node_id`),
    CONSTRAINT `fk_countersign_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_countersign_node` FOREIGN KEY (`node_id`) REFERENCES `approval_node_definitions`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会签结果';

-- ============================================================
-- 10. 审批操作日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_action_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_id` INT NOT NULL COMMENT '审批实例ID',
    `task_id` INT COMMENT '任务ID',
    `node_id` INT COMMENT '节点ID',
    `operator_id` INT NOT NULL COMMENT '操作人ID',
    `operator_name` VARCHAR(50) COMMENT '操作人姓名',
    `action` VARCHAR(30) NOT NULL COMMENT '操作类型',
    `action_detail` JSON COMMENT '操作详情',
    `comment` TEXT COMMENT '操作备注',
    `attachments` JSON COMMENT '附件列表',
    `before_status` VARCHAR(20) COMMENT '操作前状态',
    `after_status` VARCHAR(20) COMMENT '操作后状态',
    `before_node_id` INT COMMENT '操作前节点ID',
    `after_node_id` INT COMMENT '操作后节点ID',
    `action_at` DATETIME NOT NULL COMMENT '操作时间',
    `ip_address` VARCHAR(50) COMMENT 'IP地址',
    `user_agent` VARCHAR(500) COMMENT 'User-Agent',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_action_log_instance` (`instance_id`),
    INDEX `idx_action_log_task` (`task_id`),
    INDEX `idx_action_log_operator` (`operator_id`),
    INDEX `idx_action_log_action` (`action`),
    INDEX `idx_action_log_time` (`action_at`),
    INDEX `idx_action_log_instance_time` (`instance_id`, `action_at`),
    CONSTRAINT `fk_action_log_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_action_log_task` FOREIGN KEY (`task_id`) REFERENCES `approval_tasks`(`id`),
    CONSTRAINT `fk_action_log_operator` FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批操作日志';

-- ============================================================
-- 11. 审批评论表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_comments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `instance_id` INT NOT NULL COMMENT '审批实例ID',
    `user_id` INT NOT NULL COMMENT '评论人ID',
    `user_name` VARCHAR(50) COMMENT '评论人姓名',
    `content` TEXT NOT NULL COMMENT '评论内容',
    `attachments` JSON COMMENT '附件列表',
    `parent_id` INT COMMENT '父评论ID',
    `reply_to_user_id` INT COMMENT '回复的用户ID',
    `mentioned_user_ids` JSON COMMENT '@提及的用户ID列表',
    `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '是否已删除',
    `deleted_at` DATETIME COMMENT '删除时间',
    `deleted_by` INT COMMENT '删除人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_comment_instance` (`instance_id`),
    INDEX `idx_comment_user` (`user_id`),
    INDEX `idx_comment_parent` (`parent_id`),
    CONSTRAINT `fk_comment_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_id`) REFERENCES `approval_comments`(`id`),
    CONSTRAINT `fk_comment_reply_to` FOREIGN KEY (`reply_to_user_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_comment_deleter` FOREIGN KEY (`deleted_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批评论';

-- ============================================================
-- 12. 审批代理人配置表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_delegates` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL COMMENT '原审批人ID',
    `delegate_id` INT NOT NULL COMMENT '代理人ID',
    `scope` VARCHAR(20) DEFAULT 'ALL' COMMENT '代理范围：ALL/TEMPLATE/CATEGORY',
    `template_ids` JSON COMMENT '指定模板ID列表',
    `categories` JSON COMMENT '指定分类列表',
    `start_date` DATE NOT NULL COMMENT '开始日期',
    `end_date` DATE NOT NULL COMMENT '结束日期',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `reason` VARCHAR(200) COMMENT '代理原因',
    `notify_original` TINYINT(1) DEFAULT 1 COMMENT '是否通知原审批人',
    `notify_delegate` TINYINT(1) DEFAULT 1 COMMENT '是否通知代理人',
    `created_by` INT COMMENT '创建人ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_delegate_user` (`user_id`),
    INDEX `idx_delegate_delegate` (`delegate_id`),
    INDEX `idx_delegate_active` (`is_active`),
    INDEX `idx_delegate_date_range` (`start_date`, `end_date`),
    INDEX `idx_delegate_user_active` (`user_id`, `is_active`),
    CONSTRAINT `fk_delegate_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_delegate_delegate` FOREIGN KEY (`delegate_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_delegate_creator` FOREIGN KEY (`created_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批代理人配置';

-- ============================================================
-- 13. 代理审批日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS `approval_delegate_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `delegate_config_id` INT NOT NULL COMMENT '代理配置ID',
    `task_id` INT NOT NULL COMMENT '任务ID',
    `instance_id` INT NOT NULL COMMENT '实例ID',
    `original_user_id` INT NOT NULL COMMENT '原审批人ID',
    `delegate_user_id` INT NOT NULL COMMENT '代理人ID',
    `action` VARCHAR(20) COMMENT '操作类型',
    `action_at` DATETIME COMMENT '操作时间',
    `original_notified` TINYINT(1) DEFAULT 0 COMMENT '是否已通知原审批人',
    `original_notified_at` DATETIME COMMENT '通知时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_delegate_log_config` (`delegate_config_id`),
    INDEX `idx_delegate_log_task` (`task_id`),
    INDEX `idx_delegate_log_original` (`original_user_id`),
    CONSTRAINT `fk_delegate_log_config` FOREIGN KEY (`delegate_config_id`) REFERENCES `approval_delegates`(`id`),
    CONSTRAINT `fk_delegate_log_task` FOREIGN KEY (`task_id`) REFERENCES `approval_tasks`(`id`),
    CONSTRAINT `fk_delegate_log_instance` FOREIGN KEY (`instance_id`) REFERENCES `approval_instances`(`id`),
    CONSTRAINT `fk_delegate_log_original` FOREIGN KEY (`original_user_id`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_delegate_log_delegate` FOREIGN KEY (`delegate_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理审批日志';

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 插入默认审批模板
-- ============================================================

INSERT INTO `approval_templates` (`template_code`, `template_name`, `category`, `description`, `entity_type`, `is_published`, `is_active`)
VALUES
    ('QUOTE_APPROVAL', '报价审批', 'BUSINESS', '报价单审批流程，根据毛利率自动选择审批层级', 'QUOTE', 1, 1),
    ('CONTRACT_APPROVAL', '合同审批', 'BUSINESS', '销售合同审批流程', 'CONTRACT', 1, 1),
    ('INVOICE_APPROVAL', '发票审批', 'FINANCE', '开票申请审批流程', 'INVOICE', 1, 1),
    ('ECN_APPROVAL', 'ECN审批', 'ENGINEERING', '工程变更通知审批流程，支持多部门会签评估', 'ECN', 1, 1),
    ('PROJECT_APPROVAL', '项目审批', 'PROJECT', '项目立项审批流程', 'PROJECT', 1, 1),
    ('LEAVE_REQUEST', '请假申请', 'HR', '员工请假审批流程，根据请假天数自动选择审批层级', 'LEAVE', 1, 1),
    ('PURCHASE_APPROVAL', '采购审批', 'FINANCE', '采购申请审批流程，根据金额自动选择审批层级', 'PURCHASE', 1, 1),
    ('TIMESHEET_APPROVAL', '工时审批', 'HR', '员工工时审批流程', 'TIMESHEET', 1, 1);

-- 更新请假模板的表单结构
UPDATE `approval_templates`
SET `form_schema` = '{"fields":[{"name":"leave_type","type":"select","label":"请假类型","options":["年假","事假","病假","婚假","产假","丧假"],"required":true},{"name":"start_date","type":"date","label":"开始日期","required":true},{"name":"end_date","type":"date","label":"结束日期","required":true},{"name":"leave_days","type":"number","label":"请假天数","required":true},{"name":"reason","type":"textarea","label":"请假原因","required":true}]}'
WHERE `template_code` = 'LEAVE_REQUEST';

COMMIT;
