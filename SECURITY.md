# Security Guidelines

## 🔒 Security Best Practices

This document outlines security considerations for the Cognitive Orchestration Stack.

### Environment Variables

**NEVER commit sensitive environment variables to git!**

- ✅ `config/*.env.template` - Safe to commit (no secrets)
- ❌ `config/*.env` - Never commit (contains secrets)
- ❌ `.env` files - Never commit (contains secrets)

### Sensitive Data

The following directories and files are gitignored and should never be committed:

- `scratch/` - Research data and synthesized content
- `chroma_db/` - Vector database files
- `logs/` - Application logs (may contain sensitive info)
- `data/` - User documents and data
- `security-results.json` - Security scan results
- `test_results.txt` - Test output files

### API Keys and Credentials

All API keys and credentials should be stored in environment variables:

- `NEO4J_PASSWORD` - Database password
- `SERPAPI_KEY` - Search API key
- `BRAVE_API_KEY` - Search API key
- `GOOGLE_API_KEY` - Google API key (optional)

### Development Setup

1. Copy the template: `cp config/dev.env.template config/dev.env`
2. Edit `config/dev.env` with your actual credentials
3. Never share your `dev.env` file

### Production Security

- Use HashiCorp Vault for production secrets
- Rotate API keys regularly
- Monitor access logs
- Use strong passwords for all services

## 🚨 Security Checklist

Before committing to git:

- [ ] No `.env` files in the commit
- [ ] No API keys in source code
- [ ] No passwords in source code
- [ ] No sensitive data in `scratch/` or `data/`
- [ ] No database files in `chroma_db/`
- [ ] No log files in `logs/`

## 🔍 Security Audit

Run security checks:

```bash
# Check for secrets in code
grep -r "password\|secret\|key\|token" src/ --exclude-dir=__pycache__

# Check git status for sensitive files
git status --porcelain | grep -E "\.(env|log|db|sqlite)$"
```

## 📞 Reporting Security Issues

If you discover a security vulnerability, please report it privately to the maintainers.
