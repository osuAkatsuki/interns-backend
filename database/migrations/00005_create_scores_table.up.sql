CREATE TABLE scores (
    score_id SERIAL PRIMARY KEY,
    account_id INT NOT NULL,
    online_checksum TEXT NOT NULL,
    beatmap_md5 TEXT NOT NULL,
    score INT NOT NULL,
    performance_points DECIMAL(7, 3) NOT NULL,
    accuracy DECIMAL(6, 3) NOT NULL,
    highest_combo INT NOT NULL,
    full_combo BOOLEAN NOT NULL,
    mods INT NOT NULL,
    num_300s INT NOT NULL,
    num_100s INT NOT NULL,
    num_50s INT NOT NULL,
    num_misses INT NOT NULL,
    num_gekis INT NOT NULL,
    num_katus INT NOT NULL,
    grade TEXT NOT NULL DEFAULT 'N',
    submission_status INT NOT NULL,
    game_mode INT NOT NULL,
    play_time datetime NOT NULL,
    time_elapsed INT NOT NULL,
    client_anticheat_flags INT NOT NULL
);
CREATE INDEX ON scores (account_id);
CREATE INDEX ON scores (online_checksum);
CREATE INDEX ON scores (beatmap_md5);
CREATE INDEX ON scores (submission_status);
CREATE INDEX ON scores (game_mode);