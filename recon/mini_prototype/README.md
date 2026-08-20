# Mini-Prototype - Stock Update Event Queue

## What This Demonstrates

This applies what I learned during Days 1-2 solo recon  to a scenario closer to this week 2 sprint's actual problem: reliably processing stock/inventory-update events without losing them if a consumer fails partway through processing.

Where the earlier recon work (`hello_world/`, `work_queues/`) followed the official tutorials  to learn the concepts, this prototype combines those concepts into something that resembles a real use case, structured event data and message safety instead of just message delivery.

## What It Does

- **`stock_producer.py`** - publishes structured stock-update events to a queue.
- **`stock_consumer.py`** - receives each event, simulates processing it, and only confirms receipt to RabbitMQ (`ack`) once that processing has genuinely finished.
- The queue is declared **durable**, so events are not lost even if the RabbitMQ server itself restarts while messages are still waiting to be picked up.

## How This Differs From the Tutorial Examples

- **Realistic payload:** instead of the string `"Hello World!"`, the producer sends a structured message representing a stock update.
- **Durability:** the queue is marked durable, I tested by restarting the RabbitMQ container and confirming a message sent before the restart was still there after.
- **Manual acknowledgment, tested under failure:** rather than just implementing `ack` and trusting it works, I Killed the consumer on mid-processing to confirm RabbitMQ actually re-queues the unacknowledged message and delivers it again.

## How to Run

Activate the project virtual environment first:

```bash
source .venv/bin/activate
```

The scripts use `localhost:5672`

1. Start RabbitMQ (via Docker):

   ```bash
   docker run -d --name rabbitmq1 -p 5672:5672 -p 15672:15672 rabbitmq:management
   ```

2. Terminal 1 - start the consumer:

   ```bash
   python recon/mini_prototype/stock_consumer.py
   ```

3. Terminal 2, run the producer to send a stock-update event:

   ```bash
   python recon/mini_prototype/stock_producer.py
   ```

4. **Expected output:**

   ```text
   [*] Waiting for stock updates. To exit press CTRL+C
   [x] Sent {"event_id": "...", "event_type": "stock_updated", "product_id": "SKU-123", "stock_level": 42, "updated_at": "..."}
   [x] Received {"event_id": "...", "event_type": "stock_updated", "product_id": "SKU-123", "stock_level": 42, "updated_at": "..."}
   [x] Processed event ...
   ```

   Publish a different event with:

   ```bash
   python recon/mini_prototype/stock_producer.py --product-id SKU-456 --stock-level 8
   ```

## Durability Test - What I Did to Verify It

The queue is declared durable and each message is published as persistent.

## Acknowledgment Test - What I Did to Verify It

I start the consumer with `python recon/mini_prototype/stock_consumer.py --delay 10 --fail-before-ack`,
published an event, and allowed the simulated failure to stop the consumer. Because
the consumer never sends `ack`, RabbitMQ re-queues the unacknowledged event when
the connection closes. Restart the consumer without `--fail-before-ack` and the
same event is delivered and acknowledged.
