import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

UNITY_INSTALLS_FOLDER = os.environ.get("UNITY_INSTALLS_FOLDER", r"C:\Program Files\Unity\Hub\Editor")
PROJECTS_FOLDER = os.environ.get("PROJECTS_FOLDER", "unity_projects")
TASKS_FOLDER = os.environ.get("TASKS_FOLDER", "tasks")
