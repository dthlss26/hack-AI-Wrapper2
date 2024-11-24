from fastapi import FastAPI, BackgroundTasks
from loguru import logger

import openAIAssistant
from models import Prompt, PromptResponse, PromptStatus
import uuid

from openAIAssistant import convert_csv_to_text, convert_csv_to_json, upload_file_to_vector_store, setup_assistant, \
    query_assistant

app = FastAPI()

def init():
    logger.info("Starting application..")
    # convert_csv_to_text(csv_path, text_file_path)
    convert_csv_to_json(openAIAssistant.csv_path, openAIAssistant.json_file_path)

    # Upload the file to vector store (choose either text or JSON)
    logger.info("Uploading to vector store...")
    vector_store_id = upload_file_to_vector_store(openAIAssistant.json_file_path, "text/plain")

    # Set up the assistant
    logger.info("Setting up assistant...")
    return  setup_assistant(vector_store_id)


assistant = init()
logger.info("Application ready")

task_status = {}
@app.get("/")
async def root():
    return {"message": "Hello World"}


async def prompt_gpt(prompt: str, task_uuid: str):
    # try:
    logger.info(f"Started generating response for prompt: {task_uuid}")

    task_status[task_uuid] = {"status": "running"}
    result = query_assistant(assistant.id, prompt)
    logger.info(f"Response: {task_uuid} -> {result}")

    if result == "error":
        task_status[task_uuid]["status"] = "failed"
    else :
        task_status[task_uuid] = {"status": "finished", "result": result}

    logger.info(f"Finished generating response for prompt: {task_uuid}")

# except Exception as e:
#     logger.error(f"An error has occured while generating response for prompt: {task_uuid}")
#     task_status[task_uuid]["status"] = "failed"
#     print(e)

@app.post("/prompt")
async def generate_prompt(prompt: Prompt, background_tasks: BackgroundTasks):
    logger.info(f"Received prompt: {prompt.prompt}")
    new_uuid = str(uuid.uuid4())

    task_status[new_uuid] = {"status": "running"}
    background_tasks.add_task(prompt_gpt, prompt.prompt, new_uuid)
    return PromptResponse(uuid=new_uuid)

@app.get("/status/{req_uuid}")
async def prompt_status(req_uuid: str):
    logger.info(f"Received prompt status request uuid: {req_uuid}")

    task = task_status.get(req_uuid, {"status": "notFound"})

    if task["status"] == "finished":
        return PromptStatus(status=task["status"], response=task["result"])

    return PromptStatus(status=task["status"])

