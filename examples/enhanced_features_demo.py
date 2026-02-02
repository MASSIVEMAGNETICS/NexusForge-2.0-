"""
Example demonstrating NexusForge 2.0 enhanced features

This example showcases:
- Enhanced goal decomposition with complexity analysis
- Performance tracking for agents and experts
- Priority message queuing
- Advanced crew workflows
- System-wide analytics
"""

import asyncio
from nexusforge import NexusForge
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.agents.crew import CrewRole, WorkflowPattern
from nexusforge.agents.experts import TaskResult


async def main():
    print("🚀 NexusForge 2.0 - Enhanced Features Demo\n")
    print("=" * 60)
    
    # Initialize NexusForge
    nexus = NexusForge()
    await nexus.start()
    
    # ========================================================================
    # 1. Enhanced Goal Decomposition
    # ========================================================================
    print("\n📋 1. Enhanced Goal Decomposition")
    print("-" * 60)
    
    complex_goal = (
        "Research distributed systems and design a scalable architecture "
        "and implement concurrent processing and test performance "
        "and deploy to production"
    )
    
    print(f"Goal: {complex_goal}\n")
    
    # Bootstrap from complex goal
    root_agent_id = await nexus.bootstrap_from_goal(complex_goal)
    root_agent = nexus.get_agent(root_agent_id)
    
    # Show subtasks with complexity
    if root_agent.children:
        print("Generated subtasks with complexity analysis:")
        for i, child in enumerate(root_agent.children, 1):
            print(f"  {i}. {child.state.role}: {child.state.goals[0] if child.state.goals else 'N/A'}")
            print(f"     Capabilities: {', '.join(child.template.capabilities[:3])}")
    
    # ========================================================================
    # 2. Agent Performance Tracking
    # ========================================================================
    print("\n\n📊 2. Agent Performance Tracking")
    print("-" * 60)
    
    # Simulate some task completions
    template = AgentTemplate(
        name="HighPerformer",
        role="Builder",
        capabilities=["build", "code", "test"],
        goal_template="Build features"
    )
    
    agent = nexus.create_agent_from_template(template)
    
    # Record successful tasks
    print(f"\nAgent: {agent.state.name}")
    for i in range(5):
        agent.record_task_completion(success=True, execution_time=1.5 + i * 0.2)
    
    # Record one failure
    agent.record_task_completion(success=False, execution_time=0.5)
    
    # Get performance metrics
    metrics = agent.get_performance_metrics()
    print(f"  Tasks completed: {metrics['tasks_completed']}")
    print(f"  Tasks failed: {metrics['tasks_failed']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Performance score: {metrics['performance_score']:.2f}")
    print(f"  Avg execution time: {metrics['avg_execution_time']:.2f}s")
    
    # ========================================================================
    # 3. Expert Performance Tracking
    # ========================================================================
    print("\n\n🎓 3. Expert Performance & Learning")
    print("-" * 60)
    
    # Simulate expert task results
    experts = nexus.expert_system.get_all_experts()
    code_expert = next((e for e in experts if "code" in e.name.lower()), experts[0])
    
    print(f"\nExpert: {code_expert.name} ({code_expert.modality.value})")
    
    # Record multiple successful tasks
    for i in range(8):
        result = TaskResult(
            task_id=f"task_{i}",
            expert_id=code_expert.expert_id,
            success=i < 7,  # 7 successes, 1 failure
            completion_time=1.0 + i * 0.1,
            confidence_score=0.85 + i * 0.01
        )
        nexus.record_expert_task_result(
            code_expert.expert_id,
            result.task_id,
            result.success,
            result.completion_time,
            result.confidence_score
        )
    
    # Check updated performance
    perf = nexus.expert_system.get_expert_performance(code_expert.expert_id)
    print(f"  Total tasks: {perf['total_tasks']}")
    print(f"  Success rate: {perf['success_rate']:.1%}")
    print(f"  Expertise level: {perf['expertise_level']:.2f} (started at 1.0)")
    print(f"  Avg completion time: {perf['avg_completion_time']:.2f}s")
    
    # ========================================================================
    # 4. Priority Message Queuing
    # ========================================================================
    print("\n\n🚦 4. Priority Message Queuing")
    print("-" * 60)
    
    # Create two agents for messaging
    template1 = AgentTemplate(
        name="Sender",
        role="Coordinator",
        capabilities=["coordinate"],
        goal_template="Send messages"
    )
    template2 = AgentTemplate(
        name="Receiver",
        role="Worker",
        capabilities=["work"],
        goal_template="Receive messages"
    )
    
    sender = nexus.create_agent_from_template(template1)
    receiver = nexus.create_agent_from_template(template2)
    
    print(f"\nSending messages with different priorities to {receiver.state.name}:")
    
    # Send messages with different priorities
    await nexus.send_priority_message(
        sender.agent_id, receiver.agent_id,
        "Low priority message", priority="LOW"
    )
    print("  ✓ Sent LOW priority message")
    
    await nexus.send_priority_message(
        sender.agent_id, receiver.agent_id,
        "Normal message", priority="NORMAL"
    )
    print("  ✓ Sent NORMAL priority message")
    
    await nexus.send_priority_message(
        sender.agent_id, receiver.agent_id,
        "Urgent alert!", priority="URGENT"
    )
    print("  ✓ Sent URGENT priority message")
    
    # Receive messages (will get URGENT first)
    print("\nReceiving messages (note priority order):")
    for i in range(3):
        msg = await nexus.communication_hub.receive_message(receiver.agent_id)
        if msg:
            print(f"  {i+1}. Priority: {msg.priority.name:7s} - {msg.content}")
    
    # ========================================================================
    # 5. Advanced Crew Workflows
    # ========================================================================
    print("\n\n👥 5. Advanced Crew Workflows")
    print("-" * 60)
    
    # Create agents for crew
    crew_agents = []
    for i, role in enumerate([CrewRole.LEADER, CrewRole.RESEARCHER, 
                               CrewRole.BUILDER, CrewRole.TESTER]):
        template = AgentTemplate(
            name=f"{role.value.title()}_{i}",
            role=role.value,
            capabilities=[role.value],
            goal_template=f"Perform {role.value} tasks"
        )
        crew_agents.append(nexus.create_agent_from_template(template))
    
    # Create crew with PIPELINE workflow
    print("\nCreating crew with PIPELINE workflow:")
    crew_id = nexus.create_crew(
        name="DevPipeline",
        agent_ids=[a.agent_id for a in crew_agents],
        roles=[CrewRole.LEADER, CrewRole.RESEARCHER, CrewRole.BUILDER, CrewRole.TESTER],
        leader_id=crew_agents[0].agent_id,
        workflow_pattern=WorkflowPattern.PIPELINE
    )
    
    # Get crew statistics
    stats = nexus.crew_manager.get_crew_statistics(crew_id)
    print(f"  Name: {stats['name']}")
    print(f"  Workflow: {stats['workflow_pattern']}")
    print(f"  Members: {stats['total_members']}")
    print(f"  Active: {stats['active_members']}")
    
    # Create another crew with PARALLEL workflow
    print("\nCreating crew with PARALLEL workflow:")
    parallel_crew_id = nexus.create_crew(
        name="ResearchTeam",
        agent_ids=[crew_agents[1].agent_id, crew_agents[2].agent_id],
        roles=[CrewRole.RESEARCHER, CrewRole.RESEARCHER],
        workflow_pattern=WorkflowPattern.PARALLEL
    )
    
    parallel_stats = nexus.crew_manager.get_crew_statistics(parallel_crew_id)
    print(f"  Name: {parallel_stats['name']}")
    print(f"  Workflow: {parallel_stats['workflow_pattern']}")
    
    # ========================================================================
    # 6. System-Wide Analytics
    # ========================================================================
    print("\n\n📈 6. System-Wide Analytics")
    print("-" * 60)
    
    # Get comprehensive statistics
    stats = nexus.get_statistics()
    
    print(f"\nAgent Statistics:")
    print(f"  Total agents: {stats['agent_stats']['total']}")
    print(f"  By depth: {dict(stats['agent_stats']['by_depth'])}")
    print(f"  By role: {', '.join(f'{k}: {v}' for k, v in list(stats['agent_stats']['by_role'].items())[:3])}")
    
    if stats['agent_stats']['top_performers']:
        print(f"\n  Top Performing Agent:")
        top = stats['agent_stats']['top_performers'][0]
        print(f"    {top['name']}: {top['success_rate']:.1%} success rate, "
              f"score {top['performance_score']:.2f}")
    
    print(f"\nCrew Statistics:")
    print(f"  Total crews: {stats['crew_stats']['total']}")
    print(f"  By workflow: {stats['crew_stats']['by_workflow']}")
    
    print(f"\nExpert Statistics:")
    print(f"  Total experts: {stats['expert_stats']['total']}")
    if stats['expert_stats']['top_experts']:
        top_expert = stats['expert_stats']['top_experts'][0]
        print(f"  Top Expert: {top_expert['name']} - "
              f"{top_expert['success_rate']:.1%} success, "
              f"expertise {top_expert['expertise_level']:.2f}")
    
    print(f"\nCommunication Statistics:")
    print(f"  Total messages: {stats['communication_stats']['total_messages']}")
    print(f"  Conversations: {stats['communication_stats']['conversations']}")
    print(f"  Pending messages: {stats['communication_stats']['pending_messages']}")
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    await nexus.stop()
    
    print("\n" + "=" * 60)
    print("✅ Demo complete! All enhanced features demonstrated.")
    print("\nKey Improvements:")
    print("  • Smart goal decomposition with complexity analysis")
    print("  • Performance tracking for agents and experts")
    print("  • Priority-based message delivery")
    print("  • Advanced crew workflow patterns")
    print("  • Comprehensive system analytics")
    print("\nSee docs/ENHANCEMENTS.md for full documentation.")


if __name__ == "__main__":
    asyncio.run(main())
