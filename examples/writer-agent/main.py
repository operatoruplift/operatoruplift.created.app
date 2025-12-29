import os
import requests

# The Runtime injects these secrets at launch
API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

def get_task_context():
    """Get the delegated task context from the Runtime."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{API_URL}/orchestrate/current_task", headers=headers)
    return response.json()

def query_memory(scope, query_text):
    """Query a specific memory scope for relevant data."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    query_payload = {"query": query_text, "scopes": [scope]}
    response = requests.post(f"{API_URL}/memory/query", json=query_payload, headers=headers)
    return response.json()

def generate_article(research_data):
    """Generate an article based on research data."""
    # Placeholder for actual generation logic
    # In production, this would use an LLM to synthesize the content
    article = "# Quantum Computing: A Deep Dive\n\n"
    article += "Quantum computing represents a paradigm shift in computational power...\n\n"
    article += f"Research findings: {research_data}\n"
    return article

def save_draft(content):
    """Save the generated article to the Writer's private memory."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "scope": "uplift://agent/private",
        "key": "draft_article_001",
        "value": content
    }
    requests.post(f"{API_URL}/memory/store", json=payload, headers=headers)

if __name__ == "__main__":
    print("Writer Agent: Initializing...")
    
    # Get the delegated task context
    context = get_task_context()
    print(f"Received task: {context.get('objective')}")
    
    # The Writer can now query the shared scope provided by the Researcher
    shared_scope = context['shared_scopes'][0]
    print(f"Accessing shared scope: {shared_scope}")
    
    # Query the Research Agent's data
    research_data = query_memory(shared_scope, "Latest research logs")
    print(f"Received data from {shared_scope}. Generating article...")
    
    # Generate the article
    article = generate_article(research_data)
    
    # Save the draft
    save_draft(article)
    print("Article draft saved to private memory.")
    
    # Signal completion to the Runtime
    headers = {"Authorization": f"Bearer {TOKEN}"}
    completion_payload = {
        "task_id": context['task_id'],
        "status": "success",
        "output_memory_key": "draft_article_001"
    }
    requests.post(f"{API_URL}/orchestrate/complete", json=completion_payload, headers=headers)
    print("Task completed and reported to Runtime.")
