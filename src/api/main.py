"""FastAPI application for chatbot web interface."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import structlog
import uuid
from datetime import datetime
from pathlib import Path

from src.agents.orchestrator import ChatbotOrchestrator

logger = structlog.get_logger()

app = FastAPI(
    title="Generic WhatsApp Chatbot API",
    description="Chatbot inteligente com múltiplos agentes especializados",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = ChatbotOrchestrator()

# Store active websocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket connected", client_id=client_id)

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info("WebSocket disconnected", client_id=client_id)

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "message",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })

manager = ConnectionManager()


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str


# REST Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the chat interface."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return """
    <html>
        <head>
            <title>Chatbot</title>
        </head>
        <body>
            <h1>Chatbot API Running</h1>
            <p>Access <a href="/docs">/docs</a> for API documentation</p>
            <p>Frontend will be available at <a href="/chat">/chat</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response (REST endpoint)."""
    try:
        thread_id = request.thread_id or str(uuid.uuid4())
        
        logger.info("Chat request received", 
                   message=request.message[:50],
                   thread_id=thread_id)
        
        response = orchestrator.process_message(
            message=request.message,
            thread_id=thread_id
        )
        
        return ChatResponse(
            response=response,
            thread_id=thread_id
        )
        
    except Exception as e:
        logger.error("Error processing chat request", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            thread_id = data.get("thread_id", client_id)
            
            logger.info("WebSocket message received",
                       client_id=client_id,
                       message=message[:50])
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "typing": True
            })
            
            # Process message
            try:
                response = orchestrator.process_message(
                    message=message,
                    thread_id=thread_id
                )
                
                # Send response
                await websocket.send_json({
                    "type": "message",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "typing": False
                })
                
            except Exception as e:
                logger.error("Error processing websocket message", error=str(e))
                await websocket.send_json({
                    "type": "error",
                    "content": f"Erro ao processar mensagem: {str(e)}",
                    "typing": False
                })
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info("WebSocket disconnected", client_id=client_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), client_id=client_id)
        manager.disconnect(client_id)


# Mount static files (will create this directory)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except:
    pass  # Static dir might not exist yet


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
