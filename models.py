from typing import Literal

from pydantic import BaseModel

class Prompt(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    uuid: str

class PromptStatus(BaseModel):
    status: Literal["failed", "running", "finished"]
    response: str