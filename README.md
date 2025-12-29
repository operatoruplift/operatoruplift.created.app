# Operator Uplift - Complete Platform

> **Repository Consolidation Notice (Dec 29, 2025)**  
> This repository now contains the complete Operator Uplift platform, consolidating both the UPLIFT Runtime documentation/examples and the web application code from the former `operatoruplift-created-app` repository. All advanced examples and documentation added today have been preserved.

## Overview

**Operator Uplift** is a revolutionary local-first AI agent platform that combines:
- 🏗️ **UPLIFT Runtime** - An agent-native operating system for secure orchestration of AI agents
- 🤖 **Gemini 3 Pro Integration** - Powered by Google's advanced AI model
- 🌐 **Modern Web Interface** - Built with Next.js/React for seamless user experience
- 🔒 **Privacy-First Architecture** - Your data stays on your device
- 🔧 **Extensible Agent System** - Build and deploy custom AI agents

### What is UPLIFT?

UPLIFT is an infrastructure layer designed to run and govern AI agents on your own device. Rather than treating AI as a series of isolated prompts or cloud workflows, UPLIFT introduces an execution layer where agents are first-class entities. Agents run in isolated sandboxes, share context through a controlled memory system, and are coordinated by a local runtime.

## Key Features

### Runtime & Core Platform
- ✅ **Agent-Native Execution** - Isolated sandboxes for each agent
- ✅ **Secure Memory System** - Scoped, encrypted persistent context
- ✅ **Multi-Agent Orchestration** - Coordinate complex workflows
- ✅ **Permission-Based Security** - Zero-trust architecture with explicit grants
- ✅ **MCP Compatibility** - Uses Model Context Protocol for interoperability
- ✅ **Local-First by Default** - All execution and storage on-device

### Web Application
- 🌐 **Modern Web UI** - Built with Next.js 14 and React 18
- ⚡ **High Performance** - Optimized for speed and efficiency
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Clean Interface** - Modern, intuitive user experience
- 🔌 **API Integration** - RESTful API for programmatic access

## Repository Structure

```
operatoruplift.created.app/
├── advanced-examples/       # Advanced UPLIFT agent implementations
│   ├── approval-system/     # Multi-stage approval workflows
│   ├── code-auditor/        # Code analysis agent
│   ├── health-monitor/      # System health monitoring
│   ├── master-controller/   # Central orchestration agent
│   ├── news-scout/          # News aggregation agent
│   └── system-management/   # System administration agent
├── docs/                    # Comprehensive documentation
│   ├── company-overview/    # Company background and leadership
│   ├── product-specs/       # Product specifications
│   ├── roadmap/             # 12-month development roadmap
│   ├── technical-architecture/  # System architecture
│   ├── tokenomics/          # Token economics documentation
│   ├── API.md               # API reference
│   └── DEPLOYMENT.md        # Deployment guide
├── examples/                # Basic agent examples
│   ├── invoice-manager/     # Invoice processing agent
│   ├── research-agent/      # Research assistant
│   └── writer-agent/        # Content generation agent
├── public/                  # Web application static assets
├── src/                     # Web application source code
├── styles/                  # CSS styling
├── package.json             # Node.js dependencies
├── .env.example             # Environment configuration template
├── CONTRIBUTING.md          # Contribution guidelines
├── VIDEO-DEMO.md            # Video demonstrations
└── README.md                # This file
```

## Quick Start

### Prerequisites
- **Python 3.10+** (for UPLIFT Runtime)
- **Node.js v18+** (for web application)
- **Git**
- OpenAI/Anthropic API Key or local Ollama instance

### 1. Install the UPLIFT Runtime

```bash
# Install the UPLIFT CLI tool
pip install uplift-cli

# Initialize the UPLIFT environment
uplift setup
```

### 2. Set Up the Web Application

```bash
# Clone the repository
git clone https://github.com/operatoruplift/operatoruplift.created.app.git
cd operatoruplift.created.app

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start development server
npm run dev
```

### 3. Create Your First Agent

```bash
# Create agent directory
mkdir my-researcher && cd my-researcher

# Initialize agent structure
uplift init --name "ResearchAgent"

# Run your agent
uplift run main.py --env OPENAI_API_KEY=your_key_here
```

## Core Concepts

### Agent Model
Agents in UPLIFT are treated as installable software with:
- **Capabilities** - Declared required features (e.g., "Network Access," "File Write")
- **Identity** - Digitally signed for authenticity
- **Permissions** - Explicit, never implicit access control

### Memory System
- **Short-Term** - Session-bound context (discarded after use)
- **Long-Term** - Persistent facts, preferences, and outcomes
- **Shared** - Scopes for multi-agent collaboration
- **Encrypted** - All memory stored with encryption

### Orchestration
- **Delegation Model** - Agents request assistance through the Runtime
- **Context Passing** - Temporary scope access for specific tasks
- **Mediation** - Runtime verifies all permissions
- **Automatic Revocation** - Access removed upon task completion

## Documentation

### Getting Started
- [UPLIFT Developer Quick Start](#1-prerequisites) - Build your first agent
- [Multi-Agent Orchestration](docs/README.md) - Coordinate multiple agents
- [API Documentation](docs/API.md) - REST API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

### Advanced Topics
- [Advanced Examples](advanced-examples/README.md) - Complex agent implementations
- [Technical Architecture](docs/technical-architecture/) - System design
- [Company Overview](docs/company-overview/) - Background and leadership
- [Product Specifications](docs/product-specs/) - Detailed features
- [Tokenomics](docs/tokenomics/) - Token economics
- [12-Month Roadmap](docs/roadmap/) - Development timeline

### Video Demonstrations
- [Feature Demonstrations](VIDEO-DEMO.md) - Video walkthroughs

## Example Use Cases

### Basic Agents
1. **Research Assistant** - Gathers information and stores findings
2. **Content Writer** - Generates articles from research notes
3. **Invoice Manager** - Processes invoices and triggers payments

### Advanced Implementations
1. **Multi-Stage Approval System** - Complex workflow orchestration
2. **Code Auditor** - Automated code review and security scanning
3. **Health Monitor** - System diagnostics and alerting
4. **Master Controller** - Central coordination of agent swarms
5. **News Scout** - Aggregates and summarizes news from multiple sources
6. **System Management** - Administrative task automation

## Development

### Web Application

```bash
# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

### UPLIFT Runtime

```bash
# View agent logs
uplift logs --follow

# Query memory
uplift memory query "What did the agent find?"

# List installed agents
uplift agents list
```

## Deployment Options

### Option 1: Vercel (Web UI)
```bash
npm i -g vercel
vercel
```

### Option 2: Self-Hosted
```bash
npm run build
npm start
```

### Option 3: Docker
```bash
docker build -t operatoruplift .
docker run -p 3000:3000 -e GEMINI_API_KEY=your_key operatoruplift
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## Security & Privacy

- **Zero-Trust Architecture** - All access must be explicitly granted
- **Local-First** - Data stays on your device by default
- **Encrypted Memory** - All persistent storage is encrypted
- **Audit Trail** - Full logging of agent decisions and data access
- **Sandbox Isolation** - Agents cannot interfere with each other

## Enterprise Features

- **Governance** - Complete audit trail and compliance reporting
- **Privacy** - Sensitive data never leaves local environment
- **Resilience** - Offline operation with resumption on reconnect
- **Scalability** - Support for large agent deployments

## Marketplace & Tokenomics

- **Agent Marketplace** - Discover and install community agents
- **$UPLIFT Token** - Used for marketplace transactions and premium services
- **Versioning** - Clear agent versioning and safety manifests
- **Digital Signatures** - Verified agent authenticity

## Technology Stack

### Runtime
- Python 3.10+
- Encrypted storage (local-first)
- Model Context Protocol (MCP)
- Sandbox isolation

### Web Application
- Next.js 14
- React 18
- Node.js
- Tailwind CSS / Modern CSS3

## Support

- 📧 **Email**: support@operatoruplift.created.app
- 💬 **Community**: [GitHub Discussions](https://github.com/operatoruplift/operatoruplift.created.app/discussions)
- 🐛 **Issues**: [Issue Tracker](https://github.com/operatoruplift/operatoruplift.created.app/issues)
- 📖 **Documentation**: See [docs/](docs/) directory

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ by the Operator Uplift team
- Powered by Gemini 3 Pro
- Inspired by the Model Context Protocol
- Community-driven development

---

## Mental Model: "Think OS, Not App"

UPLIFT is not a chatbot; it is the **operating system for AI**.

- **Your Device** → The hardware
- **UPLIFT** → The OS (Kernel/Runtime)
- **Agents** → The applications (Programs)
- **Memory** → The file system (Infrastructure)
- **Permissions** → System privileges

---

## Troubleshooting

### Common Issues

**Permission Denied**
- Check your `agent.yaml` - ensure the scope is declared
- Verify the Runtime is granting the correct permissions

**Agent Won't Start**
- Ensure Python 3.10+ is installed
- Verify API keys are set correctly
- Check logs: `uplift logs --follow`

**Web UI Not Loading**
- Ensure Node.js v18+ is installed
- Check `.env` configuration
- Verify port 3000 is available

---

**Operator Uplift** - Building the future of local-first AI agent orchestration

Repository: https://github.com/operatoruplift/operatoruplift.created.app  
Website: https://operatoruplift.created.app
