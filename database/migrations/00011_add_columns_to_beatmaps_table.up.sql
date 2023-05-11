ALTER TABLE beatmaps ADD COLUMN bancho_ranked_status INT NOT NULL DEFAULT 0;
ALTER TABLE beatmaps ADD COLUMN bancho_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE beatmaps ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- since we haven't made any method for changing ranked statuses
-- on our server yet, we can assume that this is safe to do
UPDATE beatmaps SET bancho_ranked_status = ranked_status;
UPDATE beatmaps SET bancho_updated_at = updated_at;

ALTER TABLE beatmaps ALTER COLUMN bancho_ranked_status DROP DEFAULT;
ALTER TABLE beatmaps ALTER COLUMN bancho_updated_at DROP DEFAULT;
