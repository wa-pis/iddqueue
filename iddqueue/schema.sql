\set ON_ERROR_STOP on
\set schema 'dramatiq'
\set state 'state'
\set queue 'queue'

CREATE SCHEMA IF NOT EXISTS :"schema";

CREATE TYPE :"schema".:"state" AS ENUM (
  'queued',
  'consumed',
  'rejected',
  'cancelled',
  'done'
);

CREATE TABLE :"schema".:"queue"(
  message_id uuid PRIMARY KEY,
  started BOOLEAN NOT NULL DEFAULT FALSE,
  cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
  queue_name TEXT NOT NULL DEFAULT 'default',
  "state" :"schema".:"state",
  mtime TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  -- message as encoded by dramatiq.
  message JSONB,
  "result" JSONB,
  result_ttl  TIMESTAMP WITH TIME ZONE
);

-- Index state and mtime together to speed up deletion. This can also speed up
-- statistics when VACUUM ANALYZE is recent enough.
CREATE INDEX ON :"schema".:"queue"("state", mtime);
