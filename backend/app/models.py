from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str


class WorkflowStep(BaseModel):
    agent: str
    action: str
    result: str


class ChatResponse(BaseModel):
    user_id: str
    conversation_id: str
    router_decision: str
    response: str
    agent_workflow: List[WorkflowStep]
