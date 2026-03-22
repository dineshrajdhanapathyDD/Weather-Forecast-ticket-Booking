# Quick Start Guide: Bedrock Agent Setup

Get your Weather-Wise Bedrock Agent up and running in 5 steps.

## Prerequisites

- AWS Account with Bedrock access
- AWS CLI configured
- Python 3.11+
- Node.js 18+ (for CDK)
- Existing Lambda functions deployed (weather-tool, fare-tool, recommendation)

## Step 1: Enable Bedrock Model Access

1. Go to AWS Console → Amazon Bedrock
2. Navigate to "Model access" in the left sidebar
3. Click "Manage model access"
4. Enable "Claude 3 Haiku" (anthropic.claude-3-haiku-20240307-v1:0)
5. Click "Save changes"
6. Wait for status to change to "Access granted" (~2 minutes)

**Why Haiku?**
- 80% cheaper than Sonnet (~$0.25 vs $3 per 1K input tokens)
- Faster response times (~1-2s vs 3-5s)
- Sufficient for flight booking recommendations
- Can upgrade to Sonnet/Opus if needed

## Step 2: Deploy Infrastructure

Deploy the Bedrock Agent Lambda using CDK:

```bash
# Navigate to infrastructure directory
cd infrastructure

# Install dependencies (if not already done)
npm install

# Deploy the stack (includes Bedrock Agent)
cdk deploy

# Note the outputs:
# - ChatEndpoint: https://xxx.execute-api.region.amazonaws.com/prod/chat
# - BedrockAgentLambdaArn: arn:aws:lambda:region:account:function:weather-wise-bedrock-agent
```

The CDK deployment will:
- Create the Bedrock Agent Lambda function
- Configure IAM permissions for Bedrock and Lambda invocation
- Set up API Gateway `/chat` endpoint
- Configure environment variables automatically

## Step 3: Verify Deployment

Check that the Lambda function was created:

```bash
aws lambda get-function --function-name weather-wise-bedrock-agent
```

Expected output should show:
- Runtime: python3.11
- Handler: weather_wise_agent.lambda_handler
- Timeout: 300 seconds
- Memory: 1024 MB

## Step 4: Test the Agent

### Option A: Using cURL

```bash
# Get your API endpoint from CDK output
CHAT_ENDPOINT="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/chat"

# Test with a simple query
curl -X POST $CHAT_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to fly to Los Angeles from New York between July 15, 2024 and July 22, 2024"
  }'
```

### Option B: Using Test Script

```bash
cd agent

# Install dependencies
pip install -r requirements.txt

# Run test suite
python test_agent.py

# Or test a single query
python test_agent.py --query "I want to fly to Miami next week"
```

### Option C: Using AWS Console

1. Go to Lambda Console
2. Open `weather-wise-bedrock-agent` function
3. Go to "Test" tab
4. Create test event:
```json
{
  "message": "I want to fly to Los Angeles from New York in mid-July"
}
```
5. Click "Test"
6. Check response in execution results

## Step 5: Integrate with Your Application

### JavaScript/TypeScript

```typescript
async function getBookingRecommendation(userMessage: string) {
  const response = await fetch('https://your-api-endpoint/prod/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: userMessage
    })
  });
  
  const data = await response.json();
  return data.response;
}

// Usage
const recommendation = await getBookingRecommendation(
  "I want to fly to Miami from Boston in August"
);
console.log(recommendation);
```

### Python

```python
import requests

def get_booking_recommendation(user_message: str) -> str:
    response = requests.post(
        'https://your-api-endpoint/prod/chat',
        json={'message': user_message}
    )
    
    data = response.json()
    return data['response']

# Usage
recommendation = get_booking_recommendation(
    "I want to fly to Miami from Boston in August"
)
print(recommendation)
```

### React Component

```jsx
import { useState } from 'react';

function BookingAgent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await fetch('https://your-api-endpoint/prod/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      
      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      setResponse('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about flight booking..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Get Recommendation'}
        </button>
      </form>
      
      {response && (
        <div style={{ whiteSpace: 'pre-wrap' }}>
          {response}
        </div>
      )}
    </div>
  );
}
```

## Troubleshooting

### "Access Denied" Error

**Problem**: Lambda can't invoke Bedrock model

**Solution**:
1. Check Bedrock model access is enabled (Step 1)
2. Verify Lambda IAM role has `bedrock:InvokeModel` permission
3. Ensure you're using a supported region (us-east-1, us-west-2, etc.)

```bash
# Check Lambda role permissions
aws lambda get-function --function-name weather-wise-bedrock-agent \
  --query 'Configuration.Role'

# Check IAM policy
aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>
```

### "Function Not Found" Error

**Problem**: Lambda function doesn't exist

**Solution**:
1. Ensure CDK deployment completed successfully
2. Check you're in the correct AWS region
3. Verify function name is `weather-wise-bedrock-agent`

```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `weather-wise`)].FunctionName'
```

### Timeout Errors

**Problem**: Lambda times out before completing

**Solution**:
1. Increase Lambda timeout (default: 300s)
2. Check if MCP tool Lambdas are responding
3. Verify external APIs (weather, fare) are accessible

```bash
# Update timeout
aws lambda update-function-configuration \
  --function-name weather-wise-bedrock-agent \
  --timeout 600
```

### Empty or Malformed Response

**Problem**: Agent returns empty or incorrect response

**Solution**:
1. Check CloudWatch Logs for errors
2. Verify environment variables are set correctly
3. Test individual MCP tools directly

```bash
# View logs
aws logs tail /aws/lambda/weather-wise-bedrock-agent --follow

# Check environment variables
aws lambda get-function-configuration \
  --function-name weather-wise-bedrock-agent \
  --query 'Environment.Variables'
```

## Next Steps

1. **Monitor Usage**: Set up CloudWatch dashboards for metrics
2. **Add Authentication**: Integrate with Cognito or API keys
3. **Optimize Costs**: Consider using Claude 3 Haiku for lower costs
4. **Scale**: Configure Lambda concurrency limits
5. **Enhance**: Add more tools or customize agent instructions

## Cost Monitoring

Track your Bedrock usage:

```bash
# View Bedrock metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationCount \
  --dimensions Name=ModelId,Value=anthropic.claude-3-haiku-20240307-v1:0 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-12-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

**Cost Advantage with Haiku**:
- ~$4-5 per 1M requests (comparable to structured API)
- 80% cheaper than Sonnet
- Faster response times
- Sufficient quality for flight recommendations

## Support

- **Documentation**: See `agent/README.md` for detailed information
- **Integration Guide**: See `docs/bedrock-agent-integration.md`
- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/
- **Strands SDK**: https://github.com/awslabs/strands

## Summary

You now have a fully functional conversational AI agent for flight booking recommendations! The agent can:

✓ Understand natural language queries
✓ Extract travel details automatically
✓ Fetch weather and fare data
✓ Generate actionable recommendations
✓ Suggest alternative travel windows
✓ Handle errors gracefully

**Two endpoints available**:
- `/recommend` - Structured JSON API (direct Lambda)
- `/chat` - Conversational AI (Bedrock Agent)

Choose the endpoint that best fits your use case!
