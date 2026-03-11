from fastapi import FastAPI, Request
import uuid
from google.adk import Agent
from agent_logic import list_items, add_item, remove_item   
import os
import uvicorn
from pydantic import BaseModel
from logger_config import logger
import time
# client = None
# @asynccontextmanager
# async def lifespan(app: FastAPI):   
#     global client
#     client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
#     print(f"Client initialized successfully.")
#     yield
#     await client.close()


# app = FastAPI(lifespan=lifespan)

# Define the request structure
class AIQuery(BaseModel):
    prompt: str
    user_id: str

# # Point to the directory containing the 'crud_agent' folder
# AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# app = get_fast_api_app(
#     agents_dir=AGENT_DIR,
#     allow_origins=["*"], # In production, replace with your frontend URL
#     web=True             # Set to True to keep the ADK Dev UI active at /
# )
app = FastAPI()

root_agent = Agent(
    name="item_manager",
    model="gemini-1.5-flash", # Or gemini-2.0-flash
    instruction="""You are an item management assistant. Use your tools to help users 
    manage their items. Always confirm when an item is created or deleted.""",
    tools=[add_item, list_items, remove_item]
)
# --- Middleware for Observability ---
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())
    start_time = time.time()
    
    # Contextual logging using extra
    logger.info(f"Incoming {request.method} {request.url.path}", extra={"request_id": rid})
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    logger.info(f"Completed with status {response.status_code}", 
                extra={"request_id": rid, "duration_ms": round(duration, 2)})
    
    response.headers["X-Request-ID"] = rid
    return response
@app.post("/generate")
async def chat(request: Request):
    try:
        # Agent runs all tool calls and returns final text
        data = await request.json()
        print(f"Received request: {data}")
        response = root_agent.run(data["prompt"], user_id=data["user_id"])
        print(f"Agent response: {response.text}")
        return {"reply": response.text, "status": "success"}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)    
# @app.post("/generate")
# async def generate(request: Request):
#     data = await request.json()
#     result = run_logic(data["user_id"], data["prompt"], client)
#     return {"response": result}
