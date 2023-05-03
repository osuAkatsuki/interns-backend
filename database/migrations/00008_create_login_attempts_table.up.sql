CREATE TABLE login_attempts (
    login_attempt_id SERIAL NOT NULL PRIMARY KEY,
    successful BOOLEAN NOT NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON login_attempts (successful);
CREATE INDEX ON login_attempts (ip_address);
CREATE INDEX ON login_attempts (user_agent);
