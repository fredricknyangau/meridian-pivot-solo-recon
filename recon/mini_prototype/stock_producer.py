#!/usr/bin/env python

import argparse
import json
import os
import uuid
from datetime import datetime, timezone

import pika

QUEUE_NAME = os.getenv("STOCK_QUEUE", "stock_updates")


def parse_args():
    parser = argparse.ArgumentParser(description="Publish a stock update event")
    parser.add_argument("--product-id", default="SKU-123")
    parser.add_argument("--stock-level", type=int, default=42)
    parser.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "localhost"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672"))
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Build the structured event that represents a warehouse stock change.
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "stock_updated",
        "product_id": args.product_id,
        "stock_level": args.stock_level,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(event).encode("utf-8")

    # Open a connection and channel to RabbitMQ before publishing the event.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=args.host, port=args.port)
    )
    try:
        channel = connection.channel()

        # Both producer and consumer declare the same durable queue. Quorum queues
        # keep queued messages available if the RabbitMQ server restarts.
        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )

        # Persistent delivery tells RabbitMQ to store this event on disk as well
        # as in memory, so it can survive a broker restart while waiting.
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        print(f" [x] Sent {json.dumps(event)}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
