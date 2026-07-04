-- PROJ-05: normalize project lifecycle statuses to stage + STxx.
-- Legacy coarse values (EXECUTING/COMPLETED/active/archived) are kept readable
-- in code, but storage should converge to canonical STxx values.

UPDATE projects
SET is_archived = 0,
    updated_at = CURRENT_TIMESTAMP
WHERE is_archived IS NULL;

UPDATE projects
SET is_archived = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE UPPER(TRIM(COALESCE(status, ''))) = 'ARCHIVED';

UPDATE projects
SET stage = 'S9',
    status = 'ST30',
    health = CASE WHEN health IS NULL OR TRIM(health) = '' THEN 'H4' ELSE health END,
    updated_at = CURRENT_TIMESTAMP
WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('COMPLETED', 'CLOSED', 'DONE', 'FINISHED');

UPDATE projects
SET status = CASE UPPER(TRIM(COALESCE(stage, 'S1')))
    WHEN 'S1' THEN 'ST01'
    WHEN 'S2' THEN 'ST03'
    WHEN 'S3' THEN 'ST05'
    WHEN 'S4' THEN 'ST07'
    WHEN 'S5' THEN 'ST10'
    WHEN 'S6' THEN 'ST15'
    WHEN 'S7' THEN 'ST20'
    WHEN 'S8' THEN 'ST25'
    WHEN 'S9' THEN 'ST30'
    ELSE 'ST01'
END,
updated_at = CURRENT_TIMESTAMP
WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('EXECUTING', 'IN_PROGRESS', 'ACTIVE', 'ARCHIVED')
   OR status IS NULL
   OR TRIM(status) = '';
