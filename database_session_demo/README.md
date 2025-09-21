# Database Session Service Demo

A simple, focused demo showing how to use Google ADK's `DatabaseSessionService` with PostgreSQL in Docker. Perfect for learning about persistent conversation sessions!

## 🎯 What You'll Learn

- **Session Persistence**: How conversations survive application restarts
- **Database Integration**: PostgreSQL storage for session data
- **State Management**: How agents maintain context across interactions
- **Production Ready**: Real-world database-backed session management

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Python App    │    │  DatabaseSession │    │   PostgreSQL    │
│   (Docker)      │◄──►│     Service      │◄──►│   (Docker)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

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

# 3. Wait for services to be ready (about 30-60 seconds)
docker compose logs db

# 4. Run the demo
./run_demo.sh
```

### Manual Commands

```bash
# Interactive demo
docker compose exec app python demo.py

# Automated demo
docker compose exec app python demo.py quick

# Direct agent demo
docker compose exec app python simple_agent.py
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

### 4. Event History
- All messages stored chronologically
- Full conversation context available
- Tool calls and responses tracked

## 🔧 Configuration

### Required Environment Variables

```bash
# .env file (create from env.example)
GOOGLE_API_KEY=your_actual_google_api_key_here  # REQUIRED
GOOGLE_MODEL_NAME=gemini-2.5-pro                # Optional
DATABASE_URL=postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions
APP_NAME=demo_agent
```

### Docker Environment

The application automatically uses the correct database URL:
- **Local**: `postgresql://agent_user:agent_password@127.0.0.1:5432/agent_sessions`
- **Docker**: `postgresql://agent_user:agent_password@db:5432/agent_sessions`

## 🧪 Demo Scenarios

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

# Restart services
docker compose restart

# Rebuild everything
docker compose down
docker compose up -d --build
```

### Database Connection Issues
```bash
# Test database connection
docker compose exec db psql -U agent_user -d agent_sessions

# Check if tables were created
docker compose exec db psql -U agent_user -d agent_sessions -c "\dt"
```

### Container Debugging
```bash
# Access app container shell
docker compose exec app /bin/bash

# Test Python dependencies
docker compose exec app python -c "from google.adk.sessions import DatabaseSessionService; print('✅ ADK installed')"
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

Happy learning! 🚀