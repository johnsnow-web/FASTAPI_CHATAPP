import logging
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from startup import initialize_pdfs  # Call it at startup
from server import websocket_endpoint

# Initialize FastAPI app
app = FastAPI()

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def root():
    return {"message": "Server is running. Go to /static/index.html"}

# WebSocket route
app.add_api_websocket_route("/ws", websocket_endpoint)

# Load and process PDFs at startup
initialize_pdfs()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
