# Weather-Wise Infrastructure

AWS CDK infrastructure for the Weather-Wise Flight Booking Agent.

## Architecture Components

### AWS Services

1. **Lambda Functions**
   - `weather-wise-weather-tool`: Weather MCP Tool
   - `weather-wise-fare-tool`: Fare MCP Tool
   - `weather-wise-recommendation`: Recommendation Engine

2. **S3 Bucket**
   - Name: `weather-wise-historical-data`
   - Structure:
     ```
     weather/{destination}/{year}/{month}/disruption_rates.json
     fares/{origin}-{destination}/{year}/{month}/daily_prices.json
     ```

3. **DynamoDB Table**
   - Name: `weather-wise-queries`
   - Partition Key: `query_id` (String)
   - GSI: `destination-timestamp-index`
     - Partition Key: `destination` (String)
     - Sort Key: `timestamp` (Number)
   - TTL: 90 days (attribute: `ttl`)

4. **API Gateway**
   - Endpoint: POST /recommend
   - CORS enabled
   - Request validation enabled
   - Throttling: 100 req/s rate, 200 burst

### IAM Roles and Policies

**Lambda Execution Role**:
- Basic Lambda execution (CloudWatch Logs)
- S3 read access to historical data bucket
- DynamoDB read/write access to queries table
- Lambda invoke permissions (for recommendation engine)

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js 18+ and npm
3. AWS CDK CLI: `npm install -g aws-cdk`
4. Python 3.11+

## Environment Variables

Set these before deployment:

```bash
export WEATHER_API_KEY="your-weather-api-key"
export FARE_API_KEY="your-fare-api-key"
export CDK_DEFAULT_ACCOUNT="your-aws-account-id"
export CDK_DEFAULT_REGION="us-east-1"
```

## Installation

1. Install CDK dependencies:
   ```bash
   cd infrastructure
   npm install
   ```

2. Install Lambda dependencies:
   ```bash
   cd ../lambda/weather_tool && pip install -r requirements.txt -t .
   cd ../fare_tool && pip install -r requirements.txt -t .
   cd ../recommendation && pip install -r requirements.txt -t .
   ```

## Deployment

1. Bootstrap CDK (first time only):
   ```bash
   cdk bootstrap aws://${CDK_DEFAULT_ACCOUNT}/${CDK_DEFAULT_REGION}
   ```

2. Synthesize CloudFormation template:
   ```bash
   cdk synth
   ```

3. Deploy the stack:
   ```bash
   cdk deploy
   ```

4. Note the outputs:
   - API Gateway endpoint URL
   - S3 bucket name
   - DynamoDB table name
   - Lambda function ARNs

## Post-Deployment Setup

### 1. Upload Historical Data to S3

Upload sample historical data files:

```bash
# Weather historical data
aws s3 cp weather_data/ s3://weather-wise-historical-data/weather/ --recursive

# Fare historical data
aws s3 cp fare_data/ s3://weather-wise-historical-data/fares/ --recursive
```

### 2. Configure Bedrock Agent

The Bedrock Agent (AgentCore with Strands) needs to be configured separately to:
- Invoke the Lambda functions as MCP tools
- Use the API Gateway endpoint
- Handle conversation orchestration

This configuration is outside the scope of this CDK stack.

## Testing the API

Test the POST /recommend endpoint:

```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/recommend \
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

## Monitoring

- **CloudWatch Logs**: Lambda function logs
- **CloudWatch Metrics**: API Gateway metrics, Lambda metrics
- **X-Ray**: Distributed tracing (if enabled)
- **DynamoDB Metrics**: Table performance metrics

## Cost Optimization

- Lambda: Pay per invocation and duration
- API Gateway: Pay per request
- DynamoDB: On-demand billing mode
- S3: Standard storage with lifecycle rules (365-day expiration)

## Cleanup

To remove all resources:

```bash
cdk destroy
```

Note: S3 bucket and DynamoDB table have `RETAIN` removal policy and must be deleted manually if needed.

## Troubleshooting

### Lambda Timeout
- Increase timeout in `weather-wise-stack.ts`
- Check external API response times

### Permission Errors
- Verify IAM role policies
- Check Lambda execution role permissions

### API Gateway 4xx Errors
- Validate request body format
- Check required parameters

### DynamoDB Throttling
- Consider switching to provisioned capacity
- Add auto-scaling policies
