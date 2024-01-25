import json
import os
import sys
from enum import Enum
import subprocess
import sys
import os
import time
import uuid
from fastapi import BackgroundTasks, Request, APIRouter, Response
from pydantic import BaseModel
import re
from git import Repo
import glob
from config import installs_folder, tasks_folder, projects_folder


router = APIRouter(tags=["Build"])


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
    timestamp = int(time.time() * 1e7)  # Convert current time to 100-nanosecond intervals
    unique_id = uuid.uuid4()
    sortable_uuid = uuid.UUID(int=(timestamp << 64) | (unique_id.int >> 64))
    return str(sortable_uuid)


@router.post("/build")
def build_project(request_data: UnityBuildRequest, background_tasks: BackgroundTasks, request: Request):
    task_id = generate_sortable_uuid()
    background_tasks.add_task(run_unity_build, request_data, task_id)
    return {
        "task_id": task_id,
        "build_log_url": f"{str(request.base_url)}task/{task_id}/build.log",
        "task_log_url": f"{str(request.base_url)}task/{task_id}/task.log",
    }


def parse_git_repo(task_id: str, git_repo: str, build_target: BuildTargetEnum) -> GitRepo | None:
    regex = r"(?:https:\/\/|git@)(?:github\.com[:\/])?([\w-]+)\/([\w-]+)\.git"
    match = re.search(regex, git_repo)
    if match:
        org_name = match.group(1)
        project_name = match.group(2)
        return GitRepo(
            git_repo=git_repo,
            org=org_name,
            project=project_name,
            path=os.path.join(projects_folder, org_name, project_name, build_target),
        )
    else:
        log(task_id, "Not a valid github url")
        return None


def find_unity_project_in_path(task_id: str, path: str) -> UnityProject | None:
    version_files = glob.glob(f"{path}/**/ProjectVersion.txt", recursive=True)
    if len(version_files) > 1:
        log(task_id, "Too many unity projects")
        return None
    elif len(version_files) < 1:
        log(task_id, "No unity project found")
        return None
    else:
        with open(version_files[0], "r") as f:
            lines = f.readlines()
            project = UnityProject(
                path=version_files[0].split("ProjectSettings")[0].strip(),
                version=lines[0].split(": ")[1].strip(),
            )
            return project


def find_unity_install(task_id: str, version: str) -> str | None:
    paths = os.listdir(installs_folder)
    for p in paths:
        if p == version:
            log(task_id, "Unity version found: " + p)
            if sys.platform == "win32":
                return os.path.join(installs_folder, p, "Editor", "Unity.exe")
            elif sys.platform == "darwin":
                return os.path.join(installs_folder, p, "Unity.app", "Contents", "MacOS", "Unity")
            else:
                log("Unsupported platform!")
                return None
    log(task_id, f"Unity version not found! {version}")
    return None


def upload_build(task_id: str, request_data: UnityBuildRequest, build_path: str):
    log(task_id, "Uploading build to Oculus...")
    release_channel = request_data.oculus_release_channel
    if release_channel is None:
        release_channel = "DEV"
    if request_data.build_target == BuildTargetEnum.Android:
        args = f" upload-quest-build --app-id {request_data.oculus_app_id} --app-secret {request_data.oculus_app_secret} --apk {build_path} --channel {release_channel}"
        if sys.platform == "win32":
            os.system(f'{os.path.join("tools","ovr-platform-util.exe")}' + args)
        elif sys.platform == "darwin":
            os.system(f'./{os.path.join("tools","ovr-platform-util")}' + args)
    elif request_data.build_target == BuildTargetEnum.StandaloneWindows64:
        build_folder = os.path.dirname(build_path)
        git_repo_data = parse_git_repo(task_id, request_data.git_repo, request_data.build_target)
        settings_file = glob.glob(f"{git_repo_data}/**/ProjectSettings.asset")[0]
        with open(settings_file, "r") as f:
            text = f.read()
            app_version = re.search("bundleVersion: (.*)", text)
            log(task_id, f"{app_version=}")

        with open(os.path.join(tasks_folder, task_id, "task.log"), "a") as f:
            return_code = subprocess.call(
                [
                    os.path.join("tools\\ovr-platform-util.exe"),
                    "upload-rift-build",
                    "--app-id",
                    request_data.oculus_app_id,
                    "--app-secret",
                    request_data.oculus_app_secret,
                    "--build-dir",
                    build_folder,
                    "--launch-file",
                    build_path,
                    "--launch-file-2d",
                    build_path,
                    "-p",
                    "-useVR",
                    "--launch-params-2d",
                    "-2dmode",
                    "--channel",
                    release_channel,
                    "--version",
                    app_version,
                ],  # type: ignore
                stdout=f,
                stderr=f,
            )
            log(task_id, str(return_code))
    else:
        log(task_id, "Platform not supported for upload")
        return
    log(task_id, "Done uploading")


async def run_unity_build(request_data: UnityBuildRequest, task_id: str):
    start_time = time.time()
    task_folder = os.path.join(tasks_folder, task_id)
    os.makedirs(task_folder, exist_ok=True)
    os.makedirs(projects_folder, exist_ok=True)
    log(task_id, f"Starting task: {task_id}")
    with open(os.path.join(task_folder, "metadata.json"), "w") as f:
        f.write(json.dumps(request_data.__dict__, indent=4))

    git_repo_data = parse_git_repo(task_id, request_data.git_repo, request_data.build_target)
    if git_repo_data is None:
        log(task_id, "Failed.")
        return
    path = git_repo_data.path
    if not os.path.exists(path):
        r = Repo.clone_from(request_data.git_repo, path)
    repo = Repo(path)
    repo.git.reset("--hard")
    repo.remotes.origin.pull()

    project = find_unity_project_in_path(task_id, path)
    if project is None:
        log(task_id, "Failed.")
        return
    unity_install = find_unity_install(task_id, project.version)
    if unity_install is None:
        log(task_id, "Failed.")
        return

    build_path = ""

    if request_data.build_target == BuildTargetEnum.Android:
        build_path = os.path.join(os.getcwd(), task_folder, git_repo_data.project + ".apk")
        args = f'-quit -batchmode -disable-assembly-updater -projectpath `"{project.path}`" -executeMethod SimpleUnityCI.Builder.Build -buildTarget Android -keystoreName {request_data.keystore_name} -keystorePass {request_data.keystore_pass} -keyaliasName {request_data.keyalias_name} -keyaliasPass {request_data.keyalias_pass} -outputPath `"{build_path}`" -logFile `"{os.path.join(task_folder, "build.log")}`"'
    elif request_data.build_target == BuildTargetEnum.StandaloneWindows64:
        build_path = os.path.join(os.getcwd(), task_folder, "build", git_repo_data.project + ".exe")
        # os.makedirs(build_path, exist_ok=True)
        log(task_id, f"{build_path=}")
        args = f'-quit -batchmode -disable-assembly-updater -projectpath `"{project.path}`" -buildWindows64Player `"{build_path}`" -logFile `"{os.path.join(task_folder, "build.log")}`"'
    else:
        log(task_id, "Platform not supported!")
        log(task_id, "Failed.")
        return

    if sys.platform == "win32":
        cmd = f'$unity = Start-Process -FilePath "{unity_install}" -ArgumentList "{args}" -PassThru\n'
        with open("PS1Wait.ps1", "r") as f:
            cmd += f.read()
        with open(os.path.join(task_folder, f"build.ps1"), "w") as f:
            f.write(cmd)

        cmd = f'powershell.exe -command ".\\{task_folder}\\build.ps1"'
        log(task_id, cmd)
        ret = os.system(cmd)
    elif sys.platform == "darwin":
        args = args.replace("`", "")
        cmd = f"{unity_install} {args}"
        log(cmd)
        ret = os.system(cmd)
    else:
        log("Platform not supported!")
        log(task_id, "Failed.")
        return
    log(task_id, f"Finished in {time.time() - start_time:.3f} s")
    log(task_id, f"Done building! Exit code: {ret}")
    if os.path.exists(os.path.join(task_folder, build_path)):
        log(task_id, os.path.join(task_folder, build_path))
        if request_data.oculus_app_id is not None:
            upload_build(task_id, request_data, build_path)
        log(task_id, "Success.")
        return True
    else:
        log(task_id, "Failed.")
        return False


def log(task_id: str, message: str):
    print(message)
    log_file = os.path.join(tasks_folder, task_id, "task.log")
    with open(log_file, "a") as f:
        f.write(message + "\n")