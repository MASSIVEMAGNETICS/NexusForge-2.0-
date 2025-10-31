"""
Basic tests for NexusForge core functionality
"""

import pytest
import asyncio
from nexusforge import NexusForge, FractalAgent
from nexusforge.core.fractal_agent import AgentTemplate
from nexusforge.agents.crew import CrewRole
from nexusforge.agents.experts import ExpertModality


class TestFractalAgent:
    """Test fractal agent functionality"""
    
    def test_agent_creation(self):
        """Test creating an agent"""
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test", "verify"],
            goal_template="Test the system"
        )
        
        agent = FractalAgent(template, depth=0)
        
        assert agent.state.name == "TestAgent"
        assert agent.state.role == "Tester"
        assert agent.depth == 0
        assert "test" in agent.template.capabilities
    
    def test_can_spawn(self):
        """Test spawn depth checking"""
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test",
            max_depth=3
        )
        
        agent1 = FractalAgent(template, depth=0)
        assert agent1.can_spawn() is True
        
        agent2 = FractalAgent(template, depth=3)
        assert agent2.can_spawn() is False
    
    @pytest.mark.asyncio
    async def test_goal_breakdown(self):
        """Test goal decomposition"""
        template = AgentTemplate(
            name="TestAgent",
            role="Coordinator",
            capabilities=["coordinate"],
            goal_template="Test goal"
        )
        
        agent = FractalAgent(template)
        goal = "Research and build and test a feature"
        subtasks = await agent.break_down_goal(goal)
        
        assert len(subtasks) > 0
        assert any("research" in str(task).lower() for task in subtasks)
    
    def test_function_registration(self):
        """Test dynamic function registration"""
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test"
        )
        
        agent = FractalAgent(template)
        
        def test_func():
            return "tested"
        
        agent.register_function("test_func", test_func)
        
        assert "test_func" in agent.functions
        assert "test_func" in agent.template.capabilities


class TestNexusForge:
    """Test main NexusForge orchestrator"""
    
    @pytest.mark.asyncio
    async def test_nexus_initialization(self):
        """Test NexusForge initialization"""
        nexus = NexusForge()
        await nexus.start()
        
        assert nexus.running is True
        assert nexus.communication_hub is not None
        assert nexus.crew_manager is not None
        assert nexus.expert_system is not None
        
        await nexus.stop()
        assert nexus.running is False
    
    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test agent registration"""
        nexus = NexusForge()
        await nexus.start()
        
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test"
        )
        
        agent = nexus.create_agent_from_template(template)
        
        assert agent.agent_id in nexus.agents
        assert agent.agent_id in nexus.communication_hub.agents
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_bootstrap_from_goal(self):
        """Test bootstrapping from a goal"""
        nexus = NexusForge()
        await nexus.start()
        
        goal = "Test the system thoroughly"
        root_agent_id = await nexus.bootstrap_from_goal(goal)
        
        assert root_agent_id in nexus.agents
        assert root_agent_id in nexus.root_agents
        
        root_agent = nexus.get_agent(root_agent_id)
        assert root_agent is not None
        assert goal in root_agent.state.goals
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_crew_creation(self):
        """Test creating a crew"""
        nexus = NexusForge()
        await nexus.start()
        
        # Create agents
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test"
        )
        
        agent1 = nexus.create_agent_from_template(template)
        agent2 = nexus.create_agent_from_template(template)
        
        # Create crew
        crew_id = nexus.create_crew(
            name="TestCrew",
            agent_ids=[agent1.agent_id, agent2.agent_id],
            roles=[CrewRole.LEADER, CrewRole.TESTER],
            leader_id=agent1.agent_id
        )
        
        assert crew_id in nexus.crew_manager.crews
        crew = nexus.crew_manager.get_crew(crew_id)
        assert crew.name == "TestCrew"
        assert len(crew.members) == 2
        
        await nexus.stop()
    
    @pytest.mark.asyncio
    async def test_message_sending(self):
        """Test agent messaging"""
        nexus = NexusForge()
        await nexus.start()
        
        template = AgentTemplate(
            name="TestAgent",
            role="Tester",
            capabilities=["test"],
            goal_template="Test"
        )
        
        agent1 = nexus.create_agent_from_template(template)
        agent2 = nexus.create_agent_from_template(template)
        
        # Send message
        message_id = await nexus.send_message(
            agent1.agent_id,
            agent2.agent_id,
            "Test message"
        )
        
        assert message_id is not None
        assert len(nexus.communication_hub.message_history) > 0
        
        await nexus.stop()


class TestExpertSystem:
    """Test expert system"""
    
    def test_expert_initialization(self):
        """Test expert system has default experts"""
        from nexusforge.agents.experts import MultiModalExpertSystem
        
        expert_system = MultiModalExpertSystem()
        experts = expert_system.get_all_experts()
        
        assert len(experts) > 0
        assert any(e.modality == ExpertModality.TEXT for e in experts)
        assert any(e.modality == ExpertModality.CODE for e in experts)
    
    def test_expert_finding(self):
        """Test finding experts by criteria"""
        from nexusforge.agents.experts import MultiModalExpertSystem
        
        expert_system = MultiModalExpertSystem()
        
        # Find by modality
        code_experts = expert_system.find_experts(modality=ExpertModality.CODE)
        assert len(code_experts) > 0
        assert all(e.modality == ExpertModality.CODE for e in code_experts)
        
        # Find by capability
        experts = expert_system.find_experts(capability="analyze_code")
        assert len(experts) > 0


class TestCommunicationHub:
    """Test communication hub"""
    
    @pytest.mark.asyncio
    async def test_hub_initialization(self):
        """Test communication hub initialization"""
        from nexusforge.communication.hub import CommunicationHub
        
        hub = CommunicationHub()
        await hub.start()
        
        assert hub._running is True
        
        await hub.stop()
        assert hub._running is False
    
    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test registering agents with hub"""
        from nexusforge.communication.hub import CommunicationHub
        
        hub = CommunicationHub()
        
        hub.register_agent("agent1", None)
        hub.register_agent("agent2", None)
        
        assert "agent1" in hub.agents
        assert "agent2" in hub.agents
        assert "agent1" in hub.message_queues
        assert "agent2" in hub.message_queues


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
