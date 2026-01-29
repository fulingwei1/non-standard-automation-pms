-- ECN状态机修复 - 添加COMPLETED状态 (SQLite)
-- 版本: 1.1
-- 日期: 2026-01-25
-- 说明: 修复ECN状态机，添加缺失的COMPLETED状态，并确保数据完整性

BEGIN;

-- ============================================
-- 1. 验证并修复现有的ECN状态数据
-- ============================================

-- 检查是否有无效的状态值
SELECT
    COUNT(*) as invalid_count,
    status
FROM ecn
WHERE status NOT IN (
    'DRAFT',
    'PENDING_REVIEW',
    'APPROVED',
    'REJECTED',
    'IMPLEMENTED',
    'COMPLETED',
    'CANCELLED'
);

-- 如果存在无效状态，将它们设置为DRAFT（可根据实际情况调整）
UPDATE ecn
SET status = 'DRAFT'
WHERE status NOT IN (
    'DRAFT',
    'PENDING_REVIEW',
    'APPROVED',
    'REJECTED',
    'IMPLEMENTED',
    'COMPLETED',
    'CANCELLED'
);

-- ============================================
-- 2. 添加状态检查约束（通过触发器）
-- ============================================

-- 删除旧的触发器（如果存在）
DROP TRIGGER IF EXISTS tr_ecn_status_check;
DROP TRIGGER IF EXISTS tr_ecn_status_check_insert;

-- 创建状态检查触发器（INSERT）
CREATE TRIGGER tr_ecn_status_check_insert
BEFORE INSERT ON ecn
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.status NOT IN (
            'DRAFT',
            'PENDING_REVIEW',
            'APPROVED',
            'REJECTED',
            'IMPLEMENTED',
            'COMPLETED',
            'CANCELLED'
        )
        THEN RAISE(ABORT, 'Invalid ECN status: ' || NEW.status)
    END;
END;

-- 创建状态检查触发器（UPDATE）
CREATE TRIGGER tr_ecn_status_check_update
BEFORE UPDATE ON ecn
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.status NOT IN (
            'DRAFT',
            'PENDING_REVIEW',
            'APPROVED',
            'REJECTED',
            'IMPLEMENTED',
            'COMPLETED',
            'CANCELLED'
        )
        THEN RAISE(ABORT, 'Invalid ECN status: ' || NEW.status)
    END;
END;

-- ============================================
-- 3. 添加状态转换检查（通过触发器）
-- ============================================

-- 定义有效的状态转换
-- FROM: DRAFT
--   -> PENDING_REVIEW: 提交审核
--   -> CANCELLED: 取消变更
-- FROM: PENDING_REVIEW
--   -> APPROVED: 审批通过
--   -> REJECTED: 审批拒绝
-- FROM: APPROVED
--   -> IMPLEMENTED: 执行变更
-- FROM: IMPLEMENTED
--   -> COMPLETED: 验证完成
--   -> CANCELLED: 取消变更（需特殊权限）
-- FROM: REJECTED
--   -> DRAFT: 重新编辑
--   -> CANCELLED: 放弃变更
-- FROM: COMPLETED
--   -> CANCELLED: 取消已完成变更（需特殊权限）
-- FROM: CANCELLED
--   -> (无转换，终态)

-- 创建状态转换检查触发器（可选，用于数据一致性）
-- 注意：由于 SQLite 的限制，这里只实现基本的状态验证
-- 复杂的状态转换逻辑应该在应用层（状态机）中实现
DROP TRIGGER IF EXISTS tr_ecn_transition_check;

-- ============================================
-- 4. 添加状态统计视图
-- ============================================

-- 定义有效的状态转换
-- FROM: DRAFT
--   -> PENDING_REVIEW: 提交审核
--   -> CANCELLED: 取消变更
-- FROM: PENDING_REVIEW
--   -> APPROVED: 审批通过
--   -> REJECTED: 审批拒绝
-- FROM: APPROVED
--   -> IMPLEMENTED: 执行变更
-- FROM: IMPLEMENTED
--   -> COMPLETED: 验证完成
--   -> CANCELLED: 取消变更（需特殊权限）
-- FROM: REJECTED
--   -> DRAFT: 重新编辑
--   -> CANCELLED: 放弃变更
-- FROM: COMPLETED
--   -> CANCELLED: 取消已完成变更（需特殊权限）
-- FROM: CANCELLED
--   -> (无转换，终态)

-- 创建状态转换检查函数和触发器（可选，用于数据一致性）
DROP TRIGGER IF EXISTS tr_ecn_transition_check;

CREATE TRIGGER tr_ecn_transition_check
BEFORE UPDATE ON ecn
FOR EACH ROW
WHEN NEW.status <> OLD.status
BEGIN
    -- 检查状态转换是否有效
    SELECT CASE
        -- DRAFT的有效转换
        WHEN OLD.status = 'DRAFT' AND NEW.status NOT IN ('PENDING_REVIEW', 'CANCELLED') THEN
            RAISE(ABORT, 'Invalid transition from DRAFT to ' || NEW.status)

        -- PENDING_REVIEW的有效转换
        WHEN OLD.status = 'PENDING_REVIEW' AND NEW.status NOT IN ('APPROVED', 'REJECTED') THEN
            RAISE(ABORT, 'Invalid transition from PENDING_REVIEW to ' || NEW.status)

        -- APPROVED的有效转换
        WHEN OLD.status = 'APPROVED' AND NEW.status NOT IN ('IMPLEMENTED') THEN
            RAISE(ABORT, 'Invalid transition from APPROVED to ' || NEW.status)

        -- IMPLEMENTED的有效转换
        WHEN OLD.status = 'IMPLEMENTED' AND NEW.status NOT IN ('COMPLETED', 'CANCELLED') THEN
            RAISE(ABORT, 'Invalid transition from IMPLEMENTED to ' || NEW.status)

        -- REJECTED的有效转换
        WHEN OLD.status = 'REJECTED' AND NEW.status NOT IN ('DRAFT', 'CANCELLED') THEN
            RAISE(ABORT, 'Invalid transition from REJECTED to ' || NEW.status)

        -- COMPLETED的有效转换
        WHEN OLD.status = 'COMPLETED' AND NEW.status NOT IN ('CANCELLED') THEN
            RAISE(ABORT, 'Invalid transition from COMPLETED to ' || NEW.status)

        -- CANCELLED是终态，不允许转换
        WHEN OLD.status = 'CANCELLED' THEN
            RAISE(ABORT, 'Cannot transition from CANCELLED state')
    END;
END;

-- ============================================
-- 4. 添加状态统计视图
-- ============================================

-- 删除旧视图（如果存在）
DROP VIEW IF EXISTS vw_ecn_status_summary;

-- 创建状态汇总视图
CREATE VIEW vw_ecn_status_summary AS
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ecn), 2) as percentage
FROM ecn
GROUP BY status
ORDER BY
    CASE status
        WHEN 'DRAFT' THEN 1
        WHEN 'PENDING_REVIEW' THEN 2
        WHEN 'APPROVED' THEN 3
        WHEN 'REJECTED' THEN 4
        WHEN 'IMPLEMENTED' THEN 5
        WHEN 'COMPLETED' THEN 6
        WHEN 'CANCELLED' THEN 7
    END;

-- ============================================
-- 5. 更新示例数据（如果需要）
-- ============================================

-- 注意：不修改现有数据，仅添加COMPLETED状态的示例
-- 如果需要，可以取消注释以下语句：
-- INSERT INTO ecn (
--     ecn_no, ecn_title, ecn_type, source_type, project_id,
--     change_reason, change_description, status
-- ) VALUES (
--     'ECN20260125001', '示例：添加COMPLETED状态测试',
--     'DESIGN_CHANGE', 'INTERNAL', 1,
--     '测试新增的COMPLETED状态', '这是一个用于测试COMPLETED状态的示例ECN',
--     'COMPLETED'
-- );

COMMIT;

-- ============================================
-- 验证查询
-- ============================================

-- 1. 检查所有ECN的状态分布
-- SELECT * FROM vw_ecn_status_summary;

-- 2. 检查是否有无效状态
-- SELECT COUNT(*) as invalid_states FROM ecn
-- WHERE status NOT IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'IMPLEMENTED', 'COMPLETED', 'CANCELLED');

-- 3. 检查特定状态的ECN
-- SELECT ecn_no, ecn_title, status FROM ecn WHERE status = 'COMPLETED';
