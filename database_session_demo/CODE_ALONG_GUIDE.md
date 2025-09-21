# Code-Along Guide: Database Session Service Demo

This guide walks you through building the database session demo from scratch, step by step. Perfect for leading a code-along session!

## 🎯 Session Overview

**Goal**: Build a simple agent that demonstrates database session persistence with PostgreSQL
**Duration**: 45-60 minutes
**Prerequisites**: Basic Python knowledge, Docker familiarity

## 📋 Step-by-Step Build Process

### Step 1: Project Setup (5 minutes)

**What we're doing**: Create the basic project structure

```bash
# Create project directory
mkdir database_session_demo
cd database_session_demo

# Initialize git (optional but good practice)
git init

# Create basic files
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch config.py
touch simple_agent.py
touch demo.py
touch run_demo.sh
touch README.md
touch .gitignore
touch env.example
```

**Explain**: "We're creating a clean project structure. Each file has a specific purpose in our demo."

### Step 2: Environment Configuration (5 minutes)

**What we're doing**: Set up configuration management

Create `env.example`:
```bash
# Google ADK Configuration - REQUIRED
# Get your API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Model Configuration (optional)
GOOGLE_MODEL_NAME=gemini-2.5-pro

# Database Configuration (auto-configured for Docker)
DATABASE_URL=postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions

# Agent Configuration
APP_NAME=demo_agent

# PgAdmin Configuration (optional)
PGADMIN_EMAIL=admin@demo.com
PGADMIN_PASSWORD=admin123
```

Create `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration - handles both local and Docker environments
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions")

# Google ADK configuration - REQUIRED for LLM functionality
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is required. "
        "Please set it in your .env file or environment. "
        "Get your API key from: https://aistudio.google.com/app/apikey"
    )

# Model configuration
GOOGLE_MODEL_NAME = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-pro")

# Agent configuration
APP_NAME = os.getenv("APP_NAME", "demo_agent")

# PgAdmin configuration (for reference)
PGADMIN_EMAIL = os.getenv("PGADMIN_EMAIL", "admin@demo.com")
PGADMIN_PASSWORD = os.getenv("PGADMIN_PASSWORD", "admin123")

# Environment detection
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"
```

**Explain**: "Configuration management is crucial. We separate environment variables from code for security and flexibility."

### Step 3: Dependencies (3 minutes)

**What we're doing**: Define Python dependencies

Create `requirements.txt`:
```txt
google-adk
python-dotenv
```

**Explain**: "We need the Google ADK for session management and python-dotenv for environment variable loading."

### Step 4: Docker Setup (10 minutes)

**What we're doing**: Create containerized environment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "demo.py"]
```

Create `docker-compose.yml`:
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

**Explain**: "Docker Compose gives us PostgreSQL, our Python app, and PgAdmin in one setup. Notice the health checks and dependencies."

### Step 5: Core Agent Class (15 minutes)

**What we're doing**: Build the main agent with database session service

Create `simple_agent.py`:
```python
"""
Database Session Service Demo

This demonstrates how to use Google ADK's DatabaseSessionService
with PostgreSQL to persist conversation sessions.
"""

import asyncio
from google.adk.sessions import DatabaseSessionService
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.genai import types
from config import DATABASE_URL, APP_NAME


class SimpleChatAgent:
    """A minimal agent that demonstrates database session persistence."""
    
    def __init__(self):
        """Initialize the agent with database session service."""
        print(f"🔗 Connecting to PostgreSQL: {DATABASE_URL}")
        self.session_service = DatabaseSessionService(db_url=DATABASE_URL)
        
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
    """Demonstrate database session persistence."""
    print("=" * 60)
    print("DATABASE SESSION SERVICE DEMO")
    print("=" * 60)
    print("This demo shows how conversations persist across application restarts!")
    
    user_id = "demo_user"
    
    print("\n🚀 Starting conversation with database session service...")
    agent = SimpleChatAgent()
    
    # Start conversation
    session = await agent.start_conversation(
        user_id, 
        "Hello! My name is Alice and I'm testing session persistence."
    )
    
    # Send a few messages
    await agent.send_message(session.id, user_id, "What time is it?")
    await agent.send_message(session.id, user_id, "Can you remember my name?")
    
    # List sessions
    await agent.list_sessions(user_id)
    
    # Now create a new agent instance (simulating app restart)
    print("\n🔄 Simulating application restart...")
    print("(In a real application, this would be a server restart)")
    agent2 = SimpleChatAgent()
    
    # The session should still be there!
    print("\n✅ Checking if sessions survived the restart...")
    await agent2.list_sessions(user_id)
    
    # Continue the conversation
    await agent2.send_message(session.id, user_id, "I'm back! Do you remember our conversation?")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("Key takeaways:")
    print("• DatabaseSessionService persists data across restarts")
    print("• Sessions maintain conversation history and state")
    print("• Perfect for production applications!")
    print("• PostgreSQL stores all session data reliably")


if __name__ == "__main__":
    asyncio.run(demo_persistence())
```

**Key points to explain**:
- "DatabaseSessionService handles all the persistence automatically"
- "State management lets us track conversation context"
- "The demo shows what happens during an app restart"
- "Tools demonstrate how agents can access session data"

### Step 6: Interactive Demo (10 minutes)

**What we're doing**: Create an interactive demo for hands-on learning

Create `demo.py`:
```python
"""
Interactive Demo Script for Database Session Service

This script provides an interactive way to test the database session service
with PostgreSQL persistence.
"""

import asyncio
import sys
from simple_agent import SimpleChatAgent


async def interactive_demo():
    """Interactive demo where users can test session persistence."""
    print("🎯 Interactive Database Session Service Demo")
    print("=" * 50)
    print("Learn how database sessions persist across application restarts!")
    
    # Initialize agent
    agent = SimpleChatAgent()
    
    while True:
        print("\n📋 Choose an option:")
        print("1. Start new conversation")
        print("2. Continue existing conversation")
        print("3. List all sessions")
        print("4. Test persistence (restart simulation)")
        print("5. Clean up session")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            await start_new_conversation(agent)
        elif choice == "2":
            await continue_conversation(agent)
        elif choice == "3":
            await list_sessions(agent)
        elif choice == "4":
            await test_persistence()
        elif choice == "5":
            await cleanup_session(agent)
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


async def start_new_conversation(agent):
    """Start a new conversation session."""
    user_id = input("Enter user ID: ").strip()
    if not user_id:
        user_id = "demo_user"
    
    message = input("Enter your first message (or press Enter for default): ").strip()
    if not message:
        message = "Hello! I'm testing the database session service."
    
    session = await agent.start_conversation(user_id, message)
    print(f"✅ Conversation started with session ID: {session.id}")


async def continue_conversation(agent):
    """Continue an existing conversation."""
    user_id = input("Enter user ID: ").strip()
    if not user_id:
        user_id = "demo_user"
    
    # List sessions first
    sessions = await agent.list_sessions(user_id)
    
    if not sessions:
        print("❌ No sessions found for this user.")
        return
    
    session_id = input("Enter session ID: ").strip()
    if not session_id:
        print("❌ Session ID is required.")
        return
    
    # Continue chatting
    print(f"\n💬 Continuing conversation {session_id}...")
    print("Type 'quit' to stop chatting.")
    
    while True:
        message = input("\nYou: ").strip()
        if message.lower() == 'quit':
            break
        if message:
            await agent.send_message(session_id, user_id, message)


async def list_sessions(agent):
    """List all sessions for a user."""
    user_id = input("Enter user ID: ").strip()
    if not user_id:
        user_id = "demo_user"
    
    await agent.list_sessions(user_id)


async def test_persistence():
    """Test persistence by creating agent, adding data, then restarting."""
    print("\n🧪 Testing Database Session Persistence")
    print("-" * 40)
    print("This test simulates an application restart to show data persistence")
    
    user_id = "persistence_test_user"
    
    # Create first agent instance
    print("\n1️⃣ Creating first agent instance...")
    agent1 = SimpleChatAgent()
    
    # Start conversation and add some data
    session = await agent1.start_conversation(user_id, "This is a persistence test!")
    await agent1.send_message(session.id, user_id, "Please remember this message.")
    await agent1.send_message(session.id, user_id, "What's my favorite color? (It's blue!)")
    
    # List sessions
    print("\n📋 Sessions before 'restart':")
    await agent1.list_sessions(user_id)
    
    # Simulate restart by creating new agent instance
    print("\n🔄 Simulating application restart...")
    print("(In production, this would be a server restart or deployment)")
    agent2 = SimpleChatAgent()
    
    # Check if sessions are still there
    print("\n📋 Sessions after 'restart':")
    sessions = await agent2.list_sessions(user_id)
    
    if sessions:
        print("✅ SUCCESS! Sessions persisted across restart!")
        print("   This proves that PostgreSQL is storing the session data reliably.")
        
        # Continue the conversation
        await agent2.send_message(session.id, user_id, "Do you remember our previous conversation?")
    else:
        print("❌ FAILED! Sessions were lost.")
        print("   This would indicate a database connection issue.")


async def cleanup_session(agent):
    """Delete a specific session."""
    user_id = input("Enter user ID: ").strip()
    if not user_id:
        user_id = "demo_user"
    
    # List sessions first
    sessions = await agent.list_sessions(user_id)
    
    if not sessions:
        print("❌ No sessions found for this user.")
        return
    
    session_id = input("Enter session ID to delete: ").strip()
    if not session_id:
        print("❌ Session ID is required.")
        return
    
    confirm = input(f"Are you sure you want to delete session {session_id}? (y/N): ").strip().lower()
    if confirm == 'y':
        await agent.cleanup_session(session_id, user_id)
    else:
        print("❌ Deletion cancelled.")


async def quick_demo():
    """Run a quick automated demo."""
    print("🚀 Running Quick Database Session Demo...")
    print("=" * 40)
    
    from simple_agent import demo_persistence
    await demo_persistence()


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_demo())
    else:
        try:
            asyncio.run(interactive_demo())
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure PostgreSQL is running with: docker compose up -d")
            print("This demo requires PostgreSQL to store session data.")


if __name__ == "__main__":
    main()
```

**Explain**: "Interactive demos let participants explore the concepts hands-on. They can test persistence, create sessions, and see the database in action."

### Step 7: Demo Runner Script (5 minutes)

**What we're doing**: Create a convenient way to run the demo

Create `run_demo.sh`:
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
echo "1. Run interactive demo (recommended for learning)"
echo "2. Run automated demo (quick overview)"
echo "3. Access container shell for manual testing"
echo "4. Stop all services"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting interactive demo..."
        echo "This will let you test session persistence step by step!"
        docker compose exec app python demo.py
        ;;
    2)
        echo "🚀 Starting automated demo..."
        echo "This will run a quick demonstration of persistence!"
        docker compose exec app python demo.py quick
        ;;
    3)
        echo "🐚 Accessing container shell..."
        echo "You can now run: python demo.py, python simple_agent.py, etc."
        docker compose exec app /bin/bash
        ;;
    4)
        echo "🛑 Stopping all services..."
        docker compose down
        echo "✅ Services stopped"
        ;;
    *)
        echo "❌ Invalid choice. Starting interactive demo..."
        docker compose exec app python demo.py
        ;;
esac

echo ""
echo "🎉 Demo session completed!"
echo ""
echo "📋 Key Takeaways:"
echo "• Database sessions persist across application restarts"
echo "• PostgreSQL stores conversation history and state reliably"
echo "• Perfect for production applications!"
echo ""
echo "📋 Useful commands:"
echo "• View logs: docker compose logs"
echo "• Container shell: docker compose exec app /bin/bash"
echo "• Stop services: docker compose down"
echo "• Clean up everything: docker compose down -v"
```

Make it executable:
```bash
chmod +x run_demo.sh
```

**Explain**: "This script handles all the setup complexity so participants can focus on learning the concepts."

### Step 8: Documentation (5 minutes)

**What we're doing**: Create clear documentation for participants

Create `README.md`:
```markdown
# Database Session Service Demo

A simple, focused demo showing how to use Google ADK's `DatabaseSessionService` with PostgreSQL in Docker. Perfect for learning about persistent conversation sessions!

## 🎯 What You'll Learn

- **Session Persistence**: How conversations survive application restarts
- **Database Integration**: PostgreSQL storage for session data
- **State Management**: How agents maintain context across interactions
- **Production Ready**: Real-world database-backed session management

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Google API Key (get from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Setup & Run

```bash
# 1. Create .env file with your Google API key
cp env.example .env
# Edit .env and replace 'your_google_api_key_here' with your actual API key

# 2. Start all services
docker compose up -d --build

# 3. Run the demo
./run_demo.sh
```

## 📚 Key Concepts

### 1. Session Creation
```python
session = await session_service.create_session(
    app_name="demo_agent",
    user_id="user123",
    state={"conversation_started": True}
)
```

### 2. Session Persistence
- **Database**: Sessions survive app restarts
- **State**: Conversation context maintained
- **History**: Full message history stored

### 3. State Management
```python
# State persists across messages
session.state["message_count"] = 5
session.state["user_preferences"] = {"theme": "dark"}
```

## 🎓 Learning Objectives

After running this demo, you should understand:

1. **Session Lifecycle**: Create → Use → Persist → Retrieve → Delete
2. **State Management**: How agents maintain context
3. **Database Integration**: PostgreSQL setup and connection
4. **Persistence Benefits**: Why database sessions matter for production
5. **ADK Architecture**: How Google ADK handles session management

Happy learning! 🚀
```

**Explain**: "Good documentation helps participants understand what they're building and why it matters."

## 🎯 Code-Along Session Flow

### Opening (5 minutes)
1. **Introduce the problem**: "What happens to chat conversations when your app restarts?"
2. **Show the solution**: "Database session service persists everything!"
3. **Preview the demo**: "We'll build this step by step"

### Building Phase (35 minutes)
1. **Project setup** (5 min) - "Clean structure is important"
2. **Configuration** (5 min) - "Environment management best practices"
3. **Dependencies** (3 min) - "Only what we need"
4. **Docker setup** (10 min) - "Containerized development"
5. **Core agent** (15 min) - "The heart of our demo"
6. **Interactive demo** (10 min) - "Hands-on learning"
7. **Demo runner** (5 min) - "Making it easy to use"
8. **Documentation** (5 min) - "Helping others understand"

### Demo Phase (15 minutes)
1. **Run the demo** - Show persistence in action
2. **Explain key concepts** - Database vs memory
3. **Q&A** - Address questions
4. **Next steps** - How to extend this

### Closing (5 minutes)
1. **Key takeaways** - What they learned
2. **Production benefits** - Why this matters
3. **Resources** - Where to learn more

## 💡 Teaching Tips

### Keep It Interactive
- Ask questions: "What do you think happens when we restart?"
- Show the database: "Let's see what's stored in PostgreSQL"
- Demonstrate failures: "What if the database is down?"

### Explain the Why
- "Why do we need persistence?"
- "Why PostgreSQL over other databases?"
- "Why Docker for development?"

### Connect to Real World
- "This is how production apps work"
- "Session management is critical for user experience"
- "Database persistence prevents data loss"

### Handle Questions
- **"Can we use other databases?"** - Yes, but PostgreSQL is reliable
- **"What about Redis?"** - Good for caching, but PostgreSQL is better for complex state
- **"How does this scale?"** - Connection pooling, read replicas, etc.

## 🚨 Common Issues & Solutions

### Docker Issues
- **"Docker not running"** - Start Docker Desktop
- **"Port conflicts"** - Change ports in docker-compose.yml
- **"Build failures"** - Check internet connection, try `docker compose build --no-cache`

### API Key Issues
- **"Invalid API key"** - Get new key from Google AI Studio
- **"Rate limiting"** - Wait a few minutes, check quota

### Database Issues
- **"Connection refused"** - Wait for PostgreSQL to start
- **"Tables not created"** - Check logs, restart app container

### Python Issues
- **"Module not found"** - Check requirements.txt, rebuild container
- **"Import errors"** - Verify Google ADK installation

## 🎉 Success Metrics

Participants should be able to:
1. ✅ Explain what database session service does
2. ✅ Understand why persistence matters
3. ✅ Run the demo successfully
4. ✅ Modify the agent (add tools, change state)
5. ✅ Understand the Docker setup
6. ✅ Know how to troubleshoot common issues

## 📚 Follow-up Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Compose Guide](https://docs.docker.com/compose/)
- [Session Management Best Practices](https://example.com)

---

**Remember**: The goal is learning, not perfection. Encourage questions, explain concepts clearly, and make sure everyone follows along!
