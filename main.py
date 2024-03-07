from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import ui, build, monitor
# import uvicorn

app = FastAPI(title="Simple Unity CI")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ui.router)
app.include_router(build.router)
app.include_router(monitor.router)

# if __name__ == "__main__":
#     uvicorn.run(app="main:app", host="0.0.0.0", port=8000, workers=10)
