import json
from typing import Any
from flask import Flask, request, render_template

from task_queue import TaskInfo, TaskQueue
from workflow_utils import Task, WorkflowInfo


app = Flask(__name__)
queue = TaskQueue()


def load_sample_workflow_json() -> str:
    with open("./sample.json", "r") as f:
        data = f.read()
    return data


# todo: store workflow in a database
workflow = WorkflowInfo(load_sample_workflow_json())


@app.route("/receive", methods=["POST"])
def receive() -> dict[Any, Any]:
    data = request.get_json()
    print("Received data:", data)

    received_task = Task.from_dict(json.loads(data["task"]))
    is_success = data["success"]
    output_json = data.get("output", {})
    workflow.mark_task_completed(received_task, output_json)
    next_task_ids = received_task.on_success if is_success else received_task.on_failure
    next_tasks = [workflow.tasks[task_id]
                  for task_id in next_task_ids if task_id in workflow.tasks]
    next_tasks_info = [
        TaskInfo(task, {received_task.name: output_json}) for task in next_tasks]

    enqueue_tasks(next_tasks_info)

    return {"status": "ok"}


@app.route("/")  # will later use it to post workflow
def home() -> str:
    return '<h1>Welcome to the Workflow Engine</h1><p><a href="/submit_workflow">Submit a Workflow</a></p>'


@app.route("/submit_workflow")
def submit_workflow_form() -> str:
    return render_template("workflow_input.html")


@app.route("/workflow_status")
def status() -> str:
    if len(workflow.task_outputs) == len(workflow.tasks):
        return json.dumps({
            "status": f"{workflow.task_outputs}/{workflow.tasks}"
        })

    return json.dumps({
        "status": "complete",
        "info": workflow.task_outputs
    })


@app.route("/workflow", methods=["POST"])
def submit_workflow() -> dict[str, str]:
    data = request.get_json()
    # print("Workflow JSON received:", data["workflow"])
    global workflow
    workflow = WorkflowInfo(data["workflow"])
    initial_tasks = workflow.get_initial_tasks()
    enqueue_tasks([TaskInfo(task, {}) for task in initial_tasks])

    tasks_info = "\n".join(
        f"{task_id}: {task}" for task_id, task in workflow.tasks.items())

    return {"parsed": f"<pre>{tasks_info}</pre>"}


def enqueue_tasks(tasks: list[TaskInfo]) -> None:
    for task in tasks:
        queue.send_task(task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
