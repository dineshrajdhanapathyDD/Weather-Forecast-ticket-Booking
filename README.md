# Weather-Wise Flight Booking Agent

An intelligent travel assistant powered by Amazon Nova that combines weather intelligence with flight fare trends to help travelers make safer, more comfortable, and cost-effective booking decisions.

## 🌟 Features

- **Weather Intelligence**: Real-time weather forecasts and climate risk assessment
- **Fare Trend Analysis**: Historical price tracking and trend prediction
- **Smart Recommendations**: AI-powered booking suggestions (Book Now, Wait, or Change Dates)
- **Conversational AI**: Natural language chat interface powered by Amazon Nova
- **Alternative Windows**: Suggests better travel dates when conditions aren't optimal
- **Dual Interface**: Chat mode for conversational queries, Search mode for structured searches

## 🏗️ Architecture

### Core Components

- **Amazon Bedrock (Nova Micro)**: Conversational AI agent with Strands SDK orchestration
- **AWS Lambda**: Serverless compute for MCP tools and recommendation engine
- **Amazon API Gateway**: REST API endpoints for frontend integration
- **Amazon S3**: Historical weather and fare data storage
- **Amazon DynamoDB**: Query history and recommendation tracking
- **AWS CDK**: Infrastructure as Code for automated deployment

### Lambda Functions

1. **Weather MCP Tool** (`weather-wise-weather-tool`)
   - Fetches weather forecasts from WeatherAPI.com
   - Assesses climate risks and disruption probability
   - Provides comfort advisories

2. **Fare MCP Tool** (`weather-wise-fare-tool`)
   - Generates realistic fare data (mock for demo)
   - Analyzes 30-day price trends
   - Classifies trends as rising, stable, or dropping

3. **Recommendation Engine** (`weather-wise-recommendation`)
   - Combines weather and fare data
   - Generates booking recommendations
   - Finds alternative travel windows
   - Persists query history to DynamoDB

4. **Bedrock Agent** (`weather-wise-bedrock-agent`)
   - Conversational interface using Amazon Nova
   - Orchestrates tool calls via Strands SDK
   - Provides natural language responses

## 📁 Project Structure

```
weather-wise-flight-booking/
├── agent/                          # Bedrock Agent implementation
│   ├── weather_wise_agent.py     # Main agent logic with Strands SDK
│   ├── build_lambda_linux.ps1    # Build script for Lambda package
│   ├── requirements.txt           # Python dependencies
│   └── test_agent.py             # Agent unit tests
│
├── lambda/                         # Lambda function implementations
│   ├── weather_tool/              # Weather MCP Tool
│   │   ├── handler.py            # Lambda handler
│   │   ├── build.ps1             # Build script
│   │   └── requirements.txt      # Dependencies
│   ├── fare_tool/                 # Fare MCP Tool
│   │   ├── handler.py            # Lambda handler
│   │   ├── build.ps1             # Build script
│   │   └── requirements.txt      # Dependencies
│   └── recommendation/            # Recommendation Engine
│       ├── handler.py            # Lambda handler
│       ├── build.ps1             # Build script
│       └── requirements.txt      # Dependencies
│
├── infrastructure/                 # AWS CDK infrastructure code
│   ├── lib/
│   │   └── weather-wise-stack.ts # CDK stack definition
│   ├── bin/                       # CDK app entry point
│   ├── cdk.json                  # CDK configuration
│   └── package.json              # Node.js dependencies
│
├── frontend/                       # React frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── ChatInterface.js  # Chat mode UI
│   │   │   ├── SearchForm.js     # Search mode UI
│   │   │   └── ResultsDisplay.js # Results visualization
│   │   ├── App.js                # Main app component
│   │   └── index.js              # React entry point
│   ├── public/                    # Static assets
│   ├── package.json              # Node.js dependencies
│   └── .env.example              # Environment variables template
│
├── tests/                          # Test suites
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── property/                  # Property-based tests
│
├── docs/                           # Documentation
│   ├── 01-architecture-overview.md
│   ├── 02-api-specification.md
│   ├── 03-bedrock-agent-integration.md
│   ├── 04-s3-data-structure.md
│   ├── 05-deployment-guide.md
│   ├── 06-cost-comparison.md
│   ├── 07-deploy-us-east-2.md
│   ├── 08-api-keys-configuration.md
│   └── README.md                  # Documentation index
│
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore patterns
├── deploy.ps1                      # Deployment script
├── requirements.txt                # Root Python dependencies
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Node.js** 18+ and npm
- **Python** 3.11+
- **AWS CDK** CLI installed globally

### Installation

1. **Clone the repository**:

```bash
git clone <repository-url>
cd weather-wise-flight-booking
```

2. **Set up environment variables**:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
# WEATHER_API_KEY=your_weather_api_key_here
# FARE_API_KEY=your_fare_api_key_here
```

3. **Install Python dependencies**:

```bash
pip install -r requirements.txt
```

4. **Install CDK dependencies**:

```bash
cd infrastructure
npm install
cd ..
```

5. **Install frontend dependencies**:

```bash
cd frontend
npm install
cd ..
```

### Deployment

#### Option 1: Automated Deployment (Recommended)

```powershell
# PowerShell
.\deploy.ps1
```

```bash
# Bash
./deploy.sh
```

#### Option 2: Manual Deployment

1. **Build Lambda packages**:

```powershell
# Build agent
cd agent
.\build_lambda_linux.ps1

# Build weather tool
cd ../lambda/weather_tool
.\build.ps1

# Build fare tool
cd ../fare_tool
.\build.ps1

# Build recommendation engine
cd ../recommendation
.\build.ps1
cd ../..
```

2. **Deploy infrastructure**:

```bash
cd infrastructure
cdk bootstrap  # First time only
cdk deploy --require-approval never
cd ..
```

3. **Note the API endpoint** from CDK outputs:

```
Outputs:
WeatherWiseStack.ApiEndpoint = https://xxxxx.execute-api.us-east-2.amazonaws.com/prod/
```

4. **Configure frontend**:

```bash
cd frontend
echo "REACT_APP_API_ENDPOINT=https://xxxxx.execute-api.us-east-2.amazonaws.com/prod" > .env
```

5. **Start frontend**:

```bash
npm start
```

The application will open at `http://localhost:3000`

## 🧪 Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Property-Based Tests

```bash
pytest tests/property/
```

### Test Lambda Functions

```bash
# Test weather tool
aws lambda invoke \
  --function-name weather-wise-weather-tool \
  --payload '{"parameters":{"destination":"LAX","start_date":"2026-03-20","end_date":"2026-03-27"}}' \
  --region us-east-2 \
  response.json

# Test recommendation engine
aws lambda invoke \
  --function-name weather-wise-recommendation \
  --payload '{"origin":"JFK","destination":"LAX","travel_window":{"start_date":"2026-03-20","end_date":"2026-03-27"}}' \
  --region us-east-2 \
  response.json
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` folder:

1. [Architecture Overview](docs/01-architecture-overview.md) - System design and components
2. [API Specification](docs/02-api-specification.md) - REST API endpoints and schemas
3. [Bedrock Agent Integration](docs/03-bedrock-agent-integration.md) - AI agent implementation
4. [S3 Data Structure](docs/04-s3-data-structure.md) - Historical data organization
5. [Deployment Guide](docs/05-deployment-guide.md) - Detailed deployment instructions
6. [Cost Comparison](docs/06-cost-comparison.md) - AWS service costs analysis
7. [Deploy to us-east-2](docs/07-deploy-us-east-2.md) - Region-specific deployment
8. [API Keys Configuration](docs/08-api-keys-configuration.md) - Security and key management

## 🔐 Security

### API Key Management

- **Never commit API keys** to version control
- Use **environment variables** for all sensitive data
- Store production keys in **AWS Secrets Manager**
- Rotate keys regularly (every 90 days)
- Monitor API usage for anomalies

See [API Keys Configuration](docs/08-api-keys-configuration.md) for detailed security practices.

### IAM Permissions

Lambda functions use least-privilege IAM roles:

- **S3**: Read-only access to historical data bucket
- **DynamoDB**: Read/write access to queries table
- **Lambda**: Invoke permissions for inter-function calls
- **Bedrock**: Model invocation for Amazon Nova
- **CloudWatch**: Logs and metrics

## 💰 Cost Estimation

### Monthly Costs (Estimated)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 100,000 invocations | $0.20 |
| API Gateway | 100,000 requests | $0.35 |
| DynamoDB | 100,000 reads/writes | $0.25 |
| S3 | 1 GB storage | $0.02 |
| Bedrock (Nova Micro) | 1M input tokens | $0.15 |
| **Total** | | **~$1.00/month** |

See [Cost Comparison](docs/06-cost-comparison.md) for detailed analysis.

## 🛠️ Development

### Local Development

1. **Run frontend locally**:

```bash
cd frontend
npm start
```

2. **Test Lambda functions locally** (requires SAM CLI):

```bash
sam local invoke WeatherToolFunction -e events/weather-event.json
```

3. **View CloudWatch logs**:

```bash
aws logs tail /aws/lambda/weather-wise-recommendation --follow --region us-east-2
```

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow AWS CDK best practices
- **JavaScript**: Use ESLint with React configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Amazon Bedrock** for Nova Micro model
- **WeatherAPI.com** for weather data
- **Strands SDK** for agent orchestration
- **AWS CDK** for infrastructure as code

## 📧 Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Check the [documentation](docs/README.md)
- Review [troubleshooting guide](docs/08-api-keys-configuration.md#troubleshooting)

---

**Built with ❤️ using Amazon Nova**

Last Updated: March 13, 2026
