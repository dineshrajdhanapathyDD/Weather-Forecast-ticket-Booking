# Deployment Guide for US-East-2 (Ohio)

## Region Configuration

You're deploying to **us-east-2 (Ohio)** which fully supports:
- ✅ Claude 3 Haiku
- ✅ Lambda
- ✅ API Gateway
- ✅ DynamoDB
- ✅ S3

## Step 1: Set Your Region

Make sure your AWS CLI is configured for us-east-2:

```powershell
aws configure get region
```

If it shows a different region, update it:

```powershell
aws configure set region us-east-2
```

Or set it as an environment variable for this session:

```powershell
$env:AWS_REGION = "us-east-2"
$env:CDK_DEFAULT_REGION = "us-east-2"
```

## Step 2: Verify Region

```powershell
aws sts get-caller-identity
```

This should show your account info. The region will be used from your config.

## Step 3: Deploy

### Option A: Automated Script

```powershell
# Set region first
$env:AWS_REGION = "us-east-2"
$env:CDK_DEFAULT_REGION = "us-east-2"

# Run deployment
.\deploy.ps1
```

### Option B: Manual Deployment

```powershell
# Set region
$env:AWS_REGION = "us-east-2"
$env:CDK_DEFAULT_REGION = "us-east-2"

# Install CDK
npm install -g aws-cdk

# Install dependencies
cd infrastructure
npm install
cd ..

# Bootstrap CDK for us-east-2 (first time only)
cd infrastructure
cdk bootstrap aws://ACCOUNT-ID/us-east-2
```

Replace `ACCOUNT-ID` with your AWS account ID (get it from `aws sts get-caller-identity`).

```powershell
# Deploy
cdk deploy
```

## Step 4: Enable Bedrock in US-East-2

1. Go to: https://us-east-2.console.aws.amazon.com/bedrock/
2. Make sure you're in **US East (Ohio) us-east-2** region (check top-right corner)
3. Click "Model access" in left sidebar
4. Click "Manage model access"
5. Find and enable "Claude 3 Haiku" (anthropic.claude-3-haiku-20240307-v1:0)
6. Click "Save changes"
7. Wait for "Access granted" status (~2 minutes)

## Step 5: Get Your Endpoints

```powershell
aws cloudformation describe-stacks `
  --stack-name WeatherWiseStack `
  --region us-east-2 `
  --query 'Stacks[0].Outputs' `
  --output table
```

Your endpoints will look like:
- `https://xxxxx.execute-api.us-east-2.amazonaws.com/prod/recommend`
- `https://xxxxx.execute-api.us-east-2.amazonaws.com/prod/chat`

## Step 6: Test Your Deployment

### Test Structured API

```powershell
$apiEndpoint = "https://YOUR-API-ID.execute-api.us-east-2.amazonaws.com/prod"

curl -X POST "$apiEndpoint/recommend" `
  -H "Content-Type: application/json" `
  -d '{
    "destination": "LAX",
    "origin": "JFK",
    "travel_window": {
      "start_date": "2024-08-15",
      "end_date": "2024-08-22"
    }
  }'
```

### Test Conversational API

```powershell
curl -X POST "$apiEndpoint/chat" `
  -H "Content-Type: application/json" `
  -d '{
    "message": "I want to fly to Los Angeles from New York in mid-August"
  }'
```

## Troubleshooting for US-East-2

### Issue: Bedrock Not Available
**Check**: Make sure you're in us-east-2 console
- URL should be: https://us-east-2.console.aws.amazon.com/bedrock/

### Issue: Wrong Region Deployed
**Solution**: Destroy and redeploy
```powershell
cd infrastructure
cdk destroy
$env:AWS_REGION = "us-east-2"
cdk deploy
```

### Issue: Model Access Denied
**Solution**: 
1. Go to Bedrock console in us-east-2
2. Enable Claude 3 Haiku
3. Wait for "Access granted"
4. Test again

### Issue: Lambda Can't Access Bedrock
**Solution**: Check Lambda environment variables
```powershell
aws lambda get-function-configuration `
  --function-name weather-wise-bedrock-agent `
  --region us-east-2 `
  --query 'Environment.Variables'
```

Should show `AWS_REGION: us-east-2`

## Region-Specific Notes

### US-East-2 Advantages:
- ✅ Lower latency for central US users
- ✅ Full Bedrock support
- ✅ Competitive pricing
- ✅ High availability

### Bedrock Pricing in US-East-2:
Same as other regions:
- Claude 3 Haiku: $0.25 per 1K input tokens, $1.25 per 1K output tokens
- ~$4-5 per 1M requests

## Monitoring in US-East-2

### View Logs
```powershell
aws logs tail /aws/lambda/weather-wise-bedrock-agent `
  --region us-east-2 `
  --follow
```

### Check Lambda Functions
```powershell
aws lambda list-functions `
  --region us-east-2 `
  --query 'Functions[?contains(FunctionName, `weather-wise`)].FunctionName'
```

### View CloudWatch Metrics
```powershell
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Invocations `
  --dimensions Name=FunctionName,Value=weather-wise-bedrock-agent `
  --region us-east-2 `
  --start-time (Get-Date).AddHours(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
  --period 300 `
  --statistics Sum
```

## Quick Deploy for US-East-2

**One-liner deployment:**

```powershell
$env:AWS_REGION = "us-east-2"; $env:CDK_DEFAULT_REGION = "us-east-2"; .\deploy.ps1
```

This will:
1. Set region to us-east-2
2. Install dependencies
3. Deploy everything
4. Show your endpoints

**Time: 10-15 minutes**

## After Deployment Checklist

- [ ] Verify region is us-east-2 in AWS Console
- [ ] Enable Claude 3 Haiku in Bedrock (us-east-2)
- [ ] Test /recommend endpoint
- [ ] Test /chat endpoint
- [ ] Check CloudWatch Logs
- [ ] Save API endpoints
- [ ] Set up monitoring (optional)

## Support

If you encounter region-specific issues:

1. **Verify region everywhere**:
   ```powershell
   aws configure get region
   echo $env:AWS_REGION
   ```

2. **Check stack region**:
   ```powershell
   aws cloudformation describe-stacks --stack-name WeatherWiseStack --query 'Stacks[0].StackId'
   ```

3. **Ensure Bedrock is in same region**:
   - Console URL should be: https://us-east-2.console.aws.amazon.com/bedrock/

## Summary

✅ **US-East-2 is fully supported**
✅ **Claude 3 Haiku available**
✅ **Same pricing as other regions**
✅ **Ready to deploy**

**Next step**: Run `.\deploy.ps1` with region set to us-east-2!
