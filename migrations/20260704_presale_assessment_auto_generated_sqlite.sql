-- PRE-04: mark system-created placeholder technical assessments.
-- SQLite migration for technical_assessments.

ALTER TABLE technical_assessments ADD COLUMN auto_generated BOOLEAN DEFAULT 0;

UPDATE technical_assessments
SET auto_generated = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE UPPER(TRIM(COALESCE(status, ''))) = 'COMPLETED'
  AND TRIM(COALESCE(decision, '')) = '推荐立项'
  AND total_score IS NULL
  AND TRIM(COALESCE(dimension_scores, '')) IN ('', '[]', '{}')
  AND TRIM(COALESCE(item_scores, '')) IN ('', '[]', '{}')
  AND TRIM(COALESCE(risks, '')) IN ('', '[]', '{}')
  AND TRIM(COALESCE(similar_cases, '')) IN ('', '[]', '{}')
  AND TRIM(COALESCE(conditions, '')) IN ('', '[]', '{}')
  AND TRIM(COALESCE(ai_analysis, '')) = ''
  AND TRIM(COALESCE(veto_rules, '')) IN ('', '[]', '{}');
