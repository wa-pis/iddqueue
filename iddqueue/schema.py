import os.path

from .utils import quote_ident


def process_psql_lines(raw_lines, schema, prefix):
    schema = quote_ident(schema)
    tablename = quote_ident(prefix + "queue")
    statename = quote_ident(prefix + "state")

    for line in raw_lines:
        if line.startswith("\\"):
            continue
        yield (
            line.replace(':"schema"', schema)
            .replace(':"state"', statename)
            .replace(':"queue"', tablename)
            .replace(':"attempts"', quote_ident(prefix + "attempts"))
            .replace(':"attempts_message"', quote_ident(prefix + "attempts_message"))
            .replace(':"attempts_age"', quote_ident(prefix + "attempts_age"))
            .replace(':"coordination"', quote_ident(prefix + "coordination"))
            .replace(':"queue_control"', quote_ident(prefix + "queue_control"))
            .replace(':"deduplication"', quote_ident(prefix + "deduplication"))
            .replace(':"deduplication_expiry"', quote_ident(prefix + "deduplication_expiry"))
        )


def generate_init_sql(schema="dramatiq", prefix=""):
    """Returns SQL for schema initialisation

    Interpolate schema and prefix and return a single SQL string for execution
    on a PostgreSQL connection.
    """

    path = os.path.dirname(__file__) + "/schema.sql"
    with open(path) as fo:
        return "\n".join(process_psql_lines(fo, schema, prefix)) + "\n" + generate_upgrade_sql(schema, prefix)


def generate_coordination_sql(schema="dramatiq", prefix=""):
    """Idempotent upgrade for existing databases; leaves queue data intact."""
    path = os.path.join(os.path.dirname(__file__), "coordination.sql")
    with open(path) as fo:
        return "\n".join(process_psql_lines(fo, schema, prefix))


def generate_upgrade_sql(schema="dramatiq", prefix=""):
    """Add optional storage without changing existing queue data."""
    parts = [generate_coordination_sql(schema, prefix)]
    for name in ("deduplication.sql", "control.sql", "cancellation.sql", "history.sql"):
        with open(os.path.join(os.path.dirname(__file__), name)) as fo:
            parts.append("\n".join(process_psql_lines(fo, schema, prefix)))
    return "\n".join(parts)
