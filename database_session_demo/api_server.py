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
            # Split on comma, but handle case where there might not be one
            parts = data_uri.split(",", 1)
            if len(parts) == 2:
                header, b64_data = parts
                mime_match = re.match(r"data:(.*?);base64", header)
                mime_type = mime_match.group(1) if mime_match else "text/plain"
            else:
                # No comma found, treat as raw base64
                b64_data = data_uri[5:]  # Remove "data:" prefix
                mime_type = "text/plain"
        else:
            # Raw base64 string
            b64_data = data_uri
            mime_type = "text/plain"
        
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
            
            # Validate file size (max 10MB)
            if len(file_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
            
            # Validate file is not empty
            if len(file_bytes) == 0:
                raise HTTPException(status_code=400, detail="Empty file not allowed.")
            
            mime_type = file.content_type or "application/octet-stream"
            filename = file.filename or "upload"
            
            # Validate MIME type for supported formats
            supported_types = [
                "text/plain", "text/html", "text/css", "text/javascript",
                "application/json", "application/pdf", "application/xml",
                "image/jpeg", "image/png", "image/gif", "image/webp",
                "audio/mpeg", "audio/wav", "video/mp4", "video/webm"
            ]
            
            if mime_type not in supported_types:
                print(f"⚠️ Warning: Unsupported MIME type {mime_type}, proceeding anyway...")
            
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
