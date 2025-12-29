import os
import time
import requests
from pathlib import Path

# The Runtime injects these secrets at launch
API_URL = os.getenv("UPLIFT_API_URL")
TOKEN = os.getenv("UPLIFT_SESSION_TOKEN")

INBOUND_FOLDER = Path.home() / "Documents" / "UPLIFT" / "Inbound"
PROCESSED_FOLDER = Path.home() / "Documents" / "UPLIFT" / "Processed"

def watch_folder():
    """Monitor the inbound folder for new invoice files."""
    print(f"Watching folder: {INBOUND_FOLDER}")
    processed_files = set()
    
    while True:
        # List all PDF files in the inbound folder
        pdf_files = list(INBOUND_FOLDER.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            if pdf_file.name not in processed_files:
                print(f"New invoice detected: {pdf_file.name}")
                process_invoice(pdf_file)
                processed_files.add(pdf_file.name)
        
        time.sleep(5)  # Check every 5 seconds

def process_invoice(invoice_path):
    """Parse the invoice and delegate payment processing."""
    print(f"Processing invoice: {invoice_path.name}")
    
    # Parse invoice data (placeholder)
    invoice_data = parse_invoice(invoice_path)
    
    # Check if already processed
    if is_already_processed(invoice_data['invoice_id']):
        print(f"Invoice {invoice_data['invoice_id']} already processed. Skipping.")
        return
    
    # Delegate to payment gateway agent
    delegate_payment(invoice_data)
    
    # Mark as processed
    mark_as_processed(invoice_data['invoice_id'])
    
    # Move to processed folder
    invoice_path.rename(PROCESSED_FOLDER / invoice_path.name)
    print(f"Invoice moved to processed folder.")

def parse_invoice(invoice_path):
    """Extract structured data from the invoice PDF."""
    # Placeholder: In production, this would use OCR/PDF parsing
    return {
        "invoice_id": "INV-2025-001",
        "vendor": "Acme Corp",
        "amount": 1250.00,
        "currency": "USD",
        "due_date": "2025-01-15"
    }

def is_already_processed(invoice_id):
    """Check if the invoice has already been processed."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        f"{API_URL}/memory/get",
        params={"scope": "uplift://agent/private", "key": f"processed_{invoice_id}"},
        headers=headers
    )
    return response.status_code == 200

def mark_as_processed(invoice_id):
    """Mark the invoice as processed in agent memory."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "scope": "uplift://agent/private",
        "key": f"processed_{invoice_id}",
        "value": {"processed_at": time.time(), "status": "completed"}
    }
    requests.post(f"{API_URL}/memory/store", json=payload, headers=headers)

def delegate_payment(invoice_data):
    """Delegate payment processing to the payment gateway agent."""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    payload = {
        "target_agent_id": "payment-gateway-agent",
        "objective": f"Process payment for invoice {invoice_data['invoice_id']}",
        "input_data": invoice_data,
        "shared_scopes": ["uplift://user/financial-prefs"],
        "priority": "high"
    }
    
    response = requests.post(f"{API_URL}/orchestrate/delegate", json=payload, headers=headers)
    print(f"Payment delegated: Task ID {response.json()['task_id']}")

if __name__ == "__main__":
    print("Invoice Manager Agent: Starting...")
    
    # Ensure folders exist
    INBOUND_FOLDER.mkdir(parents=True, exist_ok=True)
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Start watching for invoices
    watch_folder()
