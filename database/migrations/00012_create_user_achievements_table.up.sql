CREATE TABLE user_achievements (
    achievement_id INT NOT NULL,
    account_id INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (achievement_id, account_id)
);
