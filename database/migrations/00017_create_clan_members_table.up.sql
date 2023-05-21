CREATE TABLE clan_members (
    clan_id INT NOT NULL,
    account_id INT NOT NULL,
    privileges INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (clan_id, account_id)
);
CREATE INDEX ON clan_members (privileges);
