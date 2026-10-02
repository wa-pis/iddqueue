CREATE TABLE IF NOT EXISTS :"schema".:"attempts" (
    attempt_id UUID PRIMARY KEY,
    message_id UUID NOT NULL,
    queue_name TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    finished_at TIMESTAMPTZ,
    outcome TEXT CHECK (outcome IN ('successful', 'failed')),
    error_type TEXT,
    error_text TEXT CHECK (length(error_text) <= 2000)
);
CREATE INDEX IF NOT EXISTS :"attempts_message" ON :"schema".:"attempts" (message_id, attempt_id);
CREATE INDEX IF NOT EXISTS :"attempts_age" ON :"schema".:"attempts" (started_at);
