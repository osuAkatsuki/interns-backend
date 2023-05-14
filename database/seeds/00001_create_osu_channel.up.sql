INSERT INTO channels (name, topic, read_privileges, write_privileges,
                      auto_join, temporary, created_at, updated_at)
VALUES ('#osu', 'General discussion', 0, 0, TRUE, FALSE, NOW(), NOW());
