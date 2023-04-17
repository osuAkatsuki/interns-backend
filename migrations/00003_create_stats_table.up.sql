CREATE TABLE stats (
    account_id SERIAL NOT NULL,
    game_mode INT NOT NULL,
    total_score BIGINT DEFAULT 0 NOT NULL,
    ranked_score BIGINT DEFAULT 0 NOT NULL,
    performance_points INT DEFAULT 0 NOT NULL,
    play_count INT DEFAULT 0 NOT NULL,
    play_time INT DEFAULT 0 NOT NULL,
    accuracy NUMERIC(6,3) DEFAULT 0.000 NOT NULL,
    highest_combo INT DEFAULT 0 NOT NULL,
    total_hits INT DEFAULT 0 NOT NULL,
    replay_views INT DEFAULT 0 NOT NULL,
    xh_count INT DEFAULT 0 NOT NULL,
    x_count INT DEFAULT 0 NOT NULL,
    sh_count INT DEFAULT 0 NOT NULL,
    s_count INT DEFAULT 0 NOT NULL,
    a_count INT DEFAULT 0 NOT NULL,
    PRIMARY KEY (account_id, game_mode)
);
