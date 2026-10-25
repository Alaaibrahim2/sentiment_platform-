
import os
import json
import pika
from transformers import pipeline

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "sentiment")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "SentimentPass123!")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sentiment-queue")

print("Loading sentiment model...", flush=True)

sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    device=-1
)

print("Model loaded. Connecting to RabbitMQ...", flush=True)

credentials = pika.PlainCredentials(
    RABBITMQ_USER,
    RABBITMQ_PASSWORD
)

params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=5672,
    credentials=credentials,
    heartbeat=60,
    blocked_connection_timeout=30,
    connection_attempts=10,
    retry_delay=5
)

connection = pika.BlockingConnection(params)
channel = connection.channel()

channel.queue_declare(queue=QUEUE_NAME, durable=True)
channel.basic_qos(prefetch_count=1)


def process_message(ch, method, properties, body):
    try:
        message = json.loads(body)
        text = message["text"]

        result = sentiment_model(text)[0]

        print(
            json.dumps({
                "text": text,
                "sentiment": result["label"],
                "score": round(result["score"], 4)
            }),
            flush=True
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as error:
        print(f"Message processing failed: {error}", flush=True)

        # Reject the invalid message without requeueing it.
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )


channel.basic_consume(
    queue=QUEUE_NAME,
    on_message_callback=process_message
)

print(f"Waiting for messages in '{QUEUE_NAME}'...", flush=True)
channel.start_consuming()

