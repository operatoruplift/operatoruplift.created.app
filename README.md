# UPLIFT Developer Quick Start
Target: V001-Lite Runtime
Goal: Create a "Research Assistant" agent that writes to a private memory scope.

## 1. Prerequisites
Ensure you have the following installed:
- Python 3.10+
- Git
- OpenAI/Anthropic API Key (for reasoning) or a local Ollama instance.

## 2. Install the UPLIFT CLI
The CLI manages your local runtime, agent sandboxes, and memory encryption.
```bash
# Install the UPLIFT CLI tool
pip install uplift-cli

# Initialize the UPLIFT environment on your machine
uplift setup
```
Note: This creates a hidden .uplift directory in your home folder to store encrypted memory volumes.

## 3. Scaffolding Your First Agent
Create a new directory for your agent and initialize the required structure.
```bash
mkdir my-researcher && cd my-researcher
uplift init --name "ResearchAgent"
```
This creates two core files:
1. agent.yaml: The manifest (permissions and identity).
2. main.py: The agent's logic.

## 4. Configure the Manifest
Open agent.yaml and define the memory scopes your agent is allowed to access. In UPLIFT, an agent cannot see any data unless it is declared here.
```yaml
# agent.yaml
identity: "researcher-v1"
capabilities: ["web-search", "summarization"]

permissions:
  memory:
    - scope: "uplift://agent/private"
      access: "read-write"
      description: "Stores my research notes."
    - scope: "uplift://user/interests"
      access: "read-only"
      description: "Allows me to tailor research to your hobbies."
```

## 5. Write the Agent Logic
Open main.py. UPLIFT agents use a simple HTTP gateway to talk to the host Runtime.
```python
import os
import requests

# The Runtime injects these secrets at launch
API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def write_note(title, content):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "scope": "uplift://agent/private",
        "key": title,
        "value": content
    }
    requests.post(f"{API_URL}/memory/store", json=payload, headers=headers)

if __name__ == "__main__":
    print("Agent Started: Researching 'Quantum Computing'...")
    # Simulate work
    write_note("research_log_001", "Quantum computing uses qubits...")
    print("Note saved to UPLIFT memory.")
```

## 6. Launch the Session
Run your agent through the UPLIFT Runtime. This ensures the sandbox is enforced and permissions are checked.
```bash
uplift run main.py --env OPENAI_API_KEY=your_key_here
```
What just happened?
1. Sandbox: UPLIFT spun up a temporary container/process for your script.
2. Enforcement: When main.py called /memory/store, the Runtime checked agent.yaml to ensure the agent was allowed to write to uplift://agent/private.
3. Persistence: Your note is now stored in an encrypted local volume, ready for your next session or another agent to access (if permitted).

## 7. Inspecting Memory
You can verify the data was stored using the CLI:
```bash
uplift memory query "What did the agent find about Quantum?"
```

## Troubleshooting & Tips
- Permission Denied: If your agent tries to access a scope not in agent.yaml, the Runtime will return a 403 Forbidden.
- Logs: View real-time agent behavior with uplift logs --follow.
- Ollama Integration: To use a local model instead of a cloud API, set UPLIFT_MODEL_PROVIDER=ollama in your config.

# The Orchestration API
The Orchestration API defines how multiple agents collaborate within the UPLIFT Runtime. Unlike traditional sequential workflows, UPLIFT orchestration is goal-driven, allowing agents to pass tasks and memory context to one another via the Runtime's mediation.

## 1. Orchestration Philosophy
Agents do not talk to each other directly. Instead, they "publish" tasks or "request" assistance through the Orchestration Gateway.
- Delegation: Agent A requests Agent B to perform a sub-task.
- Context Passing: Agent A provides Agent B with access to a specific Memory Scope.
- Mediation: The Runtime verifies that Agent A has permission to call Agent B and that Agent B has permission to access the passed context.

## 2. API Endpoints
POST /orchestrate/delegate
Used when an agent needs another agent to handle a specific objective.
- Body:
```json
{
  "target_agent_id": "translator-agent-01",
  "objective": "Translate the following research summary into Spanish.",
  "input_data": "...", 
  "shared_scopes": ["uplift://shared/project-nexus-summary"],
  "priority": "normal",
  "callback_url": "http://localhost:8848/v1/agent/callback"
}
```
- Runtime Action: The runtime pauses Agent A (if necessary), initializes a new session for Agent B, and injects the shared_scopes into Agent B's authorized memory.

GET /orchestrate/directory
Allows an agent to see which other agents are installed and what their "Capabilities" are.
- Response:
```json
{
  "available_agents": [
    {
      "id": "pdf-parser-v2",
      "capabilities": ["text-extraction", "ocr", "metadata-parsing"],
      "status": "idle"
    },
    {
      "id": "email-sender-v1",
      "capabilities": ["smtp-relay", "drafting"],
      "status": "ready"
    }
  ]
}
```

POST /orchestrate/complete
Used by the "Target Agent" to return results to the "Source Agent."
- Body:
```json
{
  "task_id": "task_9921",
  "status": "success",
  "output_data": "...",
  "output_memory_key": "translated_summary_v1"
}
```

## 3. The Orchestration Manifest
Agents must declare which types of agents they intend to collaborate with in their agent.yaml.
```yaml
# agent.yaml (Updated with Orchestration)
identity: "chief-editor-agent"
permissions:
  orchestration:
    - target_agent_type: "translation"
      description: "Required to localize content."
    - target_agent_id: "fact-checker-pro"
      description: "Mandatory verification step for all articles."
```

## 4. Execution Flow (The "Relay" Model)
1. Request: Agent A calls delegate with a specific memory scope URI.
2. Verification: The Runtime checks if Agent A owns or has read access to that scope.
3. Grant: The Runtime temporarily grants Agent B access to that scope for the duration of the delegated task.
4. Execution: Agent B processes the data in the shared scope.
5. Return: Agent B signals completion; the Runtime revokes Agent B's access and wakes Agent A.

## 5. Security & Safety
- Circular Dependency Protection: The Runtime monitors the "Delegation Chain." If Agent A calls B, who calls C, who calls A, the Runtime kills the session to prevent infinite loops.
- Scope Isolation: Agent B can only see the specific scopes explicitly passed by Agent A. It cannot "drift" into Agent A's private memory.
- TTL (Time To Live): Delegated tasks have a mandatory timeout (default: 300s) to prevent a single agent from hanging the orchestration pipeline.

## Implementation Example (Python)
```python
import os
import requests

GATEWAY = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def delegate_translation(text, target_lang):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "target_agent_id": "google-translate-mcp",
        "objective": f"Translate to {target_lang}",
        "input_data": text,
        "shared_scopes": ["uplift://agent/private"] # Granting temporary access to private scratchpad
    }
    
    response = requests.post(f"{GATEWAY}/orchestrate/delegate", json=payload, headers=headers)
    return response.json()["task_id"]

# Usage
task_id = delegate_translation("Hello World", "Spanish")
print(f"Delegated task {task_id} is running...")
```

# UPLIFT Documentation (Lite)
Version: V001-Lite
Core Thesis: A local-first, agent-native operating system for the secure orchestration of AI agents.

## 1. Overview
### What is UPLIFT?
UPLIFT is an infrastructure layer designed to run and govern AI agents on your own device. Rather than treating AI as a series of isolated prompts or cloud workflows, UPLIFT introduces an execution layer where agents are first-class entities. Agents run in isolated sandboxes, share context through a controlled memory system, and are coordinated by a local runtime.

### The Problem
- Fragmentation: AI tools are scattered across tabs and apps, losing context between sessions.
- Cloud-Dependency: Sensitive data is routinely sent to external servers with zero visibility or control.
- Governance Gap: There is no unified layer to manage agent permissions, data access, or auditability.

### The Solution: Agent-Native Execution
UPLIFT provides a local runtime that:
- Executes agents in isolated sandboxes.
- Grants access to shared memory only when explicitly allowed.
- Orchestrates multi-agent workflows over time.
- Maintains privacy and sovereignty by keeping data on-device.

## 2. Core Concepts
- Agent: A long-lived software entity (application) capable of reasoning and taking action.
- Runtime: The local control plane responsible for starting agents and enforcing security boundaries.
- Memory: Structured, persistent context shared across agents and sessions.
- Permissions: Explicit, time-limited authorizations for memory, files, network, and device access.
- Orchestration: Adaptive coordination of multiple agents toward a shared goal.
- Local-First: All core execution and storage occur on the user's device by default.
- MCP Compatibility: Uses the Model Context Protocol for interoperability with external tools.

## 3. How UPLIFT Works
### Execution Lifecycle
1. Installation: Agents are added from the marketplace or local sources; identities are verified.
2. Permissioning: No agent has access by default. Users must explicitly grant scoped access (e.g., "Read-only access to Project Folder A").
3. Session-Based Operation: Agents run inside bounded sessions. Permissions and context are active only during the session.
4. Memory Interaction: Agents read/write to specific Memory Scopes. This knowledge persists across sessions to build long-term context.
5. Orchestration: The system assigns tasks to agents and passes context through shared memory to achieve complex outcomes.

## 4. Mental Model: "Think OS, Not App"
UPLIFT is not a chatbot; it is the operating system for AI.
- Your Device: The hardware.
- UPLIFT: The OS (Kernel/Runtime).
- Agents: The applications (Programs).
- Memory: The file system (Infrastructure).
- Permissions: System privileges.

## 5. Architecture
### Platform Structure
UPLIFT uses a decentralized, local-first architecture:
- Core Runtime: The single enforcement point through which all agent actions must flow.
- Isolation Layer: Sandboxes that prevent agents from interfering with each other or the host system.
- Memory Layer: A persistent context system partitioned by "Scopes" to prevent data leakage.
- Cloud Extensions (Optional): Opt-in, encrypted services for cross-device sync and backups.

### The Memory System
Memory in UPLIFT is Infrastructure, not a side effect.
- Short-Term: Session-bound context (discarded after use).
- Long-Term: Facts, preferences, and outcomes that survive session resets.
- Shared: Scopes that allow multiple agents to collaborate on the same data set.

## 6. Agent Model
Agents in UPLIFT are treated as installable software.
- Capabilities: Agents must declare their required capabilities (e.g., "Network Access," "File Write") upfront.
- Identity: All agents are digitally signed to verify authenticity.
- Permissions: Access is never implicit. The runtime intercepts every request to ensure it matches user-granted permissions. If an agent tries to access a memory scope it isn't authorized for, the runtime terminates the request.

## 7. Marketplace & Tokenomics (Lite Summary)
- Marketplace: A discovery layer for agents with clear versioning and safety manifests.
- $UPLIFT Token: Used for marketplace transactions, accessing decentralized compute resources, and premium agent services. (Not required for basic local-first operation).

## 8. Enterprise & Security
- Governance: Provides a full audit trail of agent decisions and data access.
- Privacy: Zero-trust architecture ensures sensitive enterprise data never leaves the local environment unless explicitly routed.
- Resilience: Agents can operate offline and resume tasks once connectivity is restored.

# Multi-Agent Scenario: The Research-to-Article Pipeline
## 1. Configure the Writer Agent
First, we create a second agent directory. The Writer Agent needs to declare that it is open to receiving orchestration requests.
```yaml
# writer-agent/agent.yaml
identity: "writer-agent-v1"
capabilities: ["content-generation"]

permissions:
  memory:
    - scope: "uplift://agent/private"
      access: "read-write"
      description: "Stores drafts."
  orchestration:
    allow_incoming: true # Allows other agents to delegate to this one
```

## 2. Update the Research Agent (The "Sender")
The Research Agent needs permission to call the Writer and share its specific memory scope.
```yaml
# researcher-agent/agent.yaml (Updated)
identity: "researcher-v1"
permissions:
  memory:
    - scope: "uplift://agent/private"
      access: "read-write"
  orchestration:
    - target_agent_id: "writer-agent-v1"
      description: "Required to turn research notes into articles."
```

## 3. Implementing the Handoff (The Code)
### Research Agent Logic
The Research Agent performs its work, then calls the orchestrate/delegate endpoint.
```python
# researcher-agent/main.py
import os, requests

API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def delegate_to_writer():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    payload = {
        "target_agent_id": "writer-agent-v1",
        "objective": "Summarize my research logs into a 3-paragraph blog post.",
        # KEY STEP: Share the Researcher's private scope so the Writer can read the notes
        "shared_scopes": ["uplift://agent/private"], 
        "priority": "high"
    }
    
    print("Delegating task to Writer Agent...")
    response = requests.post(f"{API_URL}/orchestrate/delegate", json=payload, headers=headers)
    return response.json()

if __name__ == "__main__":
    # ... research logic ...
    task = delegate_to_writer()
    print(f"Writer is now working on Task ID: {task['task_id']}")
```

### Writer Agent Logic
The Writer Agent receives the objective and the temporary access to the Research Agent's memory.
```python
# writer-agent/main.py
import os, requests

API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def get_task_context():
    # The Runtime provides the delegated context via this endpoint
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{API_URL}/orchestrate/current_task", headers=headers)
    return response.json()

if __name__ == "__main__":
    context = get_task_context()
    # The Writer can now query the shared scope provided by the Researcher
    shared_scope = context['shared_scopes'][0] 
    
    # Query the Research Agent's data
    query_payload = {"query": "Latest research logs", "scopes": [shared_scope]}
    research_data = requests.post(f"{API_URL}/memory/query", json=query_payload, headers=headers).json()
    
    print(f"Received data from {shared_scope}. Generating article...")
    # ... generation logic ...
```

## 4. Why this is "Agent-Native"
In a traditional cloud-based system, you would have to copy and paste the text from one API to another. In UPLIFT:
1. Zero-Copy: The data stays in the Research Agent's memory scope.
2. Least Privilege: The Writer Agent only sees the specific scope shared for that specific task.
3. Automatic Revocation: Once the Writer Agent signals completion, the Runtime automatically strips the Writer's access to the Research Agent's scope.
4. Local Execution: This entire handoff happens via local inter-process communication (IPC), meaning the data never touches the internet.

## 5. Running the Pipeline
You can trigger the entire flow from the CLI:
```bash
# Start the UPLIFT Runtime Orchestrator
uplift start

# Run the researcher, which will automatically trigger the writer
uplift run researcher-agent/main.py
```

# Custom Project Template: "The File-to-Action Manager"
This template covers a common high-utility use case: an agent that monitors a Local File Directory, uses Cross-Agent Orchestration, and accesses External APIs.

This agent is designed to watch a folder (like ~/Documents/Invoices), parse the data, and delegate the payment or logging to another agent.

```yaml
# agent.yaml
identity: "invoice-manager-v1"
version: "0.1.0"
description: "Monitors local invoices and orchestrates payment workflows."

# 1. Resource Capabilities
# These define what low-level OS features the agent can use.
capabilities:
  - web-search      # For looking up company tax IDs
  - file-watcher    # To trigger actions when a new file is added
  - pdf-parsing     # To read invoice data

# 2. Permissions: Memory
# Defining where the agent stores its state and what it can read.
permissions:
  memory:
    - scope: "uplift://agent/private"
      access: "read-write"
      description: "Required to track which invoices have already been processed."
    
    - scope: "uplift://user/financial-prefs"
      access: "read-only"
      description: "Used to determine payment limits and preferred accounts."

# 3. Permissions: Filesystem
# Local-first agents need explicit paths to interact with your files.
  files:
    - path: "~/Documents/UPLIFT/Inbound"
      access: "read"
      description: "Target folder for new invoice PDFs."
      
    - path: "~/Documents/UPLIFT/Processed"
      access: "write"
      description: "Folder to move completed invoices to."

# 4. Permissions: Orchestration
# Defining which 'Sub-Agents' this manager is allowed to call.
  orchestration:
    - target_agent_id: "payment-gateway-agent"
      description: "Used to execute the actual payment transaction."
      
    - target_agent_type: "reporting"
      description: "Used to log the transaction in the global expense sheet."

# 5. Network Access
# UPLIFT blocks all traffic by default. You must whitelist specific domains.
  network:
    - domain: "api.stripe.com"
      description: "Required to verify payment status."
    - domain: "open.er-api.com"
      description: "Required for real-time currency conversion."
```