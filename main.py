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
channel.queue_declare(queue='object_detected')

channel.queue_declare(queue=os.environ['RABBITMQ_QUEUE'])

def callback(ch, method, properties, body):
    try:
        print(f" [x] Received {body}")
        data = json.loads(body.decode('utf-8'))
        asyncio.run(processor.handle_event(data))
        print('processed')
    except Exception as e:
        print(f"An error occurred while processing message: {e}")

def detect_event(ch, method, properties, body):
    try:
        print(f" [x] Received {body} --- on object_detected")
        data = json.loads(body.decode('utf-8'))
        asyncio.run(processor.detect_event(data))
        print('processed')
    except Exception as e:
        print(f"An error occurred while processing message: {e}")

channel.basic_consume(
        queue='object_detected',
        on_message_callback=detect_event,
        auto_ack=True)


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

connection.close()
