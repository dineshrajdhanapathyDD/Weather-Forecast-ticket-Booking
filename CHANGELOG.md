# Changelog

All notable changes to the Weather-Wise Flight Booking Agent project.

## [1.1.0] - 2026-03-13

### 🔒 Security Enhancements

- **Removed hardcoded API keys** from CDK stack
- **Created secure environment variable system** with `.env.example` and `.env.secure.example`
- **Moved API_KEYS.md to docs/** as `08-api-keys-configuration.md` with comprehensive security documentation
- **Updated .gitignore** with extensive security patterns
- **Added SECURITY.md** with security best practices and incident response procedures
- **Implemented environment variable validation** in deployment script

### 📁 Project Structure Improvements

- **Reorganized documentation** - All MD files now in `docs/` folder
- **Updated README.md** with comprehensive project structure and documentation
- **Created deployment script** (`deploy.ps1`) with security checks and validation
- **Added environment templates** (`.env.example`, `.env.secure.example`)
- **Updated docs/README.md** with new API keys documentation reference

### 🎨 Frontend Updates

- **Updated footer attribution** to "Powered by Amazon Nova" (simplified)
- **Maintained responsive design** and user experience
- **Kept dual-mode interface** (Chat Mode and Search Mode)

### 🐛 Bug Fixes

- **Fixed Fare Tool API error** - Replaced non-existent external API with realistic mock data generator
- **Fixed Search Mode** - Corrected response parsing to extract `data` field from Lambda response
- **Resolved "Internal server error"** in recommendation endpoint

### 🔧 Technical Improvements

- **Mock Fare Data Generator**:
  - Deterministic pricing based on route hash
  - Date-based price variations (closer to travel = higher prices)
  - 30-day historical data with realistic trends (rising, stable, dropping)
  - Consistent results for same route/date combinations

- **Environment Variable Management**:
  - CDK stack now uses `process.env` exclusively
  - No hardcoded API keys in source code
  - Deployment script validates required variables
  - Support for AWS Secrets Manager (documented)

### 📚 Documentation

- **New Documents**:
  - `docs/08-api-keys-configuration.md` - Comprehensive API key management guide
  - `SECURITY.md` - Security policy and best practices
  - `CHANGELOG.md` - This file
  - `.env.example` - Environment variables template
  - `.env.secure.example` - Detailed secure configuration template

- **Updated Documents**:
  - `README.md` - Complete rewrite with project structure and quick start
  - `docs/README.md` - Added API keys documentation reference
  - `.gitignore` - Enhanced security patterns

### 🚀 Deployment

- **New automated deployment script** (`deploy.ps1`):
  - Environment variable validation
  - Automatic Lambda package building
  - CDK bootstrap check
  - Frontend configuration
  - Comprehensive error handling
  - Colored output for better UX

### 📦 File Structure Changes

```
Added:
+ .env.example
+ .env.secure.example
+ SECURITY.md
+ CHANGELOG.md
+ docs/08-api-keys-configuration.md
+ deploy.ps1 (enhanced version)

Removed:
- API_KEYS.md (moved to docs/)

Modified:
~ README.md (complete rewrite)
~ docs/README.md (added new doc reference)
~ .gitignore (enhanced security)
~ frontend/src/App.js (updated footer)
~ infrastructure/lib/weather-wise-stack.ts (removed hardcoded keys)
~ lambda/fare_tool/handler.py (mock data generator)
~ lambda/recommendation/handler.py (response format fix)
```

## [1.0.0] - 2026-02-28

### Initial Release

- ✅ Amazon Bedrock Agent with Strands SDK
- ✅ Weather MCP Tool (WeatherAPI.com integration)
- ✅ Fare MCP Tool (external API integration)
- ✅ Recommendation Engine with smart algorithms
- ✅ React frontend with dual-mode interface
- ✅ AWS CDK infrastructure as code
- ✅ Comprehensive documentation (7 documents)
- ✅ Unit and property-based tests
- ✅ DynamoDB query history
- ✅ S3 historical data storage

---

## Version History

- **1.1.0** (2026-03-13) - Security enhancements, project reorganization, bug fixes
- **1.0.0** (2026-02-28) - Initial release

## Upgrade Guide

### From 1.0.0 to 1.1.0

1. **Create .env file**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

2. **Update deployment**:
   ```bash
   # Set environment variables
   $env:WEATHER_API_KEY = "your-key"
   $env:FARE_API_KEY = "your-key"
   
   # Run new deployment script
   .\deploy.ps1
   ```

3. **Verify security**:
   - Check that API_KEYS.md is not in your repository
   - Verify .env is in .gitignore
   - Review SECURITY.md for best practices

4. **Update frontend** (if running):
   ```bash
   cd frontend
   npm start
   ```

## Breaking Changes

### 1.1.0

- **API Keys**: Hardcoded keys removed from CDK stack. Must use environment variables.
- **File Locations**: API_KEYS.md moved to docs/08-api-keys-configuration.md
- **Deployment**: New deployment script with validation (old manual process still works)

## Migration Notes

If you have an existing deployment:

1. **Export your current API keys** from Lambda environment variables
2. **Create .env file** with those keys
3. **Redeploy** using the new deployment script
4. **Verify** all Lambda functions have correct environment variables

```bash
# Check current Lambda config
aws lambda get-function-configuration \
  --function-name weather-wise-weather-tool \
  --region us-east-2 \
  --query 'Environment.Variables'
```

## Future Roadmap

### Planned for 1.2.0

- [ ] AWS Secrets Manager integration (automatic)
- [ ] Real-time weather alerts
- [ ] Price prediction ML model
- [ ] Multi-region deployment support
- [ ] Enhanced monitoring dashboard
- [ ] Mobile app (React Native)

### Under Consideration

- [ ] Integration with real flight booking APIs
- [ ] User authentication and profiles
- [ ] Saved searches and preferences
- [ ] Email/SMS notifications
- [ ] Multi-language support
- [ ] Carbon footprint calculator

---

**Maintained by**: Weather-Wise Team  
**Last Updated**: March 13, 2026
