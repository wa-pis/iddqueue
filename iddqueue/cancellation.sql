\set schema 'dramatiq'
\set state 'state'
\set queue 'queue'
ALTER TYPE :"schema".:"state" ADD VALUE IF NOT EXISTS 'cancelled';
ALTER TABLE :"schema".:"queue" ADD COLUMN IF NOT EXISTS started BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE :"schema".:"queue" ADD COLUMN IF NOT EXISTS cancel_requested BOOLEAN NOT NULL DEFAULT FALSE;
