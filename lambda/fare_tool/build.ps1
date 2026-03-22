# Build Fare Tool Lambda Package
Write-Host "Building Fare Tool Lambda package..." -ForegroundColor Cyan

# Create build directory
$buildDir = "build"
if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt -t $buildDir --platform manylinux2014_x86_64 --only-binary=:all:

# Copy source files
Write-Host "Copying source files..." -ForegroundColor Yellow
Copy-Item handler.py $buildDir/
Copy-Item __init__.py $buildDir/

# Create ZIP package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
$zipPath = "fare_tool.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath
}

Compress-Archive -Path "$buildDir\*" -DestinationPath $zipPath

Write-Host "Package created: $zipPath" -ForegroundColor Green
Write-Host "Size: $((Get-Item $zipPath).Length / 1MB) MB" -ForegroundColor Green
