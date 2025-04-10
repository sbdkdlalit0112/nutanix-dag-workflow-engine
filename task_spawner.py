import json
import subprocess
import tempfile
import os
import uuid
import shutil
import requests

from task_queue import TaskInfo
from workflow_utils import TaskKind

LANG_INFO: dict[TaskKind, dict[str, str]] = {
    TaskKind.JS: {
        "docker_image": "node:latest",
        "suffix": "js",
        "runtime": "node"
    },
    TaskKind.PYTHON: {
        "docker_image": "python:3.11-slim",
        "suffix": "py",
        "runtime": "python"
    },
    TaskKind.BASH: {
        "docker_image": "bash:latest",
        "suffix": "sh",
        "runtime": "bash"
    }
}


def get_lang_info(kind: TaskKind) -> dict[str, str]:
    return LANG_INFO.get(kind, LANG_INFO[TaskKind.BASH])


def provision_folder(temp_dir: str, taskinf: TaskInfo, extension: str) -> None:
    entrypt_file = f"entrypt.{extension}"
    host_file_path = os.path.join(temp_dir, entrypt_file)
    input_file_path = os.path.join(temp_dir, "input.json")
    with open(host_file_path, "w") as f:
        f.write(taskinf.task.code)

    with open(input_file_path, "w") as f:
        f.write(json.dumps(taskinf.input_jsons))


def spawn_docker_vm_with_string(taskinf: TaskInfo) -> tuple[bool, str]:
    # Create a temp dir
    temp_dir = tempfile.mkdtemp()
    uid = uuid.uuid4().__str__()
    task = taskinf.task
    lang_info = get_lang_info(task.kind)
    runtime = lang_info["runtime"]
    image = lang_info["docker_image"]
    suffix = lang_info["suffix"]

    provision_folder(temp_dir, taskinf, suffix)
    container_name = f"vm_{uid}"

    try:
        command = [
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{temp_dir}:/app",
            image,
            "bash", "-c", f"cd app && {runtime} entrypt.{suffix}"
        ]
        print("Executing:", " ".join(command))
        result = subprocess.run(command, check=True,
                                capture_output=True, text=True)
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print("Docker error:", e)
        return False, f"Error running Docker: {e.stderr}"
    except Exception as e:
        print("Unexpected error:", e)
        return False, str(e)
    finally:
        shutil.rmtree(temp_dir)


# spawn_docker_vm_with_string(Task(
#     name="SampleTask",
#     description="A sample task to test JS execution",
#     code="console.log('hello from inside!');",
#     kind=TaskKind.JS,
#     on_success=[],
#     on_failure=[]
# ))


def handle_task_spawn_and_report(taskinf: TaskInfo) -> None:
    """
    Spawn a task in a docker container and send feedback to main server.
    """
    success, output = spawn_docker_vm_with_string(taskinf)
    # if success:
    #     print(f"Task {taskinf.task.name} executed successfully.")
    #     print(output)
    # else:
    #     print(f"Task {taskinf.task.name} failed.")
    #     print(output)

    payload = {
        "success": success,
        "output": output,
        "task": taskinf.task.to_json()
    }

    try:
        response = requests.post("http://localhost:8000/receive", json=payload)
        print(f"Reported result with status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send report: {e}")
