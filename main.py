# main.py
import asyncio
import json
import pika
import os

from image_processor import processor
from dotenv import load_dotenv

load_dotenv()
credentials = pika.PlainCredentials(os.environ['RABBITMQ_USERNAME'], os.environ['RABBITMQ_PASSWORD'])
parameters = pika.ConnectionParameters(
            host=os.environ['RABBITMQ_HOST'],
            port=os.environ['RABBITMQ_PORT'],
            credentials=credentials,
            heartbeat=60,
            socket_timeout=120
            )

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

threads = []

channel.basic_consume(
        queue=os.environ['RABBITMQ_QUEUE'],
        on_message_callback=callback,
        auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print('Interrupted')
    channel.stop_consuming()

# Wait for all to complete
for thread in threads:
    thread.join()

connection.close()
