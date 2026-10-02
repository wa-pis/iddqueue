\set ON_ERROR_STOP on
\set schema 'dramatiq'
\set coordination 'coordination'

CREATE SCHEMA IF NOT EXISTS :"schema";
CREATE TABLE IF NOT EXISTS :"schema".:"coordination" (
    key TEXT PRIMARY KEY,
    value BIGINT NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT '-infinity',
    event_expires_at TIMESTAMPTZ NOT NULL DEFAULT '-infinity'
);
