# main.py
import asyncio
import json
import pika
import sys
import os
import time

from pika.exceptions import AMQPConnectionError
from image_processor import processor
from dotenv import load_dotenv

def main():
    load_dotenv()
    credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
    parameters = pika.ConnectionParameters(
                host=os.environ['RABBITMQ_HOST'],
                port=os.environ['RABBITMQ_PORT'],
                credentials=credentials,
                heartbeat=60
                )

    global connection
    connection = pika.BlockingConnection(
            parameters=parameters,
            )

    channel = connection.channel()

    channel.queue_declare(queue=os.environ['RABBITMQ_QUEUE'])

    def callback(ch, method, properties, body):
        try:
            print(f" [x] Received {body}")
            data = json.loads(body.decode('utf-8'))
            asyncio.run(processor.handle_event(data))
            print('processed')
        except Exception as e:
            print(f"An error occurred while processing message: {e}")

    channel.basic_consume(
            queue=os.environ['RABBITMQ_QUEUE'],
            on_message_callback=callback,
            auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    while True:
        try:
            main()
        except AMQPConnectionError:
            time.sleep(10)
        except KeyboardInterrupt:
            print('Interrupted')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

