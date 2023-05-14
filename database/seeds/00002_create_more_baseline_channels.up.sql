UPDATE channels SET write_privileges = 1 WHERE name = '#osu';

INSERT INTO channels (name, topic, read_privileges, write_privileges,
                      auto_join, temporary, created_at, updated_at)
VALUES ('#lobby', 'General multiplayer lobby chat.', 0, 1 << 0, TRUE, FALSE, NOW(), NOW()),
       ('#announce', 'Announcements from the server.', 1 << 9, 1 << 0, TRUE, FALSE, NOW(), NOW()),
       ('#help', 'Help and support.', 0, 1 << 0, TRUE, FALSE, NOW(), NOW()),
       ('#staff', 'Staff discussion.', 1 << 7 | 1 << 9 | 1 << 13 | 1 << 30, 1 << 7 | 1 << 9 | 1 << 13 | 1 << 30, TRUE, FALSE, NOW(), NOW()),
       ('#dev', 'Developer discussion.', 1 << 30, 1 << 0, TRUE, FALSE, NOW(), NOW());
