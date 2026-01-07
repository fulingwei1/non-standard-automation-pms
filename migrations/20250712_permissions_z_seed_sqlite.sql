-- Permission module seed data (SQLite)

BEGIN;

-- Roles
INSERT OR IGNORE INTO roles (role_code, role_name, data_scope, is_system) VALUES
('ADMIN','Administrator','ALL',1),
('GM','GeneralManager','ALL',1),
('PM','ProjectManager','PROJECT',1),
('PMC','PMC','PROJECT',1),
('ENGINEER','Engineer','PROJECT',1),
('QA','Quality','PROJECT',1),
('PURCHASER','Purchaser','DEPT',1),
('FINANCE','Finance','ALL',1),
('SALES','Sales','OWN',1),
('CUSTOMER','Customer','CUSTOMER',1);

-- Permissions
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action) VALUES
('system:user:read','User Read','system','read'),
('system:user:manage','User Manage','system','manage'),
('system:role:read','Role Read','system','read'),
('system:role:manage','Role Manage','system','manage'),
('system:permission:read','Permission Read','system','read'),

('project:project:read','Project Read','project','read'),
('project:project:manage','Project Manage','project','manage'),
('project:milestone:read','Milestone Read','project','read'),
('project:milestone:manage','Milestone Manage','project','manage'),
('project:task:read','Task Read','project','read'),
('project:task:manage','Task Manage','project','manage'),
('project:wbs:read','WBS Read','project','read'),
('project:wbs:manage','WBS Manage','project','manage'),
('project:deliverable:read','Deliverable Read','project','read'),
('project:deliverable:submit','Deliverable Submit','project','submit'),
('project:deliverable:approve','Deliverable Approve','project','approve'),
('project:acceptance:read','Acceptance Read','project','read'),
('project:acceptance:submit','Acceptance Submit','project','submit'),
('project:acceptance:approve','Acceptance Approve','project','approve'),
('project:ecn:read','ECN Read','project','read'),
('project:ecn:submit','ECN Submit','project','submit'),
('project:ecn:approve','ECN Approve','project','approve'),

('supply:purchase:read','Purchase Read','supply','read'),
('supply:purchase:manage','Purchase Manage','supply','manage'),
('supply:outsourcing:read','Outsourcing Read','supply','read'),
('supply:outsourcing:manage','Outsourcing Manage','supply','manage'),

('finance:payment:read','Payment Read','finance','read'),
('finance:payment:approve','Payment Approve','finance','approve'),
('finance:invoice:read','Invoice Read','finance','read'),
('finance:invoice:issue','Invoice Issue','finance','issue'),

('crm:lead:read','Lead Read','crm','read'),
('crm:lead:manage','Lead Manage','crm','manage'),
('crm:opportunity:read','Opportunity Read','crm','read'),
('crm:opportunity:manage','Opportunity Manage','crm','manage'),
('crm:quote:read','Quote Read','crm','read'),
('crm:quote:manage','Quote Manage','crm','manage'),
('crm:quote:approve','Quote Approve','crm','approve'),
('crm:contract:read','Contract Read','crm','read'),
('crm:contract:manage','Contract Manage','crm','manage'),
('crm:contract:approve','Contract Approve','crm','approve');

-- Role permissions
-- ADMIN: all permissions
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r CROSS JOIN permissions p WHERE r.role_code = 'ADMIN';

-- GM: read all + approvals
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'GM' AND (
    p.action = 'read' OR p.perm_code IN (
        'project:deliverable:approve',
        'project:acceptance:approve',
        'project:ecn:approve',
        'finance:payment:approve',
        'crm:quote:approve',
        'crm:contract:approve'
    )
);

-- PM
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'PM' AND p.perm_code IN (
    'project:project:read','project:project:manage',
    'project:milestone:read','project:milestone:manage',
    'project:task:read','project:task:manage',
    'project:wbs:read','project:wbs:manage',
    'project:deliverable:read','project:deliverable:submit','project:deliverable:approve',
    'project:acceptance:read','project:acceptance:submit',
    'project:ecn:read','project:ecn:submit','project:ecn:approve',
    'supply:purchase:read','supply:outsourcing:read'
);

-- PMC
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'PMC' AND p.perm_code IN (
    'project:project:read',
    'project:milestone:read','project:milestone:manage',
    'project:task:read',
    'project:wbs:read',
    'supply:purchase:read','supply:purchase:manage',
    'supply:outsourcing:read','supply:outsourcing:manage'
);

-- ENGINEER
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'ENGINEER' AND p.perm_code IN (
    'project:project:read',
    'project:task:read','project:task:manage',
    'project:deliverable:read','project:deliverable:submit',
    'project:acceptance:read'
);

-- QA
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'QA' AND p.perm_code IN (
    'project:project:read',
    'project:deliverable:read',
    'project:acceptance:read','project:acceptance:approve'
);

-- PURCHASER
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'PURCHASER' AND p.perm_code IN (
    'project:project:read',
    'supply:purchase:read','supply:purchase:manage',
    'supply:outsourcing:read','supply:outsourcing:manage'
);

-- FINANCE
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'FINANCE' AND p.perm_code IN (
    'project:project:read',
    'finance:payment:read','finance:payment:approve',
    'finance:invoice:read','finance:invoice:issue',
    'crm:contract:read'
);

-- SALES
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'SALES' AND p.perm_code IN (
    'crm:lead:read','crm:lead:manage',
    'crm:opportunity:read','crm:opportunity:manage',
    'crm:quote:read','crm:quote:manage',
    'crm:contract:read','crm:contract:manage'
);

-- CUSTOMER
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r JOIN permissions p
WHERE r.role_code = 'CUSTOMER' AND p.perm_code IN (
    'project:project:read',
    'project:milestone:read',
    'project:deliverable:read',
    'project:acceptance:read'
);

COMMIT;
