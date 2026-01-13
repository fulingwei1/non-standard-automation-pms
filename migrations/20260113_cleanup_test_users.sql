-- ============================================
-- 清理测试用户脚本
-- 删除不在人事档案系统中的测试账号
-- 生成日期: 2026-01-13
-- ============================================

BEGIN TRANSACTION;

-- 要删除的测试用户ID列表
-- 188: sales_zhang, 189: pm_li, 190: mech_wang, 191: elec_zhao
-- 192: soft_chen, 193: purchase_zhou, 194: finance_qian, 195: presale_wang
-- 196: engineer_test, 197: pm_test, 198: regular_user

-- 1. 先删除 user_roles 关联
DELETE FROM user_roles WHERE user_id IN (188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198);

-- 2. 获取对应的 employee_id 用于后续删除
-- employee_ids: 520-530

-- 3. 删除用户记录
DELETE FROM users WHERE id IN (188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198);

-- 4. 删除对应的员工记录
DELETE FROM employees WHERE id IN (
  SELECT id FROM employees
  WHERE name IN ('张销售', '李项目经理', '王机械工程师', '赵电气工程师',
                 '陈软件工程师', '周采购', '钱财务', '王售前工程师',
                 '工程师一号', '项目经理', '普通业务用户')
  AND department IN ('销售部', '项目部', '技术部', '采购部', '财务部',
                     '项目管理部', '工程部', '综合管理部')
);

COMMIT;

-- 验证结果
SELECT '清理完成，统计结果:' as message;
SELECT '剩余活跃用户数' as item, COUNT(*) as count FROM users WHERE is_active = 1
UNION ALL
SELECT '剩余在职员工数', COUNT(*) FROM employees WHERE employment_status = 'active' AND is_active = 1;
