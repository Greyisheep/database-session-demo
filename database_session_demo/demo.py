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
