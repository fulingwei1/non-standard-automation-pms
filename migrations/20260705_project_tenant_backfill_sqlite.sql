-- TEN-03（Project 域首片）：projects.tenant_id 此前是彻底的幽灵列——DB 早有
-- 该列和索引，但 ORM 模型从未声明，任何代码都无法读写。现已在 Project 模型
-- 补上声明，交给 TEN-02 的框架级查询过滤接管；存量项目需要先归户，否则
-- TEN-02 过滤会把所有存量项目当成"无租户"处理。
--
-- 口径同 TEN-06 用户归户：全部归入默认租户（id=1 金凯博，active）。
-- 与用户归户不同的是这里没有"超管保留 NULL"的对应语义——项目本身没有
-- 超级管理员概念，所有存量项目都应该有明确归属。

UPDATE projects
SET tenant_id = (SELECT MIN(id) FROM tenants WHERE status = 'active')
WHERE tenant_id IS NULL;
