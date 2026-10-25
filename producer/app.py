
import os
import json
import pika

from flask import Flask, request, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "sentiment")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "SentimentPass123!")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sentiment-queue")

REQUESTS = Counter(
    "sentiment_requests_total",
    "Total requests received by the API"
)

ENQUEUED = Counter(
    "sentiment_requests_enqueued_total",
    "Total messages successfully published to RabbitMQ"
)

PUBLISH_ERRORS = Counter(
    "sentiment_publish_errors_total",
    "Total failed RabbitMQ publishing attempts"
)


def publish_message(text):
    credentials = pika.PlainCredentials(
        RABBITMQ_USER,
        RABBITMQ_PASSWORD
    )

    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=10
    )

    connection = pika.BlockingConnection(params)

    try:
        channel = connection.channel()

        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True
        )

        channel.confirm_delivery()

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps({"text": text}),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json"
            )
        )
    finally:
        connection.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


@app.post("/predict")
def predict():
    REQUESTS.inc()

    data = request.get_json(silent=True) or {}
    text = data.get("text")

    if not isinstance(text, str) or not text.strip():
        return jsonify({
            "error": "Provide a non-empty text field"
        }), 400

    try:
        publish_message(text.strip())
        ENQUEUED.inc()

        return jsonify({
            "status": "queued",
            "text": text.strip()
        }), 202

    except Exception:
        PUBLISH_ERRORS.inc()
        app.logger.exception("RabbitMQ publishing failed")

        return jsonify({
            "error": "Failed to publish message"
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

