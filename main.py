# main.py
import asyncio
import json
import pika
import sys
import os
from pika.adapters.asyncio_connection import AsyncioConnection
from surrealdb import Surreal
from image_processor import processor


def main():
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(
                host='127.0.0.1',
                credentials=credentials,
                heartbeat=60
                )

    parameters = pika.URLParameters("amqp://guest:guest@localhost:5672")

    global connection
    connection = pika.BlockingConnection(
            parameters=parameters,
            )

    channel = connection.channel()

    channel.queue_declare(queue='queue')

    def callback(ch, method, properties, body):
        try:
            print(f" [x] Received {body}")
            data = json.loads(body.decode('utf-8'))
            asyncio.run(processor.handle_event(data))
            print('processed')
        except Exception as e:
            print(f"An error occurred while processing message: {e}")

    channel.basic_consume(queue='queue', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()




if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

