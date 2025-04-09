from dataclasses import dataclass
from typing import Literal
import uuid

TaskKind = Literal["js", "python", "bash"]


@dataclass
class Task:
    name: str
    description: str
    code: str
    kind: TaskKind
    on_success: list[str]
    on_failure: list[str]

    def __repr__(self) -> str:
        return (
            f"Task(\n"
            f"  name={self.name!r},\n"
            f"  description={self.description!r},\n"
            f"  kind={self.kind!r},\n"
            f"  on_success={self.on_success},\n"
            f"  on_failure={self.on_failure}\n"
            f")"
        )


class WorkflowInfo:
    uid: str
    tasks: dict[str, Task]

    def __init__(self, workflow_json: dict) -> None:
        self.uid = uuid.uuid4().hex[:8]
        self.tasks = {}
        self.parse_workflow_json(workflow_json)
        self.validate_workflow_json()
    
    def parse_workflow_json(self, workflow_json: dict) -> None:
        for task_id, task_data in workflow_json.get("tasks", {}).items():
            task = Task(
                name=task_data["name"],
                description=task_data.get("description", ""),
                code=task_data["code"],
                kind=task_data.get("kind", "bash"),  # default to "js" if not provided
                on_success=task_data.get("on_success", []),
                on_failure=task_data.get("on_failure", [])
            )
            self.tasks[task_id] = task
    
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