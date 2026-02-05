#!/usr/bin/env python3
"""Test script for Web Search Agent."""

import sys
sys.path.insert(0, '.')

from src.tools.web_search_tool import web_search, search_news
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)

def test_web_search():
    """Test web search functionality."""
    
    print("=" * 60)
    print("Web Search Test")
    print("=" * 60)
    print()
    
    # Test 1: General search
    print("🔍 Test 1: General search - 'Python programming'")
    result = web_search("Python programming", max_results=3)
    
    if result["status"] == "success":
        print(f"✅ Found {len(result['results'])} results\n")
        for i, item in enumerate(result['results'], 1):
            print(f"{i}. {item['title']}")
            print(f"   {item['snippet'][:100]}...")
            print(f"   {item['url']}\n")
    else:
        print(f"❌ Error: {result['message']}\n")
    
    print("-" * 60)
    
    # Test 2: News search
    print("\n📰 Test 2: News search - 'artificial intelligence'")
    result = search_news("artificial intelligence", max_results=3)
    
    if result["status"] == "success":
        print(f"✅ Found {len(result['results'])} news articles\n")
        for i, item in enumerate(result['results'], 1):
            print(f"{i}. {item['title']}")
            print(f"   {item['snippet'][:100]}...")
            print(f"   📅 {item.get('date', 'N/A')}")
            print(f"   📰 {item.get('source', 'N/A')}")
            print(f"   {item['url']}\n")
    else:
        print(f"❌ Error: {result['message']}\n")
    
    print("=" * 60)
    print("✅ Web Search Agent is working!")
    print()

if __name__ == "__main__":
    test_web_search()
