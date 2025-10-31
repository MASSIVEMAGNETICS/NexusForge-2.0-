# Quick Start Guide

## Installation

### Prerequisites

- Python 3.11+
- pip
- Docker (optional, for containerized deployment)

### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/MASSIVEMAGNETICS/NexusForge-2.0-.git
cd NexusForge-2.0-

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Docker

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build manually
docker build -t nexusforge .
docker run -p 8080:8080 -p 5000:5000 nexusforge
```

## First Steps

### 1. Bootstrap from a Goal

The quickest way to start is by bootstrapping the system from a high-level goal:

```bash
python -m nexusforge bootstrap "Build a REST API for user management"
```

This will:
1. Create a root agent
2. Decompose the goal into subtasks
3. Spawn child agents for each subtask
4. Display the agent hierarchy

### 2. Start the Dashboard

Launch the web-based dashboard to monitor the system:

```bash
python -m nexusforge gui
```

Then open your browser to `http://localhost:8080`

### 3. Check System Status

```bash
python -m nexusforge status
```

## Basic Usage

### Using the CLI

```bash
# Bootstrap with GUI
python -m nexusforge bootstrap "Your goal here" --with-gui

# List all agents
python -m nexusforge list agents

# View agent hierarchy
python -m nexusforge hierarchy

# Get detailed statistics
python -m nexusforge stats
```

### Using Python API

```python
import asyncio
from nexusforge import NexusForge

async def main():
    # Initialize
    nexus = NexusForge()
    await nexus.start()
    
    # Bootstrap from goal
    root_id = await nexus.bootstrap_from_goal(
        "Research AI trends and write a report"
    )
    
    # Get hierarchy
    hierarchy = nexus.get_agent_hierarchy(root_id)
    print(f"Created {len(hierarchy['children'])} child agents")
    
    # Cleanup
    await nexus.stop()

asyncio.run(main())
```

## Web Dashboard

The dashboard provides:

1. **Bootstrap Interface**: Enter a goal and spawn agents
2. **System Status**: Real-time metrics
3. **Agent List**: All active agents
4. **Crews**: Team organization
5. **Experts**: Available specialists

### Dashboard URL

Default: `http://localhost:8080`

## Configuration

Create a `.env` file in the project root:

```bash
# Copy example
cp .env.example .env

# Edit settings
NEXUSFORGE_ENV=development
NEXUSFORGE_LOG_LEVEL=INFO
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
MAX_AGENT_DEPTH=5
```

## Examples

### Example 1: Research Task

```bash
python -m nexusforge bootstrap "Research quantum computing and summarize key findings"
```

### Example 2: Development Task

```bash
python -m nexusforge bootstrap "Build a web scraper for news articles with error handling"
```

### Example 3: Complex Workflow

```python
from nexusforge import NexusForge
from nexusforge.core.fractal_agent import AgentTemplate

async def complex_workflow():
    nexus = NexusForge()
    await nexus.start()
    
    # Create specialized template
    template = AgentTemplate(
        name="DataAnalyst",
        role="Analyst",
        capabilities=["analyze", "visualize", "report"],
        goal_template="Analyze data and create insights"
    )
    
    # Create agent
    agent = nexus.create_agent_from_template(template)
    
    # Assign goal
    result = await agent.process_goal(
        "Analyze sales data and create visualization"
    )
    
    print(f"Spawned {len(result['children'])} child agents")
    
    await nexus.stop()
```

## Troubleshooting

### Issue: Module not found

```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/NexusForge-2.0-:$PYTHONPATH
```

### Issue: Port already in use

```bash
# Change port
python -m nexusforge gui --port 8081
```

### Issue: Permission denied

```bash
# Use sudo (Linux/Mac)
sudo python -m nexusforge gui

# Or change port to > 1024
python -m nexusforge gui --port 8080
```

## Next Steps

1. Read the [Architecture Documentation](architecture.md)
2. Explore the [examples/](../examples/) directory
3. Check the [API Reference](api.md)
4. Learn about [Agent Systems](agents.md)
5. Understand [Communication](communication.md)

## Getting Help

- Check the [documentation](../docs/)
- Review [examples](../examples/)
- Open an issue on GitHub
- Read the source code (it's well-commented!)

## Tips

1. Start with simple goals to understand the system
2. Use the dashboard to visualize agent hierarchies
3. Check logs for debugging (set LOG_LEVEL=DEBUG)
4. Experiment with different agent depths
5. Create custom agent templates for specialized tasks
