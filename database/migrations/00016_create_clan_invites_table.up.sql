CREATE TABLE clan_invites (
    rec_id SERIAL NOT NULL PRIMARY KEY,
    clan_invite_id UUID NOT NULL,
    clan_id INT NOT NULL,
    uses INT NOT NULL DEFAULT 0,
    max_uses INT NULL,
    expires_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX ON clans (clan_invite_id);
CREATE UNIQUE INDEX ON clans (clan_id);