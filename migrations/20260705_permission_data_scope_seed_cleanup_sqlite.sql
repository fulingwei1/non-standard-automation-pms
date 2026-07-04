-- PERM-16: role_data_scopes / data_scope_rules 早期批量种子数据是无意义占位行
-- （rule_name 形如 "data_scope_rules_rule_name_N"，scope_type 用 NORMAL/AUTO/MANUAL
-- 等值，不对应任何 DataScopeEnum；role_data_scopes.is_active 全 NULL，
-- 查询侧一律 filter(RoleDataScope.is_active) 恒不命中）。这些行从未被任何真实
-- 业务消费，两张表在 scripts/ghost_tables_baseline.json 中也标记为幽灵表。
-- 清空垃圾种子，避免误导后续排查；表结构与模型保留，不影响 PERM-17 挂载
-- （PERM-17 走 Role.data_scope 单字段口径，不依赖这两张表）。

DELETE FROM role_data_scopes;
DELETE FROM data_scope_rules;
