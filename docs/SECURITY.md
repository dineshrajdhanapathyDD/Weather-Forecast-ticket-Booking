# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please email the maintainers directly. Do not create a public GitHub issue.

## Security Best Practices

### 1. API Key Management

✅ **DO:**
- Store API keys in environment variables
- Use AWS Secrets Manager for production
- Rotate keys every 90 days
- Use `.env` files (never commit them)
- Monitor API usage regularly

❌ **DON'T:**
- Hardcode API keys in source code
- Commit `.env` files to version control
- Share API keys in chat/email
- Use production keys in development
- Reuse keys across projects

### 2. AWS IAM Permissions

✅ **DO:**
- Use least-privilege IAM roles
- Enable MFA for AWS accounts
- Rotate IAM credentials regularly
- Use IAM roles for Lambda (not access keys)
- Enable CloudTrail logging

❌ **DON'T:**
- Use root account for deployments
- Share IAM credentials
- Grant `*` permissions unnecessarily
- Disable CloudTrail
- Use long-term access keys

### 3. Infrastructure Security

✅ **DO:**
- Enable encryption at rest (S3, DynamoDB)
- Use HTTPS for all API endpoints
- Enable API Gateway throttling
- Set Lambda timeout limits
- Enable VPC for sensitive workloads

❌ **DON'T:**
- Expose Lambda functions publicly
- Disable encryption
- Allow unlimited API requests
- Use default security groups
- Skip security reviews

### 4. Code Security

✅ **DO:**
- Validate all user inputs
- Sanitize data before storage
- Use parameterized queries
- Handle errors gracefully
- Log security events

❌ **DON'T:**
- Trust user input
- Expose stack traces to users
- Log sensitive data
- Use `eval()` or similar
- Ignore security warnings

### 5. Dependency Management

✅ **DO:**
- Keep dependencies updated
- Use `pip-audit` for Python
- Use `npm audit` for Node.js
- Pin dependency versions
- Review dependency licenses

❌ **DON'T:**
- Use outdated packages
- Ignore security advisories
- Install untrusted packages
- Skip dependency audits
- Use wildcards in versions

## Security Checklist

Before deploying to production:

- [ ] All API keys stored in AWS Secrets Manager
- [ ] `.env` files added to `.gitignore`
- [ ] IAM roles follow least-privilege principle
- [ ] CloudTrail enabled for audit logging
- [ ] API Gateway throttling configured
- [ ] Lambda timeout limits set appropriately
- [ ] S3 buckets have encryption enabled
- [ ] DynamoDB tables have encryption enabled
- [ ] All endpoints use HTTPS
- [ ] Input validation implemented
- [ ] Error handling doesn't expose sensitive data
- [ ] Dependencies audited for vulnerabilities
- [ ] CloudWatch alarms configured
- [ ] Backup and disaster recovery plan in place
- [ ] Security review completed

## Secure Deployment Workflow

### Development

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add development API keys
# Edit .env with development keys

# 3. Deploy to development account
cdk deploy --profile dev
```

### Production

```bash
# 1. Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name weather-wise/weather-api-key \
  --secret-string "production-key" \
  --region us-east-2

# 2. Update Lambda to use Secrets Manager
# (See docs/08-api-keys-configuration.md)

# 3. Deploy with production profile
cdk deploy --profile prod --require-approval never

# 4. Verify security settings
aws lambda get-function-configuration \
  --function-name weather-wise-weather-tool \
  --region us-east-2
```

## Incident Response

If a security incident occurs:

1. **Immediate Actions**:
   - Rotate all API keys immediately
   - Review CloudTrail logs for unauthorized access
   - Disable compromised IAM credentials
   - Update Lambda environment variables

2. **Investigation**:
   - Check CloudWatch logs for anomalies
   - Review API Gateway access logs
   - Analyze DynamoDB access patterns
   - Document findings

3. **Remediation**:
   - Apply security patches
   - Update IAM policies
   - Implement additional monitoring
   - Conduct security review

4. **Post-Incident**:
   - Update security documentation
   - Improve monitoring and alerts
   - Train team on lessons learned
   - Review and update security policies

## Compliance

### Data Privacy

- No personally identifiable information (PII) is stored
- Query history stored in DynamoDB with 90-day TTL
- Data encrypted at rest and in transit
- GDPR-compliant data handling

### Audit Logging

- CloudTrail enabled for all API calls
- CloudWatch Logs for Lambda executions
- API Gateway access logs enabled
- DynamoDB streams for data changes

## Security Tools

### Recommended Tools

- **AWS Security Hub**: Centralized security findings
- **AWS GuardDuty**: Threat detection
- **AWS Config**: Configuration compliance
- **pip-audit**: Python dependency scanning
- **npm audit**: Node.js dependency scanning
- **git-secrets**: Prevent committing secrets

### Installation

```bash
# Install git-secrets
git clone https://github.com/awslabs/git-secrets
cd git-secrets
make install

# Configure for repository
cd /path/to/weather-wise-flight-booking
git secrets --install
git secrets --register-aws
```

## Resources

- [AWS Security Best Practices](https://aws.amazon.com/security/best-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [API Keys Configuration](docs/08-api-keys-configuration.md)

---

**Last Updated**: March 13, 2026

For security questions or to report vulnerabilities, contact the maintainers.
