# Code-Along Guide Part 2: Multimodal Router with FastAPI

This guide extends the database session demo with a FastAPI-based multimodal router that can handle file uploads and base64 data URIs. Perfect for building production-ready agent APIs!

## 🎯 Session Overview

**Goal**: Build a FastAPI router that accepts multimodal input (text + files) and integrates with our database session service using ADK Artifacts for efficient context management
**Duration**: 30-45 minutes  
**Prerequisites**: Completed Part 1, basic FastAPI knowledge

## 🚀 What's New: ADK Artifacts

This implementation includes **Google ADK Artifacts** for efficient file context management:

- **Efficient Context**: Files are stored as artifacts and loaded only when relevant
- **Cost Optimization**: Reduces token usage by not re-sending files in every message
- **Performance**: Faster responses for follow-up questions
- **Memory Management**: Better handling of large files and long conversations

Learn more: [ADK Artifacts Documentation](https://google.github.io/adk-docs/artifacts/) | [2-Minute ADK: Manage Context Efficiently With Artifacts](https://medium.com/google-cloud/2-minute-adk-manage-context-efficiently-with-artifacts-6fcc6683d274)

## 📋 Step-by-Step Build Process

### Step 1: Enhanced Multimodal Agent (10 minutes)

**What we're doing**: Create an agent that supports artifacts for efficient file handling

Create `multimodal_agent.py`:
```python
"""
Enhanced Multimodal Agent with Artifacts Support

This demonstrates how to use Google ADK's DatabaseSessionService
with PostgreSQL and artifacts for efficient multimodal processing.
"""

import asyncio
import base64
import uuid
from typing import List, Optional, Tuple
from google.adk.sessions import DatabaseSessionService
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, load_artifacts
from google.adk.runners import Runner
from google.adk.apps import App
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types
from config import DATABASE_URL, APP_NAME


class MultimodalChatAgent:
    """An enhanced agent that supports multimodal input with artifacts for efficiency."""
    
    def __init__(self):
        """Initialize the agent with database session service and artifacts support."""
        print(f"🔗 Connecting to PostgreSQL: {DATABASE_URL}")
        self.session_service = DatabaseSessionService(db_url=DATABASE_URL)
        
        # Create function tools for demonstration
        self.tools = [
            FunctionTool(func=self._get_current_time),
            FunctionTool(func=self._count_messages),
            load_artifacts  # Tool to load artifacts dynamically
        ]
        
        # Create the LLM agent with artifacts support
        self.agent = LlmAgent(
            model="gemini-2.5-pro",
            name="MultimodalChatAgent",
            description="A multimodal chat agent that efficiently handles files with artifacts",
            tools=self.tools
        )
        
        # Create the app with artifacts plugin for efficient file handling
        self.app = App(
            name="multimodal_agent_app",
            root_agent=self.agent,
            plugins=[SaveFilesAsArtifactsPlugin()],
        )
        
        # Initialize the artifacts service
        try:
            print("🔧 Initializing artifacts service...")
            self.artifact_service = InMemoryArtifactService()
            print("✅ Multimodal agent with artifacts initialized successfully!")
        except Exception as e:
            print(f"⚠️ Warning: Artifacts service initialization issue: {e}")
            print("   Continuing with basic functionality...")
            self.artifact_service = None
    
    def _get_current_time(self) -> str:
        """Simple tool that returns current time."""
        import datetime
        return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _count_messages(self) -> str:
        """Tool that counts messages in the current session."""
        return "This tool demonstrates how tools can access session data"
    
    def _process_file_input(self, file_bytes: bytes, mime_type: str, filename: str) -> str:
        """Process file input and return data URI for the agent."""
        # Create data URI for the file
        b64_data = base64.b64encode(file_bytes).decode()
        data_uri = f"data:{mime_type};base64,{b64_data}"
        
        print(f"📁 Processed file: {filename} ({mime_type}, {len(file_bytes)} bytes)")
        return data_uri
    
    async def start_conversation(self, user_id: str, initial_message: str = None, file_data: Optional[Tuple[bytes, str, str]] = None):
        """Start a new conversation session with optional file input."""
        print(f"\n🚀 Starting new conversation for user: {user_id}")
        
        # Create a new session
        session = await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            state={"conversation_started": True, "message_count": 0, "has_files": False}
        )
        
        print(f"✅ Session created with ID: {session.id}")
        print(f"📊 Initial state: {session.state}")
        
        if initial_message or file_data:
            await self.send_message(session.id, user_id, initial_message or "Hello!", file_data)
        
        return session
    
    async def send_message(self, session_id: str, user_id: str, message: str, file_data: Optional[Tuple[bytes, str, str]] = None):
        """Send a message with optional file attachment and get agent response."""
        print(f"\n💬 User: {message}")
        if file_data:
            file_bytes, mime_type, filename = file_data
            print(f"📁 File attached: {filename} ({mime_type})")
        
        # Get the session
        session = await self.session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            print("❌ Session not found!")
            return None
        
        # Update message count in state
        current_count = session.state.get("message_count", 0)
        session.state["message_count"] = current_count + 1
        
        if file_data:
            session.state["has_files"] = True
        
        # Create runner with artifacts service support
        if self.artifact_service:
            runner = Runner(
                app_name=APP_NAME, 
                agent=self.app.root_agent, 
                session_service=self.session_service,
                artifact_service=self.artifact_service
            )
        else:
            # Fallback to basic runner without artifacts
            runner = Runner(
                app_name=APP_NAME, 
                agent=self.agent, 
                session_service=self.session_service
            )
        
        # Build message parts
        parts = [types.Part(text=message)]
        
        # Add file data if provided
        if file_data:
            file_bytes, mime_type, filename = file_data
            # Create data URI for the file
            data_uri = self._process_file_input(file_bytes, mime_type, filename)
            parts.append(types.Part(text=f"FILE_DATA::{data_uri}"))
            # Also add the file as bytes for the agent to process
            parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime_type))
        
        # Create Content object for the message
        content = types.Content(role="user", parts=parts)
        
        # Collect events from the agent
        events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content
        ):
            events.append(event)
        
        # Find the response text from events
        response_text = "No response generated"
        for event in events:
            if hasattr(event, 'text') and event.text:
                response_text = event.text
                break
            elif hasattr(event, 'content') and event.content:
                response_text = event.content
                break
        
        print(f"🤖 Agent: {response_text}")
        print(f"📊 Updated state: {session.state}")
        
        return response_text
    
    async def list_sessions(self, user_id: str):
        """List all sessions for a user."""
        print(f"\n📋 Listing sessions for user: {user_id}")
        
        response = await self.session_service.list_sessions(
            app_name=APP_NAME,
            user_id=user_id
        )
        sessions = response.sessions
        
        print(f"Found {len(sessions)} sessions:")
        for session in sessions:
            print(f"  - ID: {session.id}")
            print(f"    Last update: {session.last_update_time}")
            print(f"    Events: {len(session.events)}")
            print(f"    State: {session.state}")
        
        return sessions
    
    async def cleanup_session(self, session_id: str, user_id: str):
        """Delete a session."""
        print(f"\n🗑️ Deleting session: {session_id}")
        
        result = await self.session_service.delete_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"✅ Session deleted: {result}")
        return result


async def demo_multimodal_persistence():
    """Demonstrate multimodal database session persistence with artifacts."""
    print("=" * 60)
    print("MULTIMODAL DATABASE SESSION SERVICE DEMO")
    print("=" * 60)
    print("This demo shows how conversations with files persist across restarts!")
    
    user_id = "multimodal_demo_user"
    
    print("\n🚀 Starting multimodal conversation with database session service...")
    agent = MultimodalChatAgent()
    
    # Create a simple test file
    test_file_content = b"This is a test file for multimodal processing!"
    test_file_data = (test_file_content, "text/plain", "test.txt")
    
    # Start conversation with file
    session = await agent.start_conversation(
        user_id, 
        "Hello! I'm testing multimodal session persistence with this file.",
        file_data=test_file_data
    )
    
    # Send a few more messages
    await agent.send_message(session.id, user_id, "What time is it?")
    await agent.send_message(session.id, user_id, "Can you remember the file I uploaded?")
    
    # List sessions
    await agent.list_sessions(user_id)
    
    # Now create a new agent instance (simulating app restart)
    print("\n🔄 Simulating application restart...")
    print("(In a real application, this would be a server restart)")
    agent2 = MultimodalChatAgent()
    
    # The session should still be there!
    print("\n✅ Checking if sessions survived the restart...")
    await agent2.list_sessions(user_id)
    
    # Continue the conversation
    await agent2.send_message(session.id, user_id, "I'm back! Do you remember our conversation and the file?")
    
    print("\n" + "=" * 60)
    print("MULTIMODAL DEMO COMPLETE!")
    print("=" * 60)
    print("Key takeaways:")
    print("• DatabaseSessionService persists data across restarts")
    print("• Artifacts plugin efficiently handles file uploads")
    print("• Sessions maintain conversation history and file context")
    print("• Perfect for production multimodal applications!")
    print("• PostgreSQL stores all session data reliably")


if __name__ == "__main__":
    asyncio.run(demo_multimodal_persistence())
```

**Key points to explain**:
- "Artifacts plugin automatically handles file storage efficiently"
- "load_artifacts tool loads files only when needed"
- "This prevents sending large files repeatedly to the LLM"
- "Database sessions persist everything across restarts"

### Step 2: FastAPI Router (15 minutes)

**What we're doing**: Create a REST API that accepts multimodal input

Create `api_server.py`:
```python
"""
FastAPI Server for Multimodal Database Session Demo

This provides a REST API for testing the multimodal agent with database session persistence.
Supports both file uploads and base64 data URIs for maximum flexibility.
"""

import asyncio
import base64
import uuid
import re
from typing import List, Optional, Tuple
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from multimodal_agent import MultimodalChatAgent
from config import APP_NAME


# Pydantic models for API responses
class AgentResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    message_count: int
    has_files: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str


class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: AgentResponse


# Initialize FastAPI app
app = FastAPI(
    title="Multimodal Database Session Demo API",
    description="REST API for testing multimodal agents with database session persistence",
    version="1.0.0"
)

# Add CORS middleware for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent
    print("🚀 Starting Multimodal Database Session Demo API...")
    agent = MultimodalChatAgent()
    print("✅ Agent initialized successfully!")


def process_data_uri(data_uri: str) -> Tuple[bytes, str, str]:
    """Process base64 data URI and return file data."""
    try:
        # Handle both full data URIs and raw base64
        if data_uri.startswith("data:"):
            header, b64_data = data_uri.split(",", 1)
            mime_match = re.match(r"data:(.*?);base64", header)
            mime_type = mime_match.group(1) if mime_match else "image/png"
        else:
            # Raw base64 string
            b64_data = data_uri
            mime_type = "image/png"
        
        file_bytes = base64.b64decode(b64_data)
        ext = mime_type.split("/")[-1] if "/" in mime_type else "bin"
        filename = f"upload_{uuid.uuid4().hex[:8]}.{ext}"
        
        return file_bytes, mime_type, filename
        
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid data_uri: {exc}")


@app.post(
    "/chat",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successful agent response"},
        400: {"description": "Bad request - invalid input"},
        500: {"description": "Internal server error"}
    }
)
async def chat_with_agent(
    user_input: str = Form(..., description="User message or question"),
    file: Optional[UploadFile] = File(None, description="Optional file upload"),
    data_uri: Optional[str] = Form(None, description="Optional base64 data URI"),
    user_id: str = Form("demo_user", description="User identifier"),
    session_id: Optional[str] = Form(None, description="Existing session ID"),
    new_session: bool = Form(False, description="Force creation of new session")
):
    """
    Chat with the multimodal agent.
    
    Supports both file uploads and base64 data URIs for maximum flexibility.
    Sessions are automatically managed and persisted to PostgreSQL.
    """
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        # Process file input (either upload or data URI)
        file_data = None
        if file is not None:
            file_bytes = await file.read()
            mime_type = file.content_type or "application/octet-stream"
            filename = file.filename or "upload"
            file_data = (file_bytes, mime_type, filename)
            print(f"📁 Processed file upload: {filename} ({mime_type}, {len(file_bytes)} bytes)")
            
        elif data_uri is not None:
            file_bytes, mime_type, filename = process_data_uri(data_uri)
            file_data = (file_bytes, mime_type, filename)
            print(f"📁 Processed data URI: {filename} ({mime_type}, {len(file_bytes)} bytes)")
        
        # Handle session management
        if new_session or session_id is None:
            # Create new session
            session = await agent.start_conversation(
                user_id=user_id,
                initial_message=user_input,
                file_data=file_data
            )
            session_id = session.id
        else:
            # Continue existing session
            response = await agent.send_message(
                session_id=session_id,
                user_id=user_id,
                message=user_input,
                file_data=file_data
            )
        
        # Get session info for response
        session = await agent.session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Extract the latest response from the session events
        response_text = "No response generated"
        if session.events:
            for event in reversed(session.events):
                if hasattr(event, 'content') and event.content:
                    parts = getattr(event.content, 'parts', [])
                    if parts:
                        first_part = parts[0]
                        if hasattr(first_part, 'text') and first_part.text:
                            response_text = first_part.text
                            break
        
        # Build response
        response_data = AgentResponse(
            response=response_text,
            session_id=session_id,
            user_id=user_id,
            message_count=session.state.get("message_count", 0),
            has_files=session.state.get("has_files", False)
        )
        
        return SuccessResponse(
            success=True,
            message="Agent response generated successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sessions/{user_id}")
async def list_user_sessions(user_id: str):
    """List all sessions for a user."""
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        sessions = await agent.list_sessions(user_id)
        
        session_list = []
        for session in sessions:
            session_list.append({
                "id": session.id,
                "user_id": session.user_id,
                "last_update": session.last_update_time,
                "event_count": len(session.events),
                "state": session.state
            })
        
        return {
            "success": True,
            "message": f"Found {len(session_list)} sessions for user {user_id}",
            "data": session_list
        }
        
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    """Delete a specific session."""
    try:
        if agent is None:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        result = await agent.cleanup_session(session_id, user_id)
        
        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully",
            "data": {"deleted": result}
        }
        
    except Exception as e:
        print(f"❌ Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "service": "multimodal-database-session-demo"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Multimodal Database Session Demo API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat - Chat with the multimodal agent",
            "sessions": "GET /sessions/{user_id} - List user sessions",
            "delete_session": "DELETE /sessions/{user_id}/{session_id} - Delete a session",
            "health": "GET /health - Health check",
            "docs": "GET /docs - API documentation"
        },
        "features": [
            "Multimodal input (text + files)",
            "Database session persistence",
            "File upload support",
            "Base64 data URI support",
            "Session management"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Multimodal Database Session Demo API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Key points to explain**:
- "FastAPI provides automatic API documentation"
- "Form data handles both text and file uploads"
- "Base64 data URIs allow programmatic file sending"
- "Session management is transparent to the client"

### Step 3: Update Dependencies (2 minutes)

**What we're doing**: Add FastAPI dependencies

Update `requirements.txt`:
```txt
google-adk
psycopg2-binary
python-dotenv
fastapi
uvicorn[standard]
python-multipart
```

### Step 4: Update Docker Configuration (5 minutes)

**What we're doing**: Update Docker setup for the API server

Update `docker-compose.yml`:
```yaml
services:
  db:
    container_name: demo_postgres_db
    image: postgres:17-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: agent_sessions
      POSTGRES_USER: agent_user
      POSTGRES_PASSWORD: agent_password
    networks:
      - demo_network
    ports:
      - 127.0.0.1:5432:5432
    restart: unless-stopped
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "pg_isready -U agent_user -d agent_sessions",
        ]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    container_name: demo_python_app
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://agent_user:agent_password@db:5432/agent_sessions
      APP_NAME: demo_agent
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      GOOGLE_MODEL_NAME: ${GOOGLE_MODEL_NAME:-gemini-2.5-pro}
    ports:
      - 127.0.0.1:8000:8000
    networks:
      - demo_network
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    stdin_open: true
    tty: true
    command: ["python", "api_server.py"]  # Run the API server

  pgadmin:
    container_name: demo_pgadmin
    image: dpage/pgadmin4:8.12
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@demo.com
      PGADMIN_DEFAULT_PASSWORD: admin123
    ports:
      - 127.0.0.1:8080:80
    networks:
      - demo_network
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - pgadmin_data:/var/lib/pgadmin

networks:
  demo_network:
    name: demo_network
    driver: bridge

volumes:
  postgres_data:
  pgadmin_data:
```

### Step 5: Test Examples (10 minutes)

**What we're doing**: Create test examples for the API

Create `test_api.py`:
```python
"""
Test examples for the Multimodal Database Session Demo API

This script demonstrates how to use the API with various input methods.
"""

import requests
import base64
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_text_only_chat():
    """Test text-only chat."""
    print("\n💬 Testing text-only chat...")
    
    data = {
        "user_input": "Hello! What time is it?",
        "user_id": "test_user_1"
    }
    
    response = requests.post(f"{BASE_URL}/chat", data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result['data']['response']}")
    print(f"Session ID: {result['data']['session_id']}")
    
    return result['data']['session_id']

def test_file_upload():
    """Test file upload."""
    print("\n📁 Testing file upload...")
    
    # Create a test file
    test_content = b"This is a test file for the multimodal API!"
    
    files = {
        "file": ("test.txt", test_content, "text/plain")
    }
    
    data = {
        "user_input": "Please analyze this file",
        "user_id": "test_user_2"
    }
    
    response = requests.post(f"{BASE_URL}/chat", data=data, files=files)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result['data']['response']}")
    print(f"Has files: {result['data']['has_files']}")
    
    return result['data']['session_id']

def test_data_uri():
    """Test base64 data URI."""
    print("\n🔗 Testing base64 data URI...")
    
    # Create base64 data URI
    test_content = b"This is base64 encoded content!"
    b64_data = base64.b64encode(test_content).decode()
    data_uri = f"data:text/plain;base64,{b64_data}"
    
    data = {
        "user_input": "Please analyze this base64 encoded content",
        "data_uri": data_uri,
        "user_id": "test_user_3"
    }
    
    response = requests.post(f"{BASE_URL}/chat", data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result['data']['response']}")
    print(f"Has files: {result['data']['has_files']}")
    
    return result['data']['session_id']

def test_session_continuation(session_id, user_id):
    """Test continuing an existing session."""
    print(f"\n🔄 Testing session continuation for {session_id}...")
    
    data = {
        "user_input": "Do you remember our previous conversation?",
        "user_id": user_id,
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/chat", data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {result['data']['response']}")
    print(f"Message count: {result['data']['message_count']}")

def test_list_sessions(user_id):
    """Test listing user sessions."""
    print(f"\n📋 Testing session listing for {user_id}...")
    
    response = requests.get(f"{BASE_URL}/sessions/{user_id}")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Found {len(result['data'])} sessions:")
    for session in result['data']:
        print(f"  - {session['id']}: {session['event_count']} events")

def main():
    """Run all tests."""
    print("🚀 Starting Multimodal API Tests")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health check failed!")
        return
    
    # Test text-only chat
    session1 = test_text_only_chat()
    
    # Test file upload
    session2 = test_file_upload()
    
    # Test data URI
    session3 = test_data_uri()
    
    # Test session continuation
    test_session_continuation(session1, "test_user_1")
    
    # Test listing sessions
    test_list_sessions("test_user_1")
    test_list_sessions("test_user_2")
    test_list_sessions("test_user_3")
    
    print("\n✅ All tests completed!")
    print("\n📖 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
```

### Step 6: Update Demo Runner (5 minutes)

**What we're doing**: Update the demo runner to support the API server

Update `run_demo.sh`:
```bash
#!/bin/bash

# Database Session Service Demo Runner
# Simple setup and demo runner for learning database sessions

set -e  # Exit on any error

echo "🎯 Database Session Service Demo"
echo "================================"
echo "Learn how database sessions persist across application restarts!"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists and has GOOGLE_API_KEY
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please create .env file with your Google API key:"
    echo "   1. Copy: cp env.example .env"
    echo "   2. Edit .env and add your GOOGLE_API_KEY"
    echo "   3. Get API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Check if GOOGLE_API_KEY is set in .env
if ! grep -q "GOOGLE_API_KEY=AIza" .env 2>/dev/null; then
    echo "❌ GOOGLE_API_KEY not properly set in .env file!"
    echo "📋 Please:"
    echo "   1. Edit .env file"
    echo "   2. Replace 'your_google_api_key_here' with your actual API key"
    echo "   3. Get API key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

echo "✅ Environment configuration looks good!"

# Check if services are already running
if docker compose ps | grep -q "db.*Up"; then
    echo "✅ Services are already running"
else
    echo "🚀 Starting all services (PostgreSQL + Python App + PgAdmin)..."
    docker compose up -d --build
    
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    # Wait for PostgreSQL to be healthy
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker compose exec db pg_isready -U agent_user -d agent_sessions > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            break
        fi
        echo "⏳ Still waiting for PostgreSQL... ($timeout seconds remaining)"
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -eq 0 ]; then
        echo "❌ PostgreSQL failed to start within 60 seconds"
        docker compose logs db
        exit 1
    fi
    
    echo "✅ All services are ready!"
fi

# Show service status
echo ""
echo "📋 Service Status:"
docker compose ps

echo ""
echo "🎮 Demo Options:"
echo "1. Run interactive demo (Part 1 - original)"
echo "2. Run automated demo (Part 1 - quick overview)"
echo "3. Start API server (Part 2 - multimodal router)"
echo "4. Test API with examples (Part 2 - API testing)"
echo "5. Access container shell for manual testing"
echo "6. Stop all services"

read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo "🚀 Starting interactive demo (Part 1)..."
        echo "This will let you test session persistence step by step!"
        docker compose exec app python demo.py
        ;;
    2)
        echo "🚀 Starting automated demo (Part 1)..."
        echo "This will run a quick demonstration of persistence!"
        docker compose exec app python demo.py quick
        ;;
    3)
        echo "🚀 Starting API server (Part 2)..."
        echo "This will start the FastAPI multimodal router!"
        echo "📖 API Documentation: http://localhost:8000/docs"
        echo "🔗 Health Check: http://localhost:8000/health"
        docker compose exec app python api_server.py
        ;;
    4)
        echo "🧪 Testing API with examples..."
        echo "This will run automated tests against the API!"
        docker compose exec app python test_api.py
        ;;
    5)
        echo "🐚 Accessing container shell..."
        echo "You can now run: python demo.py, python api_server.py, etc."
        docker compose exec app /bin/bash
        ;;
    6)
        echo "🛑 Stopping all services..."
        docker compose down
        echo "✅ Services stopped"
        ;;
    *)
        echo "❌ Invalid choice. Starting API server..."
        docker compose exec app python api_server.py
        ;;
esac

echo ""
echo "🎉 Demo session completed!"
echo ""
echo "📋 Key Takeaways:"
echo "• Database sessions persist across application restarts"
echo "• FastAPI provides clean REST API interface"
echo "• Multimodal input supports both files and data URIs"
echo "• Artifacts plugin efficiently handles file processing"
echo "• Perfect for production applications!"
echo ""
echo "📋 Useful commands:"
echo "• View logs: docker compose logs"
echo "• Container shell: docker compose exec app /bin/bash"
echo "• Stop services: docker compose down"
echo "• Clean up everything: docker compose down -v"
echo "• API docs: http://localhost:8000/docs"
```

## 🎯 Code-Along Session Flow

### Opening (5 minutes)
1. **Review Part 1**: "We built database session persistence"
2. **Introduce Part 2**: "Now we'll add a REST API for multimodal input"
3. **Show the goal**: "curl commands that work with files!"

### Building Phase (25 minutes)
1. **Enhanced agent** (10 min) - "Artifacts make file handling efficient"
2. **FastAPI router** (15 min) - "REST API with multimodal support"
3. **Dependencies** (2 min) - "FastAPI and uvicorn"
4. **Docker update** (5 min) - "API server configuration"
5. **Test examples** (10 min) - "How to use the API"
6. **Demo runner** (5 min) - "Easy testing interface"

### Demo Phase (15 minutes)
1. **Start API server** - Show the running server
2. **Test with curl** - Demonstrate API calls
3. **Show API docs** - Interactive documentation
4. **File upload test** - Real multimodal example

### Closing (5 minutes)
1. **Key takeaways** - What they learned
2. **Production benefits** - Why this matters
3. **Next steps** - How to extend this

## 🧪 Testing Your API

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Test Text Chat
```bash
curl -X POST http://localhost:8000/chat \
  -F "user_input=Hello! What can you help me with?" \
  -F "user_id=test_user"
```

### Test File Upload with Artifacts
```bash
curl -X POST http://localhost:8000/chat \
  -F "user_input=Please analyze this image" \
  -F "user_id=test_user" \
  -F "file=@/path/to/your/image.png"
```

### Test Artifacts Efficiency
```bash
# First, upload an image and get the session_id
response=$(curl -s -X POST http://localhost:8000/chat \
  -F "user_input=Please analyze this image" \
  -F "user_id=artifacts_demo" \
  -F "file=@/path/to/your/image.png")

session_id=$(echo $response | jq -r '.data.session_id')

# Ask follow-up questions (artifacts will be loaded efficiently)
curl -X POST http://localhost:8000/chat \
  -F "user_input=What colors do you see?" \
  -F "user_id=artifacts_demo" \
  -F "session_id=$session_id"

curl -X POST http://localhost:8000/chat \
  -F "user_input=Describe the background" \
  -F "user_id=artifacts_demo" \
  -F "session_id=$session_id"
```

### Test Base64 Data URI
```bash
# Create a simple text file and encode it
echo "Hello, World!" > test.txt
base64_data=$(base64 -i test.txt)

curl -X POST http://localhost:8000/chat \
  -F "user_input=What does this data contain?" \
  -F "user_id=test_user" \
  -F "data_uri=data:text/plain;base64,$base64_data"
```

### List Sessions
```bash
curl "http://localhost:8000/sessions?user_id=test_user"
```

### Run Comprehensive Artifacts Test
```bash
# Run the automated test suite
python test_artifacts.py
```

## 💡 Teaching Tips

### Keep It Interactive
- Show the API docs: "http://localhost:8000/docs"
- Test with curl: "Let's make a real API call"
- Upload a file: "See how files are handled efficiently"

### Explain the Why
- "Why FastAPI?" - Automatic docs, type safety, async
- "Why artifacts?" - Efficient file handling, cost savings
- "Why REST API?" - Standard interface, easy integration

### Connect to Real World
- "This is how production APIs work"
- "curl commands work from any language"
- "File uploads are handled efficiently"

## 🚨 Common Issues & Solutions

### API Issues
- **"Connection refused"** - Wait for API server to start
- **"File too large"** - Check FastAPI file size limits
- **"Invalid data URI"** - Verify base64 encoding

### Docker Issues
- **"Port 8000 in use"** - Change port in docker-compose.yml
- **"API not responding"** - Check container logs

## 🎉 Success Metrics

Participants should be able to:
1. ✅ Explain what artifacts do for file handling
2. ✅ Understand FastAPI benefits for agent APIs
3. ✅ Make curl requests to the API
4. ✅ Upload files via API
5. ✅ Understand session management via API
6. ✅ Know how to test the API

## 📚 Follow-up Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google ADK Artifacts Guide](https://medium.com/google-cloud/2-minute-adk-manage-context-efficiently-with-artifacts-6fcc6683d274)
- [ADK Testing Guide](https://google.github.io/adk-docs/get-started/testing/)
- [Multipart Form Data](https://developer.mozilla.org/en-US/docs/Web/API/FormData)

---

**Remember**: The goal is building production-ready APIs! Show how this scales from demo to real applications.
