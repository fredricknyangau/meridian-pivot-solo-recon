#!/usr/bin/env/ python

import pika

# connection with RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# create a queue
channel.queue_declare(queue='hello', durable=True, arguments={'x-queue-type': 'quorum'})

# send a message via exchange
channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
print(" [x] Sent 'Hello World!'")

# close the connection
connection.close()
