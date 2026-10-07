"""RC5 API: atomic async publication, isolated schema and cleanup."""

import asyncio
import os
from uuid import uuid4

import dramatiq
import psycopg
from psycopg import sql

from iddqueue import PostgresBroker, generate_init_sql


async def main():
    if os.environ.get('IDDQUEUE_TEST_DATABASE') != 'dedicated':
        raise RuntimeError('Set IDDQUEUE_TEST_DATABASE=dedicated for this isolated example')
    schema = 'async_recipe_' + uuid4().hex
    broker = PostgresBroker(schema=schema)
    worker = None
    async with await psycopg.AsyncConnection.connect('', autocommit=True) as connection:
        try:
            await connection.execute(generate_init_sql(schema))
            await connection.execute(sql.SQL('CREATE TABLE {} (id uuid PRIMARY KEY)').format(
                sql.Identifier(schema, 'orders')))

            @dramatiq.actor(broker=broker, store_results=True)
            def receipt(order_id):
                return order_id

            order_id = str(uuid4())
            async with connection.transaction():
                await connection.execute(sql.SQL('INSERT INTO {} VALUES (%s)').format(
                    sql.Identifier(schema, 'orders')), (order_id,))
                message = await broker.enqueue_in_transaction_async(
                    receipt.message(order_id), connection=connection,
                    deduplication_key=order_id, deduplication_ttl=60000)
            worker = dramatiq.Worker(broker, worker_threads=1, worker_timeout=100)
            await asyncio.to_thread(worker.start)
            result = await asyncio.to_thread(
                message.get_result, backend=broker.backend, block=True, timeout=10000)
            assert result == order_id
            print('Async transaction verified: business commit and actor result')
        finally:
            try:
                if worker is not None:
                    await asyncio.to_thread(worker.stop)
                    await asyncio.to_thread(worker.join)
            finally:
                broker.close()
                await connection.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(
                    sql.Identifier(schema)))
    print('Async recipe cleanup complete:', schema)


if __name__ == '__main__':
    asyncio.run(main())
