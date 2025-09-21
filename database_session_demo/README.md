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
