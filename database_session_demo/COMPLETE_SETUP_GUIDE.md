# Complete Database Session Service Demo Setup Guide

This is a comprehensive, step-by-step guide to recreate the Google ADK DatabaseSessionService demo from scratch. Follow each section in order.

## 📋 Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Docker Compose (usually included with Docker Desktop)
- [ ] Git (for version control)
- [ ] Text editor (VS Code, Vim, etc.)
- [ ] Terminal/Command line access

## 🏗️ Step 1: Project Structure Setup

### 1.1 Create Project Directory
```bash
mkdir database_session_demo
cd database_session_demo
```

### 1.2 Initialize Git Repository
```bash
git init
```

### 1.3 Create Basic File Structure
```bash
# Create all necessary files
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

**Final structure should look like:**
```
database_session_demo/
├── .gitignore
├── Dockerfile
├── README.md
├── config.py
├── demo.py
├── docker-compose.yml
├── requirements.txt
├── run_demo.sh
├── simple_agent.py
└── env.example
```

## 🐳 Step 2: Docker Configuration

### 2.1 Create Dockerfile
**File: `Dockerfile`**
```dockerfile
# Simple Dockerfile for Database Session Demo
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Default command (can be overridden)
CMD ["python", "demo.py"]
```

### 2.2 Create docker-compose.yml
**File: `docker-compose.yml`**
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

## 📦 Step 3: Python Dependencies

### 3.1 Create requirements.txt
**File: `requirements.txt`**
```txt
google-adk
psycopg2-binary
python-dotenv
```

## ⚙️ Step 4: Configuration Setup

### 4.1 Create config.py
**File: `config.py`**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration - handles both local and Docker environments
# In Docker, use service name 'db', locally use '127.0.0.1'
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

## 🤖 Step 5: Core Agent Implementation

### 5.1 Create simple_agent.py
**File: `simple_agent.py`**
```python
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
```

## 🎮 Step 6: Interactive Demo Script

### 6.1 Create demo.py
**File: `demo.py`**
```python
"""
Interactive Demo Script for Database Session Service

This script provides an interactive way to test the database session service
with different scenarios.
"""

import asyncio
import sys
from simple_agent import SimpleChatAgent


async def interactive_demo():
    """Interactive demo where users can test session persistence."""
    print("🎯 Interactive Database Session Service Demo")
    print("=" * 50)
    
    # Initialize agent
    agent = SimpleChatAgent(use_database=True)
    
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
    print("\n🧪 Testing Session Persistence")
    print("-" * 30)
    
    user_id = "persistence_test_user"
    
    # Create first agent instance
    print("1️⃣ Creating first agent instance...")
    agent1 = SimpleChatAgent(use_database=True)
    
    # Start conversation and add some data
    session = await agent1.start_conversation(user_id, "This is a persistence test!")
    await agent1.send_message(session.id, user_id, "Please remember this message.")
    await agent1.send_message(session.id, user_id, "What's my favorite color? (It's blue!)")
    
    # List sessions
    print("\n📋 Sessions before 'restart':")
    await agent1.list_sessions(user_id)
    
    # Simulate restart by creating new agent instance
    print("\n🔄 Simulating application restart...")
    agent2 = SimpleChatAgent(use_database=True)
    
    # Check if sessions are still there
    print("\n📋 Sessions after 'restart':")
    sessions = await agent2.list_sessions(user_id)
    
    if sessions:
        print("✅ SUCCESS! Sessions persisted across restart!")
        
        # Continue the conversation
        await agent2.send_message(session.id, user_id, "Do you remember our previous conversation?")
    else:
        print("❌ FAILED! Sessions were lost.")


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
    print("🚀 Running Quick Demo...")
    print("=" * 30)
    
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


if __name__ == "__main__":
    main()
```

## 🚀 Step 7: Automation Script

### 7.1 Create run_demo.sh
**File: `run_demo.sh`**
```bash
#!/bin/bash

# Database Session Service Demo Runner
# This script sets up and runs the demo in Docker

set -e  # Exit on any error

echo "🎯 Database Session Service Demo (Docker)"
echo "=========================================="

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
echo "1. Run interactive demo in container"
echo "2. Run automated demo in container"
echo "3. Access container shell for manual testing"
echo "4. View service logs"
echo "5. Stop all services"

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "🚀 Starting interactive demo in container..."
        docker compose exec app python demo.py
        ;;
    2)
        echo "🚀 Starting automated demo in container..."
        docker compose exec app python demo.py quick
        ;;
    3)
        echo "🐚 Accessing container shell..."
        echo "You can now run: python demo.py, python simple_agent.py, etc."
        docker compose exec app /bin/bash
        ;;
    4)
        echo "📋 Showing service logs..."
        docker compose logs -f
        ;;
    5)
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
echo "📋 Useful Docker commands:"
echo "• View logs: docker compose logs [service_name]"
echo "• Connect to database: docker compose exec db psql -U agent_user -d agent_sessions"
echo "• Access PgAdmin: http://127.0.0.1:8080 (admin@demo.com / admin123)"
echo "• Container shell: docker compose exec app /bin/bash"
echo "• Stop services: docker compose down"
echo "• Clean up everything: docker compose down -v"
```

### 7.2 Make Script Executable
```bash
chmod +x run_demo.sh
```

## 📝 Step 8: Documentation

### 8.1 Create .gitignore
**File: `.gitignore`**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3

# Logs
*.log
```

### 8.2 Create README.md
**File: `README.md`**
```markdown
# Database Session Service Demo

This is a minimal, isolated example demonstrating Google ADK's `DatabaseSessionService` connected to PostgreSQL in Docker. Perfect for learning about persistent conversation sessions!

## 🎯 What This Demo Shows

- **Session Persistence**: How conversations survive application restarts
- **Database Integration**: PostgreSQL storage for session data
- **State Management**: How agents maintain context across interactions
- **Comparison**: Database vs In-Memory session services

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python App    │    │  DatabaseSession │    │   PostgreSQL    │    │    PgAdmin      │
│   (Docker)      │◄──►│     Service      │◄──►│   (Docker)      │    │   (Docker)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Git

### 2. Setup

```bash
# Clone or extract this folder
cd database_session_demo

# 1. Create .env file with your Google API key
cp env.example .env
# Edit .env and replace 'your_google_api_key_here' with your actual API key
# Get your API key from: https://aistudio.google.com/app/apikey

# 2. Start all services (PostgreSQL + Python App + PgAdmin)
docker compose up -d --build

# Wait for services to be ready (about 30-60 seconds)
docker compose logs db

# Optional: Access PgAdmin at http://127.0.0.1:8080
# Login: admin@demo.com / admin123
```

### ⚠️ Important: Google API Key Required

**You must have a Google API key to run this demo.** The Google ADK requires authentication to access Gemini models.

1. **Get your API key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Create .env file**: Copy `env.example` to `.env`
3. **Add your API key**: Replace `your_google_api_key_here` with your actual key

### 3. Run the Demo

#### Option A: Automated Setup Script (Recommended)
```bash
./run_demo.sh
```

#### Option B: Manual Docker Commands
```bash
# Interactive demo
docker compose exec app python demo.py

# Automated demo
docker compose exec app python demo.py quick

# Direct agent demo
docker compose exec app python simple_agent.py

# Container shell for manual testing
docker compose exec app /bin/bash
```

## 📚 Key Concepts Demonstrated

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
- **In-Memory**: Sessions lost on restart

### 3. State Management
```python
# State persists across messages
session.state["message_count"] = 5
session.state["user_preferences"] = {"theme": "dark"}
```

### 4. Event History
- All messages stored chronologically
- Full conversation context available
- Tool calls and responses tracked

## 🔧 Configuration

### Environment Variables

The demo requires these environment variables to be set:

```bash
# .env file (create from env.example)
GOOGLE_API_KEY=your_actual_google_api_key_here  # REQUIRED
GOOGLE_MODEL_NAME=gemini-2.5-pro                # Optional
DATABASE_URL=postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions
APP_NAME=demo_agent
PGADMIN_EMAIL=admin@demo.com
PGADMIN_PASSWORD=admin123
```

### Docker Environment Variables

The application automatically uses the correct database URL based on the environment:

```yaml
# docker-compose.yml
environment:
  DATABASE_URL: postgresql://agent_user:agent_password@db:5432/agent_sessions  # Docker service name
  APP_NAME: demo_agent
  GOOGLE_API_KEY: ${GOOGLE_API_KEY}                    # From .env file
  GOOGLE_MODEL_NAME: ${GOOGLE_MODEL_NAME:-gemini-2.5-pro}
```

### Local Development (if needed)

Edit `config.py` for local development:

```python
# Google ADK configuration - REQUIRED
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Must be set in .env

# Database connection (matches main codebase pattern)
DATABASE_URL = "postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions"

# App identifier
APP_NAME = "demo_agent"

# PgAdmin credentials (optional)
PGADMIN_EMAIL = "admin@demo.com"
PGADMIN_PASSWORD = "admin123"
```

## 🧪 Testing Scenarios

### Scenario 1: Basic Persistence
1. Start conversation
2. Send messages
3. Restart app (simulated)
4. Continue conversation
5. ✅ Previous context preserved

### Scenario 2: Multiple Users
1. Create sessions for different users
2. Verify isolation
3. Test concurrent access

### Scenario 3: Session Cleanup
1. Create test sessions
2. Delete specific sessions
3. Verify cleanup

## 📊 Database Schema

The `DatabaseSessionService` automatically creates these tables:

- `sessions`: Session metadata and state
- `events`: Conversation history
- `session_state`: Persistent state storage

## 🔍 Troubleshooting

### Docker Service Issues
```bash
# Check if all services are running
docker compose ps

# View logs for specific service
docker compose logs db
docker compose logs app
docker compose logs pgadmin

# Restart specific service
docker compose restart db
docker compose restart app

# Rebuild and restart all services
docker compose down
docker compose up -d --build

# Access PgAdmin to inspect database
# Open http://127.0.0.1:8080 in browser
# Login with admin@demo.com / admin123
```

### Container Debugging
```bash
# Access app container shell
docker compose exec app /bin/bash

# Check Python dependencies in container
docker compose exec app pip list

# Test database connection from container
docker compose exec app python -c "from google.adk.sessions import DatabaseSessionService; print('✅ ADK installed')"
```

### Port Conflicts
If ports 5432, 8000, or 8080 are in use:
```yaml
# Edit docker-compose.yml
services:
  db:
    ports:
      - 127.0.0.1:5433:5432  # Use different port
  app:
    ports:
      - 127.0.0.1:8001:8000  # Use different port
  pgadmin:
    ports:
      - 127.0.0.1:8081:80  # Use different port
```

## 🎓 Learning Objectives

After running this demo, you should understand:

1. **Session Lifecycle**: Create → Use → Persist → Retrieve → Delete
2. **State Management**: How agents maintain context
3. **Database Integration**: PostgreSQL setup and connection
4. **Persistence Benefits**: Why database sessions matter for production
5. **ADK Architecture**: How Google ADK handles session management

## 🔗 Related Resources

- [Google ADK Sessions Documentation](https://google.github.io/adk-docs/sessions/session/#sessionservice-implementations)
- [DatabaseSessionService Source](https://github.com/google/adk-python/blob/main/src/google/adk/sessions/database_session_service.py)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)

## 🧹 Cleanup

```bash
# Stop and remove containers
docker compose down

# Remove database volume (⚠️ deletes all data)
docker compose down -v
```

## 💡 Next Steps

1. **Custom Tools**: Add your own function tools
2. **Complex State**: Store structured data in session state
3. **Multi-Agent**: Multiple agents sharing sessions
4. **Production**: Deploy with proper security and monitoring
5. **Integration**: Connect to your existing application

## 🤝 Study Group Usage

This demo is perfect for:
- **Presentations**: Show live persistence demo
- **Hands-on Learning**: Interactive exploration
- **Code Review**: Understand ADK session architecture
- **Experimentation**: Modify and test different scenarios

Happy learning! 🚀
```

## 🔑 Step 9: API Key Setup

### 9.1 Create Environment File
**File: `env.example`**
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

### 9.2 Get Google API Key
1. **Visit**: [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Sign in** with your Google account
3. **Create API Key** (click "Create API Key")
4. **Copy the key** (starts with `AIza...`)

### 9.3 Create Your .env File
```bash
# Copy the example file
cp env.example .env

# Edit .env and replace 'your_google_api_key_here' with your actual key
# Example:
# GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ CRITICAL**: You must set up your Google API key before running the demo. The demo will fail without it!

## 🧪 Step 10: Testing and Validation

### 10.1 Test Docker Setup
```bash
# Test Docker Compose syntax
docker compose config

# Build and start services
docker compose up -d --build

# Check service status
docker compose ps

# View logs
docker compose logs db
docker compose logs app
```

### 10.2 Test Application
```bash
# Run automated demo
docker compose exec app python demo.py quick

# Run interactive demo
docker compose exec app python demo.py

# Test direct agent
docker compose exec app python simple_agent.py
```

### 10.3 Test Database Connection
```bash
# Connect to PostgreSQL
docker compose exec db psql -U agent_user -d agent_sessions

# In psql, check tables
\dt

# Exit psql
\q
```

### 10.4 Test PgAdmin
1. Open browser to `http://127.0.0.1:8080`
2. Login with `admin@demo.com` / `admin123`
3. Add server with host `db`, port `5432`
4. Browse the `agent_sessions` database

## 🚀 Step 11: Final Verification

### 10.1 Complete Test Run
```bash
# Make script executable
chmod +x run_demo.sh

# Run complete demo
./run_demo.sh
```

### 10.2 Verify All Features
- [ ] PostgreSQL starts and is healthy
- [ ] Python app builds and runs
- [ ] PgAdmin is accessible
- [ ] Session persistence works
- [ ] Interactive demo functions
- [ ] Automated demo completes
- [ ] Database tables are created
- [ ] Cleanup works properly

### 10.3 Git Commit
```bash
git add .
git commit -m "Initial database session service demo setup"
```

## 🎉 Success Checklist

- [ ] All files created correctly
- [ ] Docker services start successfully
- [ ] Database connection works
- [ ] Session persistence demonstrated
- [ ] Interactive demo functional
- [ ] PgAdmin accessible
- [ ] Documentation complete
- [ ] Git repository initialized

## 🔧 Common Issues and Solutions

### Issue: Docker not running
**Solution**: Start Docker Desktop and wait for it to fully load

### Issue: Port conflicts
**Solution**: Change ports in docker-compose.yml or stop conflicting services

### Issue: Build failures
**Solution**: Check Dockerfile syntax and ensure all files exist

### Issue: Database connection errors
**Solution**: Wait for PostgreSQL to be healthy, check logs with `docker compose logs db`

### Issue: Permission errors
**Solution**: Ensure run_demo.sh is executable with `chmod +x run_demo.sh`

## 📚 Understanding the Architecture

This demo creates a complete containerized environment with:

1. **PostgreSQL Database**: Stores session data persistently
2. **Python Application**: Runs the Google ADK agent
3. **PgAdmin Interface**: Web-based database administration
4. **Docker Networking**: Services communicate via Docker network
5. **Volume Persistence**: Database data survives container restarts

The key learning points are:
- How Google ADK's DatabaseSessionService works
- Session persistence across application restarts
- Docker containerization best practices
- Database integration patterns
- State management in conversational AI

This setup provides a production-ready foundation for understanding and implementing persistent session management in AI applications.
