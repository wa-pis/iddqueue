# Migrating from dramatiq-pg

This guide covers [dramatiq-pg 0.12.0](https://pypi.org/project/dramatiq-pg/0.12.0/)
to the published IDDQueue 0.13.0rc3 prerelease. See the [comparison](https://github.com/wa-pis/iddqueue/blob/main/README.md#compared-with-dramatiq-pg).
The original [DALIBO project](https://gitlab.com/dalibo/dramatiq-pg), credits and
[PostgreSQL license](https://github.com/wa-pis/iddqueue/blob/main/LICENSE) remain acknowledged.

## Prepare and rehearse

Record the current package versions, PostgreSQL database/role, schema, table
prefix, queue names, actor modules, custom encoder, middleware, pool settings
and result retention. The default storage stays `dramatiq.queue`; a prefix
`app_` selects `app_queue` and enum `app_state` in the selected schema.
Arbitrary table names must be mapped explicitly to `<prefix>queue`; do not
assume the CLI can select any table independently of the prefix.

Use Python 3.10+ and a supported PostgreSQL version (CI checks 14 and 18).
Create a separate environment for IDDQueue; Dramatiq changes from the upstream
1.x dependency range to 2.x. Review your actors/middleware and Dramatiq's own
upgrade requirements. The legacy [django-dramatiq-pg](https://github.com/uptick/django-dramatiq-pg/)
integration was archived on September 3, 2024 and is read-only. Compatibility
with IDDQueue is unverified; this migration guide does not establish Django support.

Make a database backup and retain the complete old environment/configuration.
For example, using libpq environment variables for the intended database:

```console
pg_dump --format=custom --file=before-iddqueue.dump
```

Verify restoration into a separate database before the production switch.
Rehearse the complete process there with representative queued, delayed,
rejected and result-bearing rows. Keep the same message IDs, actor names and
encoder. Check queue counts, sample payloads/results and timestamp semantics;
the old schema's timestamp default depends on the session timezone. This
upgrade does not reinterpret historical timestamps.

The upstream SQL contains `WITHOUT OIDS`, which modern PostgreSQL no longer
accepts. Existing tables do not require recreation. For a rehearsal fixture
on PostgreSQL 14/18, remove that obsolete clause from the upstream DDL only.

## Change the application environment

Install the published release candidate in a fresh environment:

```console
uv venv
uv pip install "iddqueue[binary]==0.13.0rc3"
iddqueue --version
```

Replace imports from `dramatiq_pg` with `iddqueue` (including submodules), and
replace deployment/maintenance commands `dramatiq-pg` with `iddqueue`.
Worker launch remains Dramatiq's normal command for your actor module.
Use a dedicated environment so the old installation remains available for rollback.

Psycopg 2 pools are unsupported. Prefer a broker-owned Psycopg 3 pool:

```python
import dramatiq
from iddqueue import PostgresBroker

broker = PostgresBroker(url="", schema="dramatiq", prefix="")
dramatiq.set_broker(broker)
# Import/declare actors after configuring the broker.
# On application shutdown: broker.close()
```

An empty URL uses libpq environment configuration. For explicit caller-owned
pools, use `psycopg_pool.ConnectionPool` with `autocommit=True` and close that
pool yourself. Keep schema/prefix identical on broker, results, coordination,
metrics, scheduler and CLI. UUIDs remain result keys; namespace-prefixed string
keys are unsupported. Update any existing IDDQueue preview dashboards from
`dramatiq_pg_queue_` to `iddqueue_queue_`; upstream 0.12.0 had no such collector.

## Switch the database area

1. Stop producers and schedulers. Drain running work where possible, then
   gracefully stop all workers and result waiters. Check for remaining old
   sessions before changing the area. Do not mix old and new participants,
   including applications that share the same storage.
2. Take the final consistent backup after participants stop. Upgrade the
   existing area using the new environment and the same connection settings:

   ```console
   iddqueue --schemaname dramatiq --prefix '' upgrade
   ```

   For a different schema/prefix, substitute both explicitly. Use `upgrade`
   for existing storage, not `init`. It adds feature tables, the `cancelled`
   enum value, and `started`/`cancel_requested` columns without deleting queue
   rows or results. It does not rename your schema, table or message IDs.
3. Check preserved row counts/payloads/results, role grants and the new objects.
   An upgrade run by a migration role does not automatically grant the worker
   role access to every newly created table. Apply your application's grants.
4. Start workers/result readers with matching new configuration, then producers
   and schedulers. Existing queued tasks are recovered from SQL. Validate a
   queued task, its result and a rejected-task retry before resuming full traffic.

`flush` and `purge` delete data and are not migration steps. Delivery remains
at least once, so a crash/restart may repeat an actor. Delayed tasks retain
their stored ETA; verify clocks and timezone configuration in the rehearsal.
Non-default schema/prefix areas and long channel names have new notification
and advisory-lock domains; restarting every participant together is required.

## Rollback

Stop all new participants first. Restore the pre-switch backup into the intended
rollback database, restore the old package environment and configuration, check
the queue/result contents and grants, then restart the old participants together.
Test restoration in an isolated database before relying on this procedure.

Do not simply run the old broker against upgraded live data: it does not
understand new cancellation states or optional feature semantics. Restoring
the backup loses post-switch writes; capture and reconcile them deliberately
if traffic has resumed. There is no automatic reverse migration or replay.

## Security and limits

Schema/prefix separation is storage routing, not tenant authorization. Use
PostgreSQL roles and deployment controls. Task notifications now contain only `message_id`; arguments/options remain in
SQL storage. Update **every producer, scheduler and worker**, including ACK/NACK
publishers, to the fixed revision before considering the disclosure closed.
No DDL migration is required for this fix. Legacy full hints are still accepted,
but old publishers continue exposing data while running. Custom LISTEN clients
must fetch task content from authorized SQL storage by ID. UUIDs and activity
timing remain visible to listeners in the same database. Rolling back to an
unfixed revision restores the disclosure.

Deduplication suppresses publication, not repeated execution. Cancellation is
cooperative after task start. The scheduler supports fixed intervals, not cron;
actor priority is local to the Dramatiq worker, not a global PostgreSQL scheduler.

## Manage schema through application migrations

The broker never creates or upgrades tables automatically. `iddqueue init` and
`iddqueue upgrade` perform DDL only when explicitly invoked. No `auto_migrate`
or `skip_migration` option is needed.

Choose either the CLI or your application migration runner to apply DDL. For a
new, empty namespace, execute the generated SQL through your migration connection:

```python
from iddqueue import generate_init_sql

# Run inside your migration runner's transaction, using its connection.
connection.execute(generate_init_sql(schema="dramatiq", prefix=""))
```

This example uses a Psycopg connection. Other runners must execute the returned
PostgreSQL SQL through their own driver; generation performs no database I/O.
For a supported existing installation, use `generate_upgrade_sql(schema, prefix)`
instead. `generate_init_sql` is not an upgrade script for populated storage.

Configure the broker with the same `schema` and `prefix`. Creating an arbitrary
queue table is insufficient: required types, columns, indexes and auxiliary
objects must match the package SQL. Apply migrations before starting producers
and workers. Use a migration role for DDL and grant the runtime role the needed
schema usage and data access rights; runtime does not require schema CREATE.
Missing storage produces a PostgreSQL error, with no automatic repair.

Updating **IDDQueue RC2 to RC3 requires no DDL**: Domain uses existing queue and
actor names. This does not guarantee migration-free upgrades for future versions
or replace the migration steps from legacy dramatiq-pg above.
