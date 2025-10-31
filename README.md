# NexusForge 3.0 – Live Agent Swarm System

Forge Fractal Agents that integrate multiple AI frameworks into a single, powerful system.

## Overview

NexusForge 3.0 is a live, single-file, real-world agent swarm that fuses multiple AI frameworks:

- **FractalAgentForge** - Hierarchical agent spawning
- **Auto-GPT** - Autonomous agent capabilities
- **BabyAGI** - Self-building and task management
- **SuperAGI** - Advanced orchestration
- **JARVIS** - Hugging Face integration
- **LangChain** - Tool and LLM abstraction
- **AutoGen** - Multi-agent debate via sockets
- **CrewAI** - Team-based coordination
- **LangGraph** - Workflow state management
- **LlamaIndex** - Vector storage and knowledge base
- **Semantic Kernel** - Advanced reasoning

All with **real API calls, real file writes, real subprocesses, and real sockets**. No mocks. No simulations.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MASSIVEMAGNETICS/NexusForge-2.0-.git
cd NexusForge-2.0-
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required API keys:
- `GROQ_API_KEY` (preferred) or `OPENAI_API_KEY` - Get from [Groq Console](https://console.groq.com/) or [OpenAI](https://platform.openai.com/)
- `HUGGINGFACEHUB_API_TOKEN` - Get from [Hugging Face](https://huggingface.co/settings/tokens)

## Usage

Run the agent swarm:
```bash
python nexusforge.py
```

The system will:
1. Spawn fractal agents hierarchically
2. Execute CrewAI team tasks (research + coding)
3. Run LangGraph workflows
4. Perform AutoGen-style debates via sockets
5. Query the LlamaIndex knowledge base
6. Execute Hugging Face inference
7. Self-build new functions (BabyAGI style)

## Output

Generated files will be placed in:
- `./runtime/` - Self-built Python code
- `./runtime_out/` - Agent outputs
- `./output/` - Agent-specific files
- `./persist/` - LlamaIndex vector storage

## Features

✅ **Real API Integration** - Live calls to Groq/OpenAI, Hugging Face  
✅ **Real File Operations** - Actual disk writes and reads  
✅ **Real Socket Communication** - TCP sockets for agent debates  
✅ **Multi-threaded Execution** - Concurrent agent operations  
✅ **Fractal Architecture** - Agents spawn child agents recursively  
✅ **Web Search** - DuckDuckGo API integration  
✅ **Code Generation** - LLM-powered Python code creation  
✅ **Knowledge Base** - Vector storage with LlamaIndex  

## Architecture

### Fractal Agent Forge
The core spawner creates hierarchical agent structures:
```python
root = FractalAgent("Orchestrator", "Turn trends into code")
researcher = root.spawn("Researcher", "Find trends")
coder = root.spawn("Coder", "Generate code")
```

### Tool System
Integrated tools via LangChain:
- `search_web()` - DuckDuckGo search
- `write_file()` - File operations
- `read_file()` - File reading
- `generate_code()` - LLM code generation
- `hf_inference()` - Hugging Face models

### Agent Teams
CrewAI coordination with specialized agents:
- **Trend Researcher** - Finds emerging AI trends
- **Code Generator** - Writes production Python

### Workflow Engine
LangGraph state management for multi-step processes

### Knowledge Base
LlamaIndex for document storage and semantic search

## Contributing

Contributions welcome! This is a living system designed to evolve.

## License

MIT License - See LICENSE file for details
