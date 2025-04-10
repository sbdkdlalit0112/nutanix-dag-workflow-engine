from typing import Any
import pika  # type: ignore
import json

from task_queue import TaskInfo
import task_spawner
from workflow_utils import Task


def main() -> None:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the queue in case it doesn't exist
    queue_name = 'job_queue'
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch: Any, method: Any, properties: Any, body: str) -> None:
        try:
            print(body)
            task = TaskInfo.from_json(body)
        except json.JSONDecodeError:
            print('Received invalid JSON')
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        task_spawner.handle_task_spawn_and_report(task)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=3)  # Fair dispatch
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print('Waiting for jobs. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    main()
