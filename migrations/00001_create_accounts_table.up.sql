CREATE TABLE accounts (
	account_id SERIAL PRIMARY KEY,
	username TEXT NOT NULL,
	email_address TEXT NOT NULL,
	privileges INT NOT NULL,
	password TEXT NOT NULL,
	country TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ON accounts (username);
CREATE UNIQUE INDEX ON accounts (email_address);
