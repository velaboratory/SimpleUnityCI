from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import ui, build, monitor

app = FastAPI(title="Simple Unity CI")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
app.include_router(build.router)
app.include_router(monitor.router)
