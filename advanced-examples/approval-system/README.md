# Approval System - Human-in-the-Loop Agent

## Overview

The Approval System is a critical safety component that adds human oversight to high-stakes agent actions. It provides a robust approval workflow with web-based dashboard, risk assessment, and comprehensive audit logging.

## Features

### ✅ Approval Workflows
- **Action requests**: Agents request approval before risky operations
- **Risk assessment**: Automatic risk scoring (low, medium, high, critical)
- **Multi-level approval**: Different actions require different authorization levels
- **Timeout handling**: Automatic denial/escalation after timeout

### 🏛️ Web Dashboard
- **Streamlit interface**: Beautiful, real-time approval UI
- **Action details**: Full context for informed decisions
- **Approval history**: View past decisions
- **Bulk operations**: Approve/deny multiple requests

### 📊 Risk Management
- **Automated scoring**: ML-based risk assessment
- **Risk categories**: Financial, data, security, system
- **Escalation rules**: Critical actions auto-escalate
- **Cooldown periods**: Rate limiting on risky operations

### 📝 Audit Trail
- **Complete logging**: Every request and decision logged
- **Compliance ready**: Timestamped, immutable records
- **Export capabilities**: PDF reports for compliance
- **Search and filter**: Find historical approvals

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs reports

# Initialize database
python main.py --init
```

## Quick Start

### 1. Start Dashboard

```bash
# Start the Streamlit dashboard
python main.py --dashboard

# Dashboard available at: http://localhost:8501
```

### 2. Submit Approval Request

```python
from approval_system import ApprovalSystem

approval = ApprovalSystem()

request_id = approval.request_approval(
    agent="deployment-agent",
    action="deploy_to_production",
    details={
        "service": "api-server",
        "version": "v2.1.0",
        "affected_users": 100000
    },
    risk_level="high",
    timeout=3600  # 1 hour
)

# Wait for approval
result = approval.wait_for_approval(request_id)

if result['status'] == 'approved':
    # Proceed with action
    deploy_to_production()
else:
    # Handle denial
    rollback()
```

### 3. Agent Integration

```python
# In your agent code
from master_controller import request_approval

# Before risky operation
if requires_approval(action):
    approved = request_approval(
        action=action,
        risk_level=assess_risk(action),
        details=get_action_details(action)
    )
    
    if not approved:
        logger.warning(f"Action {action} denied")
        return False

# Proceed with action
execute_action(action)
```

## Configuration

### `agent.yaml`

```yaml
name: approval-system
version: 1.0.0

settings:
  # Risk thresholds
  risk_levels:
    low:
      timeout: 3600  # 1 hour
      auto_approve: false
    medium:
      timeout: 1800  # 30 minutes
      requires_comment: true
    high:
      timeout: 900  # 15 minutes
      requires_justification: true
      escalate_after: 600  # 10 minutes
    critical:
      timeout: 300  # 5 minutes
      requires_multi_approval: true
      escalate_immediately: true
  
  # Action categories
  action_categories:
    financial:
      risk_multiplier: 2.0
      requires: "finance_approval"
    data_deletion:
      risk_multiplier: 3.0
      requires: "admin_approval"
    deployment:
      risk_multiplier: 1.5
      requires: "ops_approval"
    security:
      risk_multiplier: 2.5
      requires: "security_approval"
  
  # Notifications
  notifications:
    channels:
      - type: "dashboard"
        enabled: true
      - type: "email"
        enabled: true
        recipients: ["admin@company.com"]
      - type: "slack"
        enabled: false
        webhook: "${SLACK_WEBHOOK}"
  
  # Dashboard
  dashboard:
    port: 8501
    auth_required: false
    refresh_interval: 5  # seconds
  
  # Audit
  audit:
    enabled: true
    retention_days: 365
    export_format: "pdf"
```

## Usage Examples

### Financial Transaction

```python
# Agent requests approval for large transaction
request_id = approval.request_approval(
    agent="finance-bot",
    action="transfer_funds",
    details={
        "amount": 50000,
        "from": "operating_account",
        "to": "vendor_payment",
        "vendor": "ACME Corp",
        "invoice": "INV-2024-001"
    },
    risk_level="high",
    category="financial"
)

# Human reviews in dashboard
# - Sees full transaction details
# - Verifies invoice and vendor
# - Approves with comment: "Invoice verified, payment authorized"

result = approval.wait_for_approval(request_id, timeout=1800)

if result['status'] == 'approved':
    process_payment()
    log_transaction(approved_by=result['approved_by'])
```

### Data Deletion

```python
# User deletion request
request_id = approval.request_approval(
    agent="data-manager",
    action="delete_user_data",
    details={
        "user_id": "user-12345",
        "reason": "GDPR deletion request",
        "data_types": ["profile", "activity", "messages"],
        "permanent": True
    },
    risk_level="critical",
    category="data_deletion"
)

# Requires admin approval + justification
result = approval.wait_for_approval(request_id)

if result['status'] == 'approved':
    delete_user_data(user_id)
    notify_compliance_team()
else:
    notify_user_of_denial()
```

### Production Deployment

```python
# Deployment to production
request_id = approval.request_approval(
    agent="ci-cd-pipeline",
    action="deploy_to_production",
    details={
        "service": "api-server",
        "version": "v2.1.0",
        "changes": [
            "New authentication system",
            "Performance optimizations",
            "Bug fixes"
        ],
        "tests_passed": True,
        "rollback_plan": "automated-rollback-enabled",
        "estimated_downtime": "0 minutes"
    },
    risk_level="medium",
    category="deployment"
)

result = approval.wait_for_approval(request_id)

if result['status'] == 'approved':
    deploy(version="v2.1.0")
    monitor_deployment()
else:
    cancel_deployment()
```

## Risk Assessment

### Automatic Risk Scoring

The system automatically assesses risk based on:

1. **Action Type**
   - Financial operations: High risk
   - Data deletion: Critical risk
   - Read-only operations: Low risk

2. **Impact Scope**
   - Number of affected users
   - Data volume
   - System criticality

3. **Reversibility**
   - Can action be undone?
   - Is there a backup?
   - Rollback available?

4. **Historical Context**
   - Similar actions in past
   - Success rate
   - Previous issues

### Custom Risk Rules

```python
# Define custom risk assessment
def assess_custom_risk(action_details):
    risk_score = 0
    
    # Financial amount
    if 'amount' in action_details:
        amount = action_details['amount']
        if amount > 100000:
            risk_score += 50
        elif amount > 10000:
            risk_score += 25
    
    # User impact
    if 'affected_users' in action_details:
        users = action_details['affected_users']
        if users > 10000:
            risk_score += 30
        elif users > 1000:
            risk_score += 15
    
    # Time of day (higher risk outside business hours)
    hour = datetime.now().hour
    if hour < 8 or hour > 18:
        risk_score += 10
    
    # Map score to level
    if risk_score >= 70:
        return 'critical'
    elif risk_score >= 50:
        return 'high'
    elif risk_score >= 25:
        return 'medium'
    else:
        return 'low'
```

## Dashboard Features

### Main View

- **Pending Approvals**: List of requests awaiting decision
- **Action Details**: Full context for each request
- **Risk Indicator**: Visual risk level (color-coded)
- **Time Remaining**: Countdown to auto-deny
- **Quick Actions**: Approve/Deny buttons

### Approval View

```
┌──────────────────────────────────────────────────┐
│ Approval Request #AR-2024-001                    │
├──────────────────────────────────────────────────┤
│ Agent: deployment-agent                          │
│ Action: deploy_to_production                     │
│ Risk Level: HIGH ⚠️                              │
│                                                  │
│ Details:                                         │
│   • Service: api-server                          │
│   • Version: v2.1.0                              │
│   • Affected Users: 100,000                      │
│   • Tests Passed: ✓                              │
│   • Rollback Available: ✓                        │
│                                                  │
│ Time Remaining: 14:32                            │
│                                                  │
│ [Approve] [Deny] [Request More Info]             │
└──────────────────────────────────────────────────┘
```

### History View

- **All approvals**: Searchable history
- **Filter by**: Agent, action, risk level, date
- **Export**: Download as PDF/CSV
- **Analytics**: Approval rate, response time

## API Reference

### Python API

```python
from approval_system import ApprovalSystem

# Initialize
approval = ApprovalSystem()

# Request approval
request_id = approval.request_approval(
    agent="my-agent",
    action="risky_action",
    details={"key": "value"},
    risk_level="high",
    category="security",
    timeout=1800
)

# Check status
status = approval.get_status(request_id)

# Wait for decision
result = approval.wait_for_approval(
    request_id,
    timeout=1800,
    poll_interval=5
)

# Manual approval (for testing)
approval.approve(
    request_id,
    approver="admin",
    comment="Approved for testing"
)

# Deny request
approval.deny(
    request_id,
    approver="admin",
    reason="Insufficient justification"
)
```

## Integration Patterns

### Pattern 1: Synchronous Wait

```python
# Agent waits for approval before proceeding
if risk_level >= RiskLevel.HIGH:
    request_id = request_approval(action_details)
    result = wait_for_approval(request_id)
    
    if result['status'] != 'approved':
        return False

execute_action()
```

### Pattern 2: Asynchronous Callback

```python
# Agent continues, callback on approval
def on_approval(result):
    if result['status'] == 'approved':
        execute_action()
    else:
        cleanup()

request_id = request_approval(
    action_details,
    callback=on_approval
)

# Agent continues with other work
continue_other_tasks()
```

### Pattern 3: Workflow Integration

```python
# Multi-step workflow with approvals
workflow = WorkflowBuilder()

workflow.add_step('prepare', prepare_deployment)
workflow.add_approval('deploy_approval', risk_level='high')
workflow.add_step('deploy', execute_deployment)
workflow.add_step('verify', verify_deployment)
workflow.add_approval('finalize_approval', risk_level='medium')
workflow.add_step('finalize', finalize_deployment)

workflow.run()
```

## Security Considerations

### Authentication
- Dashboard authentication (optional)
- API key validation
- Session management
- Rate limiting

### Authorization
- Role-based access control
- Multi-level approvals
- Action-specific permissions
- Audit trail

### Data Protection
- Sensitive data masking in UI
- Encrypted database
- Secure communication
- PII handling

## Best Practices

### 1. Risk Assessment
- Always assess risk objectively
- Consider blast radius
- Check reversibility
- Review historical data

### 2. Clear Communication
- Provide full context in requests
- Include rollback plans
- Document dependencies
- Explain urgency

### 3. Timeout Strategy
- Set appropriate timeouts
- Have escalation paths
- Plan for timeout scenarios
- Monitor response times

### 4. Audit Compliance
- Log all decisions
- Retain records appropriately
- Regular audit reviews
- Export for compliance

## Troubleshooting

### Dashboard Won't Load
```bash
# Check Streamlit is installed
pip install streamlit

# Check port availability
lsof -i :8501

# Run with debug
streamlit run dashboard.py --logger.level=debug
```

### Approvals Not Saving
```bash
# Check database
python main.py --check-db

# Verify permissions
ls -la data/approvals.db

# Reinitialize if needed
python main.py --init --force
```

## License

Provided as-is for development purposes.

---

**Safety through oversight. 🛡️**