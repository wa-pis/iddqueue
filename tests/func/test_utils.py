from iddqueue.utils import (
    getconn,
    transaction,
    wait_for_notifies,
)
from tests.func.actors import pool


def test_subscription_isolation(pgconn):
    """Ensure that subscriptions don't leak."""
    conn = getconn(pool)

    channel_1_name = "channel_1"
    channel_2_name = "channel_2"

    def send_notification(channel):
        with pgconn() as cur:
            cur.execute("select pg_notify(%s, '123')", (channel,))

    def get_listening_channels(conn):
        cur = conn.cursor()
        cur.execute("select * from pg_listening_channels()")
        return [r[0] for r in cur.fetchall()]

    with transaction(conn, listen=channel_1_name):
        send_notification(channel_1_name)
        send_notification(channel_2_name)  # should be ignored

        notifies_1 = wait_for_notifies(conn, timeout=1)
        channels_1 = get_listening_channels(conn)

    with transaction(conn, listen=channel_2_name):
        send_notification(channel_1_name)  # should be ignored
        send_notification(channel_2_name)

        notifies_2 = wait_for_notifies(conn, timeout=1)
        channels_2 = get_listening_channels(conn)

    assert channels_1 == [channel_1_name]
    assert channels_2 == [channel_2_name]
    assert [n.channel for n in notifies_1] == [channel_1_name]
    assert [n.channel for n in notifies_2] == [channel_2_name]

    pool.putconn(conn)
