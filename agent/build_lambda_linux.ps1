# Build Lambda deployment package for Linux (without Docker)

Write-Host "Building Lambda deployment package for Linux..." -ForegroundColor Green

# Create a clean build directory
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null

# Copy source files
Copy-Item "weather_wise_agent.py" "build/"
Copy-Item "__init__.py" "build/"

# Install dependencies for Linux platform
Write-Host "Installing dependencies for Linux..." -ForegroundColor Yellow
pip install -r requirements.txt `
    --platform manylinux2014_x86_64 `
    --target build/ `
    --implementation cp `
    --python-version 3.11 `
    --only-binary=:all: `
    --upgrade `
    --quiet

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
if (Test-Path "lambda_package.zip") {
    Remove-Item "lambda_package.zip"
}

python -c "import shutil; shutil.make_archive('lambda_package', 'zip', 'build')"

Write-Host "Lambda package created: lambda_package.zip" -ForegroundColor Green
Write-Host "Size: $([math]::Round((Get-Item lambda_package.zip).Length / 1MB, 2)) MB" -ForegroundColor Cyan
