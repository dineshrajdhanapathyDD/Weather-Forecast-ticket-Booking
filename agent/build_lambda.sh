#!/bin/bash
# Build Lambda deployment package with dependencies

# Create a clean build directory
rm -rf build
mkdir -p build

# Copy source files
cp weather_wise_agent.py build/
cp __init__.py build/

# Install dependencies to build directory
pip install -r requirements.txt -t build/

# Create deployment package
cd build
zip -r ../lambda_package.zip .
cd ..

echo "Lambda package created: lambda_package.zip"
