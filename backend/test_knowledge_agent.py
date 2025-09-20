#!/usr/bin/env python3
"""
Simple test script for manually testing knowledge_agent.query_knowledge

Usage:
    python test_knowledge_agent.py

Make sure to set your OPENAI_API_KEY environment variable before running.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.agents.knowledge_agent import query_knowledge, initialize_knowledge_agent


def test_knowledge_agent():
    """Test the knowledge agent with sample queries."""

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return

    print("🤖 Knowledge Agent Test")
    print("=" * 50)
    print(f"✅ API Key found: {api_key[:8]}...")

    try:
        # Initialize the knowledge agent
        print("\n📚 Initializing knowledge agent...")
        initialize_knowledge_agent()
        print("✅ Knowledge agent initialized successfully!")

        # Test queries
        test_queries = [
            "What are the fees for the payment terminal?",
            # "How do I create an account?",
            # "What payment methods are accepted?",
            # "How does the refund process work?",
            # "What are the transaction limits?",
        ]

        print(f"\n🔍 Testing {len(test_queries)} sample queries:")
        print("-" * 50)

        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            print("   Response:")

            try:
                response = query_knowledge(query)
                if response:
                    # Print response with proper indentation
                    for line in response.split("\n"):
                        print(f"   {line}")
                else:
                    print("   (No response)")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")

            print("   " + "-" * 40)

        # Interactive mode
        print(f"\n🎯 Interactive Mode")
        print("Enter your own queries (type 'quit' to exit):")
        print("-" * 50)

        while True:
            try:
                user_query = input("\n💬 Your query: ").strip()

                if user_query.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if not user_query:
                    print("Please enter a query.")
                    continue

                print("🤔 Thinking...")
                response = query_knowledge(user_query)

                if response:
                    print("📝 Response:")
                    for line in response.split("\n"):
                        print(f"   {line}")
                else:
                    print("❌ No response received")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    except Exception as e:
        print(f"❌ Failed to initialize knowledge agent: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure your OPENAI_API_KEY is valid")
        print("2. Check your internet connection")
        print("3. Ensure the vector store files exist in the vector_store directory")


if __name__ == "__main__":
    test_knowledge_agent()
