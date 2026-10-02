CREATE TABLE IF NOT EXISTS :"schema".:"schedules" (
    schedule_id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name <> ''),
    message JSONB NOT NULL,
    interval_ms BIGINT NOT NULL CHECK (interval_ms > 0),
    next_run TIMESTAMPTZ NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS :"schedules_due" ON :"schema".:"schedules" (next_run) WHERE enabled;
