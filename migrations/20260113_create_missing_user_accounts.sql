-- ============================================
-- 为9位员工创建用户账号并分配角色
-- 生成日期: 2026-01-13
-- ============================================

BEGIN TRANSACTION;

-- ============================================
-- 1. 创建用户账号
-- 密码统一使用 bcrypt 加密的 "password123"
-- ============================================

INSERT INTO users (username, email, password_hash, is_active, employee_id, department, position, created_at, updated_at)
VALUES
  -- 514: 刘亚强 - 客服工程师
  ('liuyaqiang', 'liuyaqiang@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 514, '制造中心/客服部', '客服工程师', datetime('now'), datetime('now')),

  -- 515: 刘伟 - 测试工程师
  ('liuwei2', 'liuwei2@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 515, '工程技术中心/测试部/新能源组', '工程师', datetime('now'), datetime('now')),

  -- 516: 周定炫 - 售前经理
  ('zhoudingxuan', 'zhoudingxuan@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 516, '工程技术中心/售前技术部', '经理', datetime('now'), datetime('now')),

  -- 517: 廖美霞 - 接线员
  ('liaomeixia', 'liaomeixia@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 517, '制造中心/生产部/电子接线组', '接线员', datetime('now'), datetime('now')),

  -- 518: 杨唐贤 - 客服工程师
  ('yangtangxian', 'yangtangxian@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 518, '制造中心/客服部', '客服工程师', datetime('now'), datetime('now')),

  -- 519: 欧阳钰洁 - 行政专员
  ('ouyagyujie', 'ouyangyujie@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 519, '工程技术中心/新能源技术部', '行政专员', datetime('now'), datetime('now')),

  -- 520: 潘自栖 - PLC工程师
  ('panziqi', 'panziqi@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 520, '工程技术中心/PLC 部/PLC四组', '工程师', datetime('now'), datetime('now')),

  -- 521: 邱林涛 - 销售工程师
  ('qiulintao', 'qiulintao@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 521, '营销中心/销售部', '销售工程师', datetime('now'), datetime('now')),

  -- 522: 陈东洲 - PLC工程师
  ('chendongzhou', 'chendongzhou@company.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWuQTrFKW2.',
   1, 522, '工程技术中心/PLC 部/PLC二组', '工程师', datetime('now'), datetime('now'));

-- ============================================
-- 2. 分配角色 - 所有人先分配 USER 基础角色
-- ============================================
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 73  -- USER 角色 id=73
FROM users u
WHERE u.employee_id IN (514, 515, 516, 517, 518, 519, 520, 521, 522);

-- ============================================
-- 3. 根据岗位分配专业角色
-- ============================================

-- 刘亚强(514), 杨唐贤(518): 客服工程师 → DEBUG(38)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 38 FROM users u WHERE u.employee_id IN (514, 518);

-- 刘伟(515): 测试工程师 → QA(33)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 33 FROM users u WHERE u.employee_id = 515;

-- 周定炫(516): 售前经理 → PRESALES(70) + DEPT_MGR(81)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 70 FROM users u WHERE u.employee_id = 516;
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 81 FROM users u WHERE u.employee_id = 516;

-- 廖美霞(517): 接线员 → ASSEMBLER(37)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 37 FROM users u WHERE u.employee_id = 517;

-- 欧阳钰洁(519): 行政专员 → 只有USER基础角色

-- 潘自栖(520), 陈东洲(522): PLC工程师 → EE(31)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 31 FROM users u WHERE u.employee_id IN (520, 522);

-- 邱林涛(521): 销售工程师 → SALES(9)
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, 9 FROM users u WHERE u.employee_id = 521;

COMMIT;

-- ============================================
-- 验证结果
-- ============================================
SELECT '账号创建完成:' as message;
SELECT u.id, u.username, e.name, u.department, u.position,
       GROUP_CONCAT(r.role_name, ', ') as roles
FROM users u
JOIN employees e ON u.employee_id = e.id
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.employee_id IN (514, 515, 516, 517, 518, 519, 520, 521, 522)
GROUP BY u.id
ORDER BY u.id;
