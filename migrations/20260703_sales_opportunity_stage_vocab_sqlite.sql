-- Normalize legacy opportunity stage values to OpportunityStageEnum.
-- Active stages are now: DISCOVERY, QUALIFICATION, PROPOSAL, NEGOTIATION, CLOSING, WON, LOST.

UPDATE opportunities
SET stage = 'QUALIFICATION'
WHERE stage IN ('QUALIFIED', 'QUALIFYING');

UPDATE opportunities
SET stage = 'PROPOSAL'
WHERE stage = 'PROPOSING';

UPDATE opportunities
SET stage = 'NEGOTIATION'
WHERE stage IN ('NEGOTIATING', 'ON_HOLD');
