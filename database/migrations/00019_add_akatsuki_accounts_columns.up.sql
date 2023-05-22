ALTER TABLE accounts ADD COLUMN restricted_at TIMESTAMPTZ NULL;
ALTER TABLE accounts ADD COLUMN silence_reason TEXT NULL;

-- not 100% sure we'll need this, but adding for now nonetheless
ALTER TABLE accounts ADD COLUMN freeze_reason TEXT NULL;
