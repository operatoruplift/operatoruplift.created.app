# Invoice Manager Agent

This example demonstrates a file-watching agent that monitors a local directory for invoice PDFs, parses them, and delegates payment processing to another agent.

## Features

- **File Watching**: Monitors `~/Documents/UPLIFT/Inbound` for new PDF files
- **Invoice Parsing**: Extracts structured data from invoices
- **Orchestration**: Delegates payment processing to a specialized payment agent
- **State Management**: Tracks processed invoices to prevent duplicates
- **Security**: Uses scoped permissions for file access and network requests

## Setup

1. Create the required directories:
```bash
mkdir -p ~/Documents/UPLIFT/Inbound
mkdir -p ~/Documents/UPLIFT/Processed
```

2. Install the agent:
```bash
cd examples/invoice-manager
uplift install .
```

3. Run the agent:
```bash
uplift run main.py
```

## Testing

Drop a sample invoice PDF into `~/Documents/UPLIFT/Inbound` and watch the agent process it automatically.

## Permissions

This agent demonstrates all major permission types:
- **Memory**: Tracks processed invoices
- **Files**: Reads from Inbound, writes to Processed
- **Network**: Contacts Stripe API and currency conversion service
- **Orchestration**: Delegates to payment-gateway-agent
