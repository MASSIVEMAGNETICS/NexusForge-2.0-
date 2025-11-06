"""
Example usage of NexusForge 2.0

Demonstrates how to use the framework to bootstrap an agent system.
"""

import asyncio
from nexusforge import NexusForge


async def main():
    # Initialize NexusForge
    print("Initializing NexusForge 2.0...")
    nexus = NexusForge()
    await nexus.start()
    
    # Bootstrap from a goal
    goal = "Research and summarize the latest AI developments, then create a presentation"
    print(f"\nBootstrapping from goal: {goal}")
    
    root_agent_id = await nexus.bootstrap_from_goal(goal)
    
    # Get the hierarchy
    print("\nAgent Hierarchy:")
    hierarchy = nexus.get_agent_hierarchy(root_agent_id)
    print_hierarchy(hierarchy)
    
    # Get statistics
    print("\nSystem Statistics:")
    stats = nexus.get_statistics()
    print(f"Total Agents: {stats['agent_stats']['total']}")
    print(f"Agents by Depth: {stats['agent_stats']['by_depth']}")
    print(f"Agents by Role: {stats['agent_stats']['by_role']}")
    
    # Stop the system
    await nexus.stop()
    print("\nSystem stopped.")


def print_hierarchy(node, indent=0):
    """Print agent hierarchy"""
    prefix = "  " * indent + ("└─ " if indent > 0 else "")
    print(f"{prefix}{node['name']} ({node['role']}) - Depth: {node['depth']}")
    
    for child in node.get('children', []):
        print_hierarchy(child, indent + 1)


if __name__ == '__main__':
    asyncio.run(main())
