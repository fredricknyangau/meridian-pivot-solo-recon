#!/usr/bin/env python
import os
import sys

import pika


def main():
    # connection with RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # create a queue
    channel.queue_declare(
        queue='hello',
        durable=True,
        arguments={'x-queue-type': 'quorum'}
        )

    # receive a message via exchange trhough callback function
    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")

    # consume messages from the queue
    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    # new message will be received and the callback function will be called
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
