# Architecture Overview

## System Architecture

The Weather-Wise Flight Booking Agent is a serverless application built on AWS that combines weather intelligence with flight fare analytics to provide booking recommendations.

## High-Level Flow

```
User Request → API Gateway → Recommendation Lambda
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Weather Lambda                    Fare Lambda
                    ↓                               ↓
            Weather API + S3                  Fare API + S3
                    ↓                               ↓
                    └───────────────┬───────────────┘
                                    ↓
                        Recommendation Logic
                                    ↓
                            DynamoDB Storage
                                    ↓
                            JSON Response
```

## Components

### 1. API Gateway
- **Purpose**: REST API endpoint for client applications
- **Endpoint**: POST /recommend
- **Features**: Request validation, CORS, throttling, logging

### 2. Lambda Functions

#### Weather MCP Tool
- **Runtime**: Python 3.11
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Responsibilities**:
  - Fetch weather forecasts from external API
  - Retrieve seasonal climate risk data
  - Access historical weather patterns from S3
  - Calculate disruption probability

#### Fare MCP Tool
- **Runtime**: Python 3.11
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Responsibilities**:
  - Fetch current flight fare data from external API
  - Retrieve 30-day historical fare trends from S3
  - Calculate price movement percentages
  - Classify fare trends (rising/stable/dropping)

#### Recommendation Engine
- **Runtime**: Python 3.11
- **Timeout**: 60 seconds
- **Memory**: 1024 MB
- **Responsibilities**:
  - Orchestrate calls to Weather and Fare tools
  - Apply recommendation logic
  - Search for alternative travel windows
  - Store query and recommendation in DynamoDB
  - Format response

### 3. S3 Bucket
- **Name**: weather-wise-historical-data
- **Purpose**: Store historical weather and fare data
- **Structure**:
  ```
  weather/
    {destination}/
      {year}/
        {month}/
          disruption_rates.json
  fares/
    {origin}-{destination}/
      {year}/
        {month}/
          daily_prices.json
  ```
- **Lifecycle**: 365-day expiration

### 4. DynamoDB Table
- **Name**: weather-wise-queries
- **Partition Key**: query_id (String)
- **GSI**: destination-timestamp-index
- **TTL**: 90 days
- **Purpose**: Store query history and recommendations

### 5. IAM Roles
- **Lambda Execution Role**:
  - CloudWatch Logs write
  - S3 read (historical data bucket)
  - DynamoDB read/write (queries table)
  - Lambda invoke (for recommendation engine)

## Data Flow

### Request Processing

1. **Client** sends POST request to API Gateway with:
   - destination
   - origin
   - travel_window (start_date, end_date)

2. **API Gateway** validates request and invokes Recommendation Lambda

3. **Recommendation Lambda**:
   - Generates query_id
   - Invokes Weather Lambda with destination and dates
   - Invokes Fare Lambda with origin, destination, and dates
   - Waits for both responses

4. **Weather Lambda**:
   - Calls external weather API for forecast
   - Queries S3 for historical disruption rates
   - Calculates weather risk
   - Returns weather data

5. **Fare Lambda**:
   - Calls external fare API for current prices
   - Queries S3 for 30-day historical prices
   - Calculates fare trend
   - Returns fare data

6. **Recommendation Lambda** (continued):
   - Applies recommendation logic
   - Searches for alternative windows if needed
   - Stores query and recommendation in DynamoDB
   - Formats response

7. **API Gateway** returns JSON response to client

### Error Handling

- **Retry Logic**: Up to 3 attempts with exponential backoff
- **Graceful Degradation**: 
  - Weather-only recommendations if fare data fails
  - Fare-only recommendations if weather data fails
  - Error response if both fail
- **Logging**: All errors logged to CloudWatch

## Scalability

### Horizontal Scaling
- Lambda functions scale automatically with concurrent requests
- API Gateway handles up to 10,000 requests per second (default)
- DynamoDB on-demand mode scales automatically

### Performance Optimization
- Lambda warm starts: Keep functions warm with scheduled pings
- S3 data caching: Cache frequently accessed historical data
- DynamoDB query optimization: Use GSI for efficient queries

## Security

### Network Security
- API Gateway with HTTPS only
- Lambda functions in VPC (optional)
- S3 bucket with block public access

### Access Control
- IAM roles with least privilege
- API Gateway with request validation
- Lambda execution role with specific permissions

### Data Protection
- S3 encryption at rest (S3-managed keys)
- DynamoDB encryption at rest (AWS-managed keys)
- CloudWatch Logs encryption

## Monitoring and Observability

### Metrics
- Lambda: Invocations, errors, duration, throttles
- API Gateway: Request count, latency, 4xx/5xx errors
- DynamoDB: Read/write capacity, throttles
- S3: Request count, data transfer

### Logs
- Lambda execution logs in CloudWatch
- API Gateway access logs
- DynamoDB streams (optional)

### Tracing
- X-Ray for distributed tracing (optional)
- Request ID tracking across services

## Cost Optimization

### Strategies
1. **Lambda**: Right-size memory allocation
2. **API Gateway**: Use caching for repeated requests
3. **DynamoDB**: Use on-demand for variable traffic
4. **S3**: Lifecycle policies to delete old data

### Estimated Costs (1M requests/month)
- Lambda: $10
- API Gateway: $3.50
- DynamoDB: $5
- S3: $2
- **Total**: ~$20/month

## Future Enhancements

1. **Bedrock Agent Integration**: Add AgentCore with Strands orchestration
2. **Caching Layer**: Add ElastiCache for frequently accessed data
3. **Real-time Updates**: Add EventBridge for real-time fare alerts
4. **Machine Learning**: Add SageMaker for predictive analytics
5. **Multi-region**: Deploy to multiple regions for global availability
6. **Authentication**: Add Cognito for user authentication
7. **Rate Limiting**: Add per-user rate limiting
8. **Analytics**: Add Kinesis for real-time analytics

## Disaster Recovery

### Backup Strategy
- S3: Versioning enabled (optional)
- DynamoDB: Point-in-time recovery enabled
- Lambda: Code stored in S3 by CDK

### Recovery Procedures
1. **Lambda Failure**: Automatic retry by API Gateway
2. **API Gateway Failure**: Multi-region deployment
3. **DynamoDB Failure**: Restore from point-in-time backup
4. **S3 Failure**: Cross-region replication (optional)

### RTO/RPO
- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 5 minutes (DynamoDB PITR)
