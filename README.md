# 🚀 NexusForge 2.0

**AGI-lite Autonomous Agent Framework - Now Enhanced with Intelligence & Performance Tracking**

NexusForge 2.0 fuses FractalAgentForge's recursive templates with Auto-GPT's goal-breaking, BabyAGI's self-building functions, SuperAGI's production GUI, JARVIS's multi-modal experts, AutoGen's agent chats, and CrewAI's role crews. Bootstrap from a goal: spawn fractal hierarchies that converse, delegate, and evolve via dashboards and triggers—no deps, Docker-ready.

From R&D swarms to viral apps, it's AGI-lite autonomy in ~600MB. Open-source the uprising!

## ✨ Features

### Core Features
- **🌳 Fractal Agent Hierarchies**: Recursive agent spawning with depth control (FractalAgentForge-inspired)
- **🎯 Enhanced Goal Decomposition**: Automatic task breaking with complexity analysis and dependency tracking (Auto-GPT-style)
- **🔧 Self-Building Functions**: Agents dynamically register new capabilities (BabyAGI-inspired)
- **💬 Priority-Based Communication**: Multi-agent communication with intelligent message queuing (AutoGen-style)
- **👥 Advanced Crew Workflows**: Organize agents with 5 workflow patterns (SEQUENTIAL, PARALLEL, PIPELINE, MAP_REDUCE, HIERARCHICAL)
- **🎓 Self-Improving Experts**: Multi-modal experts that learn from experience and track performance (JARVIS-inspired)
- **🖥️ Production Dashboard**: Real-time monitoring and control GUI (SuperAGI-style)
- **🐳 Docker Ready**: Containerized deployment with minimal dependencies
- **⚡ Bootstrap from Goals**: Start with a high-level objective, let agents handle the rest

### 🆕 Recent Enhancements
- **📊 Performance Tracking**: Agents and experts track success rates, execution times, and self-optimize
- **🧠 Complexity Analysis**: Smart goal decomposition based on complexity scoring
- **🚦 Priority Queuing**: Messages delivered by priority with dependency resolution
- **📈 Advanced Analytics**: Top performer tracking and comprehensive system statistics
- **🔄 Workflow Patterns**: Five sophisticated crew coordination patterns

See [ENHANCEMENTS.md](docs/ENHANCEMENTS.md) for detailed documentation.

## 🏗️ Architecture

```
NexusForge
├── Core
│   ├── Fractal Agent System (recursive spawning)
│   └── Main Orchestrator (unified API)
├── Communication Hub
│   ├── Agent-to-Agent Messaging
│   ├── Task Delegation
│   └── Conversation History
├── Agent Systems
│   ├── Crew Manager (role-based teams)
│   └── Expert System (multi-modal specialists)
└── GUI/CLI
    ├── Web Dashboard (monitoring & control)
    └── Command Line Interface
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/MASSIVEMAGNETICS/NexusForge-2.0-.git
cd NexusForge-2.0-

# Install dependencies
pip install -r requirements.txt
```

### Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the dashboard at http://localhost:8080
```

### Bootstrap from a Goal

```bash
# Start with a high-level goal
python -m nexusforge bootstrap "Build a web scraper for news articles"

# With GUI dashboard
python -m nexusforge bootstrap "Research AI trends and create a report" --with-gui
```

### Start the Dashboard

```bash
python -m nexusforge gui
# Open http://localhost:8080
```

## 📚 Usage Examples

### Basic Usage

```python
import asyncio
from nexusforge import NexusForge

async def main():
    # Initialize NexusForge
    nexus = NexusForge()
    await nexus.start()
    
    # Bootstrap from a goal
    goal = "Research AI developments and create a presentation"
    root_agent_id = await nexus.bootstrap_from_goal(goal)
    
    # View the agent hierarchy
    hierarchy = nexus.get_agent_hierarchy(root_agent_id)
    print(f"Created {len(hierarchy['children'])} child agents")
    
    # Get system statistics
    stats = nexus.get_statistics()
    print(f"Total agents: {stats['agent_stats']['total']}")
    
    await nexus.stop()

asyncio.run(main())
```

### Creating a Specialized Crew

```python
from nexusforge import NexusForge
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.agents.crew import CrewRole

async def create_dev_team():
    nexus = NexusForge()
    await nexus.start()
    
    # Create specialized agents
    agents = [
        nexus.create_agent_from_template(AgentTemplate(
            name="TechLead",
            role="Leader",
            capabilities=["plan", "coordinate", "review"],
            goal_template="Lead development"
        )),
        nexus.create_agent_from_template(AgentTemplate(
            name="Developer",
            role="Builder",
            capabilities=["code", "test", "debug"],
            goal_template="Write code"
        ))
    ]
    
    # Create a crew
    crew_id = nexus.create_crew(
        name="DevTeam",
        agent_ids=[a.agent_id for a in agents],
        roles=[CrewRole.LEADER, CrewRole.BUILDER],
        goals=["Build a REST API"]
    )
    
    return crew_id
```

## 🎯 CLI Commands

```bash
# Bootstrap from goal
nexusforge bootstrap "Your goal here"

# Start GUI dashboard
nexusforge gui

# Show system status
nexusforge status

# List components
nexusforge list agents
nexusforge list crews
nexusforge list experts
nexusforge list messages

# View agent hierarchy
nexusforge hierarchy

# Show detailed statistics
nexusforge stats
```

## 🔧 Configuration

Create a `.env` file (see `.env.example`):

```bash
NEXUSFORGE_ENV=production
NEXUSFORGE_LOG_LEVEL=INFO
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
MAX_AGENT_DEPTH=5
SPAWN_THRESHOLD=0.7
```

## 📊 Dashboard Features

The web dashboard provides:

- **Real-time System Status**: Monitor agents, crews, and experts
- **Agent Hierarchy Visualization**: See the fractal structure
- **Message History**: Track agent communications
- **Bootstrap Interface**: Start new agent systems from goals
- **Statistics Dashboard**: Detailed system metrics

## 🏛️ System Components

### Fractal Agents
- Recursive spawning up to configurable depth
- Automatic goal decomposition
- Parent-child communication
- Dynamic capability registration

### Communication Hub
- Message passing between agents
- Task delegation system
- Broadcast capabilities
- Conversation tracking

### Crew Manager
- Role-based team organization
- Leader assignment
- Crew-wide broadcasting
- Goal tracking

### Expert System
- Multi-modal specialization (text, code, data, etc.)
- Automatic expert selection
- Capability-based routing
- Pluggable expert functions

## 🧪 Examples

See the `examples/` directory for:
- `basic_usage.py`: Simple bootstrapping example
- `crew_example.py`: Creating and managing crews
- More examples coming soon!

## 🐳 Docker Deployment

The system is optimized for containerized deployment:

```bash
# Build the image
docker build -t nexusforge .

# Run with custom configuration
docker run -p 8080:8080 -p 5000:5000 \
  -e NEXUSFORGE_ENV=production \
  -v $(pwd)/data:/app/data \
  nexusforge
```

Target size: ~600MB

## 🔬 Development

```bash
# Install in development mode
pip install -e .

# Run tests (when available)
pytest

# Run linting (when available)
flake8 nexusforge/
```

## 🎨 Use Cases

- **R&D Swarms**: Autonomous research teams
- **Application Development**: Self-organizing dev teams
- **Data Processing Pipelines**: Adaptive data workflows
- **Content Generation**: Multi-agent content creation
- **Task Automation**: Complex workflow automation
- **Experimental AGI**: Research platform for autonomous systems

## 🚧 Roadmap

- [ ] LLM integration for enhanced reasoning
- [ ] Persistent storage for agent state
- [ ] Advanced visualization tools
- [ ] Plugin system for custom experts
- [ ] Distributed agent deployment
- [ ] Enhanced security features
- [ ] Performance optimization
- [ ] Extended test coverage

## 📖 Documentation

- [Architecture Overview](docs/architecture.md)
- [Agent System](docs/agents.md)
- [Communication System](docs/communication.md)
- [Crew Management](docs/crews.md)
- [Expert System](docs/experts.md)
- [API Reference](docs/api.md)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Inspired by:
- FractalAgentForge (recursive templates)
- Auto-GPT (goal breaking)
- BabyAGI (self-building functions)
- SuperAGI (production GUI)
- JARVIS (multi-modal experts)
- AutoGen (agent conversations)
- CrewAI (role-based crews)

## 📞 Contact

For questions, issues, or contributions, please open an issue on GitHub.

---

**Open-source the uprising! 🚀**
