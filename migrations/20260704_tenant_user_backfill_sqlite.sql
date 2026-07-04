-- TEN-06: 存量用户租户归户（多租户已拍板，为 fail-closed/strict 做数据前提）。
-- 口径：非超管且 tenant_id 为 NULL 的用户归入默认租户（id=1 金凯博，active）；
--       超级管理员保留 NULL（跨租户身份，由中间件 superuser 分支放行）。

UPDATE users
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL
  AND (is_superuser IS NULL OR is_superuser = 0);
