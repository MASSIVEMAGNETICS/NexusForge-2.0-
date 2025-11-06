"""
Advanced example: Creating a crew for a complex task
"""

import asyncio
from nexusforge import NexusForge
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.agents.crew import CrewRole


async def main():
    # Initialize
    nexus = NexusForge()
    await nexus.start()
    
    print("🚀 Creating a specialized crew for software development")
    
    # Create specialized agents
    templates = [
        AgentTemplate(
            name="TechLead",
            role="Leader",
            capabilities=["plan", "coordinate", "review", "decide"],
            goal_template="Lead the development team"
        ),
        AgentTemplate(
            name="BackendDev",
            role="Builder",
            capabilities=["code", "api", "database", "test"],
            goal_template="Develop backend services"
        ),
        AgentTemplate(
            name="FrontendDev",
            role="Builder",
            capabilities=["code", "ui", "ux", "responsive"],
            goal_template="Develop user interface"
        ),
        AgentTemplate(
            name="QAEngineer",
            role="Tester",
            capabilities=["test", "verify", "debug", "report"],
            goal_template="Ensure quality"
        )
    ]
    
    # Create agents
    agents = []
    for template in templates:
        agent = nexus.create_agent_from_template(template)
        agents.append(agent)
        print(f"  ✓ Created {agent.state.name}")
    
    # Create a crew
    crew_id = nexus.create_crew(
        name="DevTeam Alpha",
        agent_ids=[agent.agent_id for agent in agents],
        roles=[CrewRole.LEADER, CrewRole.BUILDER, CrewRole.BUILDER, CrewRole.TESTER],
        leader_id=agents[0].agent_id,
        goals=["Build a REST API with modern frontend"]
    )
    
    print(f"\n✅ Crew created: {crew_id}")
    
    # Assign a complex goal
    goal = "Build a user authentication system with frontend and backend"
    print(f"\n🎯 Assigning goal: {goal}")
    
    result = await agents[0].process_goal(goal)
    print(f"\n📊 Goal broken into {len(result['subtasks'])} subtasks")
    
    # Show crew communication
    print("\n💬 Enabling crew communication...")
    await nexus.crew_manager.broadcast_to_crew(
        crew_id,
        "Let's start working on the authentication system!",
        agents[0].agent_id
    )
    
    # Get statistics
    stats = nexus.get_statistics()
    print(f"\n📈 System Stats:")
    print(f"  Total Agents: {stats['agent_stats']['total']}")
    print(f"  Active Crews: {stats['crew_stats']['active']}")
    print(f"  Messages: {stats['communication_stats']['total_messages']}")
    
    await nexus.stop()


if __name__ == '__main__':
    asyncio.run(main())
