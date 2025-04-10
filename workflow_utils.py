from typing import Any, List
import json
from enum import Enum
from dataclasses import dataclass, asdict
import uuid


class TaskKind(str, Enum):
    BASH = "bash"
    PYTHON = "python"
    JS = "js"


@dataclass
class Task:
    name: str
    description: str
    code: str
    kind: TaskKind
    on_success: List[str]
    on_failure: List[str]

    def __repr__(self) -> str:
        return (
            f"Task(\n"
            f"  name={self.name!r},\n"
            f"  description={self.description!r},\n"
            f"  kind={self.kind!r},\n"
            f"  code={self.code!r},\n"
            f"  on_success={self.on_success},\n"
            f"  on_failure={self.on_failure}\n"
            f")"
        )

    def to_json(self) -> str:
        data = asdict(self)
        data['kind'] = self.kind.value  # Convert enum to string
        return json.dumps(data)

    @staticmethod
    def from_json(jsonstr: str) -> "Task":
        task_dict = json.loads(jsonstr)
        return Task.from_dict(task_dict)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Task":
        return Task(
            name=data["name"],
            description=data.get("description", ""),
            code=data["code"],
            kind=TaskKind(data.get("kind", "bash")),  # Default to bash
            on_success=data.get("on_success", []),
            on_failure=data.get("on_failure", [])
        )


class WorkflowInfo:
    uid: str
    tasks: dict[str, Task]
    task_outputs: dict[str, str]

    def __init__(self, workflow_str: str) -> None:
        self.uid = uuid.uuid4().hex[:8]
        self.tasks = {}
        self.parse_workflow_json(workflow_str)
        self.validate_workflow_json()
        self.task_outputs = {}

    def parse_workflow_json(self, workflow_str: str) -> None:
        workflow_dict = json.loads(workflow_str)
        for task_id, task_data in workflow_dict.get("tasks", {}).items():
            self.tasks[task_id] = Task.from_dict(task_data)

    def validate_workflow_json(self) -> None:
        # todo: ensure No loop in graph
        pass

    def get_initial_tasks(self) -> list[Task]:
        """
        Get the initial tasks of the workflow (i.e., tasks with no dependencies).
        """
        all_task_ids = set(self.tasks.keys())
        for task in self.tasks.values():
            all_task_ids -= set(task.on_success)
            all_task_ids -= set(task.on_failure)

        return [self.tasks[task_id] for task_id in all_task_ids if task_id in self.tasks]

    def mark_task_completed(self, task: Task, output: str) -> None:
        self.task_outputs[task.name] = output
