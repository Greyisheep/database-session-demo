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
