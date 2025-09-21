"""
Simple Agent with Database Session Service Demo

This demonstrates how to use Google ADK's DatabaseSessionService
with PostgreSQL to persist conversation sessions.
"""

import asyncio
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.genai import types
from config import DATABASE_URL, APP_NAME


class SimpleChatAgent:
    """A minimal agent that demonstrates database session persistence."""
    
    def __init__(self, use_database=True):
        """
        Initialize the agent with either database or in-memory session service.
        
        Args:
            use_database: If True, use DatabaseSessionService with PostgreSQL.
                         If False, use InMemorySessionService for comparison.
        """
        self.use_database = use_database
        
        if use_database:
            print(f"🔗 Connecting to PostgreSQL: {DATABASE_URL}")
            self.session_service = DatabaseSessionService(db_url=DATABASE_URL)
        else:
            print("🧠 Using in-memory session service (data will be lost on restart)")
            self.session_service = InMemorySessionService()
        
        # Create a simple function tool for demonstration
        self.tools = [
            FunctionTool(func=self._get_current_time),
            FunctionTool(func=self._count_messages)
        ]
        
        # Create the LLM agent
        self.agent = LlmAgent(
            model="gemini-2.5-pro",
            name="SimpleChatAgent",
            description="A simple chat agent that demonstrates session persistence",
            tools=self.tools
        )
    
    def _get_current_time(self) -> str:
        """Simple tool that returns current time."""
        import datetime
        return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    def _count_messages(self) -> str:
        """Tool that counts messages in the current session."""
        # This would need access to the session, but for demo purposes:
        return "This tool demonstrates how tools can access session data"
    
    async def start_conversation(self, user_id: str, initial_message: str = None):
        """Start a new conversation session."""
        print(f"\n🚀 Starting new conversation for user: {user_id}")
        
        # Create a new session
        session = await self.session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            state={"conversation_started": True, "message_count": 0}
        )
        
        print(f"✅ Session created with ID: {session.id}")
        print(f"📊 Initial state: {session.state}")
        
        if initial_message:
            await self.send_message(session.id, user_id, initial_message)
        
        return session
    
    async def send_message(self, session_id: str, user_id: str, message: str):
        """Send a message and get agent response."""
        print(f"\n💬 User: {message}")
        
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
        
        # Create runner and run the agent
        runner = Runner(app_name=APP_NAME, agent=self.agent, session_service=self.session_service)
        
        # Create Content object for the message
        content = types.Content(role="user", parts=[types.Part(text=message)])
        
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


async def demo_persistence():
    """Demonstrate session persistence by comparing database vs in-memory."""
    print("=" * 60)
    print("DATABASE SESSION SERVICE DEMO")
    print("=" * 60)
    
    user_id = "demo_user"
    
    # First, demonstrate database persistence
    print("\n1️⃣ DATABASE SESSION SERVICE (Persistent)")
    print("-" * 40)
    
    db_agent = SimpleChatAgent(use_database=True)
    
    # Start conversation
    session = await db_agent.start_conversation(
        user_id, 
        "Hello! My name is Alice and I'm testing session persistence."
    )
    
    # Send a few messages
    await db_agent.send_message(session.id, user_id, "What time is it?")
    await db_agent.send_message(session.id, user_id, "Can you remember my name?")
    
    # List sessions
    await db_agent.list_sessions(user_id)
    
    # Now create a new agent instance (simulating app restart)
    print("\n🔄 Simulating application restart...")
    db_agent2 = SimpleChatAgent(use_database=True)
    
    # The session should still be there!
    await db_agent2.list_sessions(user_id)
    
    # Continue the conversation
    await db_agent2.send_message(session.id, user_id, "I'm back! Do you remember our conversation?")
    
    # Now demonstrate in-memory (for comparison)
    print("\n\n2️⃣ IN-MEMORY SESSION SERVICE (Non-persistent)")
    print("-" * 40)
    
    memory_agent = SimpleChatAgent(use_database=False)
    
    # Start conversation
    memory_session = await memory_agent.start_conversation(
        user_id, 
        "Hello! This is a test of in-memory sessions."
    )
    
    await memory_agent.send_message(memory_session.id, user_id, "What time is it?")
    
    # Simulate restart
    print("\n🔄 Simulating application restart...")
    memory_agent2 = SimpleChatAgent(use_database=False)
    
    # Sessions are gone!
    await memory_agent2.list_sessions(user_id)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("Key takeaways:")
    print("• DatabaseSessionService persists data across restarts")
    print("• InMemorySessionService loses data on restart")
    print("• Sessions maintain conversation history and state")
    print("• Perfect for production applications!")


if __name__ == "__main__":
    asyncio.run(demo_persistence())
