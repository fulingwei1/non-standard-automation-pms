-- PRE-14: normalize legacy presale support ticket statuses.
-- PROCESSING was a legacy synonym of IN_PROGRESS.
-- REVIEW was used for solution-review tickets but had no transition route; treat it as pending acceptance.

UPDATE presale_support_ticket
SET status = 'IN_PROGRESS',
    updated_at = CURRENT_TIMESTAMP
WHERE status = 'PROCESSING';

UPDATE presale_support_ticket
SET status = 'PENDING',
    updated_at = CURRENT_TIMESTAMP
WHERE status = 'REVIEW';
