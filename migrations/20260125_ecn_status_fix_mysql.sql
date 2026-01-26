-- ECN状态机修复 - 添加COMPLETED状态 (MySQL)
-- 版本: 1.1
-- 日期: 2026-01-25
-- 说明: 修复ECN状态机，添加缺失的COMPLETED状态，并确保数据完整性

START TRANSACTION;

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
)
GROUP BY status;

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
-- 2. 添加状态检查约束
-- ============================================

-- 创建 ENUM 类型（如果不存在）
DROP TYPE IF EXISTS ecn_status_enum;
CREATE TYPE ecn_status_enum AS ENUM (
    'DRAFT',
    'PENDING_REVIEW',
    'APPROVED',
    'REJECTED',
    'IMPLEMENTED',
    'COMPLETED',
    'CANCELLED'
);

-- 修改 status 列使用 ENUM 类型（注意：这需要表重建，生产环境需要谨慎）
-- 方式一：使用 ENUM 列类型（推荐）
-- ALTER TABLE ecn MODIFY COLUMN status ecn_status_enum NOT NULL DEFAULT 'DRAFT';

-- 方式二：使用 CHECK 约束（更安全，不重建表）
-- ALTER TABLE ecn ADD CONSTRAINT chk_ecn_status
--     CHECK (status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'IMPLEMENTED', 'COMPLETED', 'CANCELLED'));

-- 注意：以上 ALTER TABLE 语句需要根据实际情况选择执行
-- 如果列类型已经是 VARCHAR(20)，可以直接添加 CHECK 约束
ALTER TABLE ecn
ADD CONSTRAINT chk_ecn_status
CHECK (status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'IMPLEMENTED', 'COMPLETED', 'CANCELLED'));

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

-- 删除旧的触发器（如果存在）
DROP TRIGGER IF EXISTS tr_ecn_transition_check;

-- 创建状态转换检查触发器
DELIMITER //
CREATE TRIGGER tr_ecn_transition_check
BEFORE UPDATE ON ecn
FOR EACH ROW
BEGIN
    -- 检查状态转换是否有效
    IF NEW.status <> OLD.status THEN
        -- DRAFT的有效转换
        IF OLD.status = 'DRAFT' AND NEW.status NOT IN ('PENDING_REVIEW', 'CANCELLED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from DRAFT';
        END IF;

        -- PENDING_REVIEW的有效转换
        IF OLD.status = 'PENDING_REVIEW' AND NEW.status NOT IN ('APPROVED', 'REJECTED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from PENDING_REVIEW';
        END IF;

        -- APPROVED的有效转换
        IF OLD.status = 'APPROVED' AND NEW.status NOT IN ('IMPLEMENTED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from APPROVED';
        END IF;

        -- IMPLEMENTED的有效转换
        IF OLD.status = 'IMPLEMENTED' AND NEW.status NOT IN ('COMPLETED', 'CANCELLED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from IMPLEMENTED';
        END IF;

        -- REJECTED的有效转换
        IF OLD.status = 'REJECTED' AND NEW.status NOT IN ('DRAFT', 'CANCELLED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from REJECTED';
        END IF;

        -- COMPLETED的有效转换
        IF OLD.status = 'COMPLETED' AND NEW.status NOT IN ('CANCELLED') THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid transition from COMPLETED';
        END IF;

        -- CANCELLED是终态，不允许转换
        IF OLD.status = 'CANCELLED' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot transition from CANCELLED state';
        END IF;
    END IF;
END//
DELIMITER ;

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
    FIELD(status,
        'DRAFT',
        'PENDING_REVIEW',
        'APPROVED',
        'REJECTED',
        'IMPLEMENTED',
        'COMPLETED',
        'CANCELLED'
    );

-- ============================================
-- 5. 更新示例数据（如果需要）
-- ============================================

-- 注意：不修改现有数据，仅添加COMPLETED状态的示例
-- 如果需要，可以取消注释以下语句：
-- INSERT INTO ecn (
--     ecn_no, ecn_title, ecn_type, source_type, project_id,
--     change_reason, change_description, status,
--     created_by, created_at, updated_at
-- ) VALUES (
--     'ECN20260125001', '示例：添加COMPLETED状态测试',
--     'DESIGN_CHANGE', 'INTERNAL', 1,
--     '测试新增的COMPLETED状态', '这是一个用于测试COMPLETED状态的示例ECN',
--     'COMPLETED', 1, NOW(), NOW()
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

-- 4. 检查约束是否生效
-- SHOW CREATE TABLE ecn;
