ALTER TABLE beatmaps DROP COLUMN created_at;
ALTER TABLE beatmaps DROP COLUMN bancho_updated_at;
ALTER TABLE beatmaps DROP COLUMN bancho_ranked_status;
ALTER TABLE beatmaps ALTER COLUMN updated_at DROP DEFAULT;
