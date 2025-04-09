import pika  # type: ignore
import json

from workflow_utils import Task


class TaskQueue:
    def __init__(self, queue_name="job_queue", host="localhost"):
        self.queue_name = queue_name
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_purge(queue=queue_name)
        self.channel.queue_declare(queue=queue_name, durable=True)

    def send_task(self, task: Task):
        message = task.to_json()
        print("json -> ", message)
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Queued task: {task}")

    def close(self):
        self.connection.close()
