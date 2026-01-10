-- Purchase module permissions migration (SQLite)
-- 采购模块权限定义
-- 创建时间: 2026-01-10

BEGIN;

-- 采购订单权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description)
VALUES 
    ('purchase:order:read', '采购订单查看', 'purchase', 'order', 'read', '可以查看采购订单列表和详情'),
    ('purchase:order:create', '采购订单创建', 'purchase', 'order', 'create', '可以创建采购订单'),
    ('purchase:order:update', '采购订单更新', 'purchase', 'order', 'update', '可以更新采购订单'),
    ('purchase:order:delete', '采购订单删除', 'purchase', 'order', 'delete', '可以删除采购订单'),
    ('purchase:order:submit', '采购订单提交', 'purchase', 'order', 'submit', '可以提交采购订单'),
    ('purchase:order:approve', '采购订单审批', 'purchase', 'order', 'approve', '可以审批采购订单'),
    ('purchase:order:receive', '采购订单收货', 'purchase', 'order', 'receive', '可以处理采购订单收货'),
    
    -- 收货单权限
    ('purchase:receipt:read', '收货单查看', 'purchase', 'receipt', 'read', '可以查看收货单列表和详情'),
    ('purchase:receipt:create', '收货单创建', 'purchase', 'receipt', 'create', '可以创建收货单'),
    ('purchase:receipt:update', '收货单更新', 'purchase', 'receipt', 'update', '可以更新收货单状态'),
    ('purchase:receipt:inspect', '收货单质检', 'purchase', 'receipt', 'inspect', '可以对收货单进行质检'),
    
    -- 采购申请权限
    ('purchase:request:read', '采购申请查看', 'purchase', 'request', 'read', '可以查看采购申请列表和详情'),
    ('purchase:request:create', '采购申请创建', 'purchase', 'request', 'create', '可以创建采购申请'),
    ('purchase:request:update', '采购申请更新', 'purchase', 'request', 'update', '可以更新采购申请'),
    ('purchase:request:delete', '采购申请删除', 'purchase', 'request', 'delete', '可以删除采购申请'),
    ('purchase:request:submit', '采购申请提交', 'purchase', 'request', 'submit', '可以提交采购申请'),
    ('purchase:request:approve', '采购申请审批', 'purchase', 'request', 'approve', '可以审批采购申请'),
    ('purchase:request:generate', '采购申请生成订单', 'purchase', 'request', 'generate', '可以根据采购申请生成采购订单'),
    
    -- BOM相关权限
    ('purchase:bom:generate', '从BOM生成采购', 'purchase', 'bom', 'generate', '可以从BOM生成采购申请或订单');

COMMIT;
