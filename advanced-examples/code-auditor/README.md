# Code Auditor - Security Sentinel Agent

## Overview

The Code Auditor is an autonomous security scanning agent that continuously monitors your codebase for security vulnerabilities, exposed secrets, and code quality issues. It operates locally, maintaining complete privacy while providing enterprise-grade security scanning.

## Features

### 🔍 Security Scanning
- **Bandit Integration**: Python security vulnerability detection
- **Secret Detection**: Scans for exposed API keys, passwords, and tokens
- **Dependency Analysis**: Checks for vulnerable dependencies
- **OWASP Top 10**: Covers common security vulnerabilities

### 📁 File Monitoring
- **Real-time Watching**: Monitors directories for changes using watchdog
- **Selective Scanning**: Focus on specific file types and patterns
- **Incremental Analysis**: Only scans changed files for efficiency
- **Batch Processing**: Handles large codebases efficiently

### 📊 Reporting
- **SQLite Database**: Local storage of all findings
- **Severity Levels**: Critical, High, Medium, Low classifications
- **Historical Tracking**: Track issues over time
- **Trend Analysis**: Identify improving or degrading security posture

### 🔔 Notifications
- **Critical Alerts**: Immediate notification for severe issues
- **Daily Summaries**: Aggregated reports of findings
- **Custom Rules**: Define your own security patterns

## Installation

### Prerequisites

```bash
Python 3.8+
pip
virtualenv (recommended)
```

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs data reports
```

### Configuration

Edit `agent.yaml` to configure the agent:

```yaml
name: code-auditor
version: 1.0.0
description: Security scanning agent for codebase monitoring

triggers:
  - type: file_change
    path: "/path/to/your/code"
    patterns:
      - "*.py"
      - "*.js"
      - "*.java"
      - "*.go"
  - type: schedule
    cron: "0 2 * * *"  # Daily at 2 AM

settings:
  watch_directories:
    - "/path/to/project/src"
    - "/path/to/project/lib"
  
  exclude_patterns:
    - "*/node_modules/*"
    - "*/venv/*"
    - "*/.git/*"
    - "*/build/*"
  
  severity_threshold: "medium"  # Only report medium and above
  
  secret_patterns:
    - "api[_-]?key"
    - "password\s*="
    - "secret[_-]?token"
    - "aws[_-]?access[_-]?key"
  
  notification:
    critical_immediate: true
    email: your-email@example.com  # Optional

permissions:
  - filesystem:read
  - filesystem:write:./data
  - filesystem:write:./logs
  - filesystem:write:./reports

resources:
  max_memory: 512MB
  max_cpu: 50%
```

## Usage

### Basic Usage

```bash
# Run once
python main.py --scan /path/to/code

# Start monitoring mode
python main.py --watch /path/to/code

# Scan with specific rules
python main.py --scan /path/to/code --config custom-rules.yaml
```

### Command Line Options

```
Options:
  --scan PATH           Scan directory once and exit
  --watch PATH          Monitor directory for changes
  --config FILE         Custom configuration file
  --report FORMAT       Generate report (json, html, pdf)
  --severity LEVEL      Minimum severity to report
  --exclude PATTERN     Exclude files matching pattern
  --quiet              Suppress non-critical output
  --verbose            Enable detailed logging
```

### Example Commands

```bash
# Quick scan of current directory
python main.py --scan . --report html

# Watch with custom exclusions
python main.py --watch ~/projects/myapp --exclude "*/tests/*"

# Critical issues only
python main.py --scan . --severity critical --quiet
```

## Security Checks

### 1. Secrets Detection

Detects exposed sensitive information:
- API keys and tokens
- Passwords in code
- Private keys
- Database credentials
- OAuth secrets

**Example patterns:**
```python
# BAD - Will be flagged
api_key = "sk-1234567890abcdef"
password = "mySecretPassword123"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

# GOOD - Using environment variables
import os
api_key = os.getenv('API_KEY')
password = os.getenv('DB_PASSWORD')
```

### 2. Code Vulnerabilities

Scans for common security issues:
- SQL injection risks
- Command injection
- Path traversal vulnerabilities
- Insecure deserialization
- Weak cryptography

**Example:**
```python
# BAD - SQL injection risk
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD - Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### 3. Dependency Vulnerabilities

Checks for known vulnerabilities in:
- Python packages (pip)
- JavaScript packages (npm)
- Java dependencies (Maven)
- Go modules

### 4. Code Quality Issues

- Unused imports
- Dead code
- Complexity warnings
- Security anti-patterns

## Output and Reports

### Database Schema

```sql
CREATE TABLE scans (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    path TEXT,
    duration_seconds REAL,
    files_scanned INTEGER,
    issues_found INTEGER
);

CREATE TABLE findings (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER,
    file_path TEXT,
    line_number INTEGER,
    severity TEXT,
    issue_type TEXT,
    description TEXT,
    recommendation TEXT,
    cwe_id TEXT,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);
```

### Report Formats

**JSON Report:**
```json
{
  "scan_id": "20231215-120000",
  "timestamp": "2023-12-15T12:00:00Z",
  "summary": {
    "critical": 2,
    "high": 5,
    "medium": 12,
    "low": 8
  },
  "findings": [
    {
      "file": "src/api/auth.py",
      "line": 45,
      "severity": "critical",
      "type": "hardcoded_secret",
      "description": "API key found in source code",
      "recommendation": "Move to environment variable"
    }
  ]
}
```

**HTML Report:**
Generated in `./reports/scan-{timestamp}.html` with:
- Executive summary
- Severity breakdown
- Detailed findings
- Remediation guidance

## Integration

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
python /path/to/code-auditor/main.py --scan . --severity high --quiet
if [ $? -ne 0 ]; then
    echo "Security issues found. Commit rejected."
    exit 1
fi
```

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Security Audit
        run: |
          pip install -r code-auditor/requirements.txt
          python code-auditor/main.py --scan . --report json
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: reports/
```

### Master Controller Integration

```python
# Master controller can trigger audits
from code_auditor import SecurityAuditor

auditor = SecurityAuditor(config_path="agent.yaml")
results = auditor.scan_directory("/path/to/code")

if results['critical'] > 0:
    # Trigger approval workflow
    master_controller.request_approval(
        action="deploy",
        risk_level="high",
        reason=f"Critical security issues: {results['critical']}"
    )
```

## Monitoring

### Logs

Logs are written to `./logs/code-auditor.log`:

```
2023-12-15 12:00:00 INFO Starting security scan of /path/to/code
2023-12-15 12:00:05 WARNING Found hardcoded secret in auth.py:45
2023-12-15 12:00:10 ERROR Critical vulnerability in database.py:120
2023-12-15 12:00:15 INFO Scan complete: 2 critical, 5 high, 12 medium
```

### Status Monitoring

```bash
# Check agent status
python main.py --status

# Output:
Agent: code-auditor
Status: Running
Last Scan: 2 minutes ago
Findings: 2 critical, 5 high
Next Scheduled: 2023-12-16 02:00:00
```

## Troubleshooting

### Common Issues

**High CPU usage:**
- Reduce watched directory scope
- Increase scan interval
- Exclude large binary files

**False positives:**
- Adjust sensitivity in config
- Add custom exclusion patterns
- Whitelist specific findings

**Missing dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

## Security Considerations

### Agent Security
- Runs with minimal permissions
- Only reads source code files
- Writes only to designated directories
- No network access required

### Data Privacy
- All data stored locally
- No telemetry or external reporting
- Sensitive findings encrypted in database
- Reports sanitized before sharing

## Performance

### Benchmarks

| Codebase Size | Scan Time | Memory Usage |
|---------------|-----------|-------------|
| Small (<1K files) | 5-10s | 50MB |
| Medium (1-10K) | 30-60s | 150MB |
| Large (>10K) | 2-5min | 300MB |

### Optimization Tips

1. **Exclude unnecessary directories**
2. **Use incremental scanning**
3. **Run during off-hours**
4. **Limit file types**
5. **Cache scan results**

## Advanced Usage

### Custom Rules

Create `custom-rules.yaml`:

```yaml
rules:
  - id: custom-001
    name: Company Secret Pattern
    pattern: "COMPANY_[A-Z]+_KEY"
    severity: critical
    message: "Company API key detected"
  
  - id: custom-002
    name: Internal IP
    pattern: "10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    severity: medium
    message: "Internal IP address in code"
```

### API Usage

```python
from code_auditor import SecurityAuditor

# Initialize
auditor = SecurityAuditor()

# Scan single file
result = auditor.scan_file('/path/to/file.py')

# Scan directory
results = auditor.scan_directory('/path/to/code', recursive=True)

# Get findings by severity
critical = auditor.get_findings(severity='critical')

# Generate report
auditor.generate_report(format='html', output='report.html')
```

## Contributing

To extend this agent:

1. Add new security patterns to `patterns.yaml`
2. Implement custom scanners in `scanners/`
3. Add tests in `tests/`
4. Update documentation

## License

Provided as-is for educational and development purposes.

---

**Stay secure! 🔒**