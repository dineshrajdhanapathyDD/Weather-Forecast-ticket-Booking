"""
Test script for Weather-Wise Bedrock Agent

This script tests the agent with various queries to ensure proper functionality.
"""

import json
import boto3
import time
from typing import Dict, Any

# Initialize Lambda client
lambda_client = boto3.client('lambda')

# Test queries
TEST_QUERIES = [
    {
        "name": "Basic query with all details",
        "message": "I want to fly to Los Angeles from New York between July 15, 2024 and July 22, 2024"
    },
    {
        "name": "Query with relative dates",
        "message": "I'm planning a trip to Miami from Boston in mid-August"
    },
    {
        "name": "Query with city names",
        "message": "Should I book a flight to San Francisco from Seattle next month?"
    },
    {
        "name": "Weather-focused query",
        "message": "What's the weather like in Hawaii in December?"
    },
    {
        "name": "Fare-focused query",
        "message": "Are flight prices to Orlando rising or dropping?"
    },
]


def test_agent_lambda(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test the Bedrock Agent Lambda function
    
    Args:
        query: Test query dictionary with 'name' and 'message'
        
    Returns:
        Response from Lambda function
    """
    print(f"\n{'='*60}")
    print(f"Test: {query['name']}")
    print(f"{'='*60}")
    print(f"Query: {query['message']}")
    print(f"\nInvoking Lambda...")
    
    start_time = time.time()
    
    try:
        response = lambda_client.invoke(
            FunctionName='weather-wise-bedrock-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'message': query['message']
            })
        )
        
        duration = time.time() - start_time
        
        result = json.loads(response['Payload'].read())
        
        print(f"\nStatus Code: {result.get('statusCode')}")
        print(f"Duration: {duration:.2f}s")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
            agent_response = body.get('response', 'No response')
            
            print(f"\nAgent Response:")
            print("-" * 60)
            print(agent_response)
            print("-" * 60)
            
            return {
                'success': True,
                'duration': duration,
                'response': agent_response
            }
        else:
            error = result.get('body', 'Unknown error')
            print(f"\nError: {error}")
            
            return {
                'success': False,
                'duration': duration,
                'error': error
            }
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"\nException: {str(e)}")
        
        return {
            'success': False,
            'duration': duration,
            'error': str(e)
        }


def test_agent_local():
    """
    Test the agent locally (requires environment variables to be set)
    """
    print("Testing agent locally...")
    print("Note: Ensure environment variables are set:")
    print("  - WEATHER_LAMBDA_ARN")
    print("  - FARE_LAMBDA_ARN")
    print("  - RECOMMENDATION_LAMBDA_ARN")
    print("  - AWS_REGION")
    
    try:
        from weather_wise_agent import agent
        
        for query in TEST_QUERIES:
            print(f"\n{'='*60}")
            print(f"Test: {query['name']}")
            print(f"{'='*60}")
            print(f"Query: {query['message']}")
            
            start_time = time.time()
            
            try:
                response = agent.run(query['message'])
                duration = time.time() - start_time
                
                print(f"\nDuration: {duration:.2f}s")
                print(f"\nAgent Response:")
                print("-" * 60)
                print(response)
                print("-" * 60)
                
            except Exception as e:
                duration = time.time() - start_time
                print(f"\nError after {duration:.2f}s: {str(e)}")
            
            # Wait between tests to avoid rate limiting
            time.sleep(2)
            
    except ImportError as e:
        print(f"Error importing agent: {str(e)}")
        print("Make sure you're in the agent directory and dependencies are installed")


def run_all_tests():
    """
    Run all test queries against the deployed Lambda function
    """
    print("="*60)
    print("Weather-Wise Bedrock Agent Test Suite")
    print("="*60)
    
    results = []
    
    for query in TEST_QUERIES:
        result = test_agent_lambda(query)
        results.append({
            'query': query['name'],
            'success': result['success'],
            'duration': result['duration']
        })
        
        # Wait between tests to avoid rate limiting
        time.sleep(2)
    
    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - successful_tests
    avg_duration = sum(r['duration'] for r in results) / total_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Average Duration: {avg_duration:.2f}s")
    
    print(f"\nDetailed Results:")
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {result['query']}: {result['duration']:.2f}s")
    
    return successful_tests == total_tests


def test_single_query(message: str):
    """
    Test a single custom query
    
    Args:
        message: User message to test
    """
    query = {
        'name': 'Custom Query',
        'message': message
    }
    
    test_agent_lambda(query)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--local":
            # Test locally
            test_agent_local()
        elif sys.argv[1] == "--query":
            # Test single custom query
            if len(sys.argv) > 2:
                test_single_query(" ".join(sys.argv[2:]))
            else:
                print("Usage: python test_agent.py --query <your message>")
        else:
            print("Usage:")
            print("  python test_agent.py              # Run all tests against Lambda")
            print("  python test_agent.py --local      # Test locally")
            print("  python test_agent.py --query <message>  # Test single query")
    else:
        # Run all tests against deployed Lambda
        success = run_all_tests()
        sys.exit(0 if success else 1)
