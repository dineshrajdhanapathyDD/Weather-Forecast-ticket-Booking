# API Keys Configuration

**⚠️ SECURITY WARNING: This file contains sensitive information. Never commit actual API keys to version control.**

## Overview

The Weather-Wise Flight Booking Agent uses external APIs for weather and fare data. API keys are securely managed through AWS Lambda environment variables.

## API Keys

### Weather API (WeatherAPI.com)

- **Service**: WeatherAPI.com
- **Used by**: Weather MCP Tool Lambda (`weather-wise-weather-tool`)
- **Environment Variable**: `WEATHER_API_KEY`
- **Endpoint**: `https://api.weatherapi.com/v1/`
- **Free Tier**: 1,000,000 calls/month

### Flight/Fare API

- **Service**: Mock Data Generator (for demo purposes)
- **Used by**: Fare MCP Tool Lambda (`weather-wise-fare-tool`)
- **Environment Variable**: `FARE_API_KEY`
- **Note**: Currently generates realistic mock data; can be replaced with real API

## Configuration Methods

### Method 1: Automatic Configuration (Recommended)

API keys are configured in the CDK stack and automatically deployed:

**File**: `infrastructure/lib/weather-wise-stack.ts`

```typescript
environment: {
  WEATHER_API_KEY: process.env.WEATHER_API_KEY || 'your-default-key',
  FARE_API_KEY: process.env.FARE_API_KEY || 'your-default-key',
}
```

Deploy with environment variables:

```powershell
# PowerShell
$env:WEATHER_API_KEY = "your-weather-api-key"
$env:FARE_API_KEY = "your-fare-api-key"
cd infrastructure
cdk deploy
```

```bash
# Bash
export WEATHER_API_KEY="your-weather-api-key"
export FARE_API_KEY="your-fare-api-key"
cd infrastructure
cdk deploy
```

### Method 2: AWS Secrets Manager (Production)

For production deployments, use AWS Secrets Manager:

1. **Store secrets**:

```bash
aws secretsmanager create-secret \
  --name weather-wise/weather-api-key \
  --secret-string "your-weather-api-key" \
  --region us-east-2

aws secretsmanager create-secret \
  --name weather-wise/fare-api-key \
  --secret-string "your-fare-api-key" \
  --region us-east-2
```

2. **Update Lambda code** to fetch from Secrets Manager:

```python
import boto3
import json

secrets_client = boto3.client('secretsmanager', region_name='us-east-2')

def get_secret(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

WEATHER_API_KEY = get_secret('weather-wise/weather-api-key')
FARE_API_KEY = get_secret('weather-wise/fare-api-key')
```

3. **Grant Lambda permissions** in CDK:

```typescript
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['secretsmanager:GetSecretValue'],
  resources: [
    `arn:aws:secretsmanager:${this.region}:${this.account}:secret:weather-wise/*`
  ],
}));
```

### Method 3: Update Existing Deployment

**Via AWS Console**:

1. Navigate to AWS Lambda Console
2. Select function: `weather-wise-weather-tool` or `weather-wise-fare-tool`
3. Go to **Configuration** → **Environment variables**
4. Click **Edit**
5. Update `WEATHER_API_KEY` or `FARE_API_KEY`
6. Click **Save**

**Via AWS CLI**:

```bash
aws lambda update-function-configuration \
  --function-name weather-wise-weather-tool \
  --environment "Variables={WEATHER_API_KEY=new-key,S3_BUCKET=weather-wise-historical-data}" \
  --region us-east-2
```

## Security Best Practices

### 1. Never Commit Keys to Git

Add to `.gitignore`:

```
# API Keys and Secrets
API_KEYS.md
.env
.env.local
*.key
secrets/
```

### 2. Use Environment Variables

Always use environment variables, never hardcode keys:

```python
# ✅ Good
API_KEY = os.environ.get('WEATHER_API_KEY')

# ❌ Bad
API_KEY = "200dc4ddbc56469ba94134118261203"
```

### 3. Rotate Keys Regularly

- Change API keys every 90 days
- Update Lambda environment variables after rotation
- Monitor for unauthorized usage

### 4. Restrict IAM Permissions

Grant Lambda only the minimum required permissions:

```typescript
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'secretsmanager:GetSecretValue',  // Only read secrets
  ],
  resources: [
    'arn:aws:secretsmanager:*:*:secret:weather-wise/*'  // Only weather-wise secrets
  ],
}));
```

### 5. Enable CloudWatch Monitoring

Monitor API usage and errors:

```bash
aws logs tail /aws/lambda/weather-wise-weather-tool \
  --since 1h \
  --filter-pattern "ERROR" \
  --region us-east-2
```

### 6. Set Up Billing Alerts

Create CloudWatch alarms for unexpected API costs:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name weather-api-high-usage \
  --alarm-description "Alert when API usage is high" \
  --metric-name Invocations \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 3600 \
  --threshold 10000 \
  --comparison-operator GreaterThanThreshold
```

## API Limits and Quotas

### WeatherAPI.com

| Plan | Calls/Month | Rate Limit | Forecast Days |
|------|-------------|------------|---------------|
| Free | 1,000,000 | - | 3 days |
| Paid | Unlimited | Custom | 14 days |

### AWS Lambda Limits

- **Concurrent executions**: 1000 (default)
- **Function timeout**: 300 seconds (configured: 30-60s)
- **Memory**: 128 MB - 10 GB (configured: 512 MB - 1 GB)

## Troubleshooting

### Weather API Errors

**Error**: `401 Unauthorized`

- **Cause**: Invalid API key
- **Solution**: Verify key in Lambda environment variables

**Error**: `403 Forbidden`

- **Cause**: API quota exceeded
- **Solution**: Check WeatherAPI.com dashboard, upgrade plan

**Error**: `429 Too Many Requests`

- **Cause**: Rate limit exceeded
- **Solution**: Implement exponential backoff, reduce request frequency

### Fare API Errors

**Error**: `Connection timeout`

- **Cause**: External API unreachable
- **Solution**: Check API endpoint, verify network connectivity

**Error**: `Invalid response format`

- **Cause**: API response structure changed
- **Solution**: Update parsing logic in `lambda/fare_tool/handler.py`

### Lambda Configuration Errors

**Error**: `Environment variable not set`

- **Cause**: Missing environment variable
- **Solution**: Add variable via AWS Console or redeploy with CDK

```bash
aws lambda update-function-configuration \
  --function-name weather-wise-weather-tool \
  --environment "Variables={WEATHER_API_KEY=your-key,S3_BUCKET=weather-wise-historical-data}"
```

## Testing API Keys

### Test Weather API

```bash
curl "https://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=London"
```

Expected response:

```json
{
  "location": {
    "name": "London",
    "country": "United Kingdom"
  },
  "current": {
    "temp_c": 15.0,
    "condition": {
      "text": "Partly cloudy"
    }
  }
}
```

### Test Lambda Function

```bash
aws lambda invoke \
  --function-name weather-wise-weather-tool \
  --payload '{"parameters":{"destination":"LAX","start_date":"2026-03-20","end_date":"2026-03-27"}}' \
  --region us-east-2 \
  response.json

cat response.json
```

## Resources

- [WeatherAPI.com Documentation](https://www.weatherapi.com/docs/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

**Last Updated**: March 13, 2026
