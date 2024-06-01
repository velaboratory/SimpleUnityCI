from datetime import datetime
import json
import os
from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse, PlainTextResponse
from config import TASKS_FOLDER, PROJECTS_FOLDER, UNITY_INSTALLS_FOLDER


router = APIRouter(tags=["Monitor"])


@router.get("/projects")
def list_projects():
    orgs = [p for p in os.listdir(PROJECTS_FOLDER)]
    project_folders = []
    for o in orgs:
        project_folders.extend([f"{o}/{p}" for p in os.listdir(os.path.join(PROJECTS_FOLDER, o))])
    return project_folders


@router.get("/unity_versions")
def list_unity_versions():
    if not os.path.exists(UNITY_INSTALLS_FOLDER):
        return []
    versions = [p for p in os.listdir(UNITY_INSTALLS_FOLDER)]
    return versions


@router.get("/tasks")
def list_tasks():
    output = []
    for p in os.listdir(TASKS_FOLDER):
        dir = os.path.join(TASKS_FOLDER, p)
        if os.path.isdir(dir):
            files = os.listdir(dir)
            modified_times = {
                key: datetime.fromtimestamp(os.path.getmtime((os.path.join(TASKS_FOLDER, p, key))))
                for key in files
                if key != "metadata.json"
            }
            metadata = {}
            metadata_file = os.path.join(TASKS_FOLDER, p, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    try:
                        metadata = json.load(f)
                    except Exception:
                        pass
        output.append({"task_id": p, "metadata": metadata, "files": modified_times})

    output.sort(key=lambda x: x["files"]["task.log"] if "task.log" in x["files"] else datetime.now(), reverse=False)
    return output


@router.get("/tasks/{task_id}/{file_name}")
def get_task_file(task_id: str, file_name: str):
    full_file_name = os.path.join(TASKS_FOLDER, task_id, file_name)
    if not os.path.exists(full_file_name):
        raise HTTPException(status_code=404, detail="File not found")
    if full_file_name.endswith(".apk") or full_file_name.endswith(".exe"):
        return FileResponse(full_file_name)
    else:
        with open(full_file_name, "r") as f:
            return PlainTextResponse(f.read())
