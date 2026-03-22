# Weather-Wise Flight Booking Agent Documentation

This folder contains comprehensive documentation for the Weather-Wise Flight Booking Agent project.

## Reading Order

Follow this order for the best understanding of the system:

1. **[01-architecture-overview.md](01-architecture-overview.md)**
   - System architecture and component overview
   - How the agent works with MCP tools
   - Data flow and integration patterns
   - Start here to understand the big picture

2. **[02-api-specification.md](02-api-specification.md)**
   - REST API endpoints and request/response formats
   - Input validation rules
   - Error handling and status codes
   - Essential for API integration

3. **[03-bedrock-agent-integration.md](03-bedrock-agent-integration.md)**
   - Bedrock Agent setup with Strands SDK
   - Tool definitions and orchestration
   - System instructions and workflow
   - Model configuration (Claude 3 Haiku)

4. **[04-s3-data-structure.md](04-s3-data-structure.md)**
   - S3 bucket organization and folder structure
   - Historical weather and fare data formats
   - Data upload and maintenance procedures

5. **[05-deployment-guide.md](05-deployment-guide.md)**
   - Step-by-step deployment instructions
   - AWS CDK setup and configuration
   - Environment variables and credentials
   - Testing and verification steps

6. **[06-cost-comparison.md](06-cost-comparison.md)**
   - Cost analysis: Claude 3 Haiku vs Sonnet
   - Pricing breakdown and optimization tips
   - Expected costs for different usage levels

7. **[07-deploy-us-east-2.md](07-deploy-us-east-2.md)**
   - Region-specific deployment guide for US-East-2 (Ohio)
   - Quick deployment commands
   - Troubleshooting for us-east-2
   - Monitoring and verification

8. **[08-api-keys-configuration.md](08-api-keys-configuration.md)**
   - API key management and security
   - Environment variables configuration
   - AWS Secrets Manager integration
   - Security best practices and troubleshooting

## Quick Start

If you're new to the project:
1. Read **01-architecture-overview.md** to understand the system
2. Follow **05-deployment-guide.md** or **07-deploy-us-east-2.md** to deploy to AWS
3. Use **02-api-specification.md** to integrate with the API

## Additional Resources

- **Root README.md**: Project overview and quick start
- **deploy.ps1**: Automated deployment script (PowerShell)
- **agent/README.md**: Bedrock Agent implementation details
- **.kiro/specs/**: Complete specification with requirements, design, and tasks
