<<<<<<< HEAD
from contextlib import asynccontextmanager
=======
"""main.py"""

>>>>>>> c26b636a3ff9b4817884dc49469ec3efb5b36ec0
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.routes import router

<<<<<<< HEAD

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)
=======
app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    init_db()
>>>>>>> c26b636a3ff9b4817884dc49469ec3efb5b36ec0
