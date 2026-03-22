# Build Lambda deployment package with dependencies

Write-Host "Building Lambda deployment package..." -ForegroundColor Green

# Create a clean build directory
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
New-Item -ItemType Directory -Path "build" | Out-Null

# Copy source files
Copy-Item "weather_wise_agent.py" "build/"
Copy-Item "__init__.py" "build/"

# Install dependencies to build directory
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t build/ --quiet

# Create deployment package (using Python's zipfile since Windows doesn't have zip)
Write-Host "Creating deployment package..." -ForegroundColor Yellow
python -c "import shutil; shutil.make_archive('lambda_package', 'zip', 'build')"

Write-Host "Lambda package created: lambda_package.zip" -ForegroundColor Green
Write-Host "Size: $((Get-Item lambda_package.zip).Length / 1MB) MB" -ForegroundColor Cyan
