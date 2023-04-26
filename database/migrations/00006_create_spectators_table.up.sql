CREATE TABLE spectators 
(
    account_id INT NOT NULL,
    target_id INT NOT NULL,
    currently_spectating BOOLEAN NOT NULL
    PRIMARY KEY (account_id, target_id)
);

CREATE INDEX ON spectators (account_id)
CREATE INDEX ON spectators (target_id)
