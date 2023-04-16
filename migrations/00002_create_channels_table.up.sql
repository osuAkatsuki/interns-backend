CREATE TABLE channels
(
	channel_id SERIAL PRIMARY KEY,
	name TEXT NOT NULL,
	topic TEXT NOT NULL,
	read_privileges INT NOT NULL,
	write_privileges INT NOT NULL,
	auto_join BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX ON channels (name);
