CREATE TABLE beatmaps (
	beatmap_id SERIAL NOT NULL,
	beatmap_set_id INT NOT NULL,
	ranked_status INT NOT NULL, -- enum
	beatmap_md5 TEXT NOT NULL,
	artist TEXT NOT NULL, -- TODO: ensure these support utf8?
	title TEXT NOT NULL, -- TODO: ensure these support utf8?
	version TEXT NOT NULL, -- TODO: ensure these support utf8?
	creator TEXT NOT NULL, -- TODO: ensure these support utf8?
	filename TEXT NOT NULL, -- TODO: ensure these support utf8?
	last_update TIMESTAMPTZ NOT NULL,
	total_length INT NOT NULL,
	max_combo INT NOT NULL,
	ranked_status_manually_changed BOOLEAN DEFAULT FALSE NOT NULL,
	plays INT DEFAULT 0 NOT NULL,
	passes INT DEFAULT 0 NOT NULL,
	mode INT DEFAULT 0 NOT NULL,
	bpm NUMERIC(12 ,2) DEFAULT 0.00 NOT NULL,
	cs NUMERIC(4, 2) DEFAULT 0.00 NOT NULL,
	ar NUMERIC(4, 2) DEFAULT 0.00 NOT NULL,
	od NUMERIC(4, 2) DEFAULT 0.00 NOT NULL,
	hp NUMERIC(4, 2) DEFAULT 0.00 NOT NULL,
	star_rating NUMERIC(6, 3) DEFAULT 0.000 NOT NULL
);
