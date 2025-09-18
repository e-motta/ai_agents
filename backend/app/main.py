from fastapi import FastAPI
from app.api.v1.hello import router as hello_router

app = FastAPI()

app.include_router(hello_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}