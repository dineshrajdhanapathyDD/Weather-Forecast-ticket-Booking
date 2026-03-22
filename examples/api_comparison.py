"""
API Comparison Example

This script demonstrates the difference between the two API endpoints:
1. /recommend - Structured JSON API (Direct Lambda)
2. /chat - Conversational AI (Bedrock Agent)
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod"
RECOMMEND_ENDPOINT = f"{API_BASE_URL}/recommend"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"


def test_structured_api():
    """
    Test the structured /recommend endpoint
    
    Requires:
    - Exact JSON structure
    - Airport codes
    - ISO 8601 date format
    """
    print("=" * 60)
    print("Testing Structured API (/recommend)")
    print("=" * 60)
    
    # Calculate dates (15 days from now for 7 days)
    start_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d')
    
    payload = {
        "destination": "LAX",
        "origin": "JFK",
        "travel_window": {
            "start_date": start_date,
            "end_date": end_date
        }
    }
    
    print(f"\nRequest:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            RECOMMEND_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"\nResponse:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None


def test_conversational_api():
    """
    Test the conversational /chat endpoint
    
    Accepts:
    - Natural language
    - Various date formats
    - City names or airport codes
    """
    print("\n" + "=" * 60)
    print("Testing Conversational API (/chat)")
    print("=" * 60)
    
    # Natural language query
    message = "I want to fly to Los Angeles from New York in about 2 weeks for a week"
    
    payload = {
        "message": message
    }
    
    print(f"\nRequest:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        result = response.json()
        
        if 'response' in result:
            print(f"\nAgent Response:")
            print("-" * 60)
            print(result['response'])
            print("-" * 60)
        else:
            print(f"\nResponse:")
            print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None


def compare_apis():
    """
    Compare both APIs side by side
    """
    print("\n" + "=" * 60)
    print("API Comparison Summary")
    print("=" * 60)
    
    print("\n📊 Structured API (/recommend)")
    print("-" * 60)
    print("✓ Pros:")
    print("  - Lower latency (~1-2 seconds)")
    print("  - Lower cost (~$4 per 1M requests)")
    print("  - Predictable response format")
    print("  - Direct Lambda invocation")
    print("\n✗ Cons:")
    print("  - Requires exact JSON structure")
    print("  - Must provide airport codes")
    print("  - Must format dates correctly")
    print("  - No natural language support")
    
    print("\n\n🤖 Conversational API (/chat)")
    print("-" * 60)
    print("✓ Pros:")
    print("  - Natural language input")
    print("  - Flexible date formats")
    print("  - Extracts information automatically")
    print("  - User-friendly responses")
    print("  - Handles missing information")
    print("\n✗ Cons:")
    print("  - Higher latency (~3-5 seconds)")
    print("  - Higher cost (~$50-100 per 1M requests)")
    print("  - Requires Bedrock access")
    print("  - LLM processing overhead")
    
    print("\n\n💡 Use Cases")
    print("-" * 60)
    print("\nStructured API:")
    print("  - Web dashboards with forms")
    print("  - Mobile apps with date pickers")
    print("  - Programmatic integrations")
    print("  - High-volume applications")
    print("  - Cost-sensitive deployments")
    
    print("\nConversational API:")
    print("  - Chatbots and virtual assistants")
    print("  - Voice interfaces (Alexa, Google Home)")
    print("  - Messaging platforms (Slack, Teams)")
    print("  - Customer support chat")
    print("  - Natural language interfaces")


def test_various_queries():
    """
    Test the conversational API with various query formats
    """
    print("\n" + "=" * 60)
    print("Testing Various Query Formats")
    print("=" * 60)
    
    queries = [
        "I want to fly to Miami from Boston next month",
        "What's the weather like in Hawaii in December?",
        "Should I book a flight to San Francisco from Seattle?",
        "I'm planning a trip to Orlando in August",
        "Compare weather and fares for Las Vegas in July",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 60)
        
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={'message': query},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'response' in result:
                    # Print first 200 characters of response
                    preview = result['response'][:200]
                    print(f"Response preview: {preview}...")
                else:
                    print(f"Status: {response.status_code}")
            else:
                print(f"Error: Status {response.status_code}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()


def main():
    """
    Main function to run all tests
    """
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--structured":
            test_structured_api()
        elif sys.argv[1] == "--conversational":
            test_conversational_api()
        elif sys.argv[1] == "--compare":
            compare_apis()
        elif sys.argv[1] == "--various":
            test_various_queries()
        else:
            print("Usage:")
            print("  python api_comparison.py --structured     # Test structured API")
            print("  python api_comparison.py --conversational # Test conversational API")
            print("  python api_comparison.py --compare        # Compare both APIs")
            print("  python api_comparison.py --various        # Test various queries")
    else:
        # Run all tests
        print("Weather-Wise Flight Booking API Comparison")
        print("=" * 60)
        print("\nNote: Update API_BASE_URL in the script with your actual endpoint")
        print()
        
        test_structured_api()
        test_conversational_api()
        compare_apis()


if __name__ == "__main__":
    main()
