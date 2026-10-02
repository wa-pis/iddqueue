\set schema 'dramatiq'
\set deduplication 'deduplication'
CREATE TABLE IF NOT EXISTS :"schema".:"deduplication" (
    queue_name TEXT NOT NULL,
    key TEXT NOT NULL,
    message_id UUID NOT NULL,
    message JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (queue_name, key)
);
CREATE INDEX IF NOT EXISTS :"deduplication_expiry"
    ON :"schema".:"deduplication" (expires_at);
