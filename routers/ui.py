import os
from typing import Union
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


router = APIRouter(tags=["UI"])


@router.get("/")
def homepage():
    return FileResponse("static/index.html")
