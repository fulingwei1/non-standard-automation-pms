-- 全面权限配置迁移脚本 (MySQL)
-- 日期: 2026-01-20
-- 说明: 为29个缺失权限的功能模块添加完整的权限定义
-- 权限编码格式: {module}:{resource}:{action}

START TRANSACTION;

-- ============================================
-- 1. 优势产品模块 (advantage-products)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('advantage_product:read', '优势产品查看', 'advantage_product', 'advantage_product', 'read', '可以查看优势产品列表和详情'),
('advantage_product:create', '优势产品创建', 'advantage_product', 'advantage_product', 'create', '可以创建新的优势产品'),
('advantage_product:update', '优势产品更新', 'advantage_product', 'advantage_product', 'update', '可以更新优势产品信息'),
('advantage_product:delete', '优势产品删除', 'advantage_product', 'advantage_product', 'delete', '可以删除优势产品');

-- ============================================
-- 2. 装配套件模块 (assembly-kit)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('assembly_kit:read', '装配套件查看', 'assembly_kit', 'assembly_kit', 'read', '可以查看装配套件列表和详情'),
('assembly_kit:create', '装配套件创建', 'assembly_kit', 'assembly_kit', 'create', '可以创建装配套件'),
('assembly_kit:update', '装配套件更新', 'assembly_kit', 'assembly_kit', 'update', '可以更新装配套件信息'),
('assembly_kit:delete', '装配套件删除', 'assembly_kit', 'assembly_kit', 'delete', '可以删除装配套件'),
('assembly_kit:manage', '装配套件管理', 'assembly_kit', 'assembly_kit', 'manage', '可以管理装配套件的完整生命周期');

-- ============================================
-- 3. 预算管理模块 (budgets)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('budget:read', '预算查看', 'budget', 'budget', 'read', '可以查看项目预算列表和详情'),
('budget:create', '预算创建', 'budget', 'budget', 'create', '可以创建项目预算'),
('budget:update', '预算更新', 'budget', 'budget', 'update', '可以更新项目预算信息'),
('budget:approve', '预算审批', 'budget', 'budget', 'approve', '可以审批项目预算'),
('budget:delete', '预算删除', 'budget', 'budget', 'delete', '可以删除项目预算');

-- ============================================
-- 4. 业务支持模块 (business-support)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('business_support:read', '业务支持查看', 'business_support', 'business_support', 'read', '可以查看业务支持订单和详情'),
('business_support:create', '业务支持创建', 'business_support', 'business_support', 'create', '可以创建业务支持订单'),
('business_support:update', '业务支持更新', 'business_support', 'business_support', 'update', '可以更新业务支持订单'),
('business_support:approve', '业务支持审批', 'business_support', 'business_support', 'approve', '可以审批业务支持订单'),
('business_support:manage', '业务支持管理', 'business_support', 'business_support', 'manage', '可以管理业务支持的完整流程');

-- ============================================
-- 5. 成本管理模块 (costs)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('cost:read', '成本查看', 'cost', 'cost', 'read', '可以查看项目成本列表和详情'),
('cost:create', '成本创建', 'cost', 'cost', 'create', '可以创建成本记录'),
('cost:update', '成本更新', 'cost', 'cost', 'update', '可以更新成本信息'),
('cost:delete', '成本删除', 'cost', 'cost', 'delete', '可以删除成本记录'),
('cost:manage', '成本管理', 'cost', 'cost', 'manage', '可以管理成本的完整生命周期');

-- ============================================
-- 6. 客户管理模块 (customers)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('customer:read', '客户查看', 'customer', 'customer', 'read', '可以查看客户列表和详情'),
('customer:create', '客户创建', 'customer', 'customer', 'create', '可以创建新客户'),
('customer:update', '客户更新', 'customer', 'customer', 'update', '可以更新客户信息'),
('customer:delete', '客户删除', 'customer', 'customer', 'delete', '可以删除客户');

-- ============================================
-- 7. 数据导入导出模块 (data-import-export)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('data_import:import', '数据导入', 'data_import', 'data_import', 'import', '可以导入数据到系统'),
('data_export:export', '数据导出', 'data_export', 'data_export', 'export', '可以导出系统数据'),
('data_import_export:manage', '数据导入导出管理', 'data_import_export', 'data_import_export', 'manage', '可以管理数据导入导出功能');

-- ============================================
-- 8. 文档管理模块 (documents)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('document:read', '文档查看', 'document', 'document', 'read', '可以查看文档列表和详情'),
('document:create', '文档创建', 'document', 'document', 'create', '可以上传和创建文档'),
('document:update', '文档更新', 'document', 'document', 'update', '可以更新文档信息'),
('document:delete', '文档删除', 'document', 'document', 'delete', '可以删除文档'),
('document:download', '文档下载', 'document', 'document', 'download', '可以下载文档');

-- ============================================
-- 9. 工程师模块 (engineers)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('engineer:read', '工程师查看', 'engineer', 'engineer', 'read', '可以查看工程师列表和详情'),
('engineer:create', '工程师创建', 'engineer', 'engineer', 'create', '可以创建工程师信息'),
('engineer:update', '工程师更新', 'engineer', 'engineer', 'update', '可以更新工程师信息'),
('engineer:manage', '工程师管理', 'engineer', 'engineer', 'manage', '可以管理工程师的完整信息');

-- ============================================
-- 10. 小时费率模块 (hourly-rates)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('hourly_rate:read', '小时费率查看', 'hourly_rate', 'hourly_rate', 'read', '可以查看小时费率配置'),
('hourly_rate:create', '小时费率创建', 'hourly_rate', 'hourly_rate', 'create', '可以创建小时费率配置'),
('hourly_rate:update', '小时费率更新', 'hourly_rate', 'hourly_rate', 'update', '可以更新小时费率配置'),
('hourly_rate:delete', '小时费率删除', 'hourly_rate', 'hourly_rate', 'delete', '可以删除小时费率配置');

-- ============================================
-- 11. 人力资源管理模块 (hr-management)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('hr:read', 'HR管理查看', 'hr', 'hr', 'read', '可以查看HR管理相关数据'),
('hr:create', 'HR管理创建', 'hr', 'hr', 'create', '可以创建HR管理记录'),
('hr:update', 'HR管理更新', 'hr', 'hr', 'update', '可以更新HR管理信息'),
('hr:manage', 'HR管理', 'hr', 'hr', 'manage', '可以管理HR的完整功能');

-- ============================================
-- 12. 安装调度模块 (installation-dispatch)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('installation_dispatch:read', '安装调度查看', 'installation_dispatch', 'installation_dispatch', 'read', '可以查看安装调度列表和详情'),
('installation_dispatch:create', '安装调度创建', 'installation_dispatch', 'installation_dispatch', 'create', '可以创建安装调度任务'),
('installation_dispatch:update', '安装调度更新', 'installation_dispatch', 'installation_dispatch', 'update', '可以更新安装调度信息'),
('installation_dispatch:manage', '安装调度管理', 'installation_dispatch', 'installation_dispatch', 'manage', '可以管理安装调度的完整流程');

-- ============================================
-- 13. 问题管理模块 (issues)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('issue:read', '问题查看', 'issue', 'issue', 'read', '可以查看问题列表和详情'),
('issue:create', '问题创建', 'issue', 'issue', 'create', '可以创建问题记录'),
('issue:update', '问题更新', 'issue', 'issue', 'update', '可以更新问题信息'),
('issue:resolve', '问题解决', 'issue', 'issue', 'resolve', '可以解决和关闭问题'),
('issue:assign', '问题分配', 'issue', 'issue', 'assign', '可以分配问题给处理人'),
('issue:delete', '问题删除', 'issue', 'issue', 'delete', '可以删除问题记录');

-- ============================================
-- 14. 设备/机台模块 (machines)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('machine:read', '设备查看', 'machine', 'machine', 'read', '可以查看设备列表和详情'),
('machine:create', '设备创建', 'machine', 'machine', 'create', '可以创建设备信息'),
('machine:update', '设备更新', 'machine', 'machine', 'update', '可以更新设备信息'),
('machine:delete', '设备删除', 'machine', 'machine', 'delete', '可以删除设备');

-- ============================================
-- 15. 物料管理模块 (materials)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('material:read', '物料查看', 'material', 'material', 'read', '可以查看物料列表和详情'),
('material:create', '物料创建', 'material', 'material', 'create', '可以创建物料信息'),
('material:update', '物料更新', 'material', 'material', 'update', '可以更新物料信息'),
('material:delete', '物料删除', 'material', 'material', 'delete', '可以删除物料');

-- ============================================
-- 16. 里程碑模块 (milestones)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('milestone:read', '里程碑查看', 'milestone', 'milestone', 'read', '可以查看里程碑列表和详情'),
('milestone:create', '里程碑创建', 'milestone', 'milestone', 'create', '可以创建里程碑'),
('milestone:update', '里程碑更新', 'milestone', 'milestone', 'update', '可以更新里程碑信息'),
('milestone:delete', '里程碑删除', 'milestone', 'milestone', 'delete', '可以删除里程碑');

-- ============================================
-- 17. 通知模块 (notifications)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('notification:read', '通知查看', 'notification', 'notification', 'read', '可以查看通知列表'),
('notification:create', '通知创建', 'notification', 'notification', 'create', '可以创建和发送通知'),
('notification:update', '通知更新', 'notification', 'notification', 'update', '可以更新通知状态'),
('notification:delete', '通知删除', 'notification', 'notification', 'delete', '可以删除通知');

-- ============================================
-- 18. 售前集成模块 (presales-integration)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('presales_integration:read', '售前集成查看', 'presales_integration', 'presales_integration', 'read', '可以查看售前集成数据'),
('presales_integration:create', '售前集成创建', 'presales_integration', 'presales_integration', 'create', '可以创建售前集成记录'),
('presales_integration:update', '售前集成更新', 'presales_integration', 'presales_integration', 'update', '可以更新售前集成信息'),
('presales_integration:manage', '售前集成管理', 'presales_integration', 'presales_integration', 'manage', '可以管理售前集成的完整功能');

-- ============================================
-- 19. 项目评估模块 (projects/{project_id}/evaluations)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('project_evaluation:read', '项目评估查看', 'project_evaluation', 'project_evaluation', 'read', '可以查看项目评估列表和详情'),
('project_evaluation:create', '项目评估创建', 'project_evaluation', 'project_evaluation', 'create', '可以创建项目评估'),
('project_evaluation:update', '项目评估更新', 'project_evaluation', 'project_evaluation', 'update', '可以更新项目评估信息'),
('project_evaluation:manage', '项目评估管理', 'project_evaluation', 'project_evaluation', 'manage', '可以管理项目评估的完整流程');

-- ============================================
-- 20. 项目角色模块 (projects/{project_id}/roles)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('project_role:read', '项目角色查看', 'project_role', 'project_role', 'read', '可以查看项目角色列表和详情'),
('project_role:create', '项目角色创建', 'project_role', 'project_role', 'create', '可以创建项目角色'),
('project_role:update', '项目角色更新', 'project_role', 'project_role', 'update', '可以更新项目角色信息'),
('project_role:delete', '项目角色删除', 'project_role', 'project_role', 'delete', '可以删除项目角色'),
('project_role:assign', '项目角色分配', 'project_role', 'project_role', 'assign', '可以分配项目角色给用户');

-- ============================================
-- 21. 资质模块 (qualifications)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('qualification:read', '资质查看', 'qualification', 'qualification', 'read', '可以查看资质列表和详情'),
('qualification:create', '资质创建', 'qualification', 'qualification', 'create', '可以创建资质记录'),
('qualification:update', '资质更新', 'qualification', 'qualification', 'update', '可以更新资质信息'),
('qualification:delete', '资质删除', 'qualification', 'qualification', 'delete', '可以删除资质记录'),
('qualification:manage', '资质管理', 'qualification', 'qualification', 'manage', '可以管理资质的完整生命周期');

-- ============================================
-- 22. 报表中心模块 (reports)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('report:read', '报表查看', 'report', 'report', 'read', '可以查看报表列表和详情'),
('report:create', '报表创建', 'report', 'report', 'create', '可以创建和生成报表'),
('report:export', '报表导出', 'report', 'report', 'export', '可以导出报表'),
('report:manage', '报表管理', 'report', 'report', 'manage', '可以管理报表的完整功能');

-- ============================================
-- 23. 短缺预警模块 (shortage-alerts)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('shortage_alert:read', '短缺预警查看', 'shortage_alert', 'shortage_alert', 'read', '可以查看短缺预警列表和详情'),
('shortage_alert:create', '短缺预警创建', 'shortage_alert', 'shortage_alert', 'create', '可以创建短缺预警'),
('shortage_alert:update', '短缺预警更新', 'shortage_alert', 'shortage_alert', 'update', '可以更新短缺预警信息'),
('shortage_alert:resolve', '短缺预警处理', 'shortage_alert', 'shortage_alert', 'resolve', '可以处理和解决短缺预警'),
('shortage_alert:manage', '短缺预警管理', 'shortage_alert', 'shortage_alert', 'manage', '可以管理短缺预警的完整流程');

-- ============================================
-- 24. 人员匹配模块 (staff-matching)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('staff_matching:read', '人员匹配查看', 'staff_matching', 'staff_matching', 'read', '可以查看人员匹配列表和详情'),
('staff_matching:create', '人员匹配创建', 'staff_matching', 'staff_matching', 'create', '可以创建人员匹配记录'),
('staff_matching:update', '人员匹配更新', 'staff_matching', 'staff_matching', 'update', '可以更新人员匹配信息'),
('staff_matching:manage', '人员匹配管理', 'staff_matching', 'staff_matching', 'manage', '可以管理人员匹配的完整功能');

-- ============================================
-- 25. 阶段模块 (stages)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('stage:read', '阶段查看', 'stage', 'stage', 'read', '可以查看项目阶段列表和详情'),
('stage:create', '阶段创建', 'stage', 'stage', 'create', '可以创建项目阶段'),
('stage:update', '阶段更新', 'stage', 'stage', 'update', '可以更新项目阶段信息'),
('stage:delete', '阶段删除', 'stage', 'stage', 'delete', '可以删除项目阶段'),
('stage:manage', '阶段管理', 'stage', 'stage', 'manage', '可以管理项目阶段的完整生命周期');

-- ============================================
-- 26. 供应商模块 (suppliers)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('supplier:read', '供应商查看', 'supplier', 'supplier', 'read', '可以查看供应商列表和详情'),
('supplier:create', '供应商创建', 'supplier', 'supplier', 'create', '可以创建供应商信息'),
('supplier:update', '供应商更新', 'supplier', 'supplier', 'update', '可以更新供应商信息'),
('supplier:delete', '供应商删除', 'supplier', 'supplier', 'delete', '可以删除供应商');

-- ============================================
-- 27. 任务中心模块 (task-center)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('task_center:read', '任务中心查看', 'task_center', 'task_center', 'read', '可以查看任务列表和详情'),
('task_center:create', '任务中心创建', 'task_center', 'task_center', 'create', '可以创建任务'),
('task_center:update', '任务中心更新', 'task_center', 'task_center', 'update', '可以更新任务信息'),
('task_center:assign', '任务中心分配', 'task_center', 'task_center', 'assign', '可以分配任务给执行人'),
('task_center:manage', '任务中心管理', 'task_center', 'task_center', 'manage', '可以管理任务的完整生命周期');

-- ============================================
-- 28. 技术规格模块 (technical-spec)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('technical_spec:read', '技术规格查看', 'technical_spec', 'technical_spec', 'read', '可以查看技术规格列表和详情'),
('technical_spec:create', '技术规格创建', 'technical_spec', 'technical_spec', 'create', '可以创建技术规格'),
('technical_spec:update', '技术规格更新', 'technical_spec', 'technical_spec', 'update', '可以更新技术规格信息'),
('technical_spec:delete', '技术规格删除', 'technical_spec', 'technical_spec', 'delete', '可以删除技术规格');

-- ============================================
-- 29. 工时表模块 (timesheets)
-- ============================================
INSERT IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) VALUES
('timesheet:read', '工时表查看', 'timesheet', 'timesheet', 'read', '可以查看工时表列表和详情'),
('timesheet:create', '工时表创建', 'timesheet', 'timesheet', 'create', '可以创建和填报工时'),
('timesheet:update', '工时表更新', 'timesheet', 'timesheet', 'update', '可以更新工时记录'),
('timesheet:approve', '工时表审批', 'timesheet', 'timesheet', 'approve', '可以审批工时表'),
('timesheet:delete', '工时表删除', 'timesheet', 'timesheet', 'delete', '可以删除工时记录'),
('timesheet:manage', '工时表管理', 'timesheet', 'timesheet', 'manage', '可以管理工时表的完整功能');

COMMIT;
