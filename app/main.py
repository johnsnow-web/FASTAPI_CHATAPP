from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.websocket import router as websocket_router
import app.utils.logging  # Ensures logging is configured

# Initialize FastAPI app
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Include WebSocket route
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {"message": "Server is running. Go to /static/index.html"}
