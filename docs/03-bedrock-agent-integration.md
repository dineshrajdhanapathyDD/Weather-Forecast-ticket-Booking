# AWS Bedrock Agent Integration Guide

## Overview

This guide explains how to integrate your Weather-Wise Flight Booking Lambda functions with Amazon Bedrock Agent using AgentCore and the Strands SDK. The system uses Bedrock Agent to orchestrate three MCP tools (Weather Tool, Fare Tool, and Recommendation Engine) to provide intelligent booking recommendations.

## Architecture

```
User Request → API Gateway → Bedrock Agent → Lambda MCP Tools → Response
                                    ↓
                            AgentCore + Strands
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              Weather Tool    Fare Tool    Recommendation Engine
```

## Prerequisites

Before integrating with Bedrock Agent, ensure you have:

1. **Deployed Lambda Functions**:
   - `weather-wise-weather-tool` (Weather MCP Tool)
   - `weather-wise-fare-tool` (Fare MCP Tool)
   - `weather-wise-recommendation` (Recommendation Engine)

2. **AWS Resources**:
   - S3 bucket: `weather-wise-historical-data`
   - DynamoDB table: `weather-wise-queries`
   - API Gateway endpoint (from CDK deployment)

3. **API Keys**:
   - Weather API key (OpenWeatherMap or WeatherAPI.com)
   - Fare API key (Skyscanner or Amadeus)

4. **AWS Permissions**:
   - IAM role for Bedrock Agent with Lambda invoke permissions
   - Lambda execution role with S3 and DynamoDB access

## Integration Options

You have two main options for integrating with Bedrock Agent:

### Option 1: Direct Lambda Invocation (Current Implementation)

Your current implementation already works without Bedrock Agent orchestration. The Recommendation Engine Lambda directly invokes the Weather and Fare tools:

```python
# In lambda/recommendation/handler.py
weather_data = invoke_weather_tool(destination, start_date, end_date)
fare_data = invoke_fare_tool(origin, destination, start_date, end_date)
```

**Pros**:
- Simple architecture
- No additional Bedrock Agent configuration needed
- Lower latency (direct Lambda-to-Lambda calls)
- Already implemented and tested

**Cons**:
- No conversational AI capabilities
- No natural language understanding
- Limited to structured API requests

**How to use**: Simply call your API Gateway endpoint with JSON:

```bash
curl -X POST https://your-api-gateway-url/prod/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "LAX",
    "origin": "JFK",
    "travel_window": {
      "start_date": "2024-07-15",
      "end_date": "2024-07-22"
    }
  }'
```

### Option 2: Bedrock Agent Orchestration (Conversational AI)

Use Bedrock Agent to add conversational AI capabilities, allowing users to interact naturally:

**User**: "I want to fly to Los Angeles from New York in mid-July"
**Agent**: Extracts destination, origin, dates → Invokes tools → Returns formatted recommendation

**Pros**:
- Natural language understanding
- Multi-turn conversations
- Context management across interactions
- Bedrock's built-in safety and guardrails

**Cons**:
- More complex setup
- Additional AWS costs (Bedrock Agent usage)
- Higher latency (LLM processing)

## Setting Up Bedrock Agent (Option 2)

### Step 1: Install Strands SDK

The Strands SDK provides the framework for building agents on Bedrock:

```bash
pip install strands-agents
```

### Step 2: Create Agent Configuration

Create a new file `agent/weather_wise_agent.py`:

```python
from strands import Agent, Tool
from strands.models import BedrockModel
import boto3
import json

# Initialize Bedrock model
model = BedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)

# Initialize Lambda client
lambda_client = boto3.client('lambda')

# Define Weather Tool
weather_tool = Tool(
    name="get_weather_forecast",
    description="Get weather forecast, climate risks, and disruption probability for a destination and date range",
    parameters={
        "destination": {
            "type": "string",
            "description": "Destination airport code (e.g., LAX) or city name"
        },
        "start_date": {
            "type": "string",
            "description": "Travel start date in YYYY-MM-DD format"
        },
        "end_date": {
            "type": "string",
            "description": "Travel end date in YYYY-MM-DD format"
        }
    },
    required=["destination", "start_date", "end_date"]
)

@weather_tool.handler
def handle_weather_tool(destination: str, start_date: str, end_date: str):
    """Invoke Weather MCP Tool Lambda"""
    response = lambda_client.invoke(
        FunctionName='weather-wise-weather-tool',
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
        return result['data']
    else:
        raise Exception(result.get('error', {}).get('message', 'Weather tool failed'))

# Define Fare Tool
fare_tool = Tool(
    name="get_fare_trends",
    description="Get flight fare data and price trends for a route and date range",
    parameters={
        "origin": {
            "type": "string",
            "description": "Origin airport code (e.g., JFK)"
        },
        "destination": {
            "type": "string",
            "description": "Destination airport code (e.g., LAX)"
        },
        "start_date": {
            "type": "string",
            "description": "Travel start date in YYYY-MM-DD format"
        },
        "end_date": {
            "type": "string",
            "description": "Travel end date in YYYY-MM-DD format"
        }
    },
    required=["origin", "destination", "start_date", "end_date"]
)

@fare_tool.handler
def handle_fare_tool(origin: str, destination: str, start_date: str, end_date: str):
    """Invoke Fare MCP Tool Lambda"""
    response = lambda_client.invoke(
        FunctionName='weather-wise-fare-tool',
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
        return result['data']
    else:
        raise Exception(result.get('error', {}).get('message', 'Fare tool failed'))

# Define Recommendation Tool
recommendation_tool = Tool(
    name="generate_booking_recommendation",
    description="Generate booking recommendation based on weather and fare data",
    parameters={
        "destination": {
            "type": "string",
            "description": "Destination airport code or city"
        },
        "origin": {
            "type": "string",
            "description": "Origin airport code"
        },
        "travel_window": {
            "type": "object",
            "description": "Travel window with start_date and end_date",
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"}
            }
        },
        "weather_data": {
            "type": "object",
            "description": "Weather data from weather tool"
        },
        "fare_data": {
            "type": "object",
            "description": "Fare data from fare tool"
        }
    },
    required=["destination", "travel_window", "weather_data", "fare_data"]
)

@recommendation_tool.handler
def handle_recommendation_tool(destination: str, origin: str, travel_window: dict, 
                               weather_data: dict, fare_data: dict):
    """Invoke Recommendation Engine Lambda"""
    response = lambda_client.invoke(
        FunctionName='weather-wise-recommendation',
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
        return result['data']
    else:
        raise Exception(result.get('error', {}).get('message', 'Recommendation failed'))

# Create the Agent
agent = Agent(
    name="WeatherWiseFlightBookingAgent",
    model=model,
    tools=[weather_tool, fare_tool, recommendation_tool],
    instructions="""
You are a Weather-Wise Flight Booking Agent that helps travelers make safer, more comfortable, 
and cost-effective flight-booking decisions by combining weather intelligence with flight fare trends.

When a user provides a destination and travel window, you must:

1. Call get_weather_forecast to gather weather forecasts, seasonal climate risks, and disruption probability
2. Call get_fare_trends to analyze flight price trends
3. Call generate_booking_recommendation with both weather and fare data to get the final recommendation

Always respond using this structure:

🌦️ Weather Risk Summary (Low / Medium / High)
{weather_risk_explanation}

🌡️ Comfort & Climate Advisory
{comfort_advisory}

💰 Fare Trend Insight
{fare_trend_insight}

✅ Final Booking Recommendation (Book Now / Wait / Change Dates)
{recommendation_rationale}

🔁 Alternative Travel Windows (if applicable)
{alternative_windows}

Keep responses concise, actionable, and user-friendly. Focus on decision clarity, safety, and cost savings.
"""
)

# Run the agent
if __name__ == "__main__":
    # Example: Interactive mode
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        response = agent.run(user_input)
        print(f"Agent: {response}")
```

### Step 3: Deploy Agent to Lambda

Create a new Lambda function for the Bedrock Agent:

```bash
# Create deployment package
cd agent
pip install strands-agents -t .
zip -r agent.zip .

# Deploy to Lambda
aws lambda create-function \
  --function-name weather-wise-bedrock-agent \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler weather_wise_agent.lambda_handler \
  --zip-file fileb://agent.zip \
  --timeout 300 \
  --memory-size 1024 \
  --environment Variables="{
    WEATHER_LAMBDA_ARN=arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-weather-tool,
    FARE_LAMBDA_ARN=arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-fare-tool,
    RECOMMENDATION_LAMBDA_ARN=arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-recommendation
  }"
```

Add a Lambda handler wrapper:

```python
def lambda_handler(event, context):
    """Lambda handler for Bedrock Agent"""
    user_message = event.get('message', '')
    
    response = agent.run(user_message)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': response
        })
    }
```

### Step 4: Update API Gateway

Update your API Gateway to route conversational requests to the Bedrock Agent Lambda:

```typescript
// Add to infrastructure/lib/weather-wise-stack.ts

// Bedrock Agent Lambda
const bedrockAgentLambda = new lambda.Function(this, 'BedrockAgentFunction', {
  functionName: 'weather-wise-bedrock-agent',
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'weather_wise_agent.lambda_handler',
  code: lambda.Code.fromAsset(path.join(__dirname, '../../agent')),
  role: lambdaRole,
  timeout: cdk.Duration.seconds(300),
  memorySize: 1024,
  environment: {
    WEATHER_LAMBDA_ARN: weatherToolLambda.functionArn,
    FARE_LAMBDA_ARN: fareToolLambda.functionArn,
    RECOMMENDATION_LAMBDA_ARN: recommendationLambda.functionArn,
  },
  description: 'Bedrock Agent for conversational booking recommendations',
});

// Grant invoke permissions
weatherToolLambda.grantInvoke(bedrockAgentLambda);
fareToolLambda.grantInvoke(bedrockAgentLambda);
recommendationLambda.grantInvoke(bedrockAgentLambda);

// POST /chat endpoint for conversational interface
const chatResource = api.root.addResource('chat');
const chatIntegration = new apigateway.LambdaIntegration(bedrockAgentLambda);
chatResource.addMethod('POST', chatIntegration);
```

### Step 5: Test the Agent

Test with natural language:

```bash
# Conversational request
curl -X POST https://your-api-gateway-url/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to fly to Los Angeles from New York between July 15 and July 22"
  }'
```

## Workflow Comparison

### Current Implementation (Direct Lambda)

```
API Gateway → Recommendation Lambda
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
  Weather Lambda          Fare Lambda
        ↓                       ↓
    Weather API             Fare API
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
            Generate Recommendation
                    ↓
            Store in DynamoDB
                    ↓
            Return JSON Response
```

### Bedrock Agent Implementation

```
API Gateway → Bedrock Agent Lambda
                    ↓
            Parse Natural Language
                    ↓
        Extract: destination, origin, dates
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
  Weather Tool            Fare Tool
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
        Recommendation Tool
                    ↓
        Format Response (with emojis)
                    ↓
        Return Conversational Response
```

## Cost Considerations

### Option 1 (Direct Lambda):
- Lambda invocations: ~$0.20 per 1M requests
- API Gateway: ~$3.50 per 1M requests
- DynamoDB: Pay per request
- **Total**: ~$4-5 per 1M requests

### Option 2 (Bedrock Agent):
- Lambda invocations: ~$0.20 per 1M requests
- API Gateway: ~$3.50 per 1M requests
- Bedrock Claude 3 Haiku: ~$0.25 per 1K input tokens, ~$1.25 per 1K output tokens
- DynamoDB: Pay per request
- **Total**: ~$4-5 per 1M requests (comparable to Option 1!)

**Cost Comparison**:
- Using Haiku makes conversational AI cost-competitive with structured API
- 80% cheaper than Sonnet (~$50-100 per 1M requests)
- Can upgrade to Sonnet if more capability needed

## Recommendation

**For MVP and Production (Current State)**:
- Use **both endpoints** - they're now cost-competitive!
- `/recommend` for programmatic/structured access
- `/chat` for conversational interfaces
- Both share the same backend infrastructure

**Haiku makes conversational AI affordable**:
- Similar cost to structured API (~$4-5 per 1M requests)
- Faster response times than Sonnet
- Sufficient quality for flight booking recommendations
- Can upgrade to Sonnet/Opus if needed
- Let users choose based on their preference
- Use Bedrock Agent for voice assistants, chatbots, or mobile apps

## Next Steps

1. **Test Current Implementation**:
   ```bash
   # Deploy infrastructure
   cd infrastructure
   npm install
   cdk deploy
   
   # Test the API
   curl -X POST $(aws cloudformation describe-stacks \
     --stack-name WeatherWiseStack \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text)recommend \
     -H "Content-Type: application/json" \
     -d '{"destination":"LAX","origin":"JFK","travel_window":{"start_date":"2024-07-15","end_date":"2024-07-22"}}'
   ```

2. **Monitor Performance**:
   - Check CloudWatch Logs for Lambda execution
   - Monitor API Gateway metrics
   - Verify DynamoDB writes with TTL

3. **Optional: Add Bedrock Agent**:
   - Follow Step 2-5 above to add conversational capabilities
   - Deploy as separate `/chat` endpoint
   - Test with natural language queries

## Troubleshooting

### Lambda Timeout
- Increase timeout in CDK: `timeout: cdk.Duration.seconds(60)`
- Check external API response times

### Permission Errors
- Verify IAM roles have correct policies
- Check Lambda execution role has S3 and DynamoDB access
- Verify Bedrock Agent Lambda can invoke other Lambdas

### External API Failures
- Check API keys are set correctly
- Verify retry logic is working (3 attempts with exponential backoff)
- Review CloudWatch Logs for error details

### DynamoDB Write Failures
- System continues to work (graceful degradation)
- Check IAM permissions for DynamoDB
- Verify table name matches environment variable

## Resources

- [Strands SDK Documentation](https://github.com/awslabs/strands)
- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started.html)
