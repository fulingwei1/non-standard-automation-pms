-- HR-24: mark and down-weight auto-completed collaboration ratings.

ALTER TABLE collaboration_rating ADD COLUMN rating_weight NUMERIC(4, 2) DEFAULT 1 NOT NULL;
ALTER TABLE collaboration_rating ADD COLUMN is_auto_completed BOOLEAN DEFAULT 0 NOT NULL;
ALTER TABLE collaboration_rating ADD COLUMN auto_completed_at DATETIME;
ALTER TABLE collaboration_rating ADD COLUMN auto_completion_reason TEXT;

