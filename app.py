from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sales_agent import SalesAgent
from monitor import EmailMonitor
from utils import logger
import json

app = FastAPI(
    title="LLM Sales Assistant API",
    description="API interface for managing customer emails with LLM support",
    version="1.0.0"
)

sales_agent = SalesAgent()
email_monitor = EmailMonitor(sales_agent.email_handler)
email_monitor.start()

class PromptInput(BaseModel):
    input: str

@app.post("/run", summary="Run sales agent with prompt", response_description="Result from agent")
def run_agent(prompt: PromptInput):
    try:
        result = sales_agent.run(prompt.input)
        return result
    except Exception as e:
        logger.error(f"/run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emails", summary="Get new incoming emails", response_description="List of new emails")
def get_new_emails():
    try:
        emails = email_monitor.get_new_emails()
        return {"new_emails": emails}
    except Exception as e:
        logger.error(f"/emails error: {e}")
        raise HTTPException(status_code=500, detail=str(e))