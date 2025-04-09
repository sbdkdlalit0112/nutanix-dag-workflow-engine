import subprocess
import tempfile
import os
import uuid
import shutil

from workflow_utils import Task

lang_info = {
    "js": {
        "docker_image": "node:latest",
        "suffix": "js"
    },
    "python": {
        "docker_image": "python:3.11-slim",
        "suffix": "py"
    },
    "bash": {
        "docker_image": "bash:latest",
        "suffix": "sh"
    }
}

def get_lang_info(lang: str):
    return lang_info.get(lang, lang_info["bash"])


def spawn_docker_vm_with_string(task: Task) -> tuple[bool, str]:
    # Create a temp file and write the string
    temp_dir = tempfile.mkdtemp()
    uid = uuid.uuid4().hex[:8]
    lang_info = get_lang_info(task.kind)

    image = lang_info.docker_image

    container_file_name = f"task_{uid}.{lang_info.suffix}"
    host_file_path = os.path.join(temp_dir, container_file_name)
    with open(host_file_path, "w") as f:
        f.write(task.code)

    container_name = f"vm_{uid}"

    try:
        result = subprocess.run([
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{host_file_path}:/app/{container_file_name}",
            image,
            "node", f"/app/{container_file_name}"
        ], check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error running Docker: {e.stderr}"
    finally:
        shutil.rmtree(temp_dir)
    

# spawn_docker_vm_with_string("console.log('hello from inside!');")


def spawn_task(task: Task) -> None:
    """
    Spawn a task in a docker container.
    """
    success, output = spawn_docker_vm_with_string(task)
    if success:
        print(f"Task {task.name} executed successfully.")
        print(output)
    else:
        print(f"Task {task.name} failed.")
        print(output)