CREATE TABLE achievements (
    achievement_id SERIAL NOT NULL,
    file_name TEXT NOT NULL,
    achievement_name TEXT NOT NULL,
    achievement_description TEXT NOT NULL
);
CREATE INDEX ON achievements (file_name);
