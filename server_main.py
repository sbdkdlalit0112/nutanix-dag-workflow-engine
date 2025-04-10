import json
from typing import Any
from flask import Flask, request

from task_queue import TaskInfo, TaskQueue
from workflow_utils import Task, WorkflowInfo


app = Flask(__name__)
queue = TaskQueue()


def load_sample_workflow_json() -> str:
    with open("./sample.json", "r") as f:
        data = f.read()
    return data


workflow = WorkflowInfo(load_sample_workflow_json())


@app.route("/receive", methods=["POST"])
def receive() -> dict[Any, Any]:
    data = request.get_json()
    print("Received data:", data)

    received_task = Task.from_dict(json.loads(data["task"]))
    is_success = data["success"]
    output_json = data.get("output", {})
    next_task_ids = received_task.on_success if is_success else received_task.on_failure
    next_tasks = [workflow.tasks[task_id]
                  for task_id in next_task_ids if task_id in workflow.tasks]
    next_tasks_info = [
        TaskInfo(task, {received_task.name: output_json}) for task in next_tasks]

    enqueue_tasks(next_tasks_info)

    return {"status": "ok"}


@app.route("/")  # will later use it to post workflow
def index() -> str:
    # todo: accept workflow json from user
    # todo: store workflow in a database

    initial_tasks = workflow.get_initial_tasks()
    enqueue_tasks([TaskInfo(task, {}) for task in initial_tasks])

    tasks_info = "\n".join(
        f"{task_id}: {task}" for task_id, task in workflow.tasks.items())

    return f"<pre>{tasks_info}</pre>"


def enqueue_tasks(tasks: list[TaskInfo]) -> None:
    for task in tasks:
        queue.send_task(task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
