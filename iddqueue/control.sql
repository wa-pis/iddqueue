\set schema 'dramatiq'
\set queue_control 'queue_control'
CREATE TABLE IF NOT EXISTS :"schema".:"queue_control" (
    queue_name TEXT PRIMARY KEY,
    paused BOOLEAN NOT NULL DEFAULT FALSE
);
