# Build Lambda deployment package using Docker (Linux environment)

Write-Host "Building Lambda deployment package using Docker..." -ForegroundColor Green

# Create a clean build directory
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null

# Copy source files
Copy-Item "weather_wise_agent.py" "build/"
Copy-Item "__init__.py" "build/"
Copy-Item "requirements.txt" "build/"

# Use Docker to install dependencies in a Linux environment
Write-Host "Installing dependencies in Linux environment..." -ForegroundColor Yellow
docker run --rm -v "${PWD}/build:/build" -w /build public.ecr.aws/lambda/python:3.11 pip install -r requirements.txt -t . --no-cache-dir

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
if (Test-Path "lambda_package.zip") {
    Remove-Item "lambda_package.zip"
}

# Use Python to create zip (cross-platform)
python -c "import shutil; shutil.make_archive('lambda_package', 'zip', 'build')"

# Clean up build directory
Remove-Item -Recurse -Force "build"

Write-Host "Lambda package created: lambda_package.zip" -ForegroundColor Green
Write-Host "Size: $([math]::Round((Get-Item lambda_package.zip).Length / 1MB, 2)) MB" -ForegroundColor Cyan
