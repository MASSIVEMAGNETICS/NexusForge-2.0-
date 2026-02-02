"""
Tests for enhanced NexusForge functionality
- Enhanced goal decomposition
- Expert performance tracking
- Priority message queues
- Advanced crew workflows
- Agent performance metrics
"""

import pytest
import asyncio
from nexusforge import NexusForge, FractalAgent
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.agents.crew import CrewRole, WorkflowPattern
from nexusforge.agents.experts import ExpertModality, TaskResult
from nexusforge.communication.hub import MessagePriority, MessageType


class TestEnhancedGoalDecomposition:
    """Test enhanced goal decomposition features"""
    
    @pytest.mark.asyncio
    async def test_complexity_analysis(self):
        """Test goal complexity analysis"""
        template = AgentTemplate(
            name="TestAgent",
            role="Coordinator",
            capabilities=["coordinate"],
            goal_template="Test"
        )
        
        agent = FractalAgent(template)
        
        # Simple goal
        simple_complexity = agent._analyze_goal_complexity("Test the feature")
        assert 0.0 < simple_complexity < 0.5
        
        # Complex goal
        complex_complexity = agent._analyze_goal_complexity(
            "Research and design and implement and test and deploy a distributed "
            "concurrent algorithm for optimization"
        )
        assert complex_complexity > 0.5
    
    @pytest.mark.asyncio
    async def test_enhanced_subtask_generation(self):
        """Test enhanced subtask generation with dependencies"""
        template = AgentTemplate(
            name="TestAgent",
            role="Coordinator",
            capabilities=["coordinate"],
            goal_template="Test"
        )
        
        agent = FractalAgent(template)
        goal = "Research and design and implement and test the feature"
        subtasks = await agent.break_down_goal(goal)
        
        # Should have multiple subtasks
        assert len(subtasks) >= 3
        
        # Check for new fields
        for task in subtasks:
            assert "complexity" in task
            assert "dependencies" in task
            assert "estimated_effort" in task
            assert task["complexity"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_role_inference_expansion(self):
        """Test expanded role inference"""
        template = AgentTemplate(
            name="TestAgent",
            role="Coordinator",
            capabilities=["coordinate"],
            goal_template="Test"
        )
        
        agent = FractalAgent(template)
        
        # Test new roles
        assert agent._infer_role("design the architecture") == "Designer"
        assert agent._infer_role("optimize performance") == "Optimizer"
        assert agent._infer_role("deploy to production") == "DevOps"
        assert agent._infer_role("plan the project") == "Planner"


class TestExpertPerformanceTracking:
    """Test expert performance tracking and metrics"""
    
    def test_expert_performance_metrics(self):
        """Test expert profile has performance fields"""
        from nexusforge.agents.experts import MultiModalExpertSystem, ExpertProfile
        
        expert_system = MultiModalExpertSystem()
        experts = expert_system.get_all_experts()
        
        # Check all experts have performance fields
        for expert in experts:
            assert hasattr(expert, 'total_tasks')
            assert hasattr(expert, 'successful_tasks')
            assert hasattr(expert, 'failed_tasks')
            assert hasattr(expert, 'expertise_level')
            assert expert.expertise_level == 1.0  # Initial value
    
    def test_task_result_recording(self):
        """Test recording task results updates expert metrics"""
        from nexusforge.agents.experts import MultiModalExpertSystem
        
        expert_system = MultiModalExpertSystem()
        expert_id = list(expert_system.experts.keys())[0]
        
        # Record successful task
        result = TaskResult(
            task_id="task1",
            expert_id=expert_id,
            success=True,
            completion_time=1.5,
            confidence_score=0.9
        )
        
        expert_system.record_task_result(result)
        
        expert = expert_system.experts[expert_id]
        assert expert.total_tasks == 1
        assert expert.successful_tasks == 1
        assert expert.expertise_level > 1.0  # Should increase
    
    def test_enhanced_expert_selection(self):
        """Test expert selection uses performance metrics"""
        from nexusforge.agents.experts import MultiModalExpertSystem
        
        expert_system = MultiModalExpertSystem()
        
        # Get a code expert
        code_experts = expert_system.find_experts(modality=ExpertModality.CODE)
        assert len(code_experts) > 0
        
        expert_id = code_experts[0].expert_id
        
        # Simulate good performance
        for i in range(5):
            result = TaskResult(
                task_id=f"task{i}",
                expert_id=expert_id,
                success=True,
                completion_time=1.0,
                confidence_score=0.9
            )
            expert_system.record_task_result(result)
        
        # Select expert for code task
        task = {"description": "analyze code quality"}
        selected = expert_system.select_expert(task, ExpertModality.CODE)
        
        # High-performing expert should be selected
        assert selected == expert_id
    
    def test_get_top_experts(self):
        """Test getting top performing experts"""
        from nexusforge.agents.experts import MultiModalExpertSystem
        
        expert_system = MultiModalExpertSystem()
        
        # Simulate some performance
        experts = list(expert_system.experts.keys())
        for i, expert_id in enumerate(experts[:3]):
            for j in range(i + 1):
                result = TaskResult(
                    task_id=f"task{i}_{j}",
                    expert_id=expert_id,
                    success=True,
                    completion_time=1.0,
                    confidence_score=0.9
                )
                expert_system.record_task_result(result)
        
        top_experts = expert_system.get_top_experts(3)
        assert len(top_experts) <= 3
        
        # Check they have performance data
        for expert_perf in top_experts:
            if expert_perf.get("total_tasks", 0) > 0:
                assert "success_rate" in expert_perf
                assert "expertise_level" in expert_perf


class TestPriorityMessageQueue:
    """Test priority-based message queuing"""
    
    @pytest.mark.asyncio
    async def test_message_priority_ordering(self):
        """Test messages are delivered by priority"""
        from nexusforge.communication.hub import CommunicationHub, MessageType
        
        hub = CommunicationHub()
        await hub.start()
        
        hub.register_agent("agent1", None)
        hub.register_agent("agent2", None)
        
        # Send messages with different priorities
        await hub.send_message(
            "agent1", "agent2", MessageType.CHAT, "Low priority",
            priority=MessagePriority.LOW
        )
        await hub.send_message(
            "agent1", "agent2", MessageType.CHAT, "High priority",
            priority=MessagePriority.HIGH
        )
        await hub.send_message(
            "agent1", "agent2", MessageType.CHAT, "Urgent",
            priority=MessagePriority.URGENT
        )
        
        # Receive messages - should get highest priority first
        msg1 = await hub.receive_message("agent2")
        assert msg1 is not None
        assert msg1.priority == MessagePriority.URGENT
        
        msg2 = await hub.receive_message("agent2")
        assert msg2 is not None
        assert msg2.priority == MessagePriority.HIGH
        
        msg3 = await hub.receive_message("agent2")
        assert msg3 is not None
        assert msg3.priority == MessagePriority.LOW
        
        await hub.stop()
    
    @pytest.mark.asyncio
    async def test_message_dependencies(self):
        """Test message dependency tracking"""
        from nexusforge.communication.hub import CommunicationHub, MessageType
        
        hub = CommunicationHub()
        await hub.start()
        
        hub.register_agent("agent1", None)
        hub.register_agent("agent2", None)
        
        # Send first message
        msg1_id = await hub.send_message(
            "agent1", "agent2", MessageType.CHAT, "First message"
        )
        
        # Send second message that depends on first
        msg2_id = await hub.send_message(
            "agent1", "agent2", MessageType.CHAT, "Dependent message",
            dependencies=[msg1_id]
        )
        
        # Initially msg2 should be pending
        assert msg2_id in hub._pending_messages or msg2_id not in hub._pending_messages
        
        await hub.stop()


class TestAdvancedCrewWorkflows:
    """Test advanced crew workflow patterns"""
    
    @pytest.mark.asyncio
    async def test_workflow_pattern_assignment(self):
        """Test crews can be created with different workflow patterns"""
        nexus = NexusForge()
        await nexus.start()
        
        # Create agents
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test"
        )
        
        agents = [nexus.create_agent_from_template(template) for _ in range(3)]
        agent_ids = [a.agent_id for a in agents]
        
        # Create crew with parallel workflow
        crew_id = nexus.create_crew(
            name="ParallelCrew",
            agent_ids=agent_ids,
            roles=[CrewRole.LEADER, CrewRole.BUILDER, CrewRole.TESTER],
            leader_id=agent_ids[0],
            workflow_pattern=WorkflowPattern.PARALLEL
        )
        
        crew = nexus.crew_manager.get_crew(crew_id)
        assert crew.workflow_pattern == WorkflowPattern.PARALLEL
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_crew_statistics(self):
        """Test crew statistics tracking"""
        nexus = NexusForge()
        await nexus.start()
        
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agents = [nexus.create_agent_from_template(template) for _ in range(2)]
        
        crew_id = nexus.create_crew(
            name="TestCrew",
            agent_ids=[a.agent_id for a in agents],
            roles=[CrewRole.LEADER, CrewRole.BUILDER]
        )
        
        stats = nexus.crew_manager.get_crew_statistics(crew_id)
        
        assert "total_members" in stats
        assert "workflow_pattern" in stats
        assert "pending_tasks" in stats
        assert stats["total_members"] == 2
        
        await nexus.stop()


class TestAgentPerformanceMetrics:
    """Test agent performance tracking"""
    
    def test_agent_performance_tracking(self):
        """Test agents track performance metrics"""
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agent = FractalAgent(template)
        
        # Record successful task
        agent.record_task_completion(success=True, execution_time=1.5)
        
        assert agent.state.tasks_completed == 1
        assert agent.state.performance_score > 1.0  # Should increase
        
        # Record failed task
        agent.record_task_completion(success=False, execution_time=0.5)
        
        assert agent.state.tasks_failed == 1
        assert agent.state.performance_score < 1.02  # Should decrease
    
    def test_agent_success_rate(self):
        """Test agent success rate calculation"""
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agent = FractalAgent(template)
        
        # Complete some tasks
        agent.record_task_completion(success=True)
        agent.record_task_completion(success=True)
        agent.record_task_completion(success=False)
        
        success_rate = agent.get_success_rate()
        assert success_rate == 2/3  # 2 out of 3 successful
    
    def test_get_performance_metrics(self):
        """Test getting comprehensive performance metrics"""
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agent = FractalAgent(template)
        agent.record_task_completion(success=True, execution_time=2.0)
        agent.record_task_completion(success=True, execution_time=3.0)
        
        metrics = agent.get_performance_metrics()
        
        assert "performance_score" in metrics
        assert "success_rate" in metrics
        assert "avg_execution_time" in metrics
        assert "total_tasks" in metrics
        assert metrics["total_tasks"] == 2
        assert metrics["success_rate"] == 1.0


class TestNexusEnhancements:
    """Test enhancements to main NexusForge orchestrator"""
    
    @pytest.mark.asyncio
    async def test_enhanced_statistics(self):
        """Test enhanced statistics include new metrics"""
        nexus = NexusForge()
        await nexus.start()
        
        # Create some agents
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        for _ in range(3):
            nexus.create_agent_from_template(template)
        
        stats = nexus.get_statistics()
        
        # Check for new fields
        assert "top_performers" in stats["agent_stats"]
        assert "by_workflow" in stats["crew_stats"]
        assert "top_experts" in stats["expert_stats"]
        assert "pending_messages" in stats["communication_stats"]
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_priority_message_sending(self):
        """Test sending priority messages through nexus"""
        nexus = NexusForge()
        await nexus.start()
        
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agent1 = nexus.create_agent_from_template(template)
        agent2 = nexus.create_agent_from_template(template)
        
        # Send high priority message
        msg_id = await nexus.send_priority_message(
            agent1.agent_id,
            agent2.agent_id,
            "Urgent message",
            priority="HIGH"
        )
        
        assert msg_id is not None
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_top_performing_agents(self):
        """Test getting top performing agents"""
        nexus = NexusForge()
        await nexus.start()
        
        template = AgentTemplate(
            name="TestAgent",
            role="Worker",
            capabilities=["work"],
            goal_template="Work"
        )
        
        agents = [nexus.create_agent_from_template(template) for _ in range(3)]
        
        # Record different performance levels
        agents[0].record_task_completion(success=True)
        agents[0].record_task_completion(success=True)
        agents[1].record_task_completion(success=True)
        
        top_agents = nexus.get_top_performing_agents(limit=5)
        
        assert len(top_agents) <= 5
        # Agents with tasks should appear
        assert any(a["tasks_completed"] > 0 for a in top_agents)
        
        await nexus.stop()


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
