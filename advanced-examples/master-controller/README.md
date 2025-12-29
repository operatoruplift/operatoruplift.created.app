# Master Controller - Agent Orchestration System

## Overview

The Master Controller is a central orchestration system that manages, coordinates, and monitors multiple UPLIFT agents. It acts as the "brain" of your multi-agent ecosystem, handling task distribution, resource management, inter-agent communication, and system-wide coordination.

## Features

### 🎯 Agent Orchestration
- **Multi-agent coordination**: Manage dozens of agents simultaneously
- **Task distribution**: Intelligent workload balancing
- **Dependency management**: Handle inter-agent dependencies
- **Priority scheduling**: Critical tasks get immediate attention

### 📊 Resource Management
- **CPU/Memory monitoring**: Track resource usage
- **Resource allocation**: Prevent resource contention
- **Throttling**: Slow down agents exceeding limits
- **Auto-scaling**: Start/stop agents based on demand

### 🔗 Inter-Agent Communication
- **Message bus**: Agents communicate through controller
- **Event propagation**: Events trigger multi-agent workflows
- **State synchronization**: Shared state management
- **Data pipelines**: Output from one agent feeds another

### 👁️ Monitoring & Observability
- **Health checks**: Monitor agent status
- **Performance metrics**: Track execution times, success rates
- **Alerting**: Notify on failures or anomalies
- **Dashboard**: Web-based monitoring interface

## Architecture

```
┌─────────────────────────────────────────┐
│        Master Controller                │
│                                         │
│  ┌──────────┐  ┌───────────┐          │
│  │ Scheduler│  │ Resource  │          │
│  │          │  │ Manager   │          │
│  └──────────┘  └───────────┘          │
│                                         │
│  ┌──────────┐  ┌───────────┐          │
│  │ Message  │  │ Monitor   │          │
│  │ Bus      │  │           │          │
│  └──────────┘  └───────────┘          │
└─────────────────┬───────────────────────┘
                  │
       ┌──────────┼──────────┐
       │          │          │
    ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
    │Agent│   │Agent│   │Agent│
    │  1  │   │  2  │   │  N  │
    └─────┘   └─────┘   └─────┘
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create directory structure
mkdir -p logs data agents config

# Initialize
python main.py --init
```

## Configuration

### Master Configuration: `agent.yaml`

```yaml
name: master-controller
version: 1.0.0

settings:
  # Agent discovery
  agent_directory: "./agents"
  auto_discover: true
  
  # Scheduling
  scheduler:
    max_concurrent: 10
    default_priority: 5
    queue_type: "priority"  # priority, fifo, lifo
  
  # Resource limits
  resources:
    max_total_memory: "4GB"
    max_total_cpu: 80  # percent
    per_agent_memory: "512MB"
    per_agent_cpu: 25  # percent
  
  # Monitoring
  monitoring:
    health_check_interval: 60  # seconds
    metric_retention_days: 30
    enable_dashboard: true
    dashboard_port: 8501
  
  # Message bus
  messaging:
    bus_type: "in_memory"  # in_memory, redis, rabbitmq
    max_queue_size: 1000
    message_ttl: 3600  # seconds
```

### Agent Registration: `agents/agent-name/manifest.yaml`

```yaml
name: code-auditor
type: monitor
priority: 8

dependencies:
  - name: file-watcher
    required: true

resources:
  memory: 256MB
  cpu: 20%

triggers:
  - type: schedule
    cron: "0 2 * * *"
  - type: event
    event: "file_changed"

outputs:
  - type: event
    event: "security_issue_found"
  - type: message
    topic: "security.alerts"
```

## Usage

### Starting the Controller

```bash
# Start with auto-discovery
python main.py --start

# Start specific agents
python main.py --start --agents code-auditor,health-monitor

# Start in foreground (no daemon)
python main.py --start --foreground

# Start with custom config
python main.py --start --config custom-config.yaml
```

### Managing Agents

```bash
# List all agents
python main.py --list

# Agent status
python main.py --status code-auditor

# Start specific agent
python main.py --agent-start code-auditor

# Stop specific agent
python main.py --agent-stop code-auditor

# Restart agent
python main.py --agent-restart code-auditor

# Remove agent
python main.py --agent-remove code-auditor
```

### Task Management

```bash
# Submit task
python main.py --task-submit \
  --agent code-auditor \
  --action scan \
  --params '{"path": "/workspace"}'

# List tasks
python main.py --task-list

# Cancel task
python main.py --task-cancel <task_id>

# Task status
python main.py --task-status <task_id>
```

### Monitoring

```bash
# View dashboard
python main.py --dashboard

# View logs
python main.py --logs --agent code-auditor --tail

# System stats
python main.py --stats

# Export metrics
python main.py --export-metrics --format json
```

## Agent Communication

### Event-Driven Workflows

```python
# Agent 1: Emits event
from master_controller import emit_event

emit_event('file_changed', {
    'path': '/workspace/code.py',
    'change_type': 'modified'
})

# Agent 2: Listens for event
from master_controller import on_event

@on_event('file_changed')
def handle_file_change(event_data):
    path = event_data['path']
    # Scan the file
    scan_file(path)
```

### Message Passing

```python
# Agent 1: Sends message
from master_controller import send_message

send_message(
    topic='security.alerts',
    message={
        'severity': 'critical',
        'file': '/workspace/auth.py',
        'issue': 'hardcoded API key'
    }
)

# Agent 2: Subscribes to messages
from master_controller import subscribe

@subscribe('security.alerts')
def handle_security_alert(message):
    if message['severity'] == 'critical':
        # Request human approval
        request_approval(message)
```

### Direct Agent Calls

```python
# Master controller calling agent
from master_controller import invoke_agent

result = invoke_agent(
    agent_name='code-auditor',
    action='scan',
    params={'path': '/workspace'},
    timeout=300
)

if result['issues_found'] > 0:
    # Take action
    invoke_agent(
        agent_name='approval-system',
        action='request_approval',
        params={
            'action': 'deploy',
            'reason': f"{result['issues_found']} security issues"
        }
    )
```

## Scheduling

### Priority-Based Scheduling

```python
# High priority task
submit_task(
    agent='security-scanner',
    action='scan',
    priority=10,  # 1-10, 10 is highest
    params={'path': '/critical'}
)

# Background task
submit_task(
    agent='backup-agent',
    action='backup',
    priority=3,
    params={'path': '/data'}
)
```

### Dependency Management

```yaml
# Agent manifest with dependencies
name: deployment-agent
dependencies:
  - name: code-auditor
    condition: "no_critical_issues"
  - name: test-runner
    condition: "all_tests_passed"
  - name: approval-system
    condition: "approved"

workflow:
  - run: code-auditor.scan
  - if: critical_issues_found
    then: abort
  - run: test-runner.run_tests
  - if: tests_failed
    then: abort
  - run: approval-system.request_approval
  - wait_for: approval
  - run: deploy
```

## Advanced Features

### Agent Chaining

```python
from master_controller import create_chain

# Create processing pipeline
chain = create_chain([
    {'agent': 'file-watcher', 'action': 'watch'},
    {'agent': 'code-auditor', 'action': 'scan'},
    {'agent': 'test-runner', 'action': 'test'},
    {'agent': 'deployment-agent', 'action': 'deploy'}
])

chain.on_error('code-auditor', lambda e: [
    send_notification(f"Security scan failed: {e}"),
    abort_chain()
])

chain.run()
```

### Resource Quotas

```python
# Set agent resource limits
set_agent_quota(
    agent='heavy-processor',
    limits={
        'cpu_percent': 50,
        'memory_mb': 1024,
        'disk_io_mbps': 100,
        'network_mbps': 50
    }
)

# Monitor resource usage
usage = get_agent_usage('heavy-processor')
if usage['cpu_percent'] > 80:
    throttle_agent('heavy-processor', factor=0.5)
```

### Failover and Recovery

```python
# Configure failover
configure_failover(
    agent='critical-monitor',
    strategy='restart',
    max_retries=3,
    retry_delay=60,
    on_failure=[
        notify_admin,
        start_backup_agent
    ]
)

# Manual recovery
recover_agent('failed-agent', strategy='recreate')
```

## Monitoring Dashboard

The web dashboard provides:

- **Agent Status**: Real-time agent health
- **Task Queue**: View pending/running tasks
- **Resource Usage**: CPU, memory, disk charts
- **Event Log**: Recent system events
- **Metrics**: Performance statistics
- **Controls**: Start/stop agents, submit tasks

Access at: `http://localhost:8501`

## API Reference

### Python API

```python
from master_controller import MasterController

# Initialize
controller = MasterController(config_path='agent.yaml')

# Register agent
controller.register_agent(
    name='my-agent',
    manifest_path='./agents/my-agent/manifest.yaml'
)

# Start agent
controller.start_agent('my-agent')

# Submit task
task_id = controller.submit_task(
    agent='my-agent',
    action='process',
    params={'input': 'data'},
    priority=5
)

# Wait for completion
result = controller.wait_for_task(task_id, timeout=300)

# Stop agent
controller.stop_agent('my-agent')

# Shutdown controller
controller.shutdown()
```

### REST API

```bash
# Start REST API server
python main.py --api --port 8080

# Agent operations
curl http://localhost:8080/agents
curl http://localhost:8080/agents/code-auditor
curl -X POST http://localhost:8080/agents/code-auditor/start
curl -X POST http://localhost:8080/agents/code-auditor/stop

# Task operations
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "code-auditor",
    "action": "scan",
    "params": {"path": "/workspace"}
  }'

curl http://localhost:8080/tasks/<task_id>
curl -X DELETE http://localhost:8080/tasks/<task_id>

# System operations
curl http://localhost:8080/stats
curl http://localhost:8080/health
```

## Best Practices

### 1. Agent Design
- Keep agents focused and single-purpose
- Use events for loose coupling
- Handle failures gracefully
- Provide clear status updates

### 2. Resource Management
- Set appropriate resource limits
- Monitor resource usage
- Use throttling for resource-intensive tasks
- Clean up resources after completion

### 3. Error Handling
- Implement retry logic
- Use circuit breakers
- Log errors comprehensively
- Provide fallback mechanisms

### 4. Security
- Validate all inputs
- Use least privilege principle
- Audit sensitive operations
- Encrypt inter-agent communication

## Troubleshooting

### Controller Won't Start
```bash
# Check logs
tail -f logs/master-controller.log

# Verify configuration
python main.py --validate-config

# Check port availability
netstat -an | grep 8501
```

### Agent Not Responding
```bash
# Check agent status
python main.py --status problematic-agent

# View agent logs
python main.py --logs --agent problematic-agent

# Force restart
python main.py --agent-restart problematic-agent --force
```

### High Resource Usage
```bash
# Identify resource hogs
python main.py --stats --sort-by cpu

# Throttle agent
python main.py --throttle problematic-agent --factor 0.5

# Set stricter limits
python main.py --set-limit problematic-agent --cpu 25 --memory 256MB
```

## Examples

See `examples/` directory for:
- Simple multi-agent system
- Complex workflow with dependencies
- Event-driven architecture
- Resource-constrained environment
- High-availability setup

## License

Provided as-is for development purposes.

---

**Orchestrate with confidence. 🎼**