import json
from typing import Any
from flask import Flask, request
import requests

from workflow_utils import Task, WorkflowInfo


app = Flask(__name__)

def load_sample_workflow_json() -> Any:
    # import os
    # print(os.getcwd())
    with open("./sample.json", "r") as f:
        data = json.load(f)
    return data

workflow = WorkflowInfo(load_sample_workflow_json())

@app.route("/receive", methods=["POST"])
def receive():
    data = request.get_json()
    print("Received data:", data)
    return {"status": "ok"}

@app.route("/") # will later use it to post workflow
def index():
    # todo: accept workflow json from user
    # todo: store workflow in a database

    initial_tasks = workflow.get_initial_tasks()
    enqueue_tasks(initial_tasks)

    tasks_info = "\n".join(f"{task_id}: {task}" for task_id, task in workflow.tasks.items())
    
    return f"<pre>{tasks_info}</pre>"

def enqueue_tasks(tasks: list[Task]):
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
