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
    connection: pika.BlockingConnection
    channel: pika.adapters.blocking_connection.BlockingChannel

    def __init__(self, queue_name: str = "job_queue", host: str = "localhost"):
        self.queue_name = queue_name
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host))
        self.channel = self.connection.channel()
        self.channel.queue_purge(queue=queue_name)
        self.channel.queue_declare(queue=queue_name, durable=True)

    def send_task(self, task: TaskInfo) -> None:
        message = task.to_json()
        print("json -> ", message)
        self.channel.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"Queued task: {task}")

    def close(self) -> None:
        self.connection.close()
