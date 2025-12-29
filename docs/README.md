# UPLIFT Documentation

Welcome to the UPLIFT Developer Documentation repository.

## Contents

- **Quick Start Guide**: See the main [README.md](../README.md) for getting started
- **Examples**: Browse the [examples/](../examples/) directory for complete agent implementations
- **API Reference**: Coming soon
- **Architecture**: Coming soon

## Example Agents

### 1. Research Agent
Location: `examples/research-agent/`

A basic agent that performs research and stores findings in private memory.

**Key Concepts**:
- Memory scopes
- Agent identity
- Basic UPLIFT API usage

### 2. Writer Agent
Location: `examples/writer-agent/`

Receives research data from other agents and generates articles.

**Key Concepts**:
- Orchestration (receiving delegated tasks)
- Shared memory access
- Task completion reporting

### 3. Invoice Manager
Location: `examples/invoice-manager/`

A production-ready example that watches a folder, parses invoices, and delegates payments.

**Key Concepts**:
- File system permissions
- File watching
- Network permissions
- Multi-agent orchestration
- State management

## Learning Path

1. **Start Here**: Read the Quick Start Guide in the main README
2. **Build Your First Agent**: Follow the Research Agent example
3. **Learn Orchestration**: Study the Research-to-Article Pipeline
4. **Production Patterns**: Examine the Invoice Manager for real-world patterns

## Contributing

Contributions are welcome! Please submit issues or pull requests.

## License

See LICENSE file for details.
