import pika  # type: ignore
import json

from workflow_utils import Task


class TaskInfo:
    task: Task
    input_jsons: dict[str, str]

    def __init__(self, task: Task, input_jsons: dict[str, str]):
        self.task = task
        self.input_jsons = input_jsons

    def to_json(self) -> str:
        data = {
            "task": self.task.to_json(),
            "input_jsons": self.input_jsons
        }
        return json.dumps(data)

    @staticmethod
    def from_json(jsonstr: str) -> "TaskInfo":
        data = json.loads(jsonstr)
        task = Task.from_json(data["task"])
        input_jsons = data["input_jsons"]
        return TaskInfo(task, input_jsons)

    def __repr__(self) -> str:
        return f"TaskInfo(task={self.task}, input_jsons={self.input_jsons})"


class TaskQueue:
    queue_name: str
    host: str
    connection: pika.BlockingConnection
    channel: pika.adapters.blocking_connection.BlockingChannel

    def __init__(self, queue_name: str = "job_queue", host: str = "localhost"):
        self.queue_name = queue_name
        self.host = host
        self._connect()

    def _connect(self) -> None:
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.host))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue_name, durable=True)

    def _ensure_channel(self) -> None:
        if self.connection.is_closed or self.channel.is_closed:
            print("RabbitMQ connection/channel closed, reconnecting...")
            self._connect()

    def send_task(self, task: TaskInfo) -> None:
        self._ensure_channel()
        message = task.to_json()
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    def close(self) -> None:
        self.connection.close()
