#!/usr/bin/env python

import argparse
import json
import os
import time

import pika

QUEUE_NAME = os.getenv("STOCK_QUEUE", "stock_updates")


def parse_args():
    parser = argparse.ArgumentParser(description="Process stock update events")
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--fail-before-ack", action="store_true")
    parser.add_argument("--host", default=os.getenv("RABBITMQ_HOST", "localhost"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("RABBITMQ_PORT", "5672"))
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Open a connection and channel so this process can receive stock events.
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=args.host, port=args.port)
    )
    channel = connection.channel()

    # The declaration is idempotent, so the consumer can safely ensure the
    # durable queue exists without depending on the producer starting first.
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={"x-queue-type": "quorum"},
    )

    # Only give this consumer one unacknowledged event at a time. This prevents
    # work from building up in a consumer that is still processing one event.
    channel.basic_qos(prefetch_count=1)
    print(" [*] Waiting for stock updates. To exit press CTRL+C")

    def process_event(ch, method, properties, body):
        try:
            # Decode the JSON payload before simulating the work of a real
            # inventory service, such as writing the update to a database.
            event = json.loads(body.decode("utf-8"))
            print(f" [x] Received {json.dumps(event)}")
            time.sleep(args.delay)

            if args.fail_before_ack:
                print(" [!] Simulated failure before ack; message will be re-queued")
                raise RuntimeError("simulated processing failure")

            # Acknowledge only after processing finishes. If the consumer dies
            # before this line, RabbitMQ can deliver the event again.
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f" [x] Processed event {event['event_id']}")
        except (json.JSONDecodeError, KeyError) as error:
            print(f" [!] Rejecting malformed event: {error}")

            # A malformed event cannot be fixed by retrying, so discard it rather
            # than allowing it to loop forever in the queue.
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    # Register the callback, then block while RabbitMQ delivers events to it.
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_event)
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
