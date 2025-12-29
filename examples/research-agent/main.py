import os
import requests

# The Runtime injects these secrets at launch
API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def write_note(title, content):
    """Store research notes in the agent's private memory scope."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "scope": "uplift://agent/private",
        "key": title,
        "value": content
    }
    requests.post(f"{API_URL}/memory/store", json=payload, headers=headers)

def delegate_to_writer():
    """Delegate article writing task to the Writer Agent."""
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
    print("Agent Started: Researching 'Quantum Computing'...")
    
    # Simulate research work
    write_note("research_log_001", "Quantum computing uses qubits...")
    write_note("research_log_002", "Key applications include cryptography and optimization...")
    write_note("research_log_003", "Major players: IBM, Google, Microsoft, IonQ...")
    
    print("Notes saved to UPLIFT memory.")
    
    # Delegate to writer for article generation
    task = delegate_to_writer()
    print(f"Writer is now working on Task ID: {task['task_id']}")
