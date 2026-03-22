#!/bin/bash

# Deployment script for Weather-Wise Bedrock Agent Lambda
# This script packages the agent code and dependencies for Lambda deployment

set -e

echo "=========================================="
echo "Weather-Wise Bedrock Agent Deployment"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from agent directory
if [ ! -f "weather_wise_agent.py" ]; then
    echo -e "${RED}Error: Must run from agent/ directory${NC}"
    exit 1
fi

# Create build directory
echo -e "${YELLOW}Creating build directory...${NC}"
rm -rf build
mkdir -p build

# Copy agent code
echo -e "${YELLOW}Copying agent code...${NC}"
cp weather_wise_agent.py build/
cp __init__.py build/
cp requirements.txt build/

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
cd build
pip install -r requirements.txt -t . --upgrade

# Remove unnecessary files to reduce package size
echo -e "${YELLOW}Cleaning up unnecessary files...${NC}"
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Create deployment package
echo -e "${YELLOW}Creating deployment package...${NC}"
zip -r ../agent-deployment.zip . -q

cd ..

# Get package size
PACKAGE_SIZE=$(du -h agent-deployment.zip | cut -f1)
echo -e "${GREEN}✓ Deployment package created: agent-deployment.zip (${PACKAGE_SIZE})${NC}"

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}AWS CLI not found. Package created but not deployed.${NC}"
    echo -e "${YELLOW}To deploy manually, use:${NC}"
    echo "  aws lambda update-function-code --function-name weather-wise-bedrock-agent --zip-file fileb://agent-deployment.zip"
    exit 0
fi

# Ask if user wants to deploy
echo ""
read -p "Deploy to AWS Lambda now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deploying to Lambda...${NC}"
    
    # Check if function exists
    if aws lambda get-function --function-name weather-wise-bedrock-agent &> /dev/null; then
        # Update existing function
        echo -e "${YELLOW}Updating existing Lambda function...${NC}"
        aws lambda update-function-code \
            --function-name weather-wise-bedrock-agent \
            --zip-file fileb://agent-deployment.zip \
            --output json > /dev/null
        
        echo -e "${GREEN}✓ Lambda function updated successfully${NC}"
    else
        echo -e "${RED}Lambda function 'weather-wise-bedrock-agent' not found.${NC}"
        echo -e "${YELLOW}Please deploy infrastructure first using CDK:${NC}"
        echo "  cd ../infrastructure"
        echo "  cdk deploy"
        exit 1
    fi
    
    # Wait for function to be ready
    echo -e "${YELLOW}Waiting for function to be ready...${NC}"
    aws lambda wait function-updated --function-name weather-wise-bedrock-agent
    
    echo -e "${GREEN}✓ Deployment complete!${NC}"
    
    # Get function info
    echo ""
    echo -e "${GREEN}Function Details:${NC}"
    aws lambda get-function --function-name weather-wise-bedrock-agent \
        --query 'Configuration.[FunctionName,Runtime,MemorySize,Timeout,LastModified]' \
        --output table
else
    echo -e "${YELLOW}Deployment skipped. Package saved as agent-deployment.zip${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment script completed"
echo "==========================================${NC}"
