# main.py
import asyncio
import json
import pika
import sys
import os

from pika.adapters.asyncio_connection import AsyncioConnection

from surrealdb import Surreal

from image_processor import processor


async def main():
    credentials = pika.PlainCredentials('guest', 'guest')

    global connection
    connection = AsyncioConnection(
            parameters=pika.ConnectionParameters(
                host='localhost',
                credentials=credentials,
                ),
            on_open_callback=on_connect
            )

    connection.ioloop.run_forever()


def on_connect():
    channel = connection.channel()
    channel.queue_declare(queue='queue')

    async def callback(ch, method, properties, body):
        try:
            async with Surreal("ws://108.61.195.50:8000/rpc") as db:
                await db.signin({"user": "root", "pass": "root"})
                await db.use("test", "test")
            print(f" [x] Received {body}")
            data = json.loads(body.decode('utf-8'))
            await processor.handle_event(data, db)
            print('processed')
        except Exception as e:
            print(f"An error occurred while processing message: {e}")

    channel.basic_consume(queue='queue', on_message_callback=callback, auto_ack=True)



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

