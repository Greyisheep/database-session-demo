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
