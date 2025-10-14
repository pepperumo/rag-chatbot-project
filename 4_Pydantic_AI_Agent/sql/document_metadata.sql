-- Create a table to store document metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    url TEXT,
    schema TEXT
);
