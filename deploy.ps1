# Weather-Wise Flight Booking Agent - Deployment Script
# This script automates the deployment of all components

param(
    [switch]$SkipBuild,
    [switch]$SkipDeploy,
    [switch]$SkipFrontend,
    [string]$Region = "us-east-2"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Weather-Wise Flight Booking Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "❌ Please edit .env file and add your API keys before continuing!" -ForegroundColor Red
    Write-Host "   Required: WEATHER_API_KEY, FARE_API_KEY" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Load environment variables from .env file
Write-Host "📋 Loading environment variables from .env..." -ForegroundColor Green
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        Write-Host "   ✓ Loaded: $name" -ForegroundColor Gray
    }
}
Write-Host ""

# Validate required environment variables
$requiredVars = @("WEATHER_API_KEY", "FARE_API_KEY")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not [Environment]::GetEnvironmentVariable($var, "Process")) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please add these to your .env file and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ All required environment variables are set" -ForegroundColor Green
Write-Host ""

# Step 1: Build Lambda packages
if (-not $SkipBuild) {
    Write-Host "🔨 Building Lambda packages..." -ForegroundColor Cyan
    Write-Host ""
    
    # Build Bedrock Agent
    Write-Host "  Building Bedrock Agent..." -ForegroundColor Yellow
    Push-Location agent
    .\build_lambda_linux.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build Bedrock Agent" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  ✓ Bedrock Agent built successfully" -ForegroundColor Green
    Write-Host ""
    
    # Build Weather Tool
    Write-Host "  Building Weather Tool..." -ForegroundColor Yellow
    Push-Location lambda/weather_tool
    .\build.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build Weather Tool" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  ✓ Weather Tool built successfully" -ForegroundColor Green
    Write-Host ""
    
    # Build Fare Tool
    Write-Host "  Building Fare Tool..." -ForegroundColor Yellow
    Push-Location lambda/fare_tool
    .\build.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build Fare Tool" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  ✓ Fare Tool built successfully" -ForegroundColor Green
    Write-Host ""
    
    # Build Recommendation Engine
    Write-Host "  Building Recommendation Engine..." -ForegroundColor Yellow
    Push-Location lambda/recommendation
    .\build.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to build Recommendation Engine" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "  ✓ Recommendation Engine built successfully" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "✅ All Lambda packages built successfully" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping Lambda build (--SkipBuild flag)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Deploy infrastructure with CDK
if (-not $SkipDeploy) {
    Write-Host "🚀 Deploying infrastructure with AWS CDK..." -ForegroundColor Cyan
    Write-Host ""
    
    Push-Location infrastructure
    
    # Check if CDK is bootstrapped
    Write-Host "  Checking CDK bootstrap status..." -ForegroundColor Yellow
    $bootstrapCheck = aws cloudformation describe-stacks --stack-name CDKToolkit --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠️  CDK not bootstrapped. Running bootstrap..." -ForegroundColor Yellow
        cdk bootstrap --region $Region
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to bootstrap CDK" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Host "  ✓ CDK bootstrapped successfully" -ForegroundColor Green
    } else {
        Write-Host "  ✓ CDK already bootstrapped" -ForegroundColor Green
    }
    Write-Host ""
    
    # Deploy stack
    Write-Host "  Deploying WeatherWiseStack..." -ForegroundColor Yellow
    cdk deploy --require-approval never --region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to deploy stack" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host ""
    Write-Host "✅ Infrastructure deployed successfully" -ForegroundColor Green
    Write-Host ""
    
    # Get API endpoint from stack outputs
    Write-Host "📡 Retrieving API endpoint..." -ForegroundColor Cyan
    $apiEndpoint = aws cloudformation describe-stacks `
        --stack-name WeatherWiseStack `
        --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" `
        --output text `
        --region $Region
    
    if ($apiEndpoint) {
        Write-Host "  API Endpoint: $apiEndpoint" -ForegroundColor Green
        Write-Host ""
        
        # Update frontend .env file
        if (-not $SkipFrontend) {
            Write-Host "  Updating frontend configuration..." -ForegroundColor Yellow
            $frontendEnv = "REACT_APP_API_ENDPOINT=$apiEndpoint"
            Set-Content -Path "frontend/.env" -Value $frontendEnv
            Write-Host "  ✓ Frontend .env updated" -ForegroundColor Green
            Write-Host ""
        }
    } else {
        Write-Host "  ⚠️  Could not retrieve API endpoint" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "⏭️  Skipping infrastructure deployment (--SkipDeploy flag)" -ForegroundColor Yellow
    Write-Host ""
}

# Step 3: Install and start frontend
if (-not $SkipFrontend) {
    Write-Host "🎨 Setting up frontend..." -ForegroundColor Cyan
    Write-Host ""
    
    Push-Location frontend
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "  Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Frontend dependencies already installed" -ForegroundColor Green
    }
    
    Pop-Location
    Write-Host ""
    Write-Host "✅ Frontend setup complete" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "🌐 To start the frontend, run:" -ForegroundColor Cyan
    Write-Host "   cd frontend" -ForegroundColor White
    Write-Host "   npm start" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping frontend setup (--SkipFrontend flag)" -ForegroundColor Yellow
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start the frontend: cd frontend && npm start" -ForegroundColor White
Write-Host "  2. Open browser: http://localhost:3000" -ForegroundColor White
Write-Host "  3. Test the application with sample queries" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  - View logs: aws logs tail /aws/lambda/weather-wise-recommendation --follow --region $Region" -ForegroundColor White
Write-Host "  - Test API: curl https://your-api-endpoint/prod/recommend" -ForegroundColor White
Write-Host "  - Destroy stack: cd infrastructure && cdk destroy" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: docs/README.md" -ForegroundColor Cyan
Write-Host ""
