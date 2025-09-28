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
