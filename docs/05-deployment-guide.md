# Deployment Guide

## Prerequisites Checklist

- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI installed and configured
- [ ] Node.js 18+ and npm installed
- [ ] Python 3.11+ installed
- [ ] AWS CDK CLI installed (`npm install -g aws-cdk`)
- [ ] Weather API key (e.g., OpenWeatherMap, WeatherAPI.com)
- [ ] Fare API key (e.g., Skyscanner, Amadeus)

## Step 1: Clone and Setup

```bash
# Navigate to project root
cd weather-wise-flight-booking

# Install Python dependencies
pip install -r requirements.txt

# Install CDK dependencies
cd infrastructure
npm install
cd ..
```

## Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
# AWS Configuration
export CDK_DEFAULT_ACCOUNT="123456789012"
export CDK_DEFAULT_REGION="us-east-1"

# API Keys
export WEATHER_API_KEY="your-weather-api-key-here"
export FARE_API_KEY="your-fare-api-key-here"
```

Load the environment:
```bash
source .env
```

## Step 3: Prepare Lambda Packages

Install dependencies for each Lambda function:

```bash
# Weather Tool
cd lambda/weather_tool
pip install -r requirements.txt -t .
cd ../..

# Fare Tool
cd lambda/fare_tool
pip install -r requirements.txt -t .
cd ../..

# Recommendation Engine
cd lambda/recommendation
pip install -r requirements.txt -t .
cd ../..
```

## Step 4: Bootstrap CDK (First Time Only)

```bash
cd infrastructure
cdk bootstrap aws://${CDK_DEFAULT_ACCOUNT}/${CDK_DEFAULT_REGION}
```

This creates the necessary S3 bucket and IAM roles for CDK deployments.

## Step 5: Review Infrastructure

Synthesize the CloudFormation template to review:

```bash
cdk synth
```

Review the generated template in `infrastructure/cdk.out/`.

## Step 6: Deploy

Deploy the stack:

```bash
cdk deploy
```

Confirm the deployment when prompted. This will create:
- 3 Lambda functions
- 1 S3 bucket
- 1 DynamoDB table
- 1 API Gateway
- IAM roles and policies

**Deployment time**: ~5-10 minutes

## Step 7: Note the Outputs

After deployment, note the following outputs:

```
Outputs:
WeatherWiseStack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com/prod/
WeatherWiseStack.S3BucketName = weather-wise-historical-data
WeatherWiseStack.DynamoDBTableName = weather-wise-queries
WeatherWiseStack.WeatherLambdaArn = arn:aws:lambda:us-east-1:123456789012:function:weather-wise-weather-tool
WeatherWiseStack.FareLambdaArn = arn:aws:lambda:us-east-1:123456789012:function:weather-wise-fare-tool
WeatherWiseStack.RecommendationLambdaArn = arn:aws:lambda:us-east-1:123456789012:function:weather-wise-recommendation
```

Save these values for later use.

## Step 8: Upload Historical Data

Prepare sample historical data files and upload to S3:

```bash
# Create sample data structure
mkdir -p sample_data/weather/LAX/2024/01
mkdir -p sample_data/fares/JFK-LAX/2024/01

# Upload to S3
aws s3 sync sample_data/ s3://weather-wise-historical-data/
```

See `docs/s3-data-structure.md` for data format specifications.

## Step 9: Test the API

Test the deployed API:

```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/prod/recommend \
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

Expected response: JSON with recommendation data.

## Step 10: Configure Bedrock Agent (Optional)

To integrate with Amazon Bedrock AgentCore:

1. Create a Bedrock Agent in the AWS Console
2. Configure the agent to use Strands orchestration
3. Add Lambda functions as MCP tools:
   - Weather Tool: `weather-wise-weather-tool`
   - Fare Tool: `weather-wise-fare-tool`
   - Recommendation Engine: `weather-wise-recommendation`
4. Configure the agent prompt and instructions
5. Test the agent through the Bedrock console

## Verification Checklist

- [ ] All Lambda functions deployed successfully
- [ ] S3 bucket created with correct name
- [ ] DynamoDB table created with GSI
- [ ] API Gateway endpoint accessible
- [ ] Test API call returns valid response
- [ ] CloudWatch logs show Lambda executions
- [ ] DynamoDB table receives query records

## Monitoring Setup

### CloudWatch Dashboards

Create a dashboard to monitor:
- Lambda invocation count and errors
- API Gateway request count and latency
- DynamoDB read/write capacity
- Lambda duration and memory usage

### CloudWatch Alarms

Set up alarms for:
- Lambda error rate > 5%
- API Gateway 5xx errors > 10
- DynamoDB throttling events
- Lambda timeout errors

### X-Ray Tracing (Optional)

Enable X-Ray for distributed tracing:

```typescript
// In weather-wise-stack.ts
tracing: lambda.Tracing.ACTIVE
```

## Troubleshooting

### Issue: CDK Deploy Fails

**Solution**: Check AWS credentials and permissions
```bash
aws sts get-caller-identity
```

### Issue: Lambda Function Timeout

**Solution**: Increase timeout in `weather-wise-stack.ts`
```typescript
timeout: cdk.Duration.seconds(60)
```

### Issue: API Returns 403 Forbidden

**Solution**: Check API Gateway resource policy and CORS configuration

### Issue: DynamoDB Write Fails

**Solution**: Verify Lambda execution role has DynamoDB permissions

### Issue: S3 Access Denied

**Solution**: Verify Lambda execution role has S3 read permissions

## Rollback

If deployment fails or issues occur:

```bash
cdk destroy
```

This will remove all resources except:
- S3 bucket (RETAIN policy)
- DynamoDB table (RETAIN policy)

Delete these manually if needed:

```bash
aws s3 rb s3://weather-wise-historical-data --force
aws dynamodb delete-table --table-name weather-wise-queries
```

## Updates and Redeployment

To update the infrastructure:

1. Make changes to CDK code or Lambda functions
2. Run `cdk diff` to see changes
3. Run `cdk deploy` to apply changes

CDK will automatically update only the changed resources.

## Cost Estimation

Estimated monthly costs (low traffic):
- Lambda: $5-10 (1M requests)
- API Gateway: $3.50 (1M requests)
- DynamoDB: $1-5 (on-demand)
- S3: $1-2 (10GB storage)
- **Total**: ~$10-20/month

Costs scale with usage. Monitor with AWS Cost Explorer.

## Security Considerations

1. **API Authentication**: Add API keys or IAM authentication
2. **Encryption**: Enable encryption at rest for S3 and DynamoDB
3. **VPC**: Deploy Lambda functions in VPC for network isolation
4. **Secrets**: Store API keys in AWS Secrets Manager
5. **Least Privilege**: Review and minimize IAM permissions

## Next Steps

1. Implement Lambda function logic (Tasks 2-4)
2. Add comprehensive error handling
3. Write unit and property-based tests
4. Set up CI/CD pipeline
5. Configure monitoring and alerting
6. Add API authentication
7. Optimize Lambda performance
8. Load test the API


## Bedrock Agent Deployment (Optional - Conversational AI)

The Weather-Wise system includes an optional Bedrock Agent for conversational AI capabilities.

### Prerequisites for Bedrock Agent

1. **Enable Bedrock Model Access**:
   - Go to AWS Console → Amazon Bedrock
   - Navigate to "Model access"
   - Enable "Claude 3 Sonnet" model
   - Wait for "Access granted" status

2. **Verify Bedrock Availability**:
   ```bash
   aws bedrock list-foundation-models --region us-east-1 \
     --query 'modelSummaries[?contains(modelId, `claude-3-sonnet`)].modelId'
   ```

### Deploy Bedrock Agent

The Bedrock Agent is automatically deployed with the CDK stack:

```bash
cd infrastructure
cdk deploy
```

This creates:
- `weather-wise-bedrock-agent` Lambda function
- `/chat` API Gateway endpoint for conversational interface
- IAM permissions for Bedrock model access
- Environment variables for MCP tool integration

### Test Bedrock Agent

```bash
# Get the chat endpoint from CDK output
CHAT_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name WeatherWiseStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ChatEndpoint`].OutputValue' \
  --output text)

# Test with natural language
curl -X POST $CHAT_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to fly to Los Angeles from New York in mid-July"
  }'
```

### Bedrock Agent Features

- **Natural Language Understanding**: Users can ask questions in plain English
- **Context Extraction**: Automatically extracts origin, destination, and dates
- **Tool Orchestration**: Calls Weather, Fare, and Recommendation tools in sequence
- **Formatted Responses**: Returns recommendations with emoji indicators
- **Error Handling**: Gracefully handles missing information and tool failures

### Cost Considerations

Bedrock Agent adds additional costs:
- Claude 3 Haiku: ~$0.25 per 1K input tokens, ~$1.25 per 1K output tokens
- Typical query: ~$0.01-0.03 per request (80% cheaper than Sonnet)
- Can upgrade to Sonnet (~$0.05-0.15 per request) if more capability needed
- Opus available for most demanding use cases (~$0.15-0.45 per request)

### Monitoring Bedrock Agent

```bash
# View agent logs
aws logs tail /aws/lambda/weather-wise-bedrock-agent --follow

# Check invocation metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=weather-wise-bedrock-agent \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

For detailed Bedrock Agent setup and usage, see:
- `agent/README.md` - Complete agent documentation
- `agent/QUICKSTART.md` - Quick start guide
- `docs/bedrock-agent-integration.md` - Integration guide

## Deployment Comparison

### Standard Mode (Direct Lambda)
- **Endpoint**: `/recommend`
- **Input**: Structured JSON with destination, origin, travel_window
- **Cost**: ~$4-5 per 1M requests
- **Latency**: Low (~1-2 seconds)
- **Use Case**: Web dashboards, mobile apps, programmatic access

### Conversational Mode (Bedrock Agent)
- **Endpoint**: `/chat`
- **Input**: Natural language message
- **Cost**: ~$4-5 per 1M requests (using Haiku)
- **Latency**: Medium (~2-3 seconds)
- **Use Case**: Chatbots, voice assistants, conversational interfaces

Both endpoints can be used simultaneously based on your application needs.
