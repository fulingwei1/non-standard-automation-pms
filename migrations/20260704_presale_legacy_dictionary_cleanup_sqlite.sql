-- PRE-24: normalize legacy presale dictionary values.
-- presale_ai_quotation.quotation_type stores SQLAlchemy Enum names in SQLite.
-- Keep BASIC/STANDARD/PREMIUM uppercase; collapse old AUTO/MANUAL/NORMAL to STANDARD.

UPDATE presale_ai_quotation
SET quotation_type = CASE
    WHEN UPPER(TRIM(quotation_type)) = 'BASIC' THEN 'BASIC'
    WHEN UPPER(TRIM(quotation_type)) = 'PREMIUM' THEN 'PREMIUM'
    ELSE 'STANDARD'
END,
updated_at = CURRENT_TIMESTAMP
WHERE quotation_type IS NULL
   OR TRIM(quotation_type) = ''
   OR UPPER(TRIM(quotation_type)) NOT IN ('BASIC', 'STANDARD', 'PREMIUM')
   OR quotation_type != UPPER(TRIM(quotation_type));

-- opportunities.assessment_status now uses AssessmentStatusEnum:
-- PENDING / IN_PROGRESS / COMPLETED / CANCELLED.
UPDATE opportunities
SET assessment_status = CASE
    WHEN UPPER(TRIM(assessment_status)) = 'REQUESTED' THEN 'PENDING'
    WHEN UPPER(TRIM(assessment_status)) = 'ASSESSMENT_IN_PROGRESS' THEN 'IN_PROGRESS'
    WHEN UPPER(TRIM(assessment_status)) = 'ASSESSMENT_COMPLETED' THEN 'COMPLETED'
    WHEN UPPER(TRIM(assessment_status)) IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')
        THEN UPPER(TRIM(assessment_status))
    ELSE assessment_status
END,
updated_at = CURRENT_TIMESTAMP
WHERE assessment_status IS NOT NULL
  AND TRIM(assessment_status) != ''
  AND (
      UPPER(TRIM(assessment_status)) IN ('REQUESTED', 'ASSESSMENT_IN_PROGRESS', 'ASSESSMENT_COMPLETED')
      OR assessment_status != UPPER(TRIM(assessment_status))
  );

UPDATE opportunities
SET assessment_status = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE assessment_status IS NOT NULL
  AND TRIM(assessment_status) = '';
