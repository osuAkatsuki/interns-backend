CREATE TYPE RelationshipEnum AS ENUM('friend', 'blocked');

CREATE TABLE relationships (
    account_id INT NOT NULL,
    target_id INT NOT NULL,
    relationship RelationshipEnum NOT NULL,
    PRIMARY KEY (account_id, target_id)
);
CREATE INDEX ON relationships (account_id);
CREATE INDEX ON relationships (target_id);
