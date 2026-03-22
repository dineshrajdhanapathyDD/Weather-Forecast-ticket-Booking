# Weather-Wise Bedrock Agent

Conversational AI agent for flight booking recommendations using Amazon Bedrock and Strands SDK.

## Overview

This agent provides natural language interaction for the Weather-Wise Flight Booking system. Users can ask questions in plain English, and the agent will:

1. Extract travel details (origin, destination, dates)
2. Fetch weather forecasts and climate risks
3. Analyze flight fare trends
4. Generate actionable booking recommendations
5. Suggest alternative travel windows if needed

## Architecture

```
User Message → Bedrock Agent → Tool Orchestration
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Weather Tool      Fare Tool      Recommendation Tool
                    ↓                 ↓                 ↓
              Weather API        Fare API         DynamoDB
                    ↓                 ↓                 ↓
                    └─────────────────┴─────────────────┘
                                      ↓
                          Formatted Response with Emojis
```

## Prerequisites

1. **Python 3.11+**
2. **AWS Account** with:
   - Bedrock access (Claude 3 Sonnet model enabled)
   - Lambda functions deployed (weather-wise-weather-tool, weather-wise-fare-tool, weather-wise-recommendation)
   - IAM permissions for Lambda invocation and Bedrock model access

3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Local Testing

Test the agent locally before deploying to Lambda:

```bash
# Set environment variables
export WEATHER_LAMBDA_ARN="arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-weather-tool"
export FARE_LAMBDA_ARN="arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-fare-tool"
export RECOMMENDATION_LAMBDA_ARN="arn:aws:lambda:REGION:ACCOUNT:function:weather-wise-recommendation"
export AWS_REGION="us-east-1"

# Run interactive CLI
python weather_wise_agent.py
```

Example conversation:
```
You: I want to fly to Los Angeles from New York between July 15 and July 22

Agent: 🌦️ Weather Risk Summary: Low
Clear skies expected with minimal disruption risk (8%)

🌡️ Comfort & Climate Advisory:
Pleasant temperatures 22-28°C, low humidity, ideal travel conditions

💰 Fare Trend Insight:
Prices rising 15% over past 30 days - book soon to lock in rates

✅ Final Booking Recommendation: Book Now
Low weather risk and rising fares make this an optimal time to book
```

## Deployment

### Option 1: Using CDK (Recommended)

The agent is automatically deployed when you deploy the infrastructure:

```bash
cd ../infrastructure
npm install
cdk deploy
```

This will:
- Create the Bedrock Agent Lambda function
- Configure IAM permissions
- Set up API Gateway `/chat` endpoint
- Configure environment variables

### Option 2: Manual Deployment

If you need to update just the agent code:

```bash
# Package the agent
./deploy.sh

# Or manually:
pip install -r requirements.txt -t .
zip -r agent-deployment.zip .
aws lambda update-function-code \
  --function-name weather-wise-bedrock-agent \
  --zip-file fileb://agent-deployment.zip
```

## API Usage

### Endpoint

```
POST https://your-api-gateway-url/prod/chat
```

### Request Format

```json
{
  "message": "I want to fly to Los Angeles from New York in mid-July"
}
```

### Response Format

```json
{
  "statusCode": 200,
  "body": {
    "response": "🌦️ Weather Risk Summary: Low\n..."
  }
}
```

### Example cURL Request

```bash
curl -X POST https://your-api-gateway-url/prod/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to fly to Miami from Boston between August 1 and August 7"
  }'
```

## Supported Query Formats

The agent understands various natural language formats:

- "I want to fly to [destination] from [origin] between [start date] and [end date]"
- "What's the weather like in [destination] for [date range]?"
- "Should I book a flight to [destination] in [month]?"
- "I'm planning a trip to [destination] next week"
- "Compare weather and fares for [destination] in [date range]"

The agent will:
- Extract location and date information
- Ask for missing details (e.g., origin airport)
- Convert relative dates to specific dates
- Handle various date formats

## Tool Workflow

The agent orchestrates three MCP tools:

### 1. Weather Tool (`get_weather_forecast`)
- **Input**: destination, start_date, end_date
- **Output**: Weather risk level, comfort advisory, disruption probability
- **Lambda**: `weather-wise-weather-tool`

### 2. Fare Tool (`get_fare_trends`)
- **Input**: origin, destination, start_date, end_date
- **Output**: Current prices, 30-day trends, price movement classification
- **Lambda**: `weather-wise-fare-tool`

### 3. Recommendation Tool (`generate_booking_recommendation`)
- **Input**: destination, origin, travel_window, weather_data, fare_data
- **Output**: Booking recommendation (Book Now/Wait/Change Dates), alternative windows
- **Lambda**: `weather-wise-recommendation`

## Configuration

### Environment Variables

Set in Lambda function configuration:

- `WEATHER_LAMBDA_ARN`: ARN of Weather Tool Lambda
- `FARE_LAMBDA_ARN`: ARN of Fare Tool Lambda
- `RECOMMENDATION_LAMBDA_ARN`: ARN of Recommendation Engine Lambda
- `AWS_REGION`: AWS region (e.g., us-east-1)

### Bedrock Model

Default model: `anthropic.claude-3-haiku-20240307-v1:0` (optimized for cost and speed)

To change the model, update in `weather_wise_agent.py`:

```python
model = BedrockModel(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",  # More capable
    region=os.environ.get('AWS_REGION', 'us-east-1')
)
```

Available models:
- `anthropic.claude-3-haiku-20240307-v1:0` (Fast and economical - **recommended**)
- `anthropic.claude-3-sonnet-20240229-v1:0` (Balanced performance)
- `anthropic.claude-3-opus-20240229-v1:0` (Most capable, higher cost)

## Error Handling

The agent handles various error scenarios:

1. **Missing Information**: Asks user for missing details
2. **Invalid Dates**: Requests valid future dates
3. **Tool Failures**: Explains issue and suggests retry
4. **Partial Data**: Recommendation tool handles graceful degradation

## Monitoring

### CloudWatch Logs

View agent execution logs:

```bash
aws logs tail /aws/lambda/weather-wise-bedrock-agent --follow
```

### Metrics

Monitor in CloudWatch:
- Invocation count
- Duration
- Error rate
- Bedrock token usage

## Cost Estimation

Per 1,000 requests (assuming average conversation):

- Lambda execution: ~$0.20
- Bedrock Claude 3 Haiku: ~$0.25-1.25 (varies by conversation length)
- API Gateway: ~$3.50
- **Total**: ~$4-5 per 1,000 requests

Cost optimization tips:
- Haiku is already the most cost-effective model (~80% cheaper than Sonnet)
- Cache common queries
- Set appropriate Lambda timeout (300s default)
- Consider upgrading to Sonnet only if response quality is insufficient

## Troubleshooting

### Agent not responding

1. Check CloudWatch Logs for errors
2. Verify Lambda has correct IAM permissions
3. Ensure Bedrock model is enabled in your region
4. Check environment variables are set correctly

### Tool invocation failures

1. Verify Lambda ARNs are correct
2. Check Lambda execution role has invoke permissions
3. Test individual tools directly
4. Review tool Lambda logs

### Bedrock access denied

1. Ensure Bedrock is enabled in your AWS account
2. Request model access in Bedrock console
3. Verify IAM policy includes `bedrock:InvokeModel`
4. Check region supports Claude 3 models

## Development

### Adding New Tools

1. Define tool in `weather_wise_agent.py`:
```python
new_tool = Tool(
    name="tool_name",
    description="What the tool does",
    parameters={...},
    required=[...]
)

@new_tool.handler
def handle_new_tool(**kwargs):
    # Tool implementation
    pass
```

2. Add to agent tools list:
```python
agent = Agent(
    tools=[weather_tool, fare_tool, recommendation_tool, new_tool],
    ...
)
```

### Modifying Agent Instructions

Update the `instructions` parameter in the `Agent` constructor to change agent behavior, response format, or workflow.

## Testing

### Unit Tests

```bash
pytest tests/test_agent.py
```

### Integration Tests

```bash
# Test with real Lambda functions
python test_integration.py
```

### Load Testing

```bash
# Simulate multiple concurrent requests
python load_test.py --requests 100 --concurrency 10
```

## Security

- Agent runs in Lambda with least-privilege IAM role
- No sensitive data stored in agent code
- API keys managed via environment variables
- Bedrock provides built-in content filtering
- All Lambda invocations use IAM authentication

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review this README
3. Consult main project documentation
4. Check AWS Bedrock documentation

## License

Same as parent project.
