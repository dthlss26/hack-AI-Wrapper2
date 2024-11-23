from fastapi import FastAPI
from loguru import logger
from models import Prompt, PromptResponse
import uuid

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/prompt/generate")
async def generate_prompt(prompt: Prompt):
    logger.info(f"Received prompt: {prompt.prompt}")
    new_uuid = str(uuid.uuid4())

    return PromptResponse(uuid=new_uuid)

@app.get("/prompt/status/{uuid}")
async def prompt_status(req_uuid: str):
    logger.info(f"Received prompt status request uuid: {req_uuid}")
