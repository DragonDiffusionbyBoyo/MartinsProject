from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import sqlite3
import os
from datetime import datetime
import uuid

# Import our custom modules
from ollama_client import OllamaClient
from menu_generator import MenuGenerator

app = FastAPI(
    title="MenuBot API",
    description="Dynamic AI Workflow Builder",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our AI clients
ollama_client = OllamaClient()
menu_generator = MenuGenerator(ollama_client)

# Database setup
DATABASE_PATH = "database/menubot.db"

def init_database():
    """Initialize SQLite database with required tables"""
    os.makedirs("database", exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create nodes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            title TEXT NOT NULL,
            content TEXT,
            node_type TEXT DEFAULT 'menu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES nodes(id)
        )
    """)
    
    # Create actions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY,
            node_id TEXT NOT NULL,
            title TEXT NOT NULL,
            prompt TEXT,
            tools TEXT,
            alt_text TEXT,
            icon TEXT,
            FOREIGN KEY (node_id) REFERENCES nodes(id)
        )
    """)
    
    # Create context table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role_description TEXT,
            current_node_id TEXT,
            conversation_history TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

@app.get("/")
async def root():
    return {"message": "MenuBot API is running", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ollama_status": await ollama_client.check_health(),
        "database": "connected" if os.path.exists(DATABASE_PATH) else "not_found"
    }

@app.post("/api/generate-menu")
async def generate_menu(request: Request):
    """Generate context-aware menu options"""
    try:
        data = await request.json()
        
        role = data.get("role", "General User")
        context = data.get("context", "")
        previous_actions = data.get("previous_actions", [])
        current_node_data = data.get("current_node_data", {})
        
        # Generate menu using our AI
        menu_items = await menu_generator.generate_menu(
            role=role,
            context=context,
            previous_actions=previous_actions,
            current_node_data=current_node_data
        )
        
        return {"menu_items": menu_items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Menu generation failed: {str(e)}")

@app.post("/api/execute-action")
async def execute_action(request: Request):
    """Execute a selected menu action"""
    try:
        data = await request.json()
        
        action_id = data.get("action_id")
        context = data.get("context", {})
        user_input = data.get("user_input", "")
        
        # Execute action using our AI
        result = await menu_generator.execute_action(
            action_id=action_id,
            context=context,
            user_input=user_input
        )
        
        # Create new node for result
        node_id = str(uuid.uuid4())
        
        # Store in database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO nodes (id, title, content, node_type) VALUES (?, ?, ?, ?)",
            (node_id, "Action Result", json.dumps(result), "result")
        )
        conn.commit()
        conn.close()
        
        return {
            "result": result["content"],
            "new_node_id": node_id,
            "suggested_next_actions": result.get("next_actions", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")

@app.get("/api/models")
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.post("/api/set-model")
async def set_model(request: Request):
    """Set the active model for menu generation"""
    try:
        data = await request.json()
        model_name = data.get("model_name")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name is required")
        
        ollama_client.set_model(model_name)
        return {"message": f"Model set to {model_name}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set model: {str(e)}")

if __name__ == "__main__":
    print("Starting MenuBot API...")
    print("Available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
