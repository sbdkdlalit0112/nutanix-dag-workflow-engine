# Setup

To run the project locally:

1. Spin up a RabbitMQ server - preferably via a docker image.
Make sure to map the ports such that it is accessible from the host machine.

```bash
docker run -d --hostname rabbitmq-host --name rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
```

2. Clone the repo and open a terminal in the folder.

3. Create a python venv and activate it.

```bash
python3 -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

4. Start the main backend.

```bash
python server_main.py
```

5. Start some workers in other terminals (make sure to activate venv).

```bash
python worker_main.py
```

6. Go to `localhost:8000`. Follow the suggested link.

This project was developed in MacOS and hasn't been tested in other OS.