import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Any, Dict
from flask import Flask, request, render_template
from bson import ObjectId

from task_queue import TaskInfo, TaskQueue
from workflow_utils import Task, WorkflowInfo, mark_task_completed


app = Flask(__name__)
queue = TaskQueue()
load_dotenv()  # To load environment variables from a .env file
# Default to localhost if not set
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client: MongoClient[Dict[str, Any]] = MongoClient(mongo_uri)
db = client.get_database("WorkflowExecutionEngine")
workflow_collection = db.get_collection("workflows")


@app.route("/receive", methods=["POST"])
def receive() -> dict[Any, Any]:
    data = request.get_json()
    # print(data)
    workflow_id = data["workflow_id"]
    workflow_doc = workflow_collection.find_one({"_id": ObjectId(workflow_id)})
    if not workflow_doc:
        return {"status": "workflow not found"}
    workflow_doc["uid"] = str(workflow_doc["_id"])

    received_task = Task.from_dict(json.loads(data["task"]))
    is_success = data["success"]
    output_json = data.get("output", {})
    mark_task_completed(workflow_doc, received_task, output_json)
    next_task_ids = received_task.on_success if is_success else received_task.on_failure
    next_tasks = [workflow_doc["tasks"][task_id]
                  for task_id in next_task_ids if task_id in workflow_doc["tasks"]]
    next_tasks_info = [
        TaskInfo(Task.from_dict(task), {received_task.name: output_json}, workflow_id) for task in next_tasks]

    enqueue_tasks(next_tasks_info)

    workflow_collection.update_one(
        {"_id": ObjectId(workflow_id)},
        {"$set": workflow_doc}
    )

    return {"status": "ok"}


@app.route("/")  # will later use it to post workflow
def home() -> str:
    return '<h1>Welcome to the Workflow Engine</h1><p><a href="/submit_workflow">Submit a Workflow</a></p>'


@app.route("/submit_workflow")
def submit_workflow_form() -> str:
    return render_template("workflow_input.html")


@app.route("/workflow_status/<workflow_id>")
def status(workflow_id: str) -> str:
    workflow_doc = workflow_collection.find_one({"_id": ObjectId(workflow_id)})

    if not workflow_doc:
        return json.dumps({"status": "not found"})

    # if len(workflow_doc["task_outputs"]) < len(workflow_doc["tasks"]):
    #     return json.dumps({
    #         "status": f"{len(workflow_doc['task_outputs'])}/{len(workflow_doc['tasks'])}"
    #     })

    return json.dumps({
        "status": "complete",
        "info": workflow_doc["task_outputs"]
    })


@app.route("/workflow", methods=["POST"])
def submit_workflow() -> dict[str, str]:
    data = request.get_json()
    workflow = WorkflowInfo(data['workflow'])
    workflow_doc = workflow_collection.insert_one(workflow.to_dict())

    initial_tasks = workflow.get_initial_tasks()
    print("init tasks", [task.name for task in initial_tasks])
    enqueue_tasks([TaskInfo(task, {}, str(workflow_doc.inserted_id))
                  for task in initial_tasks])

    tasks_info = "\n".join(
        f"{task_id}: {task}" for task_id, task in workflow.tasks.items())

    return {"parsed": f"<pre>{tasks_info}</pre>", "workflow_id": str(workflow_doc.inserted_id)}


def enqueue_tasks(tasks: list[TaskInfo]) -> None:
    for task in tasks:
        queue.send_task(task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
