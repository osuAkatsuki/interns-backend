CREATE TABLE screenshots (
    screenshot_id UUID PRIMARY KEY,
    file_name TEXT UNIQUE NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    download_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON screenshots (file_type);
