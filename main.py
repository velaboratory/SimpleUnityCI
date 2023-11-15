import asyncio
from enum import Enum
import sys
import os
import time
import uuid
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel
import re
from git import Repo
import glob
from config import installs_folder

app = FastAPI(title="Simple Unity CI")

projects_folder = "unity_projects"
tasks_folder = "tasks"


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse("/docs")


@app.get("/projects")
def list_projects():
    orgs = [p for p in os.listdir(projects_folder)]
    project_folders = []
    for o in orgs:
        project_folders.extend(
            [f"{o}/{p}" for p in os.listdir(os.path.join(projects_folder, o))]
        )
    return project_folders


@app.get("/tasks")
def list_tasks():
    folders = [p for p in os.listdir(tasks_folder)]
    return folders


class BuildTargetEnum(str, Enum):
    StandaloneWindows64 = ("StandaloneWindows64",)
    StandaloneWindows = ("StandaloneWindows",)
    Android = ("Android",)
    StandaloneLinux64 = ("StandaloneLinux64",)
    StandaloneOSX = ("StandaloneOSX",)
    LinuxHeadlessSimulation = ("LinuxHeadlessSimulation",)
    iOS = ("iOS",)
    WebGL = ("WebGL",)
    WSAPlayer = ("WSAPlayer",)
    PS4 = ("PS4",)
    XboxOne = ("XboxOne",)
    tvOS = ("tvOS",)
    Switch = ("Switch",)
    Stadia = ("Stadia",)
    PS5 = ("PS5",)
    VisionOS = ("VisionOS",)


class UnityBuildRequest(BaseModel):
    git_repo: str
    build_target: BuildTargetEnum
    oculus_app_id: str | None = None
    oculus_app_secret: str | None = None
    oculus_release_channel: str | None = None
    keystore_name: str | None = None
    keystore_pass: str | None = None
    keyalias_name: str | None = None
    keyalias_pass: str | None = None


class GitRepo(BaseModel):
    git_repo: str
    org: str
    project: str
    path: str


class UnityProject(BaseModel):
    path: str
    version: str


def generate_sortable_uuid():
    timestamp = int(
        time.time() * 1e7
    )  # Convert current time to 100-nanosecond intervals
    unique_id = uuid.uuid4()
    sortable_uuid = uuid.UUID(int=(timestamp << 64) | (unique_id.int >> 64))
    return str(sortable_uuid)


@app.post("/build")
def build_project(
    request_data: UnityBuildRequest, background_tasks: BackgroundTasks, request: Request
):
    task_id = generate_sortable_uuid()
    background_tasks.add_task(run_unity_build, request_data, task_id)
    return {
        "task_id": task_id,
        "build_log_url": f"{str(request.base_url)}task/{task_id}/build.log",
        "task_log_url": f"{str(request.base_url)}task/{task_id}/task.log",
    }


@app.get("/task/{task_id}/build.log")
def get_status(task_id: str):
    log = os.path.join(tasks_folder, task_id, "build.log")
    with open(log, "r") as f:
        return PlainTextResponse(f.read())


@app.get("/task/{task_id}/task.log")
def get_status(task_id: str):
    log = os.path.join(tasks_folder, task_id, "task.log")
    with open(log, "r") as f:
        return PlainTextResponse(f.read())


def parse_git_repo(git_repo: str, build_target: BuildTargetEnum) -> GitRepo:
    regex = r"(?:https:\/\/|git@)(?:github\.com[:\/])?([\w-]+)\/([\w-]+)\.git"
    match = re.search(regex, git_repo)
    if match:
        org_name = match.group(1)
        project_name = match.group(2)
        return {
            "git_repo": git_repo,
            "org": org_name,
            "project": project_name,
            "path": os.path.join(projects_folder, org_name, project_name, build_target),
        }
    else:
        print("Not a valid github url")
        return None


def find_unity_project_in_path(path: str) -> UnityProject:
    version_files = glob.glob(f"{path}/**/ProjectVersion.txt", recursive=True)
    if len(version_files) > 1:
        print("Too many unity projects")
        return None
    elif len(version_files) < 1:
        print("No unity project found")
        return None
    else:
        with open(version_files[0], "r") as f:
            lines = f.readlines()
            project: UnityProject = {
                "path": version_files[0].split("ProjectSettings")[0].strip(),
                "version": lines[0].split(": ")[1].strip(),
            }
            return project


def find_unity_install(version: str) -> str:
    paths = os.listdir(installs_folder)
    for p in paths:
        if p == version:
            print("Unity version found: " + p)
            if sys.platform == 'win32':
                return os.path.join(installs_folder, p, "Editor", "Unity.exe")
            elif sys.platform == 'darwin':
                return os.path.join(installs_folder, p, "Unity.app", "Contents", "MacOS", "Unity")
            else:
                print("Unsupported platform!")
                return None
    print(f"Unity version not found! {version}")
    return None


def upload_build(request_data: UnityBuildRequest, build_path: str):
    print("Uploading build to Oculus...")
    release_channel = request_data.oculus_release_channel
    if release_channel is None:
        release_channel = "DEV"
    if request_data.build_target == BuildTargetEnum.Android:
        args = f' upload-quest-build --app-id {request_data.oculus_app_id} --app-secret {request_data.oculus_app_secret} --apk {build_path} --channel {release_channel}'
        if sys.platform == 'win32':
            os.system(f'{os.path.join("tools","ovr-platform-util.exe")}' + args)
        elif sys.platform == 'darwin':
            os.system(f'./{os.path.join("tools","ovr-platform-util")}' + args)
    elif request_data.build_target == BuildTargetEnum.StandaloneWindows64:
        build_folder = os.path.dirname(build_path)
        git_repo_data = parse_git_repo(request_data.git_repo, request_data.build_target)
        settings_file = glob.glob(f"{git_repo_data}/**/ProjectSettings.asset")[0]
        with open(settings_file, "r") as f:
            text = f.read()
            app_version = re.search("bundleVersion: (.*)", text)
            print(f"{app_version=}")
        os.system(
            f'tools\\ovr-platform-util.exe upload-rift-build --app-id {request_data["oculus_app_id"]} --app-secret {request_data["oculus_app_secret"]} --build-dir "{build_folder}" --launch-file "{build_path}" --launch-file-2d "{build_path}" -p " -useVR" --launch-params-2d "-2dmode" --channel {release_channel} --version "{app_version}"'
        )
    else:
        print("Platform not supported for upload")
        return
    print("Done uploading")


async def run_unity_build(request_data: UnityBuildRequest, task_id: str):
    start_time = time.time()
    print(f"Starting task: {task_id}")
    task_folder = os.path.join(tasks_folder, task_id)
    os.makedirs(task_folder, exist_ok=True)
    os.makedirs(projects_folder, exist_ok=True)

    git_repo_data = parse_git_repo(request_data.git_repo, request_data.build_target)
    path = git_repo_data["path"]
    if not os.path.exists(path):
        r = Repo.clone_from(request_data.git_repo, path)
    repo = Repo(path)
    repo.git.reset("--hard")
    repo.remotes.origin.pull()

    project = find_unity_project_in_path(path)
    unity_install = find_unity_install(project["version"])
    if unity_install is None:
        return

    build_path = ""

    if request_data.build_target == BuildTargetEnum.Android:
        build_path = os.path.join(
            os.getcwd(), task_folder, git_repo_data["project"] + ".apk"
        )
        args = f'-quit -batchmode -disable-assembly-updater -projectpath `"{project["path"]}`" -executeMethod SimpleUnityCI.Builder.Build -buildTarget Android -keystoreName {request_data.keystore_name} -keystorePass {request_data.keystore_pass} -keyaliasName {request_data.keyalias_name} -keyaliasPass {request_data.keyalias_pass} -outputPath `"{build_path}`" -logFile `"{os.path.join(task_folder, "build.log")}`"'
    elif request_data.build_target == BuildTargetEnum.StandaloneWindows64:
        build_path = os.path.join(
            os.getcwd(), task_folder, "build", git_repo_data["project"] + ".exe"
        )
        # os.makedirs(build_path, exist_ok=True)
        print(f"{build_path=}")
        args = f'-quit -batchmode -disable-assembly-updater -projectpath `"{project["path"]}`" -buildWindows64Player `"{build_path}`" -logFile `"{os.path.join(task_folder, "build.log")}`"'
    else:
        print("Platform not supported!")
        return None
    # cmd = f'"{unity_install}" {args}'

    if sys.platform == 'win32':
        cmd = f'$unity = Start-Process -FilePath "{unity_install}" -ArgumentList "{args}" -PassThru\n'
        with open("PS1Wait.ps1", "r") as f:
            cmd += f.read()
        with open(os.path.join(task_folder, f"build.ps1"), "w") as f:
            f.write(cmd)

        cmd = f'powershell.exe -command ".\\{task_folder}\\build.ps1"'
        print(cmd)
        ret = os.system(cmd)
    elif sys.platform == 'darwin':
        args = args.replace('`', '')
        cmd = f'{unity_install} {args}'
        print(cmd)
        ret = os.system(cmd)
    else:
        print('Platform not supported!')
        return None
    print(f"Finished in {time.time() - start_time:.3f} s")
    print(f"Done building! Exit code: {ret}")
    if os.path.exists(os.path.join(task_folder, build_path)):
        print(os.path.join(task_folder, build_path))
        if request_data.oculus_app_id is not None:
            upload_build(request_data, build_path)
        return True
    else:
        return False
