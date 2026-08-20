# Learning & Blocker Journal - Solo Recon (Days 1-2)

## The Meridian Pivot - Assignment 1

**Chosen tool:** RabbitMQ (Message Queues)
**Time-box:** Not stated in the documents or by the instructor on the call. I worked within my own disciplined time window and logged the real time honestly.
**Start time:** Day 2, 9:30 PM

---

## Why This Tool

I chose RabbitMQ because it is genuinely new to me and not part of my current stack (FastAPI, PostgreSQL, Redis, Docker, Nginx).

---

## Day 1 - Preparation & Setup

I received the assignment email and opened the guide. I read through the tool options and picked one based on what I genuinely did not know yet, compared to my own stack.

I waited for the scheduled call before doing any hands-on work, since the brief had some unclear parts (later made clear: this is an individual assignment, honesty in tool choice matters, and the work is individual from Day 3). I used the call to confirm these things instead of guessing and possibly wasting Day 1-2 time on a wrong assumption.

After the call, I got my environment ready: created the solo recon repository, set up the first project structure, and confirmed RabbitMQ as my final tool choice.

No hands-on technical work (installing, coding) happened on Day 1. That started on Day 2 at 9:30 PM, shown below.

---

## Resources Consulted

- RabbitMQ official documentation (Getting Started / "Hello World" tutorial, Python client)
- RabbitMQ official documentation (Work Queues tutorial)
- Pika (Python client library for RabbitMQ) official docs
- Docker Hub - `rabbitmq:management` image

---

## Concepts Learned (Terminology Log)

### From Hello World
- **Message Queue (RabbitMQ):** A tool that accepts and forwards messages. Works like a "post office" between services.
- **Messaging and streaming broker:** This is RabbitMQ's main job in a system.
- **Common use cases:**
  - Decoupling services that talk to each other - helps absorb load spikes, and lets two notification channels run without depending on each other.
  - Remote Procedure Call (RPC) pattern - many clients/websites calling into one backend service.
- **Producer (P):** Sends messages into a queue.
- **Queue:** A named "post box," limited by the host's memory and disk space.
- **Consumer (C):** Receives messages from a queue.
- **`queue_declare` is idempotent:** calling it many times will not create many queues. Only one queue is ever made. This makes it safe to call it just to be sure the queue exists.
- **Used the raw Python client (Pika) directly, not a framework** - I did this on purpose, to understand how the tool actually works before using any higher-level shortcut.

### From Work Queues (Day 2, continued)
- **Work Queues / Task Queues:** Used to spread out time-consuming tasks across many workers.
- **Main idea:** Avoid doing a heavy task right away and making something wait for it to finish. Instead, turn the task into a message, send it to a queue, and let a background worker pick it up and run it later.
- **Many workers = shared tasks.** This is useful when a task is too heavy to handle inside a short HTTP request.
- **Round-robin dispatch:** By default, RabbitMQ sends each new message to the next consumer in line. If tasks are spread evenly, every consumer ends up doing roughly the same amount of work over time.
- **Task Queue advantage:** it makes it easy to parallelize work across many workers.
- **Message acknowledgment (ack):** When RabbitMQ sends a message to a consumer, it normally marks that message for deletion right away. If the worker dies before finishing the task, that message and its work are lost. The fix is manual acknowledgment: the consumer tells RabbitMQ "I'm done" only after the task is actually finished. If the consumer dies before sending that confirmation, RabbitMQ knows the task was not finished and puts the message back in the queue for another consumer. There is a default 30-minute limit for a consumer to send this confirmation.
- **Message durability:** If the RabbitMQ server itself stops or restarts, it will forget all queued messages by default. To stop this from happening, the queue itself must be marked as durable.

---

## Blocker Log

### Blocker 1: RabbitMQ server installation - wrong OS version supported

- **Tried:** Installing RabbitMQ directly on my machine, following the official install docs.
- **Result/error:** The official install docs only support Ubuntu 22.04. My machine runs Ubuntu 26.04.
- **Next idea:** Skip the OS problem completely by running RabbitMQ inside Docker instead of installing it directly.
- **Time spent:** About 20 minutes (research + deciding to use Docker).
- **How I fixed it:** Pulled the `rabbitmq:management` image and ran it as a container:

  ```bash
  docker pull rabbitmq:management

  docker run -d \
    --name rabbitmq1 \
    -p 5672:5672 \
    -p 15672:15672 \
    rabbitmq:management
  ```

  I confirmed the server was running by logging into the RabbitMQ management web page.

- **Rule of 30 checkpoint:** Yes. I noticed the OS mismatch quickly through research, instead of repeating the same broken install over and over, and moved to Docker in well under 30 minutes.

### Blocker 2: No pip installed - needed it for the Python client (Pika)

- **Tried:** Running `python -m pip install pika --upgrade` to install the Python client library.
- **Result/error:** `pip` was not installed on my system.
- **Next idea:** Use a Python virtual environment, since it comes with its own `pip` automatically, instead of depending on a system-wide install.
- **Time spent:** About 10 minutes.
- **How I fixed it:** Created and activated a virtual environment (`python -m venv .venv` then `source .venv/bin/activate`), which gave me a working `pip` inside it. Installed Pika from there with `pip install pika`.
- **Rule of 30 checkpoint:** Yes. Solved well within 30 minutes using a pattern I already knew (venv comes with pip), instead of fighting the system-level install.

### Blocker 3: Round-robin dispatch - ran the file from the wrong folder

- **Tried:** Testing round-robin dispatch by opening 3 terminals, 2 running `worker.py` (as two consumers) and 1 for publishing new tasks.
- **Result/error:** I ran the worker file from a different folder than the project folder, so it did not behave as expected.
- **Next idea:** Switch to the correct project folder before running the file again.
- **Time spent:** ~5 min since it was only changing the working directory.
- **How I fixed it:** Moved into the correct folder and ran the worker again, it worked as expected.
- **Rule of 30 checkpoint:** Yes, this was a quick fix once I noticed the folder was wrong.

### Blocker 4: Publishing a new task - channel name error

- **Tried:** Running/publishing a new task after setting up the work queue.
- **Result/error:** Got a name error connected to the channel.
- **Next idea:** Check how the channel is named in the file that publishes new tasks.
- **Time spent:** Spent almost 20 min since it was new fix for me
- **How I fixed it:** Fixed the channel name in the `new_task.py` file so it correctly referenced `"channel"`.
- **Rule of 30 checkpoint:** Yes, it was not a quick fix once I saw the name error.

---

## Hello World Walkthrough

**Goal:** Producer (P) sends a message into a queue named `hello`; Consumer (C) receives it.

```
(P) --> [ hello queue ] --> (C)
         Producer            Consumer
```

### `send.py` - Steps
1. Connect to the RabbitMQ server.
2. Create / declare the queue.
3. Send the message.
4. Close the connection.

### `receive.py` - Steps
1. Connect to the server again (a separate connection from the producer).
2. Declare the queue. Since `queue_declare` is idempotent, this safely makes sure the queue exists without creating a duplicate.
3. Start the **consumer** first, before the **producer** sends anything, so it is ready and listening.
4. **Output:** message successfully sent and received.

### Confirmed Output

```
$ python send.py
 [x] Sent 'Hello World!'

$ python receive.py
 [*] Waiting for messages. To exit press CTRL+C
 [x] Received b'Hello World!'
```

---

## Work Queues Walkthrough (Day 2, continued)

**Goal:** Spread tasks across multiple workers instead of doing them one at a time, and make sure a task is not lost if a worker dies mid-task.

### Task Simulation
Changed `send.py` so it can send any message typed from the command line (CLI), instead of a fixed string. Used the number of dots in the message to represent how "complex" or long the task is, paired with `time.sleep()` in the worker to act out real processing time.

### Round-Robin Dispatch Test
Opened 3 terminals: two running `worker.py` (two separate consumers) and one for publishing new tasks. Confirmed that RabbitMQ, by default, sends each new message to the next consumer in line, so over time both consumers get roughly the same number of tasks.

### Message Acknowledgment
**Question I looked into:** what happens if a consumer starts a long task and dies before it finishes?

Without acknowledgment, RabbitMQ marks a message as done (safe to delete) the moment it hands it to a consumer. If that consumer dies mid-task, the message and the unfinished work are simply lost.

**Fix - manual acknowledgment (ack):** the consumer sends a message back to RabbitMQ once it is truly finished processing, only then does RabbitMQ delete it. If the consumer dies before sending that confirmation, RabbitMQ notices the task was not finished and puts the message back in the queue. If another consumer is online, it gets delivered to that one instead. There is a default 30-minute limit for how long a consumer can take before confirming.

### Message Durability
**Question I looked into:** what happens to messages sitting in a queue if the RabbitMQ server itself stops?

By default, the server forgets everything. To stop this, the queue needs to be explicitly marked as durable so messages survive a server restart.

---

## Mini-Prototype Scope

**What I set out to build:**
- A producer that sends a message standing in for a "stock updated" event
- A consumer that receives and processes that message
- Basic acknowledgment handling, so a message is not lost if the consumer fails mid-task

## Note on Mini-Prototype Origin

The `quorum` queue type and `basic_qos(prefetch_count=1)` pattern used in the mini-prototype came directly from the official Work Queues tutorial, the same source cited above, not introduced separately. The mini-prototype extends this base (durable quorum queue, manual ack, prefetch limiting) with a structured JSON event payload, CLI arguments for testing different scenarios, and a deliberate `--fail-before-ack` flag used specifically to verify RabbitMQ's re-queue behavior under failure, going beyond what the tutorial itself covers.

**Final status as of end of Day 2:**
- [x] RabbitMQ server running (via Docker)
- [x] Core concepts (producer / queue / consumer, idempotent queue declaration) understood
- [x] `send.py` and `receive.py` built and tested (Hello World)
- [x] Full end-to-end message sent and received, confirmed working
- [x] Task queue built and tested with variable-length simulated tasks
- [x] Round-robin dispatch tested across multiple consumers, confirmed working
- [x] Manual acknowledgment (ack) understood and connected to real re-delivery behavior
- [x] Message durability understood (queues must be marked durable to survive a server restart)

**What this means:**
My original target (producer, consumer, basic acknowledgment handling) has been fully met, and I went further by also testing round-robin dispatch across multiple workers and understanding message durability, both of which are directly useful for a future service that needs to reliably process inventory-update events without losing them.

---

## Time-to-Completion

- **Time-boxed allowance:** Not stated in the documents or by the instructor. I used my own judgment on a reasonable amount of time, and logged my real hours honestly instead of guessing at a limit.
- **Actual time spent:** 2 hours on Hello World (Day 2, 9:30 PM - 11:30 PM), plus additional time on Work Queues the same day ( from 12:00 am to around 2:00 am).
- **Where most time went:** Getting the environment working (Ubuntu/RabbitMQ install mismatch, fixing it with Docker; missing pip, fixed with a virtual environment) took a good part of the early time, before I could test anything RabbitMQ-specific. Once the environment worked, both Hello World and Work Queues moved faster.

---

## Final Reflection

I understand how a message broker keeps a producer and a consumer separate from each other, they do not need to run at the same time or know about each other directly. The queue sits in between and holds the message until it is picked up. I also understand why `queue_declare` being idempotent matters, it lets both sides safely make sure the queue exists without worrying about who creates it first or causing an error by declaring it twice.

I now understand how work queues let you spread tasks across many workers, how round-robin dispatch spreads that work out evenly, how manual acknowledgment stops a task from being lost if a worker dies mid-way, and why a queue needs to be marked durable if it should survive the RabbitMQ server restarting.


**Honest note on any moment I was tempted to fake confidence or skip logging a struggle:**
No. Every real blocker I hit, the Ubuntu install mismatch, the missing pip, the wrong folder, and the channel name error, was written down as it happened, not remembered and written up afterward. None of them took very long to fix, but each one was a real point where my first attempt did not work and I had to actually stop, think, and try something different, which is exactly why I logged them instead of only writing about what worked in the end.
