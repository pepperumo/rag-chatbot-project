# Dynamous AI Agent Mastery - n8n Prototypes

This folder contains two n8n workflow prototypes that serve as the foundation for the Pydantic AI Agent implementation in `4_Pydantic_AI_Agent`. Both workflows demonstrate powerful AI agent capabilities in different deployment scenarios - local vs. cloud.

## Available Workflows

### 1. AI_Agent_Mastery_Prototype_Local.json
A fully local AI agent implementation that runs entirely on your machine, preserving privacy and giving you complete control.

### 2. AI_Agent_Mastery_Prototype_Cloud.json
A cloud-based AI agent implementation that leverages state-of-the-art LLMs and cloud services for optimal performance.

## Core Features (Both Workflows)

- **Agentic RAG**: Knowledge retrieval from vector database
- **Long-term Memory**: Persistent conversation context
- **Web Search**: Internet search capabilities
- **Code Execution**: JavaScript code generation and execution
- **Image Analysis**: Vision-capable processing

Both workflows are very well documented with notes on the side.

## Key Differences

| Feature | Local Workflow | Cloud Workflow |
|---------|---------------|---------------|
| LLM Integration | Ollama models | OpenAI/Your Provider of Choice |
| RAG Pipeline | Local files | Google Drive |
| Web Search | SearXNG | Brave API |
| Infrastructure | Self-hosted | Cloud services |

## Getting Started

1. Import the desired workflow into your n8n instance
2. Review the in-workflow documentation and Dynamous AI Agent Mastery videos for detailed setup instructions
3. Follow the setup nodes to configure your database
4. Set required credentials based on your deployment choice
5. Activate the workflow to enable the RAG pipeline

## Next Steps

These prototypes serve as the foundation for the full Python implementation in the `4_Pydantic_AI_Agent` folder, which builds on these concepts with additional capabilities and a more production-ready approach.

For detailed implementation specifics, refer to the documentation nodes within each workflow.