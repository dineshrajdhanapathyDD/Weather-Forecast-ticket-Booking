"""
Weather-Wise Flight Booking Agent using Strands SDK and Amazon Bedrock

This agent provides conversational AI capabilities for flight booking recommendations
by orchestrating Weather, Fare, and Recommendation MCP tools.
"""

from strands import Agent, tool
from strands.models import BedrockModel
import boto3
import json
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Initialize Bedrock model
# Using Amazon Nova Micro for optimal cost-performance balance
# Nova Micro: Ultra-low cost, fast text-only model
# Must use inference profile (not direct model ID) for on-demand throughput
# Using us-east-2 specific inference profile
model = BedrockModel(
    model_id="us.amazon.nova-micro-v1:0",
    region="us-east-2"
)

# ========================================
# Tool Definitions
# ========================================

@tool
def get_weather_forecast(destination: str, start_date: str, end_date: str) -> dict:
    """Get weather forecast, climate risks, and disruption probability for a destination and date range.
    
    Args:
        destination: Destination airport code (e.g., LAX, JFK) or city name (e.g., Los Angeles, New York)
        start_date: Travel start date in YYYY-MM-DD format (e.g., 2024-07-15)
        end_date: Travel end date in YYYY-MM-DD format (e.g., 2024-07-22)
    
    Returns:
        Weather data with risk level, comfort advisory, and disruption rates
    """
    try:
        weather_lambda_arn = os.environ.get('WEATHER_LAMBDA_ARN')
        if not weather_lambda_arn:
            raise Exception("WEATHER_LAMBDA_ARN environment variable not set")
        
        logger.info(f"Invoking Weather Tool for {destination} from {start_date} to {end_date}")
        
        response = lambda_client.invoke(
            FunctionName=weather_lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'parameters': {
                    'destination': destination,
                    'start_date': start_date,
                    'end_date': end_date
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('success'):
            logger.info(f"Weather Tool succeeded for {destination}")
            return result['data']
        else:
            error_msg = result.get('error', {}).get('message', 'Weather tool failed')
            logger.error(f"Weather Tool failed: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Error invoking Weather Tool: {str(e)}")
        raise


@tool
def get_fare_trends(origin: str, destination: str, start_date: str, end_date: str) -> dict:
    """Get flight fare data and price trends for a route and date range.
    
    Args:
        origin: Origin airport code (e.g., JFK, LAX, ORD)
        destination: Destination airport code (e.g., LAX, JFK, MIA)
        start_date: Travel start date in YYYY-MM-DD format (e.g., 2024-07-15)
        end_date: Travel end date in YYYY-MM-DD format (e.g., 2024-07-22)
    
    Returns:
        Fare data with current prices, trends, and price movement classification
    """
    try:
        fare_lambda_arn = os.environ.get('FARE_LAMBDA_ARN')
        if not fare_lambda_arn:
            raise Exception("FARE_LAMBDA_ARN environment variable not set")
        
        logger.info(f"Invoking Fare Tool for {origin} to {destination} from {start_date} to {end_date}")
        
        response = lambda_client.invoke(
            FunctionName=fare_lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'parameters': {
                    'origin': origin,
                    'destination': destination,
                    'start_date': start_date,
                    'end_date': end_date
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('success'):
            logger.info(f"Fare Tool succeeded for {origin} to {destination}")
            return result['data']
        else:
            error_msg = result.get('error', {}).get('message', 'Fare tool failed')
            logger.error(f"Fare Tool failed: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Error invoking Fare Tool: {str(e)}")
        raise


@tool
def generate_booking_recommendation(destination: str, origin: str, travel_window: dict, 
                                   weather_data: dict, fare_data: dict) -> dict:
    """Generate booking recommendation based on weather and fare data.
    
    Args:
        destination: Destination airport code or city
        origin: Origin airport code
        travel_window: Travel window with start_date and end_date
        weather_data: Weather data from get_weather_forecast tool
        fare_data: Fare data from get_fare_trends tool
    
    Returns:
        Booking recommendation with advice and alternative windows
    """
    try:
        recommendation_lambda_arn = os.environ.get('RECOMMENDATION_LAMBDA_ARN')
        if not recommendation_lambda_arn:
            raise Exception("RECOMMENDATION_LAMBDA_ARN environment variable not set")
        
        logger.info(f"Invoking Recommendation Tool for {origin} to {destination}")
        
        response = lambda_client.invoke(
            FunctionName=recommendation_lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'destination': destination,
                'origin': origin,
                'travel_window': travel_window,
                'weather_data': weather_data,
                'fare_data': fare_data
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('success'):
            logger.info(f"Recommendation Tool succeeded")
            return result['data']
        else:
            error_msg = result.get('error', {}).get('message', 'Recommendation failed')
            logger.error(f"Recommendation Tool failed: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"Error invoking Recommendation Tool: {str(e)}")
        raise


# ========================================
# Agent Configuration
# ========================================

# System instructions for the agent
SYSTEM_INSTRUCTIONS = """
You are a Weather-Wise Flight Booking Agent that helps travelers make safer, more comfortable, 
and cost-effective flight-booking decisions by combining weather intelligence with flight fare trends.

## Your Workflow

When a user provides a destination and travel window (or you extract it from their message), you MUST:

1. **Extract Information**: Identify the origin, destination, and travel dates from the user's message
   - If origin is not provided, ask the user for it
   - Convert relative dates (e.g., "mid-July") to specific YYYY-MM-DD format
   - Ensure dates are in the future

2. **Get Weather Data**: Call `get_weather_forecast` with:
   - destination (airport code or city name)
   - start_date (YYYY-MM-DD)
   - end_date (YYYY-MM-DD)

3. **Get Fare Data**: Call `get_fare_trends` with:
   - origin (airport code)
   - destination (airport code)
   - start_date (YYYY-MM-DD)
   - end_date (YYYY-MM-DD)

4. **Generate Recommendation**: Call `generate_booking_recommendation` with:
   - destination
   - origin
   - travel_window (object with start_date and end_date)
   - weather_data (from step 2)
   - fare_data (from step 3)

5. **Format Response**: Present the recommendation using this EXACT structure:

🌦️ Weather Risk Summary: {weather_risk}
{weather_risk_explanation}

🌡️ Comfort & Climate Advisory:
{comfort_advisory}

💰 Fare Trend Insight:
{fare_trend_insight}

✅ Final Booking Recommendation: {booking_recommendation}
{recommendation_rationale}

[If alternative_windows exist:]
🔁 Alternative Travel Windows:
• {start_date} to {end_date}
  Weather Risk: {weather_risk} | Fare Trend: {fare_trend}
  {summary}

## Important Rules

- Always call all three tools in sequence (weather → fare → recommendation)
- Never skip the recommendation tool - it contains the core decision logic
- Keep responses concise, actionable, and user-friendly
- Focus on decision clarity, safety, and cost savings
- Do NOT explain AWS services, Lambda functions, or MCP protocol to users
- If a tool fails, explain the issue clearly and suggest the user try again

## Example Interaction

User: "I want to fly to Los Angeles from New York between July 15 and July 22"

You should:
1. Extract: origin=JFK, destination=LAX, start_date=2024-07-15, end_date=2024-07-22
2. Call get_weather_forecast(destination="LAX", start_date="2024-07-15", end_date="2024-07-22")
3. Call get_fare_trends(origin="JFK", destination="LAX", start_date="2024-07-15", end_date="2024-07-22")
4. Call generate_booking_recommendation with all the data
5. Format and present the recommendation with emojis

## Handling Errors

- If weather or fare data is unavailable, the recommendation tool will handle graceful degradation
- If a tool fails completely, apologize and ask the user to try again
- If dates are invalid or in the past, ask the user to provide valid future dates
"""

agent = Agent(
    model=model,
    tools=[get_weather_forecast, get_fare_trends, generate_booking_recommendation]
)


# ========================================
# Lambda Handler
# ========================================

def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent
    
    Expected event format (API Gateway proxy integration):
    {
        "body": "{\"message\": \"I want to fly to Los Angeles from New York in mid-July\"}"
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": "{\"response\": \"Agent's formatted response with recommendation\"}"
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse body from API Gateway proxy integration
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        # Extract user message
        user_message = body.get('message', '')
        
        if not user_message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: message'
                })
            }
        
        logger.info(f"Processing user message: {user_message}")
        
        # Run the agent with system instructions
        # Agent is callable, so we use agent(message, system=...)
        result = agent(
            user_message,
            system=SYSTEM_INSTRUCTIONS
        )
        
        # Extract text from result.message
        # result.message can be a string or a complex object with content array
        response_text = result.message
        if isinstance(response_text, dict):
            # Handle case where message is a dict with content array
            if 'content' in response_text and isinstance(response_text['content'], list):
                # Extract text from content array
                text_parts = []
                for item in response_text['content']:
                    if isinstance(item, dict) and 'text' in item:
                        text_parts.append(item['text'])
                response_text = '\n'.join(text_parts)
            elif 'content' in response_text and isinstance(response_text['content'], str):
                response_text = response_text['content']
        
        logger.info(f"Agent response generated successfully")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response_text
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }


# ========================================
# CLI Interface (for local testing)
# ========================================

def run_interactive():
    """Run agent in interactive CLI mode for local testing"""
    print("Weather-Wise Flight Booking Agent")
    print("=" * 50)
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
            
            print("\nAgent: ", end="")
            result = agent(user_input, system=SYSTEM_INSTRUCTIONS)
            print(result.message)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


if __name__ == "__main__":
    # Run in interactive mode for local testing
    run_interactive()
